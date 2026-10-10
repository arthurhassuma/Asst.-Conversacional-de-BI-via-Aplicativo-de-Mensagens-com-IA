"""Integração de engenharia, não avaliação acadêmica nem prova de Telegram real."""

import json
import os
from urllib.parse import parse_qs

import httpx
import psycopg
import pytest
from telegram import Bot
from telegram.request import HTTPXRequest

from app.bi_agent import BIAgent
from app.config import Settings
from app.main import create_app
from tests.test_agent import call, response
from tests.test_backend import update
from tests.test_gemini_transport import sdk_client, wire


@pytest.mark.integration
async def test_webhook_to_postgres_to_telegram_with_simulated_external_apis():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Requer PostgreSQL real em TEST_DATABASE_URL.")
    settings = Settings(
        _env_file=None,
        database_url=dsn,
        telegram_webhook_secret="local-test",
        telegram_allowed_user_ids="42",
    )
    with psycopg.connect(dsn, connect_timeout=5) as conn:
        expected = conn.execute(
            "SELECT count(*) FROM clientes WHERE cadastrado_em >= %s AND cadastrado_em < %s",
            ("2023-01-01", "2024-01-01"),
        ).fetchone()[0]
    responses = iter(
        [
            response(
                {
                    "metric": "clientes",
                    "measure": "quantidade",
                    "period": {"start": "2023-01-01", "end": "2024-01-01", "evidence": "2023"},
                }
            ),
            response(tools=[call("get_schema", {})]),
            response(
                tools=[
                    call(
                        "execute_sql",
                        {
                            "sql": "SELECT count(*) AS total FROM clientes WHERE cadastrado_em >= DATE '2023-01-01' AND cadastrado_em < DATE '2024-01-01'"
                        },
                        "t2",
                    )
                ]
            ),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    model_requests, telegram_messages = [], []

    def gemini_api(request):
        model_requests.append(json.loads(request.content))
        return httpx.Response(200, json=wire(next(responses)))

    def telegram_api(request):
        if request.url.path.endswith("/getMe"):
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": {
                        "id": 100,
                        "is_bot": True,
                        "first_name": "BI",
                        "username": "bi_test_bot",
                    },
                },
            )
        assert request.url.path.endswith("/sendMessage")
        fields = parse_qs(request.content.decode())
        telegram_messages.append(fields["text"][0])
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 1,
                    "date": 0,
                    "chat": {"id": 42, "type": "private"},
                    "text": fields["text"][0],
                },
            },
        )

    client = sdk_client(gemini_api)
    request = HTTPXRequest(httpx_kwargs={"transport": httpx.MockTransport(telegram_api)})
    async with Bot("123456:token-ficticio", request=request) as bot:
        app = create_app(settings, agent=BIAgent(settings, client=client), sender=bot)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url="http://test"
            ) as http:
                result = await http.post(
                    "/telegram/webhook",
                    json=update(text="Quantos clientes em 2023?"),
                    headers={"X-Telegram-Bot-Api-Secret-Token": "local-test"},
                )
                assert result.status_code == 200
                await app.state.queue.join()
    assert telegram_messages == [
        f"No período informado, o resultado para quantidade de clientes é {expected}."
    ]
    tool_result = model_requests[-1]["contents"][-1]["parts"][0]["functionResponse"]
    assert tool_result["response"]["rows"] == [[expected]]
