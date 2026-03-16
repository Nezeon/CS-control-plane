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

| # | Principle | Meaning |
|---|-----------|---------|
| 1 | **Draft-First** | Every agent output is a draft. Humans approve in Slack before any customer-facing action, Jira write, or email send. |
| 2 | **Slack-Push, Dashboard-Pull** | Slack is where notifications go. The dashboard is only opened via deep-links from Slack cards. Nobody browses the dashboard on their own. |
| 3 | **Event-Driven** | Every workflow starts from a discrete event — a webhook, a cron job, or a manual trigger. The frontend never polls. |
| 4 | **Customer Isolation** | Every database query is scoped to a `customer_id`. No cross-customer data leakage. Memory is per-customer. |
| 5 | **Accuracy Before Autonomy** | Agents run in draft-only mode for 4+ weeks. Only agents that prove accuracy through measured metrics earn selective autonomy. |
| 6 | **Simplicity** | 10 agents, one job each. Build what's needed, ship it, measure it. No over-engineering. |

---

## 4. Data Sources

### 4.1 Fathom (Call Recordings)

| Aspect | Detail |
|--------|--------|
| **What it provides** | Call transcripts, speaker labels, summaries, action items, sentiment |
| **How we ingest** | Webhook on call end + full API pull every 6 hours |
| **Used by** | Call Intelligence (via Fathom Agent), QBR Agent, Executive Reporter |
| **API** | Fathom External API v1 (`https://api.fathom.ai/external/v1`) |

**Checklist:**
- [ ] Fathom API client (list meetings, get transcript, get summary)
- [ ] Webhook receiver (`POST /api/webhooks/fathom`)
- [ ] Background sync (full 14-day on startup, incremental every 6 hours)
- [ ] Transcript storage in database
- [ ] Meeting knowledge indexed in ChromaDB for RAG search
- [ ] Validate: agent output quality vs Fathom's built-in "Ask Fathom" feature

### 4.2 Jira (UCSC Tickets)

| Aspect | Detail |
|--------|--------|
| **What it provides** | Tickets: priority, status, SLA, labels, comments, resolution |
| **How we ingest** | Webhook on ticket create/update + polling every 15 minutes |
| **Used by** | Ticket Triage, Troubleshooting, Escalation, Health Monitor |
| **Project** | UCSC only (filtered by project key) |

**Checklist:**
- [ ] Jira API client (search, get issue, update labels, add comment)
- [ ] Webhook receiver (`POST /api/webhooks/jira`)
- [ ] Bulk sync (full + incremental)
- [ ] Ticket normalizer (Jira fields → internal schema)
- [ ] Customer-to-project mapping (which Jira project belongs to which customer)

### 4.3 HubSpot (Deals Pipeline)

| Aspect | Detail |
|--------|--------|
| **What it provides** | Deals pipeline, stages, contacts, close reasons, demo/POC dates |
| **How we ingest** | Daily API pull (Sunday 11 PM full sync) + webhook on stage change |
| **Used by** | Pre-Sales Funnel, Executive Reporter, QBR Agent |

**Checklist:**
- [ ] HubSpot API client (list deals, get deal, list contacts, get pipeline)
- [ ] Webhook receiver for deal stage changes
- [ ] Daily sync job
- [ ] Deal storage in database
- [ ] Customer-to-deal mapping

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
- [ ] Customer Memory CRUD API (`GET/POST/PUT /api/customers/{id}/memory`)
- [ ] Seed script to populate from existing customer list
- [ ] Every agent reads memory at start of execution
- [ ] Every agent writes updated fields after execution

---

## 5. Agent Specifications

### Agent 1: CS Orchestrator

| | |
|---|---|
| **Goal** | Route every incoming event to the correct lane agent. The traffic controller. |
| **Lane** | Control |
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
  "context_snapshot": { "customer_id": "cust_xxx", "customer_name": "Acme Corp" }
}
```

**Rules:**
- NEVER does analysis or generates content
- NEVER writes to Customer Memory
- NEVER executes tools
- Coordinates only — pure routing

**Checklist:**
- [ ] Event classifier (maps event_type to agent)
- [ ] Routing table configuration
- [ ] Context snapshot assembly
- [ ] Error handling (unknown event types → log + alert)
- [ ] Routing for all 11 event types

---

### Agent 2: Customer Memory

| | |
|---|---|
| **Goal** | Maintain a single source of truth per customer. Every agent reads before executing, writes results back. |
| **Lane** | Shared Services |
| **Trigger** | Every agent reads/writes (not event-triggered) |

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
- [ ] Customer Memory JSON store (PostgreSQL JSONB column)
- [ ] CRUD API endpoints
- [ ] Read-before-execute pattern enforced in all agents
- [ ] Write-after-complete pattern enforced in all agents
- [ ] Change history logging
- [ ] Seed script with initial customer data

---

### Agent 3: Pre-Sales Funnel

| | |
|---|---|
| **Goal** | Analyze the HubSpot deals pipeline to surface conversion rates, stalled deals, and blockers. Give sales leadership visibility into the funnel. |
| **Lane** | Pre-Sales |
| **Trigger** | `deal_stage_changed` (HubSpot webhook), weekly scheduled pull (Sunday 11 PM) |

**Input:**
- HubSpot pipeline data (deal stages, dates, values, close reasons)
- Fathom demo/POC call transcripts (themes, objections, sentiment)

**Process:**
1. Pull current pipeline from HubSpot
2. Calculate conversion rates: LeadGen → Demo → POC → Close
3. Identify stalled deals (stuck >30 days in any stage)
4. Analyze Closed Lost reasons from HubSpot `close_reason` field
5. Cross-reference with Fathom demo/POC call themes for blocker patterns
6. Rank blockers by frequency and deal value

**Output:**
```json
{
  "funnel_metrics": {
    "leadgen_to_demo": 0.65,
    "demo_to_poc": 0.40,
    "poc_to_close": 0.55
  },
  "stalled_deals": [{ "deal_name": "", "stage": "", "days_stalled": 0, "owner": "" }],
  "top_blockers": [{ "reason": "", "frequency": 0, "total_deal_value": 0 }],
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

---

### Agent 4: SOW & Prerequisite

| | |
|---|---|
| **Goal** | Generate SOW documents, infrastructure checklists, and onboarding timelines for new customers. |
| **Lane** | Delivery |
| **Trigger** | `new_customer` event (HubSpot Closed Won) |

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
  "responsibility_matrix": [{ "task": "", "owner": "hivepro | customer", "deadline": "" }],
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

| | |
|---|---|
| **Goal** | Validate new deployments by checking system health, connector status, and scan results. Flag failures early. |
| **Lane** | Delivery |
| **Trigger** | `deployment_ready` (manual trigger during onboarding) |

**Input:**
- hp_health_snapshot (system health data)
- services_status (running services)
- connector_status (integration connectors)
- First scan results
- RBAC/SSO configuration

**Process:**
1. Pull health snapshot from customer environment
2. Validate all services are running
3. Check connector heartbeats
4. Verify first scan completed successfully
5. Validate RBAC/SSO configuration
6. If any check fails → route to Troubleshooting Agent

**Output:**
```json
{
  "validation_status": "pass | fail",
  "checks": [
    { "name": "services_running", "status": "pass | fail", "detail": "" },
    { "name": "connectors_healthy", "status": "pass | fail", "detail": "" },
    { "name": "first_scan_complete", "status": "pass | fail", "detail": "" },
    { "name": "rbac_configured", "status": "pass | fail", "detail": "" }
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

| | |
|---|---|
| **Goal** | Classify every incoming Jira UCSC ticket — assign category, severity, suggest diagnostics, check duplicates, and draft a customer email. |
| **Lane** | Run / Support |
| **Trigger** | `jira_ticket_created` (UCSC project only) |

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
- [ ] Ticket classifier (6 categories)
- [ ] Severity assigner (P0-P3)
- [ ] Diagnostic suggester
- [ ] Duplicate / similar ticket search (RAG)
- [ ] Customer email drafter
- [ ] Customer Memory read before processing
- [ ] Customer Memory update after processing
- [ ] Slack card to #cs-ticket-triage with approval buttons
- [ ] On Approve: update Jira labels + send email
- [ ] Dashboard deep-link to Customer Profile → Tickets tab

---

### Agent 7: Troubleshooting

| | |
|---|---|
| **Goal** | Analyze support bundles and system diagnostics to find root cause with a confidence score. If confidence is low, auto-route to Escalation. |
| **Lane** | Run / Support |
| **Trigger** | `support_bundle_uploaded` event |

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
  "evidence": ["service_x timeout at 14:23", "proxy_config missing bypass rule"],
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
- [ ] Support bundle parser
- [ ] Health snapshot analyzer
- [ ] Service status analyzer
- [ ] Connector status analyzer
- [ ] Root cause identification engine
- [ ] Confidence scoring (0-100)
- [ ] Auto-route to Escalation if confidence < 70%
- [ ] Slack card to #cs-ticket-triage
- [ ] Dashboard deep-link to Customer Profile → Tickets tab

---

### Agent 8: Escalation Writer

| | |
|---|---|
| **Goal** | Compile a complete escalation document for engineering with all context, evidence, reproduction steps, and customer update draft. |
| **Lane** | Run / Support |
| **Trigger** | `escalation_needed` (from Troubleshooting confidence < 70%), severity = High, or RCA needed |

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
- [ ] Customer context compiler
- [ ] Technical summary generator
- [ ] Evidence collector and formatter
- [ ] Reproduction steps writer
- [ ] Timeline builder
- [ ] Customer update draft generator
- [ ] Slack card to #cs-escalations with Approve button
- [ ] On Approve: attach doc to Jira ticket + notify engineering
- [ ] Dashboard deep-link to Customer Profile → Tickets tab

---

### Agent 9: Health Monitor

| | |
|---|---|
| **Goal** | Run daily health checks on every customer — compute health scores, detect risk flags, and draft proactive Jira tickets for at-risk customers. |
| **Lane** | Value |
| **Trigger** | `daily_health_check` (scheduled cron, 8 AM daily) |

**Input:**
- Scan freshness data (last scan timestamp)
- Connector heartbeat data (last seen)
- License utilization
- Job failure ratio
- Open P0/P1 tickets (age in days)
- Renewal dates
- Customer Memory (current health_score, risk_flags)

**Process:**
1. For each customer:
   - Check scan freshness (>48 hours without scan = flag)
   - Check connector heartbeat (>24 hours down = flag)
   - Check license utilization
   - Check job failure ratio (>20% = flag)
   - Check open P0/P1 tickets (>5 days = flag)
   - Check renewal date (<90 days + existing risk flags = elevated risk)
2. Compute health score (0-100) from weighted checks
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
      "risk_flags": ["scan_stale", "p0_open_7_days"],
      "draft_jira_ticket": { "summary": "Proactive: Scan stale >48hrs", "priority": "P2" }
    }
  ],
  "threshold_alerts": [
    { "type": "issue_cluster", "issue": "connector_failure", "affected_count": 7 }
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
- [ ] Scan freshness checker
- [ ] Connector heartbeat checker
- [ ] License utilization checker
- [ ] Job failure ratio checker
- [ ] Open P0/P1 age checker
- [ ] Renewal proximity checker
- [ ] Health score calculator (weighted formula)
- [ ] Risk flag detector
- [ ] Cross-customer pattern detection (5+ same issue = urgent)
- [ ] Proactive Jira ticket drafter
- [ ] Customer Memory update (health_score, risk_flags)
- [ ] Daily cron trigger (8 AM)
- [ ] Slack card to #cs-health-alerts
- [ ] Threshold alerts to #cs-executive-urgent
- [ ] Dashboard deep-link to At-Risk Dashboard

---

### Agent 10: QBR / Value Narrative

| | |
|---|---|
| **Goal** | Generate Quarterly Business Review documents — bucket customers by sentiment (Happy/Neutral/Unhappy) with evidence, diagnose root causes of dissatisfaction, and write renewal recommendations. |
| **Lane** | Value |
| **Trigger** | Manual request, quarterly schedule, `renewal_within_90_days` |

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
7. Write value narrative: risk reduction achieved, issues resolved, platform utilization
8. Write renewal recommendation

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
- [ ] 90-day Jira ticket aggregator
- [ ] 90-day Fathom sentiment aggregator
- [ ] HubSpot deal data reader
- [ ] Sentiment bucketing engine (Happy/Neutral/Unhappy with thresholds)
- [ ] Root cause analyzer (Jira categories × Fathom call themes)
- [ ] Value narrative generator
- [ ] Renewal recommendation writer
- [ ] QBR document generator (markdown)
- [ ] Customer Memory update (sentiment_bucket)
- [ ] Slack card to #cs-qbr-drafts
- [ ] Dashboard deep-link to Customer Profile → QBR tab

---

## 6. Slack Architecture

### 6.1 Channel Map

| Channel | What Gets Posted | Who Sees It | Dashboard Link |
|---------|-----------------|-------------|----------------|
| **#cs-executive-digest** | Weekly executive summary (Monday 9 AM) | Sarfaraz, Jeelan, Brian | At-Risk Dashboard |
| **#cs-executive-urgent** | Threshold alerts (5+ same issue, health crash, SLA cascade, churn signal, pipeline stall) | Sarfaraz, Jeelan, Brian | At-Risk Dashboard (filtered) |
| **#cs-call-intelligence** | Post-call summaries + action items + sentiment | All CS Managers | Customer Profile → Calls tab |
| **#cs-ticket-triage** | New ticket classifications + suggested actions | CS Engineers, Support Lead | Customer Profile → Tickets tab |
| **#cs-health-alerts** | Daily health check results + risk flags | CS Managers, Directors | At-Risk Dashboard |
| **#cs-presales-funnel** | Pipeline analytics + stalled deal alerts | Sales Leadership | Pipeline Analytics page |
| **#cs-qbr-drafts** | QBR document drafts for review | CS Managers | Customer Profile → QBR tab |
| **#cs-escalations** | Engineering escalation docs for approval | CS Managers, Engineering Lead | Customer Profile → Tickets tab |
| **#cs-delivery** | SOW drafts, deployment status | CS Managers, Onboarding Lead | Customer Profile → Overview tab |

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

- [ ] Slack Bolt SDK integration
- [ ] 9 channels configured in environment variables
- [ ] Standard card builder function (Block Kit JSON)
- [ ] Approve/Edit/Dismiss interactive button handlers
- [ ] Interactivity webhook endpoint (`POST /api/webhooks/slack/interactions`)
- [ ] Deep-link URL builder (dashboard base URL + customer/tab params)
- [ ] Action execution on Approve (Jira update, email send, etc.)
- [ ] Edit flow (Slack thread → modified draft → approve)
- [ ] Dismiss logging to audit log
- [ ] Slack signature verification for all incoming webhooks

---

## 7. Dashboard (3 Pages)

### 7.1 Page 1: At-Risk Dashboard — `/dashboard`

The single-pane view of portfolio health. What leadership cares about most. Accessed via Slack deep-links.

**Layout:**

| Section | Content |
|---------|---------|
| **Top Row** | 4 KPI cards: Total Customers, At-Risk Count, Open P0/P1 Tickets, Avg Health Score |
| **Main** | At-Risk Customer Table — Columns: Customer Name, Health Score (color-coded), Sentiment Bucket, Open Tickets, Days to Renewal, Risk Flags, Last Call Date. Click row → Customer Profile. Filters: Risk level, CSM owner, Industry, Renewal window |
| **Right Sidebar** | Live Alert Feed: latest health alerts, escalations, threshold breaches |
| **Bottom** | Trend Charts: Health score distribution (12-week heatmap), Ticket velocity (opened vs resolved/week), Sentiment trend (portfolio-wide over time) |

**Checklist:**
- [ ] KPI cards component (4 metrics from API)
- [ ] At-Risk Customer Table (sortable, filterable)
- [ ] Color-coded health score column
- [ ] Row click → navigate to Customer Profile
- [ ] Filter controls (risk level, CSM, industry, renewal window)
- [ ] Live Alert Feed sidebar
- [ ] Health score heatmap chart (12 weeks)
- [ ] Ticket velocity chart (opened vs resolved)
- [ ] Sentiment trend chart (positive/neutral/negative over time)
- [ ] URL query param support for pre-filtering from Slack deep-links

### 7.2 Page 2: Customer Profile — `/dashboard/customer/{customer_id}`

Everything about one customer in one place. CSMs land here from Slack deep-links.

**Header:** Customer name, health score gauge, sentiment badge, renewal countdown, CSM owner

**Tabs:**

| Tab | Content |
|-----|---------|
| **Overview** | Customer Memory data: deployment mode, version, integrations, constraints, risk flags, feature requests |
| **Tickets** | All UCSC tickets (priority, status, SLA countdown, triage summary). Click ticket → detail view |
| **Calls** | All Fathom calls (date, duration, sentiment, key topics, action items). Expandable rows |
| **Health History** | Health score over time (line chart), risk flag timeline, connector/scan status history |
| **QBR** | Latest QBR draft, sentiment bucket history, value narrative, renewal recommendation |
| **HubSpot** | Deal stage, pipeline position, POC/demo dates, associated contacts |

**Checklist:**
- [ ] Customer header component (health gauge, sentiment badge, renewal countdown)
- [ ] Tab navigation component
- [ ] Overview tab (Customer Memory display)
- [ ] Tickets tab (table with priority, status, SLA, triage summary)
- [ ] Calls tab (expandable call list with sentiment, topics, actions)
- [ ] Health History tab (line chart + risk flag timeline)
- [ ] QBR tab (document viewer + sentiment history)
- [ ] HubSpot tab (deal info + contacts)
- [ ] URL query param for tab pre-selection (`?tab=tickets`)
- [ ] API endpoints for each tab's data

### 7.3 Page 3: Pipeline Analytics — `/dashboard/pipeline`

Pre-sales funnel visibility for sales leadership.

| Section | Content |
|---------|---------|
| **Funnel** | Deal count and value at each stage (LeadGen → Demo → POC → Close) |
| **Conversion** | Stage-to-stage percentages with week-over-week change |
| **Stalled Deals** | Deals stuck >30 days (name, owner, days stalled, last activity) |
| **Blockers** | Top reasons for Closed Lost (HubSpot close_reason + Fathom call themes) |
| **Time-in-Stage** | Average days per stage, trend over 12 weeks |

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

| Action | Rule |
|--------|------|
| Escalation to engineering | ALWAYS requires CS Manager approval |
| QBR documents | ALWAYS reviewed by CSM before sharing |
| SOW documents | ALWAYS reviewed by CSM before sharing |
| Modify customer data | ALWAYS requires human approval |
| Delete anything | ALWAYS requires human approval |

### 8.3 Actions That Can Earn Autonomy

| Action | Autonomy Threshold | Until Threshold Met |
|--------|-------------------|---------------------|
| Health alerts to Slack | Auto from Day 1 (informational) | — |
| Executive digest to Slack | Auto from Day 1 (informational) | — |
| Update Jira labels | Triage accuracy > 95% for 3+ consecutive weeks | Draft + Slack approval |
| Create Jira ticket | Triage accuracy > 90% for 3+ consecutive weeks | Draft + Slack approval |
| Send email to customer | Fathom validation > 0.90 for 4+ consecutive weeks | Draft + Slack approval |

### 8.4 Accuracy Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Triage accuracy** | Approved without edits / Total triage outputs | > 90% |
| **False positive rate** | Health alerts dismissed / Total health alerts | < 20% |
| **Human override rate** | (Edited + Dismissed) / Total outputs | < 15% |
| **Fathom validation** | Agent output compared to Fathom AI for same call | > 0.80 |

### 8.5 Approval Workflow Checklist

- [ ] `agent_drafts` table (id, agent_id, event_id, customer_id, draft_type, draft_content JSON, status, slack_message_ts, slack_channel, approved_by, approved_at, edit_diff)
- [ ] `audit_log` table (log_id, timestamp, agent, event_id, customer_id, action, input_summary, output_summary, confidence, human_action, human_edit_diff, dashboard_url)
- [ ] Draft creation in every agent's output path
- [ ] Slack interactive button handler (approve/edit/dismiss)
- [ ] Action execution engine (on approve → do the thing)
- [ ] Edit flow (Slack thread modification → re-approve)
- [ ] Accuracy metric calculator (weekly computation)
- [ ] Autonomy gate checker (before each action, check if agent qualifies)

---

## 9. Executive Reporting

### 9.1 Weekly Executive Summary (Monday 9 AM → #cs-executive-digest)

| Section | Content | Dashboard Link |
|---------|---------|----------------|
| Portfolio Health | Health distribution (healthy/at-risk/critical), week-over-week delta | At-Risk Dashboard |
| Pre-Sales Pipeline | Funnel metrics, conversion rates, stalled deals, top blockers | Pipeline Analytics |
| Support Velocity | Tickets opened/resolved, avg resolution, SLA breaches, top categories | At-Risk Dashboard |
| Sentiment Trends | Who moved happy→unhappy and why (linked to calls/tickets) | Customer Profile → Calls |
| Risk Alerts | Customers needing immediate attention, pending escalations | At-Risk Dashboard (filtered) |
| Feature Demand | Top features ranked by customer count + ARR impact | At-Risk Dashboard |
| Agent Accuracy | Triage accuracy, false positive rate, human override rate, Fathom validation | Internal metric |

### 9.2 Threshold Alerts (Real-Time → #cs-executive-urgent)

These fire immediately. Do NOT wait for the weekly digest.

| Alert | Condition |
|-------|-----------|
| **Issue Cluster** | 5+ customers report same issue category in 7 days |
| **Health Crash** | Enterprise customer health drops >20 points in a week |
| **SLA Cascade** | 3+ P0/P1 tickets breach SLA in same week |
| **Churn Signal** | Renewal <60 days + unhappy sentiment + open P0 |
| **Pipeline Stall** | 5+ deals stuck in same stage >30 days |

### 9.3 Executive Reporting Checklist

- [ ] Weekly digest aggregator (pulls from all agent outputs)
- [ ] Portfolio health calculator
- [ ] Support velocity metrics
- [ ] Sentiment trend tracker
- [ ] Feature demand ranker
- [ ] Agent accuracy reporter
- [ ] Monday 9 AM cron trigger
- [ ] Slack message to #cs-executive-digest
- [ ] Issue cluster detector (5+ same issue in 7 days)
- [ ] Health crash detector (>20 point drop)
- [ ] SLA cascade detector (3+ P0/P1 SLA breaches)
- [ ] Churn signal detector (renewal + sentiment + P0)
- [ ] Pipeline stall detector (5+ deals stuck >30 days)
- [ ] Real-time alert to #cs-executive-urgent

---

## 10. Event Routing Map

| Event | Source | Agent | Slack Channel | Dashboard Deep-Link |
|-------|--------|-------|---------------|---------------------|
| `jira_ticket_created` | Jira UCSC webhook | Ticket Triage | #cs-ticket-triage | `/dashboard/customer/{id}?tab=tickets` |
| `jira_ticket_updated` | Jira UCSC webhook | Triage / Troubleshoot | #cs-ticket-triage | `/dashboard/customer/{id}?tab=tickets` |
| `support_bundle_uploaded` | Manual / Jira | Troubleshooting | #cs-ticket-triage | `/dashboard/customer/{id}?tab=tickets` |
| `zoom_call_completed` | Fathom webhook | Fathom Agent (Call Intel) | #cs-call-intelligence | `/dashboard/customer/{id}?tab=calls` |
| `deal_stage_changed` | HubSpot webhook | Pre-Sales Funnel | #cs-presales-funnel | `/dashboard/pipeline` |
| `daily_health_check` | Cron (8 AM) | Health Monitor | #cs-health-alerts | `/dashboard` |
| `renewal_within_90_days` | Cron scan | QBR + Health | #cs-qbr-drafts | `/dashboard/customer/{id}?tab=qbr` |
| `new_customer` | HubSpot Closed Won | SOW & Prerequisite | #cs-delivery | `/dashboard/customer/{id}?tab=overview` |
| `deployment_ready` | Manual trigger | Deployment Intel | #cs-delivery | `/dashboard/customer/{id}?tab=overview` |
| `escalation_needed` | Troubleshoot output | Escalation Writer | #cs-escalations | `/dashboard/customer/{id}?tab=tickets` |
| `weekly_exec_report` | Cron (Mon 9 AM) | Executive Reporter | #cs-executive-digest | `/dashboard` |

---

## 11. Implementation Phases

### Phase 1: Core Pipeline + Slack (Days 1-12)

**Goal:** 3 data integrations working, 4 core agents live, Slack delivery active, 2 dashboard pages deployed.

**Gate:** Process a real Fathom call AND a real UCSC ticket end-to-end through Slack with human approval.

| Day | Deliverable | Done When |
|-----|------------|-----------|
| 1 | FastAPI scaffold, DB schema (customers, tickets, insights, events, audit_log, agent_drafts), Docker Compose | Backend runs, DB migrated, health endpoint returns 200 |
| 2 | Customer Memory Agent: JSON store, CRUD API, seed script | Create/read/update customer memory via API |
| 3 | Fathom integration: webhook receiver, transcript fetcher, storage | Real transcript stored from Fathom webhook |
| 4 | Call Intelligence pipeline: transcript → summary + action items + sentiment → Customer Memory | 1 real transcript processed, output matches expected format |
| 5 | Jira UCSC integration: webhook receiver, ticket normalizer, storage | Real UCSC ticket stored from Jira webhook |
| 6 | Ticket Triage Agent: classify, severity, diagnostics, duplicates, email draft | 3 real tickets triaged, output reviewed by CS Engineer |
| 7 | CS Orchestrator: event classifier, routing for all Phase 1 events | Routes `jira_ticket_created` and `zoom_call_completed` correctly |
| 8 | Slack bot: 9 channels, card posting with Approve/Edit/Dismiss, webhook handlers | Post card to #cs-ticket-triage, click Approve, action executes |
| 9 | Wire agents → Slack: Triage → #cs-ticket-triage, Call Intel → #cs-call-intelligence. Deep-links. | End-to-end: Jira ticket → triage → Slack card → approve → Jira updated |
| 10 | At-Risk Dashboard (Page 1): customer table, health scores, KPI cards | Dashboard loads with real customer data |
| 11 | Customer Profile (Page 2): tabs for overview, tickets, calls. Linked from Slack. | Click Slack deep-link → correct customer + correct tab |
| 12 | Integration test: 5 real tickets + 3 real calls end-to-end. Gate review. | Sarfaraz approves Phase 1 complete |

---

### Phase 2: Expand + Health + Pre-Sales (Days 13-22)

**Goal:** Health monitoring, troubleshooting, escalation, pre-sales funnel, executive reporting all live.

**Gate:** Weekly executive digest generates correctly. At-Risk Dashboard shows real health scores. HubSpot pipeline visible.

| Day | Deliverable | Done When |
|-----|------------|-----------|
| 13 | Troubleshooting Agent: bundle parser, diagnostic analysis, confidence scoring | 1 real bundle parsed, root cause matches engineer assessment |
| 14 | Escalation Agent: context + evidence + repro steps. Wire to #cs-escalations. | Escalation doc reviewed by engineering, confirmed useful |
| 15 | Health Monitor Agent: daily checks, scoring formula, risk flags | Scores computed for all customers, manual verification matches |
| 16 | Health → Slack: daily digest to #cs-health-alerts, thresholds to #cs-executive-urgent | 8 AM summary posts to Slack, threshold alert fires on test data |
| 17 | HubSpot integration: API connector, deal sync, stage change webhook | Real HubSpot deals visible in DB, stage change triggers event |
| 18 | Pre-Sales Funnel Agent: conversion rates, blocker analysis, stalled deals | Funnel report matches manual HubSpot analysis within 10% |
| 19 | Pipeline Analytics (Page 3): funnel chart, stalled deals, blockers | Page loads with real HubSpot data |
| 20 | Executive Reporter: weekly digest from all agents. Wire to #cs-executive-digest. | First weekly digest generated and posted to Slack |
| 21 | Fathom validation: compare agent output to Fathom AI. Track in audit log. | Validation scores for last 10 calls, score > 0.80 |
| 22 | Integration test: 1 full week of real data. Gate review. | Sarfaraz approves Phase 2 complete |

---

### Phase 3: QBR + SOW + Autonomy (Days 23-30)

**Goal:** QBR generation, SOW automation, selective autonomy based on measured accuracy.

**Gate:** QBR sentiment buckets match CSM intuition for 80%+ customers. Auto-actions gated by accuracy metrics.

| Day | Deliverable | Done When |
|-----|------------|-----------|
| 23 | QBR Agent: sentiment bucketing, root cause analysis, value narrative | QBR for 3 customers, CSMs confirm sentiment buckets correct |
| 24 | QBR → Dashboard + Slack: Customer Profile QBR tab, #cs-qbr-drafts | QBR visible in dashboard and Slack, links work end-to-end |
| 25 | SOW & Prerequisite Agent: template SOW, checklist logic | SOW for 1 real customer, CS Manager confirms quality |
| 26 | Deployment Intelligence Agent: validation checks, failure routing | Validation report for 1 real deployment |
| 27 | Accuracy review: 4 weeks of data → triage accuracy, false positive rate, override rate | Accuracy report generated, qualifying agents identified |
| 28 | Conditional autonomy: enable auto-label if triage >90%, auto-email if Fathom >0.90 | Auto-actions enabled only for qualifying agents |
| 29 | Dashboard polish: responsive, loading states, error handling, auth | Works on desktop/tablet, auth restricts to CS team |
| 30 | Final integration test. Documentation. Production deployment. | System live. All channels active. Dashboard deployed. |

---

## 12. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.11+ / FastAPI | API server, agent orchestration |
| Database | PostgreSQL | Structured data, customer memory, drafts, audit log |
| Vector DB | ChromaDB | RAG search (similar tickets, call knowledge) |
| AI | Anthropic Claude Sonnet | All agent LLM calls |
| Slack | Slack Bolt SDK (Python) | Bot, interactive messages, webhooks |
| Frontend | React 18 + Vite | Dashboard SPA (3 pages) |
| Charts | Recharts + D3.js | Heatmap, funnel, trend charts |
| State | Zustand | Client-side state management |
| Styling | Tailwind CSS | Dashboard styling |
| Infra | Docker + Docker Compose | Containerization |
| Integrations | Fathom API, Jira REST API, HubSpot API | Data ingestion |

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

- [ ] JWT authentication for dashboard API
- [ ] Customer-scoped database queries (no cross-customer leaks)
- [ ] Slack webhook signature verification
- [ ] Jira webhook signature verification
- [ ] Fathom webhook HMAC verification
- [ ] Environment variables for all secrets (no hardcoded keys)
- [ ] Dashboard auth gate (login required)
- [ ] Audit log for all agent actions
- [ ] Audit log for all human approvals/edits/dismissals

---

*30 working days. 3 phases. 10 agents. 9 Slack channels. 3 dashboard pages.*
*Every agent output is a draft. Every action requires approval. Autonomy is earned, not assumed.*
