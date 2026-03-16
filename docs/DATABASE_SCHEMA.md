# HivePro CS Control Plane — Database Schema

**Database:** PostgreSQL 16
**ORM:** SQLAlchemy 2.0 + Alembic
**Vector DB:** ChromaDB (RAG + agent memory)
**Config:** YAML (agent profiles, org structure, pipelines, workflows)
**Version:** 3.0 (Agentic Architecture)
**Date:** March 2, 2026

---

## 1. Entity Relationship Overview

```
users ──────────┐
  │              │
  │ cs_owner_id  │ assigned_to_id
  ▼              ▼
customers ◄─── tickets
  │              │
  │              ├── triage_result (JSONB)
  │              ├── troubleshoot_result (JSONB)
  │              └── escalation_summary (JSONB)
  │
  ├── health_scores (time-series)
  ├── call_insights
  │     └── action_items (polymorphic source)
  ├── agent_logs
  ├── events ◄──── agent_execution_rounds (via event_id)
  ├── alerts
  └── reports

agent_execution_rounds ── tracks pipeline stages per agent run
  └── links to: events (trigger), agent_logs (legacy compat)

agent_messages ── inter-agent communication board
  └── links to: events (context), threads (self-referencing parent_id)

ChromaDB (external):
  ├── ticket_embeddings       (existing — RAG for similar tickets)
  ├── call_insight_embeddings (existing — RAG for similar calls)
  ├── problem_embeddings      (existing — cross-customer patterns)
  ├── episodic_memory         (NEW — per-agent execution diary)
  └── shared_knowledge        (NEW — lane-scoped knowledge pool)

YAML Config (on disk):
  ├── config/org_structure.yaml     (hierarchy, lanes, reporting lines)
  ├── config/agent_profiles.yaml    (13 agent personalities, traits, tools)
  ├── config/pipeline.yaml          (tier-specific pipeline stages)
  └── config/workflows.yaml         (event-type workflow definitions)
```

---

## 2. Existing Tables (10) — Unchanged

### 2.1 users

Stores CS team members who log into the system.

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'cs_engineer',
    avatar_url      TEXT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Roles: admin, cs_manager, cs_engineer, viewer
-- admin: full access, user management, agent config
-- cs_manager: dashboard, all customers, reports, alerts
-- cs_engineer: assigned customers, tickets, insights
-- viewer: read-only access to dashboard and reports
```

**Seed Users:**
| Email | Name | Role |
|-------|------|------|
| ayushmaan@hivepro.com | Ayushmaan Naruka | admin |
| ariza@hivepro.com | Ariza Zehra | admin |
| vignesh@hivepro.com | Vignesh | cs_engineer |
| chaitanya@hivepro.com | Chaitanya | cs_engineer |
| kazi@hivepro.com | Kazi | cs_manager |

---

### 2.2 customers

Core customer profiles — the companies HivePro serves.

```sql
CREATE TABLE customers (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(255) NOT NULL,
    industry                VARCHAR(100),
    tier                    VARCHAR(50),
    contract_start          DATE,
    renewal_date            DATE,
    primary_contact_name    VARCHAR(255),
    primary_contact_email   VARCHAR(255),
    cs_owner_id             UUID REFERENCES users(id),
    deployment_mode         VARCHAR(50) DEFAULT 'OVA',
    product_version         VARCHAR(50),
    integrations            JSONB DEFAULT '[]',
    known_constraints       JSONB DEFAULT '[]',
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_cs_owner ON customers(cs_owner_id);
CREATE INDEX idx_customers_tier ON customers(tier);
CREATE INDEX idx_customers_renewal ON customers(renewal_date);
```

**Field Notes:**
- `tier`: enterprise, mid_market, smb
- `deployment_mode`: OVA, Cloud, Hybrid, On-Premise
- `integrations`: JSON array of integration names, e.g. `["Qualys", "CrowdStrike", "ServiceNow"]`
- `known_constraints`: JSON array, e.g. `["EDR installed", "Air-gapped network", "No root access"]`
- `metadata`: Flexible JSON for future fields

**Seed Data (10 Customers):**
| Name | Industry | Tier | CS Owner | Health |
|------|----------|------|----------|--------|
| Acme Corp | Banking | Enterprise | Vignesh | 42 (HIGH RISK) |
| Beta Financial | Finance | Enterprise | Vignesh | 78 (HEALTHY) |
| Gamma Telecom | Telecom | Enterprise | Chaitanya | 55 (WATCH) |
| Delta Health | Healthcare | Mid-Market | Chaitanya | 91 (HEALTHY) |
| Epsilon Insurance | Insurance | Enterprise | Vignesh | 38 (HIGH RISK) |
| Zeta Retail | Retail | Mid-Market | Chaitanya | 67 (WATCH) |
| Eta Pharma | Pharma | Enterprise | Vignesh | 85 (HEALTHY) |
| Theta Energy | Energy | Mid-Market | Chaitanya | 72 (HEALTHY) |
| Iota Defense | Defense | Enterprise | Vignesh | 44 (HIGH RISK) |
| Kappa Logistics | Logistics | SMB | Chaitanya | 60 (WATCH) |

---

### 2.3 health_scores

Time-series health scores calculated daily (or on demand).

```sql
CREATE TABLE health_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID REFERENCES customers(id) ON DELETE CASCADE,
    score           INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    factors         JSONB NOT NULL,
    risk_flags      JSONB DEFAULT '[]',
    risk_level      VARCHAR(20),
    calculated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_customer_date ON health_scores(customer_id, calculated_at DESC);
CREATE INDEX idx_health_risk_level ON health_scores(risk_level);
```

**Field Notes:**
- `score`: 0-100 composite score
- `factors`: JSON object with 6 weighted factors:
  ```json
  {
    "ticket_severity": 18,
    "sla_compliance": 15,
    "sentiment": 12,
    "engagement": 10,
    "deployment_health": 15,
    "resolution_rate": 12
  }
  ```
- `risk_flags`: JSON array of string descriptions, e.g. `["3 overdue tickets", "Negative sentiment trend"]`
- `risk_level`: healthy (70-100), watch (50-69), high_risk (25-49), critical (0-24), trending_down (dropped 15+ in 7 days), renewal_risk (at-risk + renewal < 90 days)

---

### 2.4 tickets

Jira tickets mirrored into the system with AI-generated triage and troubleshooting data.

```sql
CREATE TABLE tickets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jira_id             VARCHAR(50) UNIQUE,
    customer_id         UUID REFERENCES customers(id),
    summary             TEXT NOT NULL,
    description         TEXT,
    ticket_type         VARCHAR(50),
    severity            VARCHAR(10),
    status              VARCHAR(50),
    assigned_to_id      UUID REFERENCES users(id),
    triage_result       JSONB,
    troubleshoot_result JSONB,
    escalation_summary  JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    sla_deadline        TIMESTAMPTZ
);

CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_severity ON tickets(severity);
CREATE INDEX idx_tickets_jira ON tickets(jira_id);
CREATE INDEX idx_tickets_assigned ON tickets(assigned_to_id);
CREATE INDEX idx_tickets_sla ON tickets(sla_deadline) WHERE status NOT IN ('resolved', 'closed');
```

**Field Notes:**
- `ticket_type`: deployment, scan_failure, connector, performance, ui, integration, feature_request
- `severity`: P1, P2, P3, P4
- `status`: open, in_progress, waiting, resolved, closed
- `triage_result` JSONB shape:
  ```json
  {
    "category": "scan_failure",
    "severity_recommendation": "P1",
    "confidence": 0.92,
    "suggested_action": "Check scanner configuration for subnet range",
    "duplicate_check": {
      "is_duplicate": false,
      "similar_tickets": ["JIRA-987", "JIRA-654"]
    },
    "triaged_at": "2026-02-27T14:23:02Z"
  }
  ```
- `troubleshoot_result` JSONB shape:
  ```json
  {
    "root_cause": "Scanner profile CIDR range does not include subnet 10.0.1.x",
    "confidence": 0.78,
    "evidence": ["Scanner config shows 10.0.0.0/24", "Subnet 10.0.1.x is in a different VLAN"],
    "next_step": "Update scanner profile to include 10.0.0.0/16 or add 10.0.1.0/24 explicitly",
    "diagnosed_at": "2026-02-27T14:30:00Z"
  }
  ```
- `escalation_summary` JSONB shape:
  ```json
  {
    "technical_summary": "Scan failure due to network segmentation.",
    "evidence": ["Packet capture shows ICMP unreachable", "Scanner logs show timeout after 30s"],
    "reproduction_steps": ["1. Navigate to scan config", "2. Run scan against 10.0.1.x", "3. Observe timeout"],
    "customer_update_draft": "We've identified the issue as a network configuration matter...",
    "escalated_at": "2026-02-27T15:00:00Z"
  }
  ```
- SLA deadlines: P1=4h, P2=8h, P3=3d, P4=7d from creation

---

### 2.5 call_insights

Processed call insights from Fathom recordings.

```sql
CREATE TABLE call_insights (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id             UUID REFERENCES customers(id),
    fathom_recording_id     VARCHAR(255),
    call_date               TIMESTAMPTZ NOT NULL,
    participants            JSONB DEFAULT '[]',
    summary                 TEXT,
    decisions               JSONB DEFAULT '[]',
    action_items            JSONB DEFAULT '[]',
    risks                   JSONB DEFAULT '[]',
    sentiment               VARCHAR(20),
    sentiment_score         FLOAT,
    key_topics              JSONB DEFAULT '[]',
    customer_recap_draft    TEXT,
    raw_transcript          TEXT,
    processed_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_insights_customer_date ON call_insights(customer_id, call_date DESC);
CREATE INDEX idx_insights_sentiment ON call_insights(sentiment);
```

**Field Notes:**
- `participants`: `[{"name": "John Doe", "role": "customer"}, {"name": "Vignesh", "role": "cs_engineer"}]`
- `action_items`: `[{"owner": "Vignesh", "task": "Schedule follow-up", "deadline": "2026-03-01", "status": "pending"}]`
- `sentiment`: positive, neutral, negative
- `sentiment_score`: -1.0 (very negative) to 1.0 (very positive)

---

### 2.6 agent_logs

Activity logs from all AI agents (legacy — kept for backward compat; new pipeline runs use `agent_execution_rounds`).

```sql
CREATE TABLE agent_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name          VARCHAR(100) NOT NULL,
    agent_type          VARCHAR(50),
    event_type          VARCHAR(100),
    trigger_event       VARCHAR(100),
    customer_id         UUID REFERENCES customers(id),
    input_summary       TEXT,
    output_summary      TEXT,
    reasoning_summary   TEXT,
    status              VARCHAR(20) DEFAULT 'running',
    duration_ms         INTEGER,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_logs_agent_date ON agent_logs(agent_name, created_at DESC);
CREATE INDEX idx_agent_logs_customer ON agent_logs(customer_id);
CREATE INDEX idx_agent_logs_status ON agent_logs(status);
```

**Field Notes:**
- `agent_name`: cso_orchestrator, customer_memory, call_intel_agent, health_monitor_agent, qbr_agent, triage_agent, troubleshooter_agent, escalation_agent, sow_agent, deployment_intel_agent, support_lead, value_lead, delivery_lead
- `agent_type`: tier_1, tier_2, tier_3, tier_4
- `status`: running, completed, failed, escalated

---

### 2.7 events

Event queue — the central nervous system of the orchestrator.

```sql
CREATE TABLE events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(100) NOT NULL,
    source          VARCHAR(50),
    payload         JSONB NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    routed_to       VARCHAR(100),
    customer_id     UUID REFERENCES customers(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_date ON events(created_at DESC);
```

**Field Notes:**
- `source`: jira_webhook, fathom_webhook, fathom_sync, cron, manual, slack
- `status`: pending, processing, completed, failed

---

### 2.8 alerts

Risk alerts generated by the Health Monitoring Agent.

```sql
CREATE TABLE alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID REFERENCES customers(id) ON DELETE CASCADE,
    alert_type          VARCHAR(50) NOT NULL,
    severity            VARCHAR(20),
    title               TEXT NOT NULL,
    description         TEXT,
    suggested_action    TEXT,
    similar_past_issues JSONB DEFAULT '[]',
    assigned_to_id      UUID REFERENCES users(id),
    status              VARCHAR(20) DEFAULT 'open',
    slack_notified      BOOLEAN DEFAULT false,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

CREATE INDEX idx_alerts_customer ON alerts(customer_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_severity ON alerts(severity);
```

**Field Notes:**
- `alert_type`: high_risk, watch, trending_down, renewal_risk, ticket_sla_breach
- `severity`: critical, high, medium, low
- `status`: open, acknowledged, in_progress, resolved, dismissed

---

### 2.9 action_items

Action items from calls, tickets, or alerts. Polymorphic source.

```sql
CREATE TABLE action_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID REFERENCES customers(id),
    source_type     VARCHAR(50),
    source_id       UUID,
    owner_id        UUID REFERENCES users(id),
    title           TEXT NOT NULL,
    description     TEXT,
    deadline        TIMESTAMPTZ,
    status          VARCHAR(20) DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_actions_customer ON action_items(customer_id);
CREATE INDEX idx_actions_owner ON action_items(owner_id);
CREATE INDEX idx_actions_status ON action_items(status);
CREATE INDEX idx_actions_deadline ON action_items(deadline) WHERE status = 'pending';
```

**Field Notes:**
- `source_type`: call_insight, ticket, alert, manual, agent_pipeline
- `source_id`: UUID of the source record
- `status`: pending, in_progress, completed, overdue

---

### 2.10 reports

Generated reports (weekly digests, monthly reports, QBRs).

```sql
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type     VARCHAR(50) NOT NULL,
    customer_id     UUID REFERENCES customers(id),
    title           TEXT NOT NULL,
    content         JSONB NOT NULL,
    period_start    DATE,
    period_end      DATE,
    generated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_type ON reports(report_type);
CREATE INDEX idx_reports_customer ON reports(customer_id);
CREATE INDEX idx_reports_date ON reports(generated_at DESC);
```

**Field Notes:**
- `report_type`: weekly_digest, monthly_report, qbr
- `customer_id`: NULL for org-wide reports (weekly/monthly), set for QBRs
- `content`: Structured JSON — shape varies by report type (see API Contract for response formats)

---

## 3. New Tables (Agentic Architecture)

### 3.1 agent_execution_rounds

Tracks every stage of every pipeline run for full observability. Each row is one pipeline stage execution.

```sql
CREATE TABLE agent_execution_rounds (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id    UUID NOT NULL,
    event_id        UUID REFERENCES events(id),
    agent_id        VARCHAR(100) NOT NULL,
    agent_name      VARCHAR(255),
    tier            INTEGER NOT NULL CHECK (tier >= 1 AND tier <= 4),
    stage_number    INTEGER NOT NULL,
    stage_name      VARCHAR(100) NOT NULL,
    lane            VARCHAR(50),
    stage_type      VARCHAR(50) NOT NULL,
    input_summary   TEXT,
    output_summary  TEXT,
    tools_called    JSONB DEFAULT '[]',
    tokens_used     INTEGER,
    duration_ms     INTEGER,
    confidence      FLOAT,
    status          VARCHAR(20) NOT NULL DEFAULT 'running',
    error_message   TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exec_rounds_execution ON agent_execution_rounds(execution_id);
CREATE INDEX idx_exec_rounds_agent ON agent_execution_rounds(agent_id, created_at DESC);
CREATE INDEX idx_exec_rounds_event ON agent_execution_rounds(event_id);
CREATE INDEX idx_exec_rounds_status ON agent_execution_rounds(status);
CREATE INDEX idx_exec_rounds_tier ON agent_execution_rounds(tier);
CREATE INDEX idx_exec_rounds_lane ON agent_execution_rounds(lane);
```

**Field Notes:**
- `execution_id`: Groups all stages of one pipeline run. Multiple rows share the same execution_id.
- `agent_id`: One of the 13 agent IDs (e.g., `cso_orchestrator`, `triage_agent`, `customer_memory`)
- `agent_name`: Human-readable name (e.g., "Naveen Kapoor", "Kai Nakamura")
- `tier`: 1 (Supervisor), 2 (Lane Lead), 3 (Specialist), 4 (Foundation)
- `lane`: support, value, delivery, or NULL (for T1 Supervisor and T4 Foundation). Denormalized from agent profile for fast filtering.
- `stage_name`: Human-readable stage label (e.g., "Event Analysis", "Memory Retrieval")
- `stage_type`: perceive, retrieve, think, act, reflect, quality_gate, finalize
- `tools_called` JSONB shape:
  ```json
  [
    {
      "tool_name": "query_customer_db",
      "arguments": {"customer_id": "cust-001"},
      "result_preview": "Acme Corp, Enterprise, health=42",
      "duration_ms": 120
    },
    {
      "tool_name": "search_similar_tickets",
      "arguments": {"query": "scan failure subnet"},
      "result_preview": "3 similar tickets found",
      "duration_ms": 340
    }
  ]
  ```
- `confidence`: 0.0-1.0, set during `reflect` stage
- `status`: running, completed, failed, skipped
- `metadata` JSONB shape (extensible):
  ```json
  {
    "memory_retrieved": 3,
    "delegated_to": ["triage_agent", "troubleshooter_agent"],
    "quality_gate_passed": true,
    "retry_count": 0
  }
  ```

**Execution-level computed fields (used by API, not stored):**
The API returns execution-level aggregates that are computed at query time from individual rounds sharing the same `execution_id`:
- `started_at` = `MIN(created_at)` across all rounds for that execution_id
- `completed_at` = `MAX(created_at)` WHERE status IN ('completed','failed') for that execution_id
- `total_duration_ms` = `SUM(duration_ms)` across all rounds
- `total_tokens` = `SUM(tokens_used)` across all rounds
- `stages_completed` = `COUNT(*)` WHERE status = 'completed'
- `stages_total` = `COUNT(*)` for that execution_id
- `pipeline_type` = derived from tier: 1→"tier_1_supervisor", 2→"tier_2_lead", 3→"tier_3_specialist", 4→"tier_4_foundation"

---

### 3.2 agent_messages

Inter-agent communication board. Every message between agents in the hierarchy.

```sql
CREATE TABLE agent_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id       UUID,
    parent_id       UUID REFERENCES agent_messages(id),
    from_agent      VARCHAR(100) NOT NULL,
    from_name       VARCHAR(255),
    to_agent        VARCHAR(100) NOT NULL,
    to_name         VARCHAR(255),
    message_type    VARCHAR(50) NOT NULL,
    direction       VARCHAR(20) NOT NULL,
    content         TEXT NOT NULL,
    priority        INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    event_id        UUID REFERENCES events(id),
    execution_id    UUID,
    customer_id     UUID REFERENCES customers(id),
    status          VARCHAR(20) DEFAULT 'pending',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_thread ON agent_messages(thread_id);
CREATE INDEX idx_messages_from ON agent_messages(from_agent, created_at DESC);
CREATE INDEX idx_messages_to ON agent_messages(to_agent, created_at DESC);
CREATE INDEX idx_messages_type ON agent_messages(message_type);
CREATE INDEX idx_messages_event ON agent_messages(event_id);
CREATE INDEX idx_messages_execution ON agent_messages(execution_id);
CREATE INDEX idx_messages_status ON agent_messages(status);
```

**Field Notes:**
- `thread_id`: Groups related messages. The first message (usually a task_assignment) sets thread_id = own id. Replies inherit the thread_id.
- `parent_id`: Direct parent message in the thread (self-referencing FK). NULL for thread-starters.
- `from_agent` / `to_agent`: Agent IDs (e.g., `support_lead`, `triage_agent`)
- `from_name` / `to_name`: Human-readable names (e.g., "Rachel Torres", "Kai Nakamura")
- `message_type`: task_assignment, deliverable, request, escalation, feedback
- `direction`: down (Lead → Specialist), up (Specialist → Lead), sideways (peer → peer)
- `priority`: 1 (lowest) to 10 (highest). Escalations default to 8+.
- `status`: pending, read, completed
- `metadata` JSONB shape (extensible):
  ```json
  {
    "lane": "support",
    "tags": ["urgent", "acme-corp"],
    "requires_response": true,
    "response_deadline": "2026-03-02T16:00:00Z"
  }
  ```

---

## 4. ChromaDB Collections

ChromaDB is used for RAG (Retrieval-Augmented Generation) and the agent memory system.

### 4.1 ticket_embeddings (existing)
- **Purpose:** Find similar past tickets for triage and troubleshooting
- **Document:** Ticket summary + description + resolution (if resolved)
- **Metadata:** `{ customer_id, jira_id, ticket_type, severity, status, resolved_at }`
- **Embedding model:** Claude embeddings or all-MiniLM-L6-v2

### 4.2 call_insight_embeddings (existing)
- **Purpose:** Find similar call discussions, surface patterns
- **Document:** Call summary + key topics + risks + decisions
- **Metadata:** `{ customer_id, call_date, sentiment, sentiment_score }`

### 4.3 problem_embeddings (existing)
- **Purpose:** Cross-customer pattern matching for issues and resolutions
- **Document:** Problem description + root cause + resolution steps
- **Metadata:** `{ customer_id, customer_name, ticket_id, resolved_in_days, resolved_at }`

### 4.4 episodic_memory (NEW)

Per-agent diary of past pipeline executions. Enables agents to recall similar past work.

- **Purpose:** "Have I handled a similar situation before?" — semantic search over an agent's past experiences
- **Document:** Execution summary including task, key findings, output, reflection, and confidence score
- **Metadata:**
  ```json
  {
    "agent_id": "triage_agent",
    "agent_name": "Kai Nakamura",
    "customer_id": "cust-001",
    "customer_name": "Acme Corp",
    "event_type": "jira_ticket_created",
    "execution_id": "exec-uuid",
    "importance": 7,
    "tier": 3,
    "lane": "support",
    "timestamp": "2026-03-01T14:23:02Z"
  }
  ```
- **Embedding model:** Same as other collections
- **Retrieval strategy:** Tri-factor scoring:
  - **35% relevance** — Cosine similarity of query to document embedding
  - **25% recency** — Exponential decay: `exp(-days_old / 30)` (half-life ~30 days)
  - **40% importance** — Normalized importance score (1-10 scale)
  - Final score: `0.35 * relevance + 0.25 * recency + 0.40 * (importance / 10)`
- **Consolidation rule:** When an agent has 25+ episodic memories, summarize the oldest 15 into 3 high-level insight entries with importance=9. Keeps active memory manageable.

### 4.5 shared_knowledge (NEW)

Lane-scoped knowledge pool. Agents publish findings that benefit the whole lane or organization.

- **Purpose:** "What does the team know about this?" — semantic search over collectively discovered patterns, best practices, and customer insights
- **Document:** Knowledge entry (finding, pattern, best practice, customer-specific insight)
- **Metadata:**
  ```json
  {
    "agent_id": "call_intel_agent",
    "agent_name": "Jordan Ellis",
    "lane": "value",
    "tags": ["sentiment-analysis", "competitor-mention", "acme-corp"],
    "importance": 8,
    "knowledge_type": "customer_pattern",
    "customer_id": "cust-001",
    "timestamp": "2026-03-01T15:00:00Z"
  }
  ```
- **Lane namespaces:** Entries are tagged with a lane (support, value, delivery, global). Agents query their own lane by default, but cross-lane queries are supported.
  - `support`: Ticket patterns, escalation triggers, SLA insights
  - `value`: Health correlations, sentiment patterns, churn signals, QBR themes
  - `delivery`: Deployment risks, SOW patterns, prerequisite findings
  - `global`: Cross-cutting insights published by any agent for broad visibility
- **Query patterns:**
  ```python
  # Query own lane knowledge
  results = shared_knowledge.query(
      query_texts=["customer health declining after deployment"],
      where={"lane": "value"},
      n_results=5
  )
  # Cross-lane query
  results = shared_knowledge.query(
      query_texts=["deployment caused scan failures"],
      where={"lane": {"$in": ["delivery", "support"]}},
      n_results=5
  )
  ```

### RAG Query Pattern (existing collections)
```python
# Example: Find similar issues for a new ticket
results = collection.query(
    query_texts=["Scan failure on subnet 10.0.1.x"],
    n_results=5,
    where={"status": "resolved"}
)
```

---

## 5. YAML Configuration Schemas

These files live at `backend/config/` and are loaded at application startup by the ProfileLoader.

### 5.1 org_structure.yaml

Defines the 4-tier hierarchy, 3 lanes, and communication rules.

```yaml
# Schema shape:
organization:
  name: string                    # "HivePro CS Control Plane"
  description: string

  hierarchy:
    tier_1:
      name: string                # "Supervisor"
      agents: [agent_id, ...]     # ["cso_orchestrator"]
      description: string
    tier_2:
      name: string                # "Lane Leads"
      agents: [agent_id, ...]     # ["support_lead", "value_lead", "delivery_lead"]
      description: string
    tier_3:
      name: string                # "Specialists"
      agents: [agent_id, ...]     # [8 specialist agent_ids]
      description: string
    tier_4:
      name: string                # "Foundation"
      agents: [agent_id, ...]     # ["customer_memory"]
      description: string

  lanes:
    support:
      lead: agent_id              # "support_lead"
      specialists: [agent_id, ...]
      focus: string
    value:
      lead: agent_id              # "value_lead"
      specialists: [agent_id, ...]
      focus: string
    delivery:
      lead: agent_id              # "delivery_lead"
      specialists: [agent_id, ...]
      focus: string

  communication_rules: [string, ...]  # Human-readable rules
```

### 5.2 agent_profiles.yaml

Defines all 13 agent profiles with personality, tools, and traits.

```yaml
# Schema shape (per agent):
<agent_id>:
  name: string                    # "Naveen Kapoor"
  codename: string                # "CS Orchestrator"
  tier: integer                   # 1-4
  lane: string | null             # "support", "value", "delivery", or null
  role: string                    # "CS Manager"
  personality: |                  # Multi-line personality description
    ...
  system_instruction: |           # Multi-line system prompt for Claude
    ...
  traits: [string, ...]           # ["strategic_oversight", "quality_evaluation", ...]
  tools: [string, ...]            # ["query_customer_db", "search_knowledge_base", ...]
  expertise: [string, ...]        # Areas of expertise
  quirks: [string, ...]           # Character-defining behaviors
  reports_to: agent_id | null     # Reporting line
  manages: [agent_id, ...]        # Direct reports (for Tier 1 and Tier 2)
```

### 5.3 pipeline.yaml

Defines tier-specific pipeline stage configurations.

```yaml
# Schema shape:
pipelines:
  <pipeline_name>:                # e.g., "tier_1_supervisor"
    description: string
    max_rounds: integer           # Safety limit on pipeline iterations
    stages:
      - name: string              # Human-readable stage label
        type: string              # perceive | retrieve | think | act | reflect | quality_gate | finalize
        description: string       # What this stage does
        max_iterations: integer   # (quality_gate only) Max rework loops
        iterate_from: string      # (quality_gate only) Stage name to loop back to
```

### 5.4 workflows.yaml

Defines how different event types route through the hierarchy.

```yaml
# Schema shape:
workflows:
  <workflow_name>:                # e.g., "ticket_workflow"
    trigger_events: [string, ...] # ["jira_ticket_created"]
    description: string
    steps:
      - agent: agent_id           # Who handles this step
        action: string            # What they do
        delegates_to: [agent_id, ...]  # Optional: who they delegate to
        condition: string         # Optional: when to execute this step
```

---

## 6. Alembic Migration Strategy

**Existing tables:** Already migrated. No changes needed.

**New tables migration:** Create a single migration file for both new tables:

```bash
# Generate migration for new tables
alembic revision --autogenerate -m "add_agent_execution_rounds_and_messages"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Migration should include:**
1. `agent_execution_rounds` table with all columns, indexes, and constraints
2. `agent_messages` table with all columns, indexes, constraints, and self-referencing FK
3. `updated_at` trigger is NOT needed for these tables (they are append-only / status-update only)

**Important:** Always include `updated_at` trigger for tables that track updates:
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Applied to: customers, tickets, users
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## 7. Seed Data Summary

The seed script (`app/utils/seed.py`) should create:

| Entity | Count | Notes |
|--------|-------|-------|
| Users | 5 | Admin, managers, engineers |
| Customers | 10 | Various industries/tiers/health levels |
| Health Scores | 300 | 30 days × 10 customers |
| Tickets | 50 | Mix of types, severities, statuses |
| Call Insights | 100 | Realistic summaries with action items |
| Agent Logs | 200 | Activity across all 13 agents |
| Events | 150 | Various event types |
| Alerts | 15 | Across at-risk customers |
| Action Items | 30 | From calls and tickets |
| Reports | 8 | 4 weekly + 2 monthly + 2 QBR |
| **Execution Rounds** | **50** | **5 sample pipeline runs × ~10 stages each, across different tiers** |
| **Agent Messages** | **40** | **Sample delegation chains: 5 complete threads showing Tier 1 → 2 → 3 → 2 → 1 flow** |
| **Episodic Memories** | **30** | **3 per specialist agent × ~10 agents — sample past execution summaries in ChromaDB** |
| **Shared Knowledge** | **15** | **5 per lane (support, value, delivery) — sample knowledge entries in ChromaDB** |

**Run:** `python -m app.utils.seed`
