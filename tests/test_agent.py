import json
from types import SimpleNamespace

import httpx
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


def plan_response(*queries):
    return response({"queries": list(queries)})


PLAN = {
    "metric": "faturamento",
    "measure": "valor",
    "operation": "analysis",
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
    agent = BIAgent(Settings(_env_file=None), Client([plan_response({**PLAN, "period": None})]), db)
    text, messages = await agent.answer("Qual o faturamento?", [])
    assert "período" in text
    assert not db.queries
    assert messages[-1]["role"] == "assistant"


async def test_invented_period_evidence_never_calls_database():
    db = Database()
    agent = BIAgent(Settings(_env_file=None), Client([plan_response(PLAN)]), db)
    text, _ = await agent.answer("Como estão os negócios?", [])
    assert "período" in text
    assert not db.queries


async def test_sql_error_is_returned_to_model_and_corrected():
    db = Database()
    client = Client(
        [
            plan_response(PLAN),
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
    trace = {}
    text, _ = await agent.answer("Qual o faturamento em janeiro de 2025?", [], trace=trace)
    assert "1.234,56" in text
    assert len(db.queries) == 2
    error_message = client.calls[3]["contents"][-1].parts[0].function_response
    assert error_message.name == "execute_sql"
    assert error_message.response["sqlstate"] == "42703"
    assert "error" in error_message.response
    assert trace["status"] == "answer"
    assert len(trace["queries"][0]["attempts"]) == 2
    assert trace["queries"][0]["selected"]["rows"] == [["1234.56"]]


async def test_trace_records_selected_result_instead_of_last_successful_query():
    client = Client(
        [
            plan_response(PLAN),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": "SELECT valor FROM faturamento"})]),
            response(tools=[call("execute_sql", {"sql": "SELECT valor FROM pedidos"})]),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )

    class DifferentResults(Database):
        def execute_sql(self, sql):
            return {
                "columns": ["total"],
                "rows": [[1 if "faturamento" in sql else 2]],
                "truncated": False,
            }

    trace = {}
    await BIAgent(Settings(_env_file=None), client, DifferentResults()).answer(
        "Faturamento em janeiro de 2025", [], trace=trace
    )
    assert trace["queries"][0]["selected"]["rows"] == [[1]]
    assert trace["queries"][0]["attempts"][-1]["result"]["rows"] == [[2]]


async def test_transport_error_is_separate_from_wrong_model_answer():
    class Unavailable(Client):
        async def create(self, **kwargs):
            raise httpx.ConnectError("Detalhe de conexão não deve aparecer na evidência.")

    trace = {}
    text, _ = await BIAgent(Settings(_env_file=None), Unavailable([]), Database()).answer(
        "Faturamento em janeiro de 2025", [], trace=trace
    )
    assert trace["status"] == "transport_error"
    assert "Detalhe" not in text + json.dumps(trace)


async def test_exhausted_sql_retry_gives_portuguese_error():
    db = Database()
    client = Client(
        [plan_response(PLAN), response(tools=[call("get_schema", {})])]
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
            plan_response(PLAN),
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
    assert "1.234,56" in text


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
    client = Client([plan_response({**PLAN, "period": None})])
    await BIAgent(Settings(_env_file=None), client, Database()).answer("E agora?", history)
    assert all(p.text is not None for m in client.calls[0]["contents"] for p in m.parts)
    assert client.calls[0]["config"].tools is None


async def test_multiple_metrics_keep_independent_results_and_only_visible_history():
    class TwoMetrics(Database):
        def execute_sql(self, sql):
            self.queries.append(sql)
            amount = "1234.56" if "faturamento" in sql else "9876.54"
            return {"columns": ["total", "registros"], "rows": [[amount, 3]], "truncated": False}

    client = Client(
        [
            plan_response({**PLAN, "metric": "pedidos"}, PLAN),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": "SELECT sum(valor) FROM pedidos"})]),
            response({"kind": "answer", "result_id": "q1"}),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": "SELECT sum(valor) FROM faturamento"})]),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    db = TwoMetrics()
    question = "Valor dos pedidos e faturamento em janeiro de 2025"
    text, history = await BIAgent(Settings(_env_file=None), client, db).answer(question, [])
    orders, revenue = text.split("\n\n")
    assert "pedidos" in orders and "9.876,54" in orders and "1.234,56" not in orders
    assert "faturamento" in revenue and "1.234,56" in revenue and "9.876,54" not in revenue
    assert len(db.queries) == 2
    assert history == [
        {"role": "user", "content": question},
        {"role": "assistant", "content": text},
    ]


async def test_multiple_metrics_clarify_only_the_missing_measure_before_any_sql():
    db = Database()
    client = Client([plan_response(PLAN, {**PLAN, "metric": "pedidos", "measure": None})])
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Pedidos e faturamento em janeiro de 2025", []
    )
    assert "Para pedidos" in text
    assert "valor ou a quantidade" in text
    assert not db.queries


async def test_unproven_period_in_one_metric_blocks_the_entire_composite_request():
    db = Database()
    client = Client(
        [
            plan_response(
                PLAN,
                {
                    **PLAN,
                    "metric": "pedidos",
                    "period": {
                        **PLAN["period"],
                        "evidence": "agosto de 2026",
                    },
                },
            )
        ]
    )
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Pedidos e faturamento em janeiro de 2025", []
    )
    assert "Qual período" in text
    assert not db.queries


async def test_failed_second_metric_does_not_present_first_as_a_complete_answer():
    client = Client(
        [
            plan_response({**PLAN, "metric": "pedidos"}, PLAN),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": "SELECT sum(valor) FROM pedidos"})]),
            response({"kind": "answer", "result_id": "q1"}),
            response(tools=[call("get_schema", {})]),
            *[
                response(
                    tools=[call("execute_sql", {"sql": "SELECT inexistente FROM faturamento"})]
                )
                for _ in range(3)
            ],
        ]
    )
    text, history = await BIAgent(Settings(_env_file=None), client, Database()).answer(
        "Pedidos e faturamento em janeiro de 2025", []
    )
    assert "Não consegui" in text and "1.234,56" not in text
    assert len(history) == 2


async def test_simple_totals_need_only_one_model_call_and_no_generated_sql():
    db = Database()
    client = Client(
        [
            plan_response(
                {**PLAN, "metric": "pedidos", "measure": "quantidade", "operation": "total"},
                {**PLAN, "operation": "total"},
            )
        ]
    )
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Total de pedidos e faturamento em janeiro de 2025", []
    )
    assert "pedidos" in text and "faturamento" in text
    assert len(client.calls) == 1 and len(db.queries) == 2
    assert "COUNT(*) AS quantidade" in db.queries[0]
    assert "data_pedido >= DATE '2025-01-01'" in db.queries[0]
    assert "status <> 'cancelado'" in db.queries[0]
    assert "SUM(valor) AS total" in db.queries[1]
    assert "emissao >= DATE '2025-01-01'" in db.queries[1]
    assert "COUNT(*) AS registros" in db.queries[1]


async def test_order_value_total_uses_template_sum_and_excludes_cancelled():
    db = Database()
    client = Client(
        [
            plan_response(
                {**PLAN, "metric": "pedidos", "measure": "valor", "operation": "total"},
            )
        ]
    )
    await BIAgent(Settings(_env_file=None), client, db).answer(
        "Valor total dos pedidos em janeiro de 2025", []
    )
    assert len(client.calls) == 1 and len(db.queries) == 1
    assert "FROM pedidos" in db.queries[0]
    assert "SUM(valor) AS total" in db.queries[0]
    assert "data_pedido >= DATE '2025-01-01'" in db.queries[0]
    assert "status <> 'cancelado'" in db.queries[0]


async def test_same_metric_and_period_measures_are_merged_without_repeating_header():
    db = Database()
    client = Client(
        [
            plan_response(
                {**PLAN, "metric": "pedidos", "measure": "valor", "operation": "total"},
                {**PLAN, "metric": "pedidos", "measure": "quantidade", "operation": "total"},
            )
        ]
    )
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Pedidos de venda, ambos, em janeiro de 2025", []
    )
    assert text.count("Período:") == 1
    assert text.count("Resumo de pedidos de venda") == 1
    assert text.count("Valor:") == 1 and text.count("Quantidade:") == 1
    assert "▸" not in text and "• Total" not in text


async def test_custom_filter_uses_analysis_instead_of_unfiltered_total():
    db = Database()
    query = "SELECT SUM(valor) AS total FROM faturamento WHERE status = 'aberta'"
    client = Client(
        [
            plan_response({**PLAN, "operation": "analysis"}),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": query})]),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Qual o faturamento aberto em janeiro de 2025?", []
    )
    assert "1.234,56" in text and db.queries == [query]


async def test_sql_in_period_is_rejected_before_templates_or_database():
    db = Database()
    client = Client(
        [
            plan_response(
                {
                    **PLAN,
                    "operation": "total",
                    "period": {
                        **PLAN["period"],
                        "start": "2025-01-01'; DROP TABLE clientes; --",
                    },
                }
            )
        ]
    )
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Faturamento em janeiro de 2025", []
    )
    assert "período" in text and not db.queries


async def test_resolution_rate_total_is_a_rounded_percentage_not_a_raw_ratio():
    class RateDatabase(Database):
        def execute_sql(self, sql):
            self.queries.append(sql)
            return {
                "columns": ["taxa", "registros"],
                "rows": [["85.714285714285714286", 7]],
                "truncated": False,
            }

    db = RateDatabase()
    client = Client(
        [
            plan_response(
                {
                    **PLAN,
                    "metric": "chamados",
                    "measure": "taxa_resolucao",
                    "operation": "total",
                }
            )
        ]
    )
    text, _ = await BIAgent(Settings(_env_file=None), client, db).answer(
        "Taxa de resolução das ocorrências em janeiro de 2025", []
    )
    assert "* 100 / NULLIF(SUM(chamados_abertos), 0)" in db.queries[0]
    assert text.splitlines()[-1] == "Taxa de resolução: 85,71%"
    assert "85,7142" not in text


def test_a_merged_group_over_the_limit_falls_back_to_the_separate_answers():
    from app.bi_agent import merge_groupable_answers
    from app.managerial_rendering import render_managerial

    period = {"start": "2025-03-01", "end": "2025-04-01", "evidence": "março de 2025"}
    rows = [
        [f"{i} — Cliente {i} Auto Peças Santa Cruz", "100.00", "200.00", "100.00", "100.00", "aumentou", 4]
        for i in range(100)
    ]
    result = {
        "columns": ["item", "base", "atual", "diferenca", "variacao_percentual", "direcao", "registros"],
        "rows": rows,
        "truncated": False,
    }

    def context(measure, unit):
        return {
            "source": "controlled_template",
            "kind": "comparacao",
            "group_by": "cliente",
            "metric": "pedidos",
            "measure": measure,
            "unit": unit,
            "period": period,
            "comparison_period": period,
        }

    contexts = [context("valor", "BRL"), context("quantidade", "quantidade")]
    answers = [render_managerial(result, c) for c in contexts]
    evidences = [{"managerial_context": c, "selected": result} for c in contexts]
    assert all(len(a) < 12000 for a in answers) and sum(map(len, answers)) > 12000
    assert merge_groupable_answers(answers, evidences) == answers
