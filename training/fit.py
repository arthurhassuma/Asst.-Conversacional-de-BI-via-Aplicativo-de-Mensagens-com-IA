"""Treino e seleção em validação; teste reservado é uma operação separada."""

import hashlib
import importlib.metadata
import json

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from app.intent_classifier import IntentClassifier
from training.corpus import LABELS, validate_corpus


def metrics(actual, predicted, *, accepted=None):
    return {
        "samples": len(actual),
        "accuracy": accuracy_score(actual, predicted),
        "macro_f1": f1_score(
            actual, predicted, labels=list(LABELS), average="macro", zero_division=0
        ),
        "per_class": classification_report(
            actual, predicted, labels=list(LABELS), output_dict=True, zero_division=0
        ),
        "matrix_labels": list(LABELS),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=list(LABELS)).tolist(),
        "coverage": sum(accepted) / len(actual) if accepted is not None else None,
        # Das sugestões aceitas, quantas acertaram a classe: o que decide se vale usar.
        "accepted_precision": (
            sum(a == p for a, p, ok in zip(actual, predicted, accepted, strict=True) if ok)
            / sum(accepted)
            if accepted is not None and sum(accepted)
            else None
        ),
    }


DEFAULT_C_GRID = (0.5, 1.0, 2.0)
DEFAULT_THRESHOLDS = (0.50, 0.60, 0.70)


def threshold_report(model, vx, vy, labels, threshold):
    """Desempenho na validação quando só se aceita sugestão com confiança >= limiar."""
    probability = model.predict_proba(vx)
    accepted = [
        (labels[row.argmax()] != "generica" and row.max() >= threshold) for row in probability
    ]
    predicted = [
        labels[row.argmax()] if ok else "generica"
        for row, ok in zip(probability, accepted, strict=True)
    ]
    return metrics(vy, predicted, accepted=accepted)


def fit_model(
    records: list[dict],
    seed: int = 42,
    c_grid: tuple[float, ...] = DEFAULT_C_GRID,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    joint: bool = False,
) -> tuple[dict, dict]:
    """Treina na partição de treino e escolhe hiperparâmetros só pela validação.

    Por padrão escolhe C pelo macro-F1 puro e depois o limiar (protocolo v1). Com
    ``joint`` escolhe C e limiar juntos pelo macro-F1 com abstenção, que já pune
    cobertura baixa; é o que importa quando as sugestões só são usadas acima do limiar.
    """
    validate_corpus(records)
    train = [r for r in records if r["split"] == "train"]
    validation = [r for r in records if r["split"] == "validation"]
    x, y = [r["question"] for r in train], [r["label"] for r in train]
    vx, vy = [r["question"] for r in validation], [r["label"] for r in validation]
    candidates = []
    for c in c_grid:
        model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2))),
                (
                    "classifier",
                    LogisticRegression(C=c, solver="lbfgs", max_iter=1000, random_state=seed),
                ),
            ]
        )
        model.fit(x, y)
        score = f1_score(
            vy, model.predict(vx), labels=list(LABELS), average="macro", zero_division=0
        )
        candidates.append((score, -c, model))
    labels = candidates[0][2].named_steps["classifier"].classes_.tolist()
    if joint:
        options = [
            (r["macro_f1"], r["coverage"], negative_c, t, negative_c, model, r)
            for score, negative_c, model in candidates
            for t in thresholds
            for r in [threshold_report(model, vx, vy, labels, t)]
        ]
        _, _, _, threshold, negative_c, model, accepted_report = max(
            options, key=lambda item: item[:4]
        )
        score = f1_score(
            vy, model.predict(vx), labels=list(LABELS), average="macro", zero_division=0
        )
    else:
        score, negative_c, model = max(candidates, key=lambda item: item[:2])
        results = [
            (r["macro_f1"], r["coverage"], t, r)
            for t in thresholds
            for r in [threshold_report(model, vx, vy, labels, t)]
        ]
        _, _, threshold, accepted_report = max(results, key=lambda item: item[:3])
    clf, vectorizer = model.named_steps["classifier"], model.named_steps["tfidf"]
    artifact = {
        "schema_version": "intent-v1",
        "classes": labels,
        "vocabulary": {k: int(v) for k, v in vectorizer.vocabulary_.items()},
        "idf": vectorizer.idf_.tolist(),
        "coef": clf.coef_.tolist(),
        "intercept": clf.intercept_.tolist(),
        "threshold": threshold,
        "vectorizer": {
            "ngram_range": [1, 2],
            "strip_accents": "unicode",
            "lowercase": True,
            "norm": "l2",
        },
        "seed": seed,
        "C": -negative_c,
        "corpus_sha256": hashlib.sha256(
            json.dumps(records, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
        "versions": {p: importlib.metadata.version(p) for p in ("scikit-learn", "numpy", "scipy")},
    }
    IntentClassifier(artifact)
    dummy = DummyClassifier(strategy="most_frequent").fit(x, y)
    return artifact, {
        "selected_C": -negative_c,
        "selected_threshold": threshold,
        "features": len(vectorizer.vocabulary_),
        "seed": seed,
        "corpus_sha256": artifact["corpus_sha256"],
        "versions": artifact["versions"],
        "train": metrics(y, model.predict(x)),
        "validation": metrics(vy, model.predict(vx)),
        "validation_with_abstention": accepted_report,
        "baseline_validation": metrics(vy, dummy.predict(vx)),
        "candidates": [{"C": -c, "macro_f1_validation": s} for s, c, _ in candidates],
    }


def evaluate_model(artifact: dict, records: list[dict], split: str) -> dict:
    if split not in {"validation", "test"}:
        raise ValueError("Avaliação aceita somente validação ou teste.")
    rows = [r for r in records if r["split"] == split]
    if not rows:
        raise ValueError("Partição de avaliação vazia.")
    model = IntentClassifier(artifact)
    predictions = [model.predict(r["question"]) for r in rows]
    y = [r["label"] for r in rows]
    accepted = [p["accepted"] for p in predictions]
    return {
        "split": split,
        "classifier": metrics(y, [p["label"] for p in predictions]),
        "with_abstention": metrics(
            y, [p["label"] if p["accepted"] else "generica" for p in predictions], accepted=accepted
        ),
        "baseline": metrics(y, ["comparacao"] * len(rows)),
        "model_sha256": model.sha256,
        "predictions": [
            {"id": r["id"], "expected": r["label"], **p}
            for r, p in zip(rows, predictions, strict=True)
        ],
    }
