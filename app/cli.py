"""CLI local com as mesmas regras e histórico do agente Telegram."""

import asyncio
from collections import deque

from app.bi_agent import BIAgent
from app.config import Settings


async def run():
    settings = Settings()
    agent = BIAgent(settings)
    turns = deque(maxlen=settings.max_history_turns)
    print("Assistente de BI. Digite /sair para encerrar ou /limpar para reiniciar a conversa.")
    try:
        while True:
            try:
                question = await asyncio.to_thread(input, "Você: ")
            except EOFError:
                break
            if question.strip() == "/sair":
                break
            if question.strip() == "/limpar":
                turns.clear()
                print("Histórico apagado.")
                continue
            text, turn = await agent.answer(question, [m for t in turns for m in t])
            if turn:
                turns.append(turn)
            print("Assistente:", text)
    finally:
        await agent.close()


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nConversa encerrada.")


if __name__ == "__main__":
    main()
