"""Corpus com separação por cenário, nunca por paráfrase individual."""

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

LABELS = ("total", "comparacao", "tendencia", "ranking", "segmentacao", "operacional", "generica")
FIELDS = {"id", "question", "label", "group_id", "split"}


def normalize(text: str) -> str:
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c)
    )
    return re.sub(r"\W+", " ", text).strip()


def validate_corpus(records: list[dict]) -> dict:
    if not isinstance(records, list) or not records:
        raise ValueError("O corpus deve conter perguntas rotuladas.")
    ids, questions, groups = set(), set(), {}
    for row in records:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("Campos inválidos no corpus.")
        if not all(isinstance(v, str) and v.strip() for v in row.values()):
            raise ValueError("Os campos do corpus devem ser textos não vazios.")
        if row["label"] not in LABELS or row["split"] not in {"train", "validation", "test"}:
            raise ValueError("Classe ou partição inválida.")
        question = normalize(row["question"])
        if row["id"] in ids or question in questions:
            raise ValueError("Pergunta ou identificador duplicado.")
        if len(row["question"]) > 4000:
            raise ValueError("Pergunta extensa demais.")
        key = (row["label"], row["split"])
        if groups.setdefault(row["group_id"], key) != key:
            raise ValueError("Um grupo não pode pertencer a classes ou partições diferentes.")
        ids.add(row["id"])
        questions.add(question)
    classes = Counter(r["label"] for r in records)
    splits = Counter(r["split"] for r in records)
    if set(classes) != set(LABELS):
        raise ValueError("O corpus deve incluir todas as classes.")
    for label in LABELS:
        if {r["split"] for r in records if r["label"] == label} != {"train", "validation", "test"}:
            raise ValueError("Cada classe precisa de treino, validação e teste.")
    return {"classes": dict(classes), "splits": dict(splits), "groups": len(groups)}


def load_corpus(path: Path) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    validate_corpus(records)
    return records
