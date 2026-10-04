import json
from types import SimpleNamespace

from google.genai import types

from app.bi_agent import BIAgent
from app.config import Settings


def response(payload=None, tools=None):
    blocks = tools or [{"text": json.dumps(payload)}]
    return types.GenerateContentResponse.model_validate(
        {
            "candidates": [{"content": {"role": "model", "parts": blocks}, "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 10},
        }
    )


def call(name, inputs, id="t1"):
    return {"functionCall": {"id": id, "name": name, "args": inputs}}


PLAN = {
    "metric": "faturamento",
    "measure": "valor",
    "period": {"start": "2025-01-01", "end": "2025-02-01", "evidence": "janeiro de 2025"},
}


class Client:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.aio = SimpleNamespace(models=SimpleNamespace(generate_content=self.create))

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.responses)


class Database:
    def __init__(self):
        self.queries = []

    def get_schema(self):
        return {"tables": {"faturamento": ["valor", "emissao"]}}

    def execute_sql(self, sql):
        self.queries.append(sql)
        if "inexistente" in sql:
            return {
                "error": "Coluna inválida.",
                "sqlstate": "42703",
                "database_detail": "column inexistente does not exist",
            }
        return {"columns": ["total"], "rows": [["1234.56"]], "truncated": False}


async def test_missing_period_never_calls_database():
    db = Database()
    agent = BIAgent(Settings(_env_file=None), Client([response({**PLAN, "period": None})]), db)
    text, messages = await agent.answer("Qual o faturamento?", [])
    assert "período" in text
    assert not db.queries
    assert messages[-1]["role"] == "assistant"


async def test_invented_period_evidence_never_calls_database():
    db = Database()
    agent = BIAgent(Settings(_env_file=None), Client([response(PLAN)]), db)
    text, _ = await agent.answer("Como estão os negócios?", [])
    assert "período" in text
    assert not db.queries


async def test_sql_error_is_returned_to_model_and_corrected():
    db = Database()
    client = Client(
        [
            response(PLAN),
            response(tools=[call("get_schema", {})]),
            response(
                tools=[call("execute_sql", {"sql": "SELECT inexistente FROM faturamento"}, "t2")]
            ),
            response(
                tools=[
                    call(
                        "execute_sql", {"sql": "SELECT sum(valor) AS total FROM faturamento"}, "t3"
                    )
                ]
            ),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    agent = BIAgent(Settings(_env_file=None), client, db)
    text, _ = await agent.answer("Qual o faturamento em janeiro de 2025?", [])
    assert "1234,56" in text
    assert len(db.queries) == 2
    error_message = client.calls[3]["contents"][-1].parts[0].function_response
    assert error_message.name == "execute_sql"
    assert error_message.response["sqlstate"] == "42703"
    assert "error" in error_message.response


async def test_exhausted_sql_retry_gives_portuguese_error():
    db = Database()
    client = Client(
        [response(PLAN), response(tools=[call("get_schema", {})])]
        + [
            response(
                tools=[call("execute_sql", {"sql": "SELECT inexistente FROM faturamento"}, f"t{i}")]
            )
            for i in range(3)
        ]
    )
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Faturamento em janeiro de 2025", []
    )
    assert "Não consegui" in text
    assert len(db.queries) == 3
    assert "column" not in text


async def test_history_supplies_explicit_period_for_followup():
    client = Client(
        [
            response(PLAN),
            response(tools=[call("get_schema", {})]),
            response(
                tools=[call("execute_sql", {"sql": "SELECT sum(valor) AS total FROM faturamento"})]
            ),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    history = [
        {"role": "user", "content": "janeiro de 2025"},
        {"role": "assistant", "content": "Qual métrica deseja consultar?"},
    ]
    text, _ = await BIAgent(Settings(_env_file=None), client, Database()).answer(
        "O faturamento", history
    )
    assert "1234,56" in text


async def test_planner_does_not_receive_tool_blocks_without_definitions():
    history = [
        {"role": "user", "content": "Faturamento em janeiro de 2025"},
        {
            "role": "assistant",
            "content": response(tools=[call("get_schema", {})])
            .candidates[0]
            .content.model_dump(exclude_none=True),
        },
        {
            "role": "user",
            "content": {
                "role": "user",
                "parts": [{"functionResponse": {"id": "t1", "name": "get_schema", "response": {}}}],
            },
        },
        {"role": "assistant", "content": "Total consultado."},
    ]
    client = Client([response({**PLAN, "period": None})])
    await BIAgent(Settings(_env_file=None), client, Database()).answer("E agora?", history)
    assert all(p.text is not None for m in client.calls[0]["contents"] for p in m.parts)
    assert client.calls[0]["config"].tools is None
