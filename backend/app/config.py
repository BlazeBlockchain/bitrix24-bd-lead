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
    APP_VERSION: str = "0.2.1"
    DEBUG: bool = True

    # CRM auth stubs (T004; real vault + per-user in T006)
    # For Bitrix: full webhook URL e.g. https://.../rest/123/TOKEN/
    # For HubSpot: access token (private app or OAuth)
    DEFAULT_CRM_PROVIDER: str = "bitrix24"
    BITRIX24_WEBHOOK_URL: str = ""
    HUBSPOT_ACCESS_TOKEN: str = ""

    # Auth (T005+): Real Google OAuth + JWT (full implementation per review)
    # Google OAuth client credentials (from Google Cloud Console)
    GOOGLE_CLIENT_ID: str = ""
    # JWT signing secret (used for HS256 — must be 32+ chars in production)
    JWT_SECRET: str = "dev-jwt-secret-change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60  # short-lived tokens, refresh via re-auth
    DEMO_AUTH_TOKEN: str = "demo-stub-jwt"  # kept for backward compat during transition

    # LLM proxy (T007): Gemini 2.5 Flash primary + Haiku fallback. Keys server-only.
    # Add to .env for real calls; if empty/DEBUG -> internal mock used for verif + demo.
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    # Budget (T007): simple per-user daily cap in cents (NFR <$0.01/lead target)
    LLM_DAILY_BUDGET_CENTS: int = 200  # ~$2/day per user hard guard (stub; real in T009+)

    # Cost model (009 P3): cents per 1,000,000 tokens, per model.
    #
    # Kept in config rather than in code so a price change is a settings change and
    # never a code change. VERIFY THESE against the providers' current pricing pages
    # before trusting any billing decision on them -- they are list rates as understood
    # when 009 landed, they do move, and nothing here fetches them.
    #
    # Measured reality per enrichment as of 009 P3, gemini-2.5-flash: ~5,950 in and
    # ~2,900 billable out, which is ~0.91 cents. Note "billable out" is larger than
    # candidates_token_count (~740): 2.5-class models charge reasoning tokens at the
    # output rate, so _call_gemini attributes total_token_count - prompt_token_count
    # to output. Sub-cent calls are exactly why the in-memory budget accumulates a
    # float rather than rounding -- see _record_usage.
    LLM_PRICE_CENTS_PER_MTOK: dict[str, dict[str, float]] = {
        "gemini-2.5-flash": {"in": 30.0, "out": 250.0},
        "claude-3-5-haiku-20241022": {"in": 80.0, "out": 400.0},
    }
    # Applied when a model is not in the table above, so an unpriced model is never
    # silently free. Deliberately on the expensive side.
    LLM_PRICE_CENTS_PER_MTOK_DEFAULT: dict[str, float] = {"in": 100.0, "out": 500.0}

    # Encryption (T006/T012): master KEK for envelope-encrypting stored CRM credentials
    # (see app/services/token_vault.py). Empty in dev falls back to a hardcoded dev-only
    # key there; MUST be set to a real secret (32+ bytes) in any shared/prod environment.
    ENCRYPTION_KEK: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
