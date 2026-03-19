from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database (Neon — set in .env)
    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""

    # Redis (optional — leave empty for sync task execution)
    REDIS_URL: str = ""

    # Auth
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"
    CLAUDE_FAST_MODEL: str = "claude-haiku-4-5-20251001"  # Fast model for interactive chat

    # ChromaDB
    CHROMADB_PATH: str = "./chromadb_data"
    CHROMADB_MODE: str = "persistent"  # "persistent" (local dev) or "ephemeral" (production/Render)

    # CORS — set to frontend URL in production (e.g. "https://your-app.vercel.app")
    FRONTEND_URL: str = ""

    # Fathom API
    FATHOM_API_KEY: str = ""
    FATHOM_API_BASE_URL: str = "https://api.fathom.ai/external/v1"
    FATHOM_WEBHOOK_SECRET: str = ""  # Optional: verify webhook signatures
    FATHOM_SYNC_INTERVAL_SECONDS: int = 86400  # Daily default; set to 60 in .env for testing

    # Fathom Agent — Meeting Knowledge Base
    MEETING_KNOWLEDGE_COLLECTION: str = "meeting_knowledge"
    FATHOM_MAX_TOOL_CALLS: int = 5
    FATHOM_SIMILARITY_THRESHOLD: float = 0.3
    FATHOM_TOP_K: int = 5

    # Demo
    DEMO_MODE: bool = True

    # Jira (Atlassian Cloud)
    JIRA_API_URL: str = "https://hivepro.atlassian.net"
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_WEBHOOK_SECRET: str = ""
    JIRA_DEFAULT_PROJECT: str = "CS"
    JIRA_SYNC_JQL: str = ""
    JIRA_SYNC_INTERVAL_SECONDS: int = 86400  # Daily default; set to 60 in .env for testing

    # Slack
    SLACK_BOT_TOKEN: str = ""
    SLACK_ENABLED: bool = False
    SLACK_SIGNING_SECRET: str = ""       # Slack app signing secret (HMAC request verification)
    SLACK_CHAT_CHANNEL: str = ""         # Optional: restrict bot to specific channel(s), comma-separated
    SLACK_BOT_USER_ID: str = ""          # Bot's own Slack user ID (to ignore its own messages)

    # Slack — 9 dedicated channels (ARCHITECTURE.md Section 6.1)
    SLACK_CH_TICKET_TRIAGE: str = "#cs-ticket-triage"
    SLACK_CH_CALL_INTEL: str = "#cs-call-intelligence"
    SLACK_CH_HEALTH_ALERTS: str = "#cs-health-alerts"
    SLACK_CH_ESCALATIONS: str = "#cs-escalations"
    SLACK_CH_DELIVERY: str = "#cs-delivery"
    SLACK_CH_QBR_DRAFTS: str = "#cs-qbr-drafts"
    SLACK_CH_PRESALES: str = "#cs-presales-funnel"
    SLACK_CH_EXEC_DIGEST: str = "#cs-executive-digest"
    SLACK_CH_EXEC_URGENT: str = "#cs-executive-urgent"

    # Dashboard base URL for deep-links in Slack cards
    DASHBOARD_BASE_URL: str = "http://localhost:5173"

    model_config = {"env_file": [".env", "../.env"], "extra": "ignore"}


settings = Settings()

# Draft type → Slack channel routing map (ARCHITECTURE.md Section 6.1 + 10)
DRAFT_CHANNEL_MAP = {
    "triage": "SLACK_CH_TICKET_TRIAGE",
    "call_intel": "SLACK_CH_CALL_INTEL",
    "health_alert": "SLACK_CH_HEALTH_ALERTS",
    "escalation": "SLACK_CH_ESCALATIONS",
    "sow": "SLACK_CH_DELIVERY",
    "deployment": "SLACK_CH_DELIVERY",
    "qbr": "SLACK_CH_QBR_DRAFTS",
    "presales": "SLACK_CH_PRESALES",
    "exec_digest": "SLACK_CH_EXEC_DIGEST",
    "exec_urgent": "SLACK_CH_EXEC_URGENT",
    "troubleshoot": "SLACK_CH_TICKET_TRIAGE",
}


def get_channel_for_draft(draft_type: str) -> str:
    """Resolve draft_type to actual Slack channel name."""
    attr = DRAFT_CHANNEL_MAP.get(draft_type, "SLACK_CH_HEALTH_ALERTS")
    return getattr(settings, attr, "#cs-health-alerts")
