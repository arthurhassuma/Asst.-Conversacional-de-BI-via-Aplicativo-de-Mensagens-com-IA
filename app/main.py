import asyncio
import hmac
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from telegram import Bot, Update

from app import metrics
from app.bi_agent import BIAgent
from app.config import Settings
from app.messaging import TelegramService
from app.sessions import SessionStore
from app.state import DUPLICATE, FULL, MemoryInbox, PostgresInbox, PostgresSessionStore

logger = logging.getLogger(__name__)


def create_app(settings=None, *, agent=None, sender=None):
    settings = settings or Settings()
    agent = agent or BIAgent(settings)
    state_dsn = settings.state_database_url.get_secret_value()
    if state_dsn:
        sessions = PostgresSessionStore(
            state_dsn, settings.max_history_turns, settings.session_ttl_seconds
        )
        inbox = PostgresInbox(state_dsn, max_pending=settings.inbox_max_pending)
    else:
        sessions = SessionStore(
            settings.max_sessions, settings.max_history_turns, settings.session_ttl_seconds
        )
        inbox = MemoryInbox(settings.inbox_max_pending)
    owned_bot = None
    workers = []

    @asynccontextmanager
    async def lifespan(app):
        nonlocal sender, owned_bot
        app_logger = logging.getLogger("app")
        if not app_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
            app_logger.addHandler(handler)
            app_logger.setLevel(logging.INFO)
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
        await inbox.start()
        app.state.ready = sender is not None

        async def settle(action, update_id):
            try:
                await action(update_id)
            except Exception:
                logger.error("falha_estado_duravel")

        async def worker():
            while True:
                update_id, payload = await inbox.next()
                try:
                    await service.process(payload)
                except Exception:
                    logger.error("falha_entrega_telegram")
                    await settle(inbox.retry, update_id)
                else:
                    await settle(inbox.done, update_id)

        workers.extend(asyncio.create_task(worker()) for _ in range(4))
        try:
            yield
        finally:
            try:
                await asyncio.wait_for(inbox.join(), timeout=10)
            except TimeoutError:
                logger.warning("encerramento_com_mensagens_pendentes")
            for task in workers:
                task.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            await agent.close()
            await inbox.close()
            if owned_bot:
                await owned_bot.shutdown()

    app = FastAPI(title="Assistente de BI — PAC", lifespan=lifespan)
    app.state.inbox, app.state.sessions = inbox, sessions
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
            "estado_duravel": bool(state_dsn),
        }

    @app.get("/metrics")
    async def metrics_endpoint(request: Request):
        token = settings.metrics_token.get_secret_value()
        if token:
            received = request.headers.get("Authorization", "")
            if not hmac.compare_digest(received.encode(), f"Bearer {token}".encode()):
                raise HTTPException(403, "Acesso não autorizado.")
        return Response(metrics.render(), media_type=metrics.CONTENT_TYPE)

    @app.post("/telegram/webhook")
    async def webhook(request: Request):
        expected = settings.telegram_webhook_secret.get_secret_value()
        received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not expected or not hmac.compare_digest(received.encode(), expected.encode()):
            metrics.UPDATES.inc("recusado_autenticacao")
            raise HTTPException(403, "Acesso não autorizado.")
        if not app.state.ready:
            metrics.UPDATES.inc("bot_nao_configurado")
            raise HTTPException(503, "O bot ainda não está configurado.")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                metrics.UPDATES.inc("corpo_grande")
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
            metrics.UPDATES.inc("invalido")
            raise HTTPException(400, "Mensagem do Telegram inválida.") from None
        try:
            outcome = await inbox.register(payload["update_id"], payload)
        except Exception:
            logger.error("falha_estado_duravel")
            metrics.UPDATES.inc("falha_estado")
            raise HTTPException(503, "O assistente está indisponível. Tente novamente.") from None
        if outcome == DUPLICATE:
            metrics.UPDATES.inc("duplicado")
            return {"status": "já recebido"}
        if outcome == FULL:
            metrics.UPDATES.inc("fila_cheia")
            raise HTTPException(503, "O assistente está ocupado. Tente novamente.")
        metrics.UPDATES.inc("aceito")
        return {"status": "recebido"}

    return app


app = create_app()
