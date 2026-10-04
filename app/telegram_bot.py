"""Polling encaminha ao FastAPI; register-webhook configura a entrega HTTPS."""

import asyncio
import logging
import re

import httpx
from telegram import Bot
from telegram.error import TelegramError

from app.cli_support import PortugueseArgumentParser
from app.config import Settings


async def forward_update(client, update, backend_url, secret):
    result = await client.post(
        backend_url + "/telegram/webhook",
        json=update.to_dict(),
        headers={"X-Telegram-Bot-Api-Secret-Token": secret},
    )
    result.raise_for_status()


async def run(command, backend_url):
    settings = Settings()
    token = settings.telegram_bot_token.get_secret_value()
    secret = settings.telegram_webhook_secret.get_secret_value()
    if not token or not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", secret):
        raise ValueError(
            "Configure TELEGRAM_BOT_TOKEN e um TELEGRAM_WEBHOOK_SECRET válido no .env."
        )
    if not settings.allowed_users:
        raise ValueError("Configure TELEGRAM_ALLOWED_USER_IDS antes de iniciar o bot.")
    for name in ("httpx", "httpcore", "telegram"):
        logging.getLogger(name).setLevel(logging.WARNING)
    async with Bot(token) as bot:
        if command == "register-webhook":
            url = settings.telegram_webhook_url
            if not url.startswith("https://") or not url.endswith("/telegram/webhook"):
                raise ValueError(
                    "TELEGRAM_WEBHOOK_URL deve ser HTTPS e terminar em /telegram/webhook."
                )
            await bot.set_webhook(
                url, secret_token=secret, allowed_updates=["message"], drop_pending_updates=False
            )
            print("Webhook registrado. Mantenha o backend em execução.")
            return
        # Valide o backend antes de desativar o webhook remoto.
        async with httpx.AsyncClient(timeout=15) as client:
            health = await client.get(backend_url + "/health")
            health.raise_for_status()
            if not health.json().get("telegram_configurado"):
                raise ValueError("Inicie o backend com o token configurado antes do polling.")
            await bot.delete_webhook(drop_pending_updates=False)
            print("Polling ativo. Envie uma mensagem privada ao bot.")
            offset = None
            while True:
                try:
                    updates = await bot.get_updates(
                        offset=offset, timeout=25, allowed_updates=["message"]
                    )
                    for update in updates:
                        # Não avança o offset se o backend não aceitar a mensagem.
                        await forward_update(client, update, backend_url, secret)
                        offset = update.update_id + 1
                except (TelegramError, httpx.HTTPError):
                    print("Falha temporária de conexão. Tentando novamente.")
                    await asyncio.sleep(3)


def main():
    parser = PortugueseArgumentParser(description="Conexão Telegram do assistente de BI")
    parser.add_argument("command", choices=["polling", "register-webhook"])
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        asyncio.run(run(args.command, args.backend_url.rstrip("/")))
    except KeyboardInterrupt:
        print("\nConexão encerrada.")
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
    except (TelegramError, httpx.HTTPError):
        parser.exit(1, "Falha de conexão. Verifique o backend e as credenciais locais.\n")


if __name__ == "__main__":
    main()
