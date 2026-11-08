import copy

import pytest
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.config import Settings
from app.managerial_queries import managerial_query
from app.managerial_rendering import render_managerial
from app.messaging import TelegramService
from app.rendering import percent_text
from app.sessions import SessionStore
from tests.test_analysis_contract import PLAN
from tests.test_backend import update


@pytest.mark.parametrize(
    ("value", "display"),
    [
        ("187.8237825408560075", "187,82"),
        ("157.5757575757575758", "157,58"),
        ("-1.005", "-1,01"),
        ("0.00000000000000000000", "0,00"),
        ("-0.004", "0,00"),
        (None, "não informado"),
    ],
)
def test_percentages_are_rounded_for_display(value, display):
    assert percent_text(value) == display


def test_rendering_changes_only_display_not_selected_numeric_data():
    result = {
        "columns": ["base", "atual", "diferenca", "variacao_percentual", "registros"],
        "rows": [["555036.49", "1597527.02", "1042490.53", "187.8237825408560075", 2]],
        "truncated": False,
    }
    before = copy.deepcopy(result)
    text = render_managerial(result, managerial_query(PLAN)["context"])
    assert "Variação percentual: 187,82%" in text
    assert "1.042.490,53" in text
    assert "sintétic" not in text.lower()
    assert result == before


async def test_choice_button_uses_same_conversation_and_keyboard_is_removed_after_answer():
    class Agent:
        def __init__(self):
            self.calls = []

        async def answer(self, text, history):
            self.calls.append((text, history))
            reply = (
                "💬 Para pedidos de venda, você deseja o valor ou a quantidade? Pode pedir ambos."
                if len(self.calls) == 1
                else "Resultado dos pedidos."
            )
            return reply, [
                {"role": "user", "content": text},
                {"role": "assistant", "content": reply},
            ]

    class Sender:
        def __init__(self):
            self.calls = []

        async def send_message(self, **kwargs):
            self.calls.append(kwargs)

    agent, sender = Agent(), Sender()
    service = TelegramService(
        Settings(_env_file=None, telegram_allowed_user_ids="42"),
        agent,
        SessionStore(10, 20, 3600),
        sender,
    )
    await service.process(update(1, text="E os pedidos dos mesmos períodos?"))
    keyboard = sender.calls[-1]["reply_markup"]
    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert [[button.text for button in row] for row in keyboard.keyboard] == [
        ["Valor", "Quantidade", "Ambos"]
    ]
    await service.process(update(2, text="Ambos"))
    assert agent.calls[-1][0] == "Ambos"
    assert agent.calls[-1][1][0]["content"] == "E os pedidos dos mesmos períodos?"
    assert isinstance(sender.calls[-1]["reply_markup"], ReplyKeyboardRemove)
    before = len(agent.calls)
    await service.process(update(3, user=999, text="Ambos"))
    assert len(agent.calls) == before
    await service.process(update(4, text="/limpar"))
    assert isinstance(sender.calls[-1]["reply_markup"], ReplyKeyboardRemove)


async def test_start_has_no_synthetic_notice_and_offers_metrics():
    class Sender:
        calls = []

        async def send_message(self, **kwargs):
            self.calls.append(kwargs)

    sender = Sender()
    service = TelegramService(
        Settings(_env_file=None, telegram_allowed_user_ids="42"),
        None,
        SessionStore(10, 20, 3600),
        sender,
    )
    await service.process(update(text="/start"))
    reply = sender.calls[-1]
    assert "sintétic" not in reply["text"].lower()
    assert isinstance(reply["reply_markup"], ReplyKeyboardMarkup)
