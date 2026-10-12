from pathlib import Path
from types import SimpleNamespace

from evaluation.dataset import load_dataset
from evaluation.runner import summarize


def test_managerial_dataset_has_distinct_ids_and_35_scenarios():
    old = load_dataset(Path("evaluation/cases.json"))
    new = load_dataset(Path("evaluation/managerial-cases-v1.json"))
    assert len(new.cases) == 35
    assert not {c.id for c in old.cases} & {c.id for c in new.cases}
    assert sum(c.split == "development" for c in new.cases) == 25
    assert sum(c.split == "test" for c in new.cases) == 10
    assert any(c.turns[-1].expected == "unsupported_request" for c in new.cases)


def test_unsupported_results_have_a_separate_denominator():
    cases = [
        SimpleNamespace(id="D21", turns=[SimpleNamespace(expected="unsupported_request")]),
        SimpleNamespace(id="D22", turns=[SimpleNamespace(expected="clarification_period")]),
    ]
    records = [{"id": c.id, "passed": True, "turns": [{"elapsed_ms": 1}]} for c in cases]
    summary = summarize(cases, records, None)
    assert summary["metrics"]["unsupported_accuracy"]["planned"] == 1
    assert summary["metrics"]["clarification_accuracy"]["planned"] == 1
