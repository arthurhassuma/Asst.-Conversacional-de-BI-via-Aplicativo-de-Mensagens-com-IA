from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: SecretStr = SecretStr("")
    admin_database_url: SecretStr = SecretStr("")
    readonly_password: SecretStr = SecretStr("")
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.5-flash-lite"
    intent_classifier_enabled: bool = True
    intent_model_path: str = ""
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_webhook_secret: SecretStr = SecretStr("")
    telegram_webhook_url: str = ""
    telegram_allowed_user_ids: str = ""
    query_timeout_ms: int = Field(3000, ge=50, le=30000)
    max_query_rows: int = Field(100, ge=1, le=500)
    session_ttl_seconds: int = Field(3600, ge=60)
    max_sessions: int = Field(1000, ge=1, le=10000)
    max_history_turns: int = Field(8, ge=1, le=20)
    max_tool_rounds: int = Field(6, ge=1, le=10)
    max_sql_errors: int = Field(3, ge=1, le=5)

    @property
    def allowed_users(self) -> set[int]:
        return {int(x.strip()) for x in self.telegram_allowed_user_ids.split(",") if x.strip()}
