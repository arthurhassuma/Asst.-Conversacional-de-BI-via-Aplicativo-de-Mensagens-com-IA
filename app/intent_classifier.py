"""Inferência TF-IDF/logística do artefato aprendido; não consulta banco ou IA."""

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

from training.corpus import LABELS


class IntentClassifier:
    def __init__(self, artifact: dict):
        try:
            self.classes = artifact["classes"]
            self.vocabulary = artifact["vocabulary"]
            self.idf = artifact["idf"]
            self.coef = artifact["coef"]
            self.intercept = artifact["intercept"]
            self.threshold = artifact["threshold"]
            n = len(self.vocabulary)
            valid = (
                artifact["schema_version"] == "intent-v1"
                and artifact["vectorizer"]
                == {
                    "ngram_range": [1, 2],
                    "strip_accents": "unicode",
                    "lowercase": True,
                    "norm": "l2",
                }
                and len(self.classes) == len(LABELS)
                and set(self.classes) == set(LABELS)
                and 1 <= n <= 100000
                and set(self.vocabulary.values()) == set(range(n))
                and all(isinstance(k, str) for k in self.vocabulary)
                and len(self.idf) == n
                and len(self.coef) == len(self.classes)
                and all(len(row) == n for row in self.coef)
                and len(self.intercept) == len(self.classes)
                and 0 <= self.threshold <= 1
                and all(
                    math.isfinite(v)
                    for values in [self.idf, self.intercept, *self.coef]
                    for v in values
                )
                and all(v > 0 for v in self.idf)
            )
            if not valid:
                raise ValueError
        except (KeyError, TypeError, ValueError, OverflowError):
            raise ValueError("Artefato de intenções inválido ou incompatível.") from None
        self.sha256 = hashlib.sha256(json.dumps(artifact, sort_keys=True).encode()).hexdigest()

    def predict(self, text: str) -> dict:
        text = "".join(
            c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c)
        )
        words = re.findall(r"(?u)\b\w\w+\b", text)
        features = Counter(words + [" ".join(pair) for pair in zip(words, words[1:])])
        vector = {
            self.vocabulary[k]: count * self.idf[self.vocabulary[k]]
            for k, count in features.items()
            if k in self.vocabulary
        }
        norm = math.sqrt(math.fsum(v * v for v in vector.values()))
        if norm:
            vector = {i: v / norm for i, v in vector.items()}
        logits = [
            b + math.fsum(row[i] * v for i, v in vector.items())
            for row, b in zip(self.coef, self.intercept, strict=True)
        ]
        highest = max(logits)
        exp = [math.exp(v - highest) for v in logits]
        denominator = math.fsum(exp)
        probabilities = dict(zip(self.classes, [v / denominator for v in exp], strict=True))
        label = max(probabilities, key=probabilities.get)
        confidence = probabilities[label]
        return {
            "label": label,
            "confidence": confidence,
            "probabilities": probabilities,
            "accepted": label != "generica" and confidence >= self.threshold,
        }


def load_classifier(path: Path) -> IntentClassifier:
    if path.stat().st_size > 10000000:
        raise ValueError("Artefato de intenções extenso demais.")
    return IntentClassifier(json.loads(path.read_text(encoding="utf-8")))


def select_examples(records: list[dict], label: str, limit: int = 2) -> list[dict]:
    if label == "generica" or label not in LABELS:
        return []
    return sorted(
        [r for r in records if r["split"] == "train" and r["label"] == label], key=lambda r: r["id"]
    )[: max(0, min(limit, 2))]


def intent_context(question: str, history: list) -> str:
    if re.match(r"(?i)^\s*(e\b|agora\b|também\b|no outro\b|\w+ de \d{4}\s*$)", question):
        previous = [
            m["content"][:4000]
            for m in history
            if m.get("role") == "user" and isinstance(m.get("content"), str)
        ][-2:]
        return "\n".join(previous + [question])
    return question
