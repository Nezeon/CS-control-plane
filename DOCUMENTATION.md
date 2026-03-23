# HivePro CS Control Plane — Complete Project Documentation

> **Codename:** Mission Control
> **Author:** Ayushmaan Singh Naruka (AI Hub Team, HivePro)
> **Design Tier:** Premium enterprise spatial 3D command center
> **Last Updated:** March 23, 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Solution Summary](#3-solution-summary)
4. [The 14 AI Agents](#4-the-14-ai-agents)
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
23. [Initial Data](#23-initial-data)
24. [Environment Variables](#24-environment-variables)
25. [Deployment Configuration](#25-deployment-configuration)
26. [Development Phases](#26-development-phases)
27. [Quick Start](#27-quick-start)
28. [Key Design Decisions](#28-key-design-decisions)
29. [Known Gaps & Limitations](#29-known-gaps--limitations)

---

## 1. Project Overview

The CS Control Plane is an AI-powered platform that orchestrates **14 agents across a 4-tier hierarchy** to automate Customer Success workflows at HivePro. It replaces manual processes like call analysis, ticket triage, health monitoring, and report generation with an always-on virtual CS workforce.

The system follows a **Slack-first delivery model**: agents push their outputs as interactive cards to 9 dedicated Slack channels. CS team members review, approve, or edit directly in Slack. A dashboard provides drill-down views when deeper context is needed. The backend is a FastAPI service with PostgreSQL (Neon cloud), ChromaDB (vector search), and Celery (async task queue). All AI calls go through Claude (Anthropic API).

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

## 4. The 14 AI Agents

The Orchestrator routes events directly to specialist agents by event type and lane. Specialists never talk directly to each other.

### Tier 1 — Supervisor

| Agent | Identity | File | Role |
|-------|----------|------|------|
| **CS Orchestrator** | Naveen Kapoor | `orchestrator.py` | Classifies events, routes to correct lane. Never analyzes — pure routing. |

### Specialists

| Agent | Identity | Lane | File | Trigger Event | Primary Output |
|-------|----------|------|------|---------------|----------------|
| **Ticket Triage** | Kai Nakamura | Support | `triage_agent.py` | `jira_ticket_created`, `jira_ticket_updated` | Category, severity, root cause hypothesis, action |
| **Troubleshooter** | Leo Petrov | Support | `troubleshoot_agent.py` | `support_bundle_uploaded` | Root cause analysis, resolution steps, communication draft |
| **Escalation Writer** | Maya Santiago | Support | `escalation_agent.py` | `ticket_escalated` | Engineering escalation package with repro steps |
| **Health Monitor** | Dr. Aisha Okafor | Value | `health_monitor.py` | `daily_health_check`, `manual_health_check` | Health score (0-100), risk level, factors, flags |
| **QBR / Value Narrative** | Sofia Marquez | Value | `qbr_agent.py` | `renewal_approaching` | QBR report content, value narrative |
| **SOW & Prerequisite** | Ethan Brooks | Delivery | `sow_agent.py` | `new_enterprise_customer` | Pre-deployment checklist, SOW docs |
| **Deployment Intelligence** | Zara Kim | Delivery | `deployment_intel_agent.py` | `deployment_started` | Known issues, config guidance |

### Tier 4 — Foundation

| Agent | Identity | File | Role |
|-------|----------|------|------|
| **Customer Memory** | Atlas | `memory_agent.py` + `memory/` | Per-customer knowledge store. 3-tier memory: Working + Episodic + Semantic. Serves ALL tiers. |

### Agent Lanes & Colors
- **Control** (Teal `#00F5D4`): T1 Orchestrator
- **Support** (Amber `#FBBF24`): T2 Rachel → T3 Kai, Leo, Maya
- **Value** (Emerald `#34D399`): T2 Damon → T3 Aisha, Jordan, Sofia, Riley
- **Delivery** (Cyan `#22D3EE`): T2 Priya → T3 Ethan, Zara
- **Foundation** (Slate): T4 Atlas (Customer Memory)

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
| PostgreSQL | 16 | Primary database (Neon cloud) |
| SQLAlchemy | 2.0 | ORM (async via asyncpg, sync via psycopg2) |
| Alembic | 1.13+ | Database migrations (6 migration files) |
| ChromaDB | 0.4+ | Vector database (6 collections for RAG + agent memory) |
| Celery | 5.3+ | Async task queue (eager mode — no Redis required locally) |
| Redis | 7.x | Celery broker/backend (optional, has sync fallback) |
| python-jose | 3.3+ | JWT authentication |
| passlib[bcrypt] | 1.7+ | Password hashing |
| Anthropic SDK | latest | Claude API client (Sonnet 4.5 + Haiku 4.5) |
| httpx | 0.26+ | Async HTTP client (Jira, Fathom, external APIs) |
| slack-sdk | 3.27+ | Slack WebClient + Block Kit formatting |
| APScheduler | 3.10+ | Cron-style scheduling (Jira/Fathom sync) |
| PyYAML | 6.0+ | YAML-driven agent configuration |
| pydantic-settings | 2.1+ | Settings from .env (40+ env vars) |
| Playwright | 1.40+ | Browser automation (E2E testing) |

### Alternative UI (Streamlit)

| Technology | Purpose |
|------------|---------|
| Streamlit | 6-page operational UI (Ask, Dashboard, Customers, Agents, Tickets, Executive Summary) |

### Deployment

| Platform | Purpose |
|----------|---------|
| Render | Backend hosting (FastAPI + optional Celery worker) |
| Vercel | Frontend hosting (React Vite static) |
| Neon | Cloud PostgreSQL 16 |
| Upstash | Cloud Redis (optional — not required for basic usage) |

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

### Rule 8: Hierarchical Delegation
The Orchestrator routes events directly to the correct specialist by event type. Specialists never delegate to each other directly. The Foundation layer (Customer Memory) serves all agents.

### Rule 9: YAML-Driven Configuration
Agent identities, personalities, traits, tools, pipeline stages, org structure, and workflows are defined in YAML config files (`backend/config/`). **Never** hardcode agent behavior in Python. The code reads YAML at startup and constructs agents dynamically. To change an agent's behavior, edit YAML, not code.

### Rule 10: Message Board Communication
Agents communicate through typed messages on the Message Board (`agent_messages` table). Five message types: `task_assignment` (down), `deliverable` (up), `request` (sideways), `escalation` (up, urgent), `feedback` (down). Messages support threading via `thread_id` and `parent_id`. Every message links to its originating event.

### Rule 11: 3-Tier Memory System
Every agent accesses three memory tiers: **Working** (in-process scratchpad, cleared per run), **Episodic** (ChromaDB `episodic_memory` collection, per-agent diary with tri-factor retrieval), **Semantic** (ChromaDB `shared_knowledge` collection, lane-scoped knowledge pools). Agents read episodic + semantic during `retrieve` stage, write to episodic during `reflect` stage.

### Rule 12: Pipeline Execution
Every agent runs a multi-round pipeline defined in `pipeline.yaml`. Stages: `perceive` → `retrieve` → `think` → `act` → `reflect` → `quality_gate` → `finalize`. Each stage is logged to `agent_execution_rounds` with tools called, tokens used, confidence, and duration. The pipeline engine handles quality gate failures (retry from a specific stage). Every stage broadcasts progress via WebSocket.

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
├── CLAUDE.md                          # AI development context (source of truth)
├── DOCUMENTATION.md                   # THIS FILE
├── README.md                          # Quick start guide
├── DEPLOYMENT.md                      # Deployment instructions
├── .env.example                       # Environment template
├── render.yaml                        # Render deployment config
│
├── docs/
│   ├── ARCHITECTURE.md                # System design, agent hierarchy
│   ├── PRD.md                         # Product Requirements Document
│   ├── WIREFRAMES.md                  # UI/UX specifications
│   ├── API_CONTRACT.md                # API endpoint contracts
│   └── DATABASE_SCHEMA.md             # Schema design document
│
├── backend/
│   ├── requirements.txt               # 47 Python packages
│   ├── alembic.ini                    # Migration config
│   ├── Procfile                       # Render start command
│   ├── runtime.txt                    # Python 3.11.7
│   ├── chromadb_data/                 # Persistent vector DB (6 collections)
│   ├── alembic/
│   │   └── versions/                  # 6 migration files
│   │
│   ├── config/                        # YAML-driven agent configuration
│   │   ├── org_structure.yaml         # 4-tier hierarchy, lanes, reporting
│   │   ├── agent_profiles.yaml        # 14 agent definitions, traits, tools
│   │   ├── pipeline.yaml              # Pipeline stage definitions per tier
│   │   └── workflows.yaml             # Event → agent routing
│   │
│   └── app/
│       ├── main.py                    # FastAPI entry + APScheduler setup
│       ├── config.py                  # Settings from .env (40+ env vars)
│       ├── database.py                # Async + Sync PostgreSQL engines
│       ├── chromadb_client.py         # ChromaDB client (6 collections)
│       ├── websocket_manager.py       # WebSocket connection manager
│       ├── demo_data.py               # Demo scenario data
│       ├── demo_runner.py             # CLI demo tool
│       │
│       ├── models/                    # SQLAlchemy models (17 tables)
│       ├── schemas/                   # Pydantic request/response schemas (17 files)
│       ├── routers/                   # API endpoint handlers (23 routers)
│       │
│       ├── agents/                    # 14 AI agent implementations
│       │   ├── base_agent.py          # Pipeline execution base class
│       │   ├── pipeline_engine.py     # Multi-round pipeline runner
│       │   ├── reflection_engine.py   # Reflection + quality gate
│       │   ├── agent_factory.py       # Agent registration
│       │   ├── profile_loader.py      # YAML profile loading
│       │   ├── demo_logger.py         # Rich terminal logging
│       │   ├── orchestrator.py        # T1: Naveen (CS Orchestrator)
│       │   ├── triage_agent.py        # T3: Kai (Ticket Triage)
│       │   ├── troubleshoot_agent.py  # T3: Leo (Troubleshooter)
│       │   ├── escalation_agent.py    # T3: Maya (Escalation Writer)
│       │   ├── health_monitor.py      # T3: Aisha (Health Monitor)
│       │   ├── qbr_agent.py           # T3: Sofia (QBR / Value Narrative)
│       │   ├── sow_agent.py           # T3: Ethan (SOW & Prerequisite)
│       │   ├── deployment_intel_agent.py # T3: Zara (Deployment Intelligence)
│       │   ├── memory_agent.py        # T4: Atlas (Customer Memory)
│       │   ├── memory/                # 3-tier memory system
│       │   │   ├── memory_manager.py  # Memory lifecycle
│       │   │   ├── working_memory.py  # In-process scratchpad
│       │   │   ├── episodic_memory.py # ChromaDB per-agent diary
│       │   │   └── semantic_memory.py # ChromaDB lane-scoped pools
│       │   └── traits/                # 13 pluggable trait behaviors
│       │       ├── confidence_scoring.py
│       │       ├── customer_sentiment.py
│       │       ├── deadline_tracking.py
│       │       ├── delegation.py
│       │       ├── pattern_recognition.py
│       │       ├── quality_evaluation.py
│       │       ├── risk_assessment.py
│       │       ├── root_cause_analysis.py
│       │       ├── sla_awareness.py
│       │       ├── strategic_oversight.py
│       │       └── trend_analysis.py
│       │
│       ├── services/                  # 17 business logic modules
│       │   ├── claude_service.py      # Claude API wrapper (Sonnet + Haiku)
│       │   ├── chat_service.py        # Unified chat orchestration
│       │   ├── chat_fast_path.py      # Haiku fast responses
│       │   ├── rag_service.py         # RAG/semantic search
│       │   ├── jira_service.py        # Jira Cloud client (httpx)
│       │   ├── fathom_service.py      # Fathom API client
│       │   ├── meeting_knowledge_service.py # Meeting knowledge RAG
│       │   ├── slack_service.py       # Slack Bot client
│       │   ├── slack_chat_handler.py  # Bidirectional Slack chat
│       │   ├── slack_formatter.py     # Markdown → Block Kit
│       │   ├── pipeline_service.py    # Pipeline execution
│       │   ├── event_service.py       # Event routing + draft creation
│       │   ├── message_service.py     # Inter-agent messages
│       │   ├── draft_service.py       # Draft create/approve/dismiss
│       │   ├── alert_rules_engine.py  # 4 alert rules
│       │   └── trend_service.py       # Analytics queries
│       │
│       ├── tasks/                     # Celery async tasks
│       │   ├── celery_app.py          # Celery config (eager mode fallback)
│       │   ├── agent_tasks.py         # 20+ async agent tasks
│       │   └── jira_sync.py           # Jira bulk + incremental sync
│       │
│       ├── middleware/
│       │   └── auth.py                # JWT authentication middleware
│       └── utils/
│           ├── security.py            # Password hashing, token generation
│           └── ensure_admin.py        # Auto-creates admin user on startup
│
├── frontend/                          # React spatial dashboard
│   ├── package.json
│   ├── vite.config.js                 # Dev proxy, chunk splitting
│   ├── tailwind.config.js             # Custom colors, fonts, animations
│   ├── vercel.json                    # Vercel deployment config
│   └── src/
│       ├── main.jsx / App.jsx / index.css
│       ├── pages/                     # DashboardPage, CustomerDetailPage, PipelineAnalyticsPage
│       ├── stores/                    # Zustand state (11 stores)
│       ├── services/                  # Axios API clients + WebSocket
│       ├── components/
│       │   ├── layout/                # AppLayout, shared layout
│       │   └── shared/                # GlassCard, HealthRing, KpiCard, etc.
│       └── utils/                     # formatters
│
├── streamlit_app/                     # Alternative UI (6 pages, fully functional)
│   ├── app.py                         # Entry (login + home)
│   ├── pages/
│   │   ├── 1_Ask.py                   # Chat interface
│   │   ├── 2_Dashboard.py             # Metrics dashboard
│   │   ├── 3_Customers.py             # Customer list + detail
│   │   ├── 4_Agents.py                # Agent status + profiles
│   │   ├── 5_Tickets.py               # Ticket board
│   │   └── 6_Executive_Summary.py     # Executive summary + charts
│   └── utils/                         # API client (JWT auth, polling) + CSS
│
├── prompt-templates/                  # Reusable prompt templates
└── e2e/                               # Playwright E2E tests
```

---

## 9. Database Schema

PostgreSQL 16 with 17 tables. All primary keys are UUIDs. Timestamps use `TIMESTAMPTZ` with server defaults. JSONB columns store flexible structured data.

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
| jira_project_key | VARCHAR(20) | Maps Jira projects to customers (e.g. "CS", "ACME") |
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

### 9.11 chat_conversations

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK -> users(id) NOT NULL |
| title | VARCHAR(500) | nullable |
| customer_id | UUID | FK -> customers(id), nullable |
| status | VARCHAR(20) | DEFAULT `'active'` |
| metadata | JSONB | DEFAULT `'{}'` — stores `slack_channel`, `slack_thread_ts` for Slack integration |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), auto-update |

**Indexes:** (user_id, created_at DESC), customer_id, status, metadata slack_channel (partial)
**Relationships:** user, customer, messages

### 9.12 chat_messages

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| conversation_id | UUID | FK -> chat_conversations(id) NOT NULL |
| role | VARCHAR(20) | NOT NULL (user, assistant, system) |
| content | TEXT | NOT NULL |
| event_id | UUID | FK -> events(id), nullable |
| agents_involved | JSONB | DEFAULT `'[]'` |
| pipeline_status | VARCHAR(20) | nullable (processing, completed, failed) |
| execution_metadata | JSONB | DEFAULT `'{}'` |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** (conversation_id, created_at ASC), event_id

### 9.13 agent_execution_rounds

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| execution_id | UUID | NOT NULL — groups stages of a single agent run |
| event_id | UUID | FK -> events(id), nullable |
| agent_id | VARCHAR(100) | NOT NULL |
| agent_name | VARCHAR(255) | nullable |
| tier | INTEGER | CHECK (1-4) NOT NULL |
| stage_number | INTEGER | NOT NULL |
| stage_name | VARCHAR(100) | NOT NULL (perceive, retrieve, think, act, reflect, quality_gate, finalize) |
| lane | VARCHAR(50) | nullable |
| stage_type | VARCHAR(50) | NOT NULL |
| input_summary | TEXT | nullable |
| output_summary | TEXT | nullable |
| tools_called | JSONB | DEFAULT `'[]'` |
| tokens_used | INTEGER | nullable |
| duration_ms | INTEGER | nullable |
| confidence | FLOAT | nullable |
| status | VARCHAR(20) | DEFAULT `'running'` (running, completed, failed) |
| error_message | TEXT | nullable |
| metadata | JSONB | DEFAULT `'{}'` |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** execution_id, (agent_id, created_at DESC), event_id, status, tier, lane

### 9.14 agent_messages

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| thread_id | UUID | nullable — groups related messages into a thread |
| parent_id | UUID | FK -> agent_messages(id), nullable |
| from_agent | VARCHAR(100) | NOT NULL |
| from_name | VARCHAR(255) | nullable |
| to_agent | VARCHAR(100) | NOT NULL |
| to_name | VARCHAR(255) | nullable |
| message_type | VARCHAR(50) | NOT NULL (task_assignment, deliverable, request, escalation, feedback) |
| direction | VARCHAR(20) | NOT NULL (down, up, sideways) |
| content | TEXT | NOT NULL |
| priority | INTEGER | CHECK (1-10) DEFAULT 5 |
| event_id | UUID | FK -> events(id), nullable |
| execution_id | UUID | nullable |
| customer_id | UUID | FK -> customers(id), nullable |
| status | VARCHAR(20) | DEFAULT `'pending'` |
| metadata | JSONB | DEFAULT `'{}'` |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** thread_id, (from_agent, created_at DESC), (to_agent, created_at DESC), message_type, event_id, execution_id, status

### 9.15 agent_drafts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| agent_id | VARCHAR(50) | NOT NULL |
| event_id | UUID | FK -> events(id) ON DELETE SET NULL, nullable |
| customer_id | UUID | FK -> customers(id) ON DELETE SET NULL, nullable |
| draft_type | VARCHAR(50) | NOT NULL (triage, call_intel, escalation, health_alert, etc.) |
| draft_content | JSONB | NOT NULL — full agent output |
| status | VARCHAR(20) | DEFAULT `'pending'` (pending, approved, edited, dismissed) |
| slack_message_ts | VARCHAR(50) | nullable — Slack ts for updating message |
| slack_channel | VARCHAR(100) | nullable |
| approved_by | VARCHAR(100) | nullable |
| approved_at | TIMESTAMPTZ | nullable |
| edit_diff | JSONB | nullable — what the human changed |
| confidence | FLOAT | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** status, agent_id, customer_id, created_at

### 9.16 audit_log

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| timestamp | TIMESTAMPTZ | DEFAULT NOW() |
| agent | VARCHAR(50) | NOT NULL |
| event_id | UUID | nullable |
| customer_id | UUID | nullable |
| action | VARCHAR(100) | NOT NULL (classify_ticket, analyze_call, etc.) |
| input_summary | TEXT | nullable |
| output_summary | TEXT | nullable |
| confidence | FLOAT | nullable |
| human_action | VARCHAR(20) | nullable (approved, edited, dismissed) |
| human_edit_diff | JSONB | nullable |
| dashboard_url | VARCHAR(500) | nullable |

**Indexes:** agent, timestamp, customer_id, human_action

---

## 10. ChromaDB Vector Store

ChromaDB provides semantic similarity search (RAG) and agent memory across **6 collections**. Uses default sentence-transformers for embeddings. L2 (Euclidean) distance metric. Similarity is calculated as `max(0.0, 1.0 - distance)`.

**Modes:**
- `persistent` (local dev) — saves to `./chromadb_data` on disk
- `ephemeral` (production/Render) — in-memory, lost on restart (backfill from PostgreSQL runs on startup)

### Collection: ticket_embeddings
- **Purpose:** Find similar past tickets for triage and troubleshooting
- **Document:** Ticket summary + description + resolution (if resolved)
- **Metadata:** `{jira_id, customer_id, status, severity}`
- **Used by:** Triage Agent (top 5 similar), Troubleshooter Agent (top 5 resolved), ticket similar endpoint
- **Backfill:** Re-embedded from PostgreSQL `tickets` table on startup

### Collection: call_insight_embeddings
- **Purpose:** Find similar call discussions, surface patterns
- **Document:** Call summary + key topics
- **Metadata:** `{customer_id, sentiment, recording_id}`
- **Used by:** Call Intelligence Agent, insights API
- **Backfill:** Re-embedded from PostgreSQL `call_insights` table on startup

### Collection: problem_embeddings
- **Purpose:** Cross-customer pattern matching for known problems
- **Document:** Problem description + root cause + resolution steps
- **Metadata:** `{customer_id, customer_name, ticket_id, resolved_in_days}`
- **Used by:** Troubleshooter Agent, knowledge base queries

### Collection: meeting_knowledge
- **Purpose:** Agentic RAG retrieval for customer meeting context
- **Document:** 155+ real customer meeting chunks (5 categories, 4 section types)
- **Metadata:** Category, section type, customer context
- **Used by:** Fathom Agent, Chat fast path
- **Backfill:** Re-populated from PostgreSQL `call_insights` via `meeting_knowledge_service` on startup

### Collection: episodic_memory
- **Purpose:** Per-agent execution diary for experience recall
- **Document:** Agent execution summaries, decisions, outcomes
- **Metadata:** `{agent_id, event_type, customer_id, timestamp}`
- **Used by:** All agents during `retrieve` stage (tri-factor retrieval: recency + relevance + importance)
- **Written by:** All agents during `reflect` stage

### Collection: shared_knowledge
- **Purpose:** Lane-scoped knowledge pool for collective intelligence
- **Document:** Published knowledge from agent executions
- **Metadata:** `{lane, agent_id, knowledge_type}`
- **Used by:** All agents during `retrieve` stage (filtered by lane)
- **Written by:** Agents that opt to `publish_knowledge` after execution

### Initial Data

The admin user (`ayushmaan@hivepro.com`) is auto-created on startup by `ensure_admin.py`. All other data comes from live integrations (Jira sync, Fathom sync, HubSpot webhooks). On startup, ChromaDB collections are backfilled from PostgreSQL data.

---

## 11. Backend API Endpoints

All endpoints are prefixed with `/api`. Authentication uses Bearer JWT tokens (except login, health check, and webhooks). There are **23 routers** total.

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

### 11.12 Chat (`/api/chat`)

| Method | Path | Input | Output | Description |
|--------|------|-------|--------|-------------|
| POST | `/send` | `{message}` | `{conversation_id, message_id}` | Send chat message (fast path via Haiku, fallback to full pipeline) |
| GET | `/conversations` | Bearer token | `[{id, title, status, created_at}]` | List user's conversations |
| GET | `/conversations/:id` | UUID | `{id, messages, pipeline_status}` | Conversation detail (used for polling) |

### 11.13 Jira (`/api/jira`)

| Method | Path | Output | Description |
|--------|------|--------|-------------|
| GET | `/status` | `{configured, url, project, last_sync}` | Jira connection status |
| POST | `/sync` | `{task_id, stats}` | Trigger manual Jira sync (bulk) |
| POST | `/sync/:key` | `{task_id, stats}` | Sync a single Jira issue by key |

### 11.14 Fathom (`/api/fathom`)

| Method | Path | Input | Output | Description |
|--------|------|-------|--------|-------------|
| POST | `/sync` | `?days=7` | `{imported, skipped, errors}` | Trigger Fathom meeting sync |

### 11.15 Executive (`/api/executive`)

| Method | Path | Output | Description |
|--------|------|--------|-------------|
| GET | `/summary` | Executive dashboard data | Portfolio snapshot, at-risk, trending |
| GET | `/trends` | `{health_trends, ticket_velocity, sentiment_shifts}` | Multi-metric trend analysis |
| POST | `/check-rules` | `{alerts_created, details}` | Run 4 alert rules engine |

### 11.16 Drafts (`/api/drafts`)

| Method | Path | Output | Description |
|--------|------|--------|-------------|
| GET | `/` | `[{id, agent_id, draft_type, status, confidence, created_at}]` | List agent drafts |
| GET | `/:id` | Full draft with content | Draft detail |
| POST | `/:id/approve` | `{id, status: "approved"}` | Approve a draft → executes action |
| POST | `/:id/dismiss` | `{id, status: "dismissed"}` | Dismiss a draft → logs rejection |

### 11.17 Webhooks (`/api/webhooks`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/jira` | Jira Cloud webhook receiver (verifies secret, syncs issue, fires triage event) |
| POST | `/slack` | Slack Events API receiver (url_verification + message handling for chat) |
| POST | `/slack/interactions` | Slack interactive message callbacks (Approve/Edit/Dismiss buttons) |

### 11.18 Demo (`/api/demo`)

| Method | Path | Input | Description |
|--------|------|-------|-------------|
| POST | `/trigger` | `{scenario}` | Trigger demo scenario (all, triage, fathom, etc.) |

### 11.19 v2 Endpoints (Hierarchy-Aware)

| Router | Prefix | Description |
|--------|--------|-------------|
| hierarchy | `/v2/hierarchy` | Agent hierarchy, tier structure, lane assignments |
| messages | `/v2/messages` | Inter-agent message board (5 message types, threaded) |
| pipeline | `/v2/pipeline` | Pipeline execution rounds, stage logs |
| memory | `/v2/memory` | Agent memory operations (episodic, semantic) |
| workflows | `/v2/workflows` | Event → agent workflow routing |

---

## 12. Agent Implementations

All agents inherit from `BaseAgent` which provides: multi-stage pipeline execution (`perceive` → `retrieve` → `think` → `act` → `reflect` → `quality_gate` → `finalize`), timing, exception handling, logging (`AgentLog` + `AgentExecutionRound` record creation), and a standard return format: `{success, output, reasoning_summary}`.

Agents are registered via `AgentFactory` and configured from YAML profiles (`backend/config/agent_profiles.yaml`). Each agent has pluggable traits from the `traits/` directory (e.g., `confidence_scoring`, `risk_assessment`, `pattern_recognition`).

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

### 12.7 QBR/Value Agent (`qbr_agent.py`)

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

### 12.11 Pipeline Engine (`pipeline_engine.py`)

Runs the multi-stage pipeline defined in `pipeline.yaml` for each agent execution:

1. **perceive** — Process raw input into structured understanding
2. **retrieve** — Fetch relevant episodic + semantic memories from ChromaDB
3. **think** — Reason about the task using Claude with `tool_use`
4. **act** — Execute the decided action (create draft, update DB, etc.)
5. **reflect** — Evaluate own performance, write to episodic memory
6. **quality_gate** — Check output quality (retry from specific stage if failed)
7. **finalize** — Format output, broadcast via WebSocket

Each stage creates an `AgentExecutionRound` record with tools called, tokens used, confidence, and duration.

### 12.14 Reflection Engine (`reflection_engine.py`)

Post-execution reflection and quality gate. Agents evaluate their own output quality and can trigger re-execution from a specific pipeline stage if the quality gate fails.

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
8. If non-chat event: auto-create draft via `_create_draft_for_output()`

### 13.4 ChatService (`services/chat_service.py`)

Unified chat orchestration for both Streamlit and Slack interfaces.

- `process_message_full(conversation_id, message_text)` — Background entry point: creates messages, tries fast path (Haiku), falls back to full agent pipeline
- Manages conversation lifecycle, message creation, response threading

### 13.5 ChatFastPath (`services/chat_fast_path.py`)

Bypasses full T1→T2→T3 pipeline for interactive chat. Single Claude Haiku call for instant responses.

- Intent-specific prompt builders (ticket lookup, health status, general Q&A)
- Uses `CLAUDE_FAST_MODEL` (Haiku 4.5) for speed
- Falls back to full pipeline if fast path can't handle the query

### 13.6 JiraService (`services/jira_service.py`)

Jira Cloud REST API client via httpx.

- Basic Auth (email + API token)
- JQL search, issue-to-Ticket mapping, ADF text extraction
- `configured` property checks if credentials are set

### 13.7 FathomService (`services/fathom_service.py`)

Fathom API v1 client. Syncs call recordings, extracts transcripts, summaries, and metadata.

### 13.8 SlackService (`services/slack_service.py`)

Real `slack_sdk` WebClient with Block Kit formatting and graceful degradation.

- `send_agent_card()` — Standard card with Approve/Edit/Dismiss interactive buttons + deep-links
- `send_message()` — General message with optional `thread_ts` for threading
- `get_user_info()` — Lookup Slack user details
- Graceful degradation: if `SLACK_ENABLED=false`, all calls are no-ops

### 13.9 SlackChatHandler (`services/slack_chat_handler.py`)

Bidirectional Slack chat handler.

- Signature verification (HMAC)
- Deduplication of Slack retry requests
- User mapping (single system user `slack-bot@hivepro.com`)
- Conversation threading: Slack `thread_ts` maps to `ChatConversation` via `metadata_` JSONB
- Reuses `ChatService.process_message_full()` — same fast path / full pipeline as Streamlit

### 13.10 SlackFormatter (`services/slack_formatter.py`)

Converts markdown to Slack Block Kit format (headings, bold, bullets, dividers, code blocks).

### 13.11 DraftService (`services/draft_service.py`)

Draft-first approval workflow.

- `create_draft(agent_id, event_id, customer_id, draft_type, content, confidence)` — Creates `AgentDraft` record
- `approve_draft(draft_id, approved_by)` — Executes the approved action + creates `AuditLog` entry
- `dismiss_draft(draft_id, dismissed_by)` — Logs rejection + creates `AuditLog` entry
- `edit_draft(draft_id, edit_diff)` — Records human edits

### 13.12 AlertRulesEngine (`services/alert_rules_engine.py`)

4 automated alert rules that check for critical conditions:

1. **health_drop_15** — Health score dropped 15+ points in 7 days
2. **critical_tickets_stale** — Critical tickets open for too long
3. **renewal_at_risk** — At-risk customer with renewal within 90 days
4. **negative_sentiment_streak** — Multiple consecutive negative call sentiments

Rules deduplicate: won't create duplicate open alerts for the same customer + type.

### 13.13 TrendService (`services/trend_service.py`)

Executive analytics queries (all pure SQL):

- `health_trends(days)` — Daily average health scores + at-risk counts
- `ticket_velocity(days)` — Ticket creation/resolution rates by severity
- `sentiment_shifts(days)` — Sentiment distribution over time
- `portfolio_snapshot()` — Current state of all customers

### 13.14 MeetingKnowledgeService (`services/meeting_knowledge_service.py`)

Manages the `meeting_knowledge` ChromaDB collection for Fathom Agent RAG retrieval.

- `backfill_from_db()` — Re-populates ChromaDB from PostgreSQL `call_insights` table on startup

### 13.15 PipelineService (`services/pipeline_service.py`)

Pipeline execution coordination, stage logging, and progress broadcasting.

### 13.16 MessageService (`services/message_service.py`)

Inter-agent message operations on the Message Board (`agent_messages` table). Creates, queries, and manages typed messages between agents.

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
- **Demo mode:** If backend is unreachable (network error), accepts any credentials and uses fallback data from `frontend/src/data/`
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
- `fetchAll()` — Parallel `Promise.allSettled` of stats, agents, events, quickHealth. Falls back to fallback data in demo mode.
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

## 23. Initial Data

The backend seed script has been removed. The admin user (`ayushmaan@hivepro.com`) is auto-created on startup by `backend/app/utils/ensure_admin.py`. All other data comes from live integrations (Jira sync, Fathom sync, HubSpot webhooks).

### Frontend Fallback Data (`frontend/src/data/`)

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

### Utilities & Hooks

**`utils/formatters.js`** — Number/date formatting, color maps for status/severity/lane/risk/event types
**`utils/chartHelpers.js`** — Chart color constants, `healthColorScale` (D3 interpolator), `getCrossFilterOpacity`, agent lane mapping, debounce
**`utils/cn.js`** — `cn(...classes)` using clsx + tailwind-merge
**`hooks/useScrollReveal.js`** — IntersectionObserver hook for scroll-triggered animations

---

## 24. Environment Variables

### Development (.env)

See `.env.example` for a complete template with inline comments and setup links.

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql+asyncpg://USER:PASS@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
SYNC_DATABASE_URL=postgresql://USER:PASS@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

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
CLAUDE_FAST_MODEL=claude-haiku-4-5-20251001

# ChromaDB
CHROMADB_PATH=./chromadb_data
CHROMADB_MODE=persistent

# Demo Mode
DEMO_MODE=true

# Jira (Atlassian Cloud)
JIRA_API_URL=https://hivepro.atlassian.net
JIRA_EMAIL=your-email@hivepro.com
JIRA_API_TOKEN=
JIRA_WEBHOOK_SECRET=
JIRA_DEFAULT_PROJECT=CS

# Fathom
FATHOM_API_KEY=fth_...
FATHOM_API_BASE_URL=https://api.fathom.ai/external/v1

# Slack
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=
SLACK_BOT_USER_ID=
SLACK_CHAT_CHANNEL=
# 9 dedicated channels
SLACK_CH_TICKET_TRIAGE=#cs-ticket-triage
SLACK_CH_CALL_INTEL=#cs-call-intelligence
SLACK_CH_HEALTH_ALERTS=#cs-health-alerts
SLACK_CH_ESCALATIONS=#cs-escalations
SLACK_CH_DELIVERY=#cs-delivery
SLACK_CH_QBR_DRAFTS=#cs-qbr-drafts
SLACK_CH_PRESALES=#cs-presales-funnel
SLACK_CH_EXEC_DIGEST=#cs-executive-digest
SLACK_CH_EXEC_URGENT=#cs-executive-urgent

# Dashboard base URL for deep-links in Slack cards
DASHBOARD_BASE_URL=http://localhost:5173

# Sync schedule timezone
SYNC_TIMEZONE=Asia/Kolkata

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
DASHBOARD_BASE_URL=https://your-app.vercel.app           # Slack deep-links
DEMO_MODE=false
VITE_API_URL=https://cs-control-plane-api.onrender.com/api
VITE_WS_URL=wss://cs-control-plane-api.onrender.com/api/ws
```

### Variable Reference

| Variable | Required | Default | Used By |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | — | FastAPI async engine (asyncpg) |
| `SYNC_DATABASE_URL` | Yes | — | Alembic, Celery, sync tasks (psycopg2) |
| `REDIS_URL` | No | `""` (sync fallback) | Celery broker/backend |
| `JWT_SECRET_KEY` | Yes | placeholder | Token signing/verification |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API calls (all agents) |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-5-20250929` | Main model (full pipeline) |
| `CLAUDE_FAST_MODEL` | No | `claude-haiku-4-5-20251001` | Fast model (interactive chat) |
| `CHROMADB_PATH` | No | `./chromadb_data` | Persistent storage path |
| `CHROMADB_MODE` | No | `persistent` | `persistent` or `ephemeral` |
| `FRONTEND_URL` | No | `""` (open CORS) | CORS origin restriction |
| `DEMO_MODE` | No | `true` | Enable demo features + rich terminal logging |
| `JIRA_API_URL` | No | `https://hivepro.atlassian.net` | Jira Cloud base URL |
| `JIRA_EMAIL` | No | `""` | Jira Basic Auth email |
| `JIRA_API_TOKEN` | No | `""` | Jira API token |
| `JIRA_WEBHOOK_SECRET` | No | `""` | Jira webhook HMAC verification |
| `JIRA_DEFAULT_PROJECT` | No | `CS` | Default Jira project for sync |
| `FATHOM_API_KEY` | No | `""` | Fathom API v1 key |
| `FATHOM_API_BASE_URL` | No | `https://api.fathom.ai/external/v1` | Fathom API base URL |
| `SLACK_ENABLED` | No | `false` | Master switch for all Slack features |
| `SLACK_BOT_TOKEN` | No | `""` | Slack Bot OAuth token (`xoxb-...`) |
| `SLACK_SIGNING_SECRET` | No | `""` | Slack app signing secret (HMAC verification) |
| `SLACK_BOT_USER_ID` | No | `""` | Bot's own user ID (to ignore own messages) |
| `SLACK_CHAT_CHANNEL` | No | `""` | Restrict chat to specific channel(s) |
| `SLACK_CH_*` (9 vars) | No | Channel names | 9 dedicated Slack channels for agent output |
| `DASHBOARD_BASE_URL` | No | `http://localhost:5173` | Deep-link URLs in Slack cards |
| `SYNC_TIMEZONE` | No | `Asia/Kolkata` | APScheduler cron job timezone |
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
| 7 | Remaining Agents | Done | All 10 agents implemented |
| 8 | Frontend Shell | Done | Design system, Tailwind, Sidebar, TopBar, CommandPalette |
| 9 | Login + Dashboard (2D) | Done | Login page, dashboard KPIs, live pulse, health grid |
| 10 | Dashboard 3D | Done | NeuralSphere, FloatingOrbs, DataFlowRivers, HealthTerrain |
| 11 | Customer Observatory + Detail | Done | PremiumGrid, DataTable, CustomerHero, HealthStory, IntelPanels |
| 12 | Agent Nexus | Done | NeuralNetwork (D3), AgentBrainPanel, ReasoningLog |
| 13 | Signal Intelligence + Warroom | Done | SentimentSpectrum, InsightCard, WarroomTable, TicketDetailDrawer |
| 14 | Analytics Lab | Done | HealthHeatmap, TicketVelocity, SentimentRiver, AgentThroughput, cross-filtering |
| 15 | Polish | Partial | Animations, empty states, toasts done. Settings page done. |
| 16 | E2E Testing + Performance | Pending | Playwright tests, 3D perf audit, bundle audit, Lighthouse |
| A | Architecture Upgrade | Done | 4-tier hierarchy (T1→T2→T3→T4), 14 agents, YAML-driven config, pipeline engine, 3-tier memory, message board, traits system, reflection engine |
| B | Fathom Integration | Done | Fathom API sync, meeting knowledge service, call intelligence pipeline, ChromaDB backfill |
| C | Jira Integration | Done | Jira REST API (httpx), bulk + incremental sync, webhook receiver, auto-triage events, `jira_project_key` mapping |
| D | Slack Integration | Done | Real slack-sdk, Block Kit formatting, 9 dedicated channels, interactive buttons (Approve/Edit/Dismiss), draft-first workflow, `agent_drafts` + `audit_log` tables |
| D.2 | Slack Chat | Done | Bidirectional chat, signature verification, conversation threading, markdown→Block Kit, user mapping, reuses chat fast path |
| E | Executive Summaries | Done | Trend service (pure SQL), alert rules engine (4 rules), executive router, Streamlit page |
| F | Chat Fast Path | Done | Haiku fast responses, intent-specific prompts, background processing, unified chat service for Streamlit + Slack |
| G | Streamlit UI | Done | 6-page app (Ask, Dashboard, Customers, Agents, Tickets, Executive Summary), JWT auth, API polling |
| H | Demo System | Done | Demo runner CLI, demo data constants, rich terminal logging, demo API endpoint |

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
pip install -r requirements.txt
# Configure .env (copy from .env.example, fill in DATABASE_URL + SYNC_DATABASE_URL + ANTHROPIC_API_KEY)
alembic upgrade head            # Create all tables
uvicorn app.main:app --reload --port 8000
```

On startup the backend will:
- Auto-create the admin user (`ayushmaan@hivepro.com` / `password123`)
- Pre-warm database connection pools (mitigates Neon cold start)
- Backfill ChromaDB from PostgreSQL
- Start APScheduler jobs (Jira daily at 8 AM, Fathom at 6 AM & 6 PM)

### Streamlit UI (Primary)
```bash
cd streamlit_app
streamlit run app.py            # Start on http://localhost:8501
```

### React Frontend (Optional)
```bash
cd frontend
npm install
npm run dev                     # Start on http://localhost:5173
```

### Admin Account (Auto-Created on Startup)

| Email | Password | Role |
|-------|----------|------|
| ayushmaan@hivepro.com | password123 | admin |

### Demo Mode
- **Backend:** Set `DEMO_MODE=true` in `.env`. Enables rich terminal logging + `POST /api/demo/trigger` endpoint. CLI: `python -m app.demo_runner --scenario all`
- **React Frontend:** If the backend is unreachable, falls back to demo mode: accepts any credentials, uses fallback data from `frontend/src/data/`, and runs fully offline.

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
9. **Demo mode** — Frontend works fully offline with fallback data when backend is down.

---

## 29. Known Gaps & Limitations

### Agents
- **SOW & Prerequisite Agent** — Code is complete but has **no persistence path**. Output from Claude is generated but discarded after the run.
- **Deployment Intelligence Agent** — Same issue: output is discarded, no save logic exists.
- **Pre-Sales Funnel Agent** — Listed in spec but no dedicated Python file exists. Pipeline analytics may be handled through other means.
- **Generic trigger endpoint** — Most agents require manually constructed payloads via `POST /agents/:name/trigger`. Only Ticket Triage and Troubleshooter have dedicated endpoints that auto-populate data from the DB.

### External Integrations
- **Jira** — ✅ Fully integrated. Live webhook + daily sync (8 AM IST). Tickets come from Jira via `jira_service.py`.
- **Fathom** — ✅ Fully integrated. Live API sync at 6 AM & 6 PM IST. Call insights from Fathom API v1.
- **Slack** — ✅ Fully integrated. Real `slack-sdk` WebClient, 9 dedicated channels, interactive buttons (Approve/Edit/Dismiss), bidirectional chat, Block Kit formatting.
- **HubSpot** — ⬜ Not yet integrated (planned). Deal pipeline sync + webhook on stage change.

### Infrastructure
- **Redis** — Optional. Without it, all Celery tasks run synchronously (no background processing, no task queueing). Fine for dev, not ideal for production load.
- **ChromaDB ephemeral mode** — In production (Render), vector embeddings are lost on restart. Backfill from PostgreSQL runs automatically on startup, but first-request latency is higher.
- **Neon free tier** — ~6s cold start on first DB connection. Pool pre-warming on startup mitigates subsequent requests.

### Testing
- **E2E tests** — Playwright config exists but test suite is not yet written (Phase 16).
- **Unit tests** — Backend test directory exists but coverage is minimal.

### Frontend
- **React dashboard** — 3 pages functional (Dashboard, CustomerDetail, PipelineAnalytics). Original 9-page spec partially implemented.
- **Accessibility** — Basic support (focus rings, reduced motion, semantic HTML) but no comprehensive audit.

---

*This document was originally generated on March 2, 2026 and updated on March 23, 2026 to reflect the current state of the codebase (Phases A-H: architecture upgrade, Jira/Fathom/Slack integration, chat system, executive summaries, Streamlit UI, demo system).*
