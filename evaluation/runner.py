"""Experimentos sequenciais: referências SQL, checkpoints e evidência reproduzível."""

import asyncio
import hashlib
import importlib.metadata
import json
import statistics
import subprocess
import time
import uuid
from datetime import datetime, timezone

from psycopg import sql

from app.database_tools import scalar
from app.sql_policy import TABLES
from evaluation.scoring import compare_rows


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def validate_references(dataset, database):
    references = {}
    for case in dataset.cases:
        for index, turn in enumerate(case.turns):
            for reference in turn.references:
                result = database.execute_sql(reference.sql)
                if "error" in result or result.get("truncated"):
                    raise ValueError(f"Referência inválida ou parcial: {case.id}, turno {index}.")
                if len(result["columns"]) != len(reference.types):
                    raise ValueError(f"Colunas incompatíveis na referência {case.id}.")
                references[(case.id, index, reference.metric)] = result
    return references


def database_fingerprint(database):
    """Somente leitura, timeout da conexão e limite explícito por tabela."""
    tables = {}
    with database.connection() as connection:
        for table in sorted(TABLES):
            cursor = connection.execute(
                sql.SQL("SELECT * FROM {} ORDER BY id LIMIT 100001").format(sql.Identifier(table))
            )
            rows = cursor.fetchall()
            if len(rows) > 100000:
                raise ValueError("Base excede o limite de identificação do experimento.")
            data = {
                "columns": [c.name for c in cursor.description],
                "rows": [[scalar(v) for v in row] for row in rows],
            }
            tables[table] = {"count": len(rows), "sha256": digest(dump(data).encode())}
    return tables


def score_turn(turn, trace, references):
    if trace.get("status") != turn.expected:
        return False
    queries = trace.get("queries", [])
    if turn.expected != "answer":
        return not queries
    if len(queries) != len(turn.references):
        return False
    by_metric = {q["plan"]["metric"]: q for q in queries}
    if len(by_metric) != len(queries):
        return False
    for reference in turn.references:
        query = by_metric.get(reference.metric, {})
        selected = query.get("selected", {})
        if not selected or selected.get("truncated") or "error" in selected:
            return False
        rows = selected["rows"]
        # O prompt e o renderer reservam registros como metadado de ausência.
        # Outras colunas extras continuam reprovando; contagens precisam ser inteiras.
        if "registros" in selected["columns"]:
            if selected["columns"].count("registros") != 1:
                return False
            index = selected["columns"].index("registros")
            if any(type(row[index]) is not int or row[index] < 0 for row in rows):
                return False
            rows = [row[:index] + row[index + 1 :] for row in rows]
            # O renderer oculta todos os valores quando afirma ausência de registros.
            if len(rows) == 1 and selected["rows"][0][index] == 0:
                if any(v is not None and str(v) not in {"0", "0.00"} for v in rows[0]):
                    return False
        if not compare_rows(
            rows, references[reference.metric]["rows"], reference.types, ordered=reference.ordered
        ):
            return False
    return True


def summarize(cases, records, stop_reason):
    complete = len(records) == len(cases) and stop_reason is None
    metrics = {}
    groups = [
        ("execution_accuracy", lambda outcome: outcome == "answer"),
        ("clarification_accuracy", lambda outcome: outcome.startswith("clarification")),
    ]
    if any(c.turns[-1].expected == "unsupported_request" for c in cases):
        groups.append(("unsupported_accuracy", lambda outcome: outcome == "unsupported_request"))
    for name, belongs in groups:
        ids = {c.id for c in cases if belongs(c.turns[-1].expected)}
        observed = [r for r in records if r["id"] in ids]
        passed = sum(r["passed"] for r in observed)
        metrics[name] = {
            "planned": len(ids),
            "completed": len(observed),
            "passed": passed,
            "rate": passed / len(ids) if complete and ids else None,
        }
    latencies = [t["elapsed_ms"] for r in records for t in r["turns"]]
    return {
        "complete": complete,
        "stop_reason": stop_reason,
        "metrics": metrics,
        "cases_completed": len(records),
        "cases_planned": len(cases),
        "not_run": [c.id for c in cases if c.id not in {r["id"] for r in records}],
        "mean_agent_ms_observed": statistics.mean(latencies) if latencies else None,
        "latency_scope": "Agente e banco; exclui transporte Telegram e intervalo entre casos.",
        "failed_cases": [r["id"] for r in records if not r["passed"]],
    }


def manifest(root, dataset_path, dataset, settings, database, split):
    sources = {}
    for folder in ("app", "evaluation", "scripts", "db", "training"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and path.suffix in {".py", ".sql", ".json"}:
                sources[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()
    )
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "live": True,
        "split": split,
        "git_commit": commit,
        "git_dirty": dirty,
        "source_hashes": sources,
        "dataset_sha256": digest(dataset_path.read_bytes()),
        "dataset_version": dataset.version,
        "seed_declared": dataset.seed,
        "clients_declared": dataset.clients,
        "database": database_fingerprint(database),
        "model": settings.gemini_model,
        "intent_classifier_enabled": settings.intent_classifier_enabled,
        "limits": {
            "rows": settings.max_query_rows,
            "sql_timeout_ms": settings.query_timeout_ms,
            "tool_rounds": settings.max_tool_rounds,
            "sql_errors": settings.max_sql_errors,
        },
        "packages": {
            p: importlib.metadata.version(p) for p in ["google-genai", "psycopg", "pglast", "Faker"]
        },
    }


async def run_cases(cases, agent, references, output, interval, *, limit=20):
    records, stop_reason = [], None
    last_call = None
    try:
        with (output / "cases.jsonl").open("x", encoding="utf-8") as stream:
            for case in cases:
                if len(records) >= limit:
                    stop_reason = "case_limit"
                    break
                history, turns = [], []
                for index, turn in enumerate(case.turns):
                    if last_call is not None:
                        await asyncio.sleep(max(0, interval - (time.monotonic() - last_call)))
                    trace = {}
                    started = last_call = time.monotonic()
                    answer, new_turn = await agent.answer(turn.question, history, trace=trace)
                    elapsed_ms = (time.monotonic() - started) * 1000
                    history.extend(new_turn)
                    expected = {
                        r.metric: references[(case.id, index, r.metric)] for r in turn.references
                    }
                    turns.append(
                        {
                            "question": turn.question,
                            "expected": turn.expected,
                            "answer": answer,
                            "elapsed_ms": elapsed_ms,
                            "trace": trace,
                            "references": expected,
                            "passed": score_turn(turn, trace, expected),
                        }
                    )
                    if trace.get("status") == "provider_error":
                        stop_reason = f"provider_error_{trace.get('provider_code')}"
                        break
                    if trace.get("status") == "transport_error":
                        stop_reason = "transport_error"
                        break
                record = {
                    "id": case.id,
                    "turns": turns,
                    "passed": len(turns) == len(case.turns) and all(t["passed"] for t in turns),
                }
                records.append(record)
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
                print(f"{case.id}: {'correto' if record['passed'] else 'falha'}", flush=True)
                if stop_reason:
                    break
    except BaseException:
        stop_reason = "interrupted_or_internal_error"
        raise
    finally:
        summary = summarize(cases, records, stop_reason)
        (output / "summary.json").write_text(dump(summary), encoding="utf-8")
        (output / "summary.md").write_text(
            "# Resultado da avaliação\n\n```json\n" + dump(summary) + "\n```\n\n"
            "Uma rodada incompleta não permite concluir a hipótese. Latência sem transporte Telegram.\n",
            encoding="utf-8",
        )
    return summary


def create_output(root):
    path = (
        root
        / ".local"
        / "evaluation"
        / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    )
    path.mkdir(parents=True, exist_ok=False)
    return path
