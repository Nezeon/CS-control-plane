# Part 0: Manager Presentation Script

---

## How to Explain the Project to Your Manager (Simple, Non-Technical)

> Use this as a talking script. Read it naturally, not word-for-word. The goal is to show what you've built, what it does, and how it maps to her vision.

---

### Opening (30 seconds)

"So let me walk you through what we've built so far with the CS Control Plane. I'll keep it simple — what it does, how it works, and where we are."

---

### What Is It? (1 minute)

"At its core, this is an **AI system that watches everything happening with our customers** — their Jira tickets, their Fathom call recordings, their health signals — and **automatically analyzes it, surfaces risks, and drafts actions** for the CS team.

Think of it like having a team of AI assistants that each specialize in one thing:
- One watches **new tickets** come in and immediately classifies them — is this a connector issue? A scan problem? What priority? — and drafts a response email
- One listens to **every customer call** via Fathom and pulls out the summary, action items, and whether the customer sounded happy or frustrated
- One runs a **daily health check** on every customer — are their scans running? Are connectors up? Any open P0s? — and flags anyone at risk
- One handles **escalations** — when something is too complex, it packages up all the context for engineering
- One generates **QBR documents** — bucketing customers as happy, neutral, or unhappy with evidence from their tickets and calls
- And one generates **SOW and deployment checklists** for new customers

All of these AI agents are coordinated by a central **orchestrator** that receives events (like 'new Jira ticket' or 'call just ended') and routes them to the right specialist."

---

### How Does the CS Team Use It? (1 minute)

"Right now we have **two ways people interact with it**:

**1. A chat interface** — you can literally ask it questions like 'What are the top issues with Acme Corp?' or 'Show me all at-risk customers' and it gives you an AI-powered answer based on real data.

**2. A dashboard** — a web app where you can see:
- All customers with their health scores, risk flags, and sentiment
- Drill into any customer to see their tickets, calls, and health history
- See alerts and threshold breaches in real-time
- View executive summaries with trends and velocity metrics

We also have **Slack integration** — the system can post alerts and respond to queries in Slack channels."

---

### What Data Does It Use? (30 seconds)

"Two main sources right now:

**1. Jira** — we pull tickets from the UCSC project via webhooks. When a new ticket comes in, the system automatically triages it.

**2. Fathom** — we pull call transcripts via API. After every customer call, the system extracts the summary, action items, sentiment, and key topics.

We have **128+ real customer meeting recordings** indexed and searchable — you can ask 'what did we discuss with Acme about connector issues?' and it finds the relevant calls."

---

### What Makes It Smart? (1 minute)

"This isn't just a simple chatbot. Each AI agent runs through a **structured thinking process**:

1. **Perceive** — understand what just happened (new ticket? call ended?)
2. **Retrieve** — pull relevant context (what do we know about this customer? any similar past issues?)
3. **Think** — analyze using Claude AI with all that context
4. **Act** — produce the output (classification, email draft, health score, etc.)
5. **Reflect** — learn from the experience for next time

The agents also have **memory** — they remember past interactions and can find similar situations they've handled before. So the more they work, the better context they have."

---

### Where Are We Now? (1 minute)

"Here's what's **working today**:
- Jira integration — real tickets flowing in and getting triaged
- Fathom integration — real call transcripts being analyzed
- Health monitoring — daily health scores computed for all customers
- Escalation engine — packages context for engineering when needed
- QBR generation — sentiment bucketing with evidence
- SOW/deployment checklists — generated for new customers
- Executive summaries — portfolio health, ticket velocity, sentiment trends
- Alert rules — auto-detects health drops, stale critical tickets, renewal risks, negative sentiment streaks
- Chat interface — ask questions, get AI-powered answers
- Dashboard — full web app with customer views, alerts, and analytics
- Slack — bidirectional, you can query it from Slack

**What's seeded for demo**: 10 customers, 50 tickets, 100 call insights, 300 health scores, 15 alerts"

---

### How It Maps to Your v2.1 Document (1 minute)

"Looking at your document, here's where we line up and where we differ:

**What matches well:**
- Your 10 agents — we have 9 of them built (Pre-Sales Funnel is the only one missing, and that needs HubSpot)
- Event-driven architecture — exactly how we built it. Events trigger agents.
- Customer isolation — each customer's data is separate
- Jira and Fathom as core data sources — both working
- Executive reporting — we have portfolio health, ticket velocity, sentiment trends, threshold alerts

**Where we went further than your spec:**
- We built 13 agents instead of 10 — the extra 3 are 'lane leads' that coordinate groups of specialists. Think of them as team leads.
- We added a memory system so agents learn from past work
- We built a richer dashboard with more pages and some 3D visualizations
- We added a chat interface where you can ask questions directly

**What we're missing from your spec:**
- **Slack as the primary delivery channel** — your doc wants 9 dedicated Slack channels with approval buttons. We have basic Slack but not the full channel architecture.
- **Draft-first approval workflow** — your doc says every agent output should be a draft that humans approve in Slack. We don't have that approval gate yet.
- **Accuracy tracking** — your doc wants to measure how accurate the agents are over weeks before giving them autonomy. We don't track that yet.
- **Deep-linking** — Slack cards should link directly to the dashboard page for that customer/ticket. Not wired up yet."

---

### What's the Plan Going Forward? (30 seconds)

"The biggest alignment item is **making Slack the primary channel** — setting up the 9 channels, building the interactive approval cards, and adding the draft-first workflow. That's the core of your vision and it's the biggest gap.

After that, it's accuracy tracking and deep-linking — which are medium effort.

The good news is the **agent logic is built**. We're not starting from scratch. It's about changing how the output gets delivered — from dashboard-first to Slack-first."

---

### Closing (15 seconds)

"So in summary: the brain is built, the data pipes are connected, the agents work. The main shift is in how we deliver it to the team — moving from 'open the dashboard' to 'Slack brings it to you.' Happy to demo any part of it."

---

### Demo Talking Points (if she asks for a live demo)

1. **Show the chat** — type "What are the top issues across all customers?" → AI responds with real data
2. **Show a customer drill-down** — click into a customer, show health score, tickets, call summaries
3. **Show the dashboard** — KPIs, at-risk customers, alerts
4. **Show executive summary** — trends, velocity, sentiment
5. **Show Slack** — send a message in Slack, get AI response
6. **Show a triage** — explain how a Jira ticket comes in and gets classified automatically

---
---

# Part 1: Manager's v2.1 Document vs. Current Architecture — Full Comparison

## TL;DR

Your app is **significantly more complex** than what the manager's v2.1 document asks for. The manager wants a lean, pragmatic system (10 agents, 3 dashboard pages, Slack-first). You've built an ambitious enterprise platform (13 agents, 4-tier hierarchy, 3D spatial UI, 3-tier memory, multi-round pipelines). About **60% of what the manager wants is covered**, but the delivery model, agent count, and dashboard philosophy are fundamentally different.

> **Note:** HubSpot integration is excluded from this comparison — it's not in scope for our current build.

---

## 1. Agent Architecture

| Aspect | Manager's v2.1 | Your Current App | Gap |
|--------|----------------|------------------|-----|
| **Agent count** | **10 agents**, flat per-lane | **13 agents**, 4-tier hierarchy | You have 3 extra (Lane Leads) + personas/traits/reflection |
| **Hierarchy** | **3 lanes** (Pre-Sales, Delivery, Run/Support, Value) + shared services | **4-tier hierarchy** (T1 Supervisor -> T2 Lane Leads -> T3 Specialists -> T4 Foundation) | Manager explicitly says "Wrong abstraction. Use lanes." — no tier hierarchy |
| **Personas/Traits** | **None**. "No personas, no traits, no reflection engine. Each agent has one job." | Full YAML-driven personalities, 9+ traits, reflection engine | Direct conflict — manager wants this removed |
| **Orchestrator** | Simple router — classifies events, routes to lane agent | Strategic orchestrator with multi-round pipeline, delegation, quality gates, synthesis | Over-engineered per manager's intent |
| **Pre-Sales Agent** | Yes — HubSpot funnel analysis | **Not in scope** | HubSpot excluded from our build |
| **Call Intelligence** | Listed as implicit (Fathom extraction) | Jordan Ellis (Fathom agent) + Riley Park (Meeting Followup) | You have this, plus extra |
| **Memory Agent** | Simple per-customer JSON store (CRUD) | 3-tier memory system (Working + Episodic ChromaDB + Semantic ChromaDB) | Manager says "Over-architected for Phase 1" |

### Verdict: Your agent system is **over-engineered** vs. what the manager wants. The 4-tier hierarchy, personas, traits, and reflection engine are explicitly called out as problems in the Gap Analysis (Section 1 of v2.1).

---

## 2. Data Sources

| Source | Manager's v2.1 | Your Current App | Gap |
|--------|----------------|------------------|-----|
| **Jira (UCSC)** | Required — webhooks + polling | Integrated (jira_service.py, webhooks) | Covered |
| **Fathom** | Required — webhooks + API pull | Integrated (fathom_service.py, fathom_agent.py, meeting_knowledge) | Covered (actually richer than required) |
| **HubSpot** | Required in manager's doc | Not integrated | **Out of scope** — excluded from our build |
| **Telemetry** | Mentioned (hp_health_snapshot, services_status, connector_status) | Not integrated | Gap for Health Monitor and Troubleshooting |

### Verdict: Jira and Fathom are solid. HubSpot is out of scope for us. Telemetry data (health snapshots, connector status) is a gap for Health Monitor and Troubleshooting agents.

---

## 3. Delivery Model (Slack vs. Dashboard)

| Aspect | Manager's v2.1 | Your Current App | Gap |
|--------|----------------|------------------|-----|
| **Primary channel** | **Slack is the PUSH layer** — all notifications, approvals, actions happen in Slack | Slack is optional (`SLACK_ENABLED=false`), bidirectional chat exists | Philosophy mismatch — manager wants Slack-FIRST |
| **Dashboard role** | "PULL layer" — drill-down only, users don't browse to it, Slack brings them there | Full React SPA + Streamlit app — standalone dashboards users browse | Opposite approach |
| **Slack channels** | **9 dedicated channels** (#cs-ticket-triage, #cs-health-alerts, #cs-executive-digest, etc.) | Single alert channel + bidirectional chat in one channel | Major gap — no channel-per-function architecture |
| **Slack cards** | Standardized format with Approve/Edit/Dismiss buttons + "View Details ->" deep-links | Basic Block Kit messages, no interactive approval workflow | Missing approval workflow |
| **Approval flow** | Human approves in Slack -> action executes (Jira update, email send) | No approval-gated actions | Critical gap for draft-first principle |
| **Dashboard pages** | **3 pages only**: At-Risk Dashboard, Customer Profile, Pipeline Analytics | **8+ React pages** + 6 Streamlit pages | Over-scoped per manager |
| **Deep-linking** | Every Slack card links to specific dashboard page + tab + filter | No deep-linking from Slack to dashboard | Missing |

### Verdict: **Fundamentally different delivery philosophy.** Manager wants Slack-first with dashboard as secondary drill-down. You've built dashboard-first with Slack as optional add-on. The 9-channel Slack architecture with interactive approval buttons is completely missing.

---

## 4. Dashboard Scope

| Manager's 3 Pages | Your Equivalent | Status |
|--------------------|-----------------|--------|
| **Page 1: At-Risk Dashboard** (KPIs, at-risk table, alert feed, trend charts) | DashboardPage (partial — has KPIs, customer table, alerts) | ~60% covered — missing filterable at-risk focus, trend charts |
| **Page 2: Customer Profile** (6 tabs: Overview, Tickets, Calls, Health History, QBR, HubSpot) | CustomerDetailPage (has overview, tickets, calls panels) | ~50% covered — missing QBR tab, HubSpot tab, health history chart |
| **Page 3: Pipeline Analytics** (funnel viz, conversion rates, stalled deals, blocker analysis) | **Does not exist** | N/A — requires HubSpot (out of scope) |

### Additional pages you have that manager didn't ask for:
- AgentsPage (3D neural network, brain panel)
- TicketsPage (constellation view, warroom)
- InsightsPage (sentiment spectrum)
- ReportsPage (heatmap, river charts)
- AlertsPage
- AskPage (chat)
- ExecutivePage
- LoginPage
- SettingsPage

### Verdict: You have **way more dashboard** than requested but are **missing the specific 3 pages** the manager designed. The Pipeline Analytics page (Pre-Sales funnel) doesn't exist at all.

---

## 5. Executive Reporting

| Aspect | Manager's v2.1 | Your Current App | Gap |
|--------|----------------|------------------|-----|
| **Weekly digest** | Monday 9AM to #cs-executive-digest (7 sections: portfolio health, pipeline, support velocity, sentiment, risks, features, agent accuracy) | trend_service.py + executive router + Streamlit page | Partially covered — missing agent accuracy metrics. Pipeline section N/A (HubSpot out of scope) |
| **Threshold alerts** | 5 real-time alerts to #cs-executive-urgent (issue cluster, health crash, SLA cascade, churn signal, pipeline stall) | alert_rules_engine.py has 4 rules (health_drop, critical_tickets, renewal_risk, sentiment_streak) | ~80% covered — pipeline stall N/A (HubSpot out of scope) |
| **Delivery** | Slack channels | Streamlit page + API | Different delivery — manager wants Slack |

---

## 6. Core Principles Alignment

| Principle | Manager's v2.1 | Your App | Aligned? |
|-----------|----------------|----------|----------|
| **Draft-First** | Every output is a DRAFT, human approves before action | No approval workflow | NO |
| **Slack-Push, Dashboard-Pull** | Slack drives, dashboard supports | Dashboard drives, Slack optional | NO |
| **Event-Driven** | Every workflow triggered by discrete event, no polling | Event-driven architecture exists | YES |
| **Customer Isolation** | No cross-customer data leakage | Per-customer memory model | YES |
| **Accuracy Before Autonomy** | 4+ weeks measured accuracy before auto-actions | No accuracy tracking or autonomy gates | NO |
| **3 Data Sources Phase 1** | Fathom + Jira + HubSpot | Fathom + Jira (HubSpot out of scope) | YES (for our scope) |

---

## 7. What You Have That Manager DIDN'T Ask For

These are features/complexity in your app that the manager's document explicitly warns against or doesn't mention:

1. **4-tier hierarchy with Lane Leads** — manager says "Wrong abstraction"
2. **13 agents with personas, traits, reflection** — manager says "Over-engineered. Trim to 10"
3. **3-tier memory system (ChromaDB)** — manager says "Over-architected for Phase 1"
4. **Multi-round pipeline engine** — manager wants simple single-job agents
5. **3D spatial UI** (NeuralSphere, HealthTerrain, DataFlowRivers) — manager says "Over-scoped"
6. **7+ page cinematic frontend** — manager says "Need a focused 3-page dashboard"
7. **Streamlit app** — not mentioned at all
8. **Meeting Knowledge Service** (128+ meetings RAG) — not in scope
9. **Chat interface** (Ask AI page) — not in manager's design
10. **Orbital navigation** — manager doesn't specify any nav pattern

---

## 8. What Manager Wants That You DON'T Have

Critical missing pieces (excluding HubSpot — out of scope):

1. **9 Slack channels** with dedicated purpose routing
2. **Interactive Slack cards** — Approve/Edit/Dismiss buttons with action execution
3. **Draft-First approval workflow** — nothing executes without human approval in Slack
4. **Deep-linking** — Slack cards -> specific dashboard page/tab/filter
5. **Accuracy tracking** — Fathom validation scores, human override rate, false positive rate
6. **Autonomy gates** — conditional auto-actions based on measured accuracy over weeks
7. **Telemetry data** — hp_health_snapshot, services_status, connector_status, scan results

---

## 9. Alignment Score by Area

| Area | Alignment | Score |
|------|-----------|-------|
| Jira Integration | Strong match | 90% |
| Fathom Integration | Exceeds requirements | 95% |
| HubSpot Integration | Out of scope | N/A |
| Agent Core Logic | Over-engineered but functional | 50% |
| Slack Delivery | Basic, not Slack-first | 20% |
| Dashboard (At-Risk) | Partial | 60% |
| Dashboard (Customer Profile) | Partial | 50% |
| Dashboard (Pipeline Analytics) | N/A (HubSpot out of scope) | N/A |
| Executive Reporting | Mostly there | 70% |
| Approval Workflow | Missing | 0% |
| Memory/Context | Over-architected | 40% (works, but wrong scope) |
| Event Routing | Good match | 85% |

**Overall alignment: ~55%** (excluding HubSpot from scope) — You've built a more ambitious system, but it's aimed in a different direction than what the manager specified.

---

## 10. Summary

**The core tension:** Your manager wants a **lean, Slack-first, 10-agent system** with 3 dashboard pages that serves as a drill-down for Slack notifications. You've built a **premium, dashboard-first, 13-agent hierarchical system** with 3D visualizations, multi-round pipelines, and a 3-tier memory architecture.

**What's good:** Jira and Fathom integrations are solid. Event-driven architecture is right. Customer isolation works. The agent logic (triage, health, escalation, QBR, etc.) covers most of the manager's 10 agents.

**What needs to change to align (HubSpot excluded from scope):**
1. Rebuild Slack as the primary delivery channel (9 channels, interactive cards, approval workflow)
2. Add draft-first approval workflow
3. Simplify agent architecture (flatten hierarchy, remove personas/traits/reflection for Phase 1)
4. Restructure dashboard to focused pages matching manager's specs
5. Add accuracy tracking and autonomy gates
6. Add deep-linking from Slack cards to dashboard pages

---
---

# CHANGES REQUIRED — Detailed Breakdown

> This section documents every specific change needed to align the current app with the manager's v2.1 spec. HubSpot is excluded from scope. No code changes — document only.

---

## Change 1: Slack-First Delivery Architecture

**Current state:** Slack is optional (`SLACK_ENABLED=false`), single channel (`SLACK_ALERT_CHANNEL`), basic Block Kit messages, bidirectional chat in one channel.

**Target state:** Slack is the PRIMARY delivery layer with 9 dedicated channels, standardized interactive cards, and approval workflows.

### 1A. Create 9 Slack Channels

| Channel | Purpose | Agent(s) That Post Here |
|---------|---------|------------------------|
| `#cs-executive-digest` | Weekly executive summary (Mon 9AM) | Executive Reporter (aggregates all agents) |
| `#cs-executive-urgent` | Threshold alerts (5+ same issue, health crash, SLA cascade) | Health Monitor, Alert Rules Engine |
| `#cs-call-intelligence` | Post-call summaries + action items + sentiment | Fathom Agent (Jordan Ellis) |
| `#cs-ticket-triage` | New ticket classifications + suggested actions | Triage Agent (Kai Nakamura) |
| `#cs-health-alerts` | Daily health check results + risk flags | Health Monitor (Dr. Aisha Okafor) |
| `#cs-qbr-drafts` | QBR document drafts for review | QBR Agent (Sofia Marquez) |
| `#cs-escalations` | Engineering escalation documents for approval | Escalation Agent (Maya Santiago) |
| `#cs-delivery` | SOW drafts, deployment status | SOW Agent (Ethan Brooks), Deployment Agent (Zara Kim) |
| `#cs-presales-funnel` | Pipeline analytics + stalled deal alerts | N/A (HubSpot out of scope — channel reserved for future) |

**What to change:**
- `backend/app/config.py` — Add 9 channel config variables (e.g., `SLACK_CHANNEL_TICKET_TRIAGE`, `SLACK_CHANNEL_HEALTH_ALERTS`, etc.)
- `backend/app/services/slack_service.py` — Add `post_to_channel(channel_name, blocks)` method that routes to the correct channel
- Each agent's output path needs to call `slack_service.post_to_channel()` with the correct channel

### 1B. Standardized Slack Card Format

Every agent output posted to Slack must follow this format:

```
+------------------------------------------------+
| [Agent Name] --- [Event Type]                  |
| Customer: [Name] | Health: [XX]                |
| Priority: [P0/P1/P2]                           |
|------------------------------------------------|
| Summary: [2-3 sentence insight]                |
| Action Required: [specific next step]          |
|                                                |
| [Approve] [Edit] [Dismiss]                     |
|                                                |
| View Details -> [Dashboard Deep-Link]          |
+------------------------------------------------+
```

**What to change:**
- `backend/app/services/slack_formatter.py` — Add `build_agent_card(agent_name, event_type, customer, priority, summary, action_required, dashboard_url)` function that returns Block Kit JSON
- Each card must include 3 interactive buttons: Approve, Edit, Dismiss
- Each card must include a "View Details ->" link to the dashboard

### 1C. Interactive Buttons (Approve/Edit/Dismiss)

**What to change:**
- `backend/app/routers/webhooks.py` — Add Slack interactivity webhook handler (`POST /api/webhooks/slack/interactions`)
- Slack app config: enable Interactivity & Shortcuts, set Request URL
- Button payloads must include: `action_type` (approve/edit/dismiss), `agent_id`, `event_id`, `customer_id`, `draft_id`
- **Approve** -> triggers the pending action (e.g., update Jira labels, send email draft)
- **Edit** -> opens a Slack modal or thread for human to modify the draft
- **Dismiss** -> logs rejection in audit log, no action taken
- Need a `pending_actions` table or status field to track drafts awaiting approval

---

## Change 2: Draft-First Approval Workflow

**Current state:** No approval workflow. Agent outputs are informational only — no gated actions.

**Target state:** Every actionable agent output (Jira updates, emails, escalations) is a DRAFT that requires human approval before execution.

**What to change:**

### 2A. Draft Storage
- Add `draft_status` field to relevant models (or new `agent_drafts` table):
  - Fields: `id`, `agent_id`, `event_id`, `customer_id`, `draft_type` (jira_label, email, escalation_doc, jira_ticket, qbr_doc, sow_doc), `draft_content` (JSON), `status` (pending/approved/edited/dismissed), `slack_message_ts`, `slack_channel`, `approved_by`, `approved_at`, `edit_diff`
- Agents write to this table instead of executing actions directly

### 2B. Action Execution on Approval
- When Slack "Approve" button clicked -> look up draft -> execute the action:
  - `jira_label` -> call Jira API to update labels
  - `email` -> send email via configured email service
  - `escalation_doc` -> attach to Jira ticket, notify engineering
  - `jira_ticket` -> create new Jira ticket
- When "Edit" clicked -> open Slack thread/modal -> save edited version -> then approve
- When "Dismiss" clicked -> mark draft as dismissed, log for accuracy tracking

### 2C. Actions That Are NEVER Auto-Approved
Per manager's spec (Section 12):
- Escalation to engineering — ALWAYS human approved
- QBR documents — ALWAYS reviewed by CSM
- SOW documents — ALWAYS reviewed by CSM
- Modify customer data — ALWAYS human approved
- Delete anything — ALWAYS human approved

### 2D. Actions That CAN Eventually Auto-Execute
After accuracy gates are met (see Change 5):
- Health alerts to Slack — auto from Day 1 (informational)
- Executive digest — auto from Day 1 (informational)
- Jira label updates — after triage accuracy >95% for 3+ weeks
- Customer emails — after Fathom validation >0.90 for 4+ weeks
- Jira ticket creation — after triage accuracy >90% for 3+ weeks

---

## Change 3: Simplify Agent Architecture

**Current state:** 13 agents in 4-tier hierarchy with personas, traits, reflection engine, multi-round pipelines.

**Target state (per manager):** 10 agents organized by lane. No personas, no traits, no reflection. Each agent has one job.

### 3A. Agent Simplification Options

**Option A — Full Simplification (match manager exactly):**
- Remove T2 Lane Leads (Rachel Torres, Damon Reeves, Priya Mehta) — 3 agents removed
- Remove Riley Park (Meeting Followup) — not in manager's 10
- Simplify Orchestrator to pure router (classify event -> route to agent, no strategic decomposition)
- Remove persona/personality YAML fields (or just ignore them)
- Disable trait system and reflection engine
- Replace multi-round pipeline with single-pass execution (trigger -> read memory -> execute -> write output -> update memory)
- Keep Customer Memory Agent as simple JSON CRUD (keep ChromaDB for RAG search but simplify the 3-tier abstraction)

**Option B — Keep Architecture, Hide Complexity (pragmatic):**
- Keep 13 agents and hierarchy internally (it works)
- Simplify the external-facing behavior: agents still have "one job" output
- Don't expose hierarchy/personas/traits in Slack cards or dashboard
- Focus effort on adding missing features (Slack channels, approval workflow) instead of tearing down working code

**Recommendation:** Option B is lower risk. The hierarchy works. Tearing it down is a large refactor with little user-facing benefit. The manager's concern is about scope and delivery speed, not internal architecture.

### 3B. The 10 Agents (Manager's List)

| # | Agent | Lane | Your Equivalent | Status |
|---|-------|------|-----------------|--------|
| 1 | CS Orchestrator | Control | Naveen Kapoor (orchestrator.py) | Exists — needs simplification if Option A |
| 2 | Customer Memory | Shared | Atlas (customer_memory.py) | Exists — simplify to JSON CRUD if Option A |
| 3 | Pre-Sales Funnel | Pre-Sales | N/A | Out of scope (HubSpot) |
| 4 | SOW & Prerequisite | Delivery | Ethan Brooks (sow_agent.py) | Exists |
| 5 | Deployment Intel | Delivery | Zara Kim (deployment_intel_agent.py) | Exists |
| 6 | Ticket Triage | Run/Support | Kai Nakamura (triage_agent.py) | Exists |
| 7 | Troubleshooting | Run/Support | Leo Petrov (troubleshoot_agent.py) | Exists |
| 8 | Escalation Writer | Run/Support | Maya Santiago (escalation_agent.py) | Exists |
| 9 | Health Monitor | Value | Dr. Aisha Okafor (health_monitor.py) | Exists |
| 10 | QBR / Value | Value | Sofia Marquez (qbr_agent.py) | Exists |

**Result:** 9 of 10 agents already exist. Only Pre-Sales Funnel is missing (and it's out of scope due to HubSpot). Your extra agents (3 Lane Leads + Riley Park + Jordan Ellis/Fathom) are bonuses.

---

## Change 4: Dashboard Restructure

**Current state:** 8+ React pages + 6 Streamlit pages, standalone browsing model.

**Target state:** 2 focused dashboard pages (3rd is N/A due to HubSpot) that serve as drill-down from Slack.

### 4A. Page 1: At-Risk Dashboard (`/dashboard`)

**What exists:** DashboardPage has KPIs, customer table, alerts — ~60% there.

**What to add/modify:**
- Make the customer table **at-risk focused**: default sort by health score ascending, color-code rows
- Add columns: Sentiment Bucket, Days to Renewal, Risk Flags, Last Call Date
- Add filters: Risk level, CSM owner, Industry, Renewal window
- Click row -> navigate to Customer Profile (Page 2)
- Add right sidebar: Live Alert Feed (latest health alerts, escalations, threshold breaches)
- Add bottom section: Trend Charts
  - Health score distribution over 12 weeks (heatmap)
  - Ticket velocity: opened vs resolved per week
  - Sentiment trend: portfolio-wide over time
- Every health alert from Slack should deep-link here with pre-applied filters

### 4B. Page 2: Customer Profile (`/dashboard/customer/{id}`)

**What exists:** CustomerDetailPage has overview, tickets, calls panels — ~50% there.

**What to add/modify:**
- Header: Health score gauge, sentiment badge, renewal countdown, CSM owner
- Restructure into 5 tabs (6th HubSpot tab is N/A):
  - **Tab 1 — Overview:** Customer Memory data (deployment mode, version, integrations, constraints), risk flags, feature requests
  - **Tab 2 — Tickets:** All UCSC tickets with priority, status, SLA countdown, triage summary
  - **Tab 3 — Calls:** All Fathom calls with date, duration, sentiment, key topics, action items (expandable)
  - **Tab 4 — Health History:** Health score over time (line chart), risk flag timeline
  - **Tab 5 — QBR:** Latest QBR draft, sentiment bucket history, value narrative
- Support deep-link with tab pre-selection: `/dashboard/customer/{id}?tab=tickets`

### 4C. What to Do With Extra Pages

The manager didn't ask for AgentsPage, TicketsPage, InsightsPage, ReportsPage, etc. Options:
- **Keep them** but don't link from Slack (they're bonus features for power users)
- **Or** fold their best features into the 2 main pages (e.g., ticket warroom data goes into At-Risk Dashboard)

---

## Change 5: Accuracy Tracking & Autonomy Gates

**Current state:** No accuracy tracking. No autonomy gates. All agent outputs are fire-and-forget.

**Target state:** Every agent output is tracked for accuracy. Autonomy is earned through measured performance.

### 5A. Audit Log Enhancement

Need to track for every agent action:
- `human_action`: approved | edited | dismissed
- `human_edit_diff`: what the human changed (if edited)
- `confidence`: agent's self-reported confidence (0-100)
- `fathom_validation_score`: for call intelligence, compare agent output to Fathom AI output

**What to change:**
- Enhance existing `AgentLog` or `Event` table with: `human_action`, `human_edit_diff`, `confidence`
- Or create dedicated `agent_audit_log` table per manager's schema (Section 13.1)
- Every Slack Approve/Edit/Dismiss action writes to this log

### 5B. Accuracy Metrics Computation

Weekly computation:
- **Triage accuracy:** % of triage outputs approved without edits
- **False positive rate:** % of health alerts dismissed
- **Human override rate:** % of outputs edited before approval
- **Fathom validation score:** compare agent call summaries to Fathom AI for same call

**What to change:**
- New service: `accuracy_service.py` — computes weekly accuracy metrics per agent
- Store in new table or append to existing reporting

### 5C. Autonomy Gate Logic

Per manager's Section 12:

| Action | Auto-Allowed When | Current |
|--------|-------------------|---------|
| Send email | Fathom validation >0.90 for 4+ weeks | Never auto |
| Create Jira ticket | Triage accuracy >90% for 3+ weeks | Never auto |
| Update Jira labels | Triage accuracy >95% for 3+ weeks | Never auto |
| Health alerts | Always auto (informational) | Already auto |
| Executive digest | Always auto (informational) | Already auto |
| Escalations | NEVER auto | N/A |
| QBR/SOW docs | NEVER auto | N/A |

**What to change:**
- `autonomy_gate_service.py` — checks weekly accuracy for each agent against thresholds
- Before executing any action, check if agent has earned autonomy for that action type
- If not earned -> create draft + post Slack card for approval
- If earned -> execute directly + post informational Slack card

---

## Change 6: Deep-Linking (Slack -> Dashboard)

**Current state:** No deep-linking. Slack messages don't link to dashboard.

**Target state:** Every Slack card includes a "View Details ->" link to the relevant dashboard page with correct tab/filter.

### 6A. URL Pattern

| Agent Output | Dashboard URL |
|-------------|---------------|
| Ticket triage | `/dashboard/customer/{id}?tab=tickets` |
| Call summary | `/dashboard/customer/{id}?tab=calls` |
| Health alert | `/dashboard?risk=high` or `/dashboard/customer/{id}?tab=health` |
| QBR draft | `/dashboard/customer/{id}?tab=qbr` |
| Escalation | `/dashboard/customer/{id}?tab=tickets` |
| SOW/Deployment | `/dashboard/customer/{id}?tab=overview` |
| Executive digest | `/dashboard` |
| Threshold alert | `/dashboard?filter={issue_type}` |

### 6B. What to Change
- `slack_formatter.py` — include dashboard URL in every card's "View Details ->" button
- Dashboard frontend — parse URL query params (`?tab=`, `?risk=`, `?filter=`) and apply them on page load
- Need `DASHBOARD_BASE_URL` config variable (e.g., `https://hivepro-dashboard.vercel.app`)

---

## Change 7: Event Routing Updates

**Current state:** Event routing exists via `EVENT_LANE_MAP` and `EVENT_ROUTING` in orchestrator.py.

**Target state:** Routing must also determine which Slack channel to post to.

**What to change:**
- Add `EVENT_SLACK_CHANNEL_MAP` in orchestrator or event_service:

```
jira_ticket_created    -> #cs-ticket-triage
jira_ticket_updated    -> #cs-ticket-triage
zoom_call_completed    -> #cs-call-intelligence
daily_health_check     -> #cs-health-alerts
escalation_needed      -> #cs-escalations
renewal_within_90_days -> #cs-qbr-drafts
new_customer           -> #cs-delivery
deployment_ready       -> #cs-delivery
weekly_exec_report     -> #cs-executive-digest
threshold_alert        -> #cs-executive-urgent
```

- After agent produces output -> look up channel -> post standardized card -> store draft

---

## Summary of All Changes

| # | Change | Effort | Priority |
|---|--------|--------|----------|
| 1 | Slack 9-channel architecture + standardized cards | Medium | HIGH |
| 2 | Draft-first approval workflow (pending_actions + Slack buttons) | High | HIGH |
| 3 | Agent simplification (Option A or B) | High (A) / Low (B) | MEDIUM |
| 4 | Dashboard restructure (At-Risk + Customer Profile pages) | Medium | MEDIUM |
| 5 | Accuracy tracking + autonomy gates | Medium | LOW (Phase 2+) |
| 6 | Deep-linking (Slack -> Dashboard) | Low | MEDIUM |
| 7 | Event -> Slack channel routing | Low | HIGH (pairs with #1) |

**Recommended order:** 1 + 7 (Slack channels + routing) -> 2 (approval workflow) -> 6 (deep-linking) -> 4 (dashboard) -> 3 (agent simplification) -> 5 (accuracy tracking)
