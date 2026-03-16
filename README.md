# HivePro CS Control Plane

AI-powered spatial dashboard that orchestrates 10 specialized agents to automate Customer Success workflows. Built with a React + Three.js frontend and a FastAPI + PostgreSQL + ChromaDB backend.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688)
![Three.js](https://img.shields.io/badge/Three.js-r161-black)

---

## What It Does

The Control Plane replaces manual CS processes with an always-on virtual workforce:

- **Agent Orchestration** — Routes events (Jira tickets, Fathom calls, cron jobs) to 10 specialized AI agents via a central Orchestrator
- **Customer Memory** — Maintains structured + semantic memory per customer (PostgreSQL + ChromaDB)
- **Spatial 3D Dashboard** — Immersive command center with neural sphere, health terrain, floating orbs, and particle rivers
- **AI Triage** — Auto-classifies incoming Jira tickets and suggests actions
- **Call Intelligence** — Extracts summaries, action items, and sentiment from call recordings
- **Health Monitoring** — Calculates daily health scores and flags at-risk customers
- **RAG-Powered Search** — Finds similar past issues across customers for faster resolution

### The 10 Agents

| Agent | Purpose |
|-------|---------|
| CS Orchestrator | Routes events to the correct agent |
| Customer Memory | Builds structured customer context |
| Call Intelligence | Extracts insights from call transcripts |
| Health Monitor | Calculates 0-100 health scores |
| Ticket Triage | Auto-classifies and prioritizes tickets |
| Troubleshooter | Deep-dives into ticket root cause |
| Escalation Summary | Generates L2/L3 escalation packages |
| QBR Value | Generates quarterly business review content |
| SOW Prerequisite | Pre-deployment checklists for new customers |
| Deployment Intelligence | Deployment guidance using RAG knowledge |

---

## Tech Stack

### Frontend
React 18, Vite, Tailwind CSS, Zustand, React Router 6, Axios, Three.js + @react-three/fiber + drei, Framer Motion, GSAP, Recharts, D3, @dnd-kit, fuse.js

### Backend
FastAPI, PostgreSQL 16 (Neon), SQLAlchemy 2.0 (async), Alembic, ChromaDB, Celery + Redis, Claude API (claude-sonnet-4-5-20250929), JWT auth, Playwright

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 16** (local or [Neon](https://neon.tech) cloud)
- **Redis** (optional — without it, tasks run synchronously)
- **Anthropic API Key** for Claude

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd hivepro-cs-control-plane
cp .env.example .env
```

Edit `.env` with your database URL, Anthropic API key, and other settings.

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed demo data (5 users, 10 customers, 300 health scores, 50 tickets, etc.)
python -m app.utils.seed

# Start the server
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`. Check health: `http://localhost:8000/api/health`

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 4. Login

After seeding, use any of these accounts (all passwords are `password123`):

| Email | Role |
|-------|------|
| `ayushmaan@hivepro.com` | Admin |
| `ariza@hivepro.com` | Admin |
| `vignesh@hivepro.com` | CS Engineer |
| `chaitanya@hivepro.com` | CS Engineer |
| `kazi@hivepro.com` | CS Manager |

---

## Environment Variables

```bash
# Database (async for FastAPI, sync for Alembic/Celery)
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SYNC_DATABASE_URL=postgresql://user:pass@host/db

# Redis (optional — leave empty for sync task execution)
REDIS_URL=

# Auth
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# ChromaDB
CHROMADB_PATH=./chromadb_data
CHROMADB_MODE=persistent  # or "ephemeral" for in-memory

# Frontend
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws
```

---

## Project Structure

```
hivepro-cs-control-plane/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings from .env
│   │   ├── database.py          # PostgreSQL async connection
│   │   ├── chromadb_client.py   # ChromaDB vector store
│   │   ├── websocket_manager.py # Real-time broadcast
│   │   ├── models/              # SQLAlchemy models (10 tables)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API endpoint handlers
│   │   ├── agents/              # 10 AI agent implementations
│   │   ├── services/            # Business logic (Claude, RAG, etc.)
│   │   ├── tasks/               # Celery async tasks
│   │   ├── middleware/          # JWT auth middleware
│   │   └── utils/               # Security helpers, seed script
│   ├── alembic/                 # Database migrations
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/               # Route-level page components
│       ├── components/          # UI components by domain
│       ├── three/               # 3D scenes (lazy-loaded)
│       ├── stores/              # Zustand state management
│       ├── services/            # API clients
│       ├── data/                # Seed/fallback data
│       └── utils/               # Formatters, helpers
│
├── docs/
│   ├── PRD.md                   # Product requirements
│   ├── WIREFRAMES.md            # UI specs, 3D specs, design system
│   ├── API_CONTRACT.md          # Endpoint request/response shapes
│   └── DATABASE_SCHEMA.md       # Table definitions, relationships
│
└── CLAUDE.md                    # AI development context
```

---

## Architecture

```
External Event (Jira / Fathom / Cron)
        │
        ▼
   ┌─────────┐     ┌──────────────┐
   │  Event   │────▶│ Orchestrator │
   │  Queue   │     └──────┬───────┘
   └─────────┘            │
                          ▼
              ┌─── Agent Router ───┐
              │                    │
    ┌─────────┴──┐          ┌─────┴────────┐
    │ Customer   │          │ Specialized  │
    │ Memory     │◀────────▶│ Agent (1-9)  │
    └─────┬──────┘          └──────┬───────┘
          │                        │
    ┌─────┴──────┐          ┌──────┴───────┐
    │ PostgreSQL │          │  Claude API  │
    │ + ChromaDB │          │  (async via  │
    └────────────┘          │   Celery)    │
                            └──────┬───────┘
                                   │
                            ┌──────┴───────┐
                            │  WebSocket   │
                            │  Broadcast   │
                            └──────┬───────┘
                                   │
                            ┌──────┴───────┐
                            │   Frontend   │
                            │  (React 3D)  │
                            └──────────────┘
```

**Key rules:**
- Agents never call each other directly — everything flows through the Orchestrator
- Customer Memory is the single source of truth for all customer data
- All Claude API calls run as async Celery tasks (never block the API thread)
- WebSocket broadcasts all real-time updates (no polling)
- 3D is progressive enhancement — 2D fallbacks always exist

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login, get JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/dashboard/stats` | Dashboard summary stats |
| GET | `/api/dashboard/agents` | Agent status overview |
| GET | `/api/dashboard/events` | Recent events feed |
| GET | `/api/dashboard/quick-health` | Customer health grid |
| GET | `/api/customers` | List customers (sortable, filterable) |
| GET | `/api/customers/:id` | Customer detail |
| GET | `/api/customers/:id/health-history` | Health score trend |
| GET | `/api/customers/:id/tickets` | Customer's tickets |
| GET | `/api/customers/:id/insights` | Customer's call insights |
| GET | `/api/customers/:id/similar-issues` | RAG-powered similar issues |
| GET | `/api/agents` | List all 10 agents with stats |
| GET | `/api/agents/:name` | Single agent detail |
| GET | `/api/agents/:name/logs` | Agent execution logs |
| POST | `/api/agents/:name/trigger` | Manually trigger an agent |
| GET | `/api/insights` | List call insights |
| GET | `/api/insights/sentiment-trend` | 30-day sentiment chart |
| GET | `/api/tickets` | List tickets (filterable) |
| POST | `/api/events` | Create event (triggers agent pipeline) |
| GET | `/api/reports` | List generated reports |
| WS | `/api/ws` | Real-time event stream |

Full request/response shapes are documented in `docs/API_CONTRACT.md`.

---

## Design System

The UI follows a spatial depth paradigm — not a traditional flat dashboard.

- **Void background:** `#020408` (near-black, not navy)
- **Accents:** Teal `#00F5D4`, Violet `#8B5CF6`, Cyan `#22D3EE`
- **Surfaces:** Three depth levels with `backdrop-blur(20px)`:
  - Near: `rgba(8,16,32,0.65)` — critical data
  - Mid: `rgba(8,16,32,0.45)` — supporting data
  - Far: `rgba(8,16,32,0.25)` — ambient context
- **Fonts:** Space Grotesk (display), IBM Plex Mono (data/labels), Inter (body)
- **Navigation:** Orbital arc at bottom-center (no sidebar), Command Palette (Cmd+K)

Full design specs in `docs/WIREFRAMES.md`.

---

## Development

```bash
# Backend (with auto-reload)
cd backend && uvicorn app.main:app --reload

# Frontend (with HMR)
cd frontend && npm run dev

# Run with Redis for async tasks (optional)
redis-server
cd backend && celery -A app.tasks.celery_app worker --loglevel=info
```

---

## License

Internal project — HivePro AI Hub Team.
