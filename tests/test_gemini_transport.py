"""Exercita o SDK oficial na fronteira HTTP, sem gastar cota ou enviar dados."""

import base64
import json

import httpx
import pytest
from google import genai
from google.genai import types

from app.bi_agent import BIAgent
from app.config import Settings
from tests.test_agent import PLAN, Database, call, response


def sdk_client(handler):
    return genai.Client(
        vertexai=False,
        api_key="chave-ficticia",
        http_options=types.HttpOptions(
            httpx_async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def wire(value):
    return value.model_dump(mode="json", by_alias=True, exclude_none=True)


async def test_native_tools_preserve_signatures_parallel_results_and_exact_numbers():
    signed_call = {
        **call("get_schema", {}, "schema"),
        "thoughtSignature": base64.b64encode(b"opaque-signature").decode(),
    }
    responses = iter(
        [
            response(PLAN),
            response(tools=[signed_call]),
            response(
                tools=[
                    call("execute_sql", {"sql": "SELECT inexistente FROM faturamento"}, "sql-bad"),
                    call(
                        "execute_sql",
                        {"sql": "SELECT sum(valor) AS total FROM faturamento"},
                        "sql-good",
                    ),
                ]
            ),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    requests = []

    def receive(request):
        assert request.url.host == "generativelanguage.googleapis.com"
        assert request.url.path.endswith(":generateContent")
        assert "key=" not in str(request.url)
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=wire(next(responses)))

    agent = BIAgent(Settings(_env_file=None), client=sdk_client(receive), database=Database())
    try:
        text, history = await agent.answer("Faturamento em janeiro de 2025", [])
    finally:
        await agent.close()
    assert "1234,56" in text
    assert requests[0]["generationConfig"]["responseMimeType"] == "application/json"
    assert not requests[0].get("tools")
    declarations = requests[1]["tools"][0]["functionDeclarations"]
    assert {tool["name"] for tool in declarations} == {"get_schema", "execute_sql"}
    original = requests[2]["contents"][-2]["parts"][0]
    assert original["thoughtSignature"] == base64.b64encode(b"opaque-signature").decode()
    results = requests[-1]["contents"][-1]["parts"]
    assert [r["functionResponse"]["id"] for r in results] == ["sql-bad", "sql-good"]
    assert results[0]["functionResponse"]["response"]["sqlstate"] == "42703"
    assert results[1]["functionResponse"]["response"]["rows"] == [["1234.56"]]
    assert history[-1]["content"] == text


@pytest.mark.parametrize(
    ("status", "message"),
    [(400, "chave"), (403, "chave"), (404, "modelo"), (429, "cota"), (503, "indisponível")],
)
async def test_api_failures_are_portuguese_and_do_not_leak_or_retry(status, message):
    requests = []

    def receive(request):
        requests.append(request)
        return httpx.Response(
            status, json={"error": {"code": status, "message": "sensitive-key-do-not-display"}}
        )

    db = Database()
    agent = BIAgent(Settings(_env_file=None), client=sdk_client(receive), database=db)
    try:
        text, _ = await agent.answer("Faturamento em janeiro de 2025", [])
    finally:
        await agent.close()
    assert message in text.lower()
    assert "sensitive" not in text
    assert not db.queries
    assert len(requests) == 1


async def test_safety_block_never_executes_sql():
    def receive(request):
        return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

    db = Database()
    agent = BIAgent(Settings(_env_file=None), client=sdk_client(receive), database=db)
    try:
        text, _ = await agent.answer("Faturamento em janeiro de 2025", [])
    finally:
        await agent.close()
    assert "Não consegui" in text
    assert not db.queries
