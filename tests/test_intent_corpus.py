import copy
from pathlib import Path

import pytest

from training.corpus import load_corpus, validate_corpus

PATH = Path("training/questions-v1.json")


def test_corpus_is_balanced_and_groups_are_disjoint():
    report = validate_corpus(load_corpus(PATH))
    assert report["splits"] == {"train": 196, "validation": 28, "test": 56}
    assert len(report["classes"]) == 7
    assert set(report["classes"].values()) == {40}


@pytest.mark.parametrize("mutation", ["duplicate", "group", "label", "extra"])
def test_corpus_rejects_leaks_and_invalid_records(mutation):
    rows = copy.deepcopy(load_corpus(PATH))
    if mutation == "duplicate":
        rows[1]["question"] = rows[0]["question"].upper()
    elif mutation == "group":
        rows[1]["split"] = "test" if rows[0]["split"] != "test" else "train"
    elif mutation == "label":
        rows[0]["label"] = "desconhecida"
    else:
        rows[0]["sql"] = "SELECT 1"
    with pytest.raises(ValueError):
        validate_corpus(rows)
