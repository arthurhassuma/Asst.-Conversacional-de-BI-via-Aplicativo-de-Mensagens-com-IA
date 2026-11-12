import getpass
import os
import re
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent / "private"
if root.exists() and any(root.iterdir()):
    raise SystemExit("Configuração privada já existe; não será sobrescrita.")
root.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(root, 0o700)
token = getpass.getpass("Token existente do Telegram (entrada oculta): ").strip()
key = getpass.getpass("Chave existente do Gemini (entrada oculta): ").strip()
users = getpass.getpass("IDs Telegram autorizados, separados por vírgula (entrada oculta): ").strip()
model = input("Mesmo GEMINI_MODEL já utilizado [gemini-3.5-flash-lite]: ").strip() or "gemini-3.5-flash-lite"
if not token or not key or not re.fullmatch(r"\d+(?:\s*,\s*\d+)*", users):
    raise SystemExit("Campos obrigatórios inválidos; nenhum arquivo criado.")
if any("\n" in value or "\r" in value for value in (token, key, users, model)):
    raise SystemExit("Valor inválido.")
admin, reader, webhook = (secrets.token_hex(32) for _ in range(3))
files = {
    "database.env": f"POSTGRES_DB=bi_comparativo\nPOSTGRES_USER=bi_owner\nPOSTGRES_PASSWORD={admin}\n",
    "setup.env": f"ADMIN_DATABASE_URL=postgresql://bi_owner:{admin}@db:5432/bi_comparativo\nREADONLY_PASSWORD={reader}\n",
    "application.env": (
        f"DATABASE_URL=postgresql://readonly_agent:{reader}@db:5432/bi_comparativo\n"
        f"GEMINI_API_KEY={key}\nGEMINI_MODEL={model}\nTELEGRAM_BOT_TOKEN={token}\n"
        f"TELEGRAM_ALLOWED_USER_IDS={users}\nTELEGRAM_WEBHOOK_SECRET={webhook}\n"
        "INTENT_CLASSIFIER_ENABLED=false\n"
    ),
}
for name, text in files.items():
    fd = os.open(root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(text)
print("Configuração gravada privadamente. Não publique nem envie esses arquivos.")
