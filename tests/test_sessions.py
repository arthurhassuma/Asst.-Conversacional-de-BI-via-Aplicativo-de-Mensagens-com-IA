import asyncio

import pytest

from app.sessions import SessionsBusy, SessionStore


async def test_conversation_isolation_and_bounded_complete_turns():
    store = SessionStore(max_sessions=3, max_turns=2, ttl=60)
    async with store.acquire("a") as session:
        for i in range(3):
            session.turns.append(
                [{"role": "user", "content": str(i)}, {"role": "assistant", "content": "ok"}]
            )
        assert [m["content"] for m in session.history() if m["role"] == "user"] == ["1", "2"]
    async with store.acquire("b") as session:
        assert session.history() == []


async def test_same_session_serializes_and_active_sessions_are_not_evicted():
    store = SessionStore(max_sessions=1, max_turns=2, ttl=60)
    async with store.acquire("a"):
        with pytest.raises(SessionsBusy):
            async with store.acquire("b"):
                pytest.fail("Uma sessão ativa foi removida.")
        entered = asyncio.Event()

        async def second():
            async with store.acquire("a"):
                entered.set()

        task = asyncio.create_task(second())
        await asyncio.sleep(0)
        assert not entered.is_set()
    await task
    assert entered.is_set()


async def test_expired_session_loses_history():
    now = [0]
    store = SessionStore(max_sessions=2, max_turns=2, ttl=60, clock=lambda: now[0])
    async with store.acquire("a") as session:
        session.turns.append([{"role": "user", "content": "antigo"}])
    now[0] = 61
    async with store.acquire("a") as session:
        assert not session.history()
