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

    # Start periodic Jira sync if configured
    jira_sync_task = None
    try:
        from app.services.jira_service import jira_service
        if jira_service.configured:
            jira_sync_task = asyncio.create_task(_jira_periodic_sync())
            logger.info(f"Jira periodic sync started (every {settings.JIRA_SYNC_INTERVAL_SECONDS}s)")
        else:
            logger.info("Jira not configured — periodic sync disabled")
    except Exception as e:
        logger.warning(f"Jira periodic sync setup failed (non-fatal): {e}")

    # Start periodic Fathom sync if configured
    fathom_sync_task = None
    try:
        if settings.FATHOM_API_KEY:
            fathom_sync_task = asyncio.create_task(_fathom_periodic_sync())
            logger.info(f"Fathom periodic sync started (every {settings.FATHOM_SYNC_INTERVAL_SECONDS}s)")
        else:
            logger.info("Fathom not configured — periodic sync disabled")
    except Exception as e:
        logger.warning(f"Fathom periodic sync setup failed (non-fatal): {e}")

    yield

    # Shutdown: cancel periodic syncs
    for task in (jira_sync_task, fathom_sync_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


async def _jira_periodic_sync():
    """Background task: checks if initial sync done, then incremental only."""
    from datetime import datetime, timedelta, timezone
    from app.tasks.jira_sync import sync_jira_tickets

    interval = settings.JIRA_SYNC_INTERVAL_SECONDS

    # Check if initial sync was already done (persisted via a marker file)
    import pathlib
    sync_marker = pathlib.Path(settings.CHROMADB_PATH) / ".jira_initial_sync_done"
    needs_initial_sync = not sync_marker.exists()
    if needs_initial_sync:
        logger.info("[JiraPeriodicSync] No initial sync marker found — will do one-time catchup")
    else:
        logger.info("[JiraPeriodicSync] Initial sync already done — incremental only")

    while True:
        if needs_initial_sync:
            await asyncio.sleep(5)  # Brief delay to let startup finish
        else:
            await asyncio.sleep(interval)

        try:
            # Only sync the configured default project (UCSE)
            project_keys = [settings.JIRA_DEFAULT_PROJECT]

            if needs_initial_sync:
                # One-time catchup: pull last 6 months (not ALL history)
                since_6m = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
                logger.info(f"[JiraPeriodicSync] Initial sync — {project_keys} since {since_6m}")
                stats = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: sync_jira_tickets(since=since_6m, project_keys=project_keys)
                )
                needs_initial_sync = False
                # Write marker so we never re-do initial sync
                sync_marker.write_text(f"done")
            else:
                # Incremental: look back interval + 5 min buffer
                since = (datetime.now(timezone.utc) - timedelta(seconds=interval + 300)).strftime(
                    "%Y-%m-%d %H:%M"
                )
                stats = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: sync_jira_tickets(since=since, project_keys=project_keys)
                )

            created = stats.get("created", 0)
            updated = stats.get("updated", 0)
            if created or updated:
                logger.info(f"[JiraPeriodicSync] {stats}")
            else:
                logger.debug(f"[JiraPeriodicSync] No changes: {stats}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"[JiraPeriodicSync] Failed: {e}")


async def _fathom_periodic_sync():
    """Background task: daily Fathom meeting sync."""
    from app.tasks.agent_tasks import run_fathom_sync

    interval = settings.FATHOM_SYNC_INTERVAL_SECONDS

    # Brief delay on startup to let everything initialize
    await asyncio.sleep(30)

    while True:
        try:
            logger.info("[FathomPeriodicSync] Starting sync (last 7 days)")
            result = await run_fathom_sync(days=7)
            imported = result.get("imported", 0)
            if imported:
                logger.info(f"[FathomPeriodicSync] {result}")
            else:
                logger.debug(f"[FathomPeriodicSync] No new meetings")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"[FathomPeriodicSync] Failed: {e}")

        await asyncio.sleep(interval)


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
