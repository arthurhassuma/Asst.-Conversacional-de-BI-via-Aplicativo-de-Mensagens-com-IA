from datetime import datetime, timezone

import httpx
from telegram import Chat, Message, Update, User

from app.telegram_bot import forward_update


async def test_polling_forwards_dates_as_json_timestamps():
    msg = Message(
        message_id=1,
        date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=42, type="private"),
        from_user=User(42, "Teste", False),
        text="Olá",
    )
    captured = []

    def receive(request):
        import json

        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"status": "recebido"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(receive)) as client:
        await forward_update(client, Update(1, message=msg), "http://localhost", "secret")
    assert captured[0]["message"]["date"] == 1735689600
    assert captured[0]["message"]["text"] == "Olá"
