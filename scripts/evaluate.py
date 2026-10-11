"""Validação offline e avaliação real opt-in; nunca imprime credenciais."""

import argparse
import asyncio
from pathlib import Path

import psycopg

from app.bi_agent import BIAgent
from app.config import Settings
from app.database_tools import DatabaseTools
from evaluation.dataset import load_dataset
from evaluation.runner import (
    create_output,
    database_fingerprint,
    dump,
    manifest,
    run_cases,
    validate_references,
)


def verify_database(database, evidence, output, summary):
    reason = "database_verification_failed"
    try:
        after = database_fingerprint(database)
        unchanged = after == evidence["database"]
        (output / "database_after.json").write_text(
            dump({"unchanged": unchanged, "tables": after}), encoding="utf-8"
        )
        reason = None if unchanged else "database_changed"
    finally:
        if reason:
            summary.update(complete=False, stop_reason=reason)
            for metric in summary["metrics"].values():
                metric["rate"] = None
            (output / "summary.json").write_text(dump(summary), encoding="utf-8")
            (output / "summary.md").write_text(
                "# Rodada inválida: verificação da base\n\n```json\n" + dump(summary) + "\n```\n",
                encoding="utf-8",
            )


async def execute(args):
    root = Path(__file__).resolve().parents[1]
    path = root / "evaluation" / "cases.json"
    dataset = load_dataset(path)
    settings = Settings(_env_file=args.env_file)
    database = DatabaseTools(settings)
    references = validate_references(dataset, database)
    print(f"{len(references)} referências SQL validadas; nenhuma chamada ao Gemini nesta etapa.")
    if args.command == "validate":
        return 0
    if not args.live or not settings.gemini_api_key.get_secret_value():
        raise ValueError("Informe --live e configure GEMINI_API_KEY no ambiente local.")
    if args.interval < 0 or args.limit < 1:
        raise ValueError("Intervalo deve ser não negativo e limite deve ser positivo.")
    cases = [c for c in dataset.cases if c.split == args.split]
    # Mantém o denominador completo; limite é um teto de chamadas, não troca de amostra.
    output = create_output(root)
    evidence = manifest(root, path, dataset, settings, database, args.split)
    evidence.update(interval_seconds=args.interval, case_limit=args.limit)
    (output / "manifest.json").write_text(dump(evidence), encoding="utf-8")
    print(f"Evidências: {output}", flush=True)
    agent = BIAgent(settings, database=database)
    try:
        summary = await run_cases(cases, agent, references, output, args.interval, limit=args.limit)
        verify_database(database, evidence, output, summary)
    finally:
        await agent.close()
    return 0 if summary["complete"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "run"])
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--split", choices=["development", "test"], default="development")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--interval", type=float, default=12)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    try:
        code = asyncio.run(execute(args))
    except (ValueError, OSError, psycopg.Error):
        parser.exit(
            1,
            "Avaliação interrompida. Confira configuração, referências e acesso local ao banco; credenciais não são exibidas.\n",
        )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
