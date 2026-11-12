import asyncio
import json
import logging
import re

from google import genai
from google.genai import types
from google.genai.errors import APIError
from telegram import Bot

from app.bi_agent import api_error_message, response_content
from app.cli_support import PortugueseArgumentParser
from app.config import Settings
from app.database_tools import DatabaseTools
from app.sql_policy import TABLES


async def check_database(settings):
    schema = await asyncio.to_thread(DatabaseTools(settings).get_schema)
    tables = schema.get("tables", {})
    if "error" in schema or any(not tables.get(name) for name in TABLES):
        raise ValueError("Banco ou schema indisponível.")
    return "Conexão somente leitura e metadados das tabelas verificados."


async def check_gemini(settings):
    client = genai.Client(
        api_key=settings.gemini_api_key.get_secret_value(),
        vertexai=False,
        http_options=types.HttpOptions(
            api_version="v1beta",
            timeout=15000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents="Responda apenas com a frase: Conexão verificada.",
            config=types.GenerateContentConfig(
                max_output_tokens=256,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        content = response_content(response)
        if not any(
            part.text and part.text.strip() and not part.thought for part in content.parts or []
        ):
            raise ValueError("Resposta vazia.")
        return "O modelo configurado respondeu. Function calling e acerto do SQL exigem teste funcional."
    finally:
        await client.aio.aclose()
        client.close()


async def check_telegram(settings):
    async with Bot(settings.telegram_bot_token.get_secret_value()):
        return "Token autenticado com getMe. Recebimento e entrega de mensagens exigem teste funcional."


async def diagnose(settings: Settings, *, test_connections=False):
    for name in ("httpx", "httpcore", "telegram", "google.genai"):
        logging.getLogger(name).setLevel(logging.WARNING)
    try:
        users_valid = bool(settings.allowed_users) and all(
            user > 0 for user in settings.allowed_users
        )
    except ValueError:
        users_valid = False
    secret_valid = bool(
        re.fullmatch(r"[A-Za-z0-9_-]{16,256}", settings.telegram_webhook_secret.get_secret_value())
    )
    checks = {
        "banco": (
            bool(settings.database_url.get_secret_value()),
            check_database,
            "Configure DATABASE_URL com readonly_agent.",
            "Verifique conexão, role somente leitura e as tabelas do schema.",
        ),
        "gemini": (
            bool(settings.gemini_api_key.get_secret_value())
            and bool(settings.gemini_model.strip()),
            check_gemini,
            "Configure GEMINI_API_KEY e GEMINI_MODEL.",
            "Não foi possível obter resposta do Gemini. Verifique modelo, chave e conexão.",
        ),
        "telegram": (
            bool(settings.telegram_bot_token.get_secret_value()),
            check_telegram,
            "Configure TELEGRAM_BOT_TOKEN.",
            "Não foi possível autenticar o Telegram. Verifique token e conexão.",
        ),
    }
    report = {}
    for name, (configured, probe, missing, failure) in checks.items():
        if not configured:
            report[name] = {"status": "pendente", "detalhe": missing}
        elif not test_connections:
            report[name] = {"status": "configurado", "detalhe": "Conexão não testada."}
        else:
            try:
                async with asyncio.timeout(25):
                    detail = await probe(settings)
                report[name] = {"status": "confirmado", "detalhe": detail}
            except APIError as exc:
                detail = api_error_message(exc.code) if name == "gemini" else failure
                report[name] = {"status": "falhou", "detalhe": detail}
            except Exception:
                report[name] = {"status": "falhou", "detalhe": failure}
    report["acesso_telegram"] = {
        "status": "configurado" if users_valid and secret_valid else "pendente",
        "detalhe": (
            "Lista de usuários e segredo válidos no formato; autorização ponta a ponta não testada."
            if users_valid and secret_valid
            else "Configure TELEGRAM_ALLOWED_USER_IDS com IDs positivos e TELEGRAM_WEBHOOK_SECRET válido."
        ),
    }
    return report


def main():
    parser = PortugueseArgumentParser(description="Diagnóstico seguro das conexões do assistente")
    parser.add_argument(
        "--testar-conexoes",
        action="store_true",
        help="testa PostgreSQL, Gemini e Telegram; consome uma chamada da cota Gemini",
    )
    args = parser.parse_args()
    try:
        settings = Settings()
    except ValueError:
        parser.exit(
            1, "Configuração inválida. Confira os valores do .env sem compartilhar segredos.\n"
        )
    try:
        report = asyncio.run(diagnose(settings, test_connections=args.testar_conexoes))
    except KeyboardInterrupt:
        parser.exit(1, "\nDiagnóstico interrompido.\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if any(item["status"] in {"falhou", "pendente"} for item in report.values()):
        parser.exit(1)


if __name__ == "__main__":
    main()
