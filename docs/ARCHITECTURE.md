# HivePro CS Control Plane — Product Requirements & Architecture

> This document defines what we are building, how every piece works, and the checklist to track progress.
> If it's not in this document, we're not building it.

---

## 1. Project Overview

The CS Control Plane is an AI-powered system that automates Customer Success workflows at HivePro. It uses **10 specialized AI agents** to watch incoming data from three sources — Jira tickets, Fathom call recordings, and HubSpot deals — and automatically triages issues, analyzes calls, monitors customer health, generates reports, and drafts actions for the CS team.

The system follows a **Slack-first delivery model**: agents push their outputs as interactive cards to 9 dedicated Slack channels. CS team members review, approve, or edit directly in Slack. A **3-page dashboard** provides drill-down views when deeper context is needed — accessed via deep-links in Slack cards, not by browsing.

Every agent output starts as a **draft**. Nothing customer-facing or system-modifying happens without human approval. Over time, agents that prove high accuracy (measured over 4+ weeks) earn selective autonomy for low-risk actions.

---

## 2. System Architecture

### 2.1 High-Level Flow

```
                        ┌─────────────────────────────────────────┐
                        │            DATA SOURCES                  │
                        │                                          │
                        │  Fathom ────── Jira (UCSC) ──── HubSpot │
                        │  (Calls)       (Tickets)        (Deals)  │
                        └──────────┬──────────┬──────────┬─────────┘
                                   │          │          │
                            Webhooks / Scheduled Pulls / API
                                   │          │          │
                                   ▼          ▼          ▼
                        ┌──────────────────────────────────────────┐
                        │          EVENT INGESTION LAYER            │
                        │                                          │
                        │  jira_ticket_created                     │
                        │  zoom_call_completed                     │
                        │  deal_stage_changed                      │
                        │  daily_health_check (cron 8 AM)          │
                        │  renewal_within_90_days (cron)            │
                        │  new_customer (HubSpot Closed Won)       │
                        │  deployment_ready (manual)                │
                        │  support_bundle_uploaded (manual)         │
                        │  weekly_exec_report (cron Mon 9 AM)      │
                        └──────────────────┬───────────────────────┘
                                           │
                                           ▼
                        ┌──────────────────────────────────────────┐
                        │         CS ORCHESTRATOR (Agent 1)         │
                        │                                          │
                        │   Classifies event → Routes to agent     │
                        │   Never analyzes. Coordinates only.      │
                        └───┬──────────┬──────────┬───────────┬────┘
                            │          │          │           │
               ┌────────────┘    ┌─────┘    ┌─────┘     ┌─────┘
               ▼                 ▼          ▼           ▼
     ┌─────────────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐
     │   PRE-SALES     │ │  DELIVERY  │ │ RUN /    │ │    VALUE     │
     │   LANE          │ │  LANE      │ │ SUPPORT  │ │    LANE      │
     │                 │ │            │ │ LANE     │ │              │
     │ Pre-Sales       │ │ SOW &      │ │ Ticket   │ │ Health       │
     │ Funnel          │ │ Prereq     │ │ Triage   │ │ Monitor      │
     │ (Agent 3)       │ │ (Agent 4)  │ │ (Agent 6)│ │ (Agent 9)    │
     │                 │ │            │ │          │ │              │
     │                 │ │ Deployment │ │ Trouble- │ │ QBR / Value  │
     │                 │ │ Intel      │ │ shoot    │ │ Narrative    │
     │                 │ │ (Agent 5)  │ │ (Agent 7)│ │ (Agent 10)   │
     │                 │ │            │ │          │ │              │
     │                 │ │            │ │ Escala-  │ │              │
     │                 │ │            │ │ tion     │ │              │
     │                 │ │            │ │ (Agent 8)│ │              │
     └─────────────────┘ └────────────┘ └──────────┘ └──────────────┘
                            │          │          │           │
                            └──────────┴──────────┴───────────┘
                                           │
                                           ▼
                        ┌──────────────────────────────────────────┐
                        │          SHARED SERVICES                  │
                        │                                          │
                        │  Customer Memory (Agent 2)               │
                        │    └─ Per-customer JSON store (CRUD)     │
                        │    └─ Every agent reads before executing │
                        │    └─ Every agent writes results back    │
                        │                                          │
                        │  Executive Reporter                      │
                        │    └─ Aggregates all agent outputs       │
                        │    └─ Weekly digest + threshold alerts   │
                        └──────────────────┬───────────────────────┘
                                           │
                                           ▼
                        ┌──────────────────────────────────────────┐
                        │           OUTPUT LAYER                    │
                        │                                          │
                        │  ┌──────────────────────────────┐        │
                        │  │  DRAFT STORAGE                │        │
                        │  │  (agent_drafts table)         │        │
                        │  │  status: pending → approved   │        │
                        │  └──────────────┬───────────────┘        │
                        │                 │                         │
                        │        ┌────────┴────────┐                │
                        │        ▼                 ▼                │
                        │   ┌─────────┐     ┌───────────┐          │
                        │   │  SLACK  │     │ DASHBOARD │          │
                        │   │  (Push) │────▶│  (Pull)   │          │
                        │   │         │deep │           │          │
                        │   │ 9 chans │link │  3 pages  │          │
                        │   │ cards   │     │  drill-   │          │
                        │   │ buttons │     │  down     │          │
                        │   └─────────┘     └───────────┘          │
                        └──────────────────────────────────────────┘
```

### 2.2 Single Event Lifecycle

```
Event arrives (webhook/cron)
    │
    ▼
Orchestrator classifies event, picks agent
    │
    ▼
Agent reads Customer Memory for context
    │
    ▼
Agent processes (classify / analyze / score / generate)
    │
    ▼
Agent writes output as DRAFT to agent_drafts table
    │
    ▼
Agent updates Customer Memory with new data
    │
    ▼
Slack bot posts card to designated channel
    ├── [Approve] → Execute action (update Jira, send email, etc.)
    ├── [Edit]    → Human modifies in Slack thread → then approve
    └── [Dismiss] → Log rejection, no action taken
    │
    ▼
Audit log records: agent, action, confidence, human decision, edit diff
```

---

## 3. Core Principles

| #   | Principle                      | Meaning                                                                                                                                   |
| --- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Draft-First**                | Every agent output is a draft. Humans approve in Slack before any customer-facing action, Jira write, or email send.                      |
| 2   | **Slack-Push, Dashboard-Pull** | Slack is where notifications go. The dashboard is only opened via deep-links from Slack cards. Nobody browses the dashboard on their own. |
| 3   | **Event-Driven**               | Every workflow starts from a discrete event — a webhook, a cron job, or a manual trigger. The frontend never polls.                       |
| 4   | **Customer Isolation**         | Every database query is scoped to a `customer_id`. No cross-customer data leakage. Memory is per-customer.                                |
| 5   | **Accuracy Before Autonomy**   | Agents run in draft-only mode for 4+ weeks. Only agents that prove accuracy through measured metrics earn selective autonomy.             |
| 6   | **Simplicity**                 | 10 agents, one job each. Build what's needed, ship it, measure it. No over-engineering.                                                   |

---

## 4. Data Sources

### 4.1 Fathom (Call Recordings)

| Aspect               | Detail                                                               |
| -------------------- | -------------------------------------------------------------------- |
| **What it provides** | Call transcripts, speaker labels, summaries, action items, sentiment |
| **How we ingest**    | Webhook on call end + full API pull every 6 hours                    |
| **Used by**          | Call Intelligence (via Fathom Agent), QBR Agent, Executive Reporter  |
| **API**              | Fathom External API v1 (`https://api.fathom.ai/external/v1`)         |

**Checklist:**

- [x] Fathom API client (list meetings, get transcript, get summary)
- [x] Webhook receiver (`POST /api/webhooks/fathom`)
- [x] Background sync (full 14-day on startup, incremental every 6 hours)
- [x] Transcript storage in database
- [x] Meeting knowledge indexed in ChromaDB for RAG search
- [x] Validate: agent output quality vs Fathom's built-in "Ask Fathom" feature

### 4.2 Jira (UCSC Tickets)

| Aspect               | Detail                                                       |
| -------------------- | ------------------------------------------------------------ |
| **What it provides** | Tickets: priority, status, SLA, labels, comments, resolution |
| **How we ingest**    | Webhook on ticket create/update + polling every 15 minutes   |
| **Used by**          | Ticket Triage, Troubleshooting, Escalation, Health Monitor   |
| **Project**          | UCSC only (filtered by project key)                          |

**Checklist:**

- [x] Jira API client (search, get issue, update labels, add comment)
- [x] Webhook receiver (`POST /api/webhooks/jira`)
- [x] Bulk sync (full + incremental)
- [x] Ticket normalizer (Jira fields → internal schema)
- [x] Customer-to-project mapping (which Jira project belongs to which customer)

### 4.3 HubSpot (Deals Pipeline)

| Aspect               | Detail                                                            |
| -------------------- | ----------------------------------------------------------------- |
| **What it provides** | Deals pipeline, stages, contacts, close reasons, demo/POC dates   |
| **How we ingest**    | Daily API pull (Sunday 11 PM full sync) + webhook on stage change |
| **Used by**          | Pre-Sales Funnel, Executive Reporter, QBR Agent                   |

**Checklist:**

- [x] HubSpot API client (list deals, get deal, list contacts, get pipeline) — `hubspot_service.py`
- [x] Webhook receiver for deal stage changes — `POST /api/webhooks/hubspot`
- [x] Daily sync job — APScheduler 7:00 AM + startup sync with marker file
- [x] Deal storage in database — `deals` table (1436 deals synced), Alembic migration `h8i9j0k1l2m3`
- [x] Customer-to-deal mapping — company name containment match (138 matched to customers)

### 4.4 Customer Memory Schema

Every agent reads this before executing and writes results back after completing. This is the single source of truth per customer.

```json
{
  "customer_id": "string",
  "company_name": "string",
  "deployment_mode": "OVA | SaaS | On-Prem",
  "version": "string",
  "integrations": ["EDR", "SIEM", "Firewall"],
  "known_constraints": ["Air-gapped", "Proxy", "Restricted ports"],
  "industry": "banking | telco | gov | tech",
  "tier": "enterprise | mid-market | smb",
  "csm_owner": "string",
  "renewal_date": "YYYY-MM-DD",
  "health_score": 0-100,
  "sentiment_bucket": "happy | neutral | unhappy",
  "open_tickets": [{ "ticket_id": "", "priority": "", "status": "", "age_days": 0 }],
  "recent_calls": [{ "call_id": "", "date": "", "sentiment": "", "topics": [] }],
  "risk_flags": ["delayed_renewal", "p0_open", "negative_sentiment"],
  "feature_requests": [{ "title": "", "votes": 0, "source": "" }],
  "hubspot_deal_id": "string",
  "hubspot_deal_stage": "string"
}
```

**Checklist:**

- [x] Customer Memory CRUD API (`GET/POST/PUT /api/customers/{id}/memory`)
- [x] ~~Seed script to populate from existing customer list~~ (removed — full customer list mapping in Phase 2 Day 20)
- [x] Every agent reads memory at start of execution
- [x] Every agent writes updated fields after execution

---

## 5. Agent Specifications

### Agent 1: CS Orchestrator

|             |                                                                                                                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**    | Route every incoming event to the correct lane agent. The traffic controller.                                                                                                                  |
| **Lane**    | Control                                                                                                                                                                                        |
| **Trigger** | All events (jira_ticket_created, zoom_call_completed, deal_stage_changed, daily_health_check, support_bundle_uploaded, renewal_within_90_days, new_customer, deployment_ready, manual_trigger) |

**Input:** Raw event payload (event_type, customer_id, metadata)

**Process:**

1. Receive event from ingestion layer
2. Classify event type
3. Look up routing table to determine which agent handles this event
4. Attach context snapshot (customer_id, priority, timestamp)
5. Forward to the assigned agent

**Output:**

```json
{
  "event_id": "evt_xxx",
  "classified_type": "jira_ticket_created",
  "assigned_agent": "ticket_triage",
  "priority": "high",
  "context_snapshot": {
    "customer_id": "cust_xxx",
    "customer_name": "Acme Corp"
  }
}
```

**Rules:**

- NEVER does analysis or generates content
- NEVER writes to Customer Memory
- NEVER executes tools
- Coordinates only — pure routing

**Checklist:**

- [x] Event classifier (maps event_type to agent)
- [x] Routing table configuration
- [x] Context snapshot assembly
- [x] Error handling (unknown event types → log + alert)
- [x] Routing for all 11 event types

---

### Agent 2: Customer Memory

|             |                                                                                                          |
| ----------- | -------------------------------------------------------------------------------------------------------- |
| **Goal**    | Maintain a single source of truth per customer. Every agent reads before executing, writes results back. |
| **Lane**    | Shared Services                                                                                          |
| **Trigger** | Every agent reads/writes (not event-triggered)                                                           |

**Input:** Agent requests to read or update customer data

**Process:**

1. On READ: return full customer JSON for the given customer_id
2. On WRITE: merge updated fields into existing customer JSON
3. Maintain history of changes (who updated what, when)

**Output:** Customer JSON (see schema in Section 4.4)

**Rules:**

- NEVER modifies data without a requesting agent context
- All writes are logged with agent_id and timestamp
- Human approval required for any destructive changes (deletes, resets)

**Checklist:**

- [x] Customer Memory JSON store (PostgreSQL JSONB column)
- [x] CRUD API endpoints
- [x] Read-before-execute pattern enforced in all agents
- [x] Write-after-complete pattern enforced in all agents
- [x] Change history logging
- [x] ~~Seed script with initial customer data~~ (removed — full customer list mapping in Phase 2 Day 20)

---

### Agent 3: Pre-Sales Funnel

|             |                                                                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**    | Analyze the HubSpot deals pipeline to surface conversion rates, stalled deals, and blockers. Give sales leadership visibility into the funnel. |
| **Lane**    | Pre-Sales                                                                                                                                      |
| **Trigger** | `deal_stage_changed` (HubSpot webhook), weekly scheduled pull (Sunday 11 PM)                                                                   |

**Input:**

- HubSpot pipeline data (deal stages, dates, values, close reasons)
- Fathom demo/POC call transcripts (themes, objections, sentiment)

**Process:**

1. Pull current pipeline from HubSpot
2. Calculate conversion rates: LeadGen → Demo → POC → Close *(answers Q3: POC→Close, Q4: Demo→POC)*
3. Identify stalled deals (stuck >30 days in any stage)
4. Analyze Closed Lost reasons from HubSpot `close_reason` field
5. Cross-reference with Fathom demo/POC call themes for blocker patterns
6. Classify deal objections from Fathom call transcripts using objection taxonomy: wrong fit, competitor overlap, feature gap, pricing, UX friction, timing, internal politics, POC execution *(answers Q5, Q6)*
7. Rank blockers by frequency and deal value
8. Calculate deal win probability by cross-referencing: HubSpot deal stage + historical win rates, Fathom call sentiment, deal age/velocity vs benchmarks, blocker patterns from similar stalled deals *(answers Q11)*

**Output:**

```json
{
  "funnel_metrics": {
    "leadgen_to_demo": 0.65,
    "demo_to_poc": 0.4,
    "poc_to_close": 0.55
  },
  "stalled_deals": [
    { "deal_name": "", "stage": "", "days_stalled": 0, "owner": "" }
  ],
  "top_blockers": [{ "reason": "", "frequency": 0, "total_deal_value": 0 }],
  "objection_analysis": [
    { "type": "wrong_fit | competitor | feature_gap | pricing | ux_friction | timing | politics | poc_execution", "frequency": 0, "example_deals": [] }
  ],
  "deal_win_probability": {
    "deal_name": "", "probability": 0.0, "factors": ["stage: POC (historical win rate 55%)", "sentiment: positive (3 calls)", "velocity: on track"]
  },
  "week_over_week_change": { "conversion_delta": 0.0 }
}
```

**Slack:** Posts to **#cs-presales-funnel** with link to Pipeline Analytics dashboard page

**Rules:**

- NEVER modifies HubSpot data
- NEVER contacts prospects or customers
- Read-only analysis

**Checklist:**

- [ ] HubSpot pipeline data fetcher
- [ ] Conversion rate calculator
- [ ] Stalled deal detector (>30 days same stage)
- [ ] Blocker analysis (HubSpot close_reason + Fathom call NLP)
- [ ] Weekly scheduled trigger
- [ ] Slack card to #cs-presales-funnel
- [ ] Dashboard deep-link to Pipeline Analytics page
- [ ] Objection taxonomy classifier (8 categories from Fathom calls) — Gap 1, Q5/Q6
- [ ] Deal win probability calculator (stage + sentiment + velocity + blockers) — Gap 4, Q11

---

### Agent 4: SOW & Prerequisite

|             |                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------- |
| **Goal**    | Generate SOW documents, infrastructure checklists, and onboarding timelines for new customers. |
| **Lane**    | Delivery                                                                                       |
| **Trigger** | `new_customer` event (HubSpot Closed Won)                                                      |

**Input:**

- Customer Memory (deployment mode, integrations, constraints)
- Standard SOW templates

**Process:**

1. Read Customer Memory for deployment context
2. Generate SOW document draft (scope, deliverables, timeline)
3. Generate infrastructure checklist (CPU, RAM, disk, ports, DNS, NTP)
4. Generate security checklist (firewall rules, proxy config, certificate requirements)
5. Generate responsibility matrix (HivePro vs customer tasks)
6. Set estimated timeline based on deployment complexity

**Output:**

```json
{
  "sow_document": "markdown_content",
  "infra_checklist": [{ "item": "", "status": "pending", "owner": "" }],
  "security_checklist": [{ "item": "", "status": "pending" }],
  "responsibility_matrix": [
    { "task": "", "owner": "hivepro | customer", "deadline": "" }
  ],
  "estimated_timeline_days": 14
}
```

**Slack:** Posts to **#cs-delivery** with link to Customer Profile → Overview tab

**Rules:**

- Output is always a DRAFT — CSM reviews before sharing with customer
- NEVER sends documents to customers directly

**Checklist:**

- [ ] SOW template engine
- [ ] Infrastructure checklist generator (based on deployment_mode)
- [ ] Security checklist generator
- [ ] Responsibility matrix builder
- [ ] Timeline estimator
- [ ] Slack card to #cs-delivery
- [ ] Dashboard deep-link to Customer Profile → Overview tab

---

### Agent 5: Deployment Intelligence

|             |                                                                                                              |
| ----------- | ------------------------------------------------------------------------------------------------------------ |
| **Goal**    | Validate new deployments by checking system health, connector status, and scan results. Flag failures early. |
| **Lane**    | Delivery                                                                                                     |
| **Trigger** | `deployment_ready` (manual trigger during onboarding)                                                        |

**Input:**

- SOW requirements and prerequisites — from Customer Memory
- Jira deployment tickets (status, blockers) — from Jira
- Customer onboarding call notes — from Fathom
- Customer profile (tier, deployment mode) — from Customer DB

**Process:**

1. Review SOW requirements against current deployment status
2. Check deployment-related Jira tickets for blockers or failures
3. Review onboarding call notes for flagged issues
4. Validate prerequisites are met per SOW checklist
5. If any check fails → route to Troubleshooting Agent

**Output:**

```json
{
  "validation_status": "pass | fail",
  "checks": [
    { "name": "sow_requirements_met", "status": "pass | fail", "detail": "" },
    { "name": "deployment_tickets_clear", "status": "pass | fail", "detail": "" },
    { "name": "prerequisites_validated", "status": "pass | fail", "detail": "" }
  ],
  "failure_routing": "troubleshooting_agent | none"
}
```

**Slack:** Posts to **#cs-delivery** with link to Customer Profile → Overview tab

**Rules:**

- NEVER modifies customer environment
- On failure → auto-routes to Troubleshooting Agent

**Checklist:**

- [ ] Health snapshot reader
- [ ] Service status validator
- [ ] Connector heartbeat checker
- [ ] Scan result validator
- [ ] RBAC/SSO config checker
- [ ] Failure → Troubleshooting routing
- [ ] Slack card to #cs-delivery
- [ ] Dashboard deep-link to Customer Profile → Overview tab

---

### Agent 6: Ticket Triage

|             |                                                                                                                                          |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**    | Classify every incoming Jira UCSC ticket — assign category, severity, suggest diagnostics, check duplicates, and draft a customer email. |
| **Lane**    | Run / Support                                                                                                                            |
| **Trigger** | `jira_ticket_created` (UCSC project only)                                                                                                |

**Input:**

- Jira ticket (summary, description, priority, reporter, labels)
- Customer Memory (deployment mode, version, integrations, known constraints, open tickets)
- Similar past tickets (from RAG search)

**Process:**

1. Read Customer Memory for customer context
2. Classify ticket category: Deployment / Scan / Connector / Performance / UI / Integration
3. Assign severity: P0 (critical) / P1 (high) / P2 (medium) / P3 (low)
4. Suggest diagnostic script or KB article
5. Search for similar past tickets (RAG vector search)
6. Draft customer acknowledgment email

**Output:**

```json
{
  "classification": {
    "label": "connector_failure",
    "severity": "P1",
    "root_cause_category": "Connector",
    "confidence": 0.87
  },
  "diagnostics": {
    "required_script": "check_connector_health.sh",
    "kb_article": "KB-1234"
  },
  "similar_tickets": ["UCSC-890", "UCSC-756"],
  "email_draft": "Dear [Customer],\n\nThank you for reporting..."
}
```

**Slack:** Posts to **#cs-ticket-triage** with Approve/Edit/Dismiss buttons + link to Customer Profile → Tickets tab

**Rules:**

- NEVER auto-responds to customer
- NEVER auto-labels Jira ticket without human approval
- NEVER auto-assigns ticket

**Checklist:**

- [x] Ticket classifier (6 categories)
- [x] Severity assigner (P0-P3)
- [x] Diagnostic suggester
- [x] Duplicate / similar ticket search (RAG)
- [x] Customer email drafter
- [x] Customer Memory read before processing
- [x] Customer Memory update after processing
- [x] Slack card to #cs-ticket-triage with approval buttons
- [x] On Approve: update Jira labels + send email
- [x] Dashboard deep-link to Customer Profile → Tickets tab

---

### Agent 7: Troubleshooting

|             |                                                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Goal**    | Analyze support bundles and system diagnostics to find root cause with a confidence score. If confidence is low, auto-route to Escalation. |
| **Lane**    | Run / Support                                                                                                                              |
| **Trigger** | `support_bundle_uploaded` event                                                                                                            |

**Input:**

- hp_health_snapshot
- services_status
- scan_job_status
- connectors_status
- network_probe results
- Customer Memory (deployment mode, version, known constraints)

**Process:**

1. Read Customer Memory for environment context
2. Parse support bundle data
3. Analyze health snapshot, service status, connectors, scans
4. Identify probable root cause
5. Score confidence (0-100)
6. If confidence < 70% → flag for escalation
7. Suggest next step

**Output:**

```json
{
  "probable_root_cause": "Connector timeout due to proxy misconfiguration",
  "confidence_score": 82,
  "evidence": [
    "service_x timeout at 14:23",
    "proxy_config missing bypass rule"
  ],
  "next_step": "Add proxy bypass for connector endpoint",
  "escalation_flag": false
}
```

**Slack:** Posts to **#cs-ticket-triage** with link to Customer Profile → Tickets tab

**Rules:**

- If confidence < 70% → auto-routes to Escalation Agent
- NEVER modifies customer environment
- NEVER applies fixes directly

**Checklist:**

- [x] Support bundle parser
- [x] Health snapshot analyzer
- [x] Service status analyzer
- [x] Connector status analyzer
- [x] Root cause identification engine
- [x] Confidence scoring (0-100)
- [x] Auto-route to Escalation if confidence < 70%
- [x] Slack card to #cs-ticket-triage
- [x] Dashboard deep-link to Customer Profile → Tickets tab

---

### Agent 8: Escalation Writer

|             |                                                                                                                                   |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**    | Compile a complete escalation document for engineering with all context, evidence, reproduction steps, and customer update draft. |
| **Lane**    | Run / Support                                                                                                                     |
| **Trigger** | `escalation_needed` (from Troubleshooting confidence < 70%), severity = High, or RCA needed                                       |

**Input:**

- Troubleshooting Agent output (root cause analysis, evidence)
- Customer Memory (full customer context)
- Jira ticket history
- Related call transcripts (if any)

**Process:**

1. Read Customer Memory for full customer context
2. Compile customer context section (tier, deployment, version, integrations)
3. Write technical summary of the issue
4. Attach evidence (logs, screenshots, diagnostic output)
5. Write reproduction steps
6. Create timeline of events
7. Draft customer update message

**Output:**

```json
{
  "escalation_document": {
    "customer_context": "Enterprise, OVA deployment, v4.2...",
    "technical_summary": "Connector failure after proxy change...",
    "evidence": ["log_excerpt_1", "screenshot_url"],
    "reproduction_steps": ["1. Configure proxy...", "2. Trigger scan..."],
    "timeline": [{ "timestamp": "", "event": "" }],
    "customer_update_draft": "Dear [Customer],\n\nOur engineering team is..."
  }
}
```

**Slack:** Posts to **#cs-escalations** with Approve button + link to Customer Profile → Tickets tab

**Rules:**

- ALWAYS requires human approval — escalations are NEVER auto-sent
- NEVER contacts engineering directly without CS Manager approval

**Checklist:**

- [x] Customer context compiler
- [x] Technical summary generator
- [x] Evidence collector and formatter
- [x] Reproduction steps writer
- [x] Timeline builder
- [x] Customer update draft generator
- [x] Slack card to #cs-escalations with Approve button
- [x] On Approve: attach doc to Jira ticket + notify engineering
- [x] Dashboard deep-link to Customer Profile → Tickets tab

---

### Agent 9: Health Monitor

|             |                                                                                                                                               |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**    | Run daily health checks on every customer — compute health scores, detect risk flags, and draft proactive Jira tickets for at-risk customers. |
| **Lane**    | Value                                                                                                                                         |
| **Trigger** | `daily_health_check` (scheduled cron, 8 AM daily)                                                                                             |

**Input:**

- Open P0/P1 tickets (age in days, severity, SLA status) — from Jira
- Recent call sentiment and trends — from Fathom
- Renewal dates and customer tier — from Customer DB
- Historical health scores and trends — from health_scores table
- Open alerts count and severity — from alerts table
- Customer Memory (current health_score, risk_flags)

**Process:**

1. For each customer:
   - Check ticket severity load (open P0/P1 >5 days = flag)
   - Check call sentiment trend (2+ negative in 14 days = flag)
   - Check renewal proximity (<90 days + existing risk flags = elevated risk)
   - Check historical health trend (drop >15 points in 7 days = flag)
   - Check open alert load (high severity unresolved alerts = flag)
2. Compute health score (0-100) from weighted checks *(directly answers Q2: which customer has highest attrition risk)*
3. Identify risk flags
4. Cross-customer pattern check: 5+ customers with same issue in 7 days → executive urgent alert
5. Draft proactive Jira tickets for at-risk customers (human approval required)
6. Update Customer Memory with new health_score and risk_flags

**Output:**

```json
{
  "customer_scores": [
    {
      "customer_id": "cust_xxx",
      "health_score": 42,
      "risk_flags": ["p0_open_7_days", "negative_sentiment_trend"],
      "draft_jira_ticket": {
        "summary": "Proactive: P0 ticket open >7 days — review needed",
        "priority": "P2"
      }
    }
  ],
  "threshold_alerts": [
    {
      "type": "issue_cluster",
      "issue": "p0_tickets_aging",
      "affected_count": 7
    }
  ]
}
```

**Slack:**

- Daily summary → **#cs-health-alerts** with link to At-Risk Dashboard
- Threshold breaches → **#cs-executive-urgent**
- Draft Jira tickets require human approval in Slack

**Rules:**

- NEVER auto-creates Jira tickets — drafts only
- Health alerts are informational — auto-posted from Day 1

**Checklist:**

- [x] Ticket severity load checker (open P0/P1 age)
- [x] Call sentiment trend checker (Fathom)
- [x] Renewal proximity checker
- [x] Historical health trend checker (score drop detection)
- [x] Open alert load checker
- [x] Health score calculator (weighted formula)
- [x] Risk flag detector
- [x] Cross-customer pattern detection (5+ same issue = urgent)
- [x] Proactive Jira ticket drafter
- [x] Customer Memory update (health_score, risk_flags)
- [x] Daily cron trigger (8 AM)
- [x] Slack card to #cs-health-alerts
- [x] Threshold alerts to #cs-executive-urgent
- [x] Dashboard deep-link to At-Risk Dashboard

---

### Agent 10: QBR / Value Narrative

|             |                                                                                                                                                                                                 |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**    | Generate Quarterly Business Review documents — bucket customers by sentiment (Happy/Neutral/Unhappy) with evidence, diagnose root causes of dissatisfaction, and write renewal recommendations. |
| **Lane**    | Value                                                                                                                                                                                           |
| **Trigger** | Manual request, quarterly schedule, `renewal_within_90_days`                                                                                                                                    |

**Input:**

- Customer Memory (full profile)
- Jira UCSC tickets (last 90 days)
- Fathom call sentiment (last 90 days)
- HubSpot deal data

**Process:**

1. Read Customer Memory for current state
2. Pull last 90 days of Jira tickets — categorize, count, resolution times
3. Pull last 90 days of Fathom calls — aggregate sentiment, extract key themes
4. Pull HubSpot deal data — stage, pipeline position
5. Bucket customer into sentiment: Happy (>70 health + positive calls), Neutral (50-70), Unhappy (<50 or negative sentiment + open P0/P1)
6. For Unhappy customers: cross-reference Jira categories with call themes to find root cause
7. For Unhappy customers: classify responsibility — product defect / customer environment / feature gap / training gap / integration issue. Cross-reference Troubleshooting Agent root cause data where available. *(Answers Q9)*
8. Generate prescriptive recovery plan: match root causes to remediation playbook, produce sequenced action list with owners, timelines, and success criteria. *(Answers Q10)*
9. Write value narrative: risk reduction achieved, issues resolved, platform utilization
10. Write renewal recommendation

**Output:**

```json
{
  "sentiment_bucket": "unhappy",
  "evidence": {
    "health_score": 38,
    "negative_calls": 3,
    "open_p0": 1,
    "key_complaint_themes": ["connector reliability", "scan performance"]
  },
  "root_cause_analysis": "Persistent connector failures (7 tickets in 90 days) driving negative sentiment",
  "responsibility_attribution": {
    "primary_cause": "product_defect | customer_env | feature_gap | training_gap | integration_issue",
    "evidence": "7 connector timeout tickets — all traced to product-side timeout handling, not customer config"
  },
  "recovery_plan": [
    { "action": "Deploy hotfix v4.2.1 for connector timeout", "owner": "hivepro", "timeline": "3 days", "success_criteria": "Zero connector timeouts for 7 days" },
    { "action": "Schedule technical deep-dive with customer infra team", "owner": "hivepro", "timeline": "this week", "success_criteria": "Joint action plan documented" },
    { "action": "Executive check-in call", "owner": "hivepro", "timeline": "2 weeks", "success_criteria": "Customer confirms improvement" }
  ],
  "value_narrative": "Risk exposure reduced 23% through...",
  "renewal_recommendation": "At-risk. Schedule executive call before renewal.",
  "qbr_document": "markdown_content"
}
```

**Slack:** Posts QBR draft to **#cs-qbr-drafts** with link to Customer Profile → QBR tab

**Rules:**

- QBR documents are ALWAYS reviewed by CSM before sharing — NEVER auto-sent
- Sentiment bucketing must include evidence (not just a label)

**Checklist:**

- [x] 90-day Jira ticket aggregator
- [x] 90-day Fathom sentiment aggregator
- [x] HubSpot deal data reader
- [x] Sentiment bucketing engine (Happy/Neutral/Unhappy with thresholds)
- [x] Root cause analyzer (Jira categories × Fathom call themes)
- [x] Value narrative generator
- [x] Renewal recommendation writer
- [x] QBR document generator (markdown)
- [x] Customer Memory update (sentiment_bucket)
- [x] Slack card to #cs-qbr-drafts
- [x] Dashboard deep-link to Customer Profile → QBR tab
- [ ] Responsibility attribution classifier (5 categories) — Gap 2, Q9
- [ ] Prescriptive remediation engine (playbook lookup + recovery plan generator) — Gap 3, Q10

---

## 6. Slack Architecture

### 6.1 Channel Map

| Channel                   | What Gets Posted                                                                          | Who Sees It                   | Dashboard Link                  |
| ------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------- |
| **#cs-executive-digest**  | Weekly executive summary (Monday 9 AM)                                                    | Sarfaraz, Jeelan, Brian       | At-Risk Dashboard               |
| **#cs-executive-urgent**  | Threshold alerts (5+ same issue, health crash, SLA cascade, churn signal, pipeline stall) | Sarfaraz, Jeelan, Brian       | At-Risk Dashboard (filtered)    |
| **#cs-call-intelligence** | Post-call summaries + action items + sentiment                                            | All CS Managers               | Customer Profile → Calls tab    |
| **#cs-ticket-triage**     | New ticket classifications + suggested actions                                            | CS Engineers, Support Lead    | Customer Profile → Tickets tab  |
| **#cs-health-alerts**     | Daily health check results + risk flags                                                   | CS Managers, Directors        | At-Risk Dashboard               |
| **#cs-presales-funnel**   | Pipeline analytics + stalled deal alerts                                                  | Sales Leadership              | Pipeline Analytics page         |
| **#cs-qbr-drafts**        | QBR document drafts for review                                                            | CS Managers                   | Customer Profile → QBR tab      |
| **#cs-escalations**       | Engineering escalation docs for approval                                                  | CS Managers, Engineering Lead | Customer Profile → Tickets tab  |
| **#cs-delivery**          | SOW drafts, deployment status                                                             | CS Managers, Onboarding Lead  | Customer Profile → Overview tab |

### 6.2 Standard Card Format

Every Slack card follows this exact format:

```
┌────────────────────────────────────────────────┐
│ [Agent Name] — [Event Type]                    │
│ Customer: [Name] | Health: [Score]             │
│ Priority: [P0/P1/P2]                           │
│────────────────────────────────────────────────│
│ Summary: [2-3 sentence insight]                │
│ Action Required: [specific next step]          │
│                                                │
│ [Approve]  [Edit]  [Dismiss]                   │
│                                                │
│ View Details → [Dashboard Deep-Link]           │
└────────────────────────────────────────────────┘
```

- **Approve** → Execute the drafted action (update Jira, send email, etc.)
- **Edit** → Open Slack thread for human to modify the draft, then approve
- **Dismiss** → No action taken. Logged for accuracy tracking.
- **View Details** → Deep-link to the dashboard page with correct tab pre-selected

### 6.3 Slack Checklist

- [x] Slack Bolt SDK integration
- [x] 9 channels configured in environment variables
- [x] Standard card builder function (Block Kit JSON)
- [x] Approve/Edit/Dismiss interactive button handlers
- [x] Interactivity webhook endpoint (`POST /api/webhooks/slack/interactions`)
- [x] Deep-link URL builder (dashboard base URL + customer/tab params)
- [x] Action execution on Approve (Jira update, email send, etc.)
- [x] Edit flow (Slack thread → modified draft → approve)
- [x] Dismiss logging to audit log
- [x] Slack signature verification for all incoming webhooks

---

## 7. Dashboard (3 Pages)

### 7.1 Page 1: At-Risk Dashboard — `/dashboard`

The single-pane view of portfolio health. What leadership cares about most. Accessed via Slack deep-links.

**Layout:**

| Section           | Content                                                                                                                                                                                                                                          |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Top Row**       | 4 KPI cards: Total Customers, At-Risk Count, Open P0/P1 Tickets, Avg Health Score                                                                                                                                                                |
| **Main**          | At-Risk Customer Table — Columns: Customer Name, Health Score (color-coded), Sentiment Bucket, Open Tickets, Days to Renewal, Risk Flags, Last Call Date. Click row → Customer Profile. Filters: Risk level, CSM owner, Industry, Renewal window |
| **Right Sidebar** | Live Alert Feed: latest health alerts, escalations, threshold breaches                                                                                                                                                                           |
| **Bottom**        | Trend Charts: Health score distribution (12-week heatmap), Ticket velocity (opened vs resolved/week), Sentiment trend (portfolio-wide over time)                                                                                                 |

**Checklist:**

- [x] KPI cards component (4 metrics from API)
- [x] At-Risk Customer Table (sortable, filterable)
- [x] Color-coded health score column
- [x] Row click → navigate to Customer Profile
- [x] Filter controls (risk level, CSM, industry, renewal window)
- [ ] Live Alert Feed sidebar
- [ ] Health score heatmap chart (12 weeks)
- [ ] Ticket velocity chart (opened vs resolved)
- [ ] Sentiment trend chart (positive/neutral/negative over time)
- [x] URL query param support for pre-filtering from Slack deep-links

### 7.2 Page 2: Customer Profile — `/dashboard/customer/{customer_id}`

Everything about one customer in one place. CSMs land here from Slack deep-links.

**Header:** Customer name, health score gauge, sentiment badge, renewal countdown, CSM owner

**Tabs:**

| Tab                | Content                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------- |
| **Overview**       | Customer Memory data: deployment mode, version, integrations, constraints, risk flags, feature requests |
| **Tickets**        | All UCSC tickets (priority, status, SLA countdown, triage summary). Click ticket → detail view          |
| **Calls**          | All Fathom calls (date, duration, sentiment, key topics, action items). Expandable rows                 |
| **Health History** | Health score over time (line chart), risk flag timeline, connector/scan status history                  |
| **QBR**            | Latest QBR draft, sentiment bucket history, value narrative, renewal recommendation                     |
| **HubSpot**        | Deal stage, pipeline position, POC/demo dates, associated contacts                                      |

**Checklist:**

- [x] Customer header component (health gauge, sentiment badge, renewal countdown)
- [x] Tab navigation component
- [x] Overview tab (Customer Memory display)
- [x] Tickets tab (table with priority, status, SLA, triage summary)
- [x] Calls tab (expandable call list with sentiment, topics, actions)
- [x] Health History tab (line chart + risk flag timeline)
- [ ] QBR tab (document viewer + sentiment history)
- [ ] HubSpot tab (deal info + contacts)
- [x] URL query param for tab pre-selection (`?tab=tickets`)
- [x] API endpoints for each tab's data

### 7.3 Page 3: Pipeline Analytics — `/dashboard/pipeline`

Pre-sales funnel visibility for sales leadership.

| Section           | Content                                                                 |
| ----------------- | ----------------------------------------------------------------------- |
| **Funnel**        | Deal count and value at each stage (LeadGen → Demo → POC → Close)       |
| **Conversion**    | Stage-to-stage percentages with week-over-week change                   |
| **Stalled Deals** | Deals stuck >30 days (name, owner, days stalled, last activity)         |
| **Blockers**      | Top reasons for Closed Lost (HubSpot close_reason + Fathom call themes) |
| **Time-in-Stage** | Average days per stage, trend over 12 weeks                             |

**Checklist:**

- [ ] Funnel visualization component
- [ ] Conversion rate display with week-over-week delta
- [ ] Stalled deals table (filterable)
- [ ] Blocker analysis section
- [ ] Time-in-stage chart (12-week trend)
- [ ] API endpoints for pipeline data

---

## 8. Approval Workflow & Autonomy Gates

### 8.1 Draft-First Flow

```
Agent produces output
    │
    ▼
Output saved as DRAFT in agent_drafts table
    │
    ▼
Slack card posted to designated channel
    │
    ├── Human clicks [Approve]
    │       └── System executes the action
    │           (update Jira labels, send email, create ticket, attach doc)
    │
    ├── Human clicks [Edit]
    │       └── Opens Slack thread
    │       └── Human modifies the draft
    │       └── Human approves modified version
    │       └── System executes modified action
    │
    └── Human clicks [Dismiss]
            └── No action taken
            └── Logged as rejection in audit log

Every interaction → audit_log (agent, action, confidence, human_decision, edit_diff)
```

### 8.2 Actions That Are NEVER Automated

| Action                    | Rule                                  |
| ------------------------- | ------------------------------------- |
| Escalation to engineering | ALWAYS requires CS Manager approval   |
| QBR documents             | ALWAYS reviewed by CSM before sharing |
| SOW documents             | ALWAYS reviewed by CSM before sharing |
| Modify customer data      | ALWAYS requires human approval        |
| Delete anything           | ALWAYS requires human approval        |

### 8.3 Actions That Can Earn Autonomy

| Action                    | Autonomy Threshold                                | Until Threshold Met    |
| ------------------------- | ------------------------------------------------- | ---------------------- |
| Health alerts to Slack    | Auto from Day 1 (informational)                   | —                      |
| Executive digest to Slack | Auto from Day 1 (informational)                   | —                      |
| Update Jira labels        | Triage accuracy > 95% for 3+ consecutive weeks    | Draft + Slack approval |
| Create Jira ticket        | Triage accuracy > 90% for 3+ consecutive weeks    | Draft + Slack approval |
| Send email to customer    | Fathom validation > 0.90 for 4+ consecutive weeks | Draft + Slack approval |

### 8.4 Accuracy Metrics

| Metric                  | Formula                                          | Target |
| ----------------------- | ------------------------------------------------ | ------ |
| **Triage accuracy**     | Approved without edits / Total triage outputs    | > 90%  |
| **False positive rate** | Health alerts dismissed / Total health alerts    | < 20%  |
| **Human override rate** | (Edited + Dismissed) / Total outputs             | < 15%  |
| **Fathom validation**   | Agent output compared to Fathom AI for same call | > 0.80 |

### 8.5 Approval Workflow Checklist

- [x] `agent_drafts` table (id, agent_id, event_id, customer_id, draft_type, draft_content JSON, status, slack_message_ts, slack_channel, approved_by, approved_at, edit_diff)
- [x] `audit_log` table (log_id, timestamp, agent, event_id, customer_id, action, input_summary, output_summary, confidence, human_action, human_edit_diff, dashboard_url)
- [x] Draft creation in every agent's output path
- [x] Slack interactive button handler (approve/edit/dismiss)
- [x] Action execution engine (on approve → do the thing)
- [x] Edit flow (Slack thread modification → re-approve)
- [ ] Accuracy metric calculator (weekly computation)
- [ ] Autonomy gate checker (before each action, check if agent qualifies)

---

## 9. Executive Reporting

### 9.1 Weekly Executive Summary (Monday 9 AM → #cs-executive-digest)

| Section            | Content                                                                      | Dashboard Link               |
| ------------------ | ---------------------------------------------------------------------------- | ---------------------------- |
| Portfolio Health   | Health distribution (healthy/at-risk/critical), week-over-week delta         | At-Risk Dashboard            |
| Pre-Sales Pipeline | Funnel metrics, conversion rates, stalled deals, top blockers                | Pipeline Analytics           |
| Support Velocity   | Tickets opened/resolved, avg resolution, SLA breaches, top categories        | At-Risk Dashboard            |
| Sentiment Trends   | Who moved happy→unhappy and why (linked to calls/tickets)                    | Customer Profile → Calls     |
| Risk Alerts        | Customers needing immediate attention, pending escalations                   | At-Risk Dashboard (filtered) |
| Feature Demand     | Top features ranked by customer count + ARR impact                           | At-Risk Dashboard            |
| Agent Accuracy     | Triage accuracy, false positive rate, human override rate, Fathom validation | Internal metric              |

### 9.2 Threshold Alerts (Real-Time → #cs-executive-urgent)

These fire immediately. Do NOT wait for the weekly digest.

| Alert              | Condition                                             |
| ------------------ | ----------------------------------------------------- |
| **Issue Cluster**  | 5+ customers report same issue category in 7 days     |
| **Health Crash**   | Enterprise customer health drops >20 points in a week |
| **SLA Cascade**    | 3+ P0/P1 tickets breach SLA in same week              |
| **Churn Signal**   | Renewal <60 days + unhappy sentiment + open P0        |
| **Pipeline Stall** | 5+ deals stuck in same stage >30 days                 |

### 9.3 Executive Reporting Checklist

- [ ] Weekly digest aggregator (pulls from all agent outputs)
- [x] Portfolio health calculator
- [x] Support velocity metrics
- [x] Sentiment trend tracker
- [ ] Feature demand ranker
- [ ] Agent accuracy reporter
- [ ] Monday 9 AM cron trigger
- [ ] Slack message to #cs-executive-digest
- [x] Issue cluster detector (5+ same issue in 7 days)
- [x] Health crash detector (>20 point drop)
- [x] SLA cascade detector (3+ P0/P1 SLA breaches)
- [x] Churn signal detector (renewal + sentiment + P0)
- [ ] Pipeline stall detector (5+ deals stuck >30 days)
- [x] Real-time alert to #cs-executive-urgent

---

## 10. Event Routing Map

| Event                     | Source              | Agent                     | Slack Channel         | Dashboard Deep-Link                     |
| ------------------------- | ------------------- | ------------------------- | --------------------- | --------------------------------------- |
| `jira_ticket_created`     | Jira UCSC webhook   | Ticket Triage             | #cs-ticket-triage     | `/dashboard/customer/{id}?tab=tickets`  |
| `jira_ticket_updated`     | Jira UCSC webhook   | Triage / Troubleshoot     | #cs-ticket-triage     | `/dashboard/customer/{id}?tab=tickets`  |
| `support_bundle_uploaded` | Manual / Jira       | Troubleshooting           | #cs-ticket-triage     | `/dashboard/customer/{id}?tab=tickets`  |
| `zoom_call_completed`     | Fathom webhook      | Fathom Agent (Call Intel) | #cs-call-intelligence | `/dashboard/customer/{id}?tab=calls`    |
| `deal_stage_changed`      | HubSpot webhook     | Pre-Sales Funnel          | #cs-presales-funnel   | `/dashboard/pipeline`                   |
| `daily_health_check`      | Cron (8 AM)         | Health Monitor            | #cs-health-alerts     | `/dashboard`                            |
| `renewal_within_90_days`  | Cron scan           | QBR + Health              | #cs-qbr-drafts        | `/dashboard/customer/{id}?tab=qbr`      |
| `new_customer`            | HubSpot Closed Won  | SOW & Prerequisite        | #cs-delivery          | `/dashboard/customer/{id}?tab=overview` |
| `deployment_ready`        | Manual trigger      | Deployment Intel          | #cs-delivery          | `/dashboard/customer/{id}?tab=overview` |
| `escalation_needed`       | Troubleshoot output | Escalation Writer         | #cs-escalations       | `/dashboard/customer/{id}?tab=tickets`  |
| `weekly_exec_report`      | Cron (Mon 9 AM)     | Executive Reporter        | #cs-executive-digest  | `/dashboard`                            |

---

## 11. Implementation Phases

### Phase 1: Core Pipeline + Slack (Days 1-12) — COMPLETE

**Goal:** 3 data integrations working, 4 core agents live, Slack delivery active, 2 dashboard pages deployed.

**Gate:** Process a real Fathom call AND a real UCSC ticket end-to-end through Slack with human approval.

| Day | Deliverable                                                                                                 | Done When                                                              | Status |
| --- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------ |
| 1   | FastAPI scaffold, DB schema (customers, tickets, insights, events, audit_log, agent_drafts), Docker Compose | Backend runs, DB migrated, health endpoint returns 200                 | Done |
| 2   | Customer Memory Agent: JSON store, CRUD API, seed script                                                    | Create/read/update customer memory via API                             | Done |
| 3   | Fathom integration: webhook receiver, transcript fetcher, storage                                           | Real transcript stored from Fathom webhook                             | Done |
| 4   | Call Intelligence pipeline: transcript → summary + action items + sentiment → Customer Memory               | 1 real transcript processed, output matches expected format            | Done |
| 5   | Jira UCSC integration: webhook receiver, ticket normalizer, storage                                         | Real UCSC ticket stored from Jira webhook                              | Done |
| 6   | Ticket Triage Agent: classify, severity, diagnostics, duplicates, email draft                               | 3 real tickets triaged, output reviewed by CS Engineer                 | Done |
| 7   | CS Orchestrator: event classifier, routing for all Phase 1 events                                           | Routes `jira_ticket_created` and `zoom_call_completed` correctly       | Done |
| 8   | Slack bot: 9 channels, card posting with Approve/Edit/Dismiss, webhook handlers                             | Post card to #cs-ticket-triage, click Approve, action executes         | Done |
| 9   | Wire agents → Slack: Triage → #cs-ticket-triage, Call Intel → #cs-call-intelligence. Deep-links.            | End-to-end: Jira ticket → triage → Slack card → approve → Jira updated | Done |
| 10  | At-Risk Dashboard (Page 1): customer table, health scores, KPI cards                                        | Dashboard loads with real customer data                                | Done |
| 11  | Customer Profile (Page 2): tabs for overview, tickets, calls. Linked from Slack.                            | Click Slack deep-link → correct customer + correct tab                 | Done |
| 12  | Integration test: 5 real tickets + 3 real calls end-to-end. Gate review.                                    | Sarfaraz approves Phase 1 complete                                     | Done |

---

### Phase 2: Expand + Health + Pre-Sales (Days 13-22)

**Goal:** Health monitoring, troubleshooting, escalation, pre-sales funnel, executive reporting all live. Chat answers deal-specific queries. Full active customer list mapped.

**Gate:** Weekly executive digest generates correctly. At-Risk Dashboard shows real health scores. HubSpot pipeline visible. Chat returns deal win probability.

| Day | Deliverable                                                                           | Done When                                                       |
| --- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 13  | Troubleshooting Agent: bundle parser, diagnostic analysis, confidence scoring         | 1 real bundle parsed, root cause matches engineer assessment    |
| 14  | Escalation Agent: context + evidence + repro steps. Wire to #cs-escalations.          | Escalation doc reviewed by engineering, confirmed useful        |
| 15  | ~~Health Monitor Agent: daily checks, scoring formula, risk flags~~ | ✅ Done — 5 deterministic checks, weighted scoring, Claude narrative |
| 16  | ~~Health → Slack: daily digest to #cs-health-alerts, thresholds to #cs-executive-urgent~~ | ✅ Done — 3-day schedule, Slack cards, threshold alerts |
| 17  | ~~HubSpot integration: API connector, deal sync, stage change webhook~~ | ✅ Done — `hubspot_service.py`, 1436 deals synced, webhook live, daily 7 AM cron |
| 18  | ~~Pre-Sales Funnel Agent: conversion rates, blocker analysis, stalled deals + deal win probability (Q3/Q4/Q11)~~ | ✅ Done — `presales_funnel_agent.py` (Jordan Reeves), multi-factor probability model (5 weighted signals: stage + engagement + intent + sentiment + velocity). Marriott test: 64% vs old 10%. Loss analysis cross-references closedlost deals with call recordings. |
| 19  | ~~Deal intent in chat fast path (Gap 4, Q11) + multi-source cross-reference~~ | ✅ Done — `DEAL_KEYWORDS`, `_build_deal_prompt`, universal cross-reference (deals + calls + meetings for ALL intents), portfolio-wide data aggregation (Jira tickets + call topics + pipeline stats). Chat answers Q1, Q2, Q3, Q5, Q6, Q11 with real data from multiple sources. |
| 20  | Executive Reporter: weekly digest from all agents. Wire to #cs-executive-digest. **+ Full active customer list mapping** | First weekly digest generated. All active customers mapped in Customer Memory. |
| 21  | Fathom validation: compare agent output to Fathom AI. Track in audit log.             | Validation scores for last 10 calls, score > 0.80               |
| 22  | Integration test: 1 full week of real data. Gate review.                              | Sarfaraz approves Phase 2 complete                              |

#### Multi-Source Cross-Reference Architecture (Phase 2 Day 19)

Every chat query is now enriched with data from ALL sources, not just the intent-specific one:

```
User Query
    │
    ▼
Intent Classification (health / fathom / ticket / deal / general)
    │
    ▼
Customer Memory (portfolio or single customer)
    │
    ├── Entity-Specific Cross-Reference (when entity found):
    │   ├── Related deals (deals table by company name)
    │   ├── Related call insights (call_insights by summary match)
    │   └── Meeting chunks (ChromaDB by customer name)
    │
    ├── Portfolio-Wide Prefetch (when no entity):
    │   ├── Feature requests (Jira Improvement + New Feature tickets, grouped by customer)
    │   ├── Open bugs (Jira Bug tickets, P1/P2 priority)
    │   ├── Aggregated call topics (top 15 from 50 recent calls)
    │   └── Pipeline summary (total/won/lost/open from deals)
    │
    ├── Deal-Specific (deal intent only):
    │   ├── Funnel metrics (conversion rates from deals table)
    │   ├── Stalled deals (>30 days in same stage)
    │   ├── Deal win probability (multi-factor: stage + engagement + intent + sentiment + velocity)
    │   └── Loss analysis (closedlost deals cross-referenced with call recordings)
    │
    └── Fathom-Specific (fathom intent only):
        └── ChromaDB semantic search (meeting knowledge base, 349+ meetings)
    │
    ▼
Claude Haiku (single call with all context)
    │
    ▼
Formatted Answer (Slack / Dashboard)
```

**Key design decisions:**
- Cross-reference is additive — never removes existing data from the prompt
- Entity search uses first word of company name to avoid partial match failures
- Portfolio prefetch limited to 30 tickets + 50 calls to stay under token budget
- Loss analysis queries once per request, not per deal (20 deals max)
- Meeting chunks checked for duplicates to avoid double-rendering

---

### Phase 3: QBR + SOW + Autonomy (Days 23-30)

**Goal:** QBR generation with responsibility attribution and prescriptive recovery plans. SOW automation. Selective autonomy based on measured accuracy.

**Gate:** QBR sentiment buckets match CSM intuition for 80%+ customers. Recovery plans confirmed actionable by CSMs. Auto-actions gated by accuracy metrics.

| Day | Deliverable                                                                            | Done When                                                   |
| --- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 23  | QBR Agent: sentiment bucketing, root cause analysis, value narrative **+ responsibility attribution: 5-category classifier (Gap 2, Q9)** | QBR for 3 customers, CSMs confirm sentiment buckets + attribution correct |
| 24  | QBR → Dashboard + Slack: Customer Profile QBR tab, #cs-qbr-drafts                      | QBR visible in dashboard and Slack, links work end-to-end   |
| 25  | **Prescriptive remediation engine (Gap 3, Q10):** remediation playbook (YAML/ChromaDB) + recovery plan generator in QBR Agent `prescribe` stage | Recovery plan generated for 3 unhappy customers |
| 26  | SOW & Prerequisite Agent: template SOW, checklist logic. Deployment Intelligence Agent: validation checks. **+ Verify recovery plans with CSMs (Gap 3 validation)** | SOW + deployment report quality confirmed. CSMs confirm recovery plans actionable. |
| 27  | Accuracy review: 4 weeks of data → triage accuracy, false positive rate, override rate | Accuracy report generated, qualifying agents identified     |
| 28  | Conditional autonomy: enable auto-label if triage >90%, auto-email if Fathom >0.90     | Auto-actions enabled only for qualifying agents             |
| 29  | Dashboard polish: responsive, loading states, error handling, auth                     | Works on desktop/tablet, auth restricts to CS team          |
| 30  | Final integration test. Documentation. Production deployment.                          | System live. All channels active. Dashboard deployed.       |

---

## 12. Tech Stack

| Layer        | Technology                             | Purpose                                             |
| ------------ | -------------------------------------- | --------------------------------------------------- |
| Backend      | Python 3.11+ / FastAPI                 | API server, agent orchestration                     |
| Database     | PostgreSQL                             | Structured data, customer memory, drafts, audit log |
| Vector DB    | ChromaDB                               | RAG search (similar tickets, call knowledge)        |
| AI           | Anthropic Claude Sonnet                | All agent LLM calls                                 |
| Slack        | Slack Bolt SDK (Python)                | Bot, interactive messages, webhooks                 |
| Frontend     | React 18 + Vite                        | Dashboard SPA (3 pages)                             |
| Charts       | Recharts + D3.js                       | Heatmap, funnel, trend charts                       |
| State        | Zustand                                | Client-side state management                        |
| Styling      | Tailwind CSS                           | Dashboard styling                                   |
| Infra        | Docker + Docker Compose                | Containerization                                    |
| Integrations | Fathom API, Jira REST API, HubSpot API | Data ingestion                                      |

---

## 13. Security & Audit

### 13.1 Audit Log Schema

Every agent action is logged:

```json
{
  "log_id": "uuid",
  "timestamp": "ISO-8601",
  "agent": "ticket_triage",
  "event_id": "evt_xxx",
  "customer_id": "cust_xxx",
  "action": "classify_ticket",
  "input_summary": "UCSC-1234: Connector failure after update",
  "output_summary": "Classified: connector_failure, P1, email drafted",
  "confidence": 0.87,
  "human_action": "approved | edited | dismissed",
  "human_edit_diff": "changed priority P1 → P0",
  "dashboard_url": "/dashboard/customer/cust_xxx?tab=tickets"
}
```

The `human_edit_diff` field is the training signal for accuracy measurement and prompt improvement.

### 13.2 Security Rules

- **Customer isolation:** Every query scoped to `customer_id`. No cross-customer access.
- **API keys:** Fathom, Jira, HubSpot keys stored in environment variables / secret manager. Rotate every 90 days.
- **AI privacy:** Customer data never persists beyond the Claude API execution window.
- **Slack:** Bot tokens per-workspace. Channels restricted to approved members only.
- **Dashboard:** Auth required. Only CS team members. No public URLs.
- **Executive reports:** Aggregate metrics only. No individual customer PII in cross-customer views.

### 13.3 Security Checklist

- [x] JWT authentication for dashboard API
- [x] Customer-scoped database queries (no cross-customer leaks)
- [x] Slack webhook signature verification
- [ ] Jira webhook signature verification
- [ ] Fathom webhook HMAC verification
- [x] Environment variables for all secrets (no hardcoded keys)
- [x] Dashboard auth gate (login required)
- [x] Audit log for all agent actions
- [x] Audit log for all human approvals/edits/dismissals

---

## 14. Executive Question Coverage

> Maps C-level executive questions to system capabilities. Based on stakeholder meeting — cross-referenced against this architecture.
> Full gap analysis with evidence: [EXECUTIVE_QA_COVERAGE.md](./EXECUTIVE_QA_COVERAGE.md)

### 14.1 Coverage Scorecard

| # | Executive Question | Status | Agent / Feature | Available | Gap Fix |
|---|---|---|---|---|---|
| Q1 | Most requested feature across customers | **Covered** ✅ | Portfolio-wide Jira ticket aggregation (Improvement + New Feature tickets grouped by theme across customers) + chat fast path | Phase 2 (Day 19) | Done — portfolio prefetch |
| Q2 | Highest attrition risk customer | **Covered** ✅ | Health Monitor (5 deterministic checks + risk flags) + portfolio memory + chat cross-reference with tickets/calls | Phase 2 (Day 15) | None |
| Q3 | Why didn't 9/10 POCs convert to deals? | **Covered** ✅ | Pre-Sales Funnel Agent: loss analysis cross-references closedlost deals with Fathom call recordings (risks, sentiment, decisions). Names specific companies + failure reasons. | Phase 2 (Day 18) | Done |
| Q4 | Why did 90/100 demos not convert to POC? | **Covered** ✅ | Pre-Sales Funnel Agent: `demo_to_poc` rate + loss analysis from call data | Phase 2 (Day 18) | Done |
| Q5 | Call sentiment — objection type classification | **Covered** ✅ | Cross-reference pulls sentiment + risks + decisions from all call recordings. Loss analysis identifies patterns (undefined success criteria, technical barriers, integration gaps). Effectively answers objection types from real data. | Phase 2 (Day 19) | Done via cross-reference |
| Q6 | What went wrong during the POC? | **Covered** ✅ | Loss analysis names specific companies (Triflo, Union Bank, Max Credit Union) with exact failure reasons from call recordings. Cross-reference provides multi-source answer. | Phase 2 (Day 19) | Done via cross-reference |
| Q8 | How many customers happy / moderate / unhappy? | **Covered** | QBR Agent: sentiment bucketing (Happy/Neutral/Unhappy) with evidence | Phase 3 (Day 23) | None |
| Q9 | Why are unhappy customers unhappy? (attribution) | **Partial** | QBR Agent: root cause analysis via Jira × Fathom. Missing responsibility attribution. | Phase 3 + prompt fix | Gap 2: Responsibility attribution |
| Q10 | Recommend specific actions to make them happy | **Partial** | QBR Agent: diagnostic + generic recs. Missing prescriptive, sequenced recovery plans. | Phase 3 + enhancement | Gap 3: Prescriptive remediation |
| Q11 | Chances of getting a specific deal? | **Covered** ✅ | Multi-factor probability model (5 signals: pipeline stage 25% + meeting engagement 25% + buyer intent 20% + sentiment 15% + velocity 15%). Tested: Marriott 64% (vs old stage-only 10%). Chat fast path with deal intent. | Phase 2 (Day 18-19) | Done |

> **Q7** (Was the platform smooth? Time spent?) is **out of scope** — requires a 4th data source (product analytics: Mixpanel/Amplitude/Pendo) not in the current architecture.

### 14.2 Gap Fixes

| # | Gap | Affects | Fix | Effort | Target |
|---|-----|---------|-----|--------|--------|
| 1 | **Objection Taxonomy** | Q5, Q6 | Add 8-category objection classification step to Call Intelligence pipeline prompt: wrong fit, competitor overlap, feature gap, pricing, UX friction, timing, internal politics, POC execution. Transcript data already ingested — pure prompt engineering. | Low (1 day) | Phase 2 Day 17 |
| 2 | **Responsibility Attribution** | Q9 | Add 5-category responsibility classifier to QBR Agent prompt: product defect / customer environment / feature gap / training gap / integration issue. Cross-reference Troubleshooting Agent root causes. | Low (1 day) | Phase 3 Day 23 |
| 3 | **Prescriptive Remediation** | Q10 | New `prescribe` stage in QBR Agent pipeline. Remediation playbook (YAML config or ChromaDB collection) maps root cause categories → proven action sequences with owners, timelines, success criteria. | Medium (2-3 days) | Phase 3 Day 25-26 |
| 4 | ~~**Deal Intent in Chat**~~ | Q11 | ✅ **Done.** `DEAL_KEYWORDS` in `chat_service.py`, `_build_deal_prompt` in `chat_fast_path.py`, multi-factor probability model with 5 weighted signals, universal cross-reference enriches all intents with deals + calls + meetings. | Done | Phase 2 Day 19 |

### 14.3 Executive Question Availability Timeline

```
PHASE 1 COMPLETE (Day 12):
  Q2 partial (At-Risk Dashboard with health scores — no churn signal alerts yet)

PHASE 2 COMPLETE (Day 22):
  Q1  — Feature demand via portfolio Jira ticket aggregation (grouped by theme across customers)
  Q2  — Full: health scores + risk flags + portfolio cross-reference with tickets/calls
  Q3  — POC conversion rates + loss analysis cross-referencing deals with call recordings
  Q4  — Demo conversion rates + blocker analysis
  Q5  — Call sentiment with cross-reference (risks, decisions, objection patterns from real calls)
  Q6  — POC failure analysis with specific company names + call evidence
  Q11 — Multi-factor deal probability (5 signals) via chat + Pre-Sales Funnel

PHASE 3 COMPLETE (Day 30):
  Q8  — Sentiment bucketing (Happy/Neutral/Unhappy) with evidence
  Q9* — Root cause analysis with responsibility attribution (requires Gap 2 fix)
  Q10*— Prescriptive recovery plans (requires Gap 3 fix)

  * = requires gap fix applied during that phase

NOT IN CURRENT PHASES:
  Q7 — Requires product analytics data source (Phase 4 / parallel workstream)
```

---

_30 working days. 3 phases. 10 agents. 9 Slack channels. 3 dashboard pages._
_Every agent output is a draft. Every action requires approval. Autonomy is earned, not assumed._
_10 executive questions answered. 4 gap fixes. Zero architecture changes._
