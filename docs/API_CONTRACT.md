# HivePro CS Control Plane — API Contract

**Version:** 1.0  
**Base URL:** `http://localhost:8000/api`  
**Auth:** JWT Bearer token (unless marked PUBLIC)  
**Content-Type:** `application/json`  
**Date:** February 27, 2026

---

## 1. Authentication

### POST /auth/login [PUBLIC]
Login with email and password.

**Request:**
```json
{
  "email": "ayushmaan@hivepro.com",
  "password": "securepassword123"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "ayushmaan@hivepro.com",
    "full_name": "Ayushmaan Naruka",
    "role": "admin",
    "avatar_url": null
  }
}
```

**Response 401:**
```json
{ "detail": "Invalid email or password" }
```

### POST /auth/refresh
Refresh access token.

**Request:**
```json
{ "refresh_token": "eyJhbGciOiJIUzI1NiIs..." }
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...(new)",
  "token_type": "bearer",
  "expires_in": 900
}
```

### GET /auth/me
Get current authenticated user.

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "ayushmaan@hivepro.com",
  "full_name": "Ayushmaan Naruka",
  "role": "admin",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2026-01-15T10:00:00Z"
}
```

---

## 2. Dashboard

### GET /dashboard/stats
KPI statistics for the command center.

**Response 200:**
```json
{
  "total_customers": 47,
  "at_risk_count": 5,
  "open_tickets": 23,
  "avg_health_score": 71.4,
  "trends": {
    "customers_change": 3,
    "risk_change": 2,
    "tickets_change": -4,
    "health_change": 5.2
  }
}
```

### GET /dashboard/agents
All agent statuses for the orchestration map.

**Response 200:**
```json
{
  "agents": [
    {
      "name": "cs_orchestrator",
      "display_name": "CS Orchestrator",
      "lane": "control",
      "status": "active",
      "current_task": "Routing jira_ticket_created to Ticket Triage",
      "tasks_today": 12,
      "avg_response_ms": 340,
      "last_active": "2026-02-27T14:23:00Z"
    },
    {
      "name": "customer_memory",
      "display_name": "Customer Memory Agent",
      "lane": "control",
      "status": "idle",
      "current_task": null,
      "tasks_today": 8,
      "avg_response_ms": 120,
      "last_active": "2026-02-27T14:22:30Z"
    },
    {
      "name": "call_intelligence",
      "display_name": "Call Intelligence Agent",
      "lane": "value",
      "status": "active",
      "current_task": "Processing Fathom recording for Acme Corp",
      "tasks_today": 3,
      "avg_response_ms": 4500,
      "last_active": "2026-02-27T14:21:00Z"
    }
  ]
}
```

### GET /dashboard/events?limit=50&offset=0
Recent events for the live stream.

**Query Params:** `limit` (int, default 50), `offset` (int, default 0)

**Response 200:**
```json
{
  "events": [
    {
      "id": "evt-001",
      "event_type": "jira_ticket_created",
      "source": "jira_webhook",
      "description": "New P2 ticket from Acme Corp: Scan failure on subnet 10.0.1.x",
      "customer_name": "Acme Corp",
      "routed_to": "ticket_triage",
      "status": "completed",
      "created_at": "2026-02-27T14:23:00Z",
      "processed_at": "2026-02-27T14:23:02Z"
    }
  ],
  "total": 245,
  "limit": 50,
  "offset": 0
}
```

### GET /dashboard/quick-health
Top 12 customers for the mini health grid (sorted by risk).

**Response 200:**
```json
{
  "customers": [
    {
      "id": "cust-001",
      "name": "Acme Corp",
      "health_score": 42,
      "risk_level": "high_risk",
      "risk_count": 3,
      "initial": "AC"
    }
  ]
}
```

---

## 3. Customers

### GET /customers
List all customers with filters and pagination.

**Query Params:**
- `search` (string) — search by name
- `risk_level` (string) — healthy | watch | high_risk
- `cs_owner_id` (uuid) — filter by assigned CS engineer
- `tier` (string) — enterprise | mid_market | smb
- `sort_by` (string) — score | name | renewal (default: score)
- `sort_order` (string) — asc | desc (default: asc for score)
- `limit` (int, default 20)
- `offset` (int, default 0)

**Response 200:**
```json
{
  "customers": [
    {
      "id": "cust-001",
      "name": "Acme Corp",
      "industry": "Banking",
      "tier": "enterprise",
      "health_score": 42,
      "risk_level": "high_risk",
      "risk_count": 3,
      "open_ticket_count": 5,
      "cs_owner": {
        "id": "user-001",
        "full_name": "Vignesh",
        "avatar_url": null
      },
      "renewal_date": "2026-06-01",
      "days_to_renewal": 94,
      "last_call_date": "2026-02-25",
      "primary_contact_name": "John Doe"
    }
  ],
  "total": 47,
  "limit": 20,
  "offset": 0
}
```

### GET /customers/:id
Full customer detail with memory.

**Response 200:**
```json
{
  "id": "cust-001",
  "name": "Acme Corp",
  "industry": "Banking",
  "tier": "enterprise",
  "contract_start": "2025-06-01",
  "renewal_date": "2026-06-01",
  "days_to_renewal": 94,
  "primary_contact_name": "John Doe",
  "primary_contact_email": "john@acme.com",
  "cs_owner": {
    "id": "user-001",
    "full_name": "Vignesh",
    "avatar_url": null
  },
  "deployment": {
    "mode": "OVA",
    "product_version": "4.2.1",
    "integrations": ["Qualys", "CrowdStrike", "ServiceNow"],
    "known_constraints": ["EDR installed", "Air-gapped network"]
  },
  "health": {
    "current_score": 42,
    "risk_level": "high_risk",
    "risk_flags": ["3 overdue tickets", "Negative sentiment trend", "SLA breach on P1"],
    "factors": {
      "ticket_severity": 8,
      "sla_compliance": 5,
      "sentiment": 6,
      "engagement": 10,
      "deployment_health": 8,
      "resolution_rate": 5
    }
  },
  "open_ticket_count": 5,
  "recent_call_count": 4,
  "pending_action_items": 3,
  "metadata": {},
  "created_at": "2025-06-01T00:00:00Z",
  "updated_at": "2026-02-27T14:00:00Z"
}
```

### GET /customers/:id/health-history?days=30
Health score time series.

**Query Params:** `days` (int, default 30)

**Response 200:**
```json
{
  "customer_id": "cust-001",
  "history": [
    {
      "date": "2026-02-27",
      "score": 42,
      "risk_level": "high_risk",
      "risk_flags": ["3 overdue tickets", "Negative sentiment trend"]
    },
    {
      "date": "2026-02-26",
      "score": 48,
      "risk_level": "high_risk",
      "risk_flags": ["2 overdue tickets"]
    }
  ]
}
```

### GET /customers/:id/insights?limit=10&offset=0
Call insights for this customer.

**Response 200:** Same shape as `/insights` but filtered to this customer.

### GET /customers/:id/tickets?limit=10&offset=0
Tickets for this customer.

**Response 200:** Same shape as `/tickets` but filtered to this customer.

### GET /customers/:id/action-items
Action items for this customer.

**Response 200:**
```json
{
  "action_items": [
    {
      "id": "ai-001",
      "title": "Schedule follow-up call",
      "description": "Customer requested follow-up on onboarding timeline",
      "source_type": "call_insight",
      "source_id": "insight-001",
      "owner": { "id": "user-001", "full_name": "Vignesh" },
      "deadline": "2026-03-01T00:00:00Z",
      "status": "pending",
      "created_at": "2026-02-25T10:00:00Z"
    }
  ]
}
```

### GET /customers/:id/similar-issues
RAG-powered similar issues from other customers.

**Response 200:**
```json
{
  "query_context": "Scan failure on subnet 10.0.1.x",
  "similar_issues": [
    {
      "ticket_id": "JIRA-987",
      "customer_name": "Beta Financial",
      "summary": "Scan failure on subnet 192.168.1.x",
      "resolution": "Configuration mismatch in scanner profile — updated CIDR range",
      "resolved_in_days": 2,
      "resolved_at": "2026-01-15",
      "similarity_score": 0.87
    },
    {
      "ticket_id": "JIRA-654",
      "customer_name": "Gamma Telecom",
      "summary": "Subnet scan timeout on 172.16.0.x",
      "resolution": "Firewall rule blocking scanner — added exception",
      "resolved_in_days": 5,
      "resolved_at": "2025-11-20",
      "similarity_score": 0.72
    }
  ]
}
```

### POST /customers
Create a new customer.

**Request:**
```json
{
  "name": "New Customer Inc",
  "industry": "Healthcare",
  "tier": "mid_market",
  "contract_start": "2026-03-01",
  "renewal_date": "2027-03-01",
  "primary_contact_name": "Jane Smith",
  "primary_contact_email": "jane@newcustomer.com",
  "cs_owner_id": "user-002",
  "deployment_mode": "Cloud",
  "product_version": "4.3.0",
  "integrations": ["Qualys"],
  "known_constraints": []
}
```

**Response 201:** Full customer object.

### PUT /customers/:id
Update customer fields.

**Request:** Partial update — only include fields to change.

**Response 200:** Updated customer object.

---

## 4. Health

### GET /health/scores
All latest health scores.

**Response 200:**
```json
{
  "scores": [
    {
      "customer_id": "cust-001",
      "customer_name": "Acme Corp",
      "score": 42,
      "risk_level": "high_risk",
      "risk_flags": ["3 overdue tickets"],
      "calculated_at": "2026-02-27T09:00:00Z"
    }
  ]
}
```

### GET /health/at-risk
Only customers with risk_level in (high_risk, trending_down, renewal_risk).

**Response 200:** Same shape as `/health/scores` but filtered.

### POST /health/run-check
Trigger manual health check for all customers. Runs async via Celery.

**Response 202:**
```json
{
  "task_id": "celery-task-001",
  "message": "Health check initiated for all customers",
  "status": "processing"
}
```

### GET /health/trends?days=30
Aggregated health trends.

**Response 200:**
```json
{
  "daily_averages": [
    { "date": "2026-02-27", "avg_score": 71.4, "at_risk_count": 5 },
    { "date": "2026-02-26", "avg_score": 70.1, "at_risk_count": 4 }
  ]
}
```

---

## 5. Tickets

### GET /tickets
List tickets with filters.

**Query Params:**
- `search` (string)
- `status` (string) — open | in_progress | waiting | resolved | closed
- `severity` (string) — P1 | P2 | P3 | P4
- `customer_id` (uuid)
- `assigned_to_id` (uuid)
- `ticket_type` (string) — deployment | scan_failure | connector | performance | ui | integration | feature_request
- `sort_by` (string) — created | severity | sla (default: created)
- `sort_order` (string) — asc | desc
- `limit` (int, default 50)
- `offset` (int, default 0)

**Response 200:**
```json
{
  "tickets": [
    {
      "id": "tkt-001",
      "jira_id": "JIRA-1234",
      "customer": { "id": "cust-001", "name": "Acme Corp" },
      "summary": "Scan failure on subnet 10.0.1.x",
      "ticket_type": "scan_failure",
      "severity": "P1",
      "status": "open",
      "assigned_to": { "id": "user-001", "full_name": "Vignesh", "avatar_url": null },
      "has_triage_result": true,
      "has_troubleshoot_result": false,
      "sla_deadline": "2026-02-27T16:23:00Z",
      "sla_remaining_hours": 2.0,
      "sla_breaching": false,
      "created_at": "2026-02-27T14:23:00Z",
      "updated_at": "2026-02-27T14:23:02Z"
    }
  ],
  "total": 50,
  "limit": 50,
  "offset": 0
}
```

### GET /tickets/:id
Full ticket detail with AI results.

**Response 200:**
```json
{
  "id": "tkt-001",
  "jira_id": "JIRA-1234",
  "customer": { "id": "cust-001", "name": "Acme Corp" },
  "summary": "Scan failure on subnet 10.0.1.x",
  "description": "Full ticket description from Jira...",
  "ticket_type": "scan_failure",
  "severity": "P1",
  "status": "open",
  "assigned_to": { "id": "user-001", "full_name": "Vignesh", "avatar_url": null },
  "triage_result": {
    "category": "scan_failure",
    "severity_recommendation": "P1",
    "confidence": 0.92,
    "suggested_action": "Check scanner configuration for subnet range and verify network connectivity",
    "duplicate_check": {
      "is_duplicate": false,
      "similar_tickets": ["JIRA-987", "JIRA-654"]
    },
    "triaged_at": "2026-02-27T14:23:02Z"
  },
  "troubleshoot_result": null,
  "escalation_summary": null,
  "sla_deadline": "2026-02-27T16:23:00Z",
  "sla_remaining_hours": 2.0,
  "sla_breaching": false,
  "created_at": "2026-02-27T14:23:00Z",
  "updated_at": "2026-02-27T14:23:02Z",
  "resolved_at": null
}
```

### PUT /tickets/:id/status
Update ticket status (for kanban drag-and-drop).

**Request:**
```json
{ "status": "in_progress" }
```

**Response 200:** Updated ticket object.

### PUT /tickets/:id/assign
Assign ticket to a user.

**Request:**
```json
{ "assigned_to_id": "user-002" }
```

**Response 200:** Updated ticket object.

### POST /tickets/:id/triage
Trigger AI triage on a ticket. Async.

**Response 202:**
```json
{
  "task_id": "celery-task-002",
  "message": "AI triage initiated for JIRA-1234",
  "status": "processing"
}
```

### POST /tickets/:id/troubleshoot
Trigger AI troubleshooting on a ticket. Async.

**Response 202:**
```json
{
  "task_id": "celery-task-003",
  "message": "AI troubleshooting initiated for JIRA-1234",
  "status": "processing"
}
```

### GET /tickets/:id/similar
Similar past tickets via RAG.

**Response 200:** Same shape as `/customers/:id/similar-issues`.

---

## 6. Insights (Fathom)

### GET /insights
List call insights.

**Query Params:**
- `search` (string)
- `customer_id` (uuid)
- `sentiment` (string) — positive | neutral | negative
- `date_from` (date)
- `date_to` (date)
- `limit` (int, default 20)
- `offset` (int, default 0)

**Response 200:**
```json
{
  "insights": [
    {
      "id": "ins-001",
      "customer": { "id": "cust-001", "name": "Acme Corp" },
      "call_date": "2026-02-25T10:00:00Z",
      "participants": [
        { "name": "John Doe", "role": "customer" },
        { "name": "Vignesh", "role": "cs_engineer" }
      ],
      "summary": "Customer expressed concern about onboarding timeline delays. Requested follow-up within a week.",
      "decisions": ["Extend onboarding by 2 weeks", "Weekly sync until go-live"],
      "action_items": [
        {
          "id": "ai-001",
          "task": "Schedule follow-up call",
          "owner": "Vignesh",
          "deadline": "2026-03-01",
          "status": "pending"
        },
        {
          "id": "ai-002",
          "task": "Share updated timeline document",
          "owner": "Sarah",
          "deadline": "2026-02-28",
          "status": "pending"
        }
      ],
      "risks": ["Possible escalation if timeline slips further"],
      "sentiment": "negative",
      "sentiment_score": -0.4,
      "key_topics": ["onboarding", "timeline", "deployment"],
      "customer_recap_draft": "Hi John,\n\nThank you for today's call. Here's a summary of what we discussed...",
      "processed_at": "2026-02-25T10:45:00Z"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### GET /insights/:id
Full insight detail (includes raw transcript if available).

**Response 200:** Same as list item + `raw_transcript` field.

### POST /insights/sync-fathom
Trigger Fathom sync. Async.

**Response 202:**
```json
{
  "task_id": "celery-task-004",
  "message": "Fathom sync initiated",
  "status": "processing"
}
```

### GET /insights/sentiment-trend?days=30&customer_id=optional
Sentiment chart data.

**Response 200:**
```json
{
  "trend": [
    { "date": "2026-02-27", "avg_sentiment_score": -0.1, "call_count": 3 },
    { "date": "2026-02-26", "avg_sentiment_score": 0.2, "call_count": 5 }
  ]
}
```

### GET /insights/action-items?status=pending&owner_id=optional
All action items from calls.

**Response 200:**
```json
{
  "action_items": [
    {
      "id": "ai-001",
      "customer_name": "Acme Corp",
      "insight_id": "ins-001",
      "task": "Schedule follow-up call",
      "owner": { "id": "user-001", "full_name": "Vignesh" },
      "deadline": "2026-03-01",
      "status": "pending",
      "is_overdue": false
    }
  ],
  "summary": { "pending": 5, "overdue": 3, "completed": 22 }
}
```

### PUT /insights/action-items/:id
Update action item status.

**Request:**
```json
{ "status": "completed" }
```

**Response 200:** Updated action item.

---

## 7. Agents

### GET /agents
All agent statuses (same as /dashboard/agents but with more detail).

**Response 200:**
```json
{
  "agents": [
    {
      "name": "cs_orchestrator",
      "display_name": "CS Orchestrator",
      "description": "Routes events to the correct agent based on event type and customer context",
      "lane": "control",
      "status": "active",
      "current_task": "Routing jira_ticket_created to Ticket Triage",
      "tasks_today": 12,
      "tasks_total": 1543,
      "avg_response_ms": 340,
      "success_rate": 0.98,
      "last_active": "2026-02-27T14:23:00Z"
    }
  ]
}
```

### GET /agents/:name
Specific agent detail.

**Response 200:** Single agent from the above list.

### GET /agents/:name/logs?limit=20&offset=0
Agent activity logs.

**Response 200:**
```json
{
  "logs": [
    {
      "id": "log-001",
      "agent_name": "ticket_triage",
      "event_type": "task_completed",
      "trigger_event": "jira_ticket_created",
      "customer_name": "Acme Corp",
      "input_summary": "New P2 ticket: Scan failure on subnet 10.0.1.x",
      "output_summary": "Classified as scan_failure, recommended P1 severity, suggested config check",
      "reasoning_summary": "Ticket mentions scan failure + specific subnet. Historical data shows similar issues resolved by config update. Severity should be P1 due to production impact.",
      "status": "completed",
      "duration_ms": 2340,
      "created_at": "2026-02-27T14:23:02Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### GET /agents/orchestration-flow?limit=20
Recent event routing timeline.

**Response 200:**
```json
{
  "flows": [
    {
      "event_id": "evt-001",
      "event_type": "jira_ticket_created",
      "source": "jira_webhook",
      "customer_name": "Acme Corp",
      "routed_to": "ticket_triage",
      "output": "Triaged as P1 scan_failure",
      "status": "completed",
      "total_duration_ms": 2680,
      "created_at": "2026-02-27T14:23:00Z"
    }
  ]
}
```

### POST /agents/:name/trigger
Manually trigger an agent. Async.

**Request:**
```json
{
  "customer_id": "cust-001",
  "context": "Manual health check requested"
}
```

**Response 202:**
```json
{
  "task_id": "celery-task-005",
  "message": "Health Monitor Agent triggered for Acme Corp",
  "status": "processing"
}
```

---

## 8. Events

### GET /events?limit=50&offset=0
Event history.

**Query Params:** `limit`, `offset`, `event_type`, `customer_id`, `status`

**Response 200:** Same shape as `/dashboard/events`.

### POST /events [Webhook Endpoint]
Create event (used by Jira/Slack webhooks and manual triggers).

**Request:**
```json
{
  "event_type": "jira_ticket_created",
  "source": "jira_webhook",
  "payload": {
    "jira_id": "JIRA-1234",
    "summary": "Scan failure on subnet 10.0.1.x",
    "severity": "P2",
    "reporter": "john@acme.com"
  },
  "customer_id": "cust-001"
}
```

**Response 201:**
```json
{
  "id": "evt-001",
  "event_type": "jira_ticket_created",
  "status": "pending",
  "created_at": "2026-02-27T14:23:00Z"
}
```

---

## 9. Alerts

### GET /alerts?status=open&severity=critical
List alerts.

**Query Params:** `status` (open/acknowledged/resolved/dismissed), `severity`, `customer_id`, `limit`, `offset`

**Response 200:**
```json
{
  "alerts": [
    {
      "id": "alert-001",
      "customer": { "id": "cust-001", "name": "Acme Corp" },
      "alert_type": "high_risk",
      "severity": "critical",
      "title": "Health score dropped to 42 (was 60 yesterday)",
      "description": "Score dropped due to 3 overdue tickets and negative sentiment from recent call",
      "suggested_action": "Review overdue tickets JIRA-1234, JIRA-1233, JIRA-1230. Schedule customer check-in.",
      "similar_past_issues": [
        { "customer": "Epsilon Insurance", "date": "2026-01-10", "resolution": "Emergency sync + ticket blitz" }
      ],
      "assigned_to": { "id": "user-001", "full_name": "Vignesh" },
      "status": "open",
      "slack_notified": true,
      "created_at": "2026-02-27T09:00:00Z"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

### PUT /alerts/:id/acknowledge
**Response 200:** Updated alert with `status: "acknowledged"`.

### PUT /alerts/:id/resolve
**Response 200:** Updated alert with `status: "resolved"`, `resolved_at` set.

### PUT /alerts/:id/dismiss
**Response 200:** Updated alert with `status: "dismissed"`.

---

## 10. Reports

### GET /reports?limit=20&offset=0
List generated reports.

**Query Params:** `report_type` (weekly_digest/monthly_report/qbr), `customer_id`, `limit`, `offset`

**Response 200:**
```json
{
  "reports": [
    {
      "id": "rpt-001",
      "report_type": "weekly_digest",
      "title": "Weekly CS Digest — Feb 17-23, 2026",
      "customer_name": null,
      "period_start": "2026-02-17",
      "period_end": "2026-02-23",
      "generated_at": "2026-02-24T09:00:00Z"
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

### GET /reports/:id
Report detail with full content.

**Response 200:**
```json
{
  "id": "rpt-001",
  "report_type": "weekly_digest",
  "title": "Weekly CS Digest — Feb 17-23, 2026",
  "customer_name": null,
  "period_start": "2026-02-17",
  "period_end": "2026-02-23",
  "content": {
    "summary": "This week saw 23 new tickets...",
    "health_overview": { "avg_score": 70, "at_risk": 4 },
    "ticket_summary": { "opened": 23, "resolved": 18, "sla_breaches": 2 },
    "call_summary": { "total_calls": 12, "action_items_created": 15 },
    "highlights": ["Acme Corp health dropped to 42", "Beta Financial renewal confirmed"],
    "recommendations": ["Schedule emergency sync with Acme", "Review Epsilon Insurance tickets"]
  },
  "generated_at": "2026-02-24T09:00:00Z"
}
```

### POST /reports/generate
Generate a new report. Async.

**Request:**
```json
{
  "report_type": "weekly_digest",
  "period_start": "2026-02-17",
  "period_end": "2026-02-23",
  "customer_id": null
}
```

**Response 202:**
```json
{
  "task_id": "celery-task-006",
  "message": "Generating Weekly Digest for Feb 17-23",
  "status": "processing"
}
```

### GET /reports/analytics
Analytics dashboard data.

**Response 200:**
```json
{
  "kpis": {
    "total_customers": 47,
    "avg_health_score": 71.4,
    "tickets_resolved_this_week": 18,
    "calls_processed_this_month": 32
  },
  "health_trend": [
    { "date": "2026-02-27", "avg_score": 71.4 }
  ],
  "ticket_volume": [
    { "week": "2026-W09", "opened": 23, "resolved": 18, "by_severity": { "P1": 3, "P2": 8, "P3": 9, "P4": 3 } }
  ],
  "sentiment_distribution": {
    "positive": 45,
    "neutral": 35,
    "negative": 20
  },
  "agent_performance": [
    { "agent": "ticket_triage", "tasks_completed": 156, "avg_duration_ms": 1200 }
  ]
}
```

---

## 11. WebSocket

### WS /ws
Real-time event stream. Connect after login with JWT.

**Connection:** `ws://localhost:8000/api/ws?token={access_token}`

**Server → Client Events:**

```json
// Agent status change
{
  "type": "agent_status",
  "data": {
    "agent": "call_intelligence",
    "status": "active",
    "task": "Processing Fathom recording for Acme Corp"
  }
}

// Event processed
{
  "type": "event_processed",
  "data": {
    "event_id": "evt-001",
    "event_type": "jira_ticket_created",
    "customer": "Acme Corp",
    "routed_to": "ticket_triage",
    "status": "completed"
  }
}

// New alert
{
  "type": "new_alert",
  "data": {
    "id": "alert-001",
    "customer": "Acme Corp",
    "alert_type": "high_risk",
    "severity": "critical",
    "title": "Health score dropped to 42"
  }
}

// Health score update
{
  "type": "health_update",
  "data": {
    "customer_id": "cust-001",
    "customer_name": "Acme Corp",
    "new_score": 42,
    "prev_score": 60,
    "risk_level": "high_risk"
  }
}

// Ticket triaged
{
  "type": "ticket_triaged",
  "data": {
    "ticket_id": "tkt-001",
    "jira_id": "JIRA-1234",
    "customer": "Acme Corp",
    "category": "scan_failure",
    "severity_rec": "P1",
    "confidence": 0.92
  }
}

// Call insight ready
{
  "type": "insight_ready",
  "data": {
    "insight_id": "ins-001",
    "customer": "Acme Corp",
    "sentiment": "negative",
    "action_items_count": 3
  }
}
```

---

## 12. Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "RESOURCE_NOT_FOUND",
  "status_code": 404
}
```

**Standard Error Codes:**
| HTTP | Code | Description |
|------|------|-------------|
| 400 | VALIDATION_ERROR | Invalid request body/params |
| 401 | UNAUTHORIZED | Missing or invalid JWT |
| 403 | FORBIDDEN | Insufficient role/permissions |
| 404 | RESOURCE_NOT_FOUND | Entity not found |
| 409 | CONFLICT | Duplicate resource |
| 422 | UNPROCESSABLE | Valid JSON but semantic error |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |
| 503 | SERVICE_UNAVAILABLE | External service down |

---

## 13. Common Headers

**Request:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Response:**
```
Content-Type: application/json
X-Request-Id: {uuid}
X-Rate-Limit-Remaining: {int}
```
