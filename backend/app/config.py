from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Stub for T004 skeleton. Auth/LLM/encryption keys added in later tasks (T005+).
    CRM tokens here for initial dev/demo of CrmClient adapters (auth stub).
    """

    # Database (asyncpg via SQLAlchemy)
    DATABASE_URL: str = "postgresql+asyncpg://bdlead:bdlead@localhost/bdlead_db"
    POSTGRES_USER: str = "bdlead"
    POSTGRES_PASSWORD: str = "bdlead"
    POSTGRES_DB: str = "bdlead_db"

    # App
    APP_NAME: str = "BD Lead Assistant API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # CRM auth stubs (T004; real vault + per-user in T006)
    # For Bitrix: full webhook URL e.g. https://.../rest/123/TOKEN/
    # For HubSpot: access token (private app or OAuth)
    DEFAULT_CRM_PROVIDER: str = "bitrix24"
    BITRIX24_WEBHOOK_URL: str = ""
    HUBSPOT_ACCESS_TOKEN: str = ""

    # Future: JWT_SECRET, ENCRYPTION_KEK, GEMINI_API_KEY etc.

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
