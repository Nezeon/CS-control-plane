import asyncio
import logging
import sys
from contextlib import asynccontextmanager

# Fix Windows cp1252 encoding for Unicode box-drawing / emoji in terminal output
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# ── Logging Configuration ─────────────────────────────────────────────────
# Ensure INFO-level logs from our modules are visible in the terminal.
# uvicorn configures its own loggers, so we configure the root logger
# plus our specific namespaces to show [Chat], [Pipeline], [Orchestrator] etc.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,  # Override any prior basicConfig (e.g. from uvicorn)
)
# Set our app loggers to INFO (even if root is changed later)
for _logger_name in [
    "services.chat",
    "routers.chat",
    "pipeline_engine",
    "agents",
    "agents.orchestrator",
    "agents.fathom",
    "agents.base",
    "services.slack_chat",
    "startup",
]:
    logging.getLogger(_logger_name).setLevel(logging.INFO)

from app.routers import (
    agents,
    alerts,
    auth,
    chat,
    customers,
    dashboard,
    demo,
    events,
    fathom,
    health,
    hierarchy,
    insights,
    memory,
    messages,
    pipeline,
    reports,
    tickets,
    webhooks,
    workflows,
)
from app.websocket_manager import manager

logger = logging.getLogger("startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("CS Control Plane starting...")
    logger.info(f"ChromaDB mode: {settings.CHROMADB_MODE}")
    logger.info(f"CORS: {'restricted to ' + settings.FRONTEND_URL if settings.FRONTEND_URL else 'open (dev)'}")
    logger.info(f"Redis: {'connected' if settings.REDIS_URL else 'disabled (eager tasks)'}")
    logger.info(f"Fathom: {'configured' if settings.FATHOM_API_KEY else 'not configured'}")
    logger.info(f"Demo mode: {'ENABLED' if settings.DEMO_MODE else 'disabled'}")
    logger.info(f"Slack chat: {'configured' if settings.SLACK_SIGNING_SECRET else 'not configured'}")

    # Install rich demo logging when demo mode is enabled
    if settings.DEMO_MODE:
        from app.agents.demo_logger import install_demo_formatter
        install_demo_formatter()

    # Ensure admin user exists (no seed data)
    try:
        from app.utils.ensure_admin import ensure_admin_user
        ensure_admin_user()
    except Exception as e:
        logger.warning(f"Admin user setup failed (non-fatal): {e}")

    # Pre-warm DB pools so first request doesn't pay Neon cold-start (~6s)
    try:
        from app.database import warm_sync_pool, engine
        from sqlalchemy import text
        warm_sync_pool()
        # Also warm async pool
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("DB pools pre-warmed (sync + async).")
    except Exception as e:
        logger.warning(f"Pool pre-warm failed (non-fatal): {e}")

    # -- Scheduled syncs via APScheduler (fixed daily times) --
    from datetime import datetime, timedelta, timezone
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler(timezone=settings.SYNC_TIMEZONE)

    # Jira: daily at 8:00 AM + run once on startup
    try:
        from app.services.jira_service import jira_service
        if jira_service.configured:
            scheduler.add_job(_run_jira_sync, "cron", hour=8, minute=0, id="jira_daily",
                              misfire_grace_time=3600)
            # Also run once on startup (5s delay)
            scheduler.add_job(_run_jira_sync, "date",
                              run_date=datetime.now(timezone.utc) + timedelta(seconds=5),
                              id="jira_startup")
            logger.info(f"Jira sync scheduled: daily at 08:00 {settings.SYNC_TIMEZONE} + on startup")
        else:
            logger.info("Jira not configured — sync disabled")
    except Exception as e:
        logger.warning(f"Jira sync setup failed (non-fatal): {e}")

    # Fathom: twice daily at 6:00 AM and 6:00 PM
    try:
        if settings.FATHOM_API_KEY:
            scheduler.add_job(_run_fathom_sync, "cron", hour=6, minute=0, id="fathom_morning",
                              misfire_grace_time=3600)
            scheduler.add_job(_run_fathom_sync, "cron", hour=18, minute=0, id="fathom_evening",
                              misfire_grace_time=3600)
            # Also run once on startup (30s delay)
            scheduler.add_job(_run_fathom_sync, "date",
                              run_date=datetime.now(timezone.utc) + timedelta(seconds=30),
                              id="fathom_startup")
            logger.info(f"Fathom sync scheduled: daily at 06:00 & 18:00 {settings.SYNC_TIMEZONE} + on startup")
        else:
            logger.info("Fathom not configured — sync disabled")
    except Exception as e:
        logger.warning(f"Fathom sync setup failed (non-fatal): {e}")

    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown(wait=False)


async def _run_jira_sync():
    """APScheduler job: Jira sync — initial catchup or incremental."""
    import pathlib
    from app.tasks.jira_sync import sync_jira_tickets

    try:
        project_keys = [settings.JIRA_DEFAULT_PROJECT]
        sync_marker = pathlib.Path(settings.CHROMADB_PATH) / ".jira_initial_sync_done"

        if not sync_marker.exists():
            # One-time catchup: pull last 6 months
            since_6m = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
            logger.info(f"[JiraSync] Initial catchup — {project_keys} since {since_6m}")
            stats = await asyncio.get_event_loop().run_in_executor(
                None, lambda: sync_jira_tickets(since=since_6m, project_keys=project_keys)
            )
            sync_marker.write_text("done")
        else:
            # Incremental: last 25 hours (covers daily + buffer)
            since = (datetime.now(timezone.utc) - timedelta(hours=25)).strftime("%Y-%m-%d %H:%M")
            stats = await asyncio.get_event_loop().run_in_executor(
                None, lambda: sync_jira_tickets(since=since, project_keys=project_keys)
            )

        created = stats.get("created", 0)
        updated = stats.get("updated", 0)
        if created or updated:
            logger.info(f"[JiraSync] {stats}")
        else:
            logger.debug(f"[JiraSync] No changes: {stats}")
    except Exception as e:
        logger.warning(f"[JiraSync] Failed: {e}")


async def _run_fathom_sync():
    """APScheduler job: Fathom meeting sync — last 7 days."""
    try:
        from app.tasks.agent_tasks import run_fathom_sync

        logger.info("[FathomSync] Starting sync (last 7 days)")
        result = await run_fathom_sync(days=7)
        imported = result.get("imported", 0)
        if imported:
            logger.info(f"[FathomSync] {result}")
        else:
            logger.debug(f"[FathomSync] No new meetings")
    except Exception as e:
        logger.warning(f"[FathomSync] Failed: {e}")


app = FastAPI(
    title="CS Control Plane API",
    description="AI-powered Customer Success orchestration platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — restricted in production, open in local dev
_allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
if settings.FRONTEND_URL:
    _allowed_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins if settings.FRONTEND_URL else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(health.router)
app.include_router(tickets.router)
app.include_router(insights.router)
app.include_router(agents.router)
app.include_router(events.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(webhooks.router)
app.include_router(chat.router)

# Jira integration
from app.routers import jira
app.include_router(jira.router)

# Fathom integration
app.include_router(fathom.router)

# v2 routers (hierarchy-aware)
app.include_router(hierarchy.router)
app.include_router(messages.router)
app.include_router(pipeline.router)
app.include_router(memory.router)
app.include_router(workflows.router)

# Executive summary + trends
from app.routers import executive
app.include_router(executive.router)

# Demo router (always available, scenarios are self-contained)
app.include_router(demo.router)

# Drafts router (draft-first approval workflow)
from app.routers import drafts
app.include_router(drafts.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    import json

    connection_id = await manager.connect(websocket)
    try:
        await manager.send_to(connection_id, "connected", {
            "message": "Connected to CS Control Plane",
            "connection_id": connection_id,
        })
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await manager.send_to(connection_id, "pong", {})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(connection_id)
    except Exception:
        await manager.disconnect(connection_id)
