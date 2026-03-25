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
    "agents.health_monitor",
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
    insights,
    reports,
    tickets,
    webhooks,
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

    # Health Monitor: every 3 days at 8:30 AM (after Jira sync at 8:00 AM)
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(settings.SYNC_TIMEZONE)
        now_local = datetime.now(tz)
        first_run = now_local.replace(hour=8, minute=30, second=0, microsecond=0)
        if first_run <= now_local:
            first_run += timedelta(days=1)
        scheduler.add_job(_run_health_check, "interval", days=3,
                          start_date=first_run,
                          id="health_3day", misfire_grace_time=3600)
        logger.info(f"Health check scheduled: every 3 days at 08:30 {settings.SYNC_TIMEZONE}")
    except Exception as e:
        logger.warning(f"Health check setup failed (non-fatal): {e}")

    # ChromaDB backfill: schedule as background job so server starts accepting requests immediately
    # (needed for ephemeral mode on Railway where ChromaDB is in-memory)
    def _run_backfills():
        try:
            from app.services.meeting_knowledge_service import meeting_knowledge_service
            stats = meeting_knowledge_service.backfill_from_db()
            logger.info(f"ChromaDB meeting knowledge backfill: {stats}")
        except Exception as e:
            logger.warning(f"ChromaDB meeting backfill failed (non-fatal): {e}")
        try:
            _backfill_rag_embeddings()
        except Exception as e:
            logger.warning(f"RAG embeddings backfill failed (non-fatal): {e}")

    scheduler.add_job(_run_backfills, "date",
                      run_date=datetime.now(timezone.utc) + timedelta(seconds=5),
                      id="backfill_startup")

    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown(wait=False)


def _backfill_rag_embeddings():
    """Re-embed call insights and tickets from PostgreSQL into ChromaDB RAG collections.

    Uses separate DB sessions for insights and tickets to avoid Neon SSL
    timeout — the embedding step is slow (~10s per item) and would keep
    the connection idle long enough for Neon to drop it.
    """
    from app.database import get_sync_session
    from app.services import rag_service

    # Phase 1: Fetch insights, close DB, then embed (slow ChromaDB work)
    db = get_sync_session()
    try:
        from app.models.call_insight import CallInsight
        insight_data = []
        for ins in db.query(CallInsight).all():
            text = f"{ins.summary or ''} {' '.join(ins.key_topics) if ins.key_topics else ''}"
            if text.strip():
                insight_data.append((str(ins.id), text, {
                    "customer_id": str(ins.customer_id) if ins.customer_id else "",
                    "sentiment": ins.sentiment or "",
                    "recording_id": ins.fathom_recording_id or "",
                }))
    finally:
        db.close()

    for iid, text, meta in insight_data:
        rag_service.embed_insight(iid, text, meta)

    # Phase 2: Fresh session for tickets (previous one would be dead by now)
    db = get_sync_session()
    try:
        from app.models.ticket import Ticket
        ticket_data = []
        for t in db.query(Ticket).all():
            text = f"{t.summary or ''} {t.description or ''}"[:2000]
            if text.strip():
                ticket_data.append((str(t.id), text, {
                    "jira_id": t.jira_id or "",
                    "customer_id": str(t.customer_id) if t.customer_id else "",
                    "severity": t.severity or "",
                    "status": t.status or "",
                }))
    finally:
        db.close()

    for tid, text, meta in ticket_data:
        rag_service.embed_ticket(tid, text, meta)

    logger.info(f"RAG backfill: {len(insight_data)} insights, {len(ticket_data)} tickets embedded")


async def _run_jira_sync():
    """APScheduler job: Jira sync — initial catchup or incremental."""
    import pathlib
    from datetime import datetime, timedelta, timezone
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


async def _run_health_check():
    """APScheduler job: daily health check for all customers."""
    try:
        from app.tasks.agent_tasks import run_health_check_all

        logger.info("[HealthCheck] Starting daily health check for all customers")
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: run_health_check_all.apply().get()
        )
        succeeded = result.get("succeeded", 0)
        total = result.get("total", 0)
        at_risk = result.get("at_risk", 0)
        logger.info(f"[HealthCheck] Done: {succeeded}/{total} succeeded, {at_risk} at-risk")
    except Exception as e:
        logger.warning(f"[HealthCheck] Failed: {e}")


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
