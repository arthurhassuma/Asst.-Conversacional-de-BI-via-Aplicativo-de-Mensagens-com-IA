import httpx
from google.genai.errors import APIError

from app import metrics
from app.bi_agent import BIAgent
from app.config import Settings
from app.database_tools import DatabaseTools
from app.main import create_app
from tests.test_agent import PLAN, Client, Database, plan_response


def snapshot():
    values = {}
    for line in metrics.render().splitlines():
        if line and not line.startswith("#"):
            name, number = line.rsplit(" ", 1)
            values[name] = float(number)
    return values


def delta(before, name):
    return snapshot().get(name, 0) - before.get(name, 0)


def test_render_follows_the_prometheus_text_format():
    metrics.QUESTIONS.inc("answer")
    metrics.QUESTION_SECONDS.observe(value=0.4)
    text = metrics.render()
    assert "# HELP bi_questions_total" in text and "# TYPE bi_questions_total counter" in text
    assert "# TYPE bi_question_duration_seconds histogram" in text
    assert 'bi_question_duration_seconds_bucket{le="+Inf"}' in text
    assert (
        "bi_question_duration_seconds_sum" in text and "bi_question_duration_seconds_count" in text
    )
    assert 'bi_build_info{revision="' in text and text.endswith("\n")


def test_histogram_buckets_are_cumulative():
    histogram = metrics.Histogram("t", "t", buckets=(1, 5))
    for value in (0.5, 3, 9):
        histogram.observe(value=value)
    lines = histogram.render()
    assert 't_bucket{le="1"} 1' in lines
    assert 't_bucket{le="5"} 2' in lines
    assert 't_bucket{le="+Inf"} 3' in lines
    assert "t_count 3" in lines


def test_label_values_are_escaped():
    counter = metrics.Counter("c", "c", ("x",))
    counter.inc('a"b\\c')
    assert 'c{x="a\\"b\\\\c"} 1' in counter.render()


async def test_answered_question_is_counted_with_its_path_and_gemini_calls():
    before = snapshot()
    client = Client([plan_response({**PLAN, "operation": "total"})])
    await BIAgent(Settings(_env_file=None), client, Database()).answer(
        "Faturamento em janeiro de 2025", []
    )
    assert delta(before, 'bi_questions_total{status="answer"}') == 1
    assert delta(before, 'bi_queries_total{path="modelo_fixo"}') == 1
    assert delta(before, "bi_gemini_requests_total") == 1
    assert delta(before, "bi_question_duration_seconds_count") == 1


async def test_clarification_and_invalid_question_have_their_own_status():
    before = snapshot()
    agent = BIAgent(Settings(_env_file=None), Client([]), Database())
    await agent.answer("   ", [])
    assert delta(before, 'bi_questions_total{status="invalid_question"}') == 1


async def test_provider_error_is_counted_by_http_code():
    class Failing:
        class aio:  # noqa: N801
            class models:  # noqa: N801
                @staticmethod
                async def generate_content(**kwargs):
                    raise APIError(429, {"error": {"code": 429, "message": "cota"}})

    before = snapshot()
    await BIAgent(Settings(_env_file=None), Failing(), Database()).answer(
        "Faturamento em janeiro de 2025", []
    )
    assert delta(before, 'bi_questions_total{status="provider_error"}') == 1
    assert delta(before, 'bi_provider_errors_total{code="429"}') == 1


def test_sql_outcomes_are_classified():
    tools = DatabaseTools.__new__(DatabaseTools)
    cases = {
        "ok": {"columns": ["a"], "rows": [[1]], "truncated": False},
        "timeout": {"error": "x", "sqlstate": "57014"},
        "db_error": {"error": "x", "sqlstate": "42703"},
        "recusado": {"error": "SQL não permitido."},
    }
    for outcome, result in cases.items():
        before = snapshot()
        tools._execute_sql = lambda sql, result=result: result
        assert tools.execute_sql("SELECT 1") == result
        assert delta(before, f'bi_sql_executions_total{{outcome="{outcome}"}}') == 1
        assert delta(before, f'bi_sql_duration_seconds_count{{outcome="{outcome}"}}') == 1


async def test_metrics_endpoint_and_webhook_counters():
    settings = Settings(_env_file=None, telegram_webhook_secret="s" * 20, metrics_token="tok")
    app = create_app(settings, agent=BIAgent(settings, Client([]), Database()), sender=object())
    before = snapshot()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as http:
        denied = await http.get("/metrics")
        wrong = await http.get("/metrics", headers={"Authorization": "Bearer nope"})
        ok = await http.get("/metrics", headers={"Authorization": "Bearer tok"})
        await http.post(
            "/telegram/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "errado"},
        )
    assert denied.status_code == 403 and wrong.status_code == 403
    assert ok.status_code == 200 and ok.headers["content-type"].startswith("text/plain")
    assert "bi_updates_total" in ok.text
    assert delta(before, 'bi_updates_total{result="recusado_autenticacao"}') == 1


async def test_metrics_endpoint_is_open_when_no_token_is_configured():
    settings = Settings(_env_file=None)
    app = create_app(settings, agent=BIAgent(settings, Client([]), Database()), sender=object())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as http:
        assert (await http.get("/metrics")).status_code == 200


async def test_metrics_never_contain_question_text():
    client = Client([plan_response({**PLAN, "operation": "total"})])
    await BIAgent(Settings(_env_file=None), client, Database()).answer(
        "Faturamento em janeiro de 2025 do cliente Oficina Segredo", []
    )
    assert "Segredo" not in metrics.render()
