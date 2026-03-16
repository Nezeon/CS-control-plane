<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Claude-Sonnet%204.5-D97706?style=for-the-badge&logo=anthropic&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/ChromaDB-0.4+-FF6F00?style=for-the-badge&logoColor=white" />
</p>

# HivePro CS Control Plane

> **Codename: Mission Control** &mdash; An AI-powered command center that orchestrates **14 named agents across a 4-tier hierarchy** to automate Customer Success workflows at HivePro.

This isn't a chatbot or a dashboard. It's a fully autonomous CS operations engine that triages Jira tickets, analyzes call recordings, monitors customer health, drafts Slack messages, and coordinates multi-step workflows &mdash; all through a hierarchy of AI agents that think, delegate, and reflect.

---

## How It Works

```
                         External Events
                    (Jira / Fathom / Slack / Cron)
                              |
                              v
                   +---------------------+
                   |   T1: Supervisor    |  Naveen Kapoor
                   |   (Orchestrator)    |  Strategic decomposition
                   +----------+----------+
                              |
              +---------------+---------------+
              |               |               |
     +--------v------+ +-----v-------+ +-----v--------+
     | T2: Support   | | T2: Value   | | T2: Delivery |
     | Rachel Torres | | Damon Reeves| | Priya Mehta  |
     +-------+-------+ +------+------+ +------+-------+
             |                 |                |
     +-------v-------+  +-----v------+  +------v-------+
     | T3 Specialists|  | T3 Specs   |  | T3 Specs     |
     | Kai, Leo,     |  | Aisha,     |  | Ethan, Zara  |
     | Maya          |  | Jordan,    |  |              |
     |               |  | Sofia,     |  |              |
     |               |  | Riley      |  |              |
     +-------+-------+  +-----+------+  +------+-------+
             |                 |                |
             +--------+--------+--------+-------+
                      |                 |
               +------v------+   +------v------+
               |  PostgreSQL |   |  ChromaDB   |
               |  (Neon)     |   |  (Vectors)  |
               +-------------+   +-------------+
                      |
               +------v------+
               | T4: Atlas   |  Foundation Memory Layer
               | (Customer   |  Serves ALL tiers
               |  Memory)    |
               +-------------+
```

**Key principle:** Tasks flow DOWN the hierarchy (T1 -> T2 -> T3). Results flow UP. Specialists never talk to each other directly &mdash; sideways coordination goes through Lane Leads.

---

## The 14 Agents

Each agent has a human identity, personality traits, specialized tools, and a multi-stage pipeline.

### Tier 1 &mdash; Supervisor
| Agent | Identity | Role |
|-------|----------|------|
| CSO Orchestrator | Naveen Kapoor | Strategic decomposition, delegation, quality evaluation, synthesis |

### Tier 2 &mdash; Lane Leads
| Agent | Identity | Lane | Role |
|-------|----------|------|------|
| Support Lead | Rachel Torres | Support | Ticket routing, escalation coordination |
| Value Lead | Damon Reeves | Value | Health monitoring, QBR, renewals |
| Delivery Lead | Priya Mehta | Delivery | Deployment, SOW, onboarding |

### Tier 3 &mdash; Specialists
| Agent | Identity | Lane | Role |
|-------|----------|------|------|
| Ticket Triage | Kai Nakamura | Support | Auto-classify severity, suggest actions |
| Troubleshooter | Leo Petrov | Support | Root cause analysis, resolution |
| Escalation Summary | Maya Santiago | Support | L2/L3 escalation packages |
| Health Monitor | Dr. Aisha Okafor | Value | Daily health scores, at-risk flags |
| Call Intelligence | Jordan Ellis | Value | Call transcript analysis, action items |
| QBR Value | Sofia Marquez | Value | Quarterly business review content |
| Meeting Followup | Riley Park | Value | Post-meeting action tracking |
| SOW Prerequisite | Ethan Brooks | Delivery | Pre-deployment checklists |
| Deployment Intelligence | Zara Kim | Delivery | Deployment guidance via RAG |

### Tier 4 &mdash; Foundation
| Agent | Identity | Role |
|-------|----------|------|
| Customer Memory | Atlas | Context provider for all tiers, 3-tier memory system |

---

## Live Integrations

| Integration | What It Does | How |
|-------------|--------------|-----|
| **Jira** | Auto-syncs UCSE project tickets every 60s, links to customers, tracks status | REST API + webhooks |
| **Fathom** | Ingests call recordings, extracts summaries + action items + sentiment | REST API + webhooks |
| **Slack** | Bidirectional chat (ask questions, get AI answers), agent draft cards with Approve/Edit/Dismiss buttons, 9 dedicated channels | Events API + interactive messages |
| **Claude API** | Powers all agent reasoning via Haiku (fast path) and Sonnet (full pipeline) | Anthropic SDK |

### Slack Chat Interface
Users can ask questions directly in Slack and get AI-powered responses:
- **"How many open tickets does PDO have?"** &rarr; Instant answer with ticket breakdown
- **"What's the health status of Etisalat?"** &rarr; Health score, trends, flags
- Responses are threaded, formatted with Block Kit, and cite real data

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI 0.109+ |
| Database | PostgreSQL 16 (Neon cloud) |
| Vector Store | ChromaDB 0.4+ (persistent) |
| ORM | SQLAlchemy 2.0 (async + sync) |
| Migrations | Alembic |
| LLM | Claude API (Sonnet 4.5 + Haiku 4.5) |
| Task Queue | Celery + Redis (optional, eager mode for local dev) |
| Config | YAML-driven (4 config files define all agent behavior) |
| HTTP Client | httpx (async) |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 18 + Vite 5 |
| Styling | Tailwind CSS 3 |
| State | Zustand 4 |
| Routing | React Router 6 |
| HTTP | Axios |

### Dual Frontend
The project has two frontends:

- **React Dashboard** (`/frontend/`) &mdash; Spatial command center with dark void UI, customer health grid, pipeline analytics
- **Streamlit App** (`/streamlit_app/`) &mdash; 6-page operational UI (Ask, Dashboard, Customers, Agents, Tickets, Executive Summary)

Both connect to the same FastAPI backend.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (local or [Neon](https://neon.tech))
- Anthropic API key
- Redis (optional &mdash; without it, tasks run synchronously)

### 1. Clone and configure

```bash
git clone https://github.com/Nezeon/CS-control-plane.git
cd hivepro-cs-control-plane
cp .env.example .env
```

Edit `.env` with your credentials (see [Environment Variables](#environment-variables) below).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server (auto-creates admin user on first run)
uvicorn app.main:app --reload --port 8000
```

On first startup, the server will:
- Create admin user `ayushmaan@hivepro.com`
- Start Jira periodic sync (every 60s)
- Pre-warm database connection pools

### 3. React Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### 4. Streamlit Frontend (alternative)

```bash
cd streamlit_app
pip install streamlit
streamlit run app.py
```

Open `http://localhost:8501`

---

## Environment Variables

```bash
# ── Database ──
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SYNC_DATABASE_URL=postgresql://user:pass@host/db

# ── Auth ──
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# ── Claude API ──
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_FAST_MODEL=claude-haiku-4-5-20251001

# ── ChromaDB ──
CHROMADB_PATH=./chromadb_data
CHROMADB_MODE=persistent

# ── Redis (optional) ──
REDIS_URL=redis://localhost:6379/0

# ── Jira ──
JIRA_API_URL=https://your-instance.atlassian.net
JIRA_EMAIL=your-email
JIRA_API_TOKEN=your-token
JIRA_DEFAULT_PROJECT=UCSE
JIRA_SYNC_INTERVAL_SECONDS=60

# ── Fathom ──
FATHOM_API_KEY=your-key
FATHOM_WEBHOOK_SECRET=your-secret

# ── Slack ──
SLACK_ENABLED=false
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=your-secret
SLACK_BOT_USER_ID=U0123456789
SLACK_CHAT_CHANNEL=C0123456789
# 9 dedicated channels (SLACK_CH_TRIAGE, SLACK_CH_HEALTH, etc.)

# ── Frontend ──
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws
```

---

## Project Structure

```
hivepro-cs-control-plane/
|
+-- backend/
|   +-- config/                     # YAML-driven agent configuration
|   |   +-- agent_profiles.yaml     # 14 agent identities, traits, tools
|   |   +-- org_structure.yaml      # 4-tier hierarchy, lanes
|   |   +-- pipeline.yaml           # 7-stage pipeline per tier
|   |   +-- workflows.yaml          # Event -> agent routing
|   |
|   +-- app/
|   |   +-- main.py                 # FastAPI entry + startup hooks
|   |   +-- config.py               # Settings from .env
|   |   +-- database.py             # PostgreSQL (async + sync)
|   |   +-- chromadb_client.py      # Vector store connection
|   |   +-- websocket_manager.py    # Real-time broadcast
|   |   |
|   |   +-- agents/                 # 14 AI agent implementations
|   |   |   +-- orchestrator.py     # T1: Naveen Kapoor
|   |   |   +-- leads/              # T2: Rachel, Damon, Priya
|   |   |   +-- triage_agent.py     # T3: Specialists
|   |   |   +-- memory_agent.py     # T4: Atlas
|   |   |   +-- base_agent.py       # Pipeline execution base
|   |   |   +-- pipeline_engine.py  # Multi-round pipeline runner
|   |   |   +-- tools/              # 12+ Claude tool_use definitions
|   |   |   +-- traits/             # 9 pluggable trait behaviors
|   |   |   +-- message_board.py    # Inter-agent communication
|   |   |
|   |   +-- models/                 # SQLAlchemy models (12 tables)
|   |   +-- schemas/                # Pydantic request/response
|   |   +-- routers/                # 22 API routers
|   |   +-- services/               # Business logic
|   |   |   +-- claude_service.py   # LLM calls
|   |   |   +-- jira_service.py     # Jira REST client
|   |   |   +-- fathom_service.py   # Fathom API client
|   |   |   +-- slack_service.py    # Slack WebClient
|   |   |   +-- slack_chat_handler.py  # Bidirectional Slack chat
|   |   |   +-- chat_fast_path.py   # Fast single-call responses
|   |   |   +-- draft_service.py    # Approval workflow
|   |   |   +-- event_service.py    # Event processing
|   |   |   +-- trend_service.py    # Executive analytics
|   |   |
|   |   +-- tasks/                  # Celery async tasks
|   |   |   +-- jira_sync.py        # Periodic Jira sync
|   |   +-- utils/
|   |       +-- ensure_admin.py     # Admin user creation
|   |       +-- security.py         # JWT + password hashing
|   |
|   +-- alembic/                    # Database migrations
|   +-- requirements.txt
|
+-- frontend/                       # React spatial dashboard
|   +-- src/
|       +-- pages/                  # Dashboard, CustomerDetail, Pipeline
|       +-- components/             # Shared UI (GlassCard, KpiCard, etc.)
|       +-- stores/                 # Zustand (dashboard, customer)
|       +-- services/               # API client + WebSocket
|
+-- streamlit_app/                  # Streamlit operational UI
|   +-- app.py                      # Login + navigation
|   +-- pages/                      # 6 pages
|   +-- utils/api.py                # API client with JWT
|
+-- docs/
|   +-- ARCHITECTURE.md             # Full architecture spec
|   +-- PRD.md                      # Product requirements
|   +-- WIREFRAMES.md               # UI/UX specs + design system
|   +-- API_CONTRACT.md             # Endpoint contracts
|   +-- DATABASE_SCHEMA.md          # Schema definitions
|
+-- CLAUDE.md                       # AI development context
+-- render.yaml                     # Render deployment config
```

---

## API Overview

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | JWT login |
| `GET` | `/api/dashboard/stats` | KPI summary (customers, tickets, health) |
| `GET` | `/api/dashboard/quick-health` | Customer health grid with ticket counts |
| `GET` | `/api/dashboard/events` | Recent event feed |
| `GET` | `/api/customers` | All customers (sorted, filterable) |
| `GET` | `/api/customers/:id` | Customer detail |
| `GET` | `/api/customers/:id/tickets` | Customer's Jira tickets |
| `GET` | `/api/customers/:id/health-history` | 90-day health trend |
| `POST` | `/api/chat/send` | Send message to AI agents |

### Integration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jira/status` | Jira connection status |
| `POST` | `/api/jira/sync` | Trigger manual Jira sync |
| `POST` | `/api/webhooks/jira` | Jira Cloud webhook receiver |
| `POST` | `/api/webhooks/fathom` | Fathom webhook receiver |
| `POST` | `/api/webhooks/slack` | Slack Events API receiver |
| `POST` | `/api/webhooks/slack/interactions` | Slack button callbacks |

### Agent Pipeline Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | All 14 agents with stats |
| `POST` | `/api/agents/:name/trigger` | Manually trigger agent |
| `GET` | `/api/drafts` | Agent draft outputs |
| `POST` | `/api/drafts/:id/approve` | Approve agent draft |
| `GET` | `/api/executive/summary` | Executive dashboard data |
| `POST` | `/api/executive/check-rules` | Run alert rules engine |

Full API contracts: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)

---

## Architecture Principles

1. **Event-Driven** &mdash; External events (Jira, Fathom, Slack) create event records. The Orchestrator reads and routes them. Agents never call each other directly.

2. **YAML-Driven Config** &mdash; Agent identities, personalities, tools, pipeline stages, and workflows are defined in 4 YAML files. To change behavior, edit YAML &mdash; not Python.

3. **Hierarchical Delegation** &mdash; T1 decomposes tasks, T2 coordinates lanes, T3 executes. Results flow back up. Foundation (T4) serves all tiers.

4. **3-Tier Memory** &mdash; Working memory (in-process scratchpad), Episodic memory (ChromaDB per-agent diary), Semantic memory (ChromaDB shared knowledge pools).

5. **Draft-First Workflow** &mdash; Agents produce drafts, not final actions. Humans approve/edit/dismiss via Slack buttons or the dashboard.

6. **Real Data Only** &mdash; No seed/demo data. All customers and tickets come from live Jira sync. Fathom provides real call data.

7. **Async AI** &mdash; All Claude API calls run in background threads (or Celery tasks with Redis). API endpoints never block.

8. **WebSocket Everything** &mdash; Real-time updates for pipeline progress, agent status, new events. Frontend never polls.

---

## Current Customers (Live from Jira)

The system tracks **25 real customers** synced from the UCSE Jira project:

> Etisalat, PDO, Mubadala Capital, Yas Holdings, Sohar Bank, Ooredoo, KSAA, KSGAA, DMS, Ujjivan Bank, Libra Solutions, GPH, Alraedah Finance, Goosehead Insurance, JES, DEG, Tencent, Meet Marigold, Datamount, IT Monkey, ConnexPay, VisionBank, Saudi Exim, Kazi, Apache (Internal)

---

## Development

```bash
# Backend with auto-reload
cd backend && uvicorn app.main:app --reload --port 8000

# React frontend with HMR
cd frontend && npm run dev

# Streamlit (alternative UI)
cd streamlit_app && streamlit run app.py

# With Redis for async tasks (optional)
redis-server
celery -A app.tasks.celery_app worker --loglevel=info
```

### Local Dev Notes
- Without Redis, all Celery tasks run synchronously (eager mode)
- ChromaDB runs in persistent mode by default (`./chromadb_data/`)
- Jira sync runs every 60s automatically on startup
- First startup creates admin user and pre-warms DB pools

---

## Documentation

| Document | Description |
|----------|-------------|
| [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full system architecture, agent hierarchy, pipeline stages |
| [`PRD.md`](docs/PRD.md) | Product requirements, user stories, acceptance criteria |
| [`WIREFRAMES.md`](docs/WIREFRAMES.md) | UI specs, 3D specs, design system, responsive fallbacks |
| [`API_CONTRACT.md`](docs/API_CONTRACT.md) | Every endpoint with request/response JSON shapes |
| [`DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) | All 12 tables, relationships, ChromaDB collections |
| [`CLAUDE.md`](CLAUDE.md) | AI development context (rules, patterns, phases) |

---

## Deployment

| Component | Platform | Config |
|-----------|----------|--------|
| Backend API | Render | `render.yaml` |
| React Frontend | Vercel | `vercel.json` |
| Database | Neon PostgreSQL | Cloud managed |
| Vector DB | ChromaDB | Persistent (local) or ephemeral (cloud) |

---

<p align="center">
  <sub>Built by Ayushmaan Singh Naruka &mdash; AI Hub Team, HivePro</sub>
</p>
