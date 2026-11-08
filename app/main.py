"""Backend FastAPI. Execute com um único worker: sessões/fila estão em memória."""

import asyncio
import hmac
import json
import logging
from collections import OrderedDict
from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from telegram import Bot, Update

from app.bi_agent import BIAgent
from app.config import Settings
from app.messaging import TelegramService
from app.sessions import SessionStore

logger = logging.getLogger(__name__)


def create_app(settings=None, *, agent=None, sender=None):
    settings = settings or Settings()
    agent = agent or BIAgent(settings)
    sessions = SessionStore(
        settings.max_sessions, settings.max_history_turns, settings.session_ttl_seconds
    )
    queue = asyncio.Queue(maxsize=100)
    seen = OrderedDict()
    owned_bot = None
    workers = []

    @asynccontextmanager
    async def lifespan(app):
        nonlocal sender, owned_bot
        app_logger = logging.getLogger("app")
        if not app_logger.handlers:
            # Sem isto o INFO dos módulos do projeto não chega ao log do container.
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
            app_logger.addHandler(handler)
            app_logger.setLevel(logging.INFO)
        # httpx INFO registra URLs que contêm o token do Telegram.
        for name in ("httpx", "httpcore", "telegram", "google.genai"):
            logging.getLogger(name).setLevel(logging.WARNING)
        if sender is None and settings.telegram_bot_token.get_secret_value():
            owned_bot = Bot(settings.telegram_bot_token.get_secret_value())
            try:
                await owned_bot.initialize()
            except Exception:
                raise RuntimeError(
                    "Não foi possível autenticar o bot. Verifique TELEGRAM_BOT_TOKEN."
                ) from None
            sender = owned_bot
        service = TelegramService(settings, agent, sessions, sender)
        app.state.ready = sender is not None

        async def worker():
            while True:
                payload = await queue.get()
                try:
                    await service.process(payload)
                except Exception:
                    logger.error("falha_entrega_telegram")
                    seen.pop(payload["update_id"], None)
                finally:
                    queue.task_done()

        workers.extend(asyncio.create_task(worker()) for _ in range(4))
        try:
            yield
        finally:
            try:
                await asyncio.wait_for(queue.join(), timeout=10)
            except TimeoutError:
                logger.warning("encerramento_com_mensagens_pendentes")
            for task in workers:
                task.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            await agent.close()
            if owned_bot:
                await owned_bot.shutdown()

    app = FastAPI(title="Assistente de BI — PAC", lifespan=lifespan)
    app.state.queue, app.state.sessions = queue, sessions
    app.state.ready = False

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(status_code=400, content={"detail": "Requisição inválida."})

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        detail = {404: "Rota não encontrada.", 405: "Método não permitido."}.get(
            exc.status_code, exc.detail
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @app.get("/health")
    async def health():
        return {
            "status": "em execução",
            "telegram_configurado": app.state.ready,
            "ia_configurada": bool(settings.gemini_api_key.get_secret_value()),
            "banco_configurado": bool(settings.database_url.get_secret_value()),
        }

    @app.post("/telegram/webhook")
    async def webhook(request: Request):
        expected = settings.telegram_webhook_secret.get_secret_value()
        received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not expected or not hmac.compare_digest(received.encode(), expected.encode()):
            raise HTTPException(403, "Acesso não autorizado.")
        if not app.state.ready:
            raise HTTPException(503, "O bot ainda não está configurado.")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                raise HTTPException(413, "Mensagem acima do tamanho permitido.")
        try:
            payload = json.loads(body)
            if (
                not isinstance(payload, dict)
                or type(payload.get("update_id")) is not int
                or payload["update_id"] < 0
            ):
                raise ValueError()
            Update.de_json(payload, None)
        except (ValueError, TypeError, KeyError, AttributeError):
            raise HTTPException(400, "Mensagem do Telegram inválida.") from None
        now = monotonic()
        for update_id, timestamp in list(seen.items()):
            if now - timestamp > 86400:
                del seen[update_id]
        if payload["update_id"] in seen:
            return {"status": "já recebido"}
        if queue.full():
            raise HTTPException(503, "O assistente está ocupado. Tente novamente.")
        seen[payload["update_id"]] = now
        if len(seen) > 10000:
            seen.popitem(last=False)
        queue.put_nowait(payload)
        return {"status": "recebido"}

    return app


app = create_app()
