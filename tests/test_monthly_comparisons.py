import copy
import os
from datetime import date
from decimal import Decimal

import pytest

from app.analysis_contract import validate_analysis
from app.bi_agent import BIAgent
from app.config import Settings
from app.database_tools import DatabaseTools
from app.managerial_queries import managerial_query
from app.managerial_rendering import render_managerial
from app.monthly_comparisons import normalize_monthly_comparison_plan
from app.relative_periods import normalize_relative_plan
from app.sql_policy import validate_select
from tests.test_agent import Client, Database, plan_response
from tests.test_analysis_contract import PLAN

QUESTION = "Nesse ano, teve algum mês que teve faturamento menor que o do ano passado?"
TODAY = date(2026, 10, 12)
MESSAGES = [{"role": "user", "content": QUESTION}]
COLUMNS = ["item", "base", "atual", "diferenca", "variacao_percentual", "direcao", "registros"]


@pytest.fixture
def database():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Requer PostgreSQL real.")
    return DatabaseTools(Settings(_env_file=None, database_url=dsn))


def monthly_plan():
    plan = copy.deepcopy(PLAN)
    plan["period"] = {"start": "2025-01-01", "end": "2025-10-13", "evidence": "ano passado"}
    plan["comparison_period"] = {
        "start": "2026-01-01",
        "end": "2026-10-13",
        "evidence": "Nesse ano",
    }
    plan["analysis"].update(group_by="mes", detail="quedas")
    return plan


def result(rows, *, truncated=False):
    return {"columns": COLUMNS, "rows": rows, "truncated": truncated}


@pytest.mark.parametrize("kind", ["tendencia", "comparacao"])
async def test_question_preserves_monthly_comparison_and_avoids_unneeded_clarification(
    kind, monkeypatch
):
    monkeypatch.setattr("app.bi_agent.current_date", lambda: TODAY)
    plan = monthly_plan()
    plan["analysis"].update(kind=kind, group_by="nenhum", detail="padrao")

    class MonthlyDatabase(Database):
        def execute_sql(self, sql):
            self.queries.append(sql)
            return result(
                [
                    ["1", "100.00", "80.00", "-20.00", "-20.00000", "diminuiu", 2],
                    ["2", "100.00", "150.00", "50.00", "50.00000", "aumentou", 2],
                ]
            )

    db, trace = MonthlyDatabase(), {}
    client = Client([plan_response(plan)])
    agent = BIAgent(Settings(_env_file=None, intent_classifier_enabled=False), client, db)
    history = [
        {
            "role": "user",
            "content": "Pedidos em setembro desse ano e do ano passado, valor e quantidade",
        },
        {"role": "assistant", "content": "Comparativo de pedidos de setembro."},
    ]
    text, _ = await agent.answer(QUESTION, history, trace=trace)
    assert trace["status"] == "answer" and len(client.calls) == 1
    assert len(db.queries) == 1 and trace["queries"][0]["template"] is True
    assert trace["plan"]["queries"][0]["analysis"]["kind"] == "comparacao"
    assert "2025-01-01" in db.queries[0] and "2026-10-13" in db.queries[0]
    assert "Janeiro" in text and "Fevereiro" not in text and "-20,00%" in text
    assert "Sim." in text and "Comparar períodos" not in text


def test_clarification_reply_keeps_pending_question_but_never_reuses_answered_request():
    plan = monthly_plan()
    plan["analysis"].update(kind="tendencia", detail="padrao")
    wrapped = {"queries": [plan]}
    history = MESSAGES + [
        {
            "role": "assistant",
            "content": "💬 Informe se deseja comparar períodos ou analisar um período só.",
        },
        {"role": "user", "content": "Comparar períodos"},
    ]
    resolved = normalize_monthly_comparison_plan(wrapped, history)
    validate_analysis(resolved["queries"][0], history, today=TODAY)
    assert resolved["queries"][0]["analysis"]["kind"] == "comparacao"
    assert (
        normalize_monthly_comparison_plan(
            wrapped,
            MESSAGES
            + [
                {"role": "assistant", "content": "Não houve quedas."},
                {"role": "user", "content": "Qual o faturamento em setembro?"},
            ],
        )
        == wrapped
    )
    assert wrapped["queries"][0]["analysis"]["kind"] == "tendencia"


def test_dates_evidence_filters_and_ambiguity_still_need_validation():
    plan = monthly_plan()
    plan["analysis"]["custom_filters"] = True
    wrapped = {"queries": [plan]}
    normalized = normalize_monthly_comparison_plan(wrapped, MESSAGES)["queries"][0]
    assert normalized["analysis"]["custom_filters"] is True
    assert managerial_query(normalized) is None
    plan["comparison_period"] = None
    assert normalize_monthly_comparison_plan(wrapped, MESSAGES) == wrapped
    plan["comparison_period"] = {
        "start": "2026-01-01",
        "end": "2026-10-13",
        "evidence": "inventado",
    }
    with pytest.raises(ValueError):
        validate_analysis(plan, MESSAGES, today=TODAY)
    with pytest.raises(ValueError):
        validate_analysis(
            monthly_plan(), [{"role": "user", "content": "Compare os anos"}], today=TODAY
        )


def test_relative_dates_keep_calendar_cutoff_for_monthly_analysis():
    plan = monthly_plan()
    plan["period"].update(start="2030-01-01", end="2031-01-01")
    plan["comparison_period"].update(start="2031-01-01", end="2032-01-01")
    normalized = normalize_relative_plan({"queries": [plan]}, MESSAGES, TODAY)["queries"][0]
    assert normalized == monthly_plan()
    validate_analysis(normalized, MESSAGES, today=TODAY)
    assert validate_select(managerial_query(normalized)["sql"])


@pytest.mark.parametrize(
    "field,start,end",
    [
        ("comparison_period", "2026-02-01", "2026-10-13"),
        ("comparison_period", "2026-01-01", "2026-10-14"),
        ("comparison_period", "2026-01-01", "2028-01-01"),
    ],
)
def test_unaligned_or_multi_year_months_never_use_the_calendar_template(field, start, end):
    plan = monthly_plan()
    plan[field].update(start=start, end=end)
    assert managerial_query(plan) is None


def test_no_decline_is_distinct_from_no_data_unknown_values_and_truncation():
    context = managerial_query(monthly_plan())["context"]
    increased = result([["1", "100.00", "150.00", "50.00", "50.00", "aumentou", 2]])
    text = render_managerial(increased, context)
    assert "Não. Nenhum dos meses" in text and "Não encontrei registros" not in text
    assert "último mês está parcial" in text
    assert "Não encontrei registros" in render_managerial(result([]), context)
    unknown = result([["1", None, "150.00", None, None, "indefinido", 2]])
    assert "não é possível concluir" in render_managerial(unknown, context)
    truncated = render_managerial({**increased, "truncated": True}, context)
    assert "Resultado parcial" in truncated and "Nenhum dos meses" not in truncated


def test_general_monthly_comparison_preserves_all_months_and_leap_year_alignment():
    plan = monthly_plan()
    plan["analysis"]["detail"] = "padrao"
    plan["period"].update(start="2023-01-01", end="2023-03-01")
    plan["comparison_period"].update(start="2024-01-01", end="2024-03-01")
    compiled = managerial_query(plan)
    assert compiled is not None and validate_select(compiled["sql"])
    selected = result(
        [
            ["1", "100.00", "80.00", "-20.00", "-20.00000", "diminuiu", 2],
            ["2", "100.00", "150.00", "50.00", "50.00000", "aumentou", 2],
        ]
    )
    text = render_managerial(selected, compiled["context"])
    assert "Janeiro" in text and "Fevereiro" in text
    assert "último mês está parcial" not in text


@pytest.mark.integration
def test_real_monthly_comparison_matches_independent_sums_for_every_month(database):
    plan = monthly_plan()
    compiled = managerial_query(plan)
    selected = database.execute_sql(compiled["sql"])
    assert "error" not in selected and selected["truncated"] is False
    expected = []
    for year in (2025, 2026):
        reference = database.execute_sql(
            "SELECT date_part('month',emissao)::integer AS mes, SUM(valor) AS total "
            "FROM faturamento WHERE status <> 'cancelada' "
            f"AND emissao >= DATE '{year}-01-01' AND emissao < DATE '{year}-10-13' "
            "GROUP BY date_part('month',emissao) ORDER BY mes"
        )
        assert "error" not in reference and not reference["truncated"]
        expected.append({str(month): Decimal(total) for month, total in reference["rows"]})
    assert {row[0] for row in selected["rows"]} == set(expected[0]) | set(expected[1])
    for month, base, current, difference, percent, direction, _ in selected["rows"]:
        b, c = expected[0].get(month, Decimal(0)), expected[1].get(month, Decimal(0))
        assert (Decimal(base), Decimal(current), Decimal(difference)) == (b, c, c - b)
        assert direction == ("diminuiu" if c < b else "aumentou" if c > b else "ficou_estavel")
        if not b:
            assert percent is None


@pytest.mark.integration
def test_monthly_entry_exit_zero_and_null_are_preserved(database, monkeypatch):
    def rows(plan, period, group):
        values = (
            "('2025-01-01',100),('2025-03-01',20),('2025-04-01',NULL),('2025-05-01',0)"
            if period["start"].startswith("2025")
            else "('2026-01-01',80),('2026-02-01',40),('2026-04-01',NULL),('2026-05-01',10)"
        )
        return f"SELECT item, valor::numeric AS valor FROM (VALUES {values}) AS v(item,valor)"

    monkeypatch.setattr("app.managerial_queries._rows", rows)
    compiled = managerial_query(monthly_plan())
    selected = database.execute_sql(compiled["sql"])
    assert "error" not in selected and not selected["truncated"]
    data = {r[0]: dict(zip(selected["columns"], r, strict=True)) for r in selected["rows"]}
    assert list(data) == ["1", "2", "3", "4", "5"]
    assert data["1"]["direcao"] == "diminuiu"
    assert Decimal(data["2"]["base"]) == 0 and data["2"]["variacao_percentual"] is None
    assert Decimal(data["3"]["atual"]) == 0 and data["3"]["direcao"] == "diminuiu"
    assert data["4"]["base"] is None and data["4"]["atual"] is None
    assert data["4"]["direcao"] == "indefinido"
    assert Decimal(data["5"]["base"]) == 0 and data["5"]["variacao_percentual"] is None
    text = render_managerial(selected, compiled["context"])
    assert "Janeiro" in text and "Março" in text and "Fevereiro" not in text
