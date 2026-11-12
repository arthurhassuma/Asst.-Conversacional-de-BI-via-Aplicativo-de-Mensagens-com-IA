import copy

import pytest

from app.analysis_contract import validate_analysis

PLAN = {
    "metric": "faturamento",
    "measure": "valor",
    "operation": "analysis",
    "period": {"start": "2025-08-01", "end": "2025-09-01", "evidence": "agosto de 2025"},
    "comparison_period": {"start": "2026-08-01", "end": "2026-09-01", "evidence": "agosto de 2026"},
    "analysis": {
        "kind": "comparacao",
        "group_by": "nenhum",
        "detail": "padrao",
        "limit": None,
        "custom_filters": False,
    },
}
MESSAGES = [{"role": "user", "content": "Compare faturamento de agosto de 2025 com agosto de 2026"}]


def test_both_periods_need_user_evidence():
    assert validate_analysis(PLAN, MESSAGES)["kind"] == "comparacao"
    with pytest.raises(ValueError):
        validate_analysis(PLAN, [{"role": "user", "content": "agosto de 2025"}])


@pytest.mark.parametrize(
    "field,value",
    [("group_by", "schema"), ("limit", 200), ("custom_filters", "false"), ("kind", "sql")],
)
def test_invalid_analysis_is_rejected(field, value):
    plan = copy.deepcopy(PLAN)
    plan["analysis"][field] = value
    with pytest.raises(ValueError):
        validate_analysis(plan, MESSAGES)


def test_legacy_plan_has_no_analysis_contract():
    assert validate_analysis({"metric": "faturamento"}, []) is None


def test_custom_filters_and_different_durations_are_preserved():
    plan = copy.deepcopy(PLAN)
    plan["comparison_period"]["end"] = "2026-10-01"
    plan["comparison_period"]["evidence"] = "agosto a setembro de 2026"
    plan["analysis"]["custom_filters"] = True
    messages = [{"role": "user", "content": "Compare agosto de 2025 com agosto a setembro de 2026"}]
    result = validate_analysis(plan, messages)
    assert result["custom_filters"] is True
    assert result["unequal_periods"] is True


@pytest.mark.parametrize(
    "reason,word",
    [
        ("custos_ausentes", "custos"),
        ("causalidade", "causa"),
        ("previsao", "previsão"),
        ("fora_escopo", "indicador"),
    ],
)
async def test_unsupported_requests_explain_limit_without_sql(reason, word):
    from app.bi_agent import BIAgent
    from app.config import Settings
    from tests.test_agent import Client, Database, response

    db, trace = Database(), {}
    agent = BIAgent(
        Settings(_env_file=None),
        Client([response({"queries": [], "unsupported_reason": reason})]),
        db,
    )
    text, _ = await agent.answer("Pedido sem dados suficientes", [], trace=trace)
    assert trace["status"] == "unsupported_request"
    assert word in text
    assert not db.queries


def test_filtered_total_without_ranking_needs_no_analysis_block():
    from app.bi_agent import clarify
    from app.prompts import PLANNER_PROMPT

    plan = {
        "metric": "faturamento",
        "measure": "valor",
        "operation": "analysis",
        "period": {"start": "2026-09-01", "end": "2026-10-01", "evidence": "setembro de 2026"},
        "comparison_period": None,
        "analysis": None,
    }
    messages = [{"role": "user", "content": "Faturamento em Joinville em setembro de 2026"}]
    assert clarify({"queries": [plan]}, messages) is None
    ranking = {**plan, "analysis": {**PLAN["analysis"], "kind": "ranking", "limit": None}}
    assert "ranking" in clarify({"queries": [ranking]}, messages).lower()
    assert 'operation="analysis" com analysis=null' in PLANNER_PROMPT
