# HivePro CS Control Plane — Product Requirements Document (PRD)

**Product Name:** CS Control Plane
**Codename:** Mission Control
**Author:** Ayushmaan Singh Naruka (AI Hub Team)
**Version:** 3.0 (Agentic Architecture Rebuild)
**Date:** March 2, 2026
**Status:** Phase A — Documentation Update

---

## 1. Product Overview

### 1.1 One-Liner

CS Control Plane is HivePro's AI-powered spatial command center where 13 named agents — organized in a 4-tier hierarchy with pipeline execution, collaborative memory, and inter-agent messaging — automate the entire customer success lifecycle, visualized through an immersive 3D dashboard with real-time neural networks, health terrains, and cinematic data flows.

### 1.2 Problem Statement

HivePro's Customer Success team faces six critical pain points:

1. **Fathom recordings go unanalyzed** — Rich call data exists but nobody has bandwidth to extract insights, action items, or sentiment signals from every recording.
2. **Jira ticket overload** — Tickets pile up without intelligent triage, categorization, or duplicate detection. Engineers waste time re-diagnosing known issues.
3. **No centralized health tracking** — At-risk customers are identified too late because health signals are scattered across tools.
4. **Manual pre-meeting preparation** — CS consultants spend 30-60 minutes before each call gathering context.
5. **No cross-customer pattern recognition** — Recurring issues aren't identified or leveraged across customers.
6. **QBR preparation is time-consuming** — Monthly/quarterly reviews require manually compiling data.

### 1.3 Solution

A full-stack web application serving as a spatial control plane for **13 AI agents organized in a 4-tier hierarchy** (Supervisor → Lane Leads → Specialists → Foundation) across 3 operational lanes (Support, Value, Delivery). The application features:

- **4-tier agent hierarchy** — A CS Manager (Naveen Kapoor) delegates to 3 Lane Leads, who coordinate 8 Specialists, all powered by a shared Foundation memory layer (Atlas)
- **Multi-round pipeline execution** — Agents think in stages (perceive → retrieve → think → act → reflect → quality_gate → finalize) instead of single-shot API calls
- **3-tier memory system** — Working memory (scratchpad), episodic memory (diary of past runs), and semantic memory (shared knowledge pools per lane)
- **Inter-agent message board** — Typed messages (task assignments, deliverables, escalations) flowing up, down, and sideways through the hierarchy
- **12+ agent tools** — Agents call real functions (query DB, search RAG, check SLA, write reports) via Claude's tool_use API instead of guessing
- **YAML-driven configuration** — Agent personalities, traits, pipeline stages, and org structure defined in config files, not hardcoded Python
- **Spatial 3D dashboard** — Neural sphere showing 13 agents in 4 tiers, health terrain maps, floating metric orbs, particle data flow rivers
- **Orbital navigation** — Bottom-arc HUD replacing traditional sidebars, with Cmd+K command palette
- **Real-time WebSocket updates** — Every pipeline stage, delegation event, and metric change streams live
- **Premium visual design** — "Deep Ocean Bioluminescence" aesthetic with two-tone accent system (teal + violet), frosted depth surfaces, cinematic page transitions

### 1.4 Target Users

| User | Role | Primary Use |
|------|------|-------------|
| CS Engineers | Day-to-day support | Ticket triage results, troubleshooting suggestions, customer context |
| CS Consultants | Customer-facing | Pre-meeting briefs, call insights, action item tracking |
| CS Managers | Team oversight | Health dashboard, risk alerts, performance metrics, agent hierarchy monitoring |
| VP/Directors | Executive oversight | QBR reports, aggregate analytics, system ROI, pipeline efficiency |
| AI Hub Team | System admins | Agent monitoring, pipeline debugging, memory inspection, trait configuration |

---

## 2. Feature Requirements

### 2.1 Core Features

#### F1: Authentication & Authorization
- JWT-based login with role-based access control (admin, cs_manager, cs_engineer, viewer)
- **Acceptance Criteria:**
  - Login returns access (15min) + refresh (7d) JWT tokens
  - Protected endpoints return 401 for unauthenticated users
  - Role-based middleware restricts admin-only endpoints
  - Passwords hashed with bcrypt

#### F2: Command Center Dashboard (Spatial)
- Central mission control — immersive full-viewport view with 3D elements and live agent activity
- **User Stories:**
  - As a CS manager, I see the overall health of our portfolio the moment I log in, through an immersive 3D visualization
  - As any user, I see agents as glowing nodes on a rotating sphere organized by their 4-tier hierarchy with live data pulses
  - As any user, I see events flowing as particle streams through the hierarchy
  - As a CS manager, I see active pipeline runs and their current stages at a glance
  - As any user, I see recent inter-agent messages highlighting current delegation activity
- **Acceptance Criteria:**
  - 4 Floating Metric Orbs (3D holographic spheres with parallax) showing Total Customers, At-Risk, Open Tickets, Avg Health
  - Neural Sphere: 3D rotating globe with **13 agent nodes grouped by tier** (inner ring = Tier 1, middle ring = Tier 2, outer ring = Tier 3, center core = Tier 4), pulsing connections along hierarchy lines, click-to-zoom agent detail
  - Data Flow Rivers: particle streams showing event routing from sources through the 4-tier hierarchy
  - Health Terrain: 3D topographic map — customer health as peaks/valleys, interactive
  - Live Pulse: EKG-style event timeline (not a list)
  - Active Pipelines strip: compact progress bars showing currently running agent pipelines with stage indicators
  - Recent Messages highlight: latest 3-5 inter-agent messages showing delegation activity
  - All real-time via WebSocket (including pipeline:* and delegation:* events)
  - 2D fallbacks for all 3D elements (progressive enhancement)
  - Orbital Nav at bottom-center for navigation

#### F3: Customer Observatory
- Portfolio view with three modes: Solar System (3D), Premium Grid (2D), Data Table
- **Acceptance Criteria:**
  - Solar System: customers as orbiting planets by tier, size by importance, color by health
  - Premium Grid: cards with 3D tilt on hover, health rings, severity ribbons
  - Data Table: sortable columns, row hover lift effect
  - Quick Intel Panel: appears on customer hover/select with summary stats + "Deep Dive" link
  - Search + filters (risk level, CS owner, sort)
  - View toggle between all three modes

#### F4: Customer Deep Dive (Scroll Journey)
- Immersive vertical scroll experience through a customer's complete story
- **Acceptance Criteria:**
  - Hero section: customer name in large display type, 3D rotating health ring, key stats
  - Health Story: animated area chart (draws on scroll), 6 radial gauge meters, risk flags
  - Deployment DNA: interactive node-link diagram showing tech setup
  - Customer Journey: horizontal scrollable timeline of all significant events
  - Intelligence Panels: 3 columns (Open Tickets, Recent Calls, Similar Issues via RAG)
  - All sections animate/reveal on scroll (IntersectionObserver)

#### F5: Agent Hierarchy & Nexus
- Interactive 4-tier hierarchy visualization of all 13 named agents with live pipeline activity
- **User Stories:**
  - As a CS manager, I see the full organizational hierarchy of my AI team — who reports to whom, which lane they belong to, and what they're currently working on
  - As a CS engineer, I click on any agent to see their profile, personality, tools, traits, and recent execution history
  - As any user, I see live delegation flow — tasks moving from Orchestrator to Lane Leads to Specialists in real-time
  - As an admin, I access sub-views for pipeline execution, message board, memory, execution traces, and workflows from within the Agent Nexus page
- **Acceptance Criteria:**
  - 4-tier hierarchy tree: Naveen (Tier 1) → Rachel/Damon/Priya (Tier 2) → 8 Specialists (Tier 3) → Atlas (Tier 4), with tier-coded colors and lane grouping
  - Live delegation flow: animated connections showing current task assignments flowing through the hierarchy
  - Agent nodes: size by current workload, pulse rate by activity, color by tier
  - Click agent → Agent Profile Card with: name, personality, tier badge, lane color, tools list, traits list, recent stats
  - Agent Brain Panel: slides up with reasoning log (terminal-style), mini stat gauges, execution history
  - Sub-navigation tabs within this page: Hierarchy (default), Pipeline, Messages, Memory, Traces, Workflows
  - Real-time status via WebSocket

#### F6: Signal Intelligence (Fathom Insights)
- Call insights with waveform/radio signal aesthetic
- **Acceptance Criteria:**
  - Sentiment Spectrum: full-width animated waveform chart (sentiment over time)
  - Insight cards: mini waveform decoration, expandable summary, action item checklist, decisions, risks
  - Action Tracker: floating side panel with pending/overdue/completed counts
  - Sentiment filter, customer filter, date range
  - Action item checkbox toggles status via API

#### F7: Ticket Warroom
- Dual-mode: Constellation (3D) + Warroom Table (2D)
- **Acceptance Criteria:**
  - Constellation: tickets as 3D stars (X=severity, Y=age, Z=status), SLA-breaching stars pulse red
  - Warroom Table: premium table with severity ribbons, live SLA countdowns (ticking per second), AI TRIAGED row shimmer
  - Ticket Detail Drawer: slides from right with AI triage, diagnostics, escalation summary, similar tickets (RAG)
  - Toggle between Constellation and Table views

#### F8: Analytics Lab
- Interactive data exploration with cross-filtering charts
- **Acceptance Criteria:**
  - Health Heatmap: calendar heatmap (customers × days)
  - Ticket Velocity: stacked area chart by severity
  - Sentiment River: stream graph
  - Agent Throughput: radial bar chart
  - Cross-filtering: selecting data in any chart highlights related data in all others
  - Report list + "Generate Report" modal (weekly/monthly/QBR)

#### F9: Real-Time WebSocket System
- **Acceptance Criteria:**
  - WebSocket maintained across page navigation
  - **Existing events:** agent_status, event_processed, new_alert, health_update, ticket_triaged, insight_ready
  - **New pipeline events:** pipeline:stage_started, pipeline:stage_completed, pipeline:tool_called
  - **New delegation events:** delegation:task_assigned, delegation:deliverable, delegation:escalation
  - **New memory events:** memory:knowledge_published
  - Toast notifications with particle trail animation for critical alerts
  - Dashboard and Agent Nexus components update in-place from all event types

#### F10: Navigation System (Orbital + Command Palette)
- **Acceptance Criteria:**
  - Orbital Nav: curved arc at bottom-center, 7 items, active item centered + enlarged
  - Command Palette: Cmd+K opens fuzzy search across Pages, Customers, Tickets, Agents, Pipeline Runs, Messages, Actions
  - Breadcrumb Trail: floating at top-left with animated connecting dots
  - No sidebar anywhere in the application

#### F11: Seed Data System
- **Acceptance Criteria:**
  - 10 customers, 50+ tickets, 100+ insights, 30 days health history, agent logs, alerts, action items
  - Hierarchy seed data: sample pipeline execution traces, inter-agent messages, episodic memories, shared knowledge entries
  - Single CLI command: `python -m app.utils.seed`

#### F12: Pipeline Execution Viewer (sub-view within Agent Nexus)
- Real-time visualization of multi-round agent pipeline runs
- **User Stories:**
  - As a CS manager, I see which pipeline stages each agent is currently executing so I can monitor work in progress
  - As an admin, I drill into any pipeline run to see stage-by-stage details including tool calls, memory retrievals, and timing
  - As any user, I see pipeline failures and quality gate rejections with clear reasons
- **Acceptance Criteria:**
  - Pipeline run list: shows active and recent pipeline executions with agent name, event trigger, status, and duration
  - Stage timeline: horizontal progress indicator showing all stages (perceive → retrieve → think → act → reflect → quality_gate → finalize) with current stage highlighted
  - Stage detail panel: shows input summary, output summary, tools called, tokens used, duration for each stage
  - Quality gate visualization: shows pass/fail status, evaluator feedback, and retry count
  - Real-time updates via WebSocket pipeline:* events
  - Filter by agent, tier, status, date range

#### F13: Inter-Agent Message Board (sub-view within Agent Nexus)
- Feed of all inter-agent communications with threading and type filtering
- **User Stories:**
  - As a CS manager, I see how my agents are collaborating — who delegated what to whom, and what came back
  - As an admin, I trace a delegation chain from Orchestrator → Lane Lead → Specialist and back
  - As a CS engineer, I filter messages by type (escalations, deliverables) to quickly find relevant communications
- **Acceptance Criteria:**
  - Message feed: chronological list of messages with agent avatar, name, type badge, content preview
  - Message types visually differentiated: task_assignment (blue), deliverable (green), request (amber), escalation (red), feedback (violet)
  - Thread view: click any message to see the full thread (assignment → specialist work → deliverable → feedback)
  - Filters: by message type, agent, event, lane, date range
  - Delegation chain trace: visual flow showing the full delegation path for any event
  - Real-time updates via WebSocket delegation:* events

#### F14: Memory Inspector (sub-view within Agent Nexus)
- Browse and search the 3-tier agent memory system
- **User Stories:**
  - As an admin, I browse an agent's episodic memories to understand what past experiences inform its decisions
  - As a CS manager, I explore the shared knowledge pool per lane to see what the team has learned
  - As any user, I search across all memory tiers by semantic similarity
- **Acceptance Criteria:**
  - Episodic memory view: timeline of an agent's past execution summaries, sorted by recency, with importance scores
  - Semantic memory view: knowledge pool browser organized by lane (Support, Value, Delivery, Global), with tags and importance
  - Working memory view: current scratchpad contents for agents with active pipeline runs
  - Semantic search: search across all memory tiers with results ranked by the tri-factor score (35% relevance + 25% recency + 40% importance)
  - Memory detail: expand any entry to see full content, source agent, linked execution, and metadata
  - Filter by agent, lane, importance threshold, date range

#### F15: Execution Trace Viewer (sub-view within Agent Nexus)
- Detailed drill-down into any completed agent pipeline execution
- **User Stories:**
  - As an admin, I inspect exactly what happened at each stage of an agent's pipeline run for debugging
  - As a CS manager, I see the full chain of tool calls, memory retrievals, and Claude interactions for any execution
- **Acceptance Criteria:**
  - Execution summary: agent name, tier, event trigger, total duration, total tokens, status
  - Stage-by-stage breakdown: expandable cards for each pipeline stage showing input, output, tools called, timing
  - Tool call detail: for each tool call — tool name, arguments, result, duration
  - Token usage breakdown: tokens per stage with a total summary
  - Confidence scores: from the reflect stage, displayed per execution
  - Navigation: link from any pipeline run in F12 to the full trace in F15

#### F16: Workflow Viewer (sub-view within Agent Nexus)
- Visualization of how events flow through the agent hierarchy
- **User Stories:**
  - As a CS manager, I see the standard workflow for different event types (ticket → triage → troubleshoot → escalate)
  - As an admin, I see which agents are involved in each workflow and their typical delegation patterns
- **Acceptance Criteria:**
  - Workflow definitions: shows all configured workflows from YAML (e.g., ticket_workflow, call_workflow, health_workflow)
  - Flow diagram: visual representation of event → Tier 1 → Tier 2 → Tier 3 routing with agent names
  - Active instances: list of currently running workflow instances with progress indicators
  - Historical view: past completed workflows with duration and outcome

### 2.2 Post-MVP Features

| Feature | Description |
|---------|-------------|
| Slack Integration | Risk alerts to channels, @cs-bot commands, action item reminders |
| Jira Webhooks | Real-time ticket sync, auto-create, bi-directional status |
| Advanced RAG | Multi-turn queries, cross-customer patterns, resolution engine |
| Email Drafts | Auto-generate customer-facing emails from insights |
| Trait Marketplace | Pluggable trait library — add new agent behaviors via config |
| Cross-Lane Collaboration | Automatic cross-lane request routing when agents detect cross-cutting issues |
| Memory Consolidation | Automatic summarization of old episodic memories into high-level insights |

---

## 3. Non-Functional Requirements

### 3.1 Performance
- Dashboard initial load (with 3D): < 4 seconds
- Dashboard initial load (2D fallback): < 2 seconds
- API response times: < 500ms (CRUD), < 5s (AI-powered single stage)
- Full pipeline execution (all stages): < 30s for Tier 3, < 60s for Tier 2, < 120s for full Tier 1 delegation chain
- Memory retrieval (episodic + semantic): < 500ms per query
- WebSocket latency: < 100ms
- 3D scenes: 60fps on M1 MacBook / RTX 2060 equivalent
- Three.js bundle: lazy-loaded, code-split, NOT in main bundle
- Support 50 concurrent users

### 3.2 Security
- JWT auth (access 15min + refresh 7d)
- bcrypt passwords, RBAC on all endpoints
- CORS restricted, Pydantic validation, parameterized queries
- Rate limiting on auth endpoints
- Fathom webhook signature verification (HMAC-SHA256)

### 3.3 Design Requirements
- **Theme:** Dark mode only — "Deep Ocean Bioluminescence"
- **Background:** Void black (#020408) with animated nebula gradient mesh, NOT navy
- **Accents:** Two-tone — electric teal (#00F5D4) + rich violet (#8B5CF6)
- **Tier Colors:** Tier 1 = teal (#00F5D4), Tier 2 = violet (#8B5CF6), Tier 3 = cyan (#22D3EE), Tier 4 = slate (#64748B)
- **Typography:** Space Grotesk (display), IBM Plex Mono (data), Inter (body)
- **Surfaces:** Frosted Depth — three opacity levels (near 0.65, mid 0.45, far 0.25) with backdrop-blur(20px)
- **Navigation:** Orbital arc at bottom-center, no sidebar. Cmd+K palette.
- **3D Elements:** Neural Sphere (13 agents in 4 tiers), Health Terrain, Floating Orbs, Data Flow Rivers, Ticket Constellation
- **Progressive Enhancement:** All 3D has 2D fallbacks. Respects prefers-reduced-motion.
- **Responsive:** Full 3D > 1440px, simplified 3D 1024-1440, premium 2D < 1024, mobile tab bar < 768

### 3.4 Accessibility
- Reduce Motion toggle in Settings
- prefers-reduced-motion media query respected (3D → 2D)
- All statuses use shape + icon + color (never color alone)
- Keyboard navigation for all 3D scenes
- Screen reader labels on all canvas elements

---

## 4. Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18 + Vite | |
| Styling | Tailwind CSS + custom CSS | Void/glow effects |
| State | Zustand | |
| Routing | React Router v6 | |
| HTTP | Axios | |
| **3D** | Three.js + @react-three/fiber + drei | Neural sphere, terrain, orbs |
| **Animation** | Framer Motion + GSAP | Page transitions, scroll, 3D camera |
| **Charts** | Recharts + D3 | Recharts (simple), D3 (heatmap, river, radial) |
| Interactions | @dnd-kit, fuse.js | Drag-drop, fuzzy search |
| Backend | FastAPI | |
| Database | PostgreSQL 16 | |
| Vector DB | ChromaDB | RAG + episodic/semantic memory |
| ORM | SQLAlchemy 2.0 + Alembic | |
| Auth | python-jose (JWT) | |
| Task Queue | Celery + Redis | Pipeline execution |
| LLM | Claude API (claude-sonnet-4-5-20250929) | With tool_use for agent tools |
| HTTP Client | httpx | Fathom API integration |
| Config | PyYAML | Agent profiles, org structure, pipelines |
| Testing | Pytest + Playwright | |

---

## 5. System Architecture

### 5.1 The 4-Tier Agent Hierarchy (13 Agents)

```
┌──────────────────────────────────────────────────────┐
│                    TIER 1: SUPERVISOR                  │
│            Naveen Kapoor — CS Orchestrator             │
│    Decomposes → Delegates → Evaluates → Synthesizes   │
└───────────┬──────────────┬──────────────┬────────────┘
            │              │              │
   ┌────────▼────┐  ┌──────▼─────┐  ┌────▼──────┐
   │   TIER 2    │  │   TIER 2   │  │  TIER 2   │
   │   Rachel    │  │   Damon    │  │   Priya   │
   │   Torres    │  │   Reeves   │  │   Mehta   │
   │ Support Lead│  │ Value Lead │  │Delivery Ld│
   └──┬──┬──┬────┘  └──┬──┬──┬──┘  └──┬──┬─────┘
      │  │  │          │  │  │        │  │
      ▼  ▼  ▼          ▼  ▼  ▼        ▼  ▼
   ┌───────────────────────────────────────────────┐
   │            TIER 3: SPECIALISTS                 │
   │                                                │
   │  Support Lane:          Value Lane:            │
   │   Kai Nakamura          Dr. Aisha Okafor       │
   │   Leo Petrov            Jordan Ellis           │
   │   Maya Santiago         Sofia Marquez          │
   │                                                │
   │  Delivery Lane:                                │
   │   Ethan Brooks                                 │
   │   Zara Kim                                     │
   └───────────────────┬───────────────────────────┘
                       │
   ┌───────────────────▼───────────────────────────┐
   │             TIER 4: FOUNDATION                 │
   │  Atlas — Customer Memory Manager               │
   │  (Provides context to ALL agents)              │
   └────────────────────────────────────────────────┘
```

**Full Agent Team:**

| ID | Name | Tier | Lane | Role | Tools | Traits |
|---|---|---|---|---|---|---|
| `cso_orchestrator` | Naveen Kapoor | 1 | — | CS Manager | query_customer_db, search_knowledge_base, read_agent_output | strategic_oversight, quality_evaluation, delegation, customer_sentiment |
| `support_lead` | Rachel Torres | 2 | Support | Support Operations Lead | query_customer_db, get_ticket_details, check_sla_status, read_agent_output | workflow_coordination, delegation, synthesis, customer_sentiment |
| `value_lead` | Damon Reeves | 2 | Value | Value & Insights Lead | query_customer_db, query_health_scores, read_call_transcript, read_agent_output | workflow_coordination, delegation, synthesis, customer_sentiment |
| `delivery_lead` | Priya Mehta | 2 | Delivery | Delivery Operations Lead | query_customer_db, read_agent_output | workflow_coordination, delegation, synthesis, customer_sentiment |
| `triage_agent` | Kai Nakamura | 3 | Support | Ticket Triage Specialist | get_ticket_details, search_similar_tickets, check_sla_status | confidence_scoring, escalation_detection, sla_awareness, customer_sentiment |
| `troubleshooter_agent` | Leo Petrov | 3 | Support | Troubleshooting Engineer | get_ticket_details, search_similar_tickets, search_knowledge_base, query_customer_db | confidence_scoring, escalation_detection, customer_sentiment |
| `escalation_agent` | Maya Santiago | 3 | Support | Escalation Manager | get_ticket_details, check_sla_status, send_alert, create_action_item | escalation_detection, sla_awareness, customer_sentiment |
| `health_monitor_agent` | Dr. Aisha Okafor | 3 | Value | Customer Health Analyst | query_health_scores, query_customer_db, search_knowledge_base, send_alert | confidence_scoring, customer_sentiment |
| `call_intel_agent` | Jordan Ellis | 3 | Value | Call Intelligence Analyst | read_call_transcript, query_customer_db, create_action_item, publish_knowledge | confidence_scoring, customer_sentiment |
| `qbr_agent` | Sofia Marquez | 3 | Value | QBR & Review Specialist | query_customer_db, query_health_scores, read_call_transcript, write_report | confidence_scoring, customer_sentiment |
| `sow_agent` | Ethan Brooks | 3 | Delivery | Scope & SOW Specialist | query_customer_db, write_report, create_action_item | confidence_scoring, customer_sentiment |
| `deployment_intel_agent` | Zara Kim | 3 | Delivery | Deployment Intelligence Analyst | query_customer_db, search_knowledge_base, publish_knowledge | confidence_scoring, customer_sentiment |
| `customer_memory` | Atlas | 4 | — | Customer Memory Manager | query_customer_db, query_health_scores, search_knowledge_base | — |

### 5.2 Pipeline Execution

Every agent runs through a tier-specific multi-round pipeline instead of a single-shot Claude call:

```
perceive → retrieve → think → act → reflect → quality_gate → finalize
```

| Stage | What Happens | Agent Method |
|---|---|---|
| `perceive` | Read the task, add to working memory, traits fire on_perceive hooks | `agent.perceive(task)` |
| `retrieve` | Query episodic + semantic memory for relevant past context | `agent.retrieve(task)` |
| `think` | Reason about the task with all context (Claude call with tools available) | `agent.think(task, context)` |
| `act` | Produce output, may call multiple tools mid-conversation | `agent.act(task, context)` |
| `reflect` | Self-assess: confidence score, gaps, what might be missing | `agent.reflect(output)` |
| `quality_gate` | Higher-tier agent evaluates output quality; can loop back for rework (max 2x) | `evaluator.evaluate(output)` |
| `finalize` | Polish final output, format for consumption | `agent.finalize(outputs)` |

**Pipeline configurations per tier:**
- **Tier 1** (Orchestrator): perceive → retrieve → think → act → quality_gate → finalize (5 stages, strategy-focused)
- **Tier 2** (Lane Leads): perceive → retrieve → think → act → finalize (4 stages, coordination-focused)
- **Tier 3** (Specialists): perceive → retrieve → think → act → reflect (5 stages, execution-focused)
- **Tier 4** (Foundation): perceive → act (2 stages, service-focused)

### 5.3 3-Tier Memory System

| Memory Tier | Scope | Storage | Retrieval | Lifecycle |
|---|---|---|---|---|
| **Working Memory** (Scratchpad) | Current pipeline run only | In-process dict | Direct key access | Cleared after each run |
| **Episodic Memory** (Diary) | Per-agent, persistent | ChromaDB `episodic_memory` | Tri-factor: 35% relevance + 25% recency + 40% importance | Consolidation at 25+ entries |
| **Semantic Memory** (Shared Knowledge) | Per-lane, persistent | ChromaDB `shared_knowledge` | Semantic similarity search by lane | Long-term, cross-agent |

**How agents use memory:**
1. Task arrives → stored in **working memory**
2. Agent queries **episodic memory**: "Have I seen similar situations?"
3. Agent queries **semantic memory**: "What does the team know about this customer/issue?"
4. All context feeds into the `think` and `act` stages
5. After completing, agent writes execution summary to **episodic memory**
6. If agent discovers something broadly useful, it publishes to **semantic memory**

### 5.4 Inter-Agent Communication

Agents communicate via typed messages on a shared message board:

| Message Type | Direction | Example |
|---|---|---|
| `task_assignment` | Down (Lead → Specialist) | Rachel → Kai: "Triage this ticket and report severity" |
| `deliverable` | Up (Specialist → Lead) | Kai → Rachel: "Ticket triaged: severity 7, category: integration" |
| `request` | Sideways (Specialist ↔ Specialist) | Leo → Zara: "Can you check if a recent deployment caused this?" |
| `escalation` | Up (any → higher tier) | Maya → Rachel: "This needs Naveen's attention — customer threatening churn" |
| `feedback` | Down (Lead → Specialist) | Damon → Aisha: "Good analysis, but also check the call sentiment trend" |

Messages support **threading** — a task_assignment creates a thread, and all related deliverables, requests, and feedback link back to it. Full delegation chains are traceable.

### 5.5 Agent Tools (12+ via Claude tool_use)

| Tool | What It Does | Wraps |
|---|---|---|
| `query_customer_db` | Look up customer profile and history | SQLAlchemy queries |
| `query_health_scores` | Get health score timeline | Health score table |
| `search_similar_tickets` | Find similar past tickets via RAG | ChromaDB RAG |
| `search_knowledge_base` | Search across all knowledge | ChromaDB RAG |
| `read_call_transcript` | Get call insight details | Call insights table |
| `get_ticket_details` | Look up specific ticket | Tickets table |
| `check_sla_status` | Calculate SLA countdown | Ticket timestamps |
| `write_report` | Generate and save a report | Reports table |
| `create_action_item` | Create a follow-up action | Action items table |
| `send_alert` | Trigger an alert | Alerts table |
| `read_agent_output` | Read another agent's work | Agent logs table |
| `publish_knowledge` | Share a finding with the team | Shared knowledge pool |

### 5.6 Event-Driven Flow (Hierarchical Delegation)

```
Event (Jira/Fathom/Cron)
  │
  ▼
Tier 1: Naveen (Orchestrator)
  ├── perceive → retrieve → think → act (delegate)
  │
  ├───▶ Tier 2: Rachel (Support Lead)
  │       ├── perceive → think → act (coordinate)
  │       ├───▶ Tier 3: Kai (Triage) → pipeline → deliverable ──▶ Rachel
  │       ├───▶ Tier 3: Leo (Troubleshoot) → pipeline → deliverable ──▶ Rachel
  │       └── finalize → deliverable ──▶ Naveen
  │
  ├───▶ Tier 2: Damon (Value Lead)
  │       ├───▶ Tier 3: Aisha (Health) → pipeline → deliverable ──▶ Damon
  │       └── finalize → deliverable ──▶ Naveen
  │
  ▼
Tier 1: Naveen → quality_gate → finalize → Output
  │
  ▼
Tier 4: Atlas (Memory) — served context to every agent, received results back
  │
  ▼
WebSocket broadcast → Dashboard update
```

---

## 6. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pre-meeting prep time | 30-60 min → < 5 min | User survey |
| Ticket triage time | 15 min → < 2 min | Agent log timestamps |
| At-risk detection | 2 weeks earlier | Health alert timing |
| Call insight extraction | 100% of calls | Insight vs call count |
| QBR preparation | 2 days → 2 hours | User survey |
| Action item completion | > 80% rate | Status tracking |
| Pipeline execution quality | > 90% pass quality gate on first attempt | Execution trace data |
| Agent collaboration | Avg 3+ messages per event delegation chain | Message board analytics |
| Memory utilization | Agents retrieve episodic context for > 80% of tasks | Memory retrieval logs |
| Stakeholder "wow" factor | Executive buy-in on first demo | Demo feedback |

---

## 7. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| 3D performance on low-end devices | Progressive enhancement — 2D fallbacks always work, 3D lazy-loaded |
| Three.js bundle size | Code-split into separate chunks, lazy-load on demand |
| Claude API cost scaling (multi-stage pipeline) | Token tracking per stage, batch processing, cache frequent tool results, tier-appropriate pipeline depth |
| Pipeline latency (multiple Claude calls per event) | Parallel specialist execution within a lane, stage timeouts, Celery async execution |
| Inter-agent message volume | Message pruning, thread summarization, pagination on frontend |
| Memory growth (episodic + semantic) | Consolidation rules (summarize at 25+ entries), importance-based retention |
| YAML config complexity | Startup validation, profile loader validates all cross-references |
| Agent hallucination | Confidence scoring trait, quality gates, human-in-the-loop for low confidence |
| Fathom API reliability | Webhook + polling fallback, retry logic with exponential backoff |
| Data privacy | RBAC, audit logging, no PII in embeddings |

---

## 8. Development Phases

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 0: Fathom Integration | 1-2 days | Real Fathom API client, webhook receiver, historical sync — **COMPLETE** |
| Phase A: Documentation Update | 1-2 days | Rewrite PRD, WIREFRAMES, API_CONTRACT, DATABASE_SCHEMA, CLAUDE.md |
| Phase B: Foundation | 3-4 days | YAML configs, profile loader, tool registry, Claude tool_use, pipeline engine, execution logger |
| Phase C: Memory System | 1-2 days | 3-tier memory manager, 2 new ChromaDB collections, lane knowledge pools |
| Phase D: Traits + Reflection | 1-2 days | Trait registry, 9+ CS traits, reflection engine with tier-appropriate depth |
| Phase E: Message Board + Hierarchy | 2-3 days | Agent messages DB table, delegation chains, workflow YAML configs |
| Phase F: Agent Implementation | 3-4 days | Orchestrator (T1), 3 Lane Leads (T2), migrate 8 Specialists (T3), upgrade Memory Agent (T4) |
| Phase G: Frontend Redesign | 5-7 days | 6+ new pages/sub-views, new Zustand stores, WebSocket integration, hierarchy visualization |
| Phase H: Integration | 1-2 days | Celery pipeline tasks, new WebSocket events, feature flags, seed data |

**Total: 18-28 days**

**Dependency chain:** Phase 0 ✓ → Phase A → Phase B → Phases C/D/E (parallel) → Phase F → Phase G → Phase H

---

## 9. Stakeholders

| Person | Role | Interest |
|--------|------|----------|
| Kazi Sir | VP/Director | ROI, capability, team impact, visual impression |
| Ariza Zehra | AI Hub Lead | Technical feasibility, capacity |
| Vignesh / Chaitanya | CS Engineers | Daily usability, workflows |
| Priyank Tailang | QA | Testing, reliability |
| Ayushmaan Singh Naruka | Developer | Architecture, implementation |
| Divyam Garg | Developer | Co-development support |
