"""Estado durável (caixa de entrada e sessões) com PostgreSQL real.

Exige TEST_STATE_ADMIN_URL: URL administrativa de um banco de TESTE. O schema `estado` e a role
`app_estado` desse banco são recriados pela fixture.
"""

import asyncio
import os
from datetime import datetime, timezone

import httpx
import psycopg
import pytest

from app.config import Settings
from app.main import create_app
from app.sessions import SessionsBusy
from app.state import PostgresInbox, PostgresSessionStore
from scripts.manage_db import initialize_state

pytestmark = pytest.mark.integration

STATE_PASSWORD = "senha_de_teste_do_estado"


@pytest.fixture(scope="module")
def admin_url():
    url = os.getenv("TEST_STATE_ADMIN_URL")
    if not url:
        pytest.skip("Configure TEST_STATE_ADMIN_URL para executar com PostgreSQL real.")
    return url.replace("@localhost:", "@127.0.0.1:")


@pytest.fixture(scope="module")
def state_url(admin_url):
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS estado CASCADE")
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname='app_estado'").fetchone():
            # A role é do cluster e pode ter privilégios em outros bancos: só alinha a senha.
            conn.execute(f"ALTER ROLE app_estado PASSWORD '{STATE_PASSWORD}'")
        initialize_state(conn, STATE_PASSWORD)
    parts = psycopg.conninfo.conninfo_to_dict(admin_url)
    return (
        f"postgresql://app_estado:{STATE_PASSWORD}@{parts['host']}:{parts['port']}"
        f"/{parts['dbname']}"
    )


@pytest.fixture
def clean(admin_url, state_url):
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute("TRUNCATE estado.updates, estado.sessoes")
    return admin_url


def sql(admin_url, query, params=()):
    with psycopg.connect(admin_url, autocommit=True) as conn:
        cur = conn.execute(query, params)
        return cur.fetchall() if cur.description else None


def inbox(state_url, **kw):
    return PostgresInbox(state_url, poll_interval=0.05, **kw)


# --- caixa de entrada ---------------------------------------------------------------------


async def test_register_is_idempotent_across_restarts(state_url, clean):
    first = inbox(state_url)
    assert await first.register(1, {"update_id": 1}) == "received"
    assert await first.register(1, {"update_id": 1}) == "duplicate"
    await first.close()
    restarted = inbox(state_url)  # processo novo: nada em memória
    assert await restarted.register(1, {"update_id": 1}) == "duplicate"
    assert await restarted.register(2, {"update_id": 2}) == "received"
    await restarted.close()


async def test_accepted_update_survives_restart_and_is_claimed_once(state_url, clean):
    before = inbox(state_url)
    await before.register(7, {"update_id": 7, "x": "y"})
    await before.close()  # "queda" antes de processar
    after = inbox(state_url)
    assert await after.claim() == (7, {"update_id": 7, "x": "y"})
    assert await after.claim() is None
    await after.close()


async def test_concurrent_consumers_never_claim_the_same_update(state_url, clean):
    boxes = [inbox(state_url) for _ in range(8)]
    for update_id in range(1, 41):
        await boxes[0].register(update_id, {"update_id": update_id})

    async def drain(box):
        mine = []
        while (item := await box.claim()) is not None:
            mine.append(item[0])
        return mine

    claimed = [i for part in await asyncio.gather(*[drain(b) for b in boxes]) for i in part]
    assert sorted(claimed) == list(range(1, 41))  # todos, e cada um exatamente uma vez
    for box in boxes:
        await box.close()


async def test_claim_skips_rows_locked_by_another_consumer(state_url, clean):
    box = inbox(state_url)
    await box.register(1, {"update_id": 1})
    await box.register(2, {"update_id": 2})
    with psycopg.connect(clean) as other:  # outro consumidor segura a linha 1 numa transação
        other.execute("SELECT 1 FROM estado.updates WHERE update_id = 1 FOR UPDATE")
        assert await asyncio.wait_for(box.claim(), 3) == (2, {"update_id": 2})
    await box.close()


async def test_done_keeps_dedup_but_drops_payload(state_url, clean):
    box = inbox(state_url)
    await box.register(3, {"update_id": 3, "message": {"text": "pergunta privada"}})
    await box.claim()
    await box.done(3)
    row = sql(clean, "SELECT status, payload FROM estado.updates WHERE update_id=3")[0]
    assert row == ("concluido", None)
    assert await box.register(3, {"update_id": 3}) == "duplicate"
    await box.close()


async def test_stale_lease_is_reclaimed_after_worker_crash(state_url, clean):
    crashed = inbox(state_url)
    await crashed.register(5, {"update_id": 5})
    assert await crashed.claim() is not None  # processando, sem concluir
    await crashed.close()
    survivor = inbox(state_url)
    assert await survivor.claim() is None  # lease ainda vigente
    sql(clean, "UPDATE estado.updates SET reservado_ate = now() - interval '1 second'")
    assert await survivor.claim() == (5, {"update_id": 5})
    await survivor.close()


async def test_retry_requeues_until_max_attempts_then_fails(state_url, clean):
    box = inbox(state_url, max_attempts=2)
    await box.register(9, {"update_id": 9})
    for _ in range(2):
        assert await box.claim() is not None
        await box.retry(9)
    assert await box.claim() is None
    assert sql(clean, "SELECT status, payload FROM estado.updates WHERE update_id=9") == [
        ("falhou", None)
    ]
    await box.close()


async def test_backpressure_when_too_many_pending(state_url, clean):
    box = inbox(state_url, max_pending=2)
    assert await box.register(1, {"update_id": 1}) == "received"
    assert await box.register(2, {"update_id": 2}) == "received"
    assert await box.register(3, {"update_id": 3}) == "full"
    await box.claim()
    await box.done(1)  # libera espaço
    assert await box.register(3, {"update_id": 3}) == "received"
    await box.close()


async def test_old_finished_rows_are_purged_but_recent_ones_keep_dedup(state_url, clean):
    box = inbox(state_url, retention_seconds=3600)
    for i in (1, 2):
        await box.register(i, {"update_id": i})
        await box.claim()
        await box.done(i)
    sql(clean, "UPDATE estado.updates SET concluido_em = now() - interval '2 hours' WHERE update_id=1")
    await box.purge()
    assert [r[0] for r in sql(clean, "SELECT update_id FROM estado.updates")] == [2]
    await box.close()


async def test_next_waits_for_new_update(state_url, clean):
    box = inbox(state_url)
    waiter = asyncio.create_task(box.next())
    await asyncio.sleep(0.15)
    assert not waiter.done()
    await box.register(4, {"update_id": 4})
    assert await asyncio.wait_for(waiter, 2) == (4, {"update_id": 4})
    await box.close()


# --- sessões -------------------------------------------------------------------------------


def turn(text):
    return [{"role": "user", "content": text}, {"role": "assistant", "content": "ok"}]


async def test_history_survives_restart_and_respects_limit(state_url, clean):
    store = PostgresSessionStore(state_url, max_turns=2, ttl=3600)
    async with store.acquire((10, 42)) as session:
        for text in ("a", "b", "c"):
            session.turns.append(turn(text))
    restarted = PostgresSessionStore(state_url, max_turns=2, ttl=3600)
    async with restarted.acquire((10, 42)) as session:
        assert [m["content"] for m in session.history() if m["role"] == "user"] == ["b", "c"]
    async with restarted.acquire((10, 43)) as session:  # outro usuário: isolado
        assert session.history() == []


async def test_clear_is_persisted(state_url, clean):
    store = PostgresSessionStore(state_url, max_turns=4, ttl=3600)
    async with store.acquire((1, 1)) as session:
        session.turns.append(turn("a"))
    async with store.acquire((1, 1)) as session:
        session.turns.clear()
    async with PostgresSessionStore(state_url, max_turns=4, ttl=3600).acquire((1, 1)) as session:
        assert session.history() == []


async def test_expired_session_loses_history(state_url, clean):
    store = PostgresSessionStore(state_url, max_turns=4, ttl=60)
    async with store.acquire((1, 1)) as session:
        session.turns.append(turn("antigo"))
    sql(clean, "UPDATE estado.sessoes SET atualizado_em = now() - interval '61 seconds'")
    async with store.acquire((1, 1)) as session:
        assert session.history() == []


async def test_two_processes_serialize_the_same_conversation(state_url, clean):
    proc_a = PostgresSessionStore(state_url, max_turns=4, ttl=3600)
    proc_b = PostgresSessionStore(state_url, max_turns=4, ttl=3600)
    order = []

    async def second():
        async with proc_b.acquire((1, 1)) as session:
            order.append(("b", len(session.turns)))

    async with proc_a.acquire((1, 1)) as session:
        task = asyncio.create_task(second())
        await asyncio.sleep(0.2)
        assert order == []  # b espera o lock de a
        session.turns.append(turn("de a"))
    await asyncio.wait_for(task, 3)
    assert order == [("b", 1)]  # b enxerga o que a gravou


async def test_lock_wait_timeout_becomes_busy_error(state_url, clean):
    holder = PostgresSessionStore(state_url, max_turns=4, ttl=3600)
    waiter = PostgresSessionStore(state_url, max_turns=4, ttl=3600, lock_timeout=0.3)
    async with holder.acquire((1, 1)):
        with pytest.raises(SessionsBusy):
            async with waiter.acquire((1, 1)):
                pytest.fail("Não deveria obter o lock.")


# --- permissões da role de estado -----------------------------------------------------------


def test_state_role_is_restricted_to_state_tables(admin_url, state_url, clean):
    sql(admin_url, "CREATE TABLE IF NOT EXISTS public.segredo_teste (x int)")
    try:
        with psycopg.connect(state_url, autocommit=True) as conn:
            flags = conn.execute(
                "SELECT rolsuper, rolcreaterole, rolcreatedb FROM pg_roles "
                "WHERE rolname = current_user"
            ).fetchone()
            assert flags == (False, False, False)
            conn.execute("INSERT INTO estado.updates (update_id, payload) VALUES (1, '{}')")
            for forbidden in (
                "SELECT * FROM public.segredo_teste",
                "CREATE TABLE public.nova (x int)",
                "ALTER TABLE estado.updates ADD COLUMN y int",
                "DROP TABLE estado.sessoes",
            ):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    conn.execute(forbidden)
    finally:
        sql(admin_url, "DROP TABLE IF EXISTS public.segredo_teste")


def test_initialize_state_is_idempotent_and_requires_a_real_password(admin_url, state_url):
    with psycopg.connect(admin_url, autocommit=True) as conn:
        initialize_state(conn, STATE_PASSWORD)  # segunda execução não falha
        with pytest.raises(ValueError):
            initialize_state(conn, "troque_a_senha_de_estado")


# --- backend com estado durável -------------------------------------------------------------


class Agent:
    def __init__(self):
        self.histories = []

    async def answer(self, text, history):
        self.histories.append(history)
        return "Resposta em português.", turn(text)

    async def close(self):
        pass


class Sender:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.sent.append((chat_id, text))


def update(id=1, user=42, text="Qual o faturamento?"):
    return {
        "update_id": id,
        "message": {
            "message_id": id,
            "date": int(datetime.now(timezone.utc).timestamp()),
            "chat": {"id": user, "type": "private"},
            "from": {"id": user, "is_bot": False, "first_name": "Teste"},
            "text": text,
        },
    }


def make_app(state_url, agent, sender):
    settings = Settings(
        _env_file=None,
        telegram_webhook_secret="test-secret",
        telegram_allowed_user_ids="42",
        state_database_url=state_url,
    )
    return create_app(settings, agent=agent, sender=sender)


HEADERS = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}


async def post(app, payload):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        return await client.post("/telegram/webhook", json=payload, headers=HEADERS)


async def test_duplicate_after_restart_is_not_answered_twice(state_url, clean):
    agent, sender = Agent(), Sender()
    app = make_app(state_url, agent, sender)
    async with app.router.lifespan_context(app):
        assert (await post(app, update(1))).json() == {"status": "recebido"}
        await app.state.inbox.join()
    assert len(sender.sent) == 1

    app2 = make_app(state_url, agent, sender)  # reinício do processo
    async with app2.router.lifespan_context(app2):
        assert (await post(app2, update(1))).json() == {"status": "já recebido"}
        await app2.state.inbox.join()
    assert len(sender.sent) == 1


async def test_update_accepted_before_a_crash_is_answered_after_restart(state_url, clean):
    crashed = inbox(state_url)
    await crashed.register(1, update(1))  # aceito (200 enviado) e o processo caiu
    await crashed.close()

    agent, sender = Agent(), Sender()
    app = make_app(state_url, agent, sender)
    async with app.router.lifespan_context(app):
        await asyncio.wait_for(app.state.inbox.join(), 5)
    assert sender.sent == [(42, "Resposta em português.")]


async def test_history_is_kept_across_restarts(state_url, clean):
    agent, sender = Agent(), Sender()
    for update_id, question in ((1, "Qual o faturamento?"), (2, "janeiro de 2025")):
        app = make_app(state_url, agent, sender)
        async with app.router.lifespan_context(app):
            await post(app, update(update_id, text=question))
            await app.state.inbox.join()
    assert agent.histories[0] == []
    assert [m["content"] for m in agent.histories[1] if m["role"] == "user"] == [
        "Qual o faturamento?"
    ]


async def test_two_backend_processes_share_the_inbox_without_double_answer(state_url, clean):
    agent, sender = Agent(), Sender()
    app_a, app_b = make_app(state_url, agent, sender), make_app(state_url, agent, sender)
    async with app_a.router.lifespan_context(app_a), app_b.router.lifespan_context(app_b):
        for i in range(1, 7):
            await post(app_a if i % 2 else app_b, update(i, text=f"p{i}"))
        await asyncio.wait_for(app_a.state.inbox.join(), 10)
        await asyncio.wait_for(app_b.state.inbox.join(), 10)
    assert len(sender.sent) == 6
    # O lock por conversa serializa os dois processos: cada pergunta enxerga exatamente os
    # turnos gravados pelas anteriores, sem perder nem repetir nenhum.
    assert sorted(len(h) for h in agent.histories) == [0, 2, 4, 6, 8, 10]


async def test_full_inbox_returns_503(state_url, clean):
    settings = Settings(
        _env_file=None,
        telegram_webhook_secret="test-secret",
        telegram_allowed_user_ids="42",
        state_database_url=state_url,
        inbox_max_pending=1,
    )
    sender = Sender()

    class Slow(Agent):
        async def answer(self, text, history):
            await asyncio.sleep(0.5)
            return await super().answer(text, history)

    app = create_app(settings, agent=Slow(), sender=sender)
    async with app.router.lifespan_context(app):
        statuses = [(await post(app, update(i, text=f"p{i}"))).status_code for i in range(1, 6)]
        assert 503 in statuses
        await asyncio.wait_for(app.state.inbox.join(), 10)


async def test_health_reports_durable_state(state_url, clean):
    app = make_app(state_url, Agent(), Sender())
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            assert (await client.get("/health")).json()["estado_duravel"] is True
