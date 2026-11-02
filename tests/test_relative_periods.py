import copy
from datetime import date

import pytest

from app.analysis_contract import validate_analysis, validate_period
from app.bi_agent import BIAgent
from app.config import Settings
from app.messaging import TelegramService
from app.relative_periods import normalize_relative_plan
from app.sessions import SessionStore
from tests.test_agent import Client, Database, plan_response
from tests.test_analysis_contract import PLAN
from tests.test_backend import Sender, update

TODAY = date(2026, 10, 12)


def query(evidence, *, comparison=None):
    result = copy.deepcopy(PLAN)
    result["period"] = {"start": "2030-01-01", "end": "2031-01-01", "evidence": evidence}
    if comparison:
        result["comparison_period"] = {
            "start": "2020-01-01",
            "end": "2021-01-01",
            "evidence": comparison,
        }
    else:
        result.pop("comparison_period")
        result["analysis"] = None
        result["operation"] = "total"
    return result


@pytest.mark.parametrize(
    "evidence,start,end",
    [
        ("esse ano", "2026-01-01", "2026-10-13"),
        ("ano atual", "2026-01-01", "2026-10-13"),
        ("ano passado", "2025-01-01", "2026-01-01"),
        ("último ano", "2025-01-01", "2026-01-01"),
        ("fevereiro desse ano", "2026-02-01", "2026-03-01"),
    ],
)
def test_relative_year_is_calendar_anchored_and_uses_literal_evidence(evidence, start, end):
    messages = [{"role": "user", "content": "Qual o faturamento de " + evidence + "?"}]
    plan = {"queries": [query(evidence)]}
    before = copy.deepcopy(plan)
    resolved = normalize_relative_plan(plan, messages, TODAY)["queries"][0]["period"]
    assert (resolved["start"], resolved["end"], resolved["evidence"]) == (start, end, evidence)
    assert plan == before
    validate_period(resolved, messages, today=TODAY)


def test_annual_comparison_has_previous_year_base_and_same_cutoff():
    messages = [{"role": "user", "content": "Compare faturamento do ano atual com o ano anterior."}]
    result = normalize_relative_plan(
        {"queries": [query("ano atual", comparison="ano anterior")]}, messages, TODAY
    )["queries"][0]
    assert result["period"] == {
        "start": "2025-01-01",
        "end": "2025-10-13",
        "evidence": "ano anterior",
    }
    assert result["comparison_period"] == {
        "start": "2026-01-01",
        "end": "2026-10-13",
        "evidence": "ano atual",
    }
    validate_analysis(result, messages, today=TODAY)


def test_month_is_preserved_when_previous_year_is_only_named_in_followup_clause():
    messages = [
        {
            "role": "user",
            "content": "Faturamento de fevereiro desse ano. Compare com o ano passado.",
        }
    ]
    result = normalize_relative_plan(
        {"queries": [query("fevereiro desse ano", comparison="ano passado")]}, messages, TODAY
    )["queries"][0]
    assert result["period"]["start"] == "2025-02-01" and result["period"]["end"] == "2025-03-01"
    assert result["comparison_period"]["start"] == "2026-02-01"
    validate_analysis(result, messages, today=TODAY)


@pytest.mark.parametrize(
    "today,base_end,current_end",
    [
        (date(2024, 2, 29), "2023-03-01", "2024-03-01"),
        (date(2024, 2, 28), "2023-03-01", "2024-02-29"),
        (date(2026, 12, 31), "2026-01-01", "2027-01-01"),
    ],
)
def test_leap_days_and_year_boundary(today, base_end, current_end):
    messages = [{"role": "user", "content": "Compare ano atual e ano anterior"}]
    result = normalize_relative_plan(
        {"queries": [query("ano anterior", comparison="ano atual")]}, messages, today
    )["queries"][0]
    assert result["period"]["end"] == base_end
    assert result["comparison_period"]["end"] == current_end
    validate_analysis(result, messages, today=today)


def test_relative_year_drift_or_invented_evidence_is_rejected():
    with pytest.raises(ValueError):
        validate_period(
            query("esse ano")["period"], [{"role": "user", "content": "esse ano"}], today=TODAY
        )
    plan = {"queries": [query("ano passado")]}
    messages = [{"role": "user", "content": "Qual o faturamento?"}]
    assert normalize_relative_plan(plan, messages, TODAY) == plan
    with pytest.raises(ValueError):
        validate_period(plan["queries"][0]["period"], messages, today=TODAY)


@pytest.mark.parametrize(
    "evidence,start,end",
    [
        ("hoje", "2026-10-12", "2026-10-13"),
        ("ontem", "2026-10-11", "2026-10-12"),
        ("anteontem", "2026-10-10", "2026-10-11"),
        ("05/03/2025", "2025-03-05", "2025-03-06"),
        ("dia 20 de janeiro de 2025", "2025-01-20", "2025-01-21"),
        ("dia 20 de janeiro desse ano", "2026-01-20", "2026-01-21"),
        ("dia 20 de janeiro do ano passado", "2025-01-20", "2025-01-21"),
    ],
)
def test_exact_day_is_resolved_deterministically(evidence, start, end):
    messages = [{"role": "user", "content": "Qual o faturamento de " + evidence + "?"}]
    plan = {"queries": [query(evidence)]}
    before = copy.deepcopy(plan)
    resolved = normalize_relative_plan(plan, messages, TODAY)["queries"][0]["period"]
    assert (resolved["start"], resolved["end"], resolved["evidence"]) == (start, end, evidence)
    assert plan == before
    validate_period(resolved, messages, today=TODAY)


def test_exact_day_without_year_context_is_not_replaced():
    messages = [{"role": "user", "content": "Qual o faturamento no dia 20 de janeiro?"}]
    plan = {"queries": [query("dia 20 de janeiro")]}
    assert normalize_relative_plan(plan, messages, TODAY) == plan


def test_invalid_explicit_date_is_not_replaced():
    messages = [{"role": "user", "content": "Qual o faturamento em 31/02/2025?"}]
    plan = {"queries": [query("31/02/2025")]}
    assert normalize_relative_plan(plan, messages, TODAY) == plan


def test_explicit_dates_and_ambiguous_month_ranges_are_not_replaced():
    assert normalize_relative_plan(
        {"queries": [PLAN]}, [{"role": "user", "content": "agosto de 2025 e agosto de 2026"}], TODAY
    ) == {"queries": [PLAN]}
    plan = {"queries": [query("esse ano")]}
    assert (
        normalize_relative_plan(
            plan, [{"role": "user", "content": "janeiro a março desse ano"}], TODAY
        )
        == plan
    )


async def test_agent_resolves_relative_comparison_before_sql(monkeypatch):
    monkeypatch.setattr("app.bi_agent.current_date", lambda: TODAY)

    class Comparisons(Database):
        def execute_sql(self, sql):
            self.queries.append(sql)
            return {
                "columns": ["base", "atual", "diferenca", "variacao_percentual", "registros"],
                "rows": [["100.00", "120.00", "20.00", "20.00", 2]],
                "truncated": False,
            }

    db = Comparisons()
    trace = {}
    agent = BIAgent(
        Settings(_env_file=None),
        Client([plan_response(query("ano atual", comparison="ano anterior"))]),
        db,
    )
    text, _ = await agent.answer(
        "Compare faturamento do ano atual com o ano anterior", [], trace=trace
    )
    assert trace["status"] == "answer" and trace["date_anchor"] == "2026-10-12"
    assert trace["relative_periods_resolved"] and len(db.queries) == 1
    assert "2025-10-13" in db.queries[0] and "2026-10-13" in db.queries[0]
    assert "20,00%" in text


@pytest.mark.parametrize("command", ["/comecar", "/começar", "/start", "/ajuda"])
async def test_portuguese_start_commands_are_handled_without_model(command):
    sender = Sender()
    service = TelegramService(
        Settings(_env_file=None, telegram_allowed_user_ids="42"), None, SessionStore(), sender
    )
    await service.process(update(text=command))
    assert sender.sent[0][1].startswith("Olá!")
