from decimal import Decimal
from pathlib import Path

import pytest

from evaluation.dataset import load_dataset
from evaluation.runner import run_cases, score_turn, summarize
from evaluation.scoring import compare_rows


def test_decimal_equivalence_preserves_precision_and_rejects_near_values():
    assert compare_rows([["1.2300"]], [[Decimal("1.23")]], ["number"], ordered=True)
    assert not compare_rows([["1.230001"]], [["1.23"]], ["number"], ordered=True)
    assert not compare_rows([[None]], [[0]], ["number"], ordered=True)
    assert not compare_rows([[True]], [[1]], ["number"], ordered=True)


def test_unordered_rows_preserve_duplicates_and_text_is_not_numeric():
    assert compare_rows([[2], [1]], [[1], [2]], ["number"], ordered=False)
    assert not compare_rows([[1], [1]], [[1], [2]], ["number"], ordered=False)
    assert not compare_rows([[2], [1]], [[1], [2]], ["number"], ordered=True)
    assert not compare_rows([["001"]], [["1"]], ["text"], ordered=False)
    assert not compare_rows([[1, 2]], [[1]], ["number"], ordered=False)


@pytest.mark.parametrize("invalid", ["NaN", "Infinity", "abc", float("nan")])
def test_invalid_numbers_never_match(invalid):
    assert not compare_rows([[invalid]], [[invalid]], ["number"], ordered=True)


def test_dataset_is_complete_stratified_and_contains_only_valid_reference_selects():
    dataset = load_dataset(Path("evaluation/cases.json"))
    assert len(dataset.cases) == 40
    assert len({case.id for case in dataset.cases}) == 40
    for split in ("development", "test"):
        cases = [case for case in dataset.cases if case.split == split]
        assert len(cases) == 20
        assert sum(case.turns[-1].expected == "answer" for case in cases) == 16
        assert sum(case.turns[-1].expected.startswith("clarification") for case in cases) == 4
        assert {r.metric for c in cases for t in c.turns for r in t.references} >= {
            "faturamento",
            "recebimentos",
            "pedidos",
            "contratos",
            "clientes",
            "horas",
            "chamados",
        }


def test_autopecas_dataset_adapts_the_original_inside_the_profile_data_range():
    import re

    dataset = load_dataset(Path("evaluation/cases-autopecas.json"))
    original = load_dataset(Path("evaluation/cases.json"))
    assert (dataset.version, dataset.seed, dataset.clients) == ("3.1.0", 42, 100)
    assert [c.id for c in dataset.cases] == [c.id for c in original.cases]
    for split in ("development", "test"):
        cases = [c for c in dataset.cases if c.split == split]
        outcomes = [c.turns[-1].expected for c in cases]
        assert len(cases) == 20
        assert outcomes.count("answer") == 16
        assert sum(o.startswith("clarification") for o in outcomes) == 3
        assert outcomes.count("unsupported_request") == 1
    # Só D17 e T20 mudam de categoria: os demais casos mantêm o desenho do conjunto original.
    changed = {c.id for c, o in zip(dataset.cases, original.cases, strict=True) if c.category != o.category}
    assert changed == {"D17", "T20"}
    # As datas de referência ficam na faixa carregada (jan/2025 a out/2026). Exceções: cadastro de
    # clientes (desde 2022) e os casos de ausência/zero, que usam anos propositalmente vazios.
    for case in dataset.cases:
        if case.category in {"sem_dados", "zero_explicito"}:
            continue
        for turn in case.turns:
            for ref in turn.references:
                if "cadastrado_em" in ref.sql:
                    continue
                years = {int(y) for y in re.findall(r"DATE '(\d{4})-", ref.sql)}
                assert years <= {2025, 2026}, (case.id, years)


def test_autopecas_second_reserved_partition_mirrors_the_categories_inside_the_data_range():
    import re

    dataset = load_dataset(Path("evaluation/cases-autopecas-reservado-2.json"))
    original = load_dataset(Path("evaluation/cases-autopecas.json"))
    assert (dataset.version, dataset.seed, dataset.clients) == ("1.0.0", 42, 100)
    assert [c.id for c in dataset.cases] == [f"T{n}" for n in range(41, 61)]
    assert {c.split for c in dataset.cases} == {"test"}
    outcomes = [c.turns[-1].expected for c in dataset.cases]
    assert outcomes.count("answer") == 16
    assert sum(o.startswith("clarification") for o in outcomes) == 3
    assert outcomes.count("unsupported_request") == 1
    # Mesmas categorias do reservado original do conjunto A, em instâncias novas.
    reserved = [c for c in original.cases if c.split == "test"]
    assert sorted(c.category for c in dataset.cases) == sorted(c.category for c in reserved)
    # Nenhuma pergunta repete as do conjunto A.
    seen = {t.question for c in original.cases for t in c.turns}
    assert not seen & {t.question for c in dataset.cases for t in c.turns}
    for case in dataset.cases:
        if case.category in {"sem_dados", "zero_explicito"}:
            continue
        for turn in case.turns:
            for ref in turn.references:
                if "cadastrado_em" in ref.sql:
                    continue
                years = {int(y) for y in re.findall(r"DATE '(\d{4})-", ref.sql)}
                assert years <= {2025, 2026, 2027}, (case.id, years)


def test_score_rejects_truncation_extra_metrics_and_wrong_selected_result():
    turn = load_dataset(Path("evaluation/cases.json")).cases[0].turns[0]
    result = {"columns": ["total"], "rows": [["100.00"]], "truncated": False}
    query = {"plan": {"metric": "faturamento"}, "selected": result}
    trace = {"status": "answer", "queries": [query]}
    references = {"faturamento": result.copy()}
    assert score_turn(turn, trace, references)
    query["selected"] = {**result, "truncated": True}
    assert not score_turn(turn, trace, references)
    query["selected"] = {**result, "rows": [[101]]}
    query["attempts"] = [{"result": result}]
    assert not score_turn(turn, trace, references)
    query["selected"] = result
    trace["queries"].append(query)
    assert not score_turn(turn, trace, references)


async def test_quota_stops_run_preserves_checkpoint_and_no_official_rate(tmp_path):
    dataset = load_dataset(Path("evaluation/cases.json"))
    cases = dataset.cases[:2]

    class QuotaAgent:
        calls = 0

        async def answer(self, question, history, *, trace):
            self.calls += 1
            trace.update(status="provider_error", provider_code=429, queries=[])
            return "Cota atingida.", []

    refs = {(c.id, 0, r.metric): {"rows": [[1]]} for c in cases for r in c.turns[0].references}
    agent = QuotaAgent()
    result = await run_cases(cases, agent, refs, tmp_path, 0)
    assert agent.calls == 1
    assert result["stop_reason"] == "provider_error_429"
    assert result["not_run"] == [cases[1].id]
    assert result["metrics"]["execution_accuracy"]["rate"] is None
    assert (tmp_path / "cases.jsonl").read_text(encoding="utf-8").count("\n") == 1


def test_summary_does_not_hide_missing_cases_from_denominator():
    cases = load_dataset(Path("evaluation/cases.json")).cases[:2]
    result = summarize(cases, [{"id": cases[0].id, "passed": True, "turns": []}], "case_limit")
    assert result["metrics"]["execution_accuracy"] == {
        "planned": 2,
        "completed": 1,
        "passed": 1,
        "rate": None,
    }


def test_analysis_auxiliary_count_is_validated_and_does_not_change_answer_columns():
    turn = load_dataset(Path("evaluation/cases.json")).cases[0].turns[0]
    result = {"columns": ["total", "registros"], "rows": [["100.00", 2]], "truncated": False}
    query = {"plan": {"metric": "faturamento"}, "selected": result, "template": False}
    trace = {"status": "answer", "queries": [query]}
    refs = {"faturamento": {"rows": [["100.00"]]}}
    assert score_turn(turn, trace, refs)
    result["rows"][0][1] = 0
    assert not score_turn(turn, trace, refs)
    result["rows"][0][1] = "2"
    assert not score_turn(turn, trace, refs)


def test_failed_final_database_verification_invalidates_saved_rate(tmp_path, monkeypatch):
    from scripts import evaluate

    def fail(database):
        raise ValueError("Base indisponível")

    monkeypatch.setattr(evaluate, "database_fingerprint", fail)
    summary = {"complete": True, "metrics": {"execution_accuracy": {"rate": 1}}}
    with pytest.raises(ValueError):
        evaluate.verify_database(None, {"database": {}}, tmp_path, summary)
    assert summary["complete"] is False
    assert summary["metrics"]["execution_accuracy"]["rate"] is None
    assert "database_verification_failed" in (tmp_path / "summary.json").read_text()
