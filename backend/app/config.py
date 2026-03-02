from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/cs_control_plane"
    SYNC_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/cs_control_plane"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"

    # ChromaDB
    CHROMADB_PATH: str = "./chromadb_data"

    # External (Phase 2)
    JIRA_API_URL: str = "https://hivepro.atlassian.net"
    JIRA_API_TOKEN: str = ""
    SLACK_BOT_TOKEN: str = ""
    FATHOM_EMAIL: str = ""
    FATHOM_PASSWORD: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
