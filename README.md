<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Claude-Sonnet%204.5-D97706?style=for-the-badge&logo=anthropic&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/ChromaDB-0.4+-FF6F00?style=for-the-badge&logoColor=white" />
</p>

# HivePro CS Control Plane

> **Codename: Mission Control** &mdash; An AI-powered command center that orchestrates **10 agents** to automate Customer Success workflows at HivePro.

10 specialized AI agents watch Jira tickets, Fathom call recordings, and HubSpot deals &mdash; then triage issues, analyze calls, monitor customer health, draft actions, and coordinate multi-step workflows. Everything goes through Slack first; a dashboard provides deep-dives when needed.

Every agent output starts as a **draft**. Nothing customer-facing happens without human approval.

---

## How It Works

```
                         External Events
                    (Jira / Fathom / HubSpot / Cron)
                              |
                              v
                   +---------------------+
                   |   Orchestrator      |  Naveen Kapoor
                   |   (Routes events)   |  Direct specialist routing
                   +----------+----------+
                              |
              +------+--------+--------+------+
              |      |        |        |      |
     +--------v--+ +-v------+ +v------+ +----v-----+ ...
     | Triage    | | Trouble| |Health | | QBR      |
     | Kai       | | Leo    | |Aisha  | | Sofia    |
     +-----------+ +--------+ +-------+ +----------+
              |      |        |        |      |
              +------+--------+--------+------+
                      |                 |
               +------v------+   +------v------+
               |  PostgreSQL |   |  ChromaDB   |
               |  (Neon)     |   |  (Vectors)  |
               +-------------+   +-------------+
                      |
               +------v------+
               | Atlas       |  Foundation Memory Layer
               | (Customer   |  Serves ALL agents
               |  Memory)    |
               +-------------+
```

The Orchestrator routes events directly to specialist agents by event type. Specialists never talk directly to each other.

---

## The 10 Agents

Each agent has a human identity, personality traits, specialized tools, and a multi-stage pipeline (`perceive` &rarr; `retrieve` &rarr; `think` &rarr; `act` &rarr; `reflect`).

### Orchestrator
| Agent | Identity | Role |
|-------|----------|------|
| CS Orchestrator | Naveen Kapoor | Classifies events, routes to correct specialist. Never analyzes &mdash; pure routing. |

### Specialists
| Agent | Identity | Lane | Role |
|-------|----------|------|------|
| Ticket Triage | Kai Nakamura | Support | Classifies Jira tickets: category, severity, duplicates, email draft |
| Troubleshooter | Leo Petrov | Support | Root cause analysis with confidence scoring. &lt;70% &rarr; escalates |
| Escalation Writer | Maya Santiago | Support | Compiles escalation docs with full context and evidence |
| Health Monitor | Dr. Aisha Okafor | Value | Daily health scores, risk flags, cross-customer patterns |
| QBR / Value Narrative | Sofia Marquez | Value | Quarterly business review content, renewal recs |
| SOW & Prerequisite | Ethan Brooks | Delivery | SOW docs, infra/security checklists for new customers |
| Deployment Intelligence | Zara Kim | Delivery | Validates deployments, flags failures |

### Tier 4 &mdash; Foundation
| Agent | Identity | Role |
|-------|----------|------|
| Customer Memory | Atlas | Per-customer knowledge store. 3-tier memory: Working + Episodic + Semantic |

---

## Live Integrations

| Integration | What It Does | How |
|-------------|--------------|-----|
| **Jira** | Syncs UCSC project tickets, links to customers, tracks status | REST API + webhooks |
| **Fathom** | Ingests call recordings, extracts summaries + action items + sentiment | REST API (6 AM & 6 PM sync) |
| **HubSpot** | Deals pipeline, stages, contacts, close reasons | Daily API pull + webhook |
| **Slack** | Bidirectional chat, agent draft cards with Approve/Edit/Dismiss, 9 dedicated channels | Events API + interactive messages |
| **Claude API** | Powers all agent reasoning via Haiku (fast path) and Sonnet (full pipeline) | Anthropic SDK |

### Slack Channels

| Channel | Content |
|---------|---------|
| `#cs-ticket-triage` | Ticket classifications + troubleshooting results |
| `#cs-call-intelligence` | Post-call summaries + action items + sentiment |
| `#cs-health-alerts` | Daily health checks + risk flags |
| `#cs-executive-digest` | Weekly portfolio summary (Monday 9 AM) |
| `#cs-executive-urgent` | Threshold alerts (health crash, SLA cascade, churn signal) |
| `#cs-presales-funnel` | Pipeline analytics + stalled deals |
| `#cs-qbr-drafts` | QBR document drafts |
| `#cs-escalations` | Engineering escalation docs |
| `#cs-delivery` | SOW drafts + deployment status |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI 0.109+ (Python 3.11+) |
| Database | PostgreSQL 16 (Neon cloud) |
| Vector Store | ChromaDB 0.4+ (6 collections) |
| ORM | SQLAlchemy 2.0 (async + sync) |
| Migrations | Alembic (6 migration files) |
| AI (main) | Claude Sonnet 4.5 |
| AI (fast) | Claude Haiku 4.5 |
| Task Queue | Celery (eager mode &mdash; no Redis required locally) |
| Scheduling | APScheduler (cron-style, fixed times) |
| Config | YAML-driven (4 config files define all agent behavior) |
| HTTP Client | httpx (async) |
| Slack | slack-sdk (WebClient + Block Kit) |
| Auth | python-jose (JWT) + passlib |

### Frontend

| UI | Tech | URL |
|----|------|-----|
| **React Dashboard** | React 18, Vite 5, Tailwind, Three.js, Zustand, D3 | `localhost:5173` |

Connects to the same FastAPI backend.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for React dashboard, optional)
- A [Neon](https://neon.tech) PostgreSQL database
- [Anthropic API key](https://console.anthropic.com)

### 1. Clone and configure

```bash
git clone <repo-url>
cd hivepro-cs-control-plane
cp .env.example .env
# Edit .env &mdash; fill in DATABASE_URL, SYNC_DATABASE_URL, ANTHROPIC_API_KEY at minimum
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head          # Create/migrate database tables
uvicorn app.main:app --reload --port 8000
```

On startup the backend will:
- Auto-create the admin user (`ayushmaan@hivepro.com` / `password123`)
- Pre-warm database connection pools (mitigates Neon cold start)
- Backfill ChromaDB from PostgreSQL (RAG embeddings + meeting knowledge)
- Start APScheduler jobs (Jira daily at 8 AM, Fathom at 6 AM & 6 PM)

Verify: `GET http://localhost:8000/api/health` &rarr; `{"status": "healthy"}`

### 3. React Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## Project Structure

```
hivepro-cs-control-plane/
├── backend/
│   ├── config/                      # YAML-driven agent configuration
│   │   ├── agent_profiles.yaml      # 14 agent definitions, traits, tools
│   │   ├── org_structure.yaml       # 4-tier hierarchy, lanes, reporting
│   │   ├── pipeline.yaml            # Pipeline stage definitions per tier
│   │   └── workflows.yaml           # Event → agent routing
│   │
│   ├── app/
│   │   ├── main.py                  # FastAPI entry + APScheduler setup
│   │   ├── config.py                # 40+ env vars (pydantic-settings)
│   │   ├── database.py              # PostgreSQL async + sync engines
│   │   ├── chromadb_client.py       # Vector store connection
│   │   ├── websocket_manager.py     # Real-time broadcast
│   │   │
│   │   ├── agents/                  # 14 AI agent implementations
│   │   │   ├── orchestrator.py      # T1: Naveen — event routing
│   │   │   ├── triage_agent.py      # T3: Kai — ticket classification
│   │   │   ├── troubleshoot_agent.py # T3: Leo — root cause
│   │   │   ├── escalation_agent.py  # T3: Maya — escalation docs
│   │   │   ├── health_monitor.py    # T3: Aisha — daily health
│   │   │   ├── qbr_agent.py         # T3: Sofia — QBR content
│   │   │   ├── sow_agent.py         # T3: Ethan — SOW docs
│   │   │   ├── deployment_intel_agent.py  # T3: Zara — deployments
│   │   │   ├── memory_agent.py      # T4: Atlas — customer memory
│   │   │   ├── base_agent.py        # Pipeline execution base class
│   │   │   ├── pipeline_engine.py   # Multi-round pipeline runner
│   │   │   ├── reflection_engine.py # Reflection + quality gate
│   │   │   ├── memory/              # 3-tier memory system
│   │   │   └── traits/              # 13 pluggable trait behaviors
│   │   │
│   │   ├── models/                  # 17 SQLAlchemy models
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── routers/                 # 23 API route modules
│   │   ├── services/                # 17 business logic modules
│   │   │   ├── claude_service.py    # LLM calls (Sonnet + Haiku)
│   │   │   ├── chat_service.py      # Unified chat orchestration
│   │   │   ├── chat_fast_path.py    # Haiku fast responses
│   │   │   ├── jira_service.py      # Jira REST client
│   │   │   ├── fathom_service.py    # Fathom API client
│   │   │   ├── slack_service.py     # Slack Bot client
│   │   │   ├── slack_chat_handler.py # Bidirectional Slack chat
│   │   │   ├── draft_service.py     # Approval workflow
│   │   │   └── ...
│   │   │
│   │   ├── tasks/                   # Celery tasks + sync jobs
│   │   │   ├── jira_sync.py         # Jira bulk + incremental sync
│   │   │   └── agent_tasks.py       # 20+ async agent tasks
│   │   └── utils/
│   │       ├── ensure_admin.py      # Auto-create admin on startup
│   │       └── security.py          # JWT + password hashing
│   │
│   ├── alembic/                     # 6 database migrations
│   └── requirements.txt
│
├── frontend/                        # React spatial dashboard (3 pages)
│   └── src/
│       ├── pages/                   # Dashboard, CustomerDetail, PipelineAnalytics
│       ├── components/              # GlassCard, HealthRing, KpiCard, etc.
│       ├── stores/                  # Zustand (dashboard, customer)
│       └── services/                # API client + WebSocket
│
├── prompt-templates/                # Reusable prompt templates
├── docs/                            # Architecture, PRD, wireframes, API contract, DB schema
├── render.yaml                      # Render deployment config
├── CLAUDE.md                        # AI development context
├── DEPLOYMENT.md                    # Deployment guide
└── DOCUMENTATION.md                 # Comprehensive technical docs
```

---

## Data Sync Schedule

Both Jira and Fathom sync automatically via APScheduler (cron-style, fixed times in IST).

| Source | Schedule | Behavior |
|--------|----------|----------|
| **Jira** | Daily at **8:00 AM** + on startup | First run: 6-month catchup. Then incremental (last 25 hours). |
| **Fathom** | **6:00 AM** & **6:00 PM** + on startup (30s delay) | Syncs last 7 days each run. Deduplicates automatically. |

Timezone is configurable via `SYNC_TIMEZONE` (default: `Asia/Kolkata`).

Manual sync: `POST /api/jira/sync` or `POST /api/fathom/sync?days=14`

---

## API Overview

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | JWT login |
| `GET` | `/api/dashboard/stats` | KPI summary (customers, tickets, health) |
| `GET` | `/api/dashboard/quick-health` | Customer health grid with ticket counts |
| `GET` | `/api/dashboard/events` | Recent event feed |
| `GET` | `/api/customers` | All customers |
| `GET` | `/api/customers/:id` | Customer detail |
| `GET` | `/api/customers/:id/tickets` | Customer's Jira tickets |
| `GET` | `/api/customers/:id/health-history` | 90-day health trend |
| `POST` | `/api/chat/send` | Send message to AI agents |
| `GET` | `/api/executive/summary` | Executive dashboard data |
| `GET` | `/api/executive/trends` | Health trends, ticket velocity, sentiment |

### Integration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jira/status` | Jira connection status |
| `POST` | `/api/jira/sync` | Trigger manual Jira sync |
| `POST` | `/api/webhooks/jira` | Jira Cloud webhook receiver |
| `POST` | `/api/webhooks/slack` | Slack Events API receiver |
| `POST` | `/api/webhooks/slack/interactions` | Slack button callbacks (Approve/Edit/Dismiss) |

### Draft Approval

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/drafts` | List agent draft outputs |
| `POST` | `/api/drafts/:id/approve` | Approve a draft |
| `POST` | `/api/drafts/:id/dismiss` | Dismiss a draft |

Full API contracts: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)

---

## Environment Variables

Copy `.env.example` and fill in your values. Minimum required:

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | Yes | PostgreSQL asyncpg connection string |
| `SYNC_DATABASE_URL` | Yes | PostgreSQL psycopg2 connection string |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `JWT_SECRET_KEY` | Production | Auth token signing (auto-generated on Render) |
| `JIRA_EMAIL` + `JIRA_API_TOKEN` | For Jira | Atlassian Cloud credentials |
| `FATHOM_API_KEY` | For calls | Fathom API key |
| `SLACK_BOT_TOKEN` + `SLACK_SIGNING_SECRET` | For Slack | Slack app credentials |

See [.env.example](.env.example) for the full list with inline comments and setup links.

---

## Architecture Principles

1. **Event-Driven** &mdash; External events create records. The Orchestrator reads and routes them. Agents never call each other directly.

2. **YAML-Driven Config** &mdash; Agent identities, traits, tools, pipelines, and workflows are in 4 YAML files (`backend/config/`). Change behavior by editing YAML, not Python.

3. **Hierarchical Delegation** &mdash; T1 decomposes tasks, T2 coordinates lanes, T3 executes. Results flow back up. T4 serves all tiers.

4. **Draft-First** &mdash; Agents produce drafts, not final actions. Humans approve/edit/dismiss via Slack buttons or the API.

5. **3-Tier Memory** &mdash; Working (in-process scratchpad), Episodic (ChromaDB per-agent diary), Semantic (ChromaDB shared knowledge pools).

6. **Slack-Push, Dashboard-Pull** &mdash; Slack is where notifications go. The dashboard is opened via deep-links from Slack cards.

7. **Async AI** &mdash; All Claude API calls run in background threads. API endpoints return immediately.

8. **WebSocket Everything** &mdash; Real-time updates for pipeline progress, agent status, new events. Frontend never polls.

9. **Customer Isolation** &mdash; Every DB query scoped to `customer_id`. Memory is per-customer.

---

## Deployment

| Component | Platform | Config |
|-----------|----------|--------|
| Backend API | Render | [`render.yaml`](render.yaml) |
| React Frontend | Vercel | [`vercel.json`](frontend/vercel.json) |
| Database | Neon PostgreSQL | Cloud managed |
| Vector DB | ChromaDB | Persistent (local) / Ephemeral (cloud) |

Full deployment guide with Slack setup: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Documentation

| Document | Purpose |
|----------|---------|
| [DOCUMENTATION.md](DOCUMENTATION.md) | Comprehensive technical docs (29 sections covering everything) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Step-by-step deployment (Render, Vercel, Neon, Slack) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, agent specs, event routing, pipeline stages |
| [docs/PRD.md](docs/PRD.md) | Product requirements, user stories, acceptance criteria |
| [docs/WIREFRAMES.md](docs/WIREFRAMES.md) | UI specs, design system, 3D specs |
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | Every endpoint with request/response JSON shapes |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | All 17 tables + ChromaDB collections |
| [CLAUDE.md](CLAUDE.md) | AI development context (conventions, rules, patterns) |

---

## Known Limitations

- **Neon free tier**: ~6s cold start on first DB connection. Pool pre-warming mitigates subsequent requests.
- **Render free tier**: ~30s cold start after inactivity.
- **No Redis required**: Celery runs in eager mode locally. Fine for dev, not ideal for production load.
- **ChromaDB ephemeral on Render**: Vector data is lost on restart. Backfill from PostgreSQL runs automatically on startup.
- **WebSockets**: May not work on Render free tier. The app degrades gracefully.

---

<p align="center">
  <sub>Built by Ayushmaan Singh Naruka &mdash; AI Hub Team, HivePro</sub>
</p>
