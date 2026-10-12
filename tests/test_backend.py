from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.main import create_app


class Agent:
    def __init__(self):
        self.histories = []

    async def answer(self, text, history):
        self.histories.append(history)
        return "Resposta em português.", [
            {"role": "user", "content": text},
            {"role": "assistant", "content": "Resposta em português."},
        ]

    async def close(self):
        pass


class Sender:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.sent.append((chat_id, text))


def update(id=1, user=42, text="Qual o faturamento?", chat_type="private"):
    return {
        "update_id": id,
        "message": {
            "message_id": id,
            "date": int(datetime.now(timezone.utc).timestamp()),
            "chat": {"id": user, "type": chat_type},
            "from": {"id": user, "is_bot": False, "first_name": "Teste"},
            "text": text,
        },
    }


async def test_webhook_auth_dedup_and_user_isolation():
    settings = Settings(
        _env_file=None, telegram_webhook_secret="test-secret", telegram_allowed_user_ids="42,43"
    )
    agent, sender = Agent(), Sender()
    app = create_app(settings, agent=agent, sender=sender)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            assert (await client.post("/telegram/webhook", json=update())).status_code == 403
            headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
            first = await client.post("/telegram/webhook", json=update(), headers=headers)
            assert first.status_code == 200
            await app.state.queue.join()
            assert len(sender.sent) == 1
            await client.post("/telegram/webhook", json=update(), headers=headers)
            await app.state.queue.join()
            assert len(sender.sent) == 1
            await client.post("/telegram/webhook", json=update(2, 43), headers=headers)
            await app.state.queue.join()
            assert agent.histories == [[], []]
            await client.post(
                "/telegram/webhook", json=update(3, 42, "E pedidos?"), headers=headers
            )
            await app.state.queue.join()
            assert agent.histories[-1][0]["content"] == "Qual o faturamento?"


async def test_unauthorized_users_and_group_messages_cannot_call_agent():
    agent, sender = Agent(), Sender()
    app = create_app(
        Settings(
            _env_file=None, telegram_webhook_secret="test-secret", telegram_allowed_user_ids="42"
        ),
        agent=agent,
        sender=sender,
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
            await client.post("/telegram/webhook", json=update(1, 999), headers=headers)
            await client.post(
                "/telegram/webhook", json=update(2, 42, chat_type="group"), headers=headers
            )
            await app.state.queue.join()
            assert not agent.histories
            assert not sender.sent


async def test_malformed_payload_has_portuguese_error():
    app = create_app(
        Settings(_env_file=None, telegram_webhook_secret="test-secret"),
        agent=Agent(),
        sender=Sender(),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            res = await client.post(
                "/telegram/webhook",
                json={"update_id": "inválido"},
                headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
            )
            assert res.status_code == 400
            assert "inválid" in res.json()["detail"]
