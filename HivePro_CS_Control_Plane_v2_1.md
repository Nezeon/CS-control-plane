**HivePro**

Virtual Customer Success System

Agentic CS Operating Model --- v2.1 (Revised)

*Slack + Dashboard Hybrid \| Strict Timelines \| HivePro-Specific*

Prepared for: Sarfaraz Kazi, Jeelan, Brian

Date: March 2026 \| Status: Working Draft v2.1

**1. Gap Analysis: Manager Architecture vs. Intern Document**

Key structural misalignments between the manager's architecture and the intern's document.

  -------------- ----------------------------------------------- --------------------------------------------- -------------------------------------------------------
  **Area**       **Manager's Intent**                            **Intern's Document**                         **Impact**

  Agent Count    10--12 max, tight                               13 with personas, traits, reflection engine   Over-engineered. Trim to 10.

  Hierarchy      3 lanes: Delivery, Run/Support, Value           4-tier hierarchy (Tiers 0--3)                 Wrong abstraction. Use lanes.

  Autonomy       Draft first, human approves, measure accuracy   Full autonomous pipeline                      Violates core principle.

  Data Sources   Jira + Fathom + telemetry                       Only Fathom + Jira. No HubSpot.               Kills Pre-Sales use case.

  Delivery       Not specified (operational)                     7-page cinematic frontend, orbital nav        Over-scoped. Need Slack + lightweight dashboard.

  Memory         Single Customer Memory JSON                     3-tier memory + ChromaDB                      Over-architected for Phase 1.

  Timeline       Phase 1 in 2--3 weeks                           9 phases, 19--30 days                         Too slow. We need 12 working days for Phase 1.

  Dashboard      Not addressed                                   Full SPA with 7 pages                         We need a focused 3-page dashboard linked from Slack.
  -------------- ----------------------------------------------- --------------------------------------------- -------------------------------------------------------

**1.1 Missing from Intern's Document (Jeelan Requirements)**

-   Pre-Sales: Demo-to-POC and POC-to-deal funnel analysis (requires HubSpot)

-   Post-Sales: At-risk customer identification, feature request prioritization, support ticket trends

-   QBRs: Customer bucketing by sentiment (happy/unhappy) with root-cause diagnosis

-   Executive Reporting: Weekly summaries with threshold alerting (5+ customers = same issue)

-   Slack + Dashboard Hybrid: Push notifications via Slack, deep-dive via linked dashboard

-   Data: Jira UCSC tickets specifically + HubSpot for LeadGen/demos/POCs/QBRs

**2. Refined System Architecture**

4-lane model with Slack as the push layer and a lightweight dashboard for drill-down. Every Slack card links to the relevant dashboard view.

**2.1 Architecture Diagram**

┌──────────────────────────────────┐

│ CS Orchestrator Agent │

│ (Routes events to lanes) │

└────────────────┬─────────────────┘

┌─────────────┬─────────┴───────┬─────────────┐

Pre-Sales Delivery Run/Support Value

(Funnel) (Onboarding) (Troubleshoot) (QBR/Health)

└─────────────┴────────┬────────┴─────────────┘

│

┌─────────┴─────────────────┐

│ Shared Services │

│ Customer Memory │

│ Executive Reporter │

│ Slack Bot + Dashboard │

└──────────────────────────┘

**2.2 Delivery Model: Slack + Dashboard Hybrid**

> *Slack is the PUSH layer. Dashboard is the PULL layer. Every Slack message links to the dashboard for drill-down. Nobody needs to proactively open the dashboard---Slack brings them there.*

How it works:

1.  Agent produces output (e.g., ticket triage, health alert, call summary)

2.  Slack bot posts a compact card to the relevant channel with key data + action buttons

3.  Each card includes a "View Details →" link that deep-links to the dashboard page for that specific customer/ticket/insight

4.  Dashboard shows the full picture: at-risk customer list, analytics charts, ticket history, call sentiment timeline

5.  Users interact in Slack for quick approvals (Approve/Edit/Dismiss) and open the dashboard only when they need the full context

**2.3 Design Principles**

6.  Draft-First: Every agent output is a DRAFT. Humans approve before any customer-facing action or Jira write.

7.  Slack-Push, Dashboard-Pull: Notifications push to Slack. Deep analysis lives in the dashboard. Slack links to dashboard.

8.  Event-Driven: Every workflow triggered by a discrete event. No polling.

9.  Customer Isolation: No cross-customer data leakage. Memory is per-customer.

10. Accuracy Before Autonomy: 4+ weeks of measured accuracy before any auto-send or auto-create.

11. Three Data Sources in Phase 1: Fathom (calls), Jira UCSC (tickets), HubSpot (deals/pipeline).

**3. Data Source Map**

  ------------- ----------------------------------------------------------------- ------------------------------------------ ------------------------------------------
  **Source**    **What It Provides**                                              **Ingestion**                              **Used By**

  Fathom        Call transcripts, speaker labels, summaries, action items         Webhook on call end OR pull every 6 hrs    Call Intelligence, QBR, Exec Reporter

  Jira (UCSC)   Tickets: priority, status, SLA, labels, comments, resolution      Webhook on create/update OR poll 15 min    Triage, Troubleshoot, Escalation, Health

  HubSpot       Deals pipeline, stages, contacts, close reasons, demo/POC dates   API pull daily + webhook on stage change   Pre-Sales Funnel, Exec Reporter, QBR
  ------------- ----------------------------------------------------------------- ------------------------------------------ ------------------------------------------

**4. Agent Specifications (10 Agents)**

10 agents organized by lane. No personas, no traits, no reflection engine. Each agent has one job.

  -------- -------------------- ------------- ---------------------------- ----------------------------- -------------------------
  **\#**   **Agent**            **Lane**      **Trigger**                  **Key Output**                **Dashboard Link**

  1        CS Orchestrator      Control       All events                   Routing decision              ---

  2        Customer Memory      Shared        Every agent R/W              Per-customer JSON             Customer Profile page

  3        Pre-Sales Funnel     Pre-Sales     deal_stage_changed, weekly   Funnel metrics, blockers      Pipeline Analytics page

  4        SOW & Prerequisite   Delivery      new_customer                 SOW checklist, timeline       Customer Profile page

  5        Deployment Intel     Delivery      deployment_ready             Validation report             Customer Profile page

  6        Ticket Triage        Run/Support   jira_ticket_created          Classification, email draft   Ticket Detail page

  7        Troubleshooting      Run/Support   bundle_uploaded              Root cause, confidence        Ticket Detail page

  8        Escalation Writer    Run/Support   escalation_needed            Engineering escalation doc    Ticket Detail page

  9        Health Monitor       Value         daily (8 AM)                 Scores, risk flags            At-Risk Dashboard

  10       QBR / Value          Value         quarterly/manual             Sentiment buckets, QBR doc    Customer Profile page
  -------- -------------------- ------------- ---------------------------- ----------------------------- -------------------------

**4.1 CS-Orchestrator Agent**

**Role:** Router. Classifies every inbound event and sends it to the correct lane agent.

**Events it handles:** jira_ticket_created, zoom_call_completed, deal_stage_changed, daily_health_check, support_bundle_uploaded, renewal_within_90_days, new_customer, manual_trigger.

**Output:** { event_id, classified_type, assigned_agent, priority, context_snapshot }

**Never:** Does analysis, writes to customer, executes tools. Coordinates only.

**4.2 Customer Memory Agent**

**Role:** Single source of truth per customer. Every agent reads before executing, writes results back.

{

\"customer_id\": \"string\",

\"company_name\": \"string\",

\"deployment_mode\": \"OVA\",

\"version\": \"string\",

\"integrations\": \[\"EDR\", \"SIEM\"\],

\"known_constraints\": \[\"Air-gapped\", \"Proxy\"\],

\"industry\": \"banking \| telco \| gov \| tech\",

\"tier\": \"enterprise \| mid-market \| smb\",

\"csm_owner\": \"string\",

\"renewal_date\": \"date\",

\"health_score\": \"0-100\",

\"sentiment_bucket\": \"happy \| neutral \| unhappy\",

\"open_tickets\": \[{ ticket_id, priority, status, age }\],

\"recent_calls\": \[{ call_id, date, sentiment, topics }\],

\"risk_flags\": \[\"delayed_renewal\", \"p0_open\"\],

\"feature_requests\": \[{ title, votes, source }\],

\"hubspot_deal_id\": \"string\",

\"hubspot_deal_stage\": \"string\"

}

**4.3 Pre-Sales Funnel Agent**

**Trigger:** deal_stage_changed from HubSpot, weekly scheduled pull.

**Inputs:** HubSpot pipeline data + Fathom demo/POC call transcripts.

**Outputs:** Conversion rates (Demo→POC, POC→Close), blocker analysis from close_reason + call themes, stalled deal alerts.

**Slack:** Posts to #cs-presales-funnel with link to Pipeline Analytics dashboard page.

**Never:** Modifies HubSpot, contacts prospects.

**4.4 SOW & Prerequisite Agent**

**Trigger:** new_customer event.

**Outputs:** SOW document draft, infra checklist (CPU/RAM/disk/ports/DNS/NTP), security checklist, responsibility matrix, timeline.

**Slack:** Posts to #cs-delivery with link to Customer Profile on dashboard.

**4.5 Deployment Intelligence Agent**

**Trigger:** deployment_ready (manual trigger during onboarding).

**Reads:** hp_health_snapshot, services_status, connector_status, first scan results, RBAC/SSO config.

**Outputs:** Validation report. If failure → routes to Troubleshooting Agent.

**4.6 Ticket Triage Agent**

**Trigger:** jira_ticket_created (UCSC project only).

**Steps:** 1) Classify (Deployment/Scan/Connector/Performance/UI/Integration). 2) Assign severity. 3) Suggest diagnostic. 4) Check duplicates. 5) Draft customer email.

**Output:** { label, severity, root_cause_category, required_script, similar_tickets\[\], email_draft }

**Slack:** Posts to #cs-ticket-triage with Approve/Edit/Dismiss + link to Ticket Detail on dashboard.

**Never:** Auto-responds, auto-labels without human approval.

**4.7 Troubleshooting Agent**

**Trigger:** support_bundle_uploaded event.

**Reads:** hp_health_snapshot, services_status, scan_job_status, connectors_status, network_probe.

**Output:** { probable_root_cause, confidence_score (0--100), next_step, escalation_flag }

**Rule:** If confidence \< 70% → auto-routes to Escalation Agent.

**4.8 Escalation & Engineering Summary Agent**

**Trigger:** severity = High, RCA needed, or confidence \< 70%.

**Output:** Escalation doc: customer context, technical summary, evidence, reproduction steps, timeline, customer update draft.

**Slack:** Posts to #cs-escalations with Approve button + dashboard link. ALWAYS requires human approval.

**4.9 Health Monitoring Agent**

**Trigger:** daily_health_check (scheduled, 8 AM daily).

**Checks:** Ticket severity load (open P0/P1 \>5 days = flag), call sentiment trend (2+ negative in 14 days = flag), renewal proximity (\<90 days + risk flags = elevated), historical health trend (drop \>15 points in 7 days = flag), open alert load.

**Output:** Per-customer health score (0--100), risk_flags\[\], DRAFT proactive Jira tickets.

**Threshold:** 5+ customers with same issue in 7 days → executive urgent alert.

**Slack:** Daily summary to #cs-health-alerts + link to At-Risk Dashboard. Threshold breaches go to #cs-executive-urgent.

**Never:** Auto-creates Jira tickets. Drafts only.

**4.10 QBR / Value Narrative Agent**

**Trigger:** Manual request, quarterly schedule, renewal_within_90_days.

**Inputs:** Customer Memory + Jira UCSC (90 days) + Fathom sentiment (90 days) + HubSpot deal data.

**Outputs:** Sentiment bucket (Happy/Neutral/Unhappy) with evidence, root cause of dissatisfaction, exposure trends, risk reduction narrative, executive summary with renewal recommendation.

**Slack:** Posts QBR draft to #cs-qbr-drafts with link to Customer Profile on dashboard.

**5. Dashboard Architecture (3 Pages)**

> *The dashboard is NOT a standalone portal. It is the drill-down destination that Slack links open. Users don't browse to it---Slack brings them there. This avoids the ProBee problem of building a portal nobody visits.*

**5.1 Page 1: At-Risk Dashboard (Home)**

**URL:** /dashboard

**Purpose:** The single-pane view of portfolio health. This is what leadership cares about most.

**Layout**

-   Top Row: 4 KPI cards --- Total Customers, At-Risk Count, Open P0/P1 Tickets, Avg Health Score

-   Main Section: At-Risk Customer Table (filterable, sortable)

    -   Columns: Customer Name, Health Score (color-coded), Sentiment Bucket, Open Tickets, Days to Renewal, Risk Flags, Last Call Date

    -   Click any row → opens Customer Profile (Page 2)

    -   Filter by: Risk level, CSM owner, Industry, Renewal window

-   Right Sidebar: Live Alert Feed (latest health alerts, escalations, threshold breaches)

-   Bottom Section: Trend Charts

    -   Health score distribution over 12 weeks (heatmap)

    -   Ticket velocity: opened vs resolved per week

    -   Sentiment trend: portfolio-wide positive/neutral/negative over time

**Slack Integration:** Every Slack health alert links directly to this page, pre-filtered to the relevant customer or risk category.

**5.2 Page 2: Customer Profile (Deep-Dive)**

**URL:** /dashboard/customer/{customer_id}

**Purpose:** Everything about one customer in one place. This is where CSMs go from Slack links.

**Layout**

-   Header: Customer name, health score gauge, sentiment badge, renewal countdown, CSM owner

-   Tab 1 --- Overview: Customer Memory data (deployment mode, version, integrations, constraints), risk flags, feature requests

-   Tab 2 --- Tickets: All UCSC tickets for this customer (table with priority, status, SLA countdown, triage summary). Click ticket → opens Ticket Detail.

-   Tab 3 --- Calls: All Fathom calls (date, duration, sentiment, key topics, action items). Each call expandable to show full summary + action items.

-   Tab 4 --- Health History: Health score over time (line chart), risk flag timeline, connector/scan status history

-   Tab 5 --- QBR: Latest QBR draft, sentiment bucket history, value narrative, renewal recommendation

-   Tab 6 --- HubSpot: Deal stage, pipeline position, POC/demo dates, associated contacts

**Slack Integration:** Slack cards for call summaries, ticket triage, QBR drafts, and health alerts all link to this page with the relevant tab pre-selected.

**5.3 Page 3: Pipeline Analytics (Pre-Sales)**

**URL:** /dashboard/pipeline

**Purpose:** Pre-sales funnel visibility for sales leadership.

**Layout**

-   Funnel Visualization: Deal count and value at each stage (LeadGen → Demo → POC → Close)

-   Conversion Rates: Stage-to-stage conversion percentages with week-over-week change

-   Stalled Deals Table: Deals stuck \>30 days in any stage (name, owner, days stalled, last activity)

-   Blocker Analysis: Top reasons for Closed Lost (from HubSpot close_reason + Fathom call themes)

-   Time-in-Stage Chart: Average days spent in each stage, trend over last 12 weeks

**Slack Integration:** Weekly funnel summary in #cs-presales-funnel links to this page. Stalled deal alerts link directly to the stalled deals table.

**6. Slack Architecture**

**6.1 Channel Map**

  ----------------------- ------------------------------------------------------------- ------------------------------- ---------------------------------
  **Channel**             **Content**                                                   **Subscribers**                 **Dashboard Link**

  #cs-executive-digest    Weekly executive summary                                      Sarfaraz, Jeelan, Brian         At-Risk Dashboard (filtered)

  #cs-executive-urgent    Threshold alerts (5+ same issue, health crash, SLA cascade)   Sarfaraz, Jeelan, Brian         At-Risk Dashboard (filtered)

  #cs-call-intelligence   Post-call summaries + action items + sentiment                All CS Managers                 Customer Profile → Calls tab

  #cs-ticket-triage       New ticket classifications + suggested actions                CS Engineers, Support Lead      Customer Profile → Tickets tab

  #cs-health-alerts       Daily health check results + risk flags                       CS Managers, Directors          At-Risk Dashboard

  #cs-presales-funnel     Pipeline analytics + stalled deal alerts                      Sales Leadership                Pipeline Analytics page

  #cs-qbr-drafts          QBR document drafts for review                                CS Managers                     Customer Profile → QBR tab

  #cs-escalations         Engineering escalation documents for approval                 CS Managers, Engineering Lead   Customer Profile → Tickets tab

  #cs-delivery            SOW drafts, deployment status                                 CS Managers, Onboarding Lead    Customer Profile → Overview tab
  ----------------------- ------------------------------------------------------------- ------------------------------- ---------------------------------

**6.2 Slack Card Format**

Every Slack card follows this format for consistency:

┌────────────────────────────────────────────────┐

│ \[Agent\] --- \[Event Type\] │

│ Customer: \[Name\] \| Health: \[XX\] │

│ Priority: \[P0/P1/P2\] │

│────────────────────────────────────────────────│

│ Summary: \[2--3 sentence insight\] │

│ Action Required: \[specific next step\] │

│ │

│ \[✅ Approve\] \[✏️ Edit\] \[❌ Dismiss\] │

│ │

│ View Details → \[Dashboard Deep-Link\] │

└────────────────────────────────────────────────┘

**Approve:** Triggers the action (create Jira ticket, send email, etc.)

**Edit:** Opens Slack thread for human modification before action.

**Dismiss:** Logs rejection for accuracy tracking. No action taken.

**View Details:** Deep-links to the relevant dashboard page (customer profile, ticket detail, pipeline analytics).

**7. Executive Reporting**

**7.1 Weekly Executive Summary (Monday 9 AM)**

Delivered to #cs-executive-digest. Links to At-Risk Dashboard for drill-down.

  -------------------- ----------------------------------------------------------------------- ------------------------------
  **Section**          **Content**                                                             **Dashboard Link**

  Portfolio Health     Health distribution (healthy/at-risk/critical), week-over-week delta    At-Risk Dashboard

  Pre-Sales Pipeline   Funnel metrics, conversion rates, stalled deals, top blockers           Pipeline Analytics

  Support Velocity     Tickets opened/resolved, avg resolution, SLA breaches, top categories   At-Risk Dashboard → Tickets

  Sentiment Trends     Who moved happy→unhappy and why (linked to calls/tickets)               Customer Profile → Calls

  Risk Alerts          Customers needing immediate attention, pending escalations              At-Risk Dashboard (filtered)

  Feature Demand       Top features ranked by customer count + ARR impact                      At-Risk Dashboard

  Agent Accuracy       Fathom comparison scores, human override rate, false positive rate      --- (internal metric)
  -------------------- ----------------------------------------------------------------------- ------------------------------

**7.2 Threshold Alerts (Real-Time)**

These fire immediately to #cs-executive-urgent. Do NOT wait for weekly digest.

  ---------------- ----------------------------------------------------- --------------------------------------
  **Threshold**    **Condition**                                         **Dashboard Link**

  Issue Cluster    5+ customers report same issue category in 7 days     At-Risk Dashboard filtered by issue

  Health Crash     Enterprise customer health drops \>20 pts in a week   Customer Profile → Health History

  SLA Cascade      3+ P0/P1 tickets breach SLA in same week              At-Risk Dashboard → Tickets

  Churn Signal     Renewal \<60 days + unhappy sentiment + open P0       Customer Profile (specific customer)

  Pipeline Stall   5+ deals stuck in same stage \>30 days                Pipeline Analytics → Stalled Deals
  ---------------- ----------------------------------------------------- --------------------------------------

**8. Core Workflow Flows**

**8.1 Jira Ticket Intake**

12. Jira webhook: jira_ticket_created (UCSC)

13. Orchestrator → Ticket Triage Agent

14. Triage reads Customer Memory → classifies, assigns severity, checks duplicates

15. Posts triage card to #cs-ticket-triage Slack with \[View Details → /dashboard/customer/X?tab=tickets\]

16. Human clicks Approve → Jira labels updated, customer email sent

17. Customer Memory updated

**8.2 Post-Call Automation**

18. Fathom webhook: zoom_call_completed

19. Orchestrator fetches transcript from Fathom API

20. Call Intelligence extracts: decisions, action items, risks, sentiment

21. Validates against Fathom AI output (accuracy tracking)

22. Posts summary to #cs-call-intelligence with \[View Details → /dashboard/customer/X?tab=calls\]

23. Customer Memory updated: recent_calls, sentiment_bucket, risk_flags

**8.3 Health Monitoring**

24. 8 AM daily trigger

25. Health Monitor checks all customers against criteria

26. Computes health scores, identifies risk flags

27. Posts daily summary to #cs-health-alerts with \[View Dashboard → /dashboard\]

28. Cross-customer pattern check: 5+ same issue = #cs-executive-urgent

29. Drafts proactive Jira tickets (human approval in Slack required)

**8.4 Pre-Sales Funnel**

30. Weekly pull from HubSpot (Sunday 11 PM) + deal_stage_changed webhook

31. Pre-Sales Agent computes conversion rates, stalled deals, blocker themes

32. Cross-references with Fathom demo/POC call transcripts

33. Posts to #cs-presales-funnel with \[View Pipeline → /dashboard/pipeline\]

34. Feeds into weekly executive summary

**8.5 Escalation to Engineering**

35. Troubleshooting Agent confidence \< 70% OR P0 open \> 4 hours

36. Escalation Agent compiles: context, technical summary, evidence, repro steps

37. Posts to #cs-escalations with Approve button + \[View Details → /dashboard/customer/X?tab=tickets\]

38. CS Manager approves → doc attached to Jira, engineering notified

**9. Event-Driven Routing Model**

  ------------------------- --------------------- --------------------- ----------------------- ----------------------
  **Event**                 **Source**            **Agent**             **Slack Channel**       **Dashboard Link**

  jira_ticket_created       Jira UCSC webhook     Ticket Triage         #cs-ticket-triage       Customer Profile

  jira_ticket_updated       Jira UCSC webhook     Triage/Troubleshoot   #cs-ticket-triage       Customer Profile

  support_bundle_uploaded   Manual / Jira         Troubleshooting       #cs-ticket-triage       Customer Profile

  zoom_call_completed       Fathom webhook        Call Intelligence     #cs-call-intelligence   Customer Profile

  deal_stage_changed        HubSpot webhook       Pre-Sales Funnel      #cs-presales-funnel     Pipeline Analytics

  daily_health_check        Scheduled 8 AM        Health Monitor        #cs-health-alerts       At-Risk Dashboard

  renewal_within_90_days    Scheduled scan        QBR + Health          #cs-qbr-drafts          Customer Profile

  new_customer              HubSpot Closed Won    SOW & Prereq          #cs-delivery            Customer Profile

  deployment_ready          Manual trigger        Deployment Intel      #cs-delivery            Customer Profile

  escalation_needed         Troubleshoot output   Escalation Writer     #cs-escalations         Customer Profile

  weekly_exec_report        Scheduled Mon 9 AM    Exec Reporter         #cs-executive-digest    At-Risk Dashboard
  ------------------------- --------------------- --------------------- ----------------------- ----------------------

**10. Use Case Mapping (Jeelan Requirements)**

**10.1 Pre-Sales: Funnel Analysis**

  ------------------------ ---------------------------------------------------------------------------------------- -----------------------------------------------
  **Requirement**          **Solution**                                                                             **Visible In**

  Demo-to-POC conversion   Pre-Sales Agent: HubSpot stage history + Fathom demo transcript themes                   Pipeline Analytics page + #cs-presales-funnel

  POC-to-deal conversion   Pre-Sales Agent: POC Complete → Closed Won rate + close_reason analysis                  Pipeline Analytics page

  Conversion blockers      NLP on Fathom demo/POC calls + HubSpot close_reason. Ranked by frequency + deal value.   Pipeline Analytics → Blocker Analysis section
  ------------------------ ---------------------------------------------------------------------------------------- -----------------------------------------------

**10.2 Post-Sales: Risk & Feature Analysis**

  -------------------------- --------------------------------------------------------------------------------------------------------------------- --------------------------------------
  **Requirement**            **Solution**                                                                                                          **Visible In**

  At-risk customers          Health Monitor daily: composite score from ticket severity, call sentiment, renewal proximity, health trend, open alerts. \<60 = at-risk.   At-Risk Dashboard (main view)

  Feature request priority   Triage Agent tags feature-requests. QBR Agent aggregates by customer count + ARR impact.                              At-Risk Dashboard + Customer Profile

  Ticket trends              Triage classification aggregated weekly. Top categories, resolution time, SLA breaches, repeat patterns.              At-Risk Dashboard → Trend Charts
  -------------------------- --------------------------------------------------------------------------------------------------------------------- --------------------------------------

**10.3 QBRs: Sentiment Bucketing**

  ------------------------------- ----------------------------------------------------------------------------------------------------------------- ---------------------------------------------------
  **Requirement**                 **Solution**                                                                                                      **Visible In**

  Bucket by sentiment             QBR Agent: Happy (\>70 health + positive calls), Neutral (50--70), Unhappy (\<50 or neg sentiment + open P0/P1)   At-Risk Dashboard (filterable) + Customer Profile

  Root cause of dissatisfaction   Cross-reference Jira UCSC categories with Fathom call themes for unhappy customers. Ranked list.                  Customer Profile → QBR tab
  ------------------------------- ----------------------------------------------------------------------------------------------------------------- ---------------------------------------------------

**11. Implementation Roadmap (Strict Timelines)**

> *Hard deadlines. No buffer. Each phase has daily deliverables and a gate review before advancing.*

**Phase 1: Core Pipeline + Slack (12 Working Days)**

**Goal:** 3 data integrations working, 4 core agents live, Slack delivery active, basic dashboard deployed.

**Gate:** Can process a real Fathom call AND a real UCSC ticket end-to-end through Slack with human approval.

  --------- ----------------------------------------------------------------------------------------------------------------------------------- ---------------- ------------------------------------------------------------------------
  **Day**   **Deliverable**                                                                                                                     **Owner**        **Done When**

  Day 1     Project scaffold: FastAPI backend, DB schema (accounts, tickets, insights, events, audit_log), environment config, Docker Compose   Backend Dev      Backend runs, DB migrated, health endpoint returns 200

  Day 2     Customer Memory Agent: JSON store per customer, CRUD API, seed script from existing customer list                                   Backend Dev      Can create/read/update customer memory via API

  Day 3     Fathom integration: webhook receiver, transcript fetcher, raw storage. Test with 1 real recording.                                  Backend Dev      Transcript stored in DB from a real Fathom webhook

  Day 4     Call Intelligence pipeline: transcript → summary + action items + sentiment extraction. Write to Customer Memory.                   AI/Agent Dev     Process 1 real transcript, output matches expected format

  Day 5     Jira UCSC integration: webhook receiver for ticket create/update, ticket normalizer, storage                                        Backend Dev      Real UCSC ticket stored in DB from Jira webhook

  Day 6     Ticket Triage Agent: classify, severity, suggest diagnostic, check duplicates, draft email                                          AI/Agent Dev     Triage 3 real tickets, output reviewed by CS Engineer

  Day 7     CS Orchestrator: event classifier, routing logic for all Phase 1 events                                                             AI/Agent Dev     Route jira_ticket_created and zoom_call_completed correctly

  Day 8     Slack bot: channel creation, card posting with Approve/Edit/Dismiss buttons, webhook handlers                                       Full-Stack Dev   Post a card to #cs-ticket-triage, click Approve, action executes

  Day 9     Wire agents to Slack: Triage → #cs-ticket-triage, Call Intel → #cs-call-intelligence. Deep-link URLs in cards.                      Full-Stack Dev   End-to-end: Jira ticket → triage → Slack card → approve → Jira updated

  Day 10    Dashboard: At-Risk Dashboard page (Page 1). Customer table, health scores, KPI cards. React + TypeScript.                           Frontend Dev     Dashboard loads, shows real customer data from API

  Day 11    Dashboard: Customer Profile page (Page 2). Tabs for overview, tickets, calls. Linked from Slack cards.                              Frontend Dev     Click Slack link → lands on correct customer profile with correct tab

  Day 12    Integration test: process 5 real tickets + 3 real calls end-to-end. Fix bugs. Gate review with Sarfaraz.                            All              5 tickets + 3 calls processed. Sarfaraz approves Phase 1 complete.
  --------- ----------------------------------------------------------------------------------------------------------------------------------- ---------------- ------------------------------------------------------------------------

**Phase 2: Expand + Health + Pre-Sales (10 Working Days)**

**Goal:** Health monitoring, troubleshooting, escalation, pre-sales funnel, executive reporting all live.

**Gate:** Weekly executive digest generates correctly. At-Risk Dashboard shows real health scores. HubSpot pipeline visible.

  --------- ----------------------------------------------------------------------------------------------------------------- ---------------- -------------------------------------------------------------------------
  **Day**   **Deliverable**                                                                                                   **Owner**        **Done When**

  Day 13    Troubleshooting Agent: bundle parser, diagnostic analysis, confidence scoring                                     AI/Agent Dev     Parse 1 real bundle, root cause matches engineer assessment

  Day 14    Escalation Agent: compile context + evidence + repro steps. Wire to #cs-escalations Slack.                        AI/Agent Dev     Escalation doc reviewed by engineering, confirmed useful

  Day 15    Health Monitoring Agent: daily scan logic, scoring formula, risk flag detection                                   AI/Agent Dev     Scores computed for all customers. Manual verification matches.

  Day 16    Health → Slack: Daily digest to #cs-health-alerts. Threshold alerting to #cs-executive-urgent. Dashboard links.   Full-Stack Dev   8 AM health summary posts to Slack. Threshold alert fires on test data.

  Day 17    HubSpot integration: API connector, deal sync, stage change webhook, storage                                      Backend Dev      Real HubSpot deals visible in DB. Stage change triggers event.

  Day 18    Pre-Sales Funnel Agent: conversion calculations, blocker analysis, stalled deal detection                         AI/Agent Dev     Funnel report matches manual HubSpot analysis within 10%

  Day 19    Dashboard: Pipeline Analytics page (Page 3). Funnel chart, stalled deals, blockers.                               Frontend Dev     Pipeline page loads with real HubSpot data

  Day 20    Executive Reporter pipeline: aggregate all agent outputs into weekly digest format. Wire to Slack.                AI/Agent Dev     First weekly executive digest generated and posted to Slack

  Day 21    Fathom validation: compare agent output to Fathom AI for same queries. Track in audit log.                        AI/Agent Dev     Validation scores computed for last 10 calls. Score \> 0.80.

  Day 22    Integration test: 1 full week of real data. Fix bugs. Gate review.                                                All              All agents running. Dashboard live. Sarfaraz approves Phase 2.
  --------- ----------------------------------------------------------------------------------------------------------------- ---------------- -------------------------------------------------------------------------

**Phase 3: Autonomy + QBR + SOW (8 Working Days)**

**Goal:** QBR generation, SOW automation, selective autonomy based on Phase 1--2 accuracy data.

**Gate:** QBR sentiment buckets match CSM intuition for 80%+ customers. Auto-actions gated by accuracy metrics.

  --------- ----------------------------------------------------------------------------------------------------------------------------------- ---------------- ----------------------------------------------------------------------------
  **Day**   **Deliverable**                                                                                                                     **Owner**        **Done When**

  Day 23    QBR Agent: sentiment bucketing, root cause analysis, value narrative generation                                                     AI/Agent Dev     QBR for 3 customers. CSMs confirm sentiment buckets are correct.

  Day 24    QBR → Dashboard: Customer Profile QBR tab populated. QBR draft posted to #cs-qbr-drafts.                                            Full-Stack Dev   QBR visible in dashboard and Slack. Links work end-to-end.

  Day 25    SOW & Prerequisite Agent: template-based SOW generation, checklist logic                                                            AI/Agent Dev     SOW generated for 1 real new customer. CS Manager confirms quality.

  Day 26    Deployment Intelligence Agent: validation checks, failure routing                                                                   AI/Agent Dev     Validation report generated for 1 real deployment.

  Day 27    Accuracy review: analyze 4 weeks of data. Compute: triage accuracy, false positive rate, human override rate.                       AI/Agent Dev     Accuracy report generated. Identify which agents qualify for auto-actions.

  Day 28    Conditional autonomy: IF triage accuracy \>90% → enable auto-label in Jira. IF validation \>0.90 → enable auto-send recap emails.   All              Auto-actions enabled only for agents that meet accuracy gates.

  Day 29    Dashboard polish: responsive design, loading states, error handling, auth                                                           Frontend Dev     Dashboard works on desktop/tablet. Auth restricts to CS team.

  Day 30    Final integration test. Documentation. Handoff. Production deployment.                                                              All              System running in production. All channels active. Dashboard live.
  --------- ----------------------------------------------------------------------------------------------------------------------------------- ---------------- ----------------------------------------------------------------------------

**12. Human Approval Checkpoints & Autonomy Gates**

> *No agent gets autonomous until it earns it through measured accuracy. This table defines exactly when each action can be auto-executed.*

  --------------------------- ---------------------------- ---------------------------------------- ------------------------
  **Action**                  **Phase 1--2**               **Auto-Allowed When**                    **Never Auto**

  Send email to customer      DRAFT only, Slack approval   Fathom validation \> 0.90 for 4+ weeks   

  Create Jira ticket          DRAFT only, Slack approval   Triage accuracy \> 90% for 3+ weeks      

  Update Jira labels          DRAFT only, Slack approval   Triage accuracy \> 95% for 3+ weeks      

  Escalation to engineering   ---                          ---                                      ALWAYS human approved

  QBR document                DRAFT only                   ---                                      ALWAYS reviewed by CSM

  SOW document                DRAFT only                   ---                                      ALWAYS reviewed by CSM

  Health alert to Slack       Auto (informational)         Always auto from Day 1                   

  Executive digest            Auto (informational)         Always auto from Day 1                   

  Modify customer data        ---                          ---                                      ALWAYS human approved

  Delete anything             ---                          ---                                      ALWAYS human approved
  --------------------------- ---------------------------- ---------------------------------------- ------------------------

**13. Audit Logging & Security**

**13.1 Audit Log Schema**

{

\"log_id\": \"uuid\",

\"timestamp\": \"ISO-8601\",

\"agent\": \"ticket_triage\",

\"event_id\": \"evt_xxx\",

\"customer_id\": \"cust_xxx\",

\"action\": \"classify_ticket\",

\"input_summary\": \"UCSC-1234: Connector failure\",

\"output_summary\": \"Classified: connector_failure, P1\",

\"confidence\": 0.87,

\"human_action\": \"approved \| edited \| dismissed\",

\"human_edit_diff\": \"changed priority P1 -\> P0\",

\"dashboard_url\": \"/dashboard/customer/cust_xxx?tab=tickets\"

}

The human_edit_diff field creates the training signal for accuracy measurement and prompt improvement.

**13.2 Security Rules**

-   Customer data isolation: every query scoped to customer_id. No cross-customer access.

-   API keys: Fathom, Jira, HubSpot keys rotated every 90 days. Stored in secret manager.

-   Anthropic API: customer data never persists beyond the execution window.

-   Slack: bot tokens per-workspace. Channels restricted to approved members.

-   Dashboard: auth required. Only CS team members. No public URLs.

-   Executive reports: aggregate metrics only. No individual customer data in cross-customer views.

**14. Tech Stack**

  -------------- ---------------------------------------------------- -------------------------------------
  **Layer**      **Technology**                                       **Purpose**

  Backend        Python 3.11+ / FastAPI                               API server, agent orchestration

  Database       PostgreSQL (prod) / SQLite (dev)                     Structured data storage

  AI             Anthropic Claude Sonnet (claude-sonnet-4-20250514)   All agent LLM calls

  Slack          Slack Bolt SDK (Python)                              Bot, interactive messages, webhooks

  Frontend       React 18 + TypeScript + Vite                         Dashboard SPA

  Charts         Recharts + D3.js                                     Health heatmap, funnel, trends

  State          Zustand                                              Client-side state management

  Styling        Tailwind CSS                                         Dashboard UI styling

  Infra          Docker + Docker Compose                              Containerization

  CI/CD          GitHub Actions                                       Test, build, deploy

  Integrations   Fathom API, Jira REST API, HubSpot API               Data ingestion
  -------------- ---------------------------------------------------- -------------------------------------

**End of Document**

30 working days. 3 phases. 10 agents. 3 dashboard pages. 9 Slack channels. Slack pushes, dashboard pulls. Every agent earns autonomy through measured accuracy.
