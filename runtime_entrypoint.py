"""Carrega configuração privada montada; nunca grava credenciais na imagem."""

import os
import sys
import time

import httpx
from pydantic import SecretStr

from app.config import Settings


def configured():
    settings = Settings(_env_file=os.getenv("PAC_CONFIG_FILE", "/run/secrets/application.env"))
    database_file = os.getenv("PAC_DATABASE_CONFIG_FILE")
    if database_file:
        db = Settings(_env_file=database_file)
        settings = settings.model_copy(update={"database_url": db.database_url})
    mode = sys.argv[1] if len(sys.argv) > 1 else "backend"
    if mode != "manage-db":
        settings = settings.model_copy(update={
            "admin_database_url": SecretStr(""),
            "readonly_password": SecretStr(""),
        })
    for name, value in settings.__dict__.items():
        os.environ[name.upper()] = (
            value.get_secret_value() if hasattr(value, "get_secret_value") else str(value)
        )
    return settings, mode


def main():
    _, mode = configured()
    if mode == "backend":
        args = ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port",
                os.getenv("PAC_PORT", "8000"), "--workers", "1"]
    elif mode == "polling":
        url = os.getenv("PAC_BACKEND_URL", "http://backend:8000")
        for _ in range(60):
            try:
                response = httpx.get(url + "/health", timeout=2)
                if response.status_code == 200 and response.json().get("telegram_configurado"):
                    break
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(1)
        else:
            raise SystemExit("Backend indisponível; o container será reiniciado pelo Docker.")
        args = ["-m", "app.telegram_bot", "polling", "--backend-url", url]
    elif mode == "manage-db":
        args = ["-m", "scripts.manage_db", *sys.argv[2:]]
    else:
        raise SystemExit("Modo inválido.")
    os.execv(sys.executable, [sys.executable, *args])


if __name__ == "__main__":
    main()
