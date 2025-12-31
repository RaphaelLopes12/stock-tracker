from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Stock Tracker"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://stocktracker:stocktracker@localhost:5432/stock_tracker"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # APIs externas
    brapi_token: str | None = None

    # Telegram
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    # AI Features
    ai_enabled: bool = False

    # Collector intervals (em minutos)
    price_collector_interval: int = 15
    fundamentals_collector_interval: int = 1440  # 24h
    news_collector_interval: int = 30
    cvm_collector_interval: int = 60


settings = Settings()
