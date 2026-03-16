# REBUILD PLAN — CS Control Plane Agentic Architecture

> **What is this?** A step-by-step plan to upgrade our CS Control Plane from "single-shot" agents
> to a full multi-agent system with memory, tools, collaboration, and a 4-tier hierarchy.
>
> **How to read this:** Sections 1–5 give you the big picture. Sections 6–16 give you the details.
> Simple language throughout — no jargon without explanation.

---

## Table of Contents

1. [What We're Doing](#1-what-were-doing)
2. [What We Keep (Don't Rebuild)](#2-what-we-keep-dont-rebuild)
3. [What We Rebuild (Major Changes)](#3-what-we-rebuild-major-changes)
4. [What We Create New (~40 New Files)](#4-what-we-create-new-40-new-files)
5. [The 9 Phases at a Glance](#5-the-9-phases-at-a-glance)
6. [Phase 0: Fathom Integration — Get Real Data Flowing (1–2 days)](#6-phase-0-fathom-integration--get-real-data-flowing-1-2-days)
7. [Phase A: Documentation Update (1–2 days)](#7-phase-a-documentation-update-1-2-days)
8. [Phase B: Foundation (3–4 days)](#8-phase-b-foundation-3-4-days)
9. [Phase C: Memory System (1–2 days)](#9-phase-c-memory-system-1-2-days)
10. [Phase D: Traits + Reflection (1–2 days)](#10-phase-d-traits--reflection-1-2-days)
11. [Phase E: Message Board + Hierarchy (2–3 days)](#11-phase-e-message-board--hierarchy-2-3-days)
12. [Phase F: Agent Implementation (3–4 days)](#12-phase-f-agent-implementation-3-4-days)
13. [Phase G: Frontend — Complete Redesign (5–7 days)](#13-phase-g-frontend--complete-redesign-5-7-days)
14. [Phase H: Integration (1–2 days)](#14-phase-h-integration-1-2-days)
15. [The 4-Tier Hierarchy Explained](#15-the-4-tier-hierarchy-explained)
16. [File Inventory](#16-file-inventory)
17. [Timeline Summary](#17-timeline-summary)

---

# AGENT IDENTITIES — Meet the Team

Every agent has a name, personality, and working style — just like a real CS team.
This makes the system feel alive and makes logs/messages human-readable.

| ID | Name | Tier | Role | Personality |
|---|---|---|---|---|
| `cso_orchestrator` | **Naveen Kapoor** | 1 | CS Manager | Strategic, composed, sees the big picture. Delegates decisively and holds the team to high standards. Speaks concisely — every word matters. Former management consultant who values structured thinking. |
| `support_lead` | **Rachel Torres** | 2 | Support Operations Lead | Methodical, thorough, protective of her team. Runs a tight ship — no ticket falls through the cracks. Has a dry sense of humor under pressure. Tracks SLAs like a hawk. |
| `value_lead` | **Damon Reeves** | 2 | Value & Insights Lead | Analytical, data-driven, quietly intense. Obsessed with customer health patterns. Can spot a churn signal from across the dashboard. Prefers graphs over words. |
| `delivery_lead` | **Priya Mehta** | 2 | Delivery Operations Lead | Detail-oriented, organized, the one who remembers every deadline. Makes sure scope, SOWs, and deployments stay on track. Communicates in crisp bullet points. |
| `triage_agent` | **Kai Nakamura** | 3 | Ticket Triage Specialist | Fast, precise, pattern-recognizing. Classifies tickets in seconds. Has an almost instinctive sense for severity. Collects similar-ticket knowledge like a librarian. |
| `troubleshooter_agent` | **Leo Petrov** | 3 | Troubleshooting Engineer | Curious, persistent, loves root-cause analysis. Won't stop digging until the "why" is answered. Thinks in dependency chains. Gets excited by obscure edge cases. |
| `escalation_agent` | **Maya Santiago** | 3 | Escalation Manager | Calm under fire, diplomatic, decisive about urgency. Knows exactly when something needs to go up the chain and how to frame it. Acts as the team's alarm system. |
| `health_monitor_agent` | **Dr. Aisha Okafor** | 3 | Customer Health Analyst | Meticulous, trend-obsessed, thinks in time series. Treats every health score like a patient chart. Flags anomalies before they become crises. Prefers longitudinal data over snapshots. |
| `call_intel_agent` | **Jordan Ellis** | 3 | Call Intelligence Analyst | Empathetic, linguistically sharp, reads between the lines. Catches tone shifts, unspoken frustrations, and competitor mentions that others miss. Turns conversations into structured intelligence. |
| `qbr_agent` | **Sofia Marquez** | 3 | QBR & Review Specialist | Strategic, narrative-focused, excellent at synthesis. Turns scattered data into a compelling customer story. Knows that a great QBR is half data, half storytelling. |
| `sow_agent` | **Ethan Brooks** | 3 | Scope & SOW Specialist | Precise, contract-minded, detail-obsessed. Every deliverable, timeline, and boundary must be crystal clear. Catches scope creep before it starts. |
| `deployment_intel_agent` | **Zara Kim** | 3 | Deployment Intelligence Analyst | Technical, risk-aware, tracks deployment health like vital signs. Correlates deployment events with customer issues. Always asks "what changed recently?" |
| `customer_memory` | **Atlas** | 4 | Customer Memory Manager | Not a persona — a system. The institutional memory of the entire CS operation. Serves context to every agent, never forgets a customer interaction, and connects the dots across time. Named after the titan who holds up the world. |

> **Why names matter:** When you see a message from "Maya Santiago" saying "ESCALATION: Acme Corp
> threatening churn — renewal in 45 days", it's immediately clear who is speaking, what their
> role is, and why they're raising the alarm. Named agents make logs, traces, and the message
> board feel like a real team collaborating.

---

# PART 1 — THE BIG PICTURE

---

## 1. What We're Doing

### The Problem

Right now, every agent in our system works like a vending machine:

1. Something happens (a ticket comes in, a health check triggers)
2. We send ONE message to Claude with all the context stuffed in
3. Claude sends back ONE JSON response
4. We save it to the database
5. Done. Agent forgets everything.

This is what we call **"single-shot"** agents. They have no memory of past work, can't use tools,
can't talk to each other, and can't think in multiple steps. They're basically fancy API wrappers.

### The Goal

We want agents that work like a **real CS team**:

- **They remember** — An agent working on Customer X remembers what happened last week with
  that customer, what other agents found, and what worked before
- **They use tools** — Instead of guessing, agents can look up real data: query the database,
  search past tickets, check health scores, read call transcripts
- **They think in steps** — Instead of one shot, agents go through a pipeline:
  perceive → retrieve context → think → act → reflect on what they did
- **They collaborate** — Agents can send messages to each other, delegate tasks up/down the
  chain, and share knowledge across lanes
- **They have a hierarchy** — Just like a real team: a CS Manager (Orchestrator) delegates to
  Lane Leads, who delegate to Specialists, who rely on a shared Foundation layer

### The Analogy

Think of it like upgrading from a **call center where everyone works alone with no notes**
to a **full CS organization** where:

- **Naveen Kapoor** (CS Manager) assigns work and evaluates quality
- **Rachel Torres** (Support), **Damon Reeves** (Value), **Priya Mehta** (Delivery) manage their lanes
- 8 named specialists do the actual work (Kai, Leo, Maya, Aisha, Jordan, Sofia, Ethan, Zara)
- Everyone shares **Atlas** (Customer Memory) and a knowledge base

### What Changes in Practice

| Before (Now) | After (Rebuild) |
|---|---|
| Agent gets a task → one Claude call → JSON out → save | Agent gets a task → perceives → recalls memories → thinks with tools → acts → reflects → quality check |
| Orchestrator is a simple router ("if ticket → triage agent") | Orchestrator is a supervisor: decomposes problems, delegates to Lane Leads, evaluates output quality, synthesizes final answers |
| Agents have no memory | 3 tiers of memory: Working (scratchpad), Episodic (diary of past runs), Semantic (shared knowledge) |
| Agents can't use tools | 12+ tools: query DB, search RAG, check health scores, read transcripts, write reports |
| Agents don't talk to each other | Message board with threads: task assignments flow down, deliverables flow up, requests go sideways |
| Agent behavior is hardcoded in Python | Agent personality, traits, and tools defined in YAML config files |
| One pipeline for all | Different pipelines per tier: Orchestrator gets strategy stages, Specialists get execution stages |
| Frontend shows basic cards and tables | Frontend shows live agent hierarchy, pipeline execution, message threads, memory inspector |

---

## 2. What We Keep (Don't Rebuild)

The good news: **a lot of our infrastructure is solid and stays as-is.** We're not starting from
zero — we're keeping the foundation and rebuilding the brain on top.

### 2.1 All 10 Database Tables — KEEP

Every table we've built stays. They represent real business data:

| Table | Records | Purpose | Status |
|---|---|---|---|
| `users` | Auth users | Login, JWT tokens | Keep as-is |
| `customers` | Customer profiles | Core entity | Keep as-is |
| `health_scores` | Daily health data | Time-series scores | Keep as-is |
| `tickets` | Jira-style tickets | Support workflow | Keep as-is |
| `call_insights` | Fathom analysis | Call intelligence | Keep as-is |
| `agent_logs` | Agent run history | What agents did | Keep as-is |
| `events` | Event queue | Triggers for agents | Keep as-is |
| `alerts` | Alert records | Threshold warnings | Keep as-is |
| `action_items` | Tracked actions | Follow-up items | Keep as-is |
| `reports` | Generated reports | Analytics output | Keep as-is |

We'll ADD 2 new tables (agent_execution_rounds, agent_messages) — but nothing existing changes.

### 2.2 Database Layer — KEEP

All of this stays untouched:

- **`database.py`** — Async engine (asyncpg), sync engine (psycopg2), Neon SSL config,
  connection pooling, session factories
- **`alembic/`** — Migration system, env.py, version files
- **All 10 SQLAlchemy models** in `models/` directory

### 2.3 ChromaDB Client — KEEP

- **`chromadb_client.py`** — Persistent client, 3 existing collections
  (customer_interactions, ticket_analysis, knowledge_base)
- We'll add 2 new collections (episodic_memory, shared_knowledge) but existing ones stay

### 2.4 All Pydantic Schemas — KEEP

All 13 schema files stay as-is. They define request/response shapes:

```
schemas/
├── user.py          ├── health_score.py
├── customer.py      ├── ticket.py
├── call_insight.py  ├── agent_log.py
├── event.py         ├── alert.py
├── action_item.py   ├── report.py
├── dashboard.py     ├── rag.py
└── agent.py
```

We'll add new schemas for pipeline execution, messages, and memory — but nothing existing changes.

### 2.5 All API Routers — KEEP

All 11 routers stay. They serve the frontend and external integrations:

```
routers/
├── auth.py          ├── users.py
├── customers.py     ├── health.py
├── tickets.py       ├── call_insights.py
├── agents.py        ├── events.py
├── alerts.py        ├── dashboard.py
└── rag.py
```

We'll add new routers (pipeline execution, messages, memory inspector) — but existing ones stay.

### 2.6 Auth + Middleware — KEEP

- **JWT authentication** (login, refresh, token validation)
- **Auth middleware** (route protection, user extraction)
- **Security utils** (password hashing, token creation)

### 2.7 WebSocket Manager — KEEP

- **`websocket_manager.py`** — Connection management, room-based broadcasting
- We'll add new event types (pipeline progress, delegation events) — but the manager stays

### 2.8 Celery + Redis — KEEP

- **`tasks/celery_app.py`** — Celery configuration, Redis broker connection
- We'll change the task definitions — but the infrastructure stays

### 2.9 Seed Data — KEEP

- **`utils/seed.py`** — 958 lines of demo data
- We'll add new seed data for the hierarchy — but existing data stays

### 2.10 External Service Configs — KEEP

- **`config.py`** — Settings from .env, all connection strings, API keys

---

## 3. What We Rebuild (Major Changes)

These files exist today but need significant changes to support the new architecture.

### 3.1 BaseAgent → Pipeline-Aware Agent

**Current:** `backend/app/agents/base_agent.py` (110 lines)

```python
# What it does now:
class BaseAgent:
    def __init__(self, agent_type, name, description):
        self.agent_type = agent_type    # Just a label

    async def execute(self, task_data):
        # One Claude call → parse JSON → return
        result = await claude_service.generate(prompt)
        return json.loads(result)
```

**What it becomes:** A pipeline-aware agent with tier support, memory, tools, and traits.
The agent runs through multiple stages instead of one shot. Details in Phase B.

### 3.2 Orchestrator → Tier 1 Supervisor

**Current:** `backend/app/agents/orchestrator.py` (124 lines)

```python
# What it does now:
class Orchestrator:
    async def route_event(self, event):
        # Simple if/else routing
        if event.type == "ticket": return triage_agent
        if event.type == "call": return call_intel_agent
        # ...
```

**What it becomes:** A full supervisor agent (Tier 1) that:
- Reads the event and decomposes it into subtasks
- Delegates subtasks to the right Lane Lead
- Evaluates the quality of returned work
- Synthesizes final output from all lane results
- Uses its own pipeline with strategy and synthesis stages

### 3.3 ClaudeService → Tool-Use Enabled

**Current:** `backend/app/services/claude_service.py` (79 lines)

```python
# What it does now:
class ClaudeService:
    async def generate(self, system_prompt, user_message):
        # Simple message in → text out
        response = await client.messages.create(
            model=model, system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
```

**What it becomes:** A service that supports Claude's tool_use API:
- `generate_with_tools(system_prompt, messages, tools)` — sends tool definitions,
  handles tool_use responses, calls the tool, sends result back, loops until done
- Agents can now "call functions" mid-conversation instead of guessing

### 3.4 All 8 Specialist Agents → Pipeline Agents

Every agent currently has its system prompt hardcoded in Python and runs as one shot.
All 8 will be migrated to:

1. **System prompts move to YAML** — personality, traits, tools, and instructions
   defined in `config/agent_profiles.yaml`
2. **Single-shot → pipeline execution** — each agent runs through the pipeline stages
3. **Memory integration** — agents read from and write to the 3-tier memory system
4. **Tool access** — agents can call their assigned tools during the "act" stage

**Agents being migrated:**

| Agent | Current Lines | What Changes |
|---|---|---|
| Health Monitor | ~130 | Adds memory recall, tool calls for health data, reflection |
| Triage Agent | ~175 | Already uses RAG — adds pipeline, memory, escalation trait |
| Call Intel | ~190 | Adds transcript tool, sentiment trait, memory write-back |
| Troubleshooter | ~145 | Adds RAG tool, similar-ticket search, confidence trait |
| Escalation Manager | ~115 | Adds SLA-awareness trait, delegation chain support |
| QBR Generator | ~185 | Adds multi-source data gathering via tools, synthesis pipeline |
| SOW Agent | ~180 | Adds template tools, approval workflow via messages |
| Deployment Intel | ~165 | Adds deployment data tool, risk assessment trait |

### 3.5 Memory Agent → Tier 4 Foundation

**Current:** A basic agent that stores/retrieves customer context.

**What it becomes:** The Tier 4 Foundation layer — a 3-tier memory manager that ALL other
agents rely on. It manages working memory (scratchpad), episodic memory (past runs stored
in ChromaDB), and semantic memory (shared knowledge pools per lane).

### 3.6 Celery Tasks → Pipeline-Aware Execution

**Current:** Simple task wrappers that call `agent.execute()`.

**What they become:** Tasks that run the full pipeline engine for an agent, tracking each
round, supporting mid-execution tool calls, and broadcasting progress via WebSocket.

---

## 4. What We Create New (~40 New Files)

These are entirely new files and systems that don't exist today.

### 4.1 The 4-Tier Agent Hierarchy

This is the biggest new concept. Instead of 10 flat agents, we build a 4-level organization:

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
   │  Support Lane (Rachel's team):                 │
   │    • Kai Nakamura — Triage Specialist          │
   │    • Leo Petrov — Troubleshooting Engineer     │
   │    • Maya Santiago — Escalation Manager        │
   │                                                │
   │  Value Lane (Damon's team):                    │
   │    • Dr. Aisha Okafor — Health Analyst         │
   │    • Jordan Ellis — Call Intel Analyst          │
   │    • Sofia Marquez — QBR Specialist            │
   │                                                │
   │  Delivery Lane (Priya's team):                 │
   │    • Ethan Brooks — SOW Specialist             │
   │    • Zara Kim — Deployment Intel Analyst       │
   └───────────────────┬───────────────────────────┘
                       │
   ┌───────────────────▼───────────────────────────┐
   │             TIER 4: FOUNDATION                 │
   │                                                │
   │  • Atlas — Customer Memory Manager             │
   │  • RAG / Knowledge Base                        │
   │                                                │
   │  (Provides context to ALL agents)              │
   └────────────────────────────────────────────────┘
```

**How it works:**
- An event comes in (e.g., a new Jira ticket)
- **Tier 1 (Orchestrator)** reads it, decides which lane(s) need to handle it
- **Tier 2 (Lane Lead)** receives the task, breaks it down for their specialists
- **Tier 3 (Specialists)** do the actual work (triage, troubleshoot, etc.)
- **Tier 4 (Foundation)** provides memory and knowledge to everyone
- Results flow back up: Specialists → Lane Lead → Orchestrator → Final output

### 4.2 YAML Configuration System (3 new files)

Instead of hardcoding agent behavior in Python, we define everything in YAML:

**`config/agent_profiles.yaml`** — 13 agent profiles, each with:
```yaml
cso_orchestrator:
  name: "Naveen Kapoor"
  codename: "CS Orchestrator"
  tier: 1
  role: "CS Manager"
  personality: |
    Strategic, composed, sees the big picture. Delegates decisively
    and holds the team to high standards. Speaks concisely — every
    word matters. Former management consultant who values structured thinking.
  system_instruction: |
    You are Naveen Kapoor, CS Manager at HivePro. You receive
    events and decide how to delegate work across your three lane leads...
  traits:
    - strategic_oversight
    - quality_evaluation
    - delegation
  tools:
    - query_customer_db
    - search_knowledge_base
    - read_agent_output
  expertise:
    - "Customer success strategy"
    - "Cross-functional coordination"
```

**`config/org_structure.yaml`** — Hierarchy, lanes, reporting lines:
```yaml
organization:
  name: "CS Control Plane"
  lanes:
    support:
      lead: support_lead          # Rachel Torres
      specialists:
        - triage_agent            # Kai Nakamura
        - troubleshooter_agent    # Leo Petrov
        - escalation_agent        # Maya Santiago
    value:
      lead: value_lead            # Damon Reeves
      specialists:
        - health_monitor_agent    # Dr. Aisha Okafor
        - call_intel_agent        # Jordan Ellis
        - qbr_agent               # Sofia Marquez
    delivery:
      lead: delivery_lead         # Priya Mehta
      specialists:
        - sow_agent               # Ethan Brooks
        - deployment_intel_agent  # Zara Kim
  foundation:
    - customer_memory             # Atlas
```

**`config/pipeline.yaml`** — Pipeline stages per tier:
```yaml
pipelines:
  tier_1_supervisor:
    stages:
      - name: "Event Analysis"
        type: perceive
      - name: "Strategic Decomposition"
        type: think
      - name: "Delegation"
        type: act
      - name: "Quality Evaluation"
        type: quality_gate
      - name: "Synthesis"
        type: finalize

  tier_3_specialist:
    stages:
      - name: "Task Perception"
        type: perceive
      - name: "Memory Retrieval"
        type: retrieve
      - name: "Analysis"
        type: think
      - name: "Execution"
        type: act
      - name: "Self-Reflection"
        type: reflect
```

### 4.3 Pipeline Engine (1 new file)

The pipeline engine is the "brain" that runs agents through their stages:

```
perceive → retrieve → think → act → reflect → quality_gate → finalize
```

Each stage is a method call on the agent. The engine:
1. Reads the pipeline config for the agent's tier
2. Runs each stage in order
3. Passes context between stages
4. Logs every stage to the execution trace
5. Handles quality gate failures (retry from a specific stage)
6. Broadcasts progress via WebSocket

### 4.4 Tool Registry (1 new file + 12+ tool definitions)

Tools are Python functions that agents can call during the "act" stage via Claude's
tool_use API. Instead of guessing, agents ask Claude to call a function:

```
Agent: "I need to check the health score for Customer X"
Claude: [tool_use: query_health_score(customer_id="cust_123")]
System: [tool_result: {"score": 72, "trend": "declining", "factors": [...]}]
Claude: "The health score is 72 and declining. Based on the factors..."
```

**Tools we'll build:**

| Tool Name | What It Does | Wraps |
|---|---|---|
| `query_customer_db` | Look up customer profile and history | SQLAlchemy queries |
| `query_health_scores` | Get health score timeline | Health score table |
| `search_similar_tickets` | Find similar past tickets | ChromaDB RAG |
| `search_knowledge_base` | Search across all knowledge | ChromaDB RAG |
| `read_call_transcript` | Get call insight details | Call insights table |
| `get_ticket_details` | Look up specific ticket | Tickets table |
| `check_sla_status` | Calculate SLA countdown | Ticket timestamps |
| `write_report` | Generate and save a report | Reports table |
| `create_action_item` | Create a follow-up action | Action items table |
| `send_alert` | Trigger an alert | Alerts table |
| `read_agent_output` | Read another agent's work | Agent logs table |
| `publish_knowledge` | Share a finding with the team | Shared knowledge pool |

### 4.5 Trait System (1 registry + 9+ trait files)

Traits are pluggable behaviors that modify how agents work. Each trait has lifecycle hooks
that fire at different pipeline stages:

```
on_perceive    — "Before the agent processes the task, add this context"
on_think       — "When the agent is thinking, inject this guidance"
on_act         — "After the agent acts, post-process the result"
on_round_end   — "After each pipeline round, do this check"
on_complete    — "When the agent finishes, do this cleanup"
```

**Traits per tier:**

| Tier | Traits | Why |
|---|---|---|
| Tier 1 (Orchestrator) | strategic_oversight, quality_evaluation, delegation | Needs to see the big picture and judge quality |
| Tier 2 (Lane Leads) | workflow_coordination, delegation, synthesis | Needs to manage specialists and combine outputs |
| Tier 3 (Specialists) | confidence_scoring, escalation_detection, sla_awareness | Needs to know when to escalate and track deadlines |
| All Tiers | customer_sentiment | Everyone should track customer mood |

**Example — `escalation_detection` trait (used by Kai, Leo, Maya, and others):**
```
on_perceive: Adds "Check if this needs escalation" to the agent's context
on_act:      After the agent produces output, checks for escalation signals
             (severity > 8, customer health < 40, SLA breach imminent)
on_round_end: If escalation detected, Maya Santiago creates an escalation
              message to Rachel Torres via the message board
```

### 4.6 3-Tier Memory System (1 new file + 2 new ChromaDB collections)

Every agent gets access to three levels of memory:

**Working Memory (Scratchpad)**
- Short-term, lives only during the current pipeline run
- Stores: current task context, intermediate results, tool outputs
- Cleared after each run
- Think of it as: your notepad while working on a task

**Episodic Memory (Diary)**
- Medium-term, stored in ChromaDB collection `episodic_memory`
- Stores: past execution summaries with embeddings
- Searchable by semantic similarity ("find similar past situations")
- Think of it as: your diary of past work experiences

**Semantic Memory (Shared Knowledge)**
- Long-term, stored in ChromaDB collection `shared_knowledge`
- Stores: team knowledge, customer patterns, best practices
- Organized by lane (Support knowledge, Value knowledge, etc.)
- Think of it as: the team's shared wiki / knowledge base

**How agents use memory:**
```
1. Task comes in: "Triage ticket #456 for Customer X"
2. WORKING MEMORY: Store the ticket details and customer context
3. EPISODIC MEMORY: "Have I triaged similar tickets before?" → finds 3 similar past runs
4. SEMANTIC MEMORY: "What does the team know about Customer X?" → finds 5 knowledge entries
5. All this context feeds into the agent's "think" stage
6. After acting, the agent writes a summary to EPISODIC memory
7. If the agent discovers something important, it publishes to SEMANTIC memory
```

### 4.7 Message Board (1 new file + 1 new DB table)

The message board enables agents to communicate. Messages have types that reflect
the hierarchy:

| Message Type | Direction | Example |
|---|---|---|
| `task_assignment` | Down (Lead → Specialist) | Rachel → Kai: "Triage this ticket and report severity" |
| `deliverable` | Up (Specialist → Lead) | Kai → Rachel: "Ticket triaged: severity 7, category: integration" |
| `request` | Sideways (Specialist → Specialist) | Leo → Zara: "Can you check if a recent deployment caused this?" |
| `escalation` | Up (any → higher tier) | Maya → Rachel: "This needs Naveen's attention — customer threatening churn" |
| `feedback` | Down (Lead → Specialist) | Damon → Aisha: "Good analysis, but also check the call sentiment trend" |

Messages support **threading** — a task_assignment creates a thread, and all related
deliverables and follow-ups link back to it.

### 4.8 Reflection Engine (1 new file)

After completing work, agents reflect on what they did. The depth of reflection varies by tier:

- **Tier 3 (e.g., Kai, Leo, Aisha):** Self-assessment — "How confident am I? What did I miss?"
- **Tier 2 (Rachel, Damon, Priya):** Synthesis — "What patterns do I see across my specialists' work?"
- **Tier 1 (Naveen):** Strategic synthesis — "What does this mean for the customer overall?"

Reflection is triggered when an agent's cumulative importance score crosses a threshold.
The reflection output is stored back into episodic memory as a high-importance entry.

### 4.9 Structured Execution Logger (1 new file + 1 new DB table)

Every pipeline run is logged in detail:

```
agent_execution_rounds table:
├── execution_id    — unique run ID
├── agent_id        — which agent
├── round_number    — which pipeline stage
├── stage_name      — "perceive", "think", "act", etc.
├── input_context   — what the agent received
├── output          — what the agent produced
├── tools_called    — which tools were invoked
├── duration_ms     — how long this stage took
├── tokens_used     — API token count
└── timestamp       — when this happened
```

This gives us full observability: you can drill into any agent run and see exactly what
happened at each stage, what tools were called, and how long everything took.

---

## 5. The 9 Phases at a Glance

Here's the roadmap. Phase 0 gets real data flowing first, then we build the architecture.

### Phase 0: Fathom Integration — Get Real Data Flowing (1–2 days)
**Before the rebuild, make the system useful.** Replace the mock Fathom service with a real
API client that pulls call recordings, transcripts, summaries, and action items from Fathom.
Set up a webhook so Fathom pushes new meetings to us automatically. The existing Call Intel
agent (Jordan Ellis) already knows how to process transcripts — we just need to feed it real data.

### Phase A: Documentation Update (1–2 days)
**First things first.** Before writing a single line of code for the rebuild, rewrite all docs in `/docs/`
to match the new architecture: PRD (new features, user stories), WIREFRAMES (new page designs),
API_CONTRACT (new endpoints), DATABASE_SCHEMA (new tables), and CLAUDE.md (updated project
structure and rules). This becomes the blueprint everything else is built against.

### Phase B: Foundation (3–4 days)
Build the core infrastructure: YAML configs, profile loader, tool registry, enhanced Claude
service with tool_use, pipeline engine, and execution logger. This is the skeleton that
everything else plugs into. No agents change yet — we're building the framework.

### Phase C: Memory System (1–2 days)
Build the 3-tier memory manager (working + episodic + semantic) and lane knowledge pools.
Add 2 new ChromaDB collections. After this, agents have a memory system available to them.

### Phase D: Traits + Reflection (1–2 days)
Build the trait registry and implement 9+ CS-specific traits. Build the reflection engine
with tier-appropriate depth. After this, agents can have pluggable behaviors and self-assess.

### Phase E: Message Board + Hierarchy (2–3 days)
Build the message board (new DB table + service), implement delegation chains, and create
workflow YAML configs. After this, agents can communicate up/down/sideways through the hierarchy.

### Phase F: Agent Implementation (3–4 days)
The big migration. Implement the Orchestrator as a Tier 1 supervisor, build 3 new Lane Leads
(Tier 2), migrate all 8 specialists to pipeline execution (Tier 3), and upgrade the Memory
Agent to a Tier 4 foundation provider. This is where everything comes together.

### Phase G: Frontend — Complete Redesign (5–7 days)
Build an entirely new React frontend designed to showcase every capability. New pages:
Agent Hierarchy View, Pipeline Execution, Message Board, Memory Inspector, Execution Trace
Viewer, Agent Profile Cards, Workflow Viewer, and Live Dashboard. New Zustand stores,
WebSocket integration for real-time updates.

### Phase H: Integration (1–2 days)
Wire everything together: update Celery tasks for pipeline execution, add new WebSocket event
types (pipeline progress, delegation events), build feature flags for v1/v2 switching, and
create seed data that demonstrates the full hierarchy in action.

---

**Total estimated timeline: 18–28 days** (depending on complexity and iteration)

---

*End of Part 1 — The Big Picture. Part 2 below has the detailed breakdown of each phase.*

---

# PART 2 — DETAILED PHASE BREAKDOWN

---

## 6. Phase 0: Fathom Integration — Get Real Data Flowing (1–2 days)

**Before the big rebuild, make the system actually useful.** Right now the Fathom service
is 100% mock — hardcoded fake data. We have a real Fathom API key (paid plan), so let's
get real call data flowing through the system immediately.

### What We Have Now

| Component | Current State |
|---|---|
| `fathom_service.py` | Mock — returns hardcoded fake calls |
| `call_intel_agent.py` (Jordan Ellis) | Ready — already processes transcripts via Claude |
| `orchestrator.py` | Ready — already routes `fathom_recording_ready` events |
| `call_insights` table | Ready — has `fathom_recording_id` field |
| Config | Has `FATHOM_EMAIL` / `FATHOM_PASSWORD` (old approach) |
| Frontend | `insightApi.syncFathom()` exists but calls mock endpoint |

### What We Build

### 0.1: Update Config for Fathom API Key

**File: `backend/app/config.py`** (modify)

Replace the old email/password fields with the proper API key:

```python
# OLD:
FATHOM_EMAIL: str = ""
FATHOM_PASSWORD: str = ""

# NEW:
FATHOM_API_KEY: str = ""
FATHOM_API_BASE_URL: str = "https://api.fathom.ai/external/v1"
FATHOM_WEBHOOK_SECRET: str = ""  # For validating webhook payloads
```

### 0.2: Build Real Fathom API Client

**File: `backend/app/services/fathom_service.py`** (rewrite, ~200 lines)

Replace the mock with a real HTTP client that calls the Fathom API:

```python
import httpx
from app.config import settings

class FathomService:
    BASE_URL = settings.FATHOM_API_BASE_URL
    HEADERS = {"X-Api-Key": settings.FATHOM_API_KEY}

    async def list_meetings(
        self,
        created_after: str = None,    # ISO 8601 timestamp
        created_before: str = None,
        include_transcript: bool = False,
        include_summary: bool = True,
        include_action_items: bool = True,
        recorded_by: list[str] = None,
        teams: list[str] = None,
        cursor: str = None,
    ) -> dict:
        """List meetings from Fathom API with filters."""
        params = {}
        if created_after: params["created_after"] = created_after
        if created_before: params["created_before"] = created_before
        if include_transcript: params["include_transcript"] = "true"
        if include_summary: params["include_summary"] = "true"
        if include_action_items: params["include_action_items"] = "true"
        if recorded_by:
            for email in recorded_by:
                params.setdefault("recorded_by[]", []).append(email)
        if teams:
            for team in teams:
                params.setdefault("teams[]", []).append(team)
        if cursor: params["cursor"] = cursor

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/meetings",
                headers=self.HEADERS,
                params=params,
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_meeting_with_transcript(self, meeting_id: str) -> dict:
        """Fetch a single meeting with full transcript."""
        # Use list endpoint with filters to get specific meeting
        # Or use the include_transcript param on the list endpoint
        ...

    async def fetch_all_meetings(self, since: str = None) -> list[dict]:
        """Paginate through all meetings since a given date."""
        all_meetings = []
        cursor = None
        while True:
            result = await self.list_meetings(
                created_after=since,
                include_transcript=True,
                include_summary=True,
                include_action_items=True,
                cursor=cursor,
            )
            all_meetings.extend(result.get("items", []))
            cursor = result.get("next_cursor")
            if not cursor:
                break
        return all_meetings

    async def register_webhook(self, destination_url: str) -> dict:
        """Register a webhook so Fathom pushes new meetings to us."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/webhooks",
                headers=self.HEADERS,
                json={
                    "destination_url": destination_url,
                    "include_transcript": True,
                    "include_summary": True,
                    "include_action_items": True,
                    "include_crm_matches": True,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_webhook(self, webhook_id: str) -> None:
        """Remove a registered webhook."""
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.BASE_URL}/webhooks/{webhook_id}",
                headers=self.HEADERS,
                timeout=30.0,
            )
            resp.raise_for_status()
```

### 0.3: Build Webhook Receiver Endpoint

**File: `backend/app/routers/webhooks.py`** (new, ~80 lines)

Fathom sends a POST to our backend when a new meeting is ready. We receive it,
create an event, and let the orchestrator route it to the Call Intel agent (Jordan Ellis).

```python
@router.post("/webhooks/fathom")
async def receive_fathom_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Fathom calls this endpoint when a new meeting recording is ready.

    Flow:
    1. Receive the meeting payload (transcript, summary, action items)
    2. Create a 'fathom_recording_ready' event in our events table
    3. The Orchestrator picks it up and routes to Call Intel agent
    4. Jordan Ellis processes the transcript → saves call insight
    """
    payload = await request.json()

    # Extract meeting data from Fathom webhook payload
    meeting = payload  # Fathom sends the meeting object directly
    transcript_text = _extract_transcript_text(meeting.get("transcript", []))

    # Create event for the orchestrator
    event = Event(
        id=uuid.uuid4(),
        event_type="fathom_recording_ready",
        source="fathom_webhook",
        payload={
            "recording_id": meeting.get("recording_id"),
            "title": meeting.get("title"),
            "transcript": transcript_text,
            "summary": meeting.get("default_summary"),
            "action_items": meeting.get("action_items", []),
            "participants": [inv.get("email") for inv in meeting.get("calendar_invitees", [])],
            "duration_minutes": _calc_duration(meeting),
            "recorded_by": meeting.get("recorded_by", {}).get("email"),
            "fathom_url": meeting.get("url"),
        },
        status="pending",
    )
    db.add(event)
    db.commit()

    # Broadcast new event via WebSocket
    await ws_manager.broadcast("event:new", {"event_id": str(event.id), "type": "fathom_recording_ready"})

    return {"status": "received", "event_id": str(event.id)}
```

### 0.4: Build Sync Endpoint (Initial Historical Pull)

**File: `backend/app/routers/insights.py`** (modify existing sync-fathom endpoint)

Replace the mock `/sync-fathom` endpoint with a real one that pulls historical meetings:

```python
@router.post("/insights/sync-fathom")
async def sync_fathom_recordings(
    since_days: int = 30,  # How far back to sync
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Pull all meetings from the last N days from Fathom.
    Creates events for each new recording the orchestrator hasn't seen.
    """
    fathom = FathomService()
    since = (datetime.utcnow() - timedelta(days=since_days)).isoformat()
    meetings = await fathom.fetch_all_meetings(since=since)

    created = 0
    skipped = 0
    for meeting in meetings:
        # Check if we already have this recording
        existing = db.query(CallInsight).filter_by(
            fathom_recording_id=meeting.get("recording_id")
        ).first()
        if existing:
            skipped += 1
            continue

        # Create event for the orchestrator
        # ... same as webhook flow
        created += 1

    return {"synced": created, "skipped": skipped, "total_from_fathom": len(meetings)}
```

### 0.5: Wire It Up

1. **Register the webhook router** in `main.py`
2. **Add `httpx`** to `requirements.txt`
3. **Update `.env.example`** with `FATHOM_API_KEY` and `FATHOM_WEBHOOK_SECRET`
4. **Test the flow:**
   - Call `POST /insights/sync-fathom` → pulls historical meetings
   - Register webhook via the Fathom API → new meetings auto-push
   - Orchestrator routes `fathom_recording_ready` → Jordan Ellis processes → insight saved
   - Frontend already displays insights at `/insights`

### What This Gives Us

After Phase 0, the system is **immediately useful**:

```
Fathom (real calls) ──webhook──→ Backend ──event──→ Orchestrator
                                                        │
                                                        ▼
                                              Jordan Ellis (Call Intel)
                                                        │
                                                        ▼
                                              call_insights table
                                                        │
                                                        ▼
                                              Frontend /insights page
```

Real call transcripts flowing in, real AI-powered analysis, real structured insights
in the database. The existing frontend already shows call insights — it'll just show
real data instead of seed data.

### Files Changed/Created

| Action | File | Lines |
|---|---|---|
| MODIFY | `backend/app/config.py` | ~5 changed |
| REWRITE | `backend/app/services/fathom_service.py` | ~200 |
| NEW | `backend/app/routers/webhooks.py` | ~80 |
| MODIFY | `backend/app/routers/insights.py` | ~40 changed |
| MODIFY | `backend/app/main.py` | ~3 (register router) |
| MODIFY | `backend/requirements.txt` | ~1 (add httpx) |
| MODIFY | `.env.example` | ~3 changed |

---

## 7. Phase A: Documentation Update (1–2 days)

**Before writing any code for the rebuild, we update the docs to serve as the blueprint.**
The updated docs become the single source of truth that guides every implementation phase.

### A1: Rewrite `/docs/PRD.md`

**What changes:**
- Updated product description (mention 4-tier hierarchy, pipeline execution, inter-agent collaboration)
- New user stories for pipeline visualization, message board, memory inspector
- New acceptance criteria for each new page/panel
- Updated agent capabilities table (tiers, tools, traits per agent, with names)
- New non-functional requirements (pipeline stage timing, memory retrieval latency)

### A2: Rewrite `/docs/WIREFRAMES.md`

**What changes:**
- New page wireframes: Agent Hierarchy, Pipeline Execution, Message Board, Memory Inspector, Execution Trace, Workflow Viewer
- Updated Dashboard wireframe (real-time activity stream, agent status grid)
- New component specs: PipelineStageCard, MessageThread, MemoryEntry, HierarchyTree, TraitBadge
- Updated design system notes (any new colors for tier coding, lane coding)
- Responsive layouts for all new pages

### A3: Rewrite `/docs/API_CONTRACT.md`

**What changes:**
- New v2 endpoints: pipeline, messages, memory, hierarchy, workflows (detailed in Phase G frontend section)
- Updated agent endpoints (pipeline execution instead of direct invocation)
- New WebSocket event types and payloads
- New request/response schemas for all new endpoints
- API versioning strategy (v1 stays for backward compat, v2 for new features)

### A4: Rewrite `/docs/DATABASE_SCHEMA.md`

**What changes:**
- New table: `agent_execution_rounds` (full schema with column types, indexes)
- New table: `agent_messages` (full schema with column types, indexes)
- Updated ChromaDB section: 2 new collections (episodic_memory, shared_knowledge)
- YAML config schemas (agent_profiles, org_structure, pipeline, workflows)
- Migration strategy (Alembic migration for new tables)
- Updated ERD showing new table relationships

### A5: Update `CLAUDE.md`

**What changes:**
- Updated project structure (new directories: config/, agents/leads/, agents/tools/, agents/traits/, agents/memory/)
- Updated architecture rules (add rules for pipeline execution, message board, memory)
- Updated coding standards (YAML profile patterns, tool definition patterns)
- Updated development phases (new phase ordering)
- Updated design system (tier colors, lane colors, new component patterns)

---

## 8. Phase B: Foundation (3–4 days)

This phase builds all the core infrastructure. Nothing changes for existing agents yet —
we're building the framework that everything else plugs into.

### B1: Organization Structure YAML + Agent Profile YAML

**What:** Create 3 YAML config files that define the entire agent organization.

**File: `backend/config/org_structure.yaml`** (~80 lines)

Defines the 4-tier hierarchy, 3 lanes, and reporting lines:

```yaml
organization:
  name: "HivePro CS Control Plane"
  description: "AI-powered Customer Success operations center"

  hierarchy:
    tier_1:
      name: "Supervisor"
      agents: [cso_orchestrator]      # Naveen Kapoor
      description: "Strategic oversight and delegation"

    tier_2:
      name: "Lane Leads"
      agents:
        - support_lead                # Rachel Torres
        - value_lead                  # Damon Reeves
        - delivery_lead               # Priya Mehta
      description: "Coordinate specialist workflows within their lane"

    tier_3:
      name: "Specialists"
      agents:
        - triage_agent                # Kai Nakamura
        - troubleshooter_agent        # Leo Petrov
        - escalation_agent            # Maya Santiago
        - health_monitor_agent        # Dr. Aisha Okafor
        - call_intel_agent            # Jordan Ellis
        - qbr_agent                   # Sofia Marquez
        - sow_agent                   # Ethan Brooks
        - deployment_intel_agent      # Zara Kim
      description: "Execute specific CS tasks"

    tier_4:
      name: "Foundation"
      agents: [customer_memory]       # Atlas
      description: "Provides context and memory to all agents"

  lanes:
    support:
      lead: support_lead              # Rachel Torres
      specialists: [triage_agent, troubleshooter_agent, escalation_agent]
      focus: "Ticket handling, troubleshooting, escalation management"

    value:
      lead: value_lead                # Damon Reeves
      specialists: [health_monitor_agent, call_intel_agent, qbr_agent]
      focus: "Customer health, call intelligence, business reviews"

    delivery:
      lead: delivery_lead             # Priya Mehta
      specialists: [sow_agent, deployment_intel_agent]
      focus: "Scope of work, deployment tracking"

  communication_rules:
    - "Naveen can assign tasks to any Tier 2 lead"
    - "Tier 2 leads assign tasks to their own specialists only"
    - "Tier 3 specialists escalate to their lead"
    - "Cross-lane requests go through Tier 2 leads"
    - "Atlas (Tier 4) serves all tiers on request"
```

**File: `backend/config/agent_profiles.yaml`** (~500 lines)

Defines all 13 agent profiles. Each profile includes:

```yaml
# Example: Two of 13 profiles (each agent has a name and personality)
cso_orchestrator:
  name: "Naveen Kapoor"
  codename: "CS Orchestrator"
  tier: 1
  lane: null  # Above lanes
  role: "CS Manager"
  personality: |
    Strategic, composed, sees the big picture. Delegates decisively and
    holds the team to high standards. Speaks concisely — every word matters.
    Former management consultant who values structured thinking.
  system_instruction: |
    You are Naveen Kapoor, CS Manager at HivePro.
    Your job is to:
    1. Receive incoming events (tickets, calls, health alerts, scheduled tasks)
    2. Analyze the event and determine which lane(s) need to handle it
    3. Create clear task assignments for the appropriate Lane Lead(s)
    4. Evaluate the quality of work returned by your leads
    5. Synthesize final output for the customer/stakeholder

    You never do the specialist work yourself. You delegate and evaluate.
    Your leads are Rachel Torres (Support), Damon Reeves (Value),
    and Priya Mehta (Delivery).
  traits:
    - strategic_oversight
    - quality_evaluation
    - delegation
    - customer_sentiment
  tools:
    - query_customer_db
    - search_knowledge_base
    - read_agent_output
  expertise:
    - "Cross-functional CS strategy"
    - "Delegation and quality control"
    - "Customer relationship management"
  quirks:
    - "Always asks 'what's the customer impact?' before deciding"
    - "Summarizes every situation in exactly 3 bullet points"
  reports_to: null
  manages: [support_lead, value_lead, delivery_lead]

support_lead:
  name: "Rachel Torres"
  codename: "Support Lead"
  tier: 2
  lane: support
  role: "Support Operations Lead"
  personality: |
    Methodical, thorough, protective of her team. Runs a tight ship —
    no ticket falls through the cracks. Has a dry sense of humor under
    pressure. Tracks SLAs like a hawk.
  system_instruction: |
    You are Rachel Torres, Support Operations Lead at HivePro.
    You coordinate Kai Nakamura (Triage), Leo Petrov (Troubleshooting),
    and Maya Santiago (Escalation) to handle support issues efficiently.
  quirks:
    - "Starts every status update with the SLA countdown"
    - "Keeps a mental leaderboard of ticket resolution times"
  # ... (similar structure for all 13 agents)
```

**File: `backend/config/pipeline.yaml`** (~120 lines)

Defines different pipeline configurations per tier:

```yaml
pipelines:
  tier_1_supervisor:
    description: "Strategic pipeline for the Orchestrator"
    max_rounds: 5
    stages:
      - name: "Event Analysis"
        type: perceive
        description: "Understand the incoming event"
      - name: "Context Gathering"
        type: retrieve
        description: "Pull relevant customer and historical context"
      - name: "Strategic Decomposition"
        type: think
        description: "Break the event into subtasks for lane leads"
      - name: "Delegation"
        type: act
        description: "Assign tasks to the appropriate lane leads"
      - name: "Quality Evaluation"
        type: quality_gate
        description: "Evaluate returned deliverables"
        max_iterations: 2
        iterate_from: "Delegation"
      - name: "Synthesis"
        type: finalize
        description: "Combine all lane outputs into final result"

  tier_2_lane_lead:
    description: "Coordination pipeline for Lane Leads"
    max_rounds: 4
    stages:
      - name: "Task Reception"
        type: perceive
      - name: "Context Retrieval"
        type: retrieve
      - name: "Task Planning"
        type: think
        description: "Break the lead-level task into specialist subtasks"
      - name: "Specialist Coordination"
        type: act
        description: "Assign to specialists, collect results"
      - name: "Lane Synthesis"
        type: finalize
        description: "Combine specialist outputs for the Orchestrator"

  tier_3_specialist:
    description: "Execution pipeline for Specialist agents"
    max_rounds: 3
    stages:
      - name: "Task Perception"
        type: perceive
      - name: "Memory Retrieval"
        type: retrieve
      - name: "Analysis"
        type: think
      - name: "Execution"
        type: act
      - name: "Self-Reflection"
        type: reflect

  tier_4_foundation:
    description: "Service pipeline for Foundation agents"
    max_rounds: 2
    stages:
      - name: "Request Parsing"
        type: perceive
      - name: "Data Retrieval"
        type: act
```

### B2: Profile Loader

**What:** Python module that loads, validates, and caches YAML configs.

**File: `backend/app/agents/profile_loader.py`** (~120 lines)

```python
# What it does:
class ProfileLoader:
    def load_profiles() -> dict          # Load agent_profiles.yaml
    def load_org_structure() -> dict     # Load org_structure.yaml
    def load_pipeline_config() -> dict   # Load pipeline.yaml
    def get_agent_profile(agent_id) -> AgentProfile  # Get one profile
    def get_pipeline_for_tier(tier) -> PipelineConfig # Get tier pipeline
    def get_lane_for_agent(agent_id) -> str           # Which lane?
    def get_reports_to(agent_id) -> str               # Who is the boss?
```

Validates on startup: all agent_ids referenced in org_structure exist in profiles,
all traits and tools referenced exist in their registries.

### B3: Tool Registry

**What:** Maps tool names (from YAML profiles) to Python functions that agents can call
via Claude's tool_use API.

**File: `backend/app/agents/tool_registry.py`** (~80 lines)
**Directory: `backend/app/agents/tools/`** (12+ files, ~40 lines each)

```python
# Registry pattern:
class ToolRegistry:
    def register(name, function, description, parameters)
    def resolve_tools(tool_names: list) -> list[dict]
    # Returns Claude-compatible tool definitions

# Each tool file:
# backend/app/agents/tools/customer_tools.py
async def query_customer_db(customer_id: str) -> dict:
    """Look up customer profile and recent history."""
    # Uses existing SQLAlchemy queries from services/
    async with get_session() as db:
        customer = await db.get(Customer, customer_id)
        return {"name": customer.name, "health": customer.health_score, ...}
```

**Tool files:**

| File | Tools Inside |
|---|---|
| `tools/customer_tools.py` | query_customer_db, query_health_scores |
| `tools/ticket_tools.py` | get_ticket_details, search_similar_tickets, check_sla_status |
| `tools/insight_tools.py` | read_call_transcript, search_knowledge_base |
| `tools/action_tools.py` | create_action_item, send_alert, write_report |
| `tools/agent_tools.py` | read_agent_output, publish_knowledge |

These tools **wrap existing services** — they don't create new database logic.
They just give agents a clean interface to call our existing backend.

### B4: Enhanced ClaudeService with Tool Use

**What:** Upgrade `claude_service.py` to support Claude's tool_use API.

**File: `backend/app/services/claude_service.py`** (modify existing, ~200 lines after)

```python
# New method added:
class ClaudeService:
    # EXISTING (keep):
    async def generate(self, system_prompt, user_message) -> str

    # NEW:
    async def generate_with_tools(
        self,
        system_prompt: str,
        messages: list,
        tools: list[dict],       # Tool definitions from ToolRegistry
        max_tool_rounds: int = 5  # Safety limit on tool loops
    ) -> dict:
        """
        Send a message to Claude with tools available.

        Flow:
        1. Send messages + tool definitions to Claude
        2. If Claude wants to call a tool → execute it → send result back
        3. Repeat until Claude gives a final text response
        4. Return {content, tool_calls_made, tokens_used}
        """
```

This is the critical upgrade — it's what enables agents to use tools instead of guessing.

### B5: Pipeline Engine

**What:** The engine that runs agents through their tier-specific pipeline stages.

**File: `backend/app/agents/pipeline_engine.py`** (~250 lines)

```python
class PipelineEngine:
    async def run(
        self,
        agent: BaseAgent,
        task: dict,
        context: dict,
    ) -> PipelineResult:
        """
        Run an agent through its tier-specific pipeline.

        Steps:
        1. Load pipeline config for this agent's tier
        2. For each stage in the pipeline:
           a. Call the agent's stage method (perceive/retrieve/think/act/reflect)
           b. Log the stage to the execution trace
           c. Broadcast progress via WebSocket
           d. Pass output as context to the next stage
        3. Handle quality_gate stages (may loop back)
        4. Return final PipelineResult with all stage outputs
        """
```

**Pipeline stages explained:**

| Stage | What Happens | Agent Method |
|---|---|---|
| `perceive` | Agent reads the task, adds to working memory, traits fire `on_perceive` | `agent.perceive(task)` |
| `retrieve` | Agent queries episodic + semantic memory for relevant context | `agent.retrieve(task)` |
| `think` | Agent reasons about the task with all context (Claude call with tools) | `agent.think(task, context)` |
| `act` | Agent produces output (Claude call with tools, may call multiple tools) | `agent.act(task, context)` |
| `reflect` | Agent assesses its own work, confidence, what it might have missed | `agent.reflect(output)` |
| `quality_gate` | A higher-tier agent evaluates the output quality | `evaluator.evaluate(output)` |
| `finalize` | Agent produces the final, polished output | `agent.finalize(outputs)` |

### B6: Structured Execution Logger

**What:** Logs every pipeline stage to a new database table for full observability.

**New DB table: `agent_execution_rounds`**

```sql
CREATE TABLE agent_execution_rounds (
    id              UUID PRIMARY KEY,
    execution_id    UUID NOT NULL,       -- Groups all stages of one pipeline run
    agent_id        VARCHAR NOT NULL,
    tier            INTEGER NOT NULL,
    stage_number    INTEGER NOT NULL,
    stage_name      VARCHAR NOT NULL,     -- "perceive", "think", "act", etc.
    stage_type      VARCHAR NOT NULL,
    input_summary   TEXT,                 -- Truncated input for debugging
    output_summary  TEXT,                 -- Truncated output for debugging
    tools_called    JSONB,               -- [{tool_name, args, result_preview}]
    duration_ms     INTEGER,
    tokens_used     INTEGER,
    status          VARCHAR NOT NULL,     -- "completed", "failed", "skipped"
    error_message   TEXT,
    metadata        JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**File: `backend/app/agents/execution_logger.py`** (~100 lines)
**File: `backend/app/models/execution_round.py`** (~40 lines)
**File: `backend/app/schemas/execution_round.py`** (~30 lines)

---

## 9. Phase C: Memory System (1–2 days)

### C1: 3-Tier Memory Manager

**What:** Build the memory system that gives agents context from past work.

**File: `backend/app/agents/memory/memory_manager.py`** (~200 lines)

```python
class MemoryManager:
    """Manages all 3 tiers of agent memory."""

    def __init__(self, agent_id: str, lane: str):
        self.working = WorkingMemory()          # Tier 1: scratchpad
        self.episodic = EpisodicMemory(agent_id) # Tier 2: past runs
        self.semantic = SemanticMemory(lane)      # Tier 3: shared knowledge

    # Working Memory
    def set_context(self, key, value)          # Store temp data
    def get_context(self, key) -> any          # Retrieve temp data
    def clear()                                 # Wipe after run

    # Episodic Memory
    async def remember_execution(self, summary, importance)   # Save a run
    async def recall_similar(self, query, n=5) -> list        # Find similar past work
    async def get_recent(self, n=5) -> list                   # Get latest runs

    # Semantic Memory
    async def publish_knowledge(self, content, tags, importance)  # Share a finding
    async def query_knowledge(self, query, n=5) -> list           # Search shared pool
    async def query_cross_lane(self, query, n=3) -> list          # Search other lanes
```

**File: `backend/app/agents/memory/working_memory.py`** (~50 lines)
- Simple dict-based scratchpad
- Stores current task, intermediate results, tool outputs
- Cleared after each pipeline run

**File: `backend/app/agents/memory/episodic_memory.py`** (~120 lines)
- Backed by ChromaDB collection `episodic_memory`
- Each entry: agent_id, execution_summary, embedding, importance, timestamp
- Retrieval uses tri-factor scoring: 35% relevance + 25% recency + 40% importance
- Consolidation: when entries exceed 25, older ones are summarized into key insights

**File: `backend/app/agents/memory/semantic_memory.py`** (~120 lines)
- Backed by ChromaDB collection `shared_knowledge`
- Organized by lane (support, value, delivery) + cross-lane
- Agents publish findings with tags and importance scores
- Query combines semantic similarity + importance weighting

### C2: Lane Knowledge Pools

**What:** Shared knowledge pools organized by agent lane.

This is built into the SemanticMemory class above. Each lane has its own namespace
in the shared_knowledge ChromaDB collection:

```
shared_knowledge collection:
├── support/    — Knowledge from Triage, Troubleshooter, Escalation
├── value/      — Knowledge from Health Monitor, Call Intel, QBR
├── delivery/   — Knowledge from SOW, Deployment Intel
└── global/     — Cross-lane knowledge (customer patterns, best practices)
```

**How it works in practice:**
- Kai Nakamura triages a ticket and discovers "Customer X has a recurring auth issue"
- He publishes this to the `support` knowledge pool with tags ["auth", "recurring", "customer_x"]
- Later, Leo Petrov is troubleshooting another ticket for Customer X
- He queries the support knowledge pool: "auth issues for Customer X"
- Gets back Kai's finding and uses it for faster diagnosis

---

## 10. Phase D: Traits + Reflection (1–2 days)

### D1: Trait Registry + CS Traits

**What:** Build the trait system and implement CS-specific traits.

**File: `backend/app/agents/traits/base_trait.py`** (~60 lines)

```python
from abc import ABC, abstractmethod

class BaseTrait(ABC):
    """Base class for all agent traits."""

    name: str           # "escalation_detection"
    description: str    # "Detects when issues need escalation"

    def on_perceive(self, agent, context, round_number) -> str:
        """Add context before perception. Return extra context string."""
        return ""

    def on_think_prompt(self, agent, task, round_number) -> str:
        """Inject guidance into the thinking stage. Return prompt addition."""
        return ""

    def on_act_postprocess(self, agent, result, round_number) -> dict:
        """Post-process the agent's action output. Return modified result."""
        return result

    def on_round_end(self, agent, round_number):
        """Called after each pipeline round. Side effects OK."""
        pass

    def on_complete(self, agent):
        """Called when the full pipeline completes."""
        pass
```

**File: `backend/app/agents/traits/registry.py`** (~50 lines)

```python
class TraitRegistry:
    _traits: dict[str, type[BaseTrait]] = {}

    def register(name, trait_class)
    def get(name) -> BaseTrait
    def resolve_traits(trait_names: list) -> list[BaseTrait]
```

**Trait files in `backend/app/agents/traits/`:**

| File | Trait | Tier | What It Does |
|---|---|---|---|
| `strategic_oversight.py` | strategic_oversight | Tier 1 | Adds big-picture context: "Consider cross-lane impact" |
| `quality_evaluation.py` | quality_evaluation | Tier 1 | Post-processes output: checks for completeness, flags gaps |
| `delegation.py` | delegation | Tier 1, 2 | Adds context about available agents and their capabilities |
| `workflow_coordination.py` | workflow_coordination | Tier 2 | Tracks which specialists are working on what |
| `synthesis.py` | synthesis | Tier 2 | Combines multiple specialist outputs coherently |
| `confidence_scoring.py` | confidence_scoring | Tier 3 | Adds "Rate your confidence 1-10" to output, logs it |
| `escalation_detection.py` | escalation_detection | Tier 3 | Checks severity, health, SLA → triggers escalation message |
| `sla_awareness.py` | sla_awareness | Tier 3 | Adds SLA countdown context to ticket-related tasks |
| `customer_sentiment.py` | customer_sentiment | All | Tracks sentiment cues in task context, flags mood shifts |

### D2: Reflection Engine

**What:** Build the reflection system with tier-appropriate depth.

**File: `backend/app/agents/reflection_engine.py`** (~150 lines)

```python
class ReflectionEngine:
    IMPORTANCE_THRESHOLD = 25  # Cumulative importance to trigger reflection

    def should_reflect(self, agent_id, memory_stream, current_round) -> bool:
        """Check if cumulative importance exceeds threshold."""

    def build_reflection_prompt(self, agent_name, role, recent_memories) -> str:
        """Build self-assessment prompt for Tier 3 specialists."""
        # Asks: What went well? What could improve? Confidence level?

    def build_synthesis_prompt(self, agent_name, role, team_outputs, own_reflection) -> str:
        """Build synthesis prompt for Tier 2 lane leads."""
        # Asks: Cross-cutting themes? Alignment/conflicts? Recommendations?

    def build_strategic_prompt(self, agent_name, role, all_lane_outputs, own_reflection) -> str:
        """Build strategic synthesis prompt for Tier 1 orchestrator."""
        # Asks: Overall customer impact? Risk assessment? Next priorities?

    def record_reflection(self, agent_id, memory, content, round_number):
        """Store reflection back into episodic memory (high importance)."""
```

**How reflection varies by tier:**

| Tier | Agent Example | Reflection Type | Output |
|---|---|---|---|
| Tier 3 | Kai after triaging | Self-assessment | "Confidence: 7/10. I may have missed deployment context. Flagging for Leo." |
| Tier 2 | Rachel after collecting results | Cross-specialist synthesis | "Kai and Leo agree on root cause but Maya sees higher urgency — escalation warranted." |
| Tier 1 | Naveen after all lanes report | Strategic synthesis | "This customer needs proactive outreach. Rachel's lane resolved the ticket but Damon's lane flagged declining health trend." |

---

## 11. Phase E: Message Board + Hierarchy (2–3 days)

### E1: Message Board + Database Table

**What:** Inter-agent communication system with threading and message types.

**New DB table: `agent_messages`**

```sql
CREATE TABLE agent_messages (
    id              UUID PRIMARY KEY,
    thread_id       UUID,                -- Groups related messages
    parent_id       UUID,                -- Reply-to (for threading)
    from_agent      VARCHAR NOT NULL,
    to_agent        VARCHAR NOT NULL,
    message_type    VARCHAR NOT NULL,     -- task_assignment, deliverable, request, escalation, feedback
    content         TEXT NOT NULL,
    metadata        JSONB,               -- Extra data (task context, priority, etc.)
    status          VARCHAR DEFAULT 'pending',  -- pending, read, completed
    priority        INTEGER DEFAULT 5,   -- 1-10
    event_id        UUID,                -- Links to the triggering event
    created_at      TIMESTAMP DEFAULT NOW(),
    read_at         TIMESTAMP,
    completed_at    TIMESTAMP
);
```

**File: `backend/app/models/agent_message.py`** (~40 lines)
**File: `backend/app/schemas/agent_message.py`** (~50 lines)
**File: `backend/app/services/message_service.py`** (~180 lines)

```python
class MessageService:
    async def send_task_assignment(from_agent, to_agent, task, context) -> Message
    async def send_deliverable(from_agent, to_agent, thread_id, content) -> Message
    async def send_request(from_agent, to_agent, question) -> Message
    async def send_escalation(from_agent, content, severity) -> Message
    async def send_feedback(from_agent, to_agent, thread_id, feedback) -> Message

    async def get_inbox(agent_id) -> list[Message]     # Unread messages
    async def get_thread(thread_id) -> list[Message]   # Full conversation
    async def mark_read(message_id)
    async def mark_completed(message_id)

    # For the frontend:
    async def get_recent_messages(limit=50) -> list[Message]
    async def get_messages_by_event(event_id) -> list[Message]
```

**New API router: `backend/app/routers/messages.py`** (~80 lines)

```
GET  /api/messages                    — Recent messages (paginated)
GET  /api/messages/thread/{thread_id} — Full thread
GET  /api/messages/agent/{agent_id}   — Messages for an agent
GET  /api/messages/event/{event_id}   — Messages for an event
```

### E2: Delegation Chains

**What:** The flow of work through the 4-tier hierarchy.

This isn't a separate file — it's how the Orchestrator, Lane Leads, and Specialists
use the message board. Here's the flow:

```
1. Event arrives: "New Jira ticket #789 — Customer X can't export reports"

2. NAVEEN KAPOOR — Orchestrator (Tier 1):
   - Perceives the event
   - Thinks: "This is a support issue. Rachel's lane should handle it."
   - Acts: Sends task_assignment to Rachel Torres
     → Message: "Rachel, triage and resolve ticket #789 for Customer X.
                 Priority: High. SLA: 4 hours."

3. RACHEL TORRES — Support Lead (Tier 2):
   - Receives task_assignment from Naveen
   - Thinks: "This needs Kai for triage first, then Leo for troubleshooting."
   - Acts: Sends task_assignment to Kai Nakamura
     → Message: "Kai, classify ticket #789. Determine severity, category,
                 and suggested initial response."

4. KAI NAKAMURA — Triage Specialist (Tier 3):
   - Receives task_assignment from Rachel
   - Perceives → Retrieves similar tickets from memory → Thinks → Acts
   - Sends deliverable to Rachel
     → Message: "Ticket #789 classified: Severity 6, Category: Export/Reports,
                 Root cause likely: permission config. See 3 similar tickets."

5. RACHEL TORRES — Support Lead (Tier 2):
   - Receives deliverable from Kai
   - Sends task_assignment to Leo Petrov
     → Message: "Leo, diagnose export issue for Customer X. Kai says likely
                 permission config. Check deployment history."

6. LEO PETROV — Troubleshooter (Tier 3):
   - Works through pipeline → sends deliverable to Rachel

7. RACHEL TORRES — Support Lead (Tier 2):
   - Collects deliverables from Kai and Leo
   - Synthesizes into lane-level output
   - Sends deliverable to Naveen
     → Message: "Naveen, ticket #789 resolved. Root cause: export permissions
                 were reset during last deployment. Fix applied. Recommended:
                 add deployment validation check."

8. NAVEEN KAPOOR — Orchestrator (Tier 1):
   - Evaluates quality (quality_gate)
   - Synthesizes final output
   - Updates the ticket, creates action items, broadcasts via WebSocket
```

### E3: Workflow YAML Config

**What:** Data-driven workflow definitions for common event types.

**File: `backend/config/workflows.yaml`** (~100 lines)

```yaml
workflows:
  ticket_pipeline:
    trigger: "new_ticket"
    description: "Handle a new support ticket"
    steps:
      - agent: cso_orchestrator
        action: delegate
        to_lane: support
      - agent: support_lead
        action: coordinate
        specialists: [triage_agent, troubleshooter_agent]
        optional: [escalation_agent]  # Only if escalation detected
      - agent: support_lead
        action: synthesize
      - agent: cso_orchestrator
        action: evaluate_and_finalize

  health_alert_pipeline:
    trigger: "health_score_drop"
    steps:
      - agent: cso_orchestrator
        action: delegate
        to_lane: value
      - agent: value_lead
        action: coordinate
        specialists: [health_monitor_agent]
        optional: [call_intel_agent]  # Check recent calls
      - agent: value_lead
        action: synthesize
      - agent: cso_orchestrator
        action: evaluate_and_finalize

  call_analysis_pipeline:
    trigger: "new_call_recording"
    steps:
      - agent: cso_orchestrator
        action: delegate
        to_lane: value
      - agent: value_lead
        action: coordinate
        specialists: [call_intel_agent]
      - agent: value_lead
        action: synthesize
      - agent: cso_orchestrator
        action: evaluate_and_finalize

  qbr_generation_pipeline:
    trigger: "qbr_scheduled"
    steps:
      - agent: cso_orchestrator
        action: delegate
        to_lanes: [value, delivery]  # Multi-lane
      - agent: value_lead
        action: coordinate
        specialists: [health_monitor_agent, call_intel_agent, qbr_agent]
      - agent: delivery_lead
        action: coordinate
        specialists: [sow_agent, deployment_intel_agent]
      - agent: cso_orchestrator
        action: evaluate_and_finalize
```

---

## 12. Phase F: Agent Implementation (3–4 days)

This is the big migration phase. We implement all 13 agents using the framework
built in Phases B–E.

### F1: Implement Orchestrator (Tier 1)

**File: `backend/app/agents/orchestrator.py`** (rewrite, ~300 lines)

The Orchestrator becomes a full Tier 1 supervisor agent:

```python
class Orchestrator(BaseAgent):
    tier = 1

    async def perceive(self, event):
        """Read the event, pull customer context, add to working memory."""

    async def think(self, event, context):
        """
        Strategic decomposition:
        - What type of event is this?
        - Which lane(s) need to handle it?
        - What's the priority?
        - Are there cross-lane dependencies?
        Uses Claude with tools to query customer data and past events.
        """

    async def act(self, plan):
        """
        Delegation:
        - Send task_assignments to Lane Leads via message board
        - Wait for deliverables to come back
        - Handle timeouts and failures
        """

    async def evaluate(self, deliverables):
        """
        Quality gate:
        - Check completeness of each lane's output
        - Verify nothing was missed
        - Send feedback if quality is insufficient → retry
        """

    async def finalize(self, all_outputs):
        """
        Synthesis:
        - Combine all lane outputs into a coherent final result
        - Update the relevant database records
        - Create action items if needed
        - Broadcast via WebSocket
        """
```

### F2: Implement 3 Lane Leads (Tier 2)

**New files:**
- `backend/app/agents/leads/support_lead.py` (~200 lines)
- `backend/app/agents/leads/value_lead.py` (~200 lines)
- `backend/app/agents/leads/delivery_lead.py` (~200 lines)

Each Lane Lead follows the same pattern:

```python
class SupportLead(BaseAgent):
    tier = 2
    lane = "support"

    async def perceive(self, task_assignment):
        """Read the task from Orchestrator, understand scope."""

    async def think(self, task, context):
        """
        Plan which specialists to engage:
        - Parse the task requirements
        - Check which specialists are available
        - Determine sequence (parallel or sequential)
        """

    async def act(self, plan):
        """
        Coordinate specialists:
        - Send task_assignments to specialists
        - Collect deliverables
        - Handle specialist escalations
        """

    async def finalize(self, specialist_outputs):
        """
        Lane synthesis:
        - Combine specialist outputs
        - Add lane-level insights
        - Send deliverable back to Orchestrator
        """
```

**What each lead manages:**

| Lead | Specialists | Common Workflows |
|---|---|---|
| Support Lead | Triage, Troubleshooter, Escalation | Ticket handling, incident response |
| Value Lead | Health Monitor, Call Intel, QBR | Customer health, call analysis, reviews |
| Delivery Lead | SOW, Deployment Intel | Scope tracking, deployment monitoring |

### F3: Migrate 8 Specialist Agents (Tier 3)

Each specialist gets migrated from single-shot to pipeline-aware. The migration follows
a consistent pattern:

**For each agent:**
1. Move system prompt to `agent_profiles.yaml`
2. Replace `execute()` with pipeline methods (perceive/retrieve/think/act/reflect)
3. Add memory integration (read from episodic + semantic before thinking)
4. Add tool access (use tools during think/act instead of guessing)
5. Add trait hooks (traits fire at each stage)
6. Write execution results to episodic memory

**Migration order (easiest → hardest):**

| Order | Agent | Why This Order |
|---|---|---|
| 1 | Health Monitor | Simplest: query health data → analyze → output |
| 2 | Triage Agent | Already uses RAG — easiest to add tools |
| 3 | Call Intel | Clear input (transcript) → clear output (analysis) |
| 4 | Troubleshooter | Needs RAG tools, similar-ticket search |
| 5 | Escalation Manager | Needs message board integration for escalation flow |
| 6 | QBR Generator | Complex: multi-source data gathering |
| 7 | SOW Agent | Complex: template-based, may need approval workflow |
| 8 | Deployment Intel | Needs deployment data tools, risk assessment |

**Example migration — Triage Agent:**

```python
# BEFORE (current):
class TriageAgent(BaseAgent):
    async def execute(self, ticket_data):
        prompt = f"Classify this ticket: {ticket_data}"
        result = await claude.generate(self.system_prompt, prompt)
        return json.loads(result)

# AFTER (migrated):
class TriageAgent(BaseAgent):
    tier = 3
    lane = "support"

    async def perceive(self, task):
        """Read the ticket, add to working memory."""
        self.memory.set_context("ticket", task["ticket_data"])
        # Traits fire: escalation_detection adds "check urgency" context

    async def retrieve(self, task):
        """Search for similar past tickets and customer context."""
        similar = await self.memory.recall_similar(task["description"], n=3)
        customer_knowledge = await self.memory.query_knowledge(task["customer_name"])
        self.memory.set_context("similar_tickets", similar)
        self.memory.set_context("customer_context", customer_knowledge)

    async def think(self, task, context):
        """Reason about the ticket with full context and tools."""
        # Claude call with tools: can query_customer_db, search_similar_tickets
        result = await self.claude.generate_with_tools(
            system_prompt=self.profile.system_instruction,
            messages=[{"role": "user", "content": self._build_prompt(task, context)}],
            tools=self.tools
        )
        return result

    async def act(self, thinking_result):
        """Produce the triage output."""
        return {
            "severity": thinking_result["severity"],
            "category": thinking_result["category"],
            "suggested_response": thinking_result["response"],
            "similar_tickets": thinking_result.get("similar", []),
            "confidence": thinking_result.get("confidence", 5)
        }

    async def reflect(self, output):
        """Self-assess the triage quality."""
        # Saves to episodic memory
        await self.memory.remember_execution(
            summary=f"Triaged ticket: severity {output['severity']}, "
                    f"category {output['category']}, confidence {output['confidence']}",
            importance=output["severity"]
        )
```

### F4: Upgrade Memory Agent (Tier 4)

**File: `backend/app/agents/customer_memory.py`** (rewrite, ~200 lines)

The Memory Agent becomes the Tier 4 foundation — a service agent that other agents
call to get customer context:

```python
class CustomerMemoryAgent(BaseAgent):
    tier = 4

    async def serve_context_request(self, agent_id, customer_id, query):
        """
        Called by any agent that needs customer context.
        Returns:
        - Customer profile summary
        - Recent health scores and trend
        - Recent tickets and their outcomes
        - Recent call insights
        - Relevant knowledge base entries
        """

    async def update_customer_memory(self, customer_id, new_data, source_agent):
        """
        Called after an agent produces output that should update
        the customer's memory (new insight, resolved ticket, etc.)
        """
```

---

## 13. Phase G: Frontend — Complete Redesign (5–7 days)

The frontend gets completely redesigned to showcase every capability of the new
agent architecture. This is a fresh build, not an enhancement of the old frontend.

### New Pages and Panels

**1. Agent Hierarchy View** — `AgentHierarchyPage.jsx`
```
What it shows:
- 4-tier tree visualization (Orchestrator → Lane Leads → Specialists → Foundation)
- Live delegation flow: see tasks flowing down and deliverables flowing up
- Click any agent to see its profile card
- Color-coded by lane (Support = blue, Value = green, Delivery = purple)
- Animated connections showing active message threads
```

**2. Pipeline Execution Page** — `PipelineExecutionPage.jsx`
```
What it shows:
- Real-time pipeline stages per agent (perceive → think → act → reflect)
- Progress bar for each stage with timing
- Tool calls displayed inline (which tool, what args, what result)
- Memory retrievals shown (what the agent remembered)
- WebSocket-driven: updates live as stages complete
```

**3. Message Board Page** — `MessageBoardPage.jsx`
```
What it shows:
- Inter-agent communication feed (like a team Slack)
- Threaded conversations grouped by event
- Message type badges (task_assignment, deliverable, escalation, etc.)
- Filter by agent, lane, or message type
- Click a thread to see the full delegation chain
```

**4. Memory Inspector** — `MemoryInspectorPage.jsx`
```
What it shows:
- Browse agent episodic memories (past runs with summaries)
- View shared knowledge pools per lane
- Search across all memory with semantic query
- See memory importance scores and recency
- Visualize what an agent "remembers" about a customer
```

**5. Execution Trace Viewer** — `ExecutionTracePage.jsx`
```
What it shows:
- Drill into any agent run
- See every pipeline stage: input → output → tools called → timing
- Token usage per stage
- Error details if any stage failed
- Compare across runs: "How did this agent handle similar tasks before?"
```

**6. Agent Profile Cards** — Panel component used across pages
```
What it shows:
- Agent name, role, tier, lane
- Personality description
- Active traits (with descriptions)
- Available tools (with descriptions)
- Recent execution stats (avg time, success rate, confidence)
```

**7. Workflow Viewer** — `WorkflowViewerPage.jsx`
```
What it shows:
- How events flow through the 4-tier hierarchy
- Active workflow instances with status per step
- Workflow definitions from workflows.yaml (visual flow diagram)
- Historical: how past events were processed
```

**8. Live Dashboard** — `DashboardPage.jsx` (redesigned)
```
What it shows:
- Real-time activity stream: events coming in, agents activating, stages completing
- Active pipeline runs with progress
- Agent status grid: who's working, who's idle
- Key metrics: tickets handled, health scores monitored, calls analyzed
- Recent message board highlights
```

### New Zustand Stores

| Store | Manages |
|---|---|
| `pipelineStore.js` | Active pipeline runs, stage progress, WebSocket updates |
| `messageStore.js` | Agent messages, threads, unread counts |
| `memoryStore.js` | Agent memories, knowledge pool contents |
| `hierarchyStore.js` | Agent hierarchy state, delegation flows |
| `executionStore.js` | Execution traces, round details |
| `profileStore.js` | Agent profiles from YAML (loaded from API) |

### New API Endpoints for Frontend

```
GET  /api/v2/pipeline/active              — Active pipeline runs
GET  /api/v2/pipeline/{execution_id}      — Execution trace details
GET  /api/v2/pipeline/{execution_id}/rounds — All rounds for a run

GET  /api/v2/messages                     — Recent messages (paginated)
GET  /api/v2/messages/thread/{id}         — Full thread
GET  /api/v2/messages/agent/{id}          — Agent inbox

GET  /api/v2/memory/{agent_id}/episodic   — Agent's episodic memories
GET  /api/v2/memory/{agent_id}/working    — Agent's current working memory
GET  /api/v2/memory/knowledge/{lane}      — Lane knowledge pool
GET  /api/v2/memory/search                — Cross-memory semantic search

GET  /api/v2/hierarchy                    — Full org structure
GET  /api/v2/hierarchy/agents             — All agent profiles
GET  /api/v2/hierarchy/agents/{id}        — Single agent profile + stats

GET  /api/v2/workflows                    — All workflow definitions
GET  /api/v2/workflows/active             — Active workflow instances
GET  /api/v2/workflows/{id}/status        — Workflow instance status

WebSocket events (new):
  pipeline:stage_started    — A pipeline stage began
  pipeline:stage_completed  — A pipeline stage finished
  pipeline:tool_called      — An agent called a tool
  delegation:task_assigned  — A task was delegated down
  delegation:deliverable    — A deliverable was sent up
  delegation:escalation     — An escalation was triggered
  memory:knowledge_published — New knowledge added to a pool
```

### WebSocket Integration

Every real-time page connects to WebSocket for live updates:

```javascript
// Example: Pipeline Execution page
const ws = useWebSocket();

ws.on('pipeline:stage_completed', (data) => {
  // data: { execution_id, agent_id, stage_name, duration_ms, output_preview }
  pipelineStore.updateStage(data);
});

ws.on('pipeline:tool_called', (data) => {
  // data: { execution_id, agent_id, tool_name, args, result_preview }
  pipelineStore.addToolCall(data);
});
```

---

## 14. Phase H: Integration (1–2 days)

### H1: Celery Task Updates

**File: `backend/app/tasks/agent_tasks.py`** (rewrite)

```python
# BEFORE: Simple wrapper
@celery.task
def run_triage(ticket_data):
    agent = TriageAgent()
    return agent.execute(ticket_data)

# AFTER: Pipeline-aware execution
@celery.task
def run_agent_pipeline(agent_id, event_id, task_data):
    """
    Run any agent through its tier-specific pipeline.
    1. Load agent profile from YAML
    2. Initialize agent with memory, tools, traits
    3. Run pipeline engine
    4. Log execution trace
    5. Broadcast progress via WebSocket
    6. Return result
    """
    agent = AgentFactory.create(agent_id)
    engine = PipelineEngine()
    result = engine.run(agent, task_data)
    return result
```

### H2: WebSocket New Event Types

Add new event types to the WebSocket manager:

```python
# New broadcast types:
await ws_manager.broadcast("pipeline:stage_started", {
    "execution_id": exec_id,
    "agent_id": agent_id,
    "stage_name": "think",
    "timestamp": now()
})

await ws_manager.broadcast("delegation:task_assigned", {
    "from_agent": "cso_orchestrator",
    "to_agent": "support_lead",
    "task_preview": "Triage ticket #789...",
    "priority": 8
})
```

### H3: Agent Factory

**New file: `backend/app/agents/agent_factory.py`** (~80 lines)

```python
class AgentFactory:
    """Creates fully initialized agents from YAML profiles."""

    @staticmethod
    def create(agent_id: str) -> BaseAgent:
        profile = ProfileLoader.get_agent_profile(agent_id)
        tools = ToolRegistry.resolve_tools(profile.tools)
        traits = TraitRegistry.resolve_traits(profile.traits)
        memory = MemoryManager(agent_id, profile.lane)

        agent_class = AGENT_CLASS_MAP[agent_id]
        return agent_class(
            profile=profile,
            tools=tools,
            traits=traits,
            memory=memory,
        )
```

### H4: Updated Seed Data

Add seed data that demonstrates the full hierarchy:

- Sample pipeline execution trace (5+ stages with tool calls)
- Sample message threads (delegation chain for a ticket)
- Sample episodic memories (past agent runs)
- Sample knowledge pool entries (per lane)

---

## 15. The 4-Tier Hierarchy Explained

### How Delegation Actually Flows

Here's a complete example of how a real event flows through all 4 tiers:

```
EVENT: "Customer Acme Corp's health score dropped from 82 to 61"

═══════════════════════════════════════════════════════════════════
TIER 1 — NAVEEN KAPOOR (CS Orchestrator)
═══════════════════════════════════════════════════════════════════

  PERCEIVE: "Health score drop of 21 points for Acme Corp. This is significant."

  RETRIEVE: Queries customer DB → Acme Corp is a $200K ARR account,
            renewal in 45 days. Last QBR was 30 days ago.

  THINK: "This is critical — large account with imminent renewal.
          Need Damon's Value lane to investigate health decline.
          May also need Rachel's Support lane if there are open tickets."

  ACT (Delegate):
    → TASK to Damon Reeves: "Investigate Acme Corp health decline from 82→61.
       Account renews in 45 days, $200K ARR. Priority: CRITICAL.
       Determine root cause and recommended actions."
    → TASK to Rachel Torres: "Check if Acme Corp has open tickets that
       may be contributing to health decline."

═══════════════════════════════════════════════════════════════════
TIER 2 — DAMON REEVES (Value Lead)
═══════════════════════════════════════════════════════════════════

  PERCEIVE: "Health decline investigation for critical renewal-at-risk account."

  THINK: "Need Aisha for score breakdown, Jordan for recent call
          sentiment, and Sofia for renewal risk assessment."

  ACT (Coordinate):
    → TASK to Dr. Aisha Okafor: "Break down Acme Corp health score factors.
       What drove the 21-point decline?"
    → TASK to Jordan Ellis: "Analyze Acme Corp's last 3 calls.
       Any negative sentiment or churn signals?"

  [Waits for specialist deliverables]

  RECEIVE: Aisha says "Product adoption dropped 40%, support
           tickets up 60%, NPS declined"
  RECEIVE: Jordan says "Last call had frustrated tone, mentioned
           competitor evaluation, 3 unresolved action items"

  FINALIZE (Synthesize): "Acme Corp health decline caused by: product adoption
    drop (main driver), increasing support load, and customer frustration.
    Churn risk: HIGH. Recommend: executive sponsor call within 48 hours,
    dedicated support sprint, QBR acceleration."

  → DELIVERABLE to Naveen: [synthesized analysis + recommendations]

═══════════════════════════════════════════════════════════════════
TIER 2 — RACHEL TORRES (Support Lead, parallel)
═══════════════════════════════════════════════════════════════════

  → TASK to Kai Nakamura: "Check open tickets for Acme Corp"
  RECEIVE from Kai: "3 open tickets: 2 medium (integration issues),
                     1 high (data export bug)"

  → DELIVERABLE to Naveen: "3 open tickets contributing to health decline"

═══════════════════════════════════════════════════════════════════
TIER 1 — NAVEEN KAPOOR (quality gate + synthesis)
═══════════════════════════════════════════════════════════════════

  EVALUATE: Both lanes reported. Damon's analysis is comprehensive.
            Rachel's lane confirms active issues.

  FINALIZE: Creates unified response:
    - Updates Acme Corp health record with root cause analysis
    - Creates 3 action items (exec call, support sprint, accelerated QBR)
    - Triggers alert: "CRITICAL: Acme Corp churn risk — renewal in 45 days"
    - Broadcasts via WebSocket to dashboard

═══════════════════════════════════════════════════════════════════
TIER 4 — ATLAS (Foundation, throughout)
═══════════════════════════════════════════════════════════════════

  Atlas served context to every agent that asked:
    - Customer profile, ARR, renewal date
    - Historical health scores
    - Past ticket patterns
    - Previous call insights

  After completion, all agents wrote their results back to Atlas:
    - Episodic: Each agent saved a summary of what they did
    - Semantic: "Acme Corp showing churn signals" published to knowledge pool
```

### Tier Responsibilities Summary

| Tier | Role | Thinks About | Delegates To | Reports To |
|---|---|---|---|---|
| 1 | Supervisor | Strategy, prioritization, quality | Tier 2 Lane Leads | — |
| 2 | Lane Leads | Workflow planning, specialist coordination | Tier 3 Specialists | Tier 1 |
| 3 | Specialists | Task execution, analysis, diagnosis | — | Tier 2 Lane Lead |
| 4 | Foundation | Data retrieval, memory management | — | Serves all tiers |

---

## 16. File Inventory

Every new and modified file, organized by phase:

### Phase 0: Fathom Integration

| Action | File | Est. Lines | Description |
|---|---|---|---|
| MODIFY | `backend/app/config.py` | ~5 changed | Add FATHOM_API_KEY, remove old fields |
| REWRITE | `backend/app/services/fathom_service.py` | ~200 | Real Fathom API client (httpx) |
| NEW | `backend/app/routers/webhooks.py` | ~80 | Webhook receiver for Fathom events |
| MODIFY | `backend/app/routers/insights.py` | ~40 changed | Real sync-fathom endpoint |
| MODIFY | `backend/app/main.py` | ~3 changed | Register webhooks router |
| MODIFY | `backend/requirements.txt` | ~1 changed | Add httpx |
| MODIFY | `.env.example` | ~3 changed | Fathom API key fields |

### Phase A: Documentation

| Action | File | Est. Lines | Description |
|---|---|---|---|
| REWRITE | `docs/PRD.md` | ~400 | Updated features + user stories |
| REWRITE | `docs/WIREFRAMES.md` | ~600 | New page designs + component specs |
| REWRITE | `docs/API_CONTRACT.md` | ~500 | New endpoints + schemas |
| REWRITE | `docs/DATABASE_SCHEMA.md` | ~300 | New tables + YAML schemas |
| MODIFY | `CLAUDE.md` | ~200 modify | Updated structure + rules |

### Phase B: Foundation

| Action | File | Est. Lines | Description |
|---|---|---|---|
| NEW | `backend/config/org_structure.yaml` | ~80 | Hierarchy and lanes |
| NEW | `backend/config/agent_profiles.yaml` | ~500 | 13 agent profiles |
| NEW | `backend/config/pipeline.yaml` | ~120 | Pipeline configs per tier |
| NEW | `backend/app/agents/profile_loader.py` | ~120 | YAML loader + validator |
| NEW | `backend/app/agents/tool_registry.py` | ~80 | Tool name → function map |
| NEW | `backend/app/agents/tools/__init__.py` | ~20 | Tools package |
| NEW | `backend/app/agents/tools/customer_tools.py` | ~60 | Customer + health tools |
| NEW | `backend/app/agents/tools/ticket_tools.py` | ~80 | Ticket + SLA tools |
| NEW | `backend/app/agents/tools/insight_tools.py` | ~60 | Call + knowledge tools |
| NEW | `backend/app/agents/tools/action_tools.py` | ~60 | Action item + alert tools |
| NEW | `backend/app/agents/tools/agent_tools.py` | ~40 | Agent output + knowledge tools |
| MODIFY | `backend/app/services/claude_service.py` | ~200 | Add generate_with_tools() |
| NEW | `backend/app/agents/pipeline_engine.py` | ~250 | Multi-stage pipeline runner |
| NEW | `backend/app/agents/execution_logger.py` | ~100 | Structured execution trace |
| NEW | `backend/app/models/execution_round.py` | ~40 | SQLAlchemy model |
| NEW | `backend/app/schemas/execution_round.py` | ~30 | Pydantic schema |
| NEW | `backend/alembic/versions/xxx_add_execution_rounds.py` | ~40 | Migration |

### Phase C: Memory

| Action | File | Est. Lines | Description |
|---|---|---|---|
| NEW | `backend/app/agents/memory/__init__.py` | ~10 | Memory package |
| NEW | `backend/app/agents/memory/memory_manager.py` | ~200 | 3-tier memory coordinator |
| NEW | `backend/app/agents/memory/working_memory.py` | ~50 | In-memory scratchpad |
| NEW | `backend/app/agents/memory/episodic_memory.py` | ~120 | ChromaDB-backed past runs |
| NEW | `backend/app/agents/memory/semantic_memory.py` | ~120 | ChromaDB shared knowledge |

### Phase D: Traits + Reflection

| Action | File | Est. Lines | Description |
|---|---|---|---|
| NEW | `backend/app/agents/traits/__init__.py` | ~10 | Traits package |
| NEW | `backend/app/agents/traits/base_trait.py` | ~60 | Abstract base trait |
| NEW | `backend/app/agents/traits/registry.py` | ~50 | Trait registry |
| NEW | `backend/app/agents/traits/strategic_oversight.py` | ~40 | Tier 1 trait |
| NEW | `backend/app/agents/traits/quality_evaluation.py` | ~40 | Tier 1 trait |
| NEW | `backend/app/agents/traits/delegation.py` | ~40 | Tier 1, 2 trait |
| NEW | `backend/app/agents/traits/workflow_coordination.py` | ~40 | Tier 2 trait |
| NEW | `backend/app/agents/traits/synthesis.py` | ~40 | Tier 2 trait |
| NEW | `backend/app/agents/traits/confidence_scoring.py` | ~40 | Tier 3 trait |
| NEW | `backend/app/agents/traits/escalation_detection.py` | ~50 | Tier 3 trait |
| NEW | `backend/app/agents/traits/sla_awareness.py` | ~40 | Tier 3 trait |
| NEW | `backend/app/agents/traits/customer_sentiment.py` | ~40 | All tiers trait |
| NEW | `backend/app/agents/reflection_engine.py` | ~150 | Tier-aware reflection |

### Phase E: Message Board + Hierarchy

| Action | File | Est. Lines | Description |
|---|---|---|---|
| NEW | `backend/app/models/agent_message.py` | ~40 | SQLAlchemy model |
| NEW | `backend/app/schemas/agent_message.py` | ~50 | Pydantic schemas |
| NEW | `backend/app/services/message_service.py` | ~180 | Message CRUD + threading |
| NEW | `backend/app/routers/messages.py` | ~80 | API endpoints |
| NEW | `backend/config/workflows.yaml` | ~100 | Workflow definitions |
| NEW | `backend/alembic/versions/xxx_add_agent_messages.py` | ~40 | Migration |

### Phase F: Agent Implementation

| Action | File | Est. Lines | Description |
|---|---|---|---|
| MODIFY | `backend/app/agents/base_agent.py` | ~250 | Pipeline-aware base class |
| REWRITE | `backend/app/agents/orchestrator.py` | ~300 | Tier 1 supervisor |
| NEW | `backend/app/agents/leads/__init__.py` | ~10 | Leads package |
| NEW | `backend/app/agents/leads/support_lead.py` | ~200 | Support lane lead |
| NEW | `backend/app/agents/leads/value_lead.py` | ~200 | Value lane lead |
| NEW | `backend/app/agents/leads/delivery_lead.py` | ~200 | Delivery lane lead |
| MODIFY | `backend/app/agents/health_monitor.py` | ~200 | Pipeline migration |
| MODIFY | `backend/app/agents/triage_agent.py` | ~220 | Pipeline migration |
| MODIFY | `backend/app/agents/call_intel_agent.py` | ~220 | Pipeline migration |
| MODIFY | `backend/app/agents/troubleshooter.py` | ~200 | Pipeline migration |
| MODIFY | `backend/app/agents/escalation_agent.py` | ~180 | Pipeline migration |
| MODIFY | `backend/app/agents/qbr_agent.py` | ~220 | Pipeline migration |
| MODIFY | `backend/app/agents/sow_agent.py` | ~220 | Pipeline migration |
| MODIFY | `backend/app/agents/deployment_intel.py` | ~200 | Pipeline migration |
| REWRITE | `backend/app/agents/memory_agent.py` | ~200 | Tier 4 foundation |
| NEW | `backend/app/agents/agent_factory.py` | ~80 | Agent creation factory |

### Phase G: Frontend (Complete Redesign)

| Action | File | Est. Lines | Description |
|---|---|---|---|
| NEW | `frontend/src/pages/AgentHierarchyPage.jsx` | ~200 | 4-tier tree view |
| NEW | `frontend/src/pages/PipelineExecutionPage.jsx` | ~250 | Real-time pipeline |
| NEW | `frontend/src/pages/MessageBoardPage.jsx` | ~200 | Agent communication |
| NEW | `frontend/src/pages/MemoryInspectorPage.jsx` | ~200 | Memory browser |
| NEW | `frontend/src/pages/ExecutionTracePage.jsx` | ~200 | Drill-down traces |
| NEW | `frontend/src/pages/WorkflowViewerPage.jsx` | ~200 | Workflow visualization |
| REWRITE | `frontend/src/pages/DashboardPage.jsx` | ~300 | Redesigned dashboard |
| NEW | `frontend/src/components/hierarchy/HierarchyTree.jsx` | ~150 | Tree component |
| NEW | `frontend/src/components/hierarchy/AgentProfileCard.jsx` | ~100 | Profile card |
| NEW | `frontend/src/components/hierarchy/DelegationFlow.jsx` | ~120 | Flow animation |
| NEW | `frontend/src/components/pipeline/PipelineTimeline.jsx` | ~150 | Stage timeline |
| NEW | `frontend/src/components/pipeline/StageCard.jsx` | ~80 | Stage detail card |
| NEW | `frontend/src/components/pipeline/ToolCallLog.jsx` | ~80 | Tool call display |
| NEW | `frontend/src/components/messages/MessageThread.jsx` | ~120 | Thread component |
| NEW | `frontend/src/components/messages/MessageBadge.jsx` | ~40 | Type badge |
| NEW | `frontend/src/components/memory/MemoryEntry.jsx` | ~80 | Memory item |
| NEW | `frontend/src/components/memory/KnowledgePool.jsx` | ~100 | Pool browser |
| NEW | `frontend/src/components/execution/TraceViewer.jsx` | ~150 | Trace component |
| NEW | `frontend/src/stores/pipelineStore.js` | ~100 | Pipeline state |
| NEW | `frontend/src/stores/messageStore.js` | ~80 | Message state |
| NEW | `frontend/src/stores/memoryStore.js` | ~80 | Memory state |
| NEW | `frontend/src/stores/hierarchyStore.js` | ~60 | Hierarchy state |
| NEW | `frontend/src/stores/executionStore.js` | ~80 | Execution state |
| NEW | `frontend/src/stores/profileStore.js` | ~60 | Agent profiles state |
| NEW | `frontend/src/services/pipelineApi.js` | ~60 | Pipeline API client |
| NEW | `frontend/src/services/messageApi.js` | ~50 | Message API client |
| NEW | `frontend/src/services/memoryApi.js` | ~50 | Memory API client |
| NEW | `frontend/src/services/hierarchyApi.js` | ~40 | Hierarchy API client |

### Phase H: Integration

| Action | File | Est. Lines | Description |
|---|---|---|---|
| REWRITE | `backend/app/tasks/agent_tasks.py` | ~150 | Pipeline-aware tasks |
| MODIFY | `backend/app/websocket_manager.py` | ~50 add | New event types |
| NEW | `backend/app/routers/pipeline.py` | ~100 | Pipeline execution API |
| NEW | `backend/app/routers/hierarchy.py` | ~60 | Hierarchy API |
| NEW | `backend/app/routers/memory.py` | ~80 | Memory API |
| NEW | `backend/app/routers/workflows.py` | ~60 | Workflow API |
| MODIFY | `backend/app/utils/seed.py` | ~200 add | Hierarchy seed data |

### Totals

| Category | New Files | Modified Files | Estimated New Lines |
|---|---|---|---|
| Phase 0: Fathom Integration | 1 | 6 | ~200 |
| Phase A: Documentation | 0 | 5 | ~2,000 |
| Phase B: Foundation | 15 | 1 | ~1,880 |
| Phase C: Memory | 5 | 0 | ~500 |
| Phase D: Traits + Reflection | 13 | 0 | ~640 |
| Phase E: Message Board | 6 | 0 | ~490 |
| Phase F: Agents | 5 new + 11 modify | 11 | ~2,900 |
| Phase G: Frontend | 28 | 1 | ~3,830 |
| Phase H: Integration | 4 | 3 | ~700 |
| **TOTAL** | **~77 new** | **~27 modify** | **~13,140** |

---

## 17. Timeline Summary

### Phase Dependencies

```
Phase 0: Fathom (IMMEDIATE) ───┐
                                │
         Phase A: Docs ─────────┴──────────────────────┐
                                                        │
         Phase B: Foundation ───────────────────┐       │
                                                │       │
         Phase C: Memory ──────────┐            │       │
                                   ├── Phase F: Agents ──┐
         Phase D: Traits ──────────┤                     │
                                   │                     ├── Phase H: Integration
         Phase E: Messages ────────┘                     │
                                                         │
                                      Phase G: Frontend ─┘
```

**Dependency rules:**
- **Phase 0 (Fathom) starts IMMEDIATELY** — get real call data flowing before the rebuild
- **Phase A (Docs) starts after Phase 0** — updated docs become the blueprint for everything
- Phases B, C, D, E can **overlap** (C, D, E depend on B but can start as B finishes)
- Phase F requires B, C, D, E to be complete (agents need all the infrastructure)
- Phase G can start once Phase F begins (frontend needs API endpoints to exist)
- Phase H requires F + G to be complete (integration wires everything together)

### Timeline Estimates

| Phase | Estimated Days | Can Start After |
|---|---|---|
| 0: Fathom Integration | 1–2 | Immediately (FIRST) |
| A: Documentation Update | 1–2 | Phase 0 complete |
| B: Foundation | 3–4 | Phase A complete |
| C: Memory | 1–2 | Phase B (day 2+) |
| D: Traits + Reflection | 1–2 | Phase B (day 3+) |
| E: Message Board | 2–3 | Phase B complete |
| F: Agent Implementation | 3–4 | B, C, D, E complete |
| G: Frontend Redesign | 5–7 | Phase F started |
| H: Integration | 1–2 | F + G complete |

### Optimistic vs Realistic

| Scenario | Total Days | Assumption |
|---|---|---|
| **Optimistic** | 19 days | Max overlap, no blockers, single developer focused |
| **Realistic** | 25 days | Some overlap, minor blockers, iterations on quality |
| **Conservative** | 30 days | Sequential phases, refactoring, UI polish iterations |

### Recommended Approach

1. **Start with Phase 0 (Fathom)** — get real call data flowing immediately
2. **Phase A (Docs)** — update PRD, WIREFRAMES, API_CONTRACT, DATABASE_SCHEMA, CLAUDE.md
3. **Phase B** — build the core framework using the docs as the spec
3. **Phase C + D in parallel** once B is mostly done (memory and traits are independent)
4. **Phase E** once message board schema is clear
5. **Phase F** is the critical path — this is where the most complex work happens
6. **Phase G** can start designing while F is being built (API shapes defined in docs)
7. **Phase H** is the final wiring

---

## Summary

We're upgrading from a system of **independent single-shot agents** to a **collaborative
4-tier agent organization** with:

- **13 agents** across 4 tiers (1 Orchestrator + 3 Lane Leads + 8 Specialists + 1 Foundation)
- **Multi-round pipelines** with perceive → retrieve → think → act → reflect stages
- **3-tier memory** (working + episodic + semantic) for context-aware decisions
- **12+ tools** for agents to query real data instead of guessing
- **9+ traits** for pluggable behaviors with lifecycle hooks
- **Message board** for inter-agent delegation, collaboration, and escalation
- **Reflection engine** for self-assessment and higher-level synthesis
- **Full observability** via structured execution traces
- **Complete frontend redesign** to showcase every capability

We keep all existing infrastructure (DB, auth, WebSocket, Celery, routers, schemas)
and rebuild the agent layer on top.

**~77 new files, ~27 modified files, ~13,140 new lines of code.**
**Estimated: 19–30 days.**

---

*This document is the roadmap. Once approved, we start with Phase 0: Fathom Integration.*
