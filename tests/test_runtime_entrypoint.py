"""O entrypoint do container deve respeitar a configuração privada do classificador."""

import os
import sys

import pytest

import runtime_entrypoint


@pytest.mark.parametrize(("value", "expected"), [("true", True), ("false", False)])
def test_backend_honours_the_classifier_flag_from_the_private_file(
    tmp_path, monkeypatch, value, expected
):
    # Regressão: o entrypoint forçava False em todos os modos, e o valor do arquivo
    # privado nunca chegava ao backend, mesmo com o classificador v2 empacotado.
    config = tmp_path / "application.env"
    config.write_text(
        f"INTENT_CLASSIFIER_ENABLED={value}\nADMIN_DATABASE_URL=postgresql://admin\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PAC_CONFIG_FILE", str(config))
    monkeypatch.setattr(sys, "argv", ["runtime_entrypoint.py", "backend"])
    monkeypatch.setattr(os, "environ", dict(os.environ))  # configured() exporta variáveis
    settings, mode = runtime_entrypoint.configured()
    assert mode == "backend"
    assert settings.intent_classifier_enabled is expected
    assert os.environ["INTENT_CLASSIFIER_ENABLED"] == str(expected)
    # As credenciais administrativas continuam removidas dos modos de aplicação.
    assert settings.admin_database_url.get_secret_value() == ""


def test_classifier_is_on_when_the_private_file_does_not_mention_it(tmp_path, monkeypatch):
    config = tmp_path / "application.env"
    config.write_text("GEMINI_MODEL=gemini-3.5-flash-lite\n", encoding="utf-8")
    monkeypatch.setenv("PAC_CONFIG_FILE", str(config))
    monkeypatch.setattr(sys, "argv", ["runtime_entrypoint.py", "polling"])
    monkeypatch.setattr(os, "environ", dict(os.environ))
    settings, _ = runtime_entrypoint.configured()
    assert settings.intent_classifier_enabled is True
