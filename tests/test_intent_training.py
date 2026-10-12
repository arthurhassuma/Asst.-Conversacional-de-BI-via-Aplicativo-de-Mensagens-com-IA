import copy
from pathlib import Path

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.intent_classifier import IntentClassifier, select_examples
from training.corpus import load_corpus
from training.fit import fit_model


@pytest.fixture(scope="module")
def trained():
    rows = load_corpus(Path("training/questions-v1.json"))
    return rows, *fit_model(rows)


def test_fit_does_not_learn_validation_or_test_vocabulary():
    rows = copy.deepcopy(load_corpus(Path("training/questions-v1.json")))
    for row in rows:
        if row["split"] != "train":
            row["question"] += " palavraineditadeavaliacao"
    artifact, report = fit_model(rows)
    assert "palavraineditadeavaliacao" not in artifact["vocabulary"]
    assert "test" not in report


def test_exported_inference_matches_sklearn(trained):
    rows, artifact, report = trained
    train = [r for r in rows if r["split"] == "train"]
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2))),
            (
                "classifier",
                LogisticRegression(C=report["selected_C"], max_iter=1000, random_state=42),
            ),
        ]
    )
    model.fit([r["question"] for r in train], [r["label"] for r in train])
    texts = [
        "Ranking de clientes em março de 2026",
        "Horas realizadas versus previstas",
        "Faturamento de agosto de 2026 comparado a agosto de 2025",
        "",
        "texto inexistente",
    ]
    expected = model.predict_proba(texts)
    local = IntentClassifier(artifact)
    actual = [
        [local.predict(t)["probabilities"][label] for label in artifact["classes"]] for t in texts
    ]
    np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=1e-10)
    assert report["validation"]["samples"] == 28


@pytest.mark.parametrize("field", ["idf", "coef", "classes", "threshold"])
def test_invalid_artifact_is_rejected(trained, field):
    artifact = copy.deepcopy(trained[1])
    artifact[field] = [float("nan")] if field != "threshold" else float("inf")
    with pytest.raises(ValueError):
        IntentClassifier(artifact)


def test_selected_examples_never_include_reserved_rows(trained):
    rows = trained[0]
    examples = select_examples(rows, "comparacao")
    assert len(examples) == 2 and all(r["split"] == "train" for r in examples)
    assert not select_examples(rows, "generica")
