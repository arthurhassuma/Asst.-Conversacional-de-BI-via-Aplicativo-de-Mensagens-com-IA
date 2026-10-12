import json
from pathlib import Path

import pytest

from app.intent_classifier import intent_context, load_classifier


def test_missing_or_invalid_model_is_not_deserialized(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_classifier(tmp_path / "missing.json")
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"schema_version": "other"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_classifier(path)


def test_context_uses_only_recent_user_text_for_followup():
    history = [
        {"role": "user", "content": "Faturamento em agosto de 2025"},
        {"role": "assistant", "content": "Resultado 123"},
        {"role": "user", "content": {"tool": "não deve entrar"}},
    ]
    context = intent_context("E em agosto de 2026?", history)
    assert "2025" in context and "2026" in context
    assert "123" not in context and "tool" not in context
    assert intent_context("Ranking de clientes em 2026", history) == "Ranking de clientes em 2026"


def test_packaged_artifact_has_probabilities_without_runtime_sklearn():
    result = load_classifier(Path("training/intent-model-v1.json")).predict("texto desconhecido")
    assert sum(result["probabilities"].values()) == pytest.approx(1)
    assert 0 <= result["confidence"] <= 1
