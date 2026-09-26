"""
Central application configuration.
All values can be overridden via environment variables or a `.env` file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    APP_NAME: str = "Smart Electricity Utility Management System"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # --- Database ---
    # Defaults to a local SQLite file so the project runs with zero setup.
    # Swap to a Postgres URL in production, e.g.:
    # postgresql+psycopg2://user:password@localhost:5432/electricity_db
    DATABASE_URL: str = "sqlite:///./electricity.db"

    # --- JWT / Auth ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_super_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: str = "*"

    # --- Rate limiting (simple in-memory limiter, see utils/rate_limit.py) ---
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- Billing defaults ---
    LATE_FEE_FLAT_AMOUNT: float = 100.0
    TAX_PERCENTAGE: float = 5.0
    BILL_DUE_DAYS: int = 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
