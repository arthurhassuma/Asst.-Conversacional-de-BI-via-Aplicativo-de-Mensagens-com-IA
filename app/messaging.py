"""Regras de mensageria compartilhadas pelo webhook e pelo polling local."""

import asyncio
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.error import NetworkError, RetryAfter

from app.bi_agent import FAILURE
from app.sessions import SessionsBusy

logger = logging.getLogger(__name__)


def clarification_keyboard(text):
    """Opções controladas enviam texto normal e mantêm o contexto/autorização do chat."""
    if "Qual métrica deseja consultar:" in text or "Informe a métrica e o período." in text:
        return ReplyKeyboardMarkup(
            [
                ["Faturamento emitido", "Recebimentos"],
                ["Pedidos", "Contratos", "Clientes"],
                ["Horas", "Chamados"],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder="Escolha a métrica",
        )
    choices = {
        "Para pedidos de serviços,": [["Valor", "Quantidade", "Ambos"]],
        "Para contratos,": [["Valor", "Quantidade", "Ambos"]],
        "Para horas de trabalho,": [["Horas previstas", "Horas realizadas"], ["Ambas"]],
        "Para chamados operacionais,": [
            ["Chamados abertos", "Chamados resolvidos"],
            ["Taxa de resolução"],
        ],
        "Para clientes,": [["Quantidade de clientes"]],
        "Para faturamento emitido,": [["Valor total emitido"]],
        "Para recebimentos,": [["Valor total recebido"]],
    }
    for prefix, keyboard in choices.items():
        if text.removeprefix("💬 ").startswith(prefix):
            return ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True,
                input_field_placeholder="Escolha uma opção ou digite",
            )
    return ReplyKeyboardRemove()


def message_chunks(text: str):
    # Margem para limite UTF-16 do Telegram; separa linhas, preservando cada célula.
    chunks, current = [], ""
    for line in text.splitlines():
        if len(line.encode("utf-16-le")) // 2 > 3500:
            return [
                "O resultado contém um registro muito extenso. Peça um resumo ou refine os filtros."
            ]
        candidate = current + ("\n" if current else "") + line
        if len(candidate.encode("utf-16-le")) // 2 > 3500:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


class TelegramService:
    def __init__(self, settings, agent, sessions, sender):
        self.settings, self.agent, self.sessions, self.sender = settings, agent, sessions, sender

    async def send(self, chat_id, text):
        chunks = message_chunks(text)
        for index, chunk in enumerate(chunks):
            markup = (
                {"reply_markup": clarification_keyboard(text)} if index == len(chunks) - 1 else {}
            )
            for attempt in range(3):
                try:
                    await self.sender.send_message(chat_id=chat_id, text=chunk, **markup)
                    break
                except RetryAfter as exc:
                    if attempt == 2:
                        raise
                    seconds = exc.retry_after
                    if hasattr(seconds, "total_seconds"):
                        seconds = seconds.total_seconds()
                    await asyncio.sleep(min(float(seconds), 30))
                except NetworkError:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(attempt + 1)

    async def process(self, payload):
        update = Update.de_json(payload, None)
        msg, user = update.message, update.effective_user
        if (
            not msg
            or not user
            or msg.chat.type != "private"
            or user.id not in self.settings.allowed_users
            or user.is_bot
        ):
            return
        if not msg.text:
            await self.send(msg.chat_id, "Envie sua pergunta como mensagem de texto, por favor.")
            return
        key = (msg.chat_id, user.id)
        try:
            async with self.sessions.acquire(key) as session:
                command = msg.text.split()[0].split("@")[0]
                if command.casefold() in ("/start", "/help", "/comecar", "/começar", "/ajuda"):
                    text = (
                        "Olá! Consulto dados de negócio. Informe a métrica e o período. "
                        "Por exemplo: qual o faturamento em janeiro do ano desejado? "
                        "Use /limpar para apagar o histórico desta conversa."
                    )
                elif command == "/limpar":
                    session.turns.clear()
                    text = "Histórico desta conversa apagado."
                elif command.startswith("/"):
                    text = "Comando não reconhecido. Use /ajuda ou envie uma pergunta de negócio."
                else:
                    text, turn = await self.agent.answer(msg.text, session.history())
                    if turn:
                        session.turns.append(turn)
                await self.send(msg.chat_id, text)
        except SessionsBusy as exc:
            await self.send(msg.chat_id, str(exc))
        except Exception:
            logger.error("falha_processamento_mensagem")
            # Não revelar traceback, perguntas, respostas ou token nos logs.
            await self.send(msg.chat_id, FAILURE)
