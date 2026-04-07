# Escalation Rules Proposal — CS Control Plane

> **For review by: Ariza Zehra**
> **Prepared by: Ayushmaan Singh Naruka**
> **Date: April 7, 2026**
>
> These rules will run automatically on a schedule. When triggered, they post a formatted alert to a **dedicated Slack channel** (e.g., `#cs-escalations-auto` or the existing `#cs-executive-urgent`). All thresholds are configurable — we can adjust numbers anytime without code changes.

---

## Rule 1: Repeated Feature Requests (3+ customers in 30 days)

**What it detects:**
If the same feature request appears in Jira tickets from **3 or more different customers** within the last 30 days, it's flagged as a trending feature demand.

**How it works:**
- Scans Jira tickets labeled as `feature_request` (or with "feature request" in the category/labels)
- Groups by similar topic (keyword matching on ticket summary)
- If 3+ distinct customers raised similar requests in the last 30 days → trigger

**Slack output:**
> **Trending Feature Request** (3 customers in 30 days)
> **Topic:** "Improved logging & observability"
> **Requested by:** PDO, Aldrea AI, Rade Finance
> **Tickets:** UCSC-1234, UCSC-1289, UCSC-1301
> **First raised:** March 12, 2026
> **Suggested action:** Review for roadmap prioritization

**Configurable thresholds:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_customers` | 3 | Minimum distinct customers requesting the same feature |
| `time_window_days` | 30 | Lookback period in days |
| `match_method` | `label + keyword` | How we group similar requests |

---

## Rule 2: Repeated Complaint / Same Issue (3+ occurrences in 30 days)

**What it detects:**
If the same type of issue/complaint is raised **3 or more times** (by same or different customers) within 30 days, it's flagged as a recurring problem.

**How it works:**
- Scans Jira tickets by category (e.g., "connectivity issue", "scan failure", "RBAC error")
- Groups tickets with matching categories or similar summaries
- If 3+ tickets match the same issue pattern in 30 days → trigger

**Slack output:**
> **Recurring Issue Detected** (4 tickets in 30 days)
> **Issue pattern:** "Connector timeout / connectivity failure"
> **Affected customers:** PDO, Mavadla Corp, Islami Bank
> **Severity breakdown:** 1x P0, 2x P1, 1x P2
> **Tickets:** UCSC-1245, UCSC-1267, UCSC-1290, UCSC-1305
> **Suggested action:** Escalate to engineering — this is a systemic issue, not isolated incidents

**Configurable thresholds:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_occurrences` | 3 | Minimum tickets with the same issue pattern |
| `time_window_days` | 30 | Lookback period in days |
| `group_by` | `category + keyword` | How we cluster similar issues |

---

## Rule 3: Unresolved Jira Escalation (Stale > 3 days)

**What it detects:**
If a Jira ticket that has been escalated (P0 or P1, or marked as escalation) remains unresolved for more than 3 days, flag it.

**How it works:**
- Checks all open tickets with severity P0 or P1 (or status = "escalated")
- If the ticket has been open for more than 3 days with no resolution or status change → trigger
- Deduplicates: won't re-flag the same ticket if already flagged and still open

**Slack output:**
> **Stale Escalation Alert**
> **Ticket:** UCSC-1234 — "Production scan failure on RBAC-enabled nodes"
> **Customer:** PDO
> **Severity:** P0
> **Open for:** 5 days (threshold: 3 days)
> **Last updated:** April 2, 2026
> **Assigned to:** (from Jira assignee field)
> **Suggested action:** Follow up immediately — SLA at risk

**Configurable thresholds:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_days_p0` | 3 | Days before a P0 escalation is flagged as stale |
| `max_days_p1` | 4 | Days before a P1 escalation is flagged as stale |
| `check_status_change` | true | Also flag if no status update in N days (even if not resolved) |

**Note:** We already have rules for P0 stale > 7 days and P1 stale > 10 days. This new rule is **stricter** (3-4 days) and specifically targets the executive Slack channel. We can either tighten the existing rules or keep both — the existing ones alert on `#cs-health-alerts`, this one alerts on the executive channel.

---

## Rule 4: Unanswered Customer Action Items from Calls (Fathom)

**What it detects:**
If an action item was captured from a Fathom call recording and no follow-up activity (Jira ticket, another call, or deal update) is detected within 3 days, flag it as potentially dropped.

**How it works:**
- After each Fathom sync, extracts action items (already stored in `call_insights.action_items` and `action_items` table)
- For each action item, checks if any related activity happened within 3 days:
  - A Jira ticket was created for that customer
  - A follow-up call happened with the same customer
  - A deal stage change occurred
- If no related activity is found → flag as "potentially unanswered"

**Slack output:**
> **Unanswered Action Item** (3+ days, no follow-up detected)
> **From call:** "PDO Quarterly Check-in" (April 1, 2026)
> **Action item:** "Chaitanya Garg — send requirement documentation for RBAC enhancement"
> **Assigned to:** Chaitanya Garg
> **Customer:** PDO
> **Days since call:** 5
> **Suggested action:** Follow up with Chaitanya on the pending requirement doc

**Configurable thresholds:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `followup_window_days` | 3 | Days to wait before flagging no follow-up |
| `check_jira` | true | Look for related Jira activity as follow-up |
| `check_calls` | true | Look for follow-up calls with same customer |
| `check_deals` | true | Look for deal stage changes as follow-up |

**Limitation:** The system detects *absence* of activity, not whether the action was actually completed offline. So this is a reminder/nudge, not a definitive "missed" flag. We can label it as "Reminder" rather than "Alert".

---

## Slack Channel Routing

| Rule | Destination Channel | Why |
|------|-------------------|-----|
| Rule 1 (Feature requests) | `#cs-executive-urgent` | Executives need to see trending demands for roadmap decisions |
| Rule 2 (Recurring issues) | `#cs-executive-urgent` | Systemic issues need engineering leadership attention |
| Rule 3 (Stale escalations) | `#cs-executive-urgent` | Kazi sir / Anand sir need to know about stuck escalations |
| Rule 4 (Unanswered action items) | `#cs-executive-urgent` or a new `#cs-followups` | Gentle reminders for the team |

> **Question for Ariza:** Should all four rules go to `#cs-executive-urgent`, or should we create a separate channel for Rules 1 & 2 (trending patterns) vs Rules 3 & 4 (individual follow-ups)?

---

## Schedule

| Option | Frequency | Pros | Cons |
|--------|-----------|------|------|
| **A) Daily (8:30 AM)** | Every morning | Catches issues fast | Might be noisy |
| **B) Twice a week (Wed + Fri)** | 2x per week | Less noise, matches exec digest | Slower to catch |
| **C) Daily for P0/P1, weekly for patterns** | Mixed | Best of both worlds | Slightly more complex |

> **Recommendation:** Option C — stale escalations (Rule 3) checked daily, pattern rules (Rules 1, 2, 4) checked twice a week.

---

## Existing Rules (Already Active)

For reference, these rules are already running in the system:

| Rule | Trigger | Severity | Channel |
|------|---------|----------|---------|
| Health score drop > 15 pts (7 days) | Health decline | HIGH | #cs-health-alerts |
| P0 tickets stale > 7 days | Aging ticket | HIGH | #cs-health-alerts |
| P1 tickets stale > 10 days | Aging ticket | HIGH | #cs-health-alerts |
| Renewal at risk (< 60 days + bad health) | Renewal proximity | CRITICAL | #cs-health-alerts |
| 3+ negative sentiment calls in a row | Sentiment streak | MEDIUM | #cs-health-alerts |

> **Question for Ariza:** Should we tighten the existing P0/P1 stale thresholds (currently 7 and 10 days) to match the new 3-4 day thresholds? Or keep both — existing rules for the CS team channel, new stricter rules for the executive channel?

---

## Implementation Approach

Once rules are approved:
1. Add new rule definitions to `alert_rules_engine.py` (same pattern as existing 5 rules)
2. Add configurable thresholds to `config.py` (env vars so we can change without redeploying)
3. Schedule via APScheduler (already set up for other jobs)
4. Slack cards formatted with Block Kit (consistent with existing alerts)
5. All thresholds adjustable via environment variables — no code changes needed to tune

**Estimated effort:** 1-2 days to implement all 4 rules after approval.

---

## Questions for Ariza

1. **Channel routing:** All 4 rules to `#cs-executive-urgent`, or split across channels?
2. **Stale escalation threshold:** 3 days for P0, 4 days for P1 — correct?
3. **Feature request matching:** Should we match by Jira labels only, or also by AI-powered similarity on ticket summaries?
4. **Action item reminders (Rule 4):** Should these go to the executive channel, or a separate team channel?
5. **Existing rules:** Tighten P0/P1 stale thresholds, or keep both old (7/10 day) and new (3/4 day)?
6. **Schedule preference:** Daily for urgent, twice-weekly for patterns — okay?
