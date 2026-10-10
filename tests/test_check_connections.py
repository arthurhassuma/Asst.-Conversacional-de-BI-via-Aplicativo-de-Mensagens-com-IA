"""Diagnóstico operacional: configuração não deve ser confundida com acesso real."""

import json

import httpx
import pytest
from pydantic import SecretStr
from telegram import Bot
from telegram.request import HTTPXRequest

from app.config import Settings
from app.sql_policy import TABLES
from scripts import check_connections as diagnostic
from tests.test_gemini_transport import sdk_client


def configured():
    return Settings(
        _env_file=None,
        database_url="postgresql://readonly_agent:senha-local-privada@localhost/bi",
        gemini_api_key="segredo-gemini",
        telegram_bot_token="123456:segredo-telegram",
        telegram_webhook_secret="segredo-webhook-valido",
        telegram_allowed_user_ids="42",
    )


async def test_default_checks_configuration_without_network(monkeypatch):
    async def forbidden(*args):
        pytest.fail("Diagnóstico sem opção explícita não pode acessar a rede.")

    for name in ("check_database", "check_gemini", "check_telegram"):
        monkeypatch.setattr(diagnostic, name, forbidden)
    report = await diagnostic.diagnose(configured())
    assert all(item["status"] == "configurado" for item in report.values())
    assert "confirmado" not in json.dumps(report)
    assert all(
        value not in json.dumps(report)
        for value in (
            "senha-local-privada",
            "segredo-gemini",
            "segredo-telegram",
            "segredo-webhook-valido",
            "segredo-na-excecao",
        )
    )


async def test_invalid_and_missing_configuration_never_calls_providers(monkeypatch):
    async def forbidden(*args):
        pytest.fail("Credenciais ausentes não podem disparar chamadas.")

    for name in ("check_database", "check_gemini", "check_telegram"):
        monkeypatch.setattr(diagnostic, name, forbidden)
    # _env_file=None desativa apenas dotenv, não as variáveis do processo/CI.
    monkeypatch.setenv("DATABASE_URL", "postgresql://configuracao-ambiente/bi")
    report = await diagnostic.diagnose(
        Settings(
            _env_file=None,
            database_url="",
            gemini_api_key="",
            telegram_bot_token="",
            telegram_webhook_secret="",
            telegram_allowed_user_ids="id-invalido",
        ),
        test_connections=True,
    )
    assert all(item["status"] == "pendente" for item in report.values())


async def test_probes_use_native_apis_without_messages_or_webhook_changes(monkeypatch):
    routes = []

    def gemini_api(request):
        routes.append(request.url.path)
        body = json.loads(request.content)
        assert not body.get("tools")
        assert "postgresql" not in str(body)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"role": "model", "parts": [{"text": "Conexão verificada."}]},
                        "finishReason": "STOP",
                    }
                ]
            },
        )

    def telegram_api(request):
        assert request.url.path.endswith("/getMe")
        routes.append("getMe")
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "id": 100,
                    "is_bot": True,
                    "first_name": "BI",
                    "username": "teste_bot",
                },
            },
        )

    client = sdk_client(gemini_api)
    monkeypatch.setattr(diagnostic.genai, "Client", lambda **kw: client)
    request = HTTPXRequest(httpx_kwargs={"transport": httpx.MockTransport(telegram_api)})
    monkeypatch.setattr(diagnostic, "Bot", lambda token: Bot(token, request=request))
    monkeypatch.setattr(
        diagnostic.DatabaseTools,
        "get_schema",
        lambda self: {
            "tables": {name: [{"column": "id"}] for name in TABLES},
        },
    )
    report = await diagnostic.diagnose(configured(), test_connections=True)
    assert all(report[name]["status"] == "confirmado" for name in ("banco", "gemini", "telegram"))
    assert report["acesso_telegram"]["status"] == "configurado"
    assert sum(path.endswith(":generateContent") for path in routes) == 1
    assert routes.count("getMe") == 1
    assert all(
        value not in json.dumps(report)
        for value in (
            "senha-local-privada",
            "segredo-gemini",
            "segredo-telegram",
            "segredo-webhook-valido",
            "segredo-na-excecao",
        )
    )


async def test_quota_error_and_incomplete_schema_are_not_reported_as_connected(monkeypatch):
    client = sdk_client(
        lambda request: httpx.Response(
            429,
            json={
                "error": {"code": 429, "message": "segredo-na-excecao"},
            },
        )
    )
    monkeypatch.setattr(diagnostic.genai, "Client", lambda **kw: client)
    monkeypatch.setattr(diagnostic.DatabaseTools, "get_schema", lambda self: {"tables": {}})
    settings = configured().model_copy(update={"telegram_bot_token": SecretStr("")})
    report = await diagnostic.diagnose(settings, test_connections=True)
    assert report["gemini"]["status"] == "falhou"
    assert "cota" in report["gemini"]["detalhe"]
    assert report["banco"]["status"] == "falhou"
    assert report["telegram"]["status"] == "pendente"
    assert all(
        value not in json.dumps(report)
        for value in (
            "senha-local-privada",
            "segredo-gemini",
            "segredo-telegram",
            "segredo-webhook-valido",
            "segredo-na-excecao",
        )
    )
