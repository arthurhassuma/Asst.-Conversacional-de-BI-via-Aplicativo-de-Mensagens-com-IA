import os
import sys

import pytest

import runtime_entrypoint


@pytest.mark.parametrize(("value", "expected"), [("true", True), ("false", False)])
def test_backend_honours_the_classifier_flag_from_the_private_file(
    tmp_path, monkeypatch, value, expected
):
    config = tmp_path / "application.env"
    config.write_text(
        f"INTENT_CLASSIFIER_ENABLED={value}\nADMIN_DATABASE_URL=postgresql://admin\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PAC_CONFIG_FILE", str(config))
    monkeypatch.setattr(sys, "argv", ["runtime_entrypoint.py", "backend"])
    monkeypatch.setattr(os, "environ", dict(os.environ))
    settings, mode = runtime_entrypoint.configured()
    assert mode == "backend"
    assert settings.intent_classifier_enabled is expected
    assert os.environ["INTENT_CLASSIFIER_ENABLED"] == str(expected)
    assert settings.admin_database_url.get_secret_value() == ""


def test_classifier_is_on_when_the_private_file_does_not_mention_it(tmp_path, monkeypatch):
    config = tmp_path / "application.env"
    config.write_text("GEMINI_MODEL=gemini-3.5-flash-lite\n", encoding="utf-8")
    monkeypatch.setenv("PAC_CONFIG_FILE", str(config))
    monkeypatch.setattr(sys, "argv", ["runtime_entrypoint.py", "polling"])
    monkeypatch.setattr(os, "environ", dict(os.environ))
    settings, _ = runtime_entrypoint.configured()
    assert settings.intent_classifier_enabled is True


def _backend_args(tmp_path, monkeypatch, text):
    config = tmp_path / "application.env"
    config.write_text(text, encoding="utf-8")
    monkeypatch.setenv("PAC_CONFIG_FILE", str(config))
    monkeypatch.setattr(sys, "argv", ["runtime_entrypoint.py", "backend"])
    monkeypatch.setattr(os, "environ", dict(os.environ))
    captured = {}
    monkeypatch.setattr(os, "execv", lambda exe, argv: captured.setdefault("argv", argv))
    runtime_entrypoint.main()
    return captured["argv"]


def test_backend_runs_a_single_worker_by_default(tmp_path, monkeypatch):
    argv = _backend_args(tmp_path, monkeypatch, "GEMINI_MODEL=gemini-3.5-flash-lite\n")
    assert argv[argv.index("--workers") + 1] == "1"


def test_backend_accepts_several_workers_with_durable_state(tmp_path, monkeypatch):
    argv = _backend_args(
        tmp_path,
        monkeypatch,
        "BACKEND_WORKERS=3\nSTATE_DATABASE_URL=postgresql://app_estado:x@db/bi\n",
    )
    assert argv[argv.index("--workers") + 1] == "3"


def test_several_workers_without_durable_state_are_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        _backend_args(tmp_path, monkeypatch, "BACKEND_WORKERS=2\n")


def test_state_password_is_removed_outside_manage_db(tmp_path, monkeypatch):
    config = tmp_path / "application.env"
    config.write_text("STATE_PASSWORD=segredo-administrativo\n", encoding="utf-8")
    monkeypatch.setenv("PAC_CONFIG_FILE", str(config))
    monkeypatch.setattr(os, "environ", dict(os.environ))
    monkeypatch.setattr(sys, "argv", ["runtime_entrypoint.py", "backend"])
    settings, _ = runtime_entrypoint.configured()
    assert settings.state_password.get_secret_value() == ""
    os.environ.pop("STATE_PASSWORD", None)
    monkeypatch.setattr(sys, "argv", ["runtime_entrypoint.py", "manage-db", "init-state"])
    settings, _ = runtime_entrypoint.configured()
    assert settings.state_password.get_secret_value() == "segredo-administrativo"
