from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from env vars (prefix CHAT_) or a local .env file.

    Example: CHAT_LOG_LEVEL=DEBUG CHAT_LOG_JSON=false uvicorn ...
    Secrets never get a default value here; in AWS they come from Secrets Manager.
    """

    model_config = SettingsConfigDict(env_prefix="CHAT_", env_file=".env", extra="ignore")

    app_name: str = "chat-service"
    log_level: str = "INFO"
    log_json: bool = True
    token_delay_seconds: float = 0.05
