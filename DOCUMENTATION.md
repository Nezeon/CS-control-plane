# HivePro CS Control Plane — Complete Project Documentation

> **Codename:** Mission Control
> **Author:** Ayushmaan Singh Naruka (AI Hub Team, HivePro)
> **Design Tier:** Premium enterprise spatial 3D command center
> **Last Updated:** March 2, 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Solution Summary](#3-solution-summary)
4. [The 10 AI Agents](#4-the-10-ai-agents)
5. [Tech Stack](#5-tech-stack)
6. [Architecture Rules](#6-architecture-rules)
7. [Design System](#7-design-system)
8. [Project Structure](#8-project-structure)
9. [Database Schema](#9-database-schema)
10. [ChromaDB Vector Store](#10-chromadb-vector-store)
11. [Backend API Endpoints](#11-backend-api-endpoints)
12. [Agent Implementations](#12-agent-implementations)
13. [Backend Services](#13-backend-services)
14. [Celery Async Tasks](#14-celery-async-tasks)
15. [Auth System](#15-auth-system)
16. [WebSocket Real-Time](#16-websocket-real-time)
17. [Frontend Routing](#17-frontend-routing)
18. [Frontend Pages](#18-frontend-pages)
19. [Zustand Stores](#19-zustand-stores)
20. [Frontend API Services](#20-frontend-api-services)
21. [Frontend Components](#21-frontend-components)
22. [3D Components](#22-3d-components)
23. [Seed Data](#23-seed-data)
24. [Environment Variables](#24-environment-variables)
25. [Deployment Configuration](#25-deployment-configuration)
26. [Development Phases](#26-development-phases)
27. [Quick Start](#27-quick-start)
28. [Key Design Decisions](#28-key-design-decisions)
29. [Known Gaps & Limitations](#29-known-gaps--limitations)

---

## 1. Project Overview

The CS Control Plane is an AI-powered spatial dashboard that orchestrates **10 specialized agents** to automate Customer Success workflows at HivePro. It replaces manual processes like call analysis, ticket triage, health monitoring, and report generation with an always-on virtual CS workforce.

The frontend is a spatial 3D command center (not a traditional flat dashboard) built with React + Three.js. The backend is a FastAPI service with PostgreSQL, ChromaDB (vector search), and Celery (async task queue). All AI calls go through Claude (Anthropic API).

---

## 2. Problem Statement

Six critical pain points this project solves:

1. **Fathom recordings go unanalyzed** — Rich call data exists but no bandwidth to extract insights, action items, and sentiment
2. **Jira ticket overload** — Tickets pile up without intelligent triage, categorization, or duplicate detection
3. **No centralized health tracking** — At-risk customers identified too late because signals are scattered across tools
4. **Manual pre-meeting prep** — CS consultants spend 30-60 min before calls gathering context from multiple systems
5. **No cross-customer pattern recognition** — Recurring issues are not identified or leveraged across customers
6. **QBR preparation is time-consuming** — Monthly/quarterly business reviews require manual data compilation

---

## 3. Solution Summary

- **Event-Driven Orchestration** — External events (Jira webhooks, Fathom recordings, cron jobs) flow through a central Orchestrator that routes them to the correct AI agent
- **Customer Memory** — Structured + semantic memory for every customer (PostgreSQL for structured data, ChromaDB for vector embeddings/RAG)
- **Spatial 3D Dashboard** — Immersive command center with neural sphere, health terrain, floating orbs, particle rivers, and cinematic transitions
- **Real-Time WebSocket** — All updates (agent status, new events, alerts, health scores) broadcast instantly via WebSocket. The frontend never polls.
- **Async AI Processing** — All Claude API calls go through Celery tasks. The API returns 202 Accepted with a task_id. Results broadcast via WebSocket when ready.

---

## 4. The 10 AI Agents

| # | Agent Name | Lane | Trigger Event | Primary Output |
|---|------------|------|---------------|----------------|
| 1 | **CS Orchestrator** | Control | All events | Routes to correct agent |
| 2 | **Customer Memory** | Control | Called by all agents | Structured customer profile from DB |
| 3 | **Call Intelligence** | Value | `zoom_call_completed`, `fathom_recording_ready` | Summary, action items, sentiment, customer recap draft |
| 4 | **Health Monitor** | Value | `daily_health_check`, `manual_health_check` | Health score (0-100), risk level, factors, flags |
| 5 | **QBR/Value Narrative** | Value | `renewal_approaching` | QBR report content, value narrative |
| 6 | **Ticket Triage** | Support | `jira_ticket_created`, `jira_ticket_updated` | Category, severity, root cause hypothesis, action |
| 7 | **Troubleshooter** | Support | `support_bundle_uploaded` | Root cause analysis, resolution steps, communication draft |
| 8 | **Escalation Summary** | Support | `ticket_escalated` | Engineering escalation package with repro steps |
| 9 | **SOW & Prerequisite** | Delivery | `new_enterprise_customer` | Pre-deployment checklist |
| 10 | **Deployment Intelligence** | Delivery | `deployment_started` | Known issues, config guidance |

**Agent Lanes & Colors:**
- **Control** (Teal `#00F5D4`): Orchestrator, Memory
- **Value** (Emerald `#34D399`): Health Monitor, Call Intel, QBR
- **Support** (Amber `#FBBF24`): Triage, Troubleshooter, Escalation
- **Delivery** (Cyan `#22D3EE`): SOW, Deployment Intel

---

## 5. Tech Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI framework |
| Vite | 5.0.12 | Build tool |
| Tailwind CSS | 3.4.1 | Utility-first styling + custom void/glow CSS |
| Zustand | 4.5.0 | State management |
| React Router | 6.22.0 | Client-side routing |
| Axios | 1.6.5 | HTTP client |
| Three.js | 0.161.0 | 3D rendering engine |
| @react-three/fiber | 8.15.16 | React renderer for Three.js |
| @react-three/drei | 9.97.0 | Three.js helpers (OrbitControls, Html, Sparkles) |
| Framer Motion | 11.0.3 | Page transitions, scroll reveals, layout animations |
| GSAP | 3.12.5 | 3D camera movements, complex timelines |
| Recharts | 2.12.0 | Simple charts (line, area) |
| D3 | 7.8.5 | Complex charts (heatmap, stream graph, radial bar, force-directed) |
| @dnd-kit | 6.1.0 | Drag-and-drop interactions |
| fuse.js | latest | Fuzzy search for command palette |
| lucide-react | 0.575.0 | Icon library |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109+ | API framework |
| PostgreSQL | 16 | Primary database |
| SQLAlchemy | 2.0 | ORM (async via asyncpg, sync via psycopg2) |
| Alembic | 1.13+ | Database migrations |
| ChromaDB | 0.4+ | Vector database for RAG embeddings |
| Celery | 5.3+ | Async task queue for AI calls |
| Redis | 7.x | Celery broker/backend (optional, has sync fallback) |
| python-jose | 3.3+ | JWT authentication |
| passlib[bcrypt] | 1.7+ | Password hashing |
| Anthropic SDK | latest | Claude API client |
| Playwright | 1.40+ | Browser automation (Phase 2) |

### Deployment

| Platform | Purpose |
|----------|---------|
| Render | Backend hosting (FastAPI + Celery worker) |
| Vercel | Frontend hosting (Vite static) |
| Neon | Cloud PostgreSQL 16 |
| Upstash | Cloud Redis (optional) |

---

## 6. Architecture Rules

### Rule 1: Event-Driven Agent System
Everything flows through the Orchestrator. External events (Jira webhook, Fathom sync, cron) create an `events` record -> Orchestrator reads it -> routes to the correct agent -> agent reads Customer Memory -> executes (Claude API) -> writes output -> updates Customer Memory -> broadcasts via WebSocket.

**Agents NEVER call each other directly.** All communication goes through the Orchestrator or event system.

### Rule 2: Customer Memory is the Single Source of Truth
Every agent reads from and writes to the Customer Memory (PostgreSQL + ChromaDB). No agent maintains its own state about a customer.

### Rule 3: WebSocket for All Real-Time Updates
Any change that should appear immediately (agent status, new event, alert, health score) must broadcast via WebSocket. The frontend **never polls**.

### Rule 4: AI Calls are Always Async
All Claude API calls go through Celery tasks. The API returns `202 Accepted` with a `task_id`. Results broadcast via WebSocket. Never block the API thread with LLM calls. If Redis is unavailable, tasks run synchronously via `task_always_eager=True` fallback.

### Rule 5: 3D is Progressive Enhancement
Always build the 2D version first. 3D scenes are lazy-loaded (`React.lazy` + `Suspense`) and code-split into their own chunks. The app must be fully functional with 2D fallbacks. 3D enhances but never blocks.

### Rule 6: Spatial Depth Design
Three surface levels: near (0.65 opacity), mid (0.45), far (0.25). All surfaces use `backdrop-filter: blur(20px)`. Critical data uses surface-near. Supporting data uses surface-mid/far. The void (`#020408`) is the true background. No flat white or gray backgrounds.

### Rule 7: Orbital Navigation
No sidebar. The Orbital Nav arc is the primary navigation at the bottom-center. Command Palette (Cmd+K) is the power-user alternative. Breadcrumbs float at top-left. Content fills the full viewport.

---

## 7. Design System

### Color Palette

```
Void (Background):    #020408 (near-black, NOT navy)
Bio-Teal (Primary):   #00F5D4
Bio-Violet:           #8B5CF6
Bio-Cyan:             #22D3EE
Bio-Rose (Danger):    #FB7185
Bio-Amber (Warning):  #FBBF24
Bio-Emerald (Success):#34D399

Surfaces:
  Near:   rgba(8, 16, 32, 0.65) + blur(20px)
  Mid:    rgba(8, 16, 32, 0.45) + blur(16px)
  Far:    rgba(8, 16, 32, 0.25) + blur(8px)

Severity:
  P1: #FB7185 (Rose)
  P2: #FBBF24 (Amber)
  P3: #22D3EE (Cyan)
  P4: #64748B (Slate)

Text:
  Bright:  #F1F5F9 (headlines)
  Primary: #CBD5E1 (body)
  Muted:   #64748B (labels)
  Ghost:   #334155 (disabled)
```

### Typography

| Usage | Font | Weights |
|-------|------|---------|
| Display/Numbers | Space Grotesk | 500, 600, 700 |
| Data/Labels | IBM Plex Mono | 400, 500, 600 |
| Body | Inter | 400, 500, 600 |

### Tailwind Implementation

The actual frontend uses a slightly adapted palette in `tailwind.config.js`:
- `bg-bg` (#09090B), `bg-bg-subtle` (#111113), `bg-bg-elevated` (#18181B)
- `text-accent` (#6366F1), `text-data` (#06B6D4)
- Fonts: Inter (body), JetBrains Mono (mono)
- Custom animations: `fade-in`, `slide-in-right`, `slide-in-up`, `pulse-subtle`, `shimmer`, `spin-slow`

---

## 8. Project Structure

```
hivepro-cs-control-plane/
├── CLAUDE.md                          # AI development context
├── DOCUMENTATION.md                   # THIS FILE
├── README.md                          # Quick start guide
├── .env.example                       # Environment template (dev)
├── .env.production.example            # Environment template (production)
├── render.yaml                        # Render deployment config
│
├── docs/
│   ├── PRD.md                         # Product Requirements Document
│   ├── WIREFRAMES.md                  # UI/UX specifications
│   ├── API_CONTRACT.md                # API endpoint contracts
│   └── DATABASE_SCHEMA.md             # Schema design document
│
├── backend/
│   ├── requirements.txt               # Python dependencies
│   ├── alembic.ini                    # Migration config
│   ├── Procfile                       # Render start command
│   ├── runtime.txt                    # Python 3.11.7
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 72e7ed43351d_initial_tables.py
│   └── app/
│       ├── main.py                    # FastAPI entry, CORS, routers, WebSocket
│       ├── config.py                  # Settings from .env (pydantic-settings)
│       ├── database.py                # Async + Sync PostgreSQL engines
│       ├── chromadb_client.py         # ChromaDB client (persistent/ephemeral)
│       ├── websocket_manager.py       # WebSocket connection manager
│       ├── models/                    # SQLAlchemy models (10 tables)
│       ├── schemas/                   # Pydantic request/response schemas
│       ├── routers/                   # API endpoint handlers (10 routers)
│       ├── agents/                    # AI agent implementations (10 agents)
│       ├── services/                  # Business logic (Claude, RAG, events)
│       ├── tasks/                     # Celery async tasks
│       ├── middleware/auth.py         # JWT authentication middleware
│       └── utils/
│           ├── security.py            # Password hashing, token generation
│           └── seed.py                # Demo data seeder
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js                 # Dev proxy, chunk splitting
│   ├── tailwind.config.js             # Custom colors, fonts, animations
│   ├── vercel.json                    # Vercel deployment config
│   ├── index.html
│   └── src/
│       ├── main.jsx                   # React entry point
│       ├── App.jsx                    # Router + layout + auth guard
│       ├── index.css                  # Global CSS (void bg, cards, skeleton)
│       ├── stores/                    # Zustand state (11 stores)
│       ├── services/                  # Axios API clients + WebSocket
│       ├── three/                     # 3D scenes (lazy-loaded, code-split)
│       ├── components/
│       │   ├── layout/                # AppLayout, Sidebar, TopBar, CommandPalette
│       │   ├── shared/                # SurfaceCard, HealthRing, AnimatedCounter, etc.
│       │   ├── dashboard/             # FloatingOrbsGrid, NeuralSphereWrapper, LivePulse
│       │   ├── customers/             # PremiumGrid, DataTable, CustomerHero, HealthStory
│       │   ├── agents/                # NeuralNetwork, AgentBrainPanel, ReasoningLog
│       │   ├── insights/              # SentimentSpectrum, InsightCard, ActionTracker
│       │   ├── tickets/               # WarroomTable, TicketDetailDrawer, Constellation
│       │   └── reports/               # HealthHeatmap, TicketVelocity, SentimentRiver, AgentThroughput
│       ├── pages/                     # 9 page components
│       ├── data/                      # Seed/demo data for offline mode
│       ├── hooks/                     # useScrollReveal
│       └── utils/                     # formatters, chartHelpers, cn
│
└── e2e/                               # Playwright E2E tests (Phase 16)
```

---

## 9. Database Schema

PostgreSQL 16 with 10 tables. All primary keys are UUIDs. Timestamps use `TIMESTAMPTZ` with server defaults. JSONB columns store flexible structured data.

### 9.1 users

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | TEXT | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| role | VARCHAR(50) | DEFAULT `'cs_engineer'` (admin, cs_manager, cs_engineer, viewer) |
| avatar_url | TEXT | nullable |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), auto-update |

**Relationships:** owned_customers, assigned_tickets, assigned_alerts, owned_action_items

### 9.2 customers

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| industry | VARCHAR(100) | |
| tier | VARCHAR(50) | enterprise, mid_market, smb |
| contract_start | DATE | |
| renewal_date | DATE | |
| primary_contact_name | VARCHAR(255) | |
| primary_contact_email | VARCHAR(255) | |
| cs_owner_id | UUID | FK -> users(id) |
| deployment_mode | VARCHAR(50) | DEFAULT `'OVA'` (OVA, Cloud, Hybrid, On-Premise) |
| product_version | VARCHAR(50) | |
| integrations | JSONB | DEFAULT `'[]'` — list of integration names |
| known_constraints | JSONB | DEFAULT `'[]'` — list of constraints |
| metadata | JSONB | DEFAULT `'{}'` — arbitrary data |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** cs_owner_id, tier, renewal_date
**Relationships:** cs_owner (User), health_scores, tickets, call_insights, agent_logs, events, alerts, action_items, reports (all cascade delete where appropriate)

### 9.3 health_scores

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK -> customers(id) ON DELETE CASCADE |
| score | INTEGER | CHECK (0-100) |
| factors | JSONB | NOT NULL — weighted factor scores |
| risk_flags | JSONB | DEFAULT `'[]'` — e.g. `["high_ticket_volume", "no_calls_30d"]` |
| risk_level | VARCHAR(20) | healthy, watch, high_risk, critical, trending_down, renewal_risk |
| calculated_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** (customer_id, calculated_at DESC) for latest score lookup, risk_level for filtering

**Factors JSONB shape:**
```json
{
  "product_adoption": {"score": 75, "rationale": "Full scan coverage"},
  "support_health": {"score": 60, "rationale": "3 open P2 tickets"},
  "engagement": {"score": 80, "rationale": "Weekly calls, responsive"},
  "sentiment": {"score": 70, "rationale": "Mostly positive recent calls"},
  "outcome_delivery": {"score": 65, "rationale": "Partial value realization"},
  "contract_risk": {"score": 85, "rationale": "Renewal in 6 months, stable"}
}
```

**Risk Level Thresholds:** healthy (70-100), watch (50-69), high_risk (25-49), critical (0-24), trending_down (dropped 15+ in 7 days), renewal_risk (at-risk + renewal < 90 days)

### 9.4 tickets

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| jira_id | VARCHAR(50) | UNIQUE |
| customer_id | UUID | FK -> customers(id) |
| summary | TEXT | NOT NULL |
| description | TEXT | |
| ticket_type | VARCHAR(50) | deployment, scan_failure, connector, performance, ui, integration, feature_request |
| severity | VARCHAR(10) | P1, P2, P3, P4 |
| status | VARCHAR(50) | open, in_progress, waiting, resolved, closed |
| assigned_to_id | UUID | FK -> users(id) |
| triage_result | JSONB | AI-generated triage output |
| troubleshoot_result | JSONB | AI-generated root cause output |
| escalation_summary | JSONB | AI-generated escalation package |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |
| resolved_at | TIMESTAMPTZ | nullable, set when status = resolved |
| sla_deadline | TIMESTAMPTZ | nullable, P1=4h, P2=8h, P3=3d, P4=7d |

**Indexes:** customer_id, status, severity, jira_id, assigned_to_id, sla_deadline (filtered where status not in resolved/closed)

**triage_result JSONB shape:**
```json
{
  "category": "scan_failure",
  "confirmed_severity": "P1",
  "suggested_action": "Check scanner configuration for subnet range",
  "potential_root_cause": "CIDR range does not include target subnet",
  "is_duplicate": false,
  "duplicate_of": null,
  "estimated_effort": "medium",
  "requires_escalation": false,
  "confidence": 0.92,
  "reasoning": "Scanner config shows limited subnet coverage..."
}
```

**troubleshoot_result JSONB shape:**
```json
{
  "root_cause": "Scanner profile CIDR range excludes subnet 10.0.1.x",
  "confidence": 0.78,
  "evidence": ["Scanner config shows 10.0.0.0/24", "Subnet 10.0.1.x in different VLAN"],
  "resolution_steps": [
    {"step": 1, "action": "Update scanner profile", "details": "Expand to 10.0.0.0/16"}
  ],
  "estimated_time": "2-4 hours",
  "requires_customer_action": true,
  "customer_communication_draft": "Dear team...",
  "reasoning": "Evidence points to network segmentation issue..."
}
```

### 9.5 call_insights

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK -> customers(id) |
| fathom_recording_id | VARCHAR(255) | nullable |
| call_date | TIMESTAMPTZ | NOT NULL |
| participants | JSONB | DEFAULT `'[]'` — list of attendee names |
| summary | TEXT | 3-5 sentence summary |
| decisions | JSONB | DEFAULT `'[]'` |
| action_items | JSONB | DEFAULT `'[]'` — `[{title, owner, deadline}]` |
| risks | JSONB | DEFAULT `'[]'` |
| sentiment | VARCHAR(20) | positive, neutral, negative, mixed |
| sentiment_score | FLOAT | -1.0 to 1.0 |
| key_topics | JSONB | DEFAULT `'[]'` |
| customer_recap_draft | TEXT | AI-generated email draft |
| raw_transcript | TEXT | Full call transcript |
| processed_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** (customer_id, call_date DESC), sentiment

### 9.6 events

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| event_type | VARCHAR(100) | NOT NULL (e.g. `jira_ticket_created`, `daily_health_check`) |
| source | VARCHAR(50) | jira, fathom, slack, api, manual_trigger, celery_cron |
| payload | JSONB | NOT NULL — event-specific data |
| status | VARCHAR(20) | DEFAULT `'pending'` (pending, processing, completed, failed, queued) |
| routed_to | VARCHAR(100) | Agent name that processed it |
| customer_id | UUID | FK -> customers(id), nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| processed_at | TIMESTAMPTZ | nullable |

**Indexes:** status, event_type, created_at DESC

### 9.7 agent_logs

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| agent_name | VARCHAR(100) | NOT NULL |
| agent_type | VARCHAR(50) | control, value, support, delivery |
| event_type | VARCHAR(100) | What triggered the agent |
| trigger_event | VARCHAR(100) | e.g. `api`, `jira`, `celery_cron` |
| customer_id | UUID | FK -> customers(id), nullable |
| input_summary | TEXT | Truncated to 2000 chars |
| output_summary | TEXT | JSON stringified, truncated to 2000 chars |
| reasoning_summary | TEXT | Agent's reasoning, truncated to 2000 chars |
| status | VARCHAR(20) | DEFAULT `'running'` (running, completed, failed) |
| duration_ms | INTEGER | Execution time in milliseconds |
| metadata | JSONB | DEFAULT `'{}'` |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** (agent_name, created_at DESC), customer_id, status

### 9.8 alerts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK -> customers(id) ON DELETE CASCADE |
| alert_type | VARCHAR(50) | high_risk, watch, trending_down, renewal_risk, ticket_sla_breach |
| severity | VARCHAR(20) | critical, high, medium, low |
| title | TEXT | NOT NULL |
| description | TEXT | |
| suggested_action | TEXT | |
| similar_past_issues | JSONB | DEFAULT `'[]'` |
| assigned_to_id | UUID | FK -> users(id), nullable |
| status | VARCHAR(20) | DEFAULT `'open'` (open, acknowledged, resolved, dismissed) |
| slack_notified | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| resolved_at | TIMESTAMPTZ | nullable |

**Indexes:** customer_id, status, severity
**Status Flow:** open -> acknowledged -> resolved, OR open -> dismissed

### 9.9 action_items

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK -> customers(id) |
| source_type | VARCHAR(50) | call_insight, ticket, alert, manual |
| source_id | UUID | Reference to source record |
| owner_id | UUID | FK -> users(id), nullable |
| title | TEXT | NOT NULL |
| description | TEXT | |
| deadline | TIMESTAMPTZ | nullable |
| status | VARCHAR(20) | DEFAULT `'pending'` (pending, in_progress, completed) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| completed_at | TIMESTAMPTZ | nullable |

**Indexes:** customer_id, owner_id, status, deadline (filtered where status = pending)

### 9.10 reports

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| report_type | VARCHAR(50) | weekly_digest, monthly_report, qbr |
| customer_id | UUID | FK -> customers(id), nullable (null = org-wide) |
| title | TEXT | NOT NULL |
| content | JSONB | NOT NULL — report-specific structured data |
| period_start | DATE | |
| period_end | DATE | |
| generated_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** report_type, customer_id, generated_at DESC

---

## 10. ChromaDB Vector Store

ChromaDB provides semantic similarity search (RAG) across three collections. Uses default sentence-transformers for embeddings. L2 (Euclidean) distance metric. Similarity is calculated as `max(0.0, 1.0 - distance)`.

**Modes:**
- `persistent` (local dev) — saves to `./chromadb_data` on disk
- `ephemeral` (production/Render) — in-memory, lost on restart

### Collection: ticket_embeddings
- **Purpose:** Find similar past tickets for triage and troubleshooting
- **Document:** Ticket summary + description + resolution (if resolved)
- **Metadata:** `{jira_id, customer_name, status, severity, resolution}`
- **Used by:** Triage Agent (top 5 similar), Troubleshooter Agent (top 5 resolved), ticket similar endpoint

### Collection: call_insight_embeddings
- **Purpose:** Find similar call discussions, surface patterns
- **Document:** Call summary + key topics + risks + decisions
- **Metadata:** `{customer_name, sentiment, key_topics}`
- **Used by:** Call Intelligence Agent, insights API

### Collection: problem_embeddings
- **Purpose:** Cross-customer pattern matching for known problems
- **Document:** Problem description + root cause + resolution steps
- **Metadata:** `{customer_id, customer_name, ticket_id, resolved_in_days}`
- **Used by:** Troubleshooter Agent, knowledge base queries

### Seed Data Counts

| Table | Count |
|-------|-------|
| users | 5 |
| customers | 10 |
| health_scores | ~300 (30 days x 10 customers) |
| tickets | 50 |
| call_insights | 100 |
| agent_logs | 200 |
| events | 150 |
| alerts | 15 |
| action_items | 30 |
| reports | 8 |

---

## 11. Backend API Endpoints

All endpoints are prefixed with `/api`. Authentication uses Bearer JWT tokens (except login and health check).

### 11.1 Auth (`/api/auth`)

| Method | Path | Input | Output | Description |
|--------|------|-------|--------|-------------|
| POST | `/login` | `{email, password}` | `{access_token, refresh_token, user, token_type, expires_in}` | Login, returns JWT pair |
| POST | `/refresh` | `{refresh_token}` | `{access_token, token_type, expires_in}` | Refresh expired access token |
| GET | `/me` | Bearer token | `{id, email, full_name, role, avatar_url, created_at, updated_at}` | Current user profile |

### 11.2 Dashboard (`/api/dashboard`)

| Method | Path | Output | Description |
|--------|------|--------|-------------|
| GET | `/stats` | `{total_customers, at_risk_count, open_tickets, avg_health_score, trends}` | KPI cards with 7-day trend deltas |
| GET | `/agents` | `[{name, display_name, lane, status, tasks_today, avg_response_ms, last_active}]` | All 10 agents with live stats |
| GET | `/events?limit=20&offset=0` | `{events: [...], total, limit, offset}` | Latest events with human-readable descriptions |
| GET | `/quick-health` | `[{id, name, health_score, risk_level, risk_count, initial}]` | Top 12 customers sorted by risk (worst first) |

### 11.3 Customers (`/api/customers`)

| Method | Path | Input/Params | Output | Description |
|--------|------|--------------|--------|-------------|
| GET | `/` | `?search=&risk_level=&cs_owner_id=&tier=&sort_by=score&sort_order=asc&limit=20&offset=0` | `{customers: [...], total, limit, offset}` | List with latest health scores, ticket counts, call dates |
| GET | `/:id` | UUID | Full customer detail with deployment, health, metrics | Customer profile |
| POST | `/` | `CustomerCreate` body | New customer object | Create customer |
| PUT | `/:id` | `CustomerUpdate` body (partial) | Updated customer | Update fields |
| GET | `/:id/health-history?days=90` | days (1-365) | `{customer_id, history: [{date, score, risk_level, risk_flags}]}` | Health score time series |
| GET | `/:id/tickets?limit=10&offset=0` | | `{tickets: [...], total}` | Customer's tickets with SLA info |
| GET | `/:id/insights?limit=10&offset=0` | | `{insights: [...], total}` | Customer's call insights |
| GET | `/:id/action-items` | | `{action_items: [...]}` | Pending & completed action items |
| GET | `/:id/similar-issues` | | `{query_context, similar_issues: [...]}` | RAG vector search for similar past issues |

### 11.4 Tickets (`/api/tickets`)

| Method | Path | Input/Params | Output | Description |
|--------|------|--------------|--------|-------------|
| GET | `/` | `?search=&status=&severity=&customer_id=&ticket_type=&sort_by=created&limit=20&offset=0` | `{tickets: [...], total, limit, offset}` | Filtered list with SLA status |
| GET | `/:id` | UUID | Full ticket with triage_result, troubleshoot_result, escalation_summary | Ticket detail |
| PUT | `/:id/status` | `{status}` | `{id, status, updated_at}` | Update status, auto-set resolved_at |
| PUT | `/:id/assign` | `{assigned_to_id}` | `{id, assigned_to_id, updated_at}` | Assign to user |
| POST | `/:id/triage` | ticket_id | `{task_id, message, status}` (202) | Trigger Ticket Triage Agent |
| POST | `/:id/troubleshoot` | ticket_id | `{task_id, message, status}` (202) | Trigger Troubleshooter Agent |
| GET | `/:id/similar` | ticket_id | `{query_context, similar_issues: [...]}` | RAG search for similar tickets |

### 11.5 Insights (`/api/insights`)

| Method | Path | Input/Params | Output | Description |
|--------|------|--------------|--------|-------------|
| GET | `/` | `?search=&customer_id=&sentiment=&date_from=&date_to=&limit=20&offset=0` | `{insights: [...], total, limit, offset}` | Filtered call insights |
| GET | `/:id` | UUID | Full insight with raw_transcript | Insight detail |
| GET | `/sentiment-trend?days=30&customer_id=` | | `{trend: [{date, avg_sentiment_score, call_count}]}` | Daily sentiment averages |
| GET | `/action-items?status=&owner_id=` | | `{action_items: [...], summary: {pending, overdue, completed}}` | All action items |
| POST | `/sync-fathom` | | `{task_id, message, status}` (202) | Trigger Fathom sync (mock) |
| PUT | `/action-items/:id` | `{status}` | `{id, status, completed_at}` | Update action item status |

### 11.6 Agents (`/api/agents`)

| Method | Path | Input/Params | Output | Description |
|--------|------|--------------|--------|-------------|
| GET | `/` | | `{agents: [...]}` | All 10 agents with live stats |
| GET | `/orchestration-flow?limit=20` | | `{flows: [...]}` | Recent event routing timeline |
| GET | `/:name` | agent_name | `AgentInfo` (detail + stats) | Single agent info |
| GET | `/:name/logs?limit=20&offset=0` | | `{logs: [...], total, limit, offset}` | Agent execution logs |
| POST | `/:name/trigger` | `{context?, customer_id?}` | `{task_id, message, status}` (202) | Manually trigger any agent |

### 11.7 Events (`/api/events`)

| Method | Path | Input/Params | Output | Description |
|--------|------|--------------|--------|-------------|
| GET | `/` | `?event_type=&source=&customer_id=&status=&limit=20&offset=0` | `{events: [...], total, limit, offset}` | List events |
| POST | `/` | `{event_type, source?, payload, customer_id?}` | `{id, event_type, status, created_at}` (201) | Create event, triggers orchestrator |

### 11.8 Alerts (`/api/alerts`)

| Method | Path | Output | Description |
|--------|------|--------|-------------|
| GET | `/?status=&severity=&customer_id=&limit=20&offset=0` | `{alerts: [...], total, limit, offset}` | List alerts |
| PUT | `/:id/acknowledge` | `{id, status: "acknowledged", resolved_at}` | Acknowledge alert |
| PUT | `/:id/resolve` | `{id, status: "resolved", resolved_at}` | Resolve alert |
| PUT | `/:id/dismiss` | `{id, status: "dismissed", resolved_at}` | Dismiss alert |

### 11.9 Health (`/api/health`)

| Method | Path | Output | Description |
|--------|------|--------|-------------|
| GET | `/scores` | `{scores: [...]}` | All customers' latest health scores |
| GET | `/at-risk` | `{scores: [...]}` | Only at-risk customers |
| POST | `/run-check` | `{task_id, message, status}` (202) | Trigger health check for all customers |
| GET | `/trends?days=30` | `{daily_averages: [{date, avg_score, at_risk_count}]}` | Daily health trends |

### 11.10 Reports (`/api/reports`)

| Method | Path | Input/Params | Output | Description |
|--------|------|--------------|--------|-------------|
| GET | `/` | `?report_type=&customer_id=&limit=20&offset=0` | `[{id, report_type, title, customer_name, period_start, period_end, generated_at}]` | List reports |
| GET | `/analytics?days=30` | | `{health_heatmap, ticket_velocity, sentiment_distribution, agent_performance}` | Aggregated analytics data |
| GET | `/:id` | UUID | Full report with content JSON | Report detail |
| POST | `/generate` | `{report_type, customer_id?, period_start?, period_end?}` | `{task_id, message, status, report_id}` (202) | Generate new report |

### 11.11 WebSocket (`/api/ws`)

- `GET /api/health` — HTTP health check (`{status: "healthy", version: "1.0.0"}`)
- `WS /api/ws` — WebSocket endpoint for real-time events

---

## 12. Agent Implementations

All agents inherit from `BaseAgent` which provides: timing (`perf_counter`), exception handling, logging (`AgentLog` record creation), and a standard return format: `{success, output, reasoning_summary}`.

### 12.1 CS Orchestrator (`orchestrator.py`)

**Role:** Central event router. Not an executable agent itself — it reads the event type and dispatches to the correct agent.

**Event Routing Table:**
```
jira_ticket_created     -> ticket_triage
jira_ticket_updated     -> ticket_triage
ticket_escalated        -> escalation_summary
support_bundle_uploaded -> troubleshooter
zoom_call_completed     -> call_intelligence
fathom_recording_ready  -> call_intelligence
daily_health_check      -> health_monitor
manual_health_check     -> health_monitor
renewal_approaching     -> qbr_value
new_enterprise_customer -> sow_prerequisite
deployment_started      -> deployment_intelligence
```

**Flow:** Receives event dict -> looks up event_type in routing table -> calls `MemoryAgent.build_memory()` if customer_id present -> calls `target_agent.run(db, event, customer_memory)` -> returns result.

### 12.2 Customer Memory Agent (`memory_agent.py`)

**Role:** Builds a structured customer context dict from the database. Called directly by the Orchestrator before every agent execution — NOT triggered by events.

**Returns:**
```json
{
  "customer": { "id", "name", "industry", "tier", "contract_start", "renewal_date", "primary_contact", "deployment_mode", "product_version", "integrations", "known_constraints" },
  "health": { "current_score", "risk_level", "factors", "risk_flags", "calculated_at", "trend": [last 30 days] },
  "tickets": { "total_recent": int, "open_count": int, "items": [last 20 tickets] },
  "calls": { "total_recent": int, "items": [last 10 call insights] },
  "action_items": [pending items],
  "alerts": [active alerts]
}
```

### 12.3 Ticket Triage Agent (`triage_agent.py`)

**Trigger:** `jira_ticket_created`, `jira_ticket_updated`
**Required Payload:** `{summary}` (+ optional description, severity, jira_id, ticket_type)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 2048 | Temperature: 0.2

**Process:**
1. Queries RAG (top 5 similar tickets from `ticket_embeddings`)
2. Builds prompt with ticket data + customer memory + RAG context
3. Calls Claude for classification

**Output JSON:** `{category, confirmed_severity, suggested_action, potential_root_cause, is_duplicate, duplicate_of, estimated_effort, requires_escalation, escalation_reason, confidence, reasoning}`

**Dedicated endpoint:** `POST /api/tickets/:id/triage` (auto-populates payload from DB)

### 12.4 Troubleshooter Agent (`troubleshoot_agent.py`)

**Trigger:** `support_bundle_uploaded`
**Required Payload:** `{summary}` (+ optional description, severity, triage_result)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 3000 | Temperature: 0.3

**Process:**
1. Queries RAG (top 5 **resolved** similar tickets)
2. Builds prompt with ticket + customer memory + triage results + RAG context
3. Calls Claude for root cause analysis

**Output JSON:** `{root_cause, confidence, evidence, resolution_steps, estimated_time, requires_customer_action, customer_communication_draft, reasoning}`

**Dedicated endpoint:** `POST /api/tickets/:id/troubleshoot`

### 12.5 Escalation Summary Agent (`escalation_agent.py`)

**Trigger:** `ticket_escalated`
**Required Payload:** `{summary or ticket_id}` (+ optional description, severity, triage_result, troubleshoot_result)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 3000 | Temperature: 0.2

**Output JSON:** `{problem_statement, investigation_summary, reproduction_steps, impact_assessment: {severity, affected_users, business_impact}, technical_details: {environment, error_details, related_components}, suggested_next_steps, escalation_urgency, reasoning}`

**Save:** Updates `ticket.escalation_summary` JSONB field

### 12.6 Health Monitor Agent (`health_monitor.py`)

**Trigger:** `daily_health_check`, `manual_health_check`
**Required Payload:** None (uses customer memory from DB)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 2048 | Temperature: 0.2

**Analyzes 6 weighted factors:**
1. Product Adoption (0.20)
2. Support Health (0.20)
3. Engagement (0.15)
4. Sentiment (0.15)
5. Outcome Delivery (0.15)
6. Contract/Renewal Risk (0.15)

**Output JSON:** `{score, risk_level, factors: {each with score + rationale}, risk_flags, summary, recommended_actions}`

**Save:** Creates `HealthScore` record via `save_score()` method

### 12.7 Call Intelligence Agent (`call_intel_agent.py`)

**Trigger:** `zoom_call_completed`, `fathom_recording_ready`
**Required Payload:** `{transcript}` (+ optional participants, duration_minutes, recording_id)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 3000 | Temperature: 0.3

**Output JSON:** `{summary, sentiment, sentiment_score, key_topics, decisions, action_items: [{title, owner, deadline}], risks, customer_recap_draft}`

**Save:** Creates `CallInsight` record with full transcript stored

### 12.8 QBR/Value Agent (`qbr_agent.py`)

**Trigger:** `renewal_approaching`
**Required Payload:** None (uses customer memory)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 3000 | Temperature: 0.3

**Output JSON:** QBR report content including value narrative, health summary, recommendations

**Save:** Creates `Report` record (type: `qbr`)

### 12.9 SOW & Prerequisite Agent (`sow_agent.py`)

**Trigger:** `new_enterprise_customer`
**Required Payload:** None (uses customer memory)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 2048 | Temperature: 0.2

**Output:** Pre-deployment checklist, prerequisite requirements
**Save:** No persistence path currently implemented (output discarded)

### 12.10 Deployment Intelligence Agent (`deployment_intel_agent.py`)

**Trigger:** `deployment_started`
**Required Payload:** None (uses customer memory + RAG)
**Claude Model:** claude-sonnet-4-5-20250929 | Max Tokens: 2048 | Temperature: 0.3

**Output:** Known issues, configuration guidance, similar deployment insights from RAG
**Save:** No persistence path currently implemented (output discarded)

---

## 13. Backend Services

### 13.1 ClaudeService (`services/claude_service.py`)

Wrapper around the Anthropic Claude API. Lazy-initializes the client on first use.

**Methods:**
- `generate_sync(system_prompt, user_message, max_tokens=4096, temperature=0.3)` — Synchronous call to Claude. Returns `{content, input_tokens, output_tokens, model}`. Never raises exceptions; returns `{error, detail}` on failure.
- `parse_json_response(content)` — Extracts JSON from Claude response. Handles markdown ` ```json ... ``` ` code fences. Returns parsed dict or `{error: "parse_failed", raw: content}`.

### 13.2 RAGService (`services/rag_service.py`)

Vector DB operations using ChromaDB for semantic similarity search.

**Embed Methods:**
- `embed_ticket(ticket_id, text, metadata)` — Upserts into `ticket_embeddings`
- `embed_insight(insight_id, text, metadata)` — Upserts into `call_insight_embeddings`
- `embed_problem(problem_id, text, metadata)` — Upserts into `problem_embeddings`

**Query Methods:**
- `find_similar_tickets(query_text, n_results=5, where=None)` — Returns `[{id, text, metadata, similarity}]`
- `find_similar_insights(query_text, n_results=5, where=None)` — Same shape
- `find_similar_problems(query_text, n_results=5)` — Same shape

Similarity = `max(0.0, 1.0 - distance)` (ChromaDB returns L2 distances)

### 13.3 EventService (`services/event_service.py`)

Processes events through the orchestrator and broadcasts via WebSocket.

**`create_and_process_event(db, event_type, source, payload, customer_id)` flow:**
1. Create Event record in DB (status: "pending")
2. Broadcast `event_received` via WebSocket
3. Try Celery dispatch → if available, return task_id, set status to "queued"
4. Fallback to sync orchestrator.route() → call agent-specific save methods
5. Set status to "completed" or "failed"
6. Broadcast `event_processed`
7. If risk_level in (high_risk, critical): broadcast `new_alert`

---

## 14. Celery Async Tasks

### Configuration (`tasks/celery_app.py`)

- **Broker:** Redis (`settings.REDIS_URL`) or `memory://` fallback
- **Backend:** Redis or `rpc://` fallback
- **Serializer:** JSON
- **Task time limit:** 300 seconds (5 min)
- **Soft time limit:** 270 seconds
- **Fallback:** If `REDIS_URL` not set → `task_always_eager=True` (sync execution in-process)

### Task: `process_event` (`tasks/agent_tasks.py`)

Celery task with `max_retries=2`.

1. Update Event.status to "processing"
2. Call `orchestrator.route(db, event)`
3. Post-processing: call agent-specific save methods (save_score, save_insight, save_result)
4. Update Event.status to "completed" or "failed"
5. Return `{event_id, agent_name, success, reasoning}`

### Task: `run_health_check_all` (`tasks/agent_tasks.py`)

Runs health checks for all customers.

1. Query all customers from DB
2. For each customer: create event, route through orchestrator, save health score
3. Return `{total, succeeded, failed, results: [{customer_id, customer_name, success}]}`

---

## 15. Auth System

### JWT Flow

- **Access Token:** HS256 JWT, 15 minutes TTL (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token:** HS256 JWT, 7 days TTL (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Password Hashing:** bcrypt via passlib (auto-handles salt)

### Security Utils (`utils/security.py`)

- `hash_password(password)` — Returns bcrypt hash
- `verify_password(plain, hashed)` — Compares plaintext against hash
- `create_access_token(data)` — JWT with `{...data, exp, type: "access"}`
- `create_refresh_token(data)` — JWT with `{...data, exp, type: "refresh"}`
- `decode_token(token)` — Validates JWT, returns payload. Raises 401 on invalid.

### Auth Middleware (`middleware/auth.py`)

- `get_current_user(token, db)` — OAuth2PasswordBearer dependency. Validates access token, fetches user from DB, checks `is_active`. Raises 401 on failure.
- `require_role(*roles)` — RBAC dependency. Wraps `get_current_user`, checks `user.role in roles`. Raises 403 on unauthorized.

---

## 16. WebSocket Real-Time

### Connection Manager (`websocket_manager.py`)

Singleton that manages all WebSocket connections with thread-safe asyncio.Lock.

**Methods:**
- `connect(websocket, client_id=None)` — Accepts connection, returns connection_id (UUID)
- `disconnect(connection_id)` — Removes from active connections
- `broadcast(event_type, data)` — Sends to ALL connected clients. Auto-cleans broken connections.
- `send_to(connection_id, event_type, data)` — Sends to specific client

**Message Format:**
```json
{
  "type": "event_type",
  "data": { ... },
  "timestamp": "2026-03-02T12:34:56.789Z"
}
```

**Event Types Broadcast:**
| Event | When |
|-------|------|
| `connected` | Client connects |
| `pong` | Heartbeat response |
| `event_received` | New event created |
| `event_processing` | Celery task queued |
| `event_processed` | Agent execution complete |
| `new_alert` | High-risk health score detected |
| `agent_status` | Agent state changed |
| `ticket_status_changed` | Ticket status updated |
| `alert_updated` | Alert acknowledged/resolved |

---

## 17. Frontend Routing

**Router:** React Router v6 with `BrowserRouter`

| Path | Page Component | Auth Required | Description |
|------|---------------|---------------|-------------|
| `/login` | LoginPage | No | Login form with 3D neural sphere |
| `/` | DashboardPage | Yes | Command Center — KPIs, neural sphere, live pulse |
| `/customers` | CustomersPage | Yes | Customer Observatory — grid/table/solar views |
| `/customers/:id` | CustomerDetailPage | Yes | Deep Dive — hero, health story, intel panels |
| `/agents` | AgentsPage | Yes | Agent Nexus — neural network, brain panel |
| `/insights` | InsightsPage | Yes | Signal Intelligence — sentiment, insights, actions |
| `/tickets` | TicketsPage | Yes | Ticket Warroom — table, constellation, drawer |
| `/reports` | ReportsPage | Yes | Analytics Lab — heatmap, velocity, river, throughput |
| `/settings` | SettingsPage | Yes | Preferences, system status, account |

**Guards:**
- `ProtectedRoute` wraps all authenticated routes
- Redirects to `/login` if no valid token
- Shows loading spinner while checking auth

**Layout:**
- `AppLayout` wraps all protected pages (Sidebar, TopBar, CommandPalette, ToastContainer)
- Page transitions via Framer Motion `AnimatePresence`

---

## 18. Frontend Pages

### LoginPage
- Split layout: left side shows 3D NeuralSphere (lazy-loaded), right side shows login form
- KPI pills display live stats (Avg Health, Customers, Agents)
- Email/password form with password visibility toggle
- **Demo mode:** If backend is unreachable (network error), accepts any credentials and uses seed data
- On success: stores JWT tokens in localStorage, connects WebSocket, navigates to `/`

### DashboardPage (Command Center)
- Fetches: `dashboardStore.fetchAll()` (stats, agents, events, quickHealth) in parallel
- **Sections:**
  1. Header with live date/time
  2. FloatingOrbsGrid — 4 KPI metric cards (Avg Health, Open Tickets, Calls, Active Agents)
  3. Two-column grid: NeuralSphereWrapper (3D agent globe) + LivePulse (EKG event timeline)
  4. HealthTerrainWrapper (3D topographic health map)

### CustomersPage (Customer Observatory)
- **Filters:** Search (debounced 300ms), risk level pills, tier dropdown, sort dropdown
- **Views:** Grid (PremiumGrid with 3D-tilt cards), Table (DataTable with sortable columns)
- **QuickIntelPanel:** Hover-triggered side panel showing customer summary
- Uses: `customerStore` (customers, filters, viewMode, hoveredCustomer)

### CustomerDetailPage (Deep Dive)
- Fetches in parallel: detail, health history, tickets, insights, action items, similar issues
- **Sections:**
  1. Back navigation to `/customers`
  2. CustomerHero — company info, tier, health ring, quick metrics
  3. HealthStory — trend line chart + health factor breakdown
  4. IntelPanels — 3-column layout: Tickets | Insights | Similar Issues (RAG)

### AgentsPage (Agent Nexus)
- **Views:** Grid (agent cards) vs Network (D3 force-directed neural graph)
- Header with aggregate stats (active, idle, tasks today)
- AgentCard grid: name, lane color, tasks, success rate, avg latency
- Recent Activity section (latest agent logs)
- **AgentBrainPanel:** Right slide-out drawer showing agent detail, config, reasoning logs
- Uses: `agentStore` (agents, selectedAgent, agentLogs, brainPanelOpen)

### InsightsPage (Signal Intelligence)
- **Filters:** Search (debounced), sentiment filter pills (All, Positive, Neutral, Negative)
- SentimentSpectrum chart — full-width sentiment waveform over time
- Two-column layout:
  - Left: InsightCard grid (expandable cards with summary, action items, sentiment)
  - Right: ActionTracker sticky panel (pending/overdue/completed counters, toggle status)
- Uses: `insightStore` (insights, sentimentTrend, actionItems, actionSummary)

### TicketsPage (Ticket Warroom)
- KPI cards: Total tickets, P1 count, Open count, SLA Breaching count
- **Filters:** Search, status dropdown, severity dropdown
- **Views:** Table (WarroomTable with live SLA countdown) vs Constellation (3D star field)
- **TicketDetailDrawer:** Right slide-in panel with full ticket info, AI results, similar tickets
- Actions: Triage, Troubleshoot, Update Status
- Uses: `ticketStore` (tickets, filters, selectedTicket, drawerOpen)

### ReportsPage (Analytics Lab)
- KPI cards with trends
- Cross-filter system: clicking any chart element filters all other charts
- **2x2 Chart Grid:**
  1. HealthHeatmap (D3 calendar) — customer x day matrix
  2. TicketVelocity (Recharts stacked area) — tickets by severity over time
  3. SentimentRiver (D3 stream graph) — positive/neutral/negative flow
  4. AgentThroughput (D3 radial bar) — tasks per agent, lane-colored
- ReportList — table of generated reports + generate modal (type, date range, customer)
- Uses: `reportStore` (analytics data, crossFilter, reports)

### SettingsPage
- **Preferences:** Reduce Motion toggle (persists to localStorage, applies `.reduce-motion` class)
- **System Status:** WebSocket connection indicator, active agents count
- **Account:** User info display, Sign Out button

---

## 19. Zustand Stores

### authStore
**State:** `user, accessToken, refreshToken, isAuthenticated, isLoading, error`

**Actions:**
- `login(email, password)` — POST /auth/login. Stores tokens in localStorage. Connects WebSocket. Falls back to demo mode on network error.
- `initialize()` — On app load: validates stored token or attempts refresh. Continues demo mode if `demo-token` found.
- `logout()` — Clears tokens, disconnects WebSocket, resets state.

### dashboardStore
**State:** `stats, agents, events, quickHealth, isLoading, error`

**Actions:**
- `fetchAll()` — Parallel `Promise.allSettled` of stats, agents, events, quickHealth. Falls back to seed data in demo mode.
- `updateAgentStatus(agentName, status, task)` — WebSocket handler
- `prependEvent(event)` — Adds event to front, keeps last 50
- `updateQuickHealth(customerId, newScore, riskLevel)` — Real-time health update

### customerStore
**State:** `customers, total, isLoading, error, filters (search, risk_level, tier, sort_by, sort_order), viewMode ('grid'|'table'|'solar'), selectedCustomer, healthHistory, customerTickets, customerInsights, actionItems, similarIssues, hoveredCustomer`

**Actions:**
- `fetchCustomers()` — GET /customers with current filters
- `fetchAllDetail(id)` — Parallel fetch of detail, health history, tickets, insights, actions, similar issues
- `handleHealthUpdate(customerId, newScore, riskLevel)` — WebSocket handler
- `clearDetail()` — Resets all detail state

### agentStore
**State:** `agents, isLoading, error, orchestrationFlow, selectedAgent, selectedAgentDetail, agentLogs, logsLoading, brainPanelOpen`

**Key Functions:**
- `toAgentKey(name)` — Normalizes any agent name variant to snake_case key
- `matchesAgent(agent, key)` — Fuzzy matching for agent by name/key

**Actions:**
- `fetchAgents()` — GET /agents
- `triggerAgent(name, customerId, context)` — POST /agents/:name/trigger
- `selectAgent(name)` — Sets selectedAgent, opens brain panel, fetches detail + logs
- `closeBrainPanel()` — Clears selected state
- `updateAgentStatus(agentName, status, task)` — WebSocket handler

### ticketStore
**State:** `tickets, total, isLoading, error, filters, viewMode ('table'|'constellation'), selectedTicket, drawerOpen, detailLoading, similarTickets, similarLoading`

**Actions:**
- `fetchTickets()` — GET /tickets with filters
- `openDrawer(id)` — Fetches detail + similar tickets, opens drawer
- `closeDrawer()` — Clears drawer state
- `updateTicketStatus(id, newStatus)` — Optimistic update + PUT
- `triggerTriage(id)` — POST /tickets/:id/triage
- `triggerTroubleshoot(id)` — POST /tickets/:id/troubleshoot
- `handleTicketTriaged(data)` — WebSocket handler

### insightStore
**State:** `insights, total, isLoading, error, filters, sentimentTrend, trendLoading, actionItems, actionSummary {pending, overdue, completed}, actionsLoading, expandedInsightId`

**Actions:**
- `fetchAll()` — Parallel fetch of insights, sentiment trend, action items
- `toggleActionItem(id, newStatus)` — Optimistic update + PUT
- `syncFathom()` — POST /insights/sync-fathom
- `handleInsightReady(data)` — WebSocket handler

### reportStore
**State:** `kpis, healthTrend, ticketVolume, sentimentStream, agentPerformance, isLoading, error, reports, reportsTotal, reportsLoading, reportTypeFilter, crossFilter`

**Actions:**
- `fetchAnalytics()` — Parallel fetch of analytics + sentiment trend. Transforms data for charts.
- `fetchReports()` — GET /reports with filter
- `generateReport(type, periodStart, periodEnd, customerId)` — POST /reports/generate
- `setCrossFilter(filter)` / `clearCrossFilter()` — Cross-chart filtering

### websocketStore
**State:** `connected, reconnectAttempts, lastMessage`

**Actions:**
- `handleMessage(message)` — Routes incoming WebSocket messages to appropriate stores:
  - `agent_status` -> dashboardStore + agentStore
  - `event_processed` -> dashboardStore
  - `new_alert` -> alertStore
  - `health_update` -> dashboardStore + customerStore
  - `ticket_triaged` -> ticketStore
  - `insight_ready` -> insightStore

### alertStore
**State:** `alerts, total, unreadCount, isLoading`

**Actions:** `addAlert`, `acknowledgeAlert`, `resolveAlert`, `dismissAlert`, `clearUnread`

### toastStore
**State:** `toasts` array

**Actions:** `addToast({type, title, message, duration})` — auto-removes after duration, keeps last 5. `removeToast(id)`.

### settingsStore
**State:** `reducedMotion` (from localStorage)

**Actions:** `toggleReducedMotion()` — toggles + persists + applies `.reduce-motion` CSS class. `initialize()` — restores from localStorage.

---

## 20. Frontend API Services

All services use a shared Axios instance (`api.js`) with:
- **Base URL:** `VITE_API_URL` or `/api`
- **Timeout:** 30,000ms
- **Request interceptor:** Attaches Bearer token from localStorage
- **Response interceptor:** On 401, attempts token refresh. Queues failed requests and retries with new token. Redirects to `/login` if refresh fails.

| Service File | Endpoints |
|-------------|-----------|
| `authApi.js` | login, refresh, me |
| `dashboardApi.js` | getStats, getAgents, getEvents, getQuickHealth |
| `customerApi.js` | list, get, create, update, getHealthHistory, getInsights, getTickets, getActionItems, getSimilarIssues |
| `agentApi.js` | list, get, getLogs, getOrchestrationFlow, trigger |
| `ticketApi.js` | list, get, updateStatus, assign, triage, troubleshoot, getSimilar |
| `insightApi.js` | list, get, syncFathom, getSentimentTrend, getActionItems, updateActionItem |
| `reportApi.js` | list, get, getAnalytics, generate |
| `alertApi.js` | list, acknowledge, resolve, dismiss |
| `healthApi.js` | getScores, getAtRisk, getTrends, runCheck |
| `eventApi.js` | list, create |

### WebSocket Client (`websocket.js`)

- `connectWebSocket(token)` — Creates WebSocket to `VITE_WS_URL?token=...`
  - Heartbeat: ping every 30 seconds
  - Auto-reconnect: exponential backoff, max 10 attempts, max 30s delay
  - Routes messages to `websocketStore.handleMessage()`
- `disconnectWebSocket()` — Closes connection, clears heartbeat, prevents reconnect

---

## 21. Frontend Components

### Layout Components

| Component | Description |
|-----------|-------------|
| **AppLayout** | Main shell: Sidebar + TopBar + CommandPalette + ToastContainer. Page transitions via AnimatePresence. Sidebar collapse persisted to localStorage. |
| **ProtectedRoute** | Auth guard. Redirects to `/login` if unauthenticated. Shows spinner while loading. |
| **Sidebar** | Collapsible left nav with 7 items. Active indicator (spring animation). Live connection dot. Recent events (3 latest). Mobile: hamburger + overlay. |
| **TopBar** | Sticky top bar. Auto-generated breadcrumbs from pathname. Search button (Ctrl+K). Notifications bell (unread count). User avatar dropdown. |
| **CommandPalette** | Cmd+K / Ctrl+K modal. Fuzzy search (fuse.js) across pages, customers, agents, actions. Keyboard navigation (arrows, Enter, Esc). |
| **ToastContainer** | Fixed top-right. Types: success/error/warning/info. Framer Motion slide-in. Auto-dismiss. |

### Shared Components

| Component | Props | Description |
|-----------|-------|-------------|
| **SurfaceCard** | `elevated`, `interactive`, `className`, `onClick` | Frosted glass card. Uses `.card` / `.card-elevated` / `.card-interactive` classes. |
| **StatusIndicator** | `status`, `size`, `showLabel` | Colored dot with optional pulse animation for active/processing states. |
| **HealthRing** | `score`, `size`, `animate`, `showLabel` | SVG circular progress ring (0-100). Color interpolation: red -> yellow -> green. |
| **AnimatedCounter** | `value`, `duration`, `prefix`, `suffix` | Slot-machine style number animation. Uses requestAnimationFrame. Respects reduced motion. |
| **LoadingSkeleton** | `variant`, `count`, `width`, `height` | Shimmer animation placeholder. Variants: card, text, rect. |
| **MetricOrb2D** | `label`, `value`, `color`, `trend` | 2D fallback for floating metric orb. SVG-based. |
| **EventPulseItem** | `event` | Single event card in live feed. Color-coded by event type. |
| **EmptyState** | `icon`, `title`, `description`, `action` | Empty state placeholder component. |
| **SeverityMarker** | `severity` | Colored badge for P1/P2/P3/P4. |
| **SentimentWave** | `sentiment`, `color` | Mini waveform visualization. |

### Dashboard Components

| Component | Description |
|-----------|-------------|
| **FloatingOrbsGrid** | 4 KPI metric cards (MetricOrb2D). Responsive grid. |
| **NeuralSphereWrapper** | Suspense + lazy NeuralSphere. Fallback: NetworkGraphSVG (2D wireframe). |
| **HealthTerrainWrapper** | Suspense + lazy HealthTerrain. Fallback: LoadingSkeleton. |
| **LivePulse** | EKG-style event timeline. Latest events from dashboardStore. Color-coded. |

### Customer Components

| Component | Description |
|-----------|-------------|
| **PremiumGrid** | Responsive grid of customer cards with 3D tilt effect on hover. Shows health ring, name, tier, risk level. |
| **DataTable** | Sortable table. Columns: Name, Health, Risk, Tier, CSM, Renewal. Striped rows. |
| **CustomerHero** | Detail page header. Company name, tier badge, health ring, quick metrics. |
| **HealthStory** | Two-column: left = Recharts trend line, right = health factor breakdown. |
| **QuickIntelPanel** | Hover-triggered side panel. Company info, recent activity, metrics. |
| **IntelPanels** | Three-column layout: Tickets column, Insights column, Similar Issues (RAG) column. |

### Agent Components

| Component | Description |
|-----------|-------------|
| **NeuralNetwork** | D3 force-directed graph. Agent nodes connected by edges. Lane-colored. Click to select. |
| **AgentBrainPanel** | Right slide-out drawer. Agent name, lane, status, config, reasoning logs. |
| **ReasoningLog** | Terminal-style log viewer. Shows agent reasoning trace with timestamps. |

### Insight Components

| Component | Description |
|-----------|-------------|
| **SentimentSpectrum** | Full-width Recharts area chart. Sentiment trend over time. Green/gray/red areas. |
| **InsightCard** | Expandable card. Shows sentiment, call duration, customer, summary, action items. |
| **ActionTracker** | Sticky side panel. Pending/overdue/completed counters. Toggle action item status. |

### Ticket Components

| Component | Description |
|-----------|-------------|
| **WarroomTable** | Sortable table with live SLA countdown. Columns: ID, Summary, Severity, Status, Customer, SLA, Created. |
| **ConstellationWrapper** | Suspense + lazy TicketConstellation (3D). Fallback: severity-colored ticket grid. |
| **TicketDetailDrawer** | Right slide-in drawer. Full ticket info, AI results (triage, troubleshoot), similar tickets. Action buttons. |

### Report Components

| Component | Description |
|-----------|-------------|
| **HealthHeatmap** | D3 calendar heatmap. Customer x day matrix. Color = health score. Click to cross-filter. |
| **TicketVelocity** | Recharts stacked area chart. Ticket volume by severity over weeks. |
| **SentimentRiver** | D3 stream graph. Sentiment distribution flow over time. |
| **AgentThroughput** | D3 radial bar chart. Tasks per agent, positioned around circle, lane-colored. |
| **ReportList** | Report history table + generate modal. Select type, date range, optional customer. |

---

## 22. 3D Components

All 3D components live in `frontend/src/three/`. They are lazy-loaded via `React.lazy` + `Suspense` and code-split into a separate `three` chunk. Each has a 2D fallback.

| Component | Technology | Description |
|-----------|-----------|-------------|
| **NeuralSphere** | Three.js + R3F + Drei | Icosahedron wireframe globe with 10 agent nodes as emissive spheres. OrbitControls for interaction. Agent nodes colored by lane. |
| **HealthTerrain** | Three.js + R3F | 3D topographic heightmap generated from customer health scores. Color interpolation (red -> yellow -> green). Camera pans on hover. |
| **DataFlowRivers** | Three.js + R3F | Particle stream visualization showing data flow between agents. Glowing trails with animated paths. |
| **TicketConstellation** | Three.js + R3F | 3D star field. Tickets as star nodes. Size by priority, color by severity. Click to select. |
| **HealthRing3D** | Three.js + R3F | Rotating torus ring. Color interpolated by health score. Emissive glow. |
| **AgentIcon3D** | Three.js + R3F | Unique 3D glyph per agent lane. Lane-colored material. Emissive glow when active. |

### Vite Code Splitting

```javascript
// vite.config.js manualChunks
'three': [three, @react-three/fiber, @react-three/drei]
'gsap':  [gsap]
```

### Progressive Enhancement Pattern

```jsx
const NeuralSphereWrapper = () => (
  <Suspense fallback={<NetworkGraphSVG />}>  {/* 2D fallback */}
    <Canvas camera={{ position: [0, 2, 5], fov: 60 }}>
      <NeuralSphere />
    </Canvas>
  </Suspense>
);
```

---

## 23. Seed Data

### Frontend Seed Data (`frontend/src/data/`)

Used for **demo mode** (when backend is unreachable). Stores use this data as fallback.

| File | Exports |
|------|---------|
| `dashboard.js` | `seedDashboardStats`, `seedAgents` (10), `seedEvents` (20), `seedQuickHealth` (10 customers) |
| `customers.js` | `seedCustomers`, `seedCustomerDetail(id)` |
| `tickets.js` | `seedTickets` with severity, status, SLA |
| `insights.js` | `seedInsights`, `seedSentimentTrend`, `seedActionItems` |
| `agents.js` | `seedAgentList`, `seedAgentLogs`, `seedOrchestrationFlow` |
| `analytics.js` | `seedAnalyticsKpis`, `seedTicketVolume`, `seedHealthTrend`, `seedAgentPerformance`, `seedSentimentStream`, `seedReports` |
| `healthHistory.js` | `seedHealthHistory[customerId]` — 90 days of daily scores |

### Backend Seed Script (`backend/app/utils/seed.py`)

Run via: `python -m app.utils.seed`

Creates:
- 5 users (2 admin, 2 cs_engineer, 1 cs_manager)
- 10 customers (mix of enterprise/mid-market/SMB)
- ~300 health scores (30 days x 10 customers)
- 50 tickets (various severities and statuses)
- 100 call insights (mixed sentiments)
- 200 agent logs
- 150 events
- 15 alerts
- 30 action items
- 8 reports

### Utilities & Hooks

**`utils/formatters.js`** — Number/date formatting, color maps for status/severity/lane/risk/event types
**`utils/chartHelpers.js`** — Chart color constants, `healthColorScale` (D3 interpolator), `getCrossFilterOpacity`, agent lane mapping, debounce
**`utils/cn.js`** — `cn(...classes)` using clsx + tailwind-merge
**`hooks/useScrollReveal.js`** — IntersectionObserver hook for scroll-triggered animations

---

## 24. Environment Variables

### Development (.env)

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql+asyncpg://USER:PASS@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
SYNC_DATABASE_URL=postgresql://USER:PASS@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require

# Redis (optional — leave empty for sync task execution)
REDIS_URL=

# Auth
JWT_SECRET_KEY=<generated-64-char-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# ChromaDB
CHROMADB_PATH=./chromadb_data
CHROMADB_MODE=persistent

# External (Phase 2 — leave empty)
JIRA_API_URL=https://hivepro.atlassian.net
JIRA_API_TOKEN=
SLACK_BOT_TOKEN=
FATHOM_EMAIL=
FATHOM_PASSWORD=

# Frontend
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws
```

### Production

```bash
# Same structure but with:
REDIS_URL=rediss://default:PASS@xxx.upstash.io:6379    # Upstash Redis (TLS)
CHROMADB_MODE=ephemeral                                  # In-memory on Render
FRONTEND_URL=https://your-app.vercel.app                 # CORS restriction
VITE_API_URL=https://cs-control-plane-api.onrender.com/api
VITE_WS_URL=wss://cs-control-plane-api.onrender.com/api/ws
```

### Variable Reference

| Variable | Required | Default | Used By |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | — | FastAPI async engine (asyncpg) |
| `SYNC_DATABASE_URL` | Yes | — | Alembic, Celery, seed script (psycopg2) |
| `REDIS_URL` | No | `""` (sync fallback) | Celery broker/backend |
| `JWT_SECRET_KEY` | Yes | placeholder | Token signing/verification |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API calls |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-5-20250929` | Model selection |
| `CHROMADB_PATH` | No | `./chromadb_data` | Persistent storage path |
| `CHROMADB_MODE` | No | `persistent` | `persistent` or `ephemeral` |
| `FRONTEND_URL` | No | `""` (open CORS) | CORS origin restriction |
| `JIRA_API_URL` | No | `""` | Phase 2 Jira integration |
| `JIRA_API_TOKEN` | No | `""` | Phase 2 Jira auth |
| `SLACK_BOT_TOKEN` | No | `""` | Phase 2 Slack notifications |
| `FATHOM_EMAIL` | No | `""` | Phase 2 Fathom sync |
| `FATHOM_PASSWORD` | No | `""` | Phase 2 Fathom auth |
| `VITE_API_URL` | No | `/api` | Frontend API base URL |
| `VITE_WS_URL` | No | `ws://127.0.0.1:8000/api/ws` | Frontend WebSocket URL |

---

## 25. Deployment Configuration

### Render (Backend)

**render.yaml:**
- **Web Service:** `cs-control-plane-api`
  - Runtime: Python 3.11.7 (specified in `runtime.txt`)
  - Build: `pip install -r requirements.txt`
  - Start: `alembic upgrade head && gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
  - Health check: `GET /api/health`
  - Region: Oregon, Plan: Starter

- **Worker Service:** `cs-control-plane-worker`
  - Start: `celery -A app.tasks.celery_app:celery_app worker --loglevel=info --concurrency=2`
  - Same env vars as web service

### Vercel (Frontend)

**vercel.json:**
- Build: `npm run build`
- Output: `dist/`
- Framework: Vite
- SPA rewrite: all routes -> `/index.html`
- Asset caching: `Cache-Control: public, max-age=31536000, immutable`

### Neon (Database)
- PostgreSQL 16, cloud-hosted
- Connection pooler (PgBouncer) endpoint
- SSL required (`sslmode=require`)
- Idle connection handling: `pool_pre_ping=True` in SQLAlchemy

### Upstash (Redis)
- Optional, free tier
- TLS connection (`rediss://` with double-s)
- Used as Celery broker/backend when available

---

## 26. Development Phases

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 1 | Foundation | Done | Scaffolding, docker-compose, requirements, package.json |
| 2 | Auth + Users | Done | JWT auth, login/refresh/me, middleware, RBAC |
| 3 | Customer CRUD + Health | Done | Customer endpoints, health scores, detail views |
| 4 | Core Services | Done | Claude wrapper, ChromaDB + RAG, mock services |
| 5 | Agent Framework | Done | BaseAgent, Orchestrator, Memory Agent, Celery setup |
| 6 | Event System + WebSocket | Done | Event model, routing, WebSocket manager |
| 7 | Remaining Agents | Done | All 10 agents implemented (Triage, Troubleshoot, Escalation, Health, Call Intel, QBR, SOW, Deployment) |
| 8 | Frontend Shell | Done | Design system, Tailwind, Sidebar, TopBar, CommandPalette |
| 9 | Login + Dashboard (2D) | Done | Login page, dashboard KPIs, live pulse, health grid |
| 10 | Dashboard 3D | Done | NeuralSphere, FloatingOrbs, DataFlowRivers, HealthTerrain |
| 11 | Customer Observatory + Detail | Done | PremiumGrid, DataTable, CustomerHero, HealthStory, IntelPanels |
| 12 | Agent Nexus | Done | NeuralNetwork (D3), AgentBrainPanel, ReasoningLog |
| 13 | Signal Intelligence + Warroom | Done | SentimentSpectrum, InsightCard, WarroomTable, TicketDetailDrawer |
| 14 | Analytics Lab | Done | HealthHeatmap, TicketVelocity, SentimentRiver, AgentThroughput, cross-filtering |
| 15 | Seed Data + Polish | Partial | Seed script done. Animations, empty states, toasts done. Settings page done. |
| 16 | E2E Testing + Performance | Pending | Playwright tests, 3D perf audit, bundle audit, Lighthouse |

---

## 27. Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (or Neon cloud)
- Redis (optional — sync fallback exists)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Configure .env (copy from .env.example, fill in DATABASE_URL + ANTHROPIC_API_KEY)
alembic upgrade head            # Create all 10 tables
python -m app.utils.seed        # Seed demo data
uvicorn app.main:app --reload   # Start on http://localhost:8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev                     # Start on http://localhost:5173
```

### Test Accounts (After Seed)

| Email | Password | Role |
|-------|----------|------|
| ayushmaan@hivepro.com | password123 | admin |
| ariza@hivepro.com | password123 | admin |
| vignesh@hivepro.com | password123 | cs_engineer |
| chaitanya@hivepro.com | password123 | cs_engineer |
| kazi@hivepro.com | password123 | cs_manager |

### Demo Mode
If the backend is unreachable, the frontend falls back to **demo mode**: accepts any credentials, uses seed data from `frontend/src/data/`, and runs fully offline.

---

## 28. Key Design Decisions

1. **Spatial 3D over flat dashboard** — Immersive command center with neural sphere, health terrain, particle rivers. Progressive enhancement ensures 2D always works.
2. **Event-driven architecture** — Central event queue with Orchestrator routing. Agents never call each other. Clear separation of concerns.
3. **WebSocket real-time** — No polling anywhere. All updates broadcast instantly.
4. **Async AI calls** — Celery + Redis decouples API from LLM latency. Sync fallback when Redis unavailable.
5. **Customer Memory as SSOT** — All agents read/write to single customer repository. No agent maintains private state.
6. **RAG for cross-customer intelligence** — ChromaDB embeddings find similar past issues across all customers.
7. **Three surface levels** — Spatial depth hierarchy (near/mid/far) replaces traditional borders/shadows.
8. **Sidebar navigation** (adapted from spec) — Originally designed as Orbital Nav arc; implemented as collapsible sidebar with CommandPalette for power users.
9. **Demo mode** — Frontend works fully offline with seed data when backend is down.
10. **Seed data system** — Single CLI command creates complete demo environment for instant walkthrough.

---

## 29. Known Gaps & Limitations

### Agents
- **SOW & Prerequisite Agent** — Code is complete but has **no persistence path**. Output from Claude is generated but discarded after the run.
- **Deployment Intelligence Agent** — Same issue: output is discarded, no save logic exists.
- **Generic trigger endpoint** — Most agents require manually constructed payloads via `POST /agents/:name/trigger`. Only Ticket Triage and Troubleshooter have dedicated endpoints that auto-populate data from the DB.

### External Integrations (Phase 2)
- **Jira** — No live webhook integration. Tickets are created manually or via seed data.
- **Fathom** — No live recording sync. Call insights are seeded or manually created.
- **Slack** — No bot integration. Alerts have a `slack_notified` flag but nothing sends to Slack.

### Infrastructure
- **Redis** — Optional. Without it, all Celery tasks run synchronously (no background processing, no task queueing).
- **ChromaDB ephemeral mode** — In production (Render), vector embeddings are lost on restart. Need a persistent vector DB solution for production.

### Testing
- **E2E tests** — Playwright config exists but test suite is not yet written (Phase 16).
- **Unit tests** — Backend test directory exists but coverage is minimal.

### Frontend
- **Solar System View** — Referenced in the spec but may not be fully implemented yet.
- **Ticket Constellation 3D** — Exists but may need polish.
- **Accessibility** — Basic support (focus rings, reduced motion, semantic HTML) but no comprehensive audit.

---

*This document was generated on March 2, 2026 by analyzing every file in the HivePro CS Control Plane codebase.*
