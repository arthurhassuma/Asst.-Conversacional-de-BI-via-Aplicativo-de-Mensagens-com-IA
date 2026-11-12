import copy

import pytest

from app.bi_agent import BIAgent
from app.config import Settings
from tests.test_agent import Client, Database, plan_response
from tests.test_analysis_contract import MESSAGES, PLAN


async def test_managerial_comparison_runs_controlled_sql_and_records_context():
    class ComparisonDatabase(Database):
        def execute_sql(self, sql):
            self.queries.append(sql)
            return {
                "columns": [
                    "item",
                    "base",
                    "atual",
                    "diferenca",
                    "variacao_percentual",
                    "direcao",
                    "registros",
                ],
                "rows": [["Total", "100.00", "120.00", "20.00", "20.00", "aumentou", 2]],
                "truncated": False,
            }

    db, trace = ComparisonDatabase(), {}
    agent = BIAgent(
        Settings(_env_file=None, intent_classifier_enabled=False), Client([plan_response(PLAN)]), db
    )
    text, _ = await agent.answer(MESSAGES[0]["content"], [], trace=trace)
    assert trace["status"] == "answer"
    assert trace["queries"][0]["managerial_context"]["source"] == "controlled_template"
    assert len(db.queries) == 1 and "2026-08-01" in db.queries[0]
    assert "R$ 120,00" in text and "📈" in text


@pytest.mark.parametrize("enabled", [True, False])
async def test_classifier_never_supplies_a_missing_period(enabled):
    plan = copy.deepcopy(PLAN)
    plan["period"] = None
    db, trace = Database(), {}
    agent = BIAgent(
        Settings(_env_file=None, intent_classifier_enabled=enabled),
        Client([plan_response(plan)]),
        db,
    )
    text, _ = await agent.answer("Quais segmentos cresceram?", [], trace=trace)
    assert "período" in text and not db.queries
    assert trace["status"] == "clarification_period"


async def test_model_missing_keeps_generic_planner_available(tmp_path):
    trace = {}
    settings = Settings(
        _env_file=None,
        intent_classifier_enabled=True,
        intent_model_path=str(tmp_path / "missing.json"),
    )
    agent = BIAgent(settings, Client([plan_response({**PLAN, "period": None})]), Database())
    await agent.answer("Compare o faturamento", [], trace=trace)
    assert trace["intent"]["available"] is False
    assert trace["status"] == "clarification_period"


async def test_non_temporal_evidence_does_not_authorize_dates():
    plan = copy.deepcopy(PLAN)
    plan["period"]["evidence"] = "faturamento"
    plan["comparison_period"]["evidence"] = "faturamento"
    db = Database()
    agent = BIAgent(Settings(_env_file=None), Client([plan_response(plan)]), db)
    text, _ = await agent.answer("Compare o faturamento", [])
    assert "período" in text and not db.queries


async def test_total_cannot_use_non_temporal_evidence_either():
    plan = copy.deepcopy(PLAN)
    plan.update(operation="total", analysis=None, comparison_period=None)
    plan["period"]["evidence"] = "faturamento"
    db = Database()
    text, _ = await BIAgent(Settings(_env_file=None), Client([plan_response(plan)]), db).answer(
        "Qual o faturamento?", []
    )
    assert "período" in text and not db.queries


async def test_short_followup_without_reference_requires_clarification():
    plan = copy.deepcopy(PLAN)
    plan["comparison_period"] = None
    db = Database()
    text, _ = await BIAgent(Settings(_env_file=None), Client([plan_response(plan)]), db).answer(
        "E no outro ano?", MESSAGES
    )
    assert "período" in text and not db.queries


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Qual o faturamento aberto em agosto de 2025?",
            "SELECT SUM(valor) AS total FROM faturamento WHERE status='aberta'",
        ),
        (
            "Qual o faturamento do cliente 11 em agosto de 2025?",
            "SELECT SUM(f.valor) AS total FROM faturamento f JOIN pedidos p ON p.id=f.pedido_id JOIN contratos c ON c.id=p.contrato_id WHERE c.cliente_id=11",
        ),
        (
            "Qual a média de faturamento em agosto de 2025?",
            "SELECT AVG(valor) AS media FROM faturamento",
        ),
        (
            "Quais os cinco clientes com menor faturamento em agosto de 2025?",
            "SELECT SUM(valor) AS total FROM faturamento ORDER BY total ASC LIMIT 5",
        ),
        (
            "Arredonde o faturamento em agosto de 2025 para duas casas decimais",
            "SELECT ROUND(SUM(valor),2) AS total FROM faturamento",
        ),
    ],
)
async def test_explicit_filter_cannot_be_lost_even_if_planner_marks_total(question, sql):
    from tests.test_agent import call, response

    plan = copy.deepcopy(PLAN)
    plan.update(operation="total", analysis=None, comparison_period=None)
    client = Client(
        [
            plan_response(plan),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": sql})]),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    db = Database()
    await BIAgent(Settings(_env_file=None), client, db).answer(question, [])
    assert db.queries == [sql]


async def test_open_calls_are_a_measure_not_a_status_filter():
    class Calls(Database):
        def execute_sql(self, sql):
            self.queries.append(sql)
            return {
                "columns": [
                    "item",
                    "chamados_abertos",
                    "chamados_resolvidos",
                    "saldo",
                    "taxa_percentual",
                    "registros",
                ],
                "rows": [["Total", 10, 8, 2, "80.0", 1]],
                "truncated": False,
            }

    plan = copy.deepcopy(PLAN)
    plan.pop("comparison_period")
    plan.update(metric="chamados", measure="taxa_resolucao")
    plan["analysis"].update(kind="operacional", group_by="nenhum", detail="chamados")
    db = Calls()
    text, _ = await BIAgent(Settings(_env_file=None), Client([plan_response(plan)]), db).answer(
        "Mostre chamados abertos, resolvidos, saldo e taxa em agosto de 2025.", []
    )
    assert len(db.queries) == 1 and "80,00%" in text


def ungrouped_ranking_plan():
    return {
        "metric": "contratos",
        "measure": "valor",
        "operation": "analysis",
        "period": {"start": "2025-01-01", "end": "2026-01-01", "evidence": "2025"},
        "comparison_period": None,
        "analysis": {
            "kind": "ranking",
            "group_by": "nenhum",
            "detail": "padrao",
            "limit": None,
            "custom_filters": True,
        },
    }


@pytest.mark.parametrize("enabled", [True, False])
async def test_ranking_without_group_or_limit_is_a_filtered_total_when_no_ranking_was_asked(
    enabled,
):
    from tests.test_agent import call, response

    sql = (
        "SELECT SUM(valor_contratado) AS total FROM contratos "
        "WHERE inicio >= DATE '2025-01-01' AND inicio < DATE '2026-01-01' AND status <> 'cancelado'"
    )
    client = Client(
        [
            plan_response(ungrouped_ranking_plan()),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": sql})]),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    db, trace = Database(), {}
    settings = Settings(_env_file=None, intent_classifier_enabled=enabled)
    await BIAgent(settings, client, db).answer(
        "Qual o valor contratado dos contratos iniciados em 2025, excluindo os cancelados?",
        [],
        trace=trace,
    )
    assert trace["status"] == "answer"
    assert db.queries == [sql]
    assert trace["queries"][0]["plan"]["analysis"] is None


def grouped_ranking_plan_without_limit(group_by):
    plan = ungrouped_ranking_plan()
    plan.update(metric="clientes", measure="quantidade")
    plan["period"] = {"start": "2023-01-01", "end": "2024-01-01", "evidence": "2023"}
    plan["analysis"]["group_by"] = group_by
    return plan


@pytest.mark.parametrize("enabled", [True, False])
async def test_grouped_ranking_without_limit_runs_custom_sql_when_no_ranking_was_asked(enabled):
    from tests.test_agent import call, response

    sql = (
        "SELECT uf, COUNT(*) AS quantidade, COUNT(*) AS registros FROM clientes "
        "WHERE cadastrado_em >= DATE '2023-01-01' AND cadastrado_em < DATE '2024-01-01' "
        "GROUP BY uf ORDER BY uf"
    )
    client = Client(
        [
            plan_response(grouped_ranking_plan_without_limit("cidade")),
            response(tools=[call("get_schema", {})]),
            response(tools=[call("execute_sql", {"sql": sql})]),
            response({"kind": "answer", "result_id": "q1"}),
        ]
    )
    db, trace = Database(), {}
    settings = Settings(_env_file=None, intent_classifier_enabled=enabled)
    await BIAgent(settings, client, db).answer(
        "Quantos clientes foram cadastrados em 2023 em cada UF? Mostre UF e quantidade, "
        "ordenados pela UF.",
        [],
        trace=trace,
    )
    assert trace["status"] == "answer"
    assert db.queries == [sql]
    assert trace["queries"][0]["plan"]["analysis"] is None


@pytest.mark.parametrize(
    "question",
    ["Quais os principais clientes de 2023?", "Os clientes que mais compraram em 2023"],
)
async def test_grouped_ranking_without_limit_still_asks_for_the_size_when_ranking_is_implied(
    question,
):
    db, trace = Database(), {}
    agent = BIAgent(
        Settings(_env_file=None, intent_classifier_enabled=False),
        Client([plan_response(grouped_ranking_plan_without_limit("cliente"))]),
        db,
    )
    await agent.answer(question, [], trace=trace)
    assert trace["status"] == "clarification_limit" and not db.queries


async def test_explicit_ranking_request_without_limit_still_asks_for_the_size():
    db, trace = Database(), {}
    agent = BIAgent(
        Settings(_env_file=None, intent_classifier_enabled=False),
        Client([plan_response(ungrouped_ranking_plan())]),
        db,
    )
    text, _ = await agent.answer("Faça um ranking de contratos em 2025", [], trace=trace)
    assert trace["status"] == "clarification_limit" and not db.queries
    assert "ranking" in text
