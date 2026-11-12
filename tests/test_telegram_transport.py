from datetime import datetime, timezone

import httpx
import pytest
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


def make_update(update_id):
    msg = Message(
        message_id=update_id,
        date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=42, type="private"),
        from_user=User(42, "Teste", False),
        text="Olá",
    )
    return Update(update_id, message=msg)


async def run_batch(statuses, ids=(1, 2, 3)):
    import json

    from app.telegram_bot import forward_updates

    received, offsets = [], []

    def receive(request):
        update_id = json.loads(request.content)["update_id"]
        received.append(update_id)
        return httpx.Response(statuses.get(update_id, 200), json={})

    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(receive)) as client:
            updates = [make_update(i) for i in ids]
            async for offset in forward_updates(client, updates, "http://localhost", "secret"):
                offsets.append(offset)
    except httpx.HTTPStatusError as error:
        return received, offsets, error.response.status_code
    return received, offsets, None


@pytest.mark.parametrize("status", [400, 413, 422])
async def test_an_update_the_backend_permanently_rejects_is_skipped_not_retried_forever(status):
    received, offsets, error = await run_batch({2: status})
    assert error is None
    assert received == [1, 2, 3]
    assert offsets == [2, 3, 4]


@pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
async def test_temporary_or_configuration_errors_keep_the_update_for_a_retry(status):
    received, offsets, error = await run_batch({2: status})
    assert error == status
    assert received == [1, 2]
    assert offsets == [2]
