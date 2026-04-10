## Auto-Invoke Rules — MCP Tools & Skills

> **These are MANDATORY.** When a task matches a trigger below, invoke the corresponding tool/skill BEFORE writing any code or response. Do not wait for the user to type the slash command — auto-invoke it.

### MCP Tools

**Context7 — Library Documentation (ALWAYS use)**
When writing or modifying code that uses **any** external library (FastAPI, SQLAlchemy, Alembic, httpx, slack-sdk, APScheduler, Pydantic, React, Tailwind, Zustand, Framer Motion, recharts, chromadb, etc.):
- **MUST** use the `context7` MCP tool to fetch current documentation before writing API calls, decorators, or config patterns
- This prevents hallucinated APIs and catches breaking changes between library versions
- **Skip when:** Pure business logic, string manipulation, or code that doesn't touch external library APIs

**FastAPI-MCP — Live API Access (when backend is running)**
When the backend server is running on `localhost:8000`, the `hivepro-api` MCP server exposes all 23 API routers as callable tools:
- **USE for:** Debugging data, verifying endpoint responses, inspecting system state
- **Skip when:** Backend server is not running

### Skills — Auto-Invoke Triggers

**`/develop`** — Auto-invoke when the user asks to:
- Build a new feature, add a new agent, create a new endpoint, add a new page
- Modify existing features, add phases, change workflows
- Any task described as "implement", "add", "create", "build", "wire up"

**`/debug`** — Auto-invoke when the user reports:
- Something is broken, failing, returning errors, or behaving unexpectedly
- "Why is X not working?", "X returns 500", "This crashes when..."
- Any error trace, stack trace, or unexpected behavior

**`/code-review`** — Auto-invoke when the user asks to:
- Review a PR, review recent changes, review code quality
- "Review this", "Check this code", "Is this PR safe?"

**`/post-review-fix`** — Auto-invoke when the user:
- Shares code review feedback and asks to fix it
- Pastes review comments/findings to address

**`/write-docs`** — Auto-invoke when the user asks to:
- Write documentation, update docs, add docstrings, create a README
- Explain how something works (for documentation purposes, not casual questions)

**`/ui-ux-pro-max`** — Auto-invoke when the user asks to:
- Design or build UI components, pages, dashboards, layouts
- Choose colors, typography, spacing, animations
- Review UI/UX quality of existing components

**`/gitnexus-exploring`** — Auto-invoke when the user asks:
- "How does X work?", "What calls this?", "Show me the auth flow"
- Architecture questions, execution flow tracing, codebase exploration

**`/gitnexus-debugging`** — Auto-invoke when debugging AND GitNexus tools would help trace the call graph. Use alongside `/debug` — debug handles the fix, gitnexus-debugging traces the graph.

**`/gitnexus-impact-analysis`** — Auto-invoke BEFORE any non-trivial code edit. This is already a CLAUDE.md rule — run `gitnexus_impact` before modifying any symbol.

**`/gitnexus-refactoring`** — Auto-invoke when the user asks to:
- Rename, extract, split, move, or restructure code
- "Rename this function", "Extract this into a module", "Move this to a new file"

**`/gitnexus-cli`** — Auto-invoke when the user asks to:
- Reindex the codebase, check index status, generate a wiki
- "Reanalyze the codebase", "Index this repo"

### Skill Combinations (common patterns)
- **New feature:** `/develop` (primary) + `/gitnexus-impact-analysis` (before editing)
- **Bug fix:** `/debug` + `/gitnexus-debugging` (trace the graph)
- **UI work:** `/ui-ux-pro-max` (design) + `/develop` (implementation)
- **Refactor:** `/gitnexus-refactoring` (safety) + `/gitnexus-impact-analysis` (blast radius)
- **Post-review:** `/post-review-fix` (fixes) + `/code-review` (verify after)

---

## UI Design System Rules (read BEFORE any frontend work)

> Always read `design-system/MASTER.md` before writing any frontend code.
> For page-specific work, also read `design-system/pages/[page-name].md` if it exists.

### Tech Stack (existing — do not change)
- Framework: React + JavaScript/JSX (Vite) — NOT TypeScript
- Styling: Tailwind CSS + shadcn/ui components
- Animations: Framer Motion
- Icons: lucide-react ONLY (no emojis as icons, no other icon libraries)
- Charts: recharts
- Theme: Dark mode primary via CSS variables on [data-theme="dark"]

### HivePro Brand Tokens
Primary teal:       #18C7B6
Primary dark:       #129589
Bg default (dark):  #121212
Bg paper (dark):    #181818
Bg card (dark):     #1C1C1C
Bg sidebar (dark):  #1B1B1B
Text primary:       #FFFFFF
Text secondary:     #A7A7A7
Border:             #333333
Error:              #FA8072
Chip active (dark): teal text on #181818 bg

### Component Rules
- Button border-radius: 30px, text-transform: none, font-weight: 400
- Card/Paper border-radius: 8px
- AppBar height: 45px
- Font: Roboto, sans-serif
- Body: 14px / 400 weight
- Spacing scale: 8px base (8, 16, 24, 32, 40, 48)
- All clickables: cursor-pointer + transition 150-300ms
- Responsive: 375px, 768px, 1024px, 1440px

### Anti-Patterns — NEVER do these
- No purple gradients
- No emojis as icons (lucide-react only)
- No hardcoded color hex values in JSX — use CSS variables or Tailwind tokens
- No lorem ipsum
- No TypeScript syntax (.tsx, type annotations) — this is a JSX project
- No reinstalling or reinitialising Vite/Tailwind/React

### Aesthetic
- Style: HUD / Dark Command Center — precise, data-dense, authoritative
- Animations: Subtle — staggered card entrance, smooth sidebar collapse, no excessive glow

# CLAUDE.md — CS Control Plane Development Context

> This file is the single source of truth for Claude Code when working on this project.
> Read this FIRST before making any changes to the codebase.

---

## Core Principles

1. First think through the problem, read the codebase for relevant files.
2. Before making any code change, use the `detect_impact` GitNexus tool to analyze what will be affected, and keep those effects in mind while implementing the feature.
3. Before you make any major changes, check in with me and I will verify the plan.
4. Please every step of the way just give me a high level explanation of what changes you made
5. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
6. Maintain a documentation file that describes how the architecture of the app works inside and out.
7. Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase. Never make any claims about code before investigating unless you are certain of the correct answer - give grounded and hallucination-free answers.

---

## Project Identity

- **Name:** HivePro CS Control Plane
- **Codename:** Mission Control
- **Type:** Full-stack web application (AI agent backend + Slack-first delivery + dashboard)
- **Author:** Ayushmaan Singh Naruka (AI Hub Team, HivePro)
- **Architecture:** Event-driven, draft-first, Slack-push + dashboard-pull

---

## What This Project Does

The CS Control Plane is an AI-powered system that automates Customer Success workflows at HivePro. It uses **10 specialized AI agents** to watch incoming data from three sources — **Jira tickets**, **Fathom call recordings**, and **HubSpot deals** — and automatically triages issues, analyzes calls, monitors customer health, generates reports, and drafts actions for the CS team.

The system follows a **Slack-first delivery model**: agents push their outputs as interactive cards to **9 dedicated Slack channels**. CS team members review, approve, or edit directly in Slack. A **3-page dashboard** provides drill-down views when deeper context is needed — accessed via deep-links in Slack cards, not by browsing.

Every agent output starts as a **draft**. Nothing customer-facing or system-modifying happens without human approval. Over time, agents that prove high accuracy (measured over 4+ weeks) earn selective autonomy for low-risk actions.

**Core capabilities:**

1. **10 Agents, 4 Lanes** — CS Orchestrator routes events to agents organized in Pre-Sales, Delivery, Run/Support, and Value lanes. Customer Memory is a shared service used by all.
2. **Event-Driven** — Every workflow starts from a discrete event (webhook, cron, manual trigger). The Orchestrator classifies and routes to the correct agent.
3. **Draft-First** — Every agent output is a draft. Humans approve in Slack before any customer-facing action, Jira write, or email send.
4. **Slack-Push, Dashboard-Pull** — Slack is where notifications go. The dashboard is only opened via deep-links from Slack cards.
5. **Customer Isolation** — Every database query is scoped to a `customer_id`. Memory is per-customer.
6. **AI Triage** — Auto-classifies incoming Jira UCSC tickets with category, severity, diagnostics, duplicate detection, and email drafts
7. **Call Intelligence** — Extracts summaries, action items, sentiment from Fathom recordings
8. **Health Monitoring** — Daily health scores, risk flags, cross-customer pattern detection, proactive Jira ticket drafts
9. **Executive Reporting** — Weekly portfolio digest + real-time threshold alerts (issue clusters, health crashes, SLA cascades, churn signals, pipeline stalls)
10. **Chat Interface** — Interactive chat via Slack with fast path (Haiku) for instant responses

---

## Data Sources

| Source | What It Provides | Ingestion Method |
|--------|-----------------|-----------------|
| **Jira (UCSC)** | Tickets: priority, status, SLA, labels, comments | Webhook + daily sync (8 AM via APScheduler) |
| **Fathom** | Call transcripts, summaries, action items, sentiment | API sync (6 AM + 6 PM via APScheduler) |
| **HubSpot** | Deals pipeline, stages, contacts, close reasons | Daily API pull + webhook on stage change |

---

## Agent Roster (10 Agents)

| # | Agent | Lane | Role |
|---|-------|------|------|
| 1 | **CS Orchestrator** | Control | Classifies events, routes to correct agent. Never analyzes — pure routing. |
| 2 | **Customer Memory** | Shared Services | Per-customer JSON store (CRUD). Every agent reads before executing, writes results back. |
| 3 | **Pre-Sales Funnel** | Pre-Sales | Analyzes HubSpot pipeline: conversion rates, stalled deals, blocker patterns. Read-only. |
| 4 | **SOW & Prerequisite** | Delivery | Generates SOW docs, infra checklists, security checklists, timelines for new customers. |
| 5 | **Deployment Intelligence** | Delivery | Validates deployments: service health, connectors, first scan, RBAC/SSO. Flags failures. |
| 6 | **Ticket Triage** | Run / Support | Classifies Jira UCSC tickets: category, severity (P0-P3), diagnostics, duplicates, email draft. |
| 7 | **Troubleshooting** | Run / Support | Analyzes support bundles, finds root cause with confidence score. If < 70% → routes to Escalation. |
| 8 | **Escalation Writer** | Run / Support | Compiles escalation doc: customer context, technical summary, evidence, repro steps, timeline. |
| 9 | **Health Monitor** | Value | Daily health checks on all customers: ticket severity, call sentiment, renewal proximity, health trends, open alerts. |
| 10 | **QBR / Value Narrative** | Value | Quarterly business reviews: sentiment bucketing (Happy/Neutral/Unhappy), root cause analysis, renewal recs. |

**Lane structure:**
- **Pre-Sales:** Agent 3
- **Delivery:** Agents 4, 5
- **Run / Support:** Agents 6, 7, 8
- **Value:** Agents 9, 10
- **Shared Services:** Agent 2 (Customer Memory) + Executive Reporter

---

## Slack Channel Map

| Channel | What Gets Posted | Agent Source |
|---------|-----------------|-------------|
| **#cs-executive-overview** | Portfolio brief (Wed & Fri 9 AM) — health, renewals, pipeline, tickets, AI actions | Executive Brief Service |
| **#cs-executive-digest** | Weekly executive summary (Monday 9 AM) | Executive Reporter |
| **#cs-executive-urgent** | Escalation alerts: stale P0/P1 (daily), repeated features, recurring complaints, unanswered actions (Wed+Fri) | Alert Rules Engine |
| **#cs-call-intelligence** | Post-call summaries + action items + sentiment | Call Intelligence |
| **#cs-ticket-triage** | Ticket classifications + troubleshooting results | Ticket Triage, Troubleshooting |
| **#cs-health-alerts** | Health check results + risk flags + threshold alerts (health drops, sentiment streaks, renewal risk) | Health Monitor, Alert Rules Engine |
| **#cs-presales-funnel** | Pipeline analytics + stalled deal alerts | Pre-Sales Funnel |
| **#cs-qbr-drafts** | QBR document drafts for review | QBR / Value Narrative |
| **#cs-escalations** | Engineering escalation docs for approval | Escalation Writer |
| **#cs-delivery** | SOW drafts, deployment status | SOW & Prerequisite, Deployment Intelligence |

---

## Dashboard (3 Pages)

| Page | URL | Purpose |
|------|-----|---------|
| **At-Risk Dashboard** | `/dashboard` | Portfolio health KPIs, at-risk customer table, alert feed, trend charts |
| **Customer Profile** | `/dashboard/customer/{id}` | Single customer deep-dive with tabs: Overview, Tickets, Calls, Health History, QBR, HubSpot |
| **Pipeline Analytics** | `/dashboard/pipeline` | Pre-sales funnel, conversion rates, stalled deals, blockers |

---

## Documentation Reference

| Document | Path | Read When |
|----------|------|-----------|
| **Architecture** | `/docs/ARCHITECTURE.md` | System design, agent specs, event routing, implementation phases |
| **PRD** | `/docs/PRD.md` | Features, user stories, acceptance criteria |
| **Wireframes** | `/docs/WIREFRAMES.md` | UI component specs, 3D specs, colors, fonts, layouts |
| **API Contract** | `/docs/API_CONTRACT.md` | API endpoint request/response JSON shapes |
| **Database Schema** | `/docs/DATABASE_SCHEMA.md` | Models, migrations |
| **Executive QA** | `/docs/EXECUTIVE_QA_COVERAGE.md` | Executive feature test coverage |

**Read order for a new feature:** Architecture (context) → PRD (what) → Wireframes (how it looks) → API Contract (data shape) → Database Schema (storage)

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Backend** | FastAPI (Python 3.11+) | API server, agent orchestration |
| Database | PostgreSQL 16 (Neon cloud) | Structured data, customer memory, drafts, audit log |
| Vector DB | ChromaDB (persistent, 6 collections) | RAG search, episodic + semantic memory |
| ORM | SQLAlchemy 2.0 (async) | asyncpg driver for async, psycopg2 for sync |
| Migrations | Alembic | 6 migration files |
| AI (main) | Claude Sonnet (`claude-sonnet-4-5-20250929`) | Agent LLM calls |
| AI (fast) | Claude Haiku (`claude-haiku-4-5-20251001`) | Fast chat responses |
| Config | PyYAML | Agent profiles, org structure, pipelines, workflows |
| Scheduling | APScheduler | Fixed-time syncs (no Redis needed) |
| Task Queue | Celery (eager mode) | Async tasks, no Redis required locally |
| **Integrations** | Jira REST API (httpx) | Ticket sync + webhooks |
| | Fathom API v1 (httpx) | Call transcript sync |
| | Slack SDK (slack-sdk) | Bot, interactive messages, chat, webhooks |
| **Frontend** | React 18 + Vite 5 | Dashboard SPA (3 pages, minimal) |
| Styling | Tailwind CSS 3.x | Custom design system |
| State | Zustand | Client-side state |
| Auth | python-jose (JWT) + passlib[bcrypt] | Token-based auth |
| HTTP Client | httpx | External API integration |

---

## Project Structure (Actual)

```
hivepro-cs-control-plane/
├── CLAUDE.md                          ← YOU ARE HERE
├── DOCUMENTATION.md                   # Comprehensive docs
├── DEPLOYMENT.md                      # Deployment instructions
├── render.yaml                        # Render deployment config
├── .env / .env.example
│
├── docs/
│   ├── ARCHITECTURE.md                # System design (source of truth)
│   ├── PRD.md
│   ├── WIREFRAMES.md
│   ├── API_CONTRACT.md
│   ├── DATABASE_SCHEMA.md
│   └── EXECUTIVE_QA_COVERAGE.md
│
├── backend/
│   ├── requirements.txt               # 47 Python packages
│   ├── Procfile                       # Render process config
│   ├── runtime.txt                    # Python version
│   ├── alembic.ini
│   ├── alembic/versions/              # 7 migrations
│   ├── chromadb_data/                 # Persistent vector DB (6 collections)
│   │
│   ├── config/                        # YAML-driven agent configuration
│   │   ├── org_structure.yaml         # Lanes, agent assignments, reporting
│   │   ├── agent_profiles.yaml        # 11 agent definitions, traits, tools
│   │   ├── pipeline.yaml              # Pipeline stage definitions
│   │   └── workflows.yaml             # Event → agent routing workflows
│   │
│   └── app/
│       ├── main.py                    # FastAPI entry + APScheduler setup
│       ├── config.py                  # Settings (40+ env vars)
│       ├── database.py                # PostgreSQL async/sync connections
│       ├── chromadb_client.py         # ChromaDB persistent client
│       ├── websocket_manager.py       # WebSocket broadcast
│       ├── demo_data.py               # Demo scenario data
│       ├── demo_runner.py             # CLI demo tool
│       │
│       ├── models/                    # SQLAlchemy models (18 tables)
│       │   ├── user.py
│       │   ├── customer.py            # Includes jira_project_key
│       │   ├── deal.py                # HubSpot CRM deals
│       │   ├── health_score.py
│       │   ├── ticket.py
│       │   ├── call_insight.py
│       │   ├── action_item.py
│       │   ├── alert.py
│       │   ├── event.py
│       │   ├── agent_execution_round.py
│       │   ├── agent_log.py
│       │   ├── chat_conversation.py
│       │   ├── chat_message.py
│       │   ├── agent_draft.py
│       │   ├── audit_log.py
│       │   └── report.py
│       │
│       ├── schemas/                   # Pydantic schemas (17 files)
│       │
│       ├── routers/                   # API endpoints (23 routers)
│       │   ├── auth.py                # Login, refresh, logout
│       │   ├── dashboard.py           # KPIs, metrics
│       │   ├── customers.py           # Customer CRUD
│       │   ├── health.py              # Health score trends
│       │   ├── tickets.py             # Ticket CRUD
│       │   ├── insights.py            # Call insights
│       │   ├── agents.py              # Agent status
│       │   ├── reports.py             # Report generation
│       │   ├── events.py              # Event creation/query
│       │   ├── alerts.py              # Alert CRUD
│       │   ├── chat.py                # Chat send/poll
│       │   ├── webhooks.py            # Jira, Fathom, Slack webhooks
│       │   ├── jira.py                # Jira sync endpoints
│       │   ├── fathom.py              # Fathom sync endpoints
│       │   ├── hubspot.py             # HubSpot sync + status endpoints
│       │   ├── executive.py           # Executive summary, trends
│       │   ├── drafts.py              # Draft approve/dismiss
│       │   ├── demo.py                # Demo triggers
│       │
│       ├── agents/                    # AI agent implementations (10 agents)
│       │   ├── base_agent.py          # Base with pipeline execution
│       │   ├── pipeline_engine.py     # Multi-round pipeline runner
│       │   ├── reflection_engine.py   # Reflection + quality gate
│       │   ├── agent_factory.py       # Agent registration
│       │   ├── profile_loader.py      # YAML profile loading
│       │   ├── demo_logger.py         # Rich terminal logging
│       │   ├── orchestrator.py        # Agent 1: CS Orchestrator
│       │   │
│       │   ├── triage_agent.py        # Agent 6: Ticket Triage
│       │   ├── troubleshoot_agent.py  # Agent 7: Troubleshooting
│       │   ├── escalation_agent.py    # Agent 8: Escalation Writer
│       │   ├── health_monitor.py      # Agent 9: Health Monitor
│       │   ├── qbr_agent.py           # Agent 10: QBR / Value Narrative
│       │   ├── sow_agent.py           # Agent 4: SOW & Prerequisite
│       │   ├── deployment_intel_agent.py # Agent 5: Deployment Intelligence
│       │   ├── presales_funnel_agent.py # Agent 3: Pre-Sales Funnel (pipeline + win probability)
│       │   │
│       │   ├── memory/                # Agent 2: Customer Memory (shared service)
│       │   │   ├── memory_agent.py    # Customer Memory Manager
│       │   │   ├── memory_manager.py  # Memory lifecycle
│       │   │   ├── working_memory.py  # In-process scratchpad
│       │   │   ├── episodic_memory.py # ChromaDB per-agent diary
│       │   │   └── semantic_memory.py # ChromaDB lane-scoped pools
│       │   │
│       │   └── traits/                # Pluggable trait behaviors
│       │       ├── base_trait.py
│       │       ├── registry.py
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
│       ├── services/                  # Business logic (17 files)
│       │   ├── claude_service.py      # Claude API wrapper
│       │   ├── chat_service.py        # Unified chat orchestration
│       │   ├── chat_fast_path.py      # Haiku fast responses
│       │   ├── rag_service.py         # RAG/semantic search
│       │   ├── fathom_service.py      # Fathom API client
│       │   ├── meeting_knowledge_service.py
│       │   ├── jira_service.py        # Jira Cloud client
│       │   ├── slack_service.py       # Slack Bot client
│       │   ├── slack_chat_handler.py  # Slack message handler
│       │   ├── slack_formatter.py     # Markdown → Block Kit
│       │   ├── event_service.py       # Event routing
│       │   ├── draft_service.py       # Draft create/approve/dismiss
│       │   ├── hubspot_service.py      # HubSpot CRM API client
│       │   ├── alert_rules_engine.py  # 4 alert rules
│       │   └── trend_service.py       # Analytics queries
│       │
│       ├── tasks/                     # Background tasks
│       │   ├── celery_app.py          # Celery config (eager mode)
│       │   ├── agent_tasks.py         # 20+ async tasks
│       │   ├── jira_sync.py           # Jira bulk + incremental sync
│       │   └── hubspot_sync.py        # HubSpot deal sync + event firing
│       │
│       ├── middleware/
│       │   └── auth.py                # JWT middleware
│       │
│       └── utils/
│           ├── security.py            # JWT + password utils
│           ├── ensure_admin.py        # Auto-creates admin user on startup
│           └── ensure_admin.py
│
├── frontend/                          # React dashboard (minimal, 3 pages)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── vercel.json
│   └── src/
│       ├── App.jsx / main.jsx / index.css
│       ├── pages/
│       │   ├── DashboardPage.jsx      # At-Risk Dashboard
│       │   ├── CustomerDetailPage.jsx # Customer Profile
│       │   └── PipelineAnalyticsPage.jsx
│       ├── components/
│       │   ├── layout/AppLayout.jsx
│       │   └── shared/                # GlassCard, HealthRing, KpiCard, etc.
│       ├── services/                  # api.js, customerApi, dashboardApi, ticketApi, websocket
│       ├── stores/                    # dashboardStore, customerStore (Zustand)
│       └── utils/formatters.js
│
```

---

## Architecture Rules

### Rule 1: Event-Driven Agent System

Everything flows through the Orchestrator. External events (Jira webhook, Fathom sync, cron) create an `events` record → Orchestrator reads it → routes to the correct agent → agent reads Customer Memory → executes → writes output → updates Customer Memory → broadcasts via WebSocket.

**Never** have agents directly call each other. Always go through the Orchestrator or event system.

### Rule 2: Customer Memory is the Single Source of Truth

Every agent reads from and writes to the Customer Memory (PostgreSQL + ChromaDB). No agent should maintain its own state about a customer.

### Rule 3: WebSocket for All Real-Time Updates

Any change that should appear immediately (agent status, new event, alert, health score, pipeline progress, delegation) must broadcast via WebSocket. The frontend never polls. New event types: `pipeline:*`, `delegation:*`, `memory:*`.

### Rule 4: AI Calls are Always Async

All Claude API calls go through Celery tasks. The API returns 202 with a task_id. Results broadcast via WebSocket. Never block the API thread.

### Rule 5: 3D is Progressive Enhancement

Always build the 2D version first. 3D scenes are lazy-loaded (React.lazy + Suspense) and code-split into their own chunks. The app must be fully functional with 2D fallbacks. 3D enhances but never blocks.

### Rule 6: Spatial Depth Design

Three surface levels: near (0.65 opacity), mid (0.45), far (0.25). Critical data uses surface-near. Supporting data uses surface-mid/far. The void (#020408) is the true background. No flat white or gray backgrounds anywhere.

### Rule 7: Orbital Navigation

No sidebar. The Orbital Nav arc is the primary navigation at the bottom-center. Command Palette (Cmd+K) is the power-user alternative. Breadcrumbs float at top-left. Content fills the full viewport.

### Rule 8: Hierarchical Delegation

The Orchestrator routes events directly to the appropriate specialist agent based on event type and lane. Specialists NEVER delegate to each other directly — sideways requests go through the Message Board. The Foundation layer (Customer Memory) serves ALL agents.

### Rule 9: YAML-Driven Configuration

Agent identities, personalities, traits, tools, pipeline stages, org structure, and workflows are defined in YAML config files (`backend/config/`). **Never** hardcode agent behavior in Python. The code reads YAML at startup and constructs agents dynamically. To change an agent's behavior, edit YAML, not code.

### Rule 10: 3-Tier Memory System

Every agent accesses three memory tiers: **Working** (in-process scratchpad, cleared per run), **Episodic** (ChromaDB `episodic_memory` collection, per-agent diary with tri-factor retrieval), **Semantic** (ChromaDB `shared_knowledge` collection, lane-scoped knowledge pools). Agents read episodic + semantic during `retrieve` stage, write to episodic during `reflect` stage, and optionally publish to semantic via `publish_knowledge` tool.

### Rule 11: Pipeline Execution

Every agent runs a multi-round pipeline defined in `pipeline.yaml`. Stages: `perceive` → `retrieve` → `think` → `act` → `reflect` → `quality_gate` → `finalize`. Each stage is logged to `agent_execution_rounds` with tools called, tokens used, confidence, and duration. The pipeline engine handles quality gate failures (retry from a specific stage). Every stage broadcasts progress via WebSocket.

---

## Event Routing Map

| Event | Source | Agent | Slack Channel |
|-------|--------|-------|---------------|
| `jira_ticket_created` | Jira UCSC webhook | Ticket Triage | #cs-ticket-triage |
| `jira_ticket_updated` | Jira UCSC webhook | Triage / Troubleshooting | #cs-ticket-triage |
| `support_bundle_uploaded` | Manual / Jira | Troubleshooting | #cs-ticket-triage |
| `zoom_call_completed` | Fathom webhook | Call Intelligence | #cs-call-intelligence |
| `deal_stage_changed` | HubSpot webhook | Pre-Sales Funnel | #cs-presales-funnel |
| `daily_health_check` | Cron (8 AM) | Health Monitor | #cs-health-alerts |
| `renewal_within_90_days` | Cron scan | QBR + Health Monitor | #cs-qbr-drafts |
| `new_customer` | HubSpot Closed Won | SOW & Prerequisite | #cs-delivery |
| `deployment_ready` | Manual trigger | Deployment Intelligence | #cs-delivery |
| `escalation_needed` | Troubleshoot confidence < 70% | Escalation Writer | #cs-escalations |
| `weekly_exec_report` | Cron (Mon 9 AM) | Executive Reporter | #cs-executive-digest |

---

## Approval Workflow

```
Agent produces output → Saved as DRAFT (agent_drafts table)
    → Slack card posted to channel
        ├── [Approve] → Execute action (update Jira, send email, etc.)
        ├── [Edit]    → Slack thread → modify → approve
        └── [Dismiss] → Log rejection, no action
    → audit_log records: agent, action, confidence, human decision, edit diff
```

**Never automated:** Escalations, QBR docs, SOW docs, customer data modifications, deletes.

---

## Scheduled Jobs (APScheduler)

| Job | Schedule | Scope |
|-----|----------|-------|
| Jira daily sync | 8:00 AM IST | Incremental (last 25 hours) |
| Jira initial sync | On first startup | Full (last 6 months) |
| Fathom sync | 6:00 AM + 6:00 PM IST | Last 7 days of meetings |
| Fathom startup sync | 30s after app start | Last 7 days |
| HubSpot daily sync | 7:00 AM IST | Full (all deals + company resolution + renewal dates + CS managers) |
| HubSpot startup sync | 15s after app start | Full (first time only — marker file `.hubspot_initial_sync_done`) |
| Health check | Every 3 days at 8:30 AM | All customers |
| Executive brief | Wed & Fri at 9:00 AM | Portfolio summary → #cs-executive-overview |
| Escalation daily | Daily at 8:30 AM | Stale P0 (>3d) + P1 (>4d) → #cs-executive-urgent |
| Escalation patterns | Wed & Fri at 9:15 AM | Feature requests, recurring complaints, unanswered actions → #cs-executive-urgent |

Timezone: `Asia/Kolkata` (configurable via `SYNC_TIMEZONE`)

---

## Coding Standards

### Python (Backend)

```python
# Type hints, Pydantic schemas, HTTPException, dependency injection
# See API_CONTRACT.md for exact response shapes

# YAML Profile Loading Pattern:
import yaml
from pathlib import Path

def load_agent_profiles() -> dict:
    config_path = Path(__file__).parent.parent.parent / "config" / "agent_profiles.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

# Tool Definition Pattern (for Claude tool_use):
def query_customer_db(customer_id: str) -> dict:
    """Look up customer profile and history."""
    customer = db.query(Customer).filter_by(id=customer_id).first()
    return {"name": customer.name, "health_score": customer.current_health, ...}

# Pipeline Stage Method Pattern:
class BaseAgent:
    async def perceive(self, context: WorkingMemory) -> WorkingMemory:
        """Process raw input into structured understanding."""
        ...
    async def retrieve(self, context: WorkingMemory) -> WorkingMemory:
        """Fetch relevant episodic + semantic memories."""
        ...
    async def think(self, context: WorkingMemory) -> WorkingMemory:
        """Reason about the task using Claude with tool_use."""
        ...
```

### JavaScript/React (Frontend)

```javascript
// File naming: PascalCase.jsx for components, camelCase.js for utils/stores
// Animations: framer-motion for layout/page, CSS for micro-interactions

// Surface Card Pattern:
<GlassCard level="near" interactive>
  <h3>Card Title</h3>
</GlassCard>
```

### Import Order

1. React / external libraries
2. Internal modules (stores, services, utils)
3. Components
4. Styles

---

## Design System Quick Reference

**Void:** #020408 (body bg — absolute black, not navy)
**Accents:** --bio-teal=#00F5D4, --bio-violet=#8B5CF6, --bio-cyan=#22D3EE
**Danger:** --bio-rose=#FB7185, Warning: --bio-amber=#FBBF24, Success: --bio-emerald=#34D399
**Lanes:** Control=#00F5D4, Pre-Sales=#8B5CF6, Support=#FBBF24, Value=#34D399, Delivery=#22D3EE
**Surfaces:** near=rgba(8,16,32,0.65), mid=0.45, far=0.25 — all with backdrop-blur(20px)
**Fonts:** Space Grotesk (display/numbers), IBM Plex Mono (data/labels), Inter (body)

**Full design system:** See WIREFRAMES.md Section 1

---

## Environment Variables

```bash
# Database (Neon Cloud)
DATABASE_URL=postgresql+asyncpg://...@ep-xxx.us-east-2.aws.neon.tech/cs_control_plane
SYNC_DATABASE_URL=postgresql://...@ep-xxx.us-east-2.aws.neon.tech/cs_control_plane

# Auth
JWT_SECRET_KEY=your-secret-key
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

# Jira Integration
JIRA_API_URL=https://hivepro-kronos.atlassian.net
JIRA_EMAIL=...
JIRA_API_TOKEN=...
JIRA_DEFAULT_PROJECT=UCSE
JIRA_SYNC_INTERVAL_SECONDS=900
JIRA_WEBHOOK_SECRET=...

# Slack Integration
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_BOT_USER_ID=...
SLACK_CHAT_CHANNEL=...
SLACK_CH_EXECUTIVE_DIGEST=...
SLACK_CH_EXECUTIVE_URGENT=...
SLACK_CH_CALL_INTELLIGENCE=...
SLACK_CH_TICKET_TRIAGE=...
SLACK_CH_HEALTH_ALERTS=...
SLACK_CH_PRESALES_FUNNEL=...
SLACK_CH_QBR_DRAFTS=...
SLACK_CH_ESCALATIONS=...
SLACK_CH_DELIVERY=...

# Fathom Integration
FATHOM_API_KEY=...
FATHOM_API_BASE_URL=https://api.fathom.ai/external/v1

# HubSpot CRM
HUBSPOT_ACCESS_TOKEN=pat-na1-...
HUBSPOT_APP_ID=...
HUBSPOT_API_BASE_URL=https://api.hubapi.com
HUBSPOT_WEBHOOK_SECRET=...

# Scheduling
SYNC_TIMEZONE=Asia/Kolkata

# Frontend
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws
```

---

## Database Schema (18 Tables)

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email, role, is_active) |
| `customers` | Customer profiles (name, health_score, jira_project_key, renewal_date, metadata JSONB with cs_manager) |
| `deals` | HubSpot CRM deals (stage as label, amount, company, ced + deal_terms in properties JSONB) |
| `health_scores` | Daily health score history |
| `tickets` | Support tickets (summary, severity, status, sla_minutes) |
| `call_insights` | Fathom meeting transcripts + extracted insights |
| `action_items` | Agent-created action items |
| `alerts` | Customer health/SLA alerts |
| `events` | Incoming events (type, status, payload) |
| `agent_execution_rounds` | Pipeline stage execution logs |
| `agent_logs` | Agent activity logs |
| `chat_conversations` | Chat conversation threads |
| `chat_messages` | Individual chat messages |
| `agent_drafts` | Draft outputs awaiting approval |
| `audit_logs` | Approval/dismissal audit trail |
| `reports` | Generated reports |

---

## Key Patterns to Know

| Pattern | Detail |
|---------|--------|
| **Agent factory** | All agents registered via `AgentFactory` in `backend/app/agents/agent_factory.py` |
| **Claude calls** | `self._call_claude()` → `claude_service.generate_sync()` (returns input_tokens/output_tokens) |
| **Event routing** | `orchestrator.py` has `EVENT_LANE_MAP` and `EVENT_ROUTING` dicts |
| **Lane routing** | Each lane lead has `SPECIALIST_MAP` and `_fallback_plan()` |
| **Chat fast path** | Bypasses full agent pipeline; single Haiku call for interactive chat. 5 intents: health, fathom, ticket, deal, general. |
| **Cross-reference** | Universal prefetch enriches ALL intents with deals + calls + meetings from all data sources. Portfolio prefetch adds Jira tickets + call topics for broad questions. |
| **Deal probability** | Multi-factor model: stage 25% + engagement 25% + intent 20% + sentiment 15% + velocity 15%. Uses call_insights for signals. |
| **HubSpot sync** | `hubspot_service.py` singleton, Bearer token auth, daily 7 AM cron + startup marker file. 1448 deals synced. Also populates `renewal_date` (from `ced` property) and `cs_manager` (from deal owner) on customers. |
| **Deal stages** | DB stores human-readable labels ("Closed Won", "Discovery Meeting"), NOT HubSpot internal IDs ("closedwon"). All SQL must use labels. |
| **Alert rules** | 9 rules total: 5 original (→ #cs-health-alerts) + 4 escalation (→ #cs-executive-urgent). Escalation rules: stale P0/P1, repeated features (AI-grouped), recurring complaints (AI-grouped), unanswered action items (fire-once). |
| **Executive brief** | `executive_brief_service.py` generates portfolio summary → #cs-executive-overview. Wed+Fri 9 AM. Manual: `POST /api/executive/brief`. |
| **Chat endpoint** | `POST /api/chat/send` with `{"message": text}` (NOT `{"text": text}`) |
| **Chat polling** | `poll_for_response()` checks conversation for `pipeline_status != "processing"` |
| **Model fields** | `HealthScore.calculated_at` (not scored_at), `Ticket.summary` (not title), `Ticket.severity` (not priority) |
| **Admin user** | `ayushmaan@hivepro.com` / auto-created on startup by `ensure_admin.py` |
| **Demo mode** | `DEMO_MODE=true` + `python -m app.demo_runner --scenario all` or `POST /api/demo/trigger` |
| **Neon latency** | ~6s cold start, ~1s warm query from local dev |

---

## Running Locally

```bash
# Backend (no Docker, no Redis needed)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# React Frontend
cd frontend
npm install && npm run dev
```

- PostgreSQL: Neon cloud (no local Docker needed)
- Redis: Disabled (Celery runs in eager mode)
- ChromaDB: Persistent local storage in `backend/chromadb_data/`

---

## Common Pitfalls — Do / Don't

| DO | DON'T |
|----|-------|
| Build 2D first, add 3D as progressive enhancement | Block the app on 3D loading |
| Lazy-load all Three.js scenes (React.lazy + Suspense) | Import Three.js in the main bundle |
| Use the three surface levels (near/mid/far) for depth | Use flat solid backgrounds |
| Use Space Grotesk for display, IBM Plex Mono for data | Use a single font everywhere |
| Body background is #020408 (near-black void) | Use #080C14 or any navy |
| Put async AI calls in Celery tasks | Block API threads with Claude API calls |
| Broadcast changes via WebSocket | Poll endpoints from frontend |
| Respect prefers-reduced-motion | Force 3D on all users |
| Use D3 for complex charts (heatmap, river, radial) | Try to force everything into Recharts |
| Define agent behavior in YAML config files | Hardcode agent personalities/traits/tools in Python |
| Route tasks through hierarchy (T1→T2→T3) | Let specialists call each other directly |
| Use typed messages (task_assignment, deliverable, etc.) | Send unstructured strings between agents |
| Run agents through full pipeline (perceive→...→finalize) | Use single-shot Claude API calls for agent work |
| Log every pipeline stage to agent_execution_rounds | Skip execution logging (breaks trace viewer) |
| Use tri-factor retrieval for episodic memory | Use simple vector similarity only |
| Thread all messages with thread_id + parent_id | Create orphaned messages without thread context |
| Use tier colors (T1=teal, T2=violet, T3=cyan, T4=slate) | Use random colors for agent hierarchy |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **hivepro-cs-control-plane** (2134 symbols, 6958 relationships, 172 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/hivepro-cs-control-plane/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/hivepro-cs-control-plane/context` | Codebase overview, check index freshness |
| `gitnexus://repo/hivepro-cs-control-plane/clusters` | All functional areas |
| `gitnexus://repo/hivepro-cs-control-plane/processes` | All execution flows |
| `gitnexus://repo/hivepro-cs-control-plane/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
