# HivePro CS Control Plane — API Contract

**Version:** 2.0 (Agentic Architecture)
**Base URL:** `http://localhost:8000/api`
**v2 Base URL:** `http://localhost:8000/api/v2`
**Auth:** JWT Bearer token (unless marked PUBLIC)
**Content-Type:** `application/json`
**Date:** March 2, 2026

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
      "name": "cso_orchestrator",
      "display_name": "CS Orchestrator",
      "human_name": "Naveen Kapoor",
      "tier": 1,
      "lane": null,
      "status": "active",
      "current_task": "Delegating health_alert to Value Lane",
      "tasks_today": 12,
      "avg_response_ms": 340,
      "last_active": "2026-03-01T14:23:00Z"
    },
    {
      "name": "support_lead",
      "display_name": "Support Operations Lead",
      "human_name": "Rachel Torres",
      "tier": 2,
      "lane": "support",
      "status": "active",
      "current_task": "Coordinating triage for JIRA-1234",
      "tasks_today": 8,
      "avg_response_ms": 520,
      "last_active": "2026-03-01T14:22:30Z"
    },
    {
      "name": "triage_agent",
      "display_name": "Ticket Triage Specialist",
      "human_name": "Kai Nakamura",
      "tier": 3,
      "lane": "support",
      "status": "active",
      "current_task": "Triaging JIRA-1234 for Acme Corp",
      "tasks_today": 5,
      "avg_response_ms": 2100,
      "last_active": "2026-03-01T14:21:00Z"
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
      "created_at": "2026-03-01T14:23:00Z",
      "processed_at": "2026-03-01T14:23:02Z"
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

### GET /dashboard/active-pipelines
Currently running agent pipeline executions (for the dashboard active pipelines strip).

**Response 200:**
```json
{
  "pipelines": [
    {
      "execution_id": "exec-001",
      "agent_id": "triage_agent",
      "agent_name": "Kai Nakamura",
      "tier": 3,
      "event_type": "jira_ticket_created",
      "customer_name": "Acme Corp",
      "current_stage": "think",
      "stages_completed": 2,
      "stages_total": 5,
      "started_at": "2026-03-01T14:23:00Z",
      "duration_ms": 1200
    },
    {
      "execution_id": "exec-002",
      "agent_id": "cso_orchestrator",
      "agent_name": "Naveen Kapoor",
      "tier": 1,
      "event_type": "daily_health_check",
      "customer_name": null,
      "current_stage": "act",
      "stages_completed": 3,
      "stages_total": 6,
      "started_at": "2026-03-01T14:22:00Z",
      "duration_ms": 3400
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
  "updated_at": "2026-03-01T14:00:00Z"
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
      "date": "2026-03-01",
      "score": 42,
      "risk_level": "high_risk",
      "risk_flags": ["3 overdue tickets", "Negative sentiment trend"]
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
      "calculated_at": "2026-03-01T09:00:00Z"
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
    { "date": "2026-03-01", "avg_score": 71.4, "at_risk_count": 5 }
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
      "sla_deadline": "2026-03-01T16:23:00Z",
      "sla_remaining_hours": 2.0,
      "sla_breaching": false,
      "created_at": "2026-03-01T14:23:00Z",
      "updated_at": "2026-03-01T14:23:02Z"
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
    "triaged_at": "2026-03-01T14:23:02Z"
  },
  "troubleshoot_result": null,
  "escalation_summary": null,
  "sla_deadline": "2026-03-01T16:23:00Z",
  "sla_remaining_hours": 2.0,
  "sla_breaching": false,
  "created_at": "2026-03-01T14:23:00Z",
  "updated_at": "2026-03-01T14:23:02Z",
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
Trigger AI triage on a ticket. Runs pipeline execution async.

**Response 202:**
```json
{
  "execution_id": "exec-010",
  "task_id": "celery-task-002",
  "message": "Pipeline triage initiated for JIRA-1234 (Agent: Kai Nakamura)",
  "status": "processing"
}
```

### POST /tickets/:id/troubleshoot
Trigger AI troubleshooting on a ticket. Runs pipeline execution async.

**Response 202:**
```json
{
  "execution_id": "exec-011",
  "task_id": "celery-task-003",
  "message": "Pipeline troubleshooting initiated for JIRA-1234 (Agent: Leo Petrov)",
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
      "summary": "Customer expressed concern about onboarding timeline delays.",
      "decisions": ["Extend onboarding by 2 weeks", "Weekly sync until go-live"],
      "action_items": [
        {
          "id": "ai-001",
          "task": "Schedule follow-up call",
          "owner": "Vignesh",
          "deadline": "2026-03-01",
          "status": "pending"
        }
      ],
      "risks": ["Possible escalation if timeline slips further"],
      "sentiment": "negative",
      "sentiment_score": -0.4,
      "key_topics": ["onboarding", "timeline", "deployment"],
      "customer_recap_draft": "Hi John,\n\nThank you for today's call...",
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
Trigger Fathom sync. Pulls historical meetings from real Fathom API.

**Query Params:** `since_days` (int, default 30)

**Response 202:**
```json
{
  "task_id": "celery-task-004",
  "message": "Fathom sync initiated for last 30 days",
  "status": "processing"
}
```

### GET /insights/sentiment-trend?days=30&customer_id=optional
Sentiment chart data.

**Response 200:**
```json
{
  "trend": [
    { "date": "2026-03-01", "avg_sentiment_score": -0.1, "call_count": 3 }
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
All agent profiles and statuses.

**Response 200:**
```json
{
  "agents": [
    {
      "name": "cso_orchestrator",
      "display_name": "CS Orchestrator",
      "human_name": "Naveen Kapoor",
      "tier": 1,
      "lane": null,
      "role": "CS Manager",
      "personality": "Strategic, composed, sees the big picture...",
      "traits": ["strategic_oversight", "quality_evaluation", "delegation", "customer_sentiment"],
      "tools": ["query_customer_db", "search_knowledge_base", "read_agent_output"],
      "manages": ["support_lead", "value_lead", "delivery_lead"],
      "reports_to": null,
      "status": "active",
      "current_task": "Delegating health_alert to Value Lane",
      "tasks_today": 12,
      "tasks_total": 1543,
      "avg_response_ms": 340,
      "success_rate": 0.98,
      "last_active": "2026-03-01T14:23:00Z"
    },
    {
      "name": "triage_agent",
      "display_name": "Ticket Triage Specialist",
      "human_name": "Kai Nakamura",
      "tier": 3,
      "lane": "support",
      "role": "Ticket Triage Specialist",
      "personality": "Fast, precise, pattern-recognizing...",
      "traits": ["confidence_scoring", "escalation_detection", "sla_awareness", "customer_sentiment"],
      "tools": ["get_ticket_details", "search_similar_tickets", "check_sla_status"],
      "manages": [],
      "reports_to": "support_lead",
      "status": "active",
      "current_task": "Triaging JIRA-1234 for Acme Corp",
      "tasks_today": 5,
      "tasks_total": 456,
      "avg_response_ms": 2100,
      "success_rate": 0.95,
      "last_active": "2026-03-01T14:21:00Z"
    }
  ]
}
```

### GET /agents/:name
Specific agent profile and status.

**Response 200:** Single agent from the above list.

### GET /agents/:name/logs?limit=20&offset=0
Agent activity logs.

**Response 200:**
```json
{
  "logs": [
    {
      "id": "log-001",
      "agent_name": "triage_agent",
      "agent_display_name": "Kai Nakamura",
      "event_type": "task_completed",
      "trigger_event": "jira_ticket_created",
      "customer_name": "Acme Corp",
      "input_summary": "New P2 ticket: Scan failure on subnet 10.0.1.x",
      "output_summary": "Classified as scan_failure, recommended P1 severity, suggested config check",
      "reasoning_summary": "Ticket mentions scan failure + specific subnet. Historical data shows similar issues resolved by config update.",
      "status": "completed",
      "duration_ms": 2340,
      "created_at": "2026-03-01T14:23:02Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### GET /agents/orchestration-flow?limit=20
Recent event routing timeline showing hierarchical delegation.

**Response 200:**
```json
{
  "flows": [
    {
      "event_id": "evt-001",
      "event_type": "jira_ticket_created",
      "source": "jira_webhook",
      "customer_name": "Acme Corp",
      "delegation_chain": [
        { "agent": "cso_orchestrator", "agent_name": "Naveen Kapoor", "action": "Delegated to Support Lane" },
        { "agent": "support_lead", "agent_name": "Rachel Torres", "action": "Assigned triage to Kai" },
        { "agent": "triage_agent", "agent_name": "Kai Nakamura", "action": "Triaged as P1 scan_failure" }
      ],
      "output": "Triaged as P1 scan_failure",
      "status": "completed",
      "total_duration_ms": 2680,
      "created_at": "2026-03-01T14:23:00Z"
    }
  ]
}
```

### POST /agents/:name/trigger
Manually trigger an agent pipeline execution. Async.

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
  "execution_id": "exec-020",
  "task_id": "celery-task-005",
  "agent_name": "Dr. Aisha Okafor",
  "message": "Pipeline execution initiated for Health Monitor Agent on Acme Corp",
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
  "created_at": "2026-03-01T14:23:00Z"
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
      "created_at": "2026-03-01T09:00:00Z"
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
      "title": "Weekly CS Digest — Feb 24 - Mar 1, 2026",
      "customer_name": null,
      "period_start": "2026-02-24",
      "period_end": "2026-03-01",
      "generated_at": "2026-03-02T09:00:00Z"
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
  "title": "Weekly CS Digest — Feb 24 - Mar 1, 2026",
  "customer_name": null,
  "period_start": "2026-02-24",
  "period_end": "2026-03-01",
  "content": {
    "summary": "This week saw 23 new tickets...",
    "health_overview": { "avg_score": 70, "at_risk": 4 },
    "ticket_summary": { "opened": 23, "resolved": 18, "sla_breaches": 2 },
    "call_summary": { "total_calls": 12, "action_items_created": 15 },
    "highlights": ["Acme Corp health dropped to 42", "Beta Financial renewal confirmed"],
    "recommendations": ["Schedule emergency sync with Acme", "Review Epsilon Insurance tickets"]
  },
  "generated_at": "2026-03-02T09:00:00Z"
}
```

### POST /reports/generate
Generate a new report. Async.

**Request:**
```json
{
  "report_type": "weekly_digest",
  "period_start": "2026-02-24",
  "period_end": "2026-03-01",
  "customer_id": null
}
```

**Response 202:**
```json
{
  "execution_id": "exec-030",
  "task_id": "celery-task-006",
  "message": "Generating Weekly Digest for Feb 24 - Mar 1 (Agent: Sofia Marquez)",
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
    { "date": "2026-03-01", "avg_score": 71.4 }
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
    { "agent": "triage_agent", "agent_name": "Kai Nakamura", "tasks_completed": 156, "avg_duration_ms": 1200 }
  ]
}
```

---

## 11. Pipeline Execution (v2)

### GET /v2/pipeline/active
Currently running pipeline executions across all agents.

**Response 200:**
```json
{
  "executions": [
    {
      "execution_id": "exec-001",
      "agent_id": "triage_agent",
      "agent_name": "Kai Nakamura",
      "tier": 3,
      "lane": "support",
      "event_id": "evt-001",
      "event_type": "jira_ticket_created",
      "customer_name": "Acme Corp",
      "pipeline_type": "tier_3_specialist",
      "current_stage": "think",
      "stages_completed": 2,
      "stages_total": 5,
      "started_at": "2026-03-01T14:23:00Z",
      "duration_ms": 1200,
      "status": "running"
    }
  ]
}
```

### GET /v2/pipeline/:execution_id
Full execution trace for a single pipeline run.

**Response 200:**
```json
{
  "execution_id": "exec-001",
  "agent_id": "triage_agent",
  "agent_name": "Kai Nakamura",
  "tier": 3,
  "lane": "support",
  "event_id": "evt-001",
  "event_type": "jira_ticket_created",
  "customer_name": "Acme Corp",
  "pipeline_type": "tier_3_specialist",
  "status": "completed",
  "started_at": "2026-03-01T14:23:00Z",
  "completed_at": "2026-03-01T14:23:08Z",
  "total_duration_ms": 8200,
  "total_tokens": 3450,
  "confidence": 0.92,
  "rounds": [
    {
      "stage_number": 1,
      "stage_name": "Task Perception",
      "stage_type": "perceive",
      "input_summary": "New P2 ticket from Acme Corp: Scan failure on subnet 10.0.1.x",
      "output_summary": "Task understood. Key elements: scan failure, specific subnet, P2 severity from reporter.",
      "tools_called": [],
      "duration_ms": 200,
      "tokens_used": 150,
      "status": "completed"
    },
    {
      "stage_number": 2,
      "stage_name": "Memory Retrieval",
      "stage_type": "retrieve",
      "input_summary": "Searching for similar past triage experiences",
      "output_summary": "Found 3 similar past triage runs. Most relevant: JIRA-987 (scan failure, resolved by config update).",
      "tools_called": [],
      "duration_ms": 340,
      "tokens_used": 0,
      "status": "completed",
      "metadata": { "memory_retrieved": 3 }
    },
    {
      "stage_number": 3,
      "stage_name": "Analysis",
      "stage_type": "think",
      "input_summary": "Analyzing ticket with customer context and past experience",
      "output_summary": "High confidence this is a scanner config issue. Similar to past JIRA-987. Recommending P1 due to production impact.",
      "tools_called": [
        {
          "tool_name": "query_customer_db",
          "arguments": { "customer_id": "cust-001" },
          "result_preview": "Acme Corp, Enterprise, health=42, 5 open tickets",
          "duration_ms": 120
        },
        {
          "tool_name": "search_similar_tickets",
          "arguments": { "query": "scan failure subnet" },
          "result_preview": "3 similar tickets found, top match: JIRA-987 (0.87 similarity)",
          "duration_ms": 340
        }
      ],
      "duration_ms": 4200,
      "tokens_used": 2100,
      "status": "completed"
    },
    {
      "stage_number": 4,
      "stage_name": "Execution",
      "stage_type": "act",
      "input_summary": "Producing triage result",
      "output_summary": "Triage complete: scan_failure, P1, confidence 0.92",
      "tools_called": [],
      "duration_ms": 2800,
      "tokens_used": 900,
      "status": "completed"
    },
    {
      "stage_number": 5,
      "stage_name": "Self-Reflection",
      "stage_type": "reflect",
      "input_summary": "Assessing triage quality",
      "output_summary": "Confidence: 0.92. Strong match with historical data. Minor gap: did not check deployment status.",
      "tools_called": [],
      "duration_ms": 660,
      "tokens_used": 300,
      "status": "completed"
    }
  ]
}
```

### GET /v2/pipeline/:execution_id/rounds
All rounds for a pipeline run (same as `rounds` array above, paginated).

**Query Params:** `limit` (int, default 20), `offset` (int, default 0)

**Response 200:**
```json
{
  "execution_id": "exec-001",
  "rounds": [ /* same shape as rounds array above */ ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

### GET /v2/pipeline/agent/:agent_id?limit=10&offset=0
Recent pipeline executions for a specific agent.

**Response 200:**
```json
{
  "agent_id": "triage_agent",
  "agent_name": "Kai Nakamura",
  "executions": [
    {
      "execution_id": "exec-001",
      "event_type": "jira_ticket_created",
      "customer_name": "Acme Corp",
      "status": "completed",
      "total_duration_ms": 8200,
      "confidence": 0.92,
      "stages_completed": 5,
      "started_at": "2026-03-01T14:23:00Z"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

---

## 12. Messages (v2)

### GET /v2/messages?limit=50&offset=0
Recent inter-agent messages.

**Query Params:**
- `message_type` (string) — task_assignment | deliverable | request | escalation | feedback
- `agent_id` (string) — filter by from_agent or to_agent
- `event_id` (uuid) — filter by related event
- `lane` (string) — support | value | delivery
- `limit` (int, default 50)
- `offset` (int, default 0)

**Response 200:**
```json
{
  "messages": [
    {
      "id": "msg-001",
      "thread_id": "msg-001",
      "parent_id": null,
      "from_agent": "cso_orchestrator",
      "from_name": "Naveen Kapoor",
      "to_agent": "support_lead",
      "to_name": "Rachel Torres",
      "message_type": "task_assignment",
      "direction": "down",
      "content": "New P2 ticket from Acme Corp needs triage. Customer health is already at 42 — handle with priority.",
      "priority": 7,
      "event_id": "evt-001",
      "customer_name": "Acme Corp",
      "status": "completed",
      "created_at": "2026-03-01T14:23:00Z",
      "reply_count": 2
    },
    {
      "id": "msg-002",
      "thread_id": "msg-001",
      "parent_id": "msg-001",
      "from_agent": "support_lead",
      "from_name": "Rachel Torres",
      "to_agent": "triage_agent",
      "to_name": "Kai Nakamura",
      "message_type": "task_assignment",
      "direction": "down",
      "content": "Kai, triage this Acme Corp ticket immediately. P2 reported but customer health is critical. Check if severity should be upgraded.",
      "priority": 8,
      "event_id": "evt-001",
      "customer_name": "Acme Corp",
      "status": "completed",
      "created_at": "2026-03-01T14:23:01Z",
      "reply_count": 1
    }
  ],
  "total": 240,
  "limit": 50,
  "offset": 0
}
```

### GET /v2/messages/thread/:thread_id
Full message thread.

**Response 200:**
```json
{
  "thread_id": "msg-001",
  "event_id": "evt-001",
  "customer_name": "Acme Corp",
  "messages": [
    {
      "id": "msg-001",
      "from_agent": "cso_orchestrator",
      "from_name": "Naveen Kapoor",
      "to_agent": "support_lead",
      "to_name": "Rachel Torres",
      "message_type": "task_assignment",
      "direction": "down",
      "content": "New P2 ticket from Acme Corp needs triage...",
      "priority": 7,
      "created_at": "2026-03-01T14:23:00Z"
    },
    {
      "id": "msg-002",
      "from_agent": "support_lead",
      "from_name": "Rachel Torres",
      "to_agent": "triage_agent",
      "to_name": "Kai Nakamura",
      "message_type": "task_assignment",
      "direction": "down",
      "content": "Kai, triage this immediately...",
      "priority": 8,
      "created_at": "2026-03-01T14:23:01Z"
    },
    {
      "id": "msg-003",
      "from_agent": "triage_agent",
      "from_name": "Kai Nakamura",
      "to_agent": "support_lead",
      "to_name": "Rachel Torres",
      "message_type": "deliverable",
      "direction": "up",
      "content": "Triage complete. Classified as scan_failure, upgrading to P1. Confidence: 0.92. Suggested action: check scanner config for subnet range.",
      "priority": 7,
      "created_at": "2026-03-01T14:23:08Z"
    }
  ],
  "total_messages": 3
}
```

### GET /v2/messages/agent/:agent_id?limit=20&offset=0
Messages sent to or from a specific agent.

**Response 200:** Same shape as `GET /v2/messages` but filtered.

### GET /v2/messages/event/:event_id
All messages related to a specific event's processing.

**Response 200:** Same shape as `GET /v2/messages` but filtered by event_id.

---

## 13. Memory (v2)

### GET /v2/memory/:agent_id/episodic?limit=20&offset=0
An agent's episodic memories (past execution diary).

**Query Params:**
- `customer_id` (uuid) — filter by customer
- `importance_min` (int) — minimum importance (1-10)
- `limit` (int, default 20)
- `offset` (int, default 0)

**Response 200:**
```json
{
  "agent_id": "triage_agent",
  "agent_name": "Kai Nakamura",
  "memories": [
    {
      "id": "mem-001",
      "content": "Triaged Acme Corp ticket JIRA-1234 as P1 scan_failure. High confidence (0.92). Found 3 similar historical tickets. Key insight: subnet config issues are recurring for this customer.",
      "customer_name": "Acme Corp",
      "event_type": "jira_ticket_created",
      "execution_id": "exec-001",
      "importance": 7,
      "timestamp": "2026-03-01T14:23:08Z"
    }
  ],
  "total": 30,
  "limit": 20,
  "offset": 0
}
```

### GET /v2/memory/:agent_id/working
An agent's current working memory (active scratchpad during pipeline run).

**Response 200:**
```json
{
  "agent_id": "triage_agent",
  "agent_name": "Kai Nakamura",
  "is_active": true,
  "execution_id": "exec-050",
  "entries": [
    { "key": "current_task", "value": "Triage JIRA-1250 for Beta Financial" },
    { "key": "customer_context", "value": { "name": "Beta Financial", "health": 78, "tier": "enterprise" } },
    { "key": "similar_tickets_found", "value": 2 },
    { "key": "tool_outputs", "value": [{ "tool": "search_similar_tickets", "result_count": 2 }] }
  ]
}
```

Returns empty `entries` and `is_active: false` if the agent has no active pipeline run.

### GET /v2/memory/knowledge/:lane?limit=20&offset=0
Knowledge pool for a specific lane.

**Query Params:**
- `lane` (string, required) — support | value | delivery | global
- `tags` (string, comma-separated) — filter by tags
- `importance_min` (int) — minimum importance
- `limit` (int, default 20)
- `offset` (int, default 0)

**Response 200:**
```json
{
  "lane": "value",
  "entries": [
    {
      "id": "know-001",
      "content": "Acme Corp shows a strong correlation between deployment events and health score drops. Every deployment in the last 6 months was followed by a 10-15 point health decline within 48 hours.",
      "agent_id": "health_monitor_agent",
      "agent_name": "Dr. Aisha Okafor",
      "tags": ["health-correlation", "deployment-risk", "acme-corp"],
      "importance": 8,
      "knowledge_type": "customer_pattern",
      "customer_name": "Acme Corp",
      "timestamp": "2026-02-28T09:00:00Z"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

### GET /v2/memory/search
Cross-memory semantic search across all tiers.

**Query Params:**
- `q` (string, required) — semantic search query
- `memory_type` (string) — episodic | knowledge | all (default: all)
- `agent_id` (string) — filter by agent
- `lane` (string) — filter by lane (for knowledge)
- `limit` (int, default 10)

**Response 200:**
```json
{
  "query": "customer health declining after deployment",
  "results": [
    {
      "type": "knowledge",
      "id": "know-001",
      "content": "Acme Corp shows a strong correlation between deployment events and health score drops...",
      "agent_name": "Dr. Aisha Okafor",
      "lane": "value",
      "importance": 8,
      "relevance_score": 0.91,
      "combined_score": 0.87,
      "timestamp": "2026-02-28T09:00:00Z"
    },
    {
      "type": "episodic",
      "id": "mem-015",
      "content": "Analyzed Gamma Telecom health drop from 72 to 55 following v4.2 deployment...",
      "agent_name": "Dr. Aisha Okafor",
      "importance": 6,
      "relevance_score": 0.78,
      "combined_score": 0.72,
      "timestamp": "2026-02-20T10:00:00Z"
    }
  ]
}
```

---

## 14. Hierarchy (v2)

### GET /v2/hierarchy
Full organizational structure tree.

**Response 200:**
```json
{
  "organization": "HivePro CS Control Plane",
  "tiers": [
    {
      "tier": 1,
      "name": "Supervisor",
      "agents": [
        {
          "id": "cso_orchestrator",
          "name": "Naveen Kapoor",
          "role": "CS Manager",
          "status": "active",
          "manages": ["support_lead", "value_lead", "delivery_lead"]
        }
      ]
    },
    {
      "tier": 2,
      "name": "Lane Leads",
      "agents": [
        {
          "id": "support_lead",
          "name": "Rachel Torres",
          "role": "Support Operations Lead",
          "lane": "support",
          "status": "active",
          "reports_to": "cso_orchestrator",
          "manages": ["triage_agent", "troubleshooter_agent", "escalation_agent"]
        },
        {
          "id": "value_lead",
          "name": "Damon Reeves",
          "role": "Value & Insights Lead",
          "lane": "value",
          "status": "idle",
          "reports_to": "cso_orchestrator",
          "manages": ["health_monitor_agent", "call_intel_agent", "qbr_agent"]
        },
        {
          "id": "delivery_lead",
          "name": "Priya Mehta",
          "role": "Delivery Operations Lead",
          "lane": "delivery",
          "status": "idle",
          "reports_to": "cso_orchestrator",
          "manages": ["sow_agent", "deployment_intel_agent"]
        }
      ]
    },
    {
      "tier": 3,
      "name": "Specialists",
      "agents": [
        {
          "id": "triage_agent",
          "name": "Kai Nakamura",
          "role": "Ticket Triage Specialist",
          "lane": "support",
          "status": "active",
          "reports_to": "support_lead"
        }
      ]
    },
    {
      "tier": 4,
      "name": "Foundation",
      "agents": [
        {
          "id": "customer_memory",
          "name": "Atlas",
          "role": "Customer Memory Manager",
          "status": "active",
          "reports_to": null
        }
      ]
    }
  ],
  "lanes": {
    "support": { "lead": "support_lead", "specialists": ["triage_agent", "troubleshooter_agent", "escalation_agent"] },
    "value": { "lead": "value_lead", "specialists": ["health_monitor_agent", "call_intel_agent", "qbr_agent"] },
    "delivery": { "lead": "delivery_lead", "specialists": ["sow_agent", "deployment_intel_agent"] }
  }
}
```

### GET /v2/hierarchy/agents
All agent profiles with stats. Same as `GET /agents` (v1) but scoped under v2 path.

**Response 200:** Same shape as `GET /agents`.

### GET /v2/hierarchy/agents/:agent_id
Single agent profile with full detail.

**Response 200:** Single agent from `GET /agents` list.

---

## 15. Workflows (v2)

### GET /v2/workflows
All workflow definitions from YAML config.

**Response 200:**
```json
{
  "workflows": [
    {
      "name": "ticket_workflow",
      "description": "Handles new Jira tickets through triage and optional troubleshooting",
      "trigger_events": ["jira_ticket_created"],
      "steps": [
        { "agent": "cso_orchestrator", "action": "Analyze and delegate to Support Lane" },
        { "agent": "support_lead", "action": "Assign triage to specialist" },
        { "agent": "triage_agent", "action": "Classify, assess severity, find similar tickets" },
        { "agent": "troubleshooter_agent", "action": "Root cause analysis (if severity >= P2)", "condition": "severity >= P2" },
        { "agent": "escalation_agent", "action": "Escalation summary (if escalation needed)", "condition": "escalation_detected" }
      ]
    },
    {
      "name": "call_workflow",
      "description": "Processes Fathom call recordings through analysis",
      "trigger_events": ["fathom_recording_ready"],
      "steps": [
        { "agent": "cso_orchestrator", "action": "Delegate to Value Lane" },
        { "agent": "value_lead", "action": "Assign call analysis" },
        { "agent": "call_intel_agent", "action": "Extract summary, sentiment, action items" }
      ]
    },
    {
      "name": "health_workflow",
      "description": "Daily health monitoring and alerting",
      "trigger_events": ["daily_health_check"],
      "steps": [
        { "agent": "cso_orchestrator", "action": "Delegate health check to Value Lane" },
        { "agent": "value_lead", "action": "Coordinate health analysis" },
        { "agent": "health_monitor_agent", "action": "Calculate scores, flag risks" },
        { "agent": "escalation_agent", "action": "Generate alerts for critical drops", "condition": "score_drop > 15" }
      ]
    }
  ]
}
```

### GET /v2/workflows/active
Currently running workflow instances.

**Response 200:**
```json
{
  "instances": [
    {
      "instance_id": "wf-inst-001",
      "workflow_name": "ticket_workflow",
      "event_id": "evt-001",
      "customer_name": "Acme Corp",
      "current_step": 3,
      "total_steps": 5,
      "current_agent": "triage_agent",
      "status": "running",
      "started_at": "2026-03-01T14:23:00Z"
    }
  ]
}
```

### GET /v2/workflows/:instance_id/status
Status of a specific workflow instance.

**Response 200:**
```json
{
  "instance_id": "wf-inst-001",
  "workflow_name": "ticket_workflow",
  "event_id": "evt-001",
  "customer_name": "Acme Corp",
  "status": "completed",
  "started_at": "2026-03-01T14:23:00Z",
  "completed_at": "2026-03-01T14:23:12Z",
  "total_duration_ms": 12000,
  "steps": [
    { "step": 1, "agent": "cso_orchestrator", "agent_name": "Naveen Kapoor", "status": "completed", "duration_ms": 800 },
    { "step": 2, "agent": "support_lead", "agent_name": "Rachel Torres", "status": "completed", "duration_ms": 600 },
    { "step": 3, "agent": "triage_agent", "agent_name": "Kai Nakamura", "status": "completed", "duration_ms": 8200 },
    { "step": 4, "agent": "troubleshooter_agent", "agent_name": "Leo Petrov", "status": "skipped", "condition": "severity >= P2" },
    { "step": 5, "agent": "escalation_agent", "agent_name": "Maya Santiago", "status": "skipped", "condition": "escalation_detected" }
  ]
}
```

---

## 16. Webhooks

### POST /webhooks/fathom [PUBLIC — verified by HMAC]
Fathom webhook receiver. Receives meeting data when a new recording is ready.

**Verification:** HMAC-SHA256 signature in `X-Fathom-Signature` header, verified against `FATHOM_WEBHOOK_SECRET`.

**Request (from Fathom):**
```json
{
  "recording_id": "rec-abc123",
  "title": "Acme Corp Weekly Sync",
  "url": "https://fathom.video/recordings/abc123",
  "recorded_by": { "email": "vignesh@hivepro.com" },
  "calendar_invitees": [
    { "email": "john@acme.com", "name": "John Doe" },
    { "email": "vignesh@hivepro.com", "name": "Vignesh" }
  ],
  "default_summary": "Discussion about onboarding timeline...",
  "transcript": [ /* transcript segments */ ],
  "action_items": [
    { "text": "Schedule follow-up call", "assignee": "Vignesh" }
  ]
}
```

**Response 200:**
```json
{
  "status": "received",
  "event_id": "evt-050"
}
```

---

## 17. WebSocket

### WS /ws
Real-time event stream. Connect after login with JWT.

**Connection:** `ws://localhost:8000/api/ws?token={access_token}`

**Server → Client Events:**

```json
// Agent status change
{
  "type": "agent_status",
  "data": {
    "agent": "triage_agent",
    "agent_name": "Kai Nakamura",
    "tier": 3,
    "status": "active",
    "task": "Triaging JIRA-1234 for Acme Corp"
  }
}

// Event processed
{
  "type": "event_processed",
  "data": {
    "event_id": "evt-001",
    "event_type": "jira_ticket_created",
    "customer": "Acme Corp",
    "routed_to": "triage_agent",
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

**New Pipeline Events (v2):**

```json
// Pipeline stage started
{
  "type": "pipeline:stage_started",
  "data": {
    "execution_id": "exec-001",
    "agent_id": "triage_agent",
    "agent_name": "Kai Nakamura",
    "tier": 3,
    "stage_name": "Analysis",
    "stage_type": "think",
    "stage_number": 3,
    "customer_name": "Acme Corp"
  }
}

// Pipeline stage completed
{
  "type": "pipeline:stage_completed",
  "data": {
    "execution_id": "exec-001",
    "agent_id": "triage_agent",
    "agent_name": "Kai Nakamura",
    "stage_name": "Analysis",
    "stage_type": "think",
    "duration_ms": 4200,
    "tokens_used": 2100,
    "tools_called": ["query_customer_db", "search_similar_tickets"]
  }
}

// Pipeline tool called
{
  "type": "pipeline:tool_called",
  "data": {
    "execution_id": "exec-001",
    "agent_id": "triage_agent",
    "agent_name": "Kai Nakamura",
    "tool_name": "search_similar_tickets",
    "arguments": { "query": "scan failure subnet" },
    "result_preview": "3 similar tickets found",
    "duration_ms": 340
  }
}
```

**New Delegation Events (v2):**

```json
// Task assigned (down the hierarchy)
{
  "type": "delegation:task_assigned",
  "data": {
    "message_id": "msg-001",
    "from_agent": "cso_orchestrator",
    "from_name": "Naveen Kapoor",
    "to_agent": "support_lead",
    "to_name": "Rachel Torres",
    "content_preview": "New P2 ticket from Acme Corp needs triage...",
    "priority": 7,
    "event_id": "evt-001"
  }
}

// Deliverable returned (up the hierarchy)
{
  "type": "delegation:deliverable",
  "data": {
    "message_id": "msg-003",
    "from_agent": "triage_agent",
    "from_name": "Kai Nakamura",
    "to_agent": "support_lead",
    "to_name": "Rachel Torres",
    "content_preview": "Triage complete. scan_failure, P1, confidence 0.92",
    "event_id": "evt-001"
  }
}

// Escalation
{
  "type": "delegation:escalation",
  "data": {
    "message_id": "msg-010",
    "from_agent": "escalation_agent",
    "from_name": "Maya Santiago",
    "to_agent": "support_lead",
    "to_name": "Rachel Torres",
    "content_preview": "ESCALATION: Acme Corp threatening churn — renewal in 45 days",
    "priority": 9,
    "customer_name": "Acme Corp"
  }
}
```

**New Memory Event (v2):**

```json
// Knowledge published
{
  "type": "memory:knowledge_published",
  "data": {
    "agent_id": "call_intel_agent",
    "agent_name": "Jordan Ellis",
    "lane": "value",
    "content_preview": "Acme Corp mentioned competitor CrowdStrike in recent call...",
    "tags": ["competitor-mention", "acme-corp"],
    "importance": 8
  }
}
```

---

## 18. Error Responses

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

## 19. Common Headers

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
