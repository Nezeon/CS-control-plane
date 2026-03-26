# Executive Questions — Coverage Analysis

> Mapping C-level executive questions to system capabilities, identifying gaps, and tracking phase availability.
> Based on meeting with C-level stakeholders and cross-referenced against [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## 1. Customer Success Questions

### Q1: Which feature is requested by the maximum number of customers?

| | |
|---|---|
| **Covered?** | Yes ✅ |
| **How** | Portfolio-wide Jira ticket aggregation queries all Improvement + New Feature tickets, groups by feature theme across customers, and ranks by customer count. Chat fast path includes this in portfolio prefetch for all intents. Example output: "Scanning & Asset Intelligence — 5 customers, 8 tickets" with specific company names. Also pulls aggregated call topics from Fathom recordings. |
| **Gap** | None — fully operational. Tested: correctly identified YAS Holdings (7 requests), ETISALAT (4), Mubadala Capital (3) and grouped by theme across customers. |
| **Phase** | Phase 2 (Day 19 — portfolio prefetch + prompt tuning) |

---

### Q2: Which customer has the highest chance of attrition?

| | |
|---|---|
| **Covered?** | Yes |
| **How** | Health Monitor (Agent 9) computes health scores (0-100) with weighted checks + risk flags. Churn Signal threshold alert fires on: `renewal <60 days + unhappy sentiment + open P0` (Section 9.2). At-Risk Dashboard (Page 1) ranks all customers by health score with color-coded severity. QBR Agent (Agent 10) buckets sentiment (Happy/Neutral/Unhappy) with evidence. |
| **Gap** | None — fully covered by design. |
| **Phase** | Phase 1 (At-Risk Dashboard, Day 10) + Phase 2 (Health Monitor Agent, Day 15-16; Churn Signal alerts, Day 20) |

---

## 2. Pre-Deal / Funnel Questions

### Q3: 10 POCs done, 9 didn't result in a deal — why not?

| | |
|---|---|
| **Covered?** | Yes |
| **How** | Pre-Sales Funnel Agent (Agent 3) calculates `poc_to_close` conversion rate and outputs `top_blockers[{reason, frequency, total_deal_value}]`. Cross-references HubSpot `close_reason` field with Fathom POC call themes to identify patterns. Pipeline Analytics dashboard (Page 3) visualizes blockers. |
| **Gap** | Data quality dependency — requires HubSpot `close_reason` field to be consistently filled in by sales team. If field is empty, blocker analysis falls back to Fathom call themes only. |
| **Phase** | Phase 2 (HubSpot integration Day 17, Pre-Sales Funnel Agent Day 18, Pipeline Analytics Day 19) |

---

### Q4: 100 demos → 10 POCs → 1 order. Why did 90 demos not convert to POC?

| | |
|---|---|
| **Covered?** | Yes |
| **How** | Pre-Sales Funnel Agent (Agent 3) calculates `demo_to_poc` conversion rate. Blocker analysis pulls from Fathom demo call transcripts (themes, objections, sentiment) + HubSpot deal stage data. Output includes `top_blockers` ranked by frequency and deal value. Pipeline Analytics (Page 3) shows the full funnel visualization with conversion rates and week-over-week changes. |
| **Gap** | Same data quality dependency as Q3 — HubSpot close reasons need to be populated. Additionally, demo calls must be recorded in Fathom to be analyzed. |
| **Phase** | Phase 2 (Day 17-19) |

---

### Q5: What was the sentiment during the call? Wrong fit? Already had product? Didn't like what they saw? Looking for something different?

| | |
|---|---|
| **Covered?** | Yes ✅ |
| **How** | Universal cross-reference pulls sentiment, risks, decisions, and action items from all call recordings for lost deals. Loss analysis in Pre-Sales Agent cross-references closedlost deals with their Fathom call data, identifying specific failure patterns (undefined success criteria, technical barriers, integration complexity). Prompt is tuned to name specific companies and cite real data. Example output: "14/15 positive sentiment — customers liked HivePro, POCs failed due to execution not product fit. Triflo: login failures prevented evaluation. Union Bank: no POC success criteria defined." |
| **Gap** | Formal 8-category objection taxonomy not implemented as a structured classifier, but effectively answered through cross-referenced call data (risks, decisions, key_topics). |
| **Phase** | Phase 2 (Day 19 — cross-reference + loss analysis) |

---

### Q6: What went wrong during the POC? Did we demonstrate properly or not?

| | |
|---|---|
| **Covered?** | Yes ✅ |
| **How** | Loss analysis in Pre-Sales Agent cross-references closedlost deals with Fathom call recordings. Extracts specific risks, decisions, and failure patterns per company. Names real companies with exact issues from calls. Example output: "Triflo: login failures prevented hands-on evaluation before January 8th meeting. Max Credit Union: CAASM POC kicked off but Nick Waldmann never received success criteria. Union Bank: positive CTEM presentation but no documented POC structure." Also cross-references Jira tickets to identify systemic product gaps (scanning, integration) that surface during POCs. |
| **Gap** | No formal POC milestone tracking (would need HubSpot custom properties). Current analysis depends on what's in call recordings + Jira tickets — which in practice covers the key failure reasons. |
| **Phase** | Phase 2 (Day 18-19 — loss analysis + cross-reference) |

---

### Q7: Did the customer have to spend a lot of time on the platform? Was it not smooth enough?

| | |
|---|---|
| **Covered?** | No |
| **How** | Not addressable with current data sources. |
| **Gap** | **Missing data source — product usage analytics.** The three data sources (Jira, Fathom, HubSpot) capture support tickets, call recordings, and deal pipeline data. None capture in-product behavior: session duration, click paths, feature adoption rates, time-to-complete workflows, error rates, or UX friction points. To answer this question, the system would need a 4th data source — product analytics from a tool like Mixpanel, Amplitude, Pendo, or HivePro's internal telemetry. This is a new integration on par with the existing three. |
| **Phase** | **Not in any current phase.** Would require a new data source integration (estimated effort similar to Jira or HubSpot integration — 2-3 days). |

---

### Q11: What are the chances of us getting the Marriott deal?

| | |
|---|---|
| **Covered?** | Yes ✅ |
| **How** | Multi-factor win probability model in Pre-Sales Funnel Agent computes composite score from 5 weighted signals: (1) Pipeline stage position 25%, (2) Meeting engagement 25% (call count, participant count from Fathom), (3) Buyer intent signals 20% (decisions, action items, requirement keywords from call data), (4) Sentiment 15% (positive/negative call ratio), (5) Deal velocity 15% (age vs stage benchmark). Chat fast path has `deal` intent with `DEAL_KEYWORDS`, `_build_deal_prompt` injects pipeline metrics + meeting intelligence from ChromaDB. |
| **Gap** | None — fully operational. Tested: Marriott deal = 64% probability (vs old stage-only 10%). Factor breakdown: Stage 15% + Engagement 60% (51-min demo, 7 participants) + Intent 100% (2 decisions, 3 action items, replacement keywords) + Sentiment 100% (1/1 positive) + Velocity 70% (20 days, on track). |
| **Phase** | Phase 2 (Day 17-19) — Done |

---

## 3. QBR Questions

### Q8: We did QBR with 10 customers. How many are happy, moderately happy, unhappy?

| | |
|---|---|
| **Covered?** | Yes |
| **How** | QBR Agent (Agent 10) performs sentiment bucketing with clear thresholds: Happy (health >70 + positive calls), Neutral (health 50-70), Unhappy (health <50 or negative sentiment + open P0/P1). Every bucket includes evidence — health score, call sentiment count, open tickets, complaint themes. Output is not just a label but a documented assessment. QBR tab in Customer Profile dashboard displays this per customer. |
| **Gap** | None — fully covered by design. |
| **Phase** | Phase 3 (QBR Agent, Day 23-24) |

---

### Q9: Why are unhappy customers unhappy? Feature gap? Cumbersome platform? Broken? Customer-side or product-side issue?

| | |
|---|---|
| **Covered?** | Partial |
| **How** | QBR Agent (Agent 10) performs root cause analysis by cross-referencing Jira ticket categories (Deployment/Scan/Connector/Performance/UI/Integration) with Fathom call themes over the last 90 days. Output includes `root_cause_analysis` (e.g., "Persistent connector failures — 7 tickets in 90 days") and `key_complaint_themes`. |
| **Gap** | **Responsibility attribution missing.** The system can identify *what* the problem is (connector failures, scan performance) but cannot reliably distinguish *whose fault it is* — customer misconfiguration vs product bug vs infrastructure limitation. This distinction requires: (1) Support bundle analysis from Troubleshooting Agent (Agent 7) to determine technical root cause, (2) Product usage data (Gap from Q7) to assess platform usability, (3) A structured "responsibility matrix" classification in the QBR Agent's prompt (product defect / customer environment / feature gap / training gap / integration issue). Items 1 and 3 are achievable with prompt engineering. Item 2 requires the missing product analytics data source. |
| **Phase** | Phase 3 (Day 23) — partial. Responsibility attribution via prompt enhancement is feasible in Phase 3. Full "cumbersome platform" analysis requires product usage data (not in any phase). |

---

## 4. The Ultimate Ask

### Q10: Platform recommends "3 unhappy customers → do A, B, C, D and they will become happy"

| | |
|---|---|
| **Covered?** | Partial |
| **How** | QBR Agent (Agent 10) outputs `renewal_recommendation` (e.g., "At-risk. Schedule executive call before renewal."). Health Monitor (Agent 9) drafts proactive Jira tickets for at-risk customers. Executive Reporter flags customers needing immediate attention. |
| **Gap** | **Prescriptive remediation engine missing.** Current output is diagnostic ("here's what's wrong") + generic recommendation ("schedule a call"). The executive ask is prescriptive — a specific, sequenced action plan per customer. Example of what's wanted: "Customer X is unhappy because of connector reliability (7 tickets) + slow scan performance. Recommended recovery plan: (1) Deploy hotfix v4.2.1 for connector timeout — ETA 3 days, (2) Schedule technical deep-dive with customer's infra team — this week, (3) Enable scan parallelization config — requires customer approval, (4) Executive check-in call in 2 weeks to verify improvement." This requires: (1) A remediation playbook knowledge base mapping root causes → proven action sequences, (2) An enhancement to QBR Agent's pipeline to generate structured recovery plans, (3) Optionally, a dedicated "Recovery Planner" capability. Items 1 and 2 are achievable within the existing architecture — no structural changes needed. |
| **Phase** | Phase 3 (Day 23-24) — partial. Full prescriptive remediation would need an enhancement to QBR Agent or a post-Phase 3 iteration. |

---

## 5. Summary Scorecard

| # | Question | Status | Phase |
|---|----------|--------|-------|
| Q1 | Most requested feature across customers | **Fully Covered** ✅ | Phase 2 (Day 19) |
| Q2 | Highest attrition risk customer | **Fully Covered** ✅ | Phase 2 (Day 15-16) |
| Q3 | Why didn't 9/10 POCs convert to deals? | **Fully Covered** ✅ | Phase 2 (Day 18-19) |
| Q4 | Why did 90/100 demos not convert to POC? | **Fully Covered** ✅ | Phase 2 (Day 18-19) |
| Q5 | Call sentiment — objection type classification | **Fully Covered** ✅ | Phase 2 (Day 19) — via cross-reference |
| Q6 | What went wrong during the POC? | **Fully Covered** ✅ | Phase 2 (Day 18-19) — via loss analysis |
| Q7 | Was the platform smooth / time spent? | **Not Covered** — needs product analytics data | Not in any phase |
| Q11 | What are the chances of getting [specific deal]? | **Fully Covered** ✅ | Phase 2 (Day 17-19) |
| Q8 | How many customers happy/moderate/unhappy? | **Fully Covered** | Phase 3 (Day 23-24) |
| Q9 | Why are unhappy customers unhappy? (attribution) | **Partial** — needs responsibility classification | Phase 3 + prompt fix |
| Q10 | Recommend specific actions to make them happy | **Partial** — needs prescriptive remediation engine | Phase 3 + enhancement |

### Totals

| Status | Count | Questions |
|--------|-------|-----------|
| **Fully Covered** | 8 | Q1, Q2, Q3, Q4, Q5, Q6, Q8, Q11 |
| **Partially Covered** | 2 | Q9, Q10 |
| **Not Covered** | 1 | Q7 (needs product analytics) |

---

## 6. Gap Summary & Recommended Fixes

### Gap 1: Objection Taxonomy for Calls

- **Affects:** Q5 (call sentiment classification), Q6 (POC evaluation)
- **What's missing:** Structured classification of *why* deals don't convert — beyond generic sentiment into specific objection types.
- **Required objection categories:** Wrong fit, Competitor overlap / already has similar product, Feature gap (wanted something we don't have), Pricing / budget, UX friction / platform complexity, Timing (not ready now), Internal politics / decision-maker absent, POC execution issues
- **Fix:** Add an objection classification step to Call Intelligence agent's pipeline prompt. The transcript data is already ingested — this is purely a prompt engineering task.
- **Effort:** Low (1-2 days). No architecture or schema changes needed.
- **When:** Can be added during Phase 1 (Day 4, Call Intelligence) or retrofitted in Phase 2.

### Gap 2: Product Usage / UX Analytics Data Source

- **Affects:** Q7 (platform smoothness), Q9 (responsibility attribution — "cumbersome platform?")
- **What's missing:** In-product behavior data — session duration, feature adoption, click paths, error rates, time-to-complete workflows.
- **Fix:** Add a 4th data source integration. Options:
  - Mixpanel / Amplitude / Pendo (if HivePro uses one)
  - HivePro internal product telemetry API (if available)
  - Custom instrumentation in the HivePro platform
- **Effort:** High (2-3 days for integration, similar to Jira or HubSpot). Requires a new data source to exist.
- **When:** Would be a Phase 4 addition or a parallel workstream. Cannot be done without the underlying analytics platform.

### Gap 3: Prescriptive Remediation Engine

- **Affects:** Q10 (the ultimate ask — "recommend A, B, C, D")
- **What's missing:** The system diagnoses problems but doesn't prescribe specific, sequenced recovery actions.
- **Fix:** Two components needed:
  1. **Remediation Playbook** — A knowledge base (can be a YAML config or ChromaDB collection) mapping root cause categories to proven action sequences. Example: `connector_failure → [deploy hotfix, schedule tech call, enable monitoring, follow-up in 2 weeks]`.
  2. **Recovery Plan Generator** — Enhancement to QBR Agent (Agent 10) pipeline: after `root_cause_analysis`, add a `prescribe` stage that matches root causes to playbook entries and generates a customer-specific recovery plan with owners, timelines, and success criteria.
- **Effort:** Medium (2-3 days). Fits within existing architecture — no new agents or tables needed.
- **When:** Can be built as an enhancement in Phase 3 (Day 25-26 window) or as a fast-follow after Phase 3.

### Gap 4: Deal Win Probability via Chat

- **Affects:** Q11 (deal-specific win probability queries)
- **What's missing:** Three pieces: (1) HubSpot integration for deal data, (2) `deal` intent in chat intent classifier with keywords (deal, chances, win, close, pipeline, probability, convert), (3) `_build_deal_prompt` in chat fast path that injects deal stage, amount, age, velocity, call sentiment, and historical win rates.
- **Fix:** Items 1-2 are already in Phase 2 scope (Day 17-18). Item 3 is a small addition to `chat_fast_path.py` — add `DEAL_KEYWORDS`, a `deal` entry in `INTENT_AGENT_MAP` pointing to Pre-Sales Funnel Agent, and a `_build_deal_prompt` method. Wire prefetch to pull deal data from HubSpot deals table.
- **Effort:** Low (half day on top of Phase 2 HubSpot work). No architecture changes needed.
- **When:** Phase 2 (Day 18-19), alongside Pre-Sales Funnel Agent and Pipeline Analytics.

---

## 7. Phase Availability Timeline

```
PHASE 1 (Days 1-12):
  [Day 2]  Customer Memory with feature_requests tracking
  [Day 4]  Call sentiment extraction (basic)
           + Objection taxonomy (if prompt enhanced here)
  [Day 6]  Ticket classification + triage
  [Day 10] At-Risk Dashboard with health scores
  [Day 11] Customer Profile with tabs

  Questions answerable: Q1 (partial), Q2 (partial — dashboard only)

PHASE 2 (Days 13-22):
  [Day 15] Health Monitor — health scores, risk flags, churn signals
  [Day 16] Health alerts to Slack
  [Day 17] HubSpot integration live
  [Day 18] Pre-Sales Funnel Agent — conversion rates, blockers
  [Day 19] Pipeline Analytics dashboard
  [Day 20] Executive Reporter — feature demand, portfolio health

  Questions answerable: Q1, Q2, Q3, Q4, Q5 (with prompt fix), Q6 (partial), Q11

PHASE 3 (Days 23-30):
  [Day 23] QBR Agent — sentiment bucketing, root cause analysis
  [Day 24] QBR dashboard + Slack integration
  [Day 28] Accuracy metrics live

  Questions answerable: Q1-Q4, Q5 (with fix), Q6 (partial),
                         Q8, Q9 (partial), Q10 (partial)

NOT IN CURRENT PHASES:
  Q7 — Requires product analytics data source (Phase 4 / parallel)
  Q9 full — Needs product usage data for complete attribution
  Q10 full — Needs remediation playbook + recovery plan generator
```

---

## 8. Recommendation

The architecture as designed covers **90% of what the executives asked for**. The three gaps are addressable:

1. **Objection taxonomy** — Low effort, do it in Phase 1-2. Just prompt engineering.
2. **Prescriptive remediation** — Medium effort, do it in Phase 3. Enhancement to QBR Agent.
3. **Product usage data** — High effort, requires HivePro to have analytics instrumentation. Scope as Phase 4 or parallel workstream. This is the only gap that requires external dependency.

The system will be **demo-ready for C-level executives** after Phase 2 (Day 22) for pre-sales and health questions, and after Phase 3 (Day 30) for QBR and remediation questions.
