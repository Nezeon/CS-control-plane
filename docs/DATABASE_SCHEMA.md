# HivePro CS Control Plane — Database Schema

**Database:** PostgreSQL 16  
**ORM:** SQLAlchemy 2.0 + Alembic  
**Vector DB:** ChromaDB (separate, for RAG)  
**Date:** February 27, 2026

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
  ├── events
  ├── alerts
  └── reports

agent_logs ── standalone (references customer optionally)
events ── standalone (references customer optionally)
```

---

## 2. Tables

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
    "ticket_severity": 18,    // max 20 — based on open ticket severity
    "sla_compliance": 15,     // max 20 — % tickets within SLA
    "sentiment": 12,          // max 15 — avg recent call sentiment
    "engagement": 10,         // max 15 — call frequency, response times
    "deployment_health": 15,  // max 15 — scan success rate, uptime
    "resolution_rate": 12     // max 15 — % tickets resolved within target
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
    "technical_summary": "Scan failure due to network segmentation. Scanner cannot reach subnet 10.0.1.x across VLAN boundary.",
    "evidence": ["Packet capture shows ICMP unreachable", "Scanner logs show timeout after 30s"],
    "reproduction_steps": ["1. Navigate to scan config", "2. Run scan against 10.0.1.x", "3. Observe timeout at 30s"],
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

Activity logs from all 10 AI agents.

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
- `agent_name`: cs_orchestrator, customer_memory, call_intelligence, health_monitor, qbr_value, ticket_triage, troubleshooter, escalation_summary, sow_agent, deployment_intel
- `agent_type`: control, value, support, delivery
- `event_type`: task_started, task_completed, task_failed, routing, alert_generated
- `trigger_event`: jira_ticket_created, zoom_call_completed, daily_health_check, renewal_90_days, new_enterprise_customer, support_bundle_uploaded, ticket_escalated, manual_trigger
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
- `source`: jira_webhook, fathom, cron, manual, slack
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
- `source_type`: call_insight, ticket, alert, manual
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

## 3. ChromaDB Collections

ChromaDB is used for RAG (Retrieval-Augmented Generation) — semantic similarity search across customer data.

### Collection: ticket_embeddings
- **Purpose:** Find similar past tickets for triage and troubleshooting
- **Document:** Ticket summary + description + resolution (if resolved)
- **Metadata:** `{ customer_id, jira_id, ticket_type, severity, status, resolved_at }`
- **Embedding model:** Claude embeddings or all-MiniLM-L6-v2

### Collection: call_insight_embeddings
- **Purpose:** Find similar call discussions, surface patterns
- **Document:** Call summary + key topics + risks + decisions
- **Metadata:** `{ customer_id, call_date, sentiment, sentiment_score }`

### Collection: problem_embeddings
- **Purpose:** Cross-customer pattern matching for issues and resolutions
- **Document:** Problem description + root cause + resolution steps
- **Metadata:** `{ customer_id, customer_name, ticket_id, resolved_in_days, resolved_at }`

### RAG Query Pattern
```python
# Example: Find similar issues for a new ticket
results = collection.query(
    query_texts=["Scan failure on subnet 10.0.1.x"],
    n_results=5,
    where={"status": "resolved"}  # Only show resolved issues
)
```

---

## 4. Alembic Migration Strategy

**Initial migration:** Create all tables in one migration file.

**Naming convention:** `{revision_id}_{description}.py`

**Commands:**
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Important:** Always include `updated_at` trigger for tables that track updates:
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## 5. Seed Data Summary

The seed script (`app/utils/seed.py`) should create:

| Entity | Count | Notes |
|--------|-------|-------|
| Users | 5 | Admin, managers, engineers |
| Customers | 10 | Various industries/tiers/health levels |
| Health Scores | 300 | 30 days × 10 customers |
| Tickets | 50 | Mix of types, severities, statuses |
| Call Insights | 100 | Realistic summaries with action items |
| Agent Logs | 200 | Activity across all 10 agents |
| Events | 150 | Various event types |
| Alerts | 15 | Across at-risk customers |
| Action Items | 30 | From calls and tickets |
| Reports | 8 | 4 weekly + 2 monthly + 2 QBR |

**Run:** `python -m app.utils.seed`
