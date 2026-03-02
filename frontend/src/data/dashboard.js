// Seed: Dashboard stats, agents summary, events, quick health

export const seedDashboardStats = {
  total_customers: 10,
  healthy: 4,
  watch: 3,
  high_risk: 3,
  avg_health: 64.2,
  total_agents: 10,
  active_agents: 7,
  total_tickets_open: 50,
  tickets_resolved_today: 6,
  calls_today: 4,
  events_today: 18,
  trend: {
    health: +2.3,
    tickets: -5,
    calls: +1,
  },
}

export const seedAgents = [
  { id: 'agent-01', name: 'CS Orchestrator', status: 'active', lane: 'control', tasks_today: 42, latency_ms: 120 },
  { id: 'agent-02', name: 'Memory Agent', status: 'active', lane: 'control', tasks_today: 38, latency_ms: 85 },
  { id: 'agent-03', name: 'Health Monitor', status: 'active', lane: 'control', tasks_today: 20, latency_ms: 200 },
  { id: 'agent-04', name: 'Escalation Agent', status: 'idle', lane: 'control', tasks_today: 5, latency_ms: 150 },
  { id: 'agent-05', name: 'Call Intelligence', status: 'active', lane: 'value', tasks_today: 12, latency_ms: 3200 },
  { id: 'agent-06', name: 'QBR Generator', status: 'idle', lane: 'value', tasks_today: 2, latency_ms: 8500 },
  { id: 'agent-07', name: 'Ticket Triage', status: 'active', lane: 'support', tasks_today: 28, latency_ms: 450 },
  { id: 'agent-08', name: 'Troubleshooter', status: 'active', lane: 'support', tasks_today: 15, latency_ms: 2800 },
  { id: 'agent-09', name: 'SOW Analyzer', status: 'active', lane: 'delivery', tasks_today: 8, latency_ms: 1600 },
  { id: 'agent-10', name: 'Deployment Intel', status: 'idle', lane: 'delivery', tasks_today: 3, latency_ms: 900 },
]

export const seedEvents = [
  { id: 'evt-01', type: 'jira_ticket_created', message: 'New P1 ticket from Acme Corp — Login failures across all regions', timestamp: '2026-02-28T09:45:00Z', customer_id: 'cust-001' },
  { id: 'evt-02', type: 'fathom_call_processed', message: 'Call intel extracted for Beta Financial QBR prep call', timestamp: '2026-02-28T09:30:00Z', customer_id: 'cust-002' },
  { id: 'evt-03', type: 'daily_health_check', message: 'Epsilon Insurance health dropped to 38 — escalation triggered', timestamp: '2026-02-28T09:15:00Z', customer_id: 'cust-005' },
  { id: 'evt-04', type: 'jira_ticket_created', message: 'P3 ticket from Gamma Telecom — Dashboard slow loading', timestamp: '2026-02-28T09:00:00Z', customer_id: 'cust-003' },
  { id: 'evt-05', type: 'alert_fired', message: 'Iota Defense SLA breach in 2 hours — 3 P2 tickets unresolved', timestamp: '2026-02-28T08:50:00Z', customer_id: 'cust-009' },
  { id: 'evt-06', type: 'fathom_call_processed', message: 'Sentiment analysis: Negative drift detected in Acme Corp calls', timestamp: '2026-02-28T08:30:00Z', customer_id: 'cust-001' },
  { id: 'evt-07', type: 'daily_health_check', message: 'Delta Health — health stable at 91, no action needed', timestamp: '2026-02-28T08:15:00Z', customer_id: 'cust-004' },
  { id: 'evt-08', type: 'jira_ticket_created', message: 'P2 ticket from Theta Energy — API rate limiting errors', timestamp: '2026-02-28T08:00:00Z', customer_id: 'cust-008' },
  { id: 'evt-09', type: 'new_alert', message: 'Zeta Retail approaching SLA warning zone — 2 tickets aging', timestamp: '2026-02-28T07:45:00Z', customer_id: 'cust-006' },
  { id: 'evt-10', type: 'fathom_call_processed', message: 'Eta Pharma compliance review call — 4 action items extracted', timestamp: '2026-02-28T07:30:00Z', customer_id: 'cust-007' },
  { id: 'evt-11', type: 'jira_ticket_created', message: 'P4 ticket from Kappa Logistics — Feature request: bulk export', timestamp: '2026-02-28T07:15:00Z', customer_id: 'cust-010' },
  { id: 'evt-12', type: 'daily_health_check', message: 'Gamma Telecom health improved slightly — 53 → 55', timestamp: '2026-02-28T07:00:00Z', customer_id: 'cust-003' },
  { id: 'evt-13', type: 'alert_fired', message: 'Acme Corp renewal risk — health below 45 for 7+ days', timestamp: '2026-02-28T06:45:00Z', customer_id: 'cust-001' },
  { id: 'evt-14', type: 'jira_ticket_created', message: 'P1 ticket from Iota Defense — Data sync failure in secure zone', timestamp: '2026-02-28T06:30:00Z', customer_id: 'cust-009' },
  { id: 'evt-15', type: 'fathom_call_processed', message: 'Kappa Logistics onboarding check-in — positive sentiment', timestamp: '2026-02-28T06:15:00Z', customer_id: 'cust-010' },
  { id: 'evt-16', type: 'new_alert', message: 'Epsilon Insurance — 12 open tickets, capacity review needed', timestamp: '2026-02-28T06:00:00Z', customer_id: 'cust-005' },
  { id: 'evt-17', type: 'daily_health_check', message: 'Beta Financial — health stable at 88, champion engaged', timestamp: '2026-02-28T05:45:00Z', customer_id: 'cust-002' },
  { id: 'evt-18', type: 'jira_ticket_created', message: 'P3 ticket from Eta Pharma — Report formatting issue', timestamp: '2026-02-28T05:30:00Z', customer_id: 'cust-007' },
  { id: 'evt-19', type: 'fathom_call_processed', message: 'Theta Energy quarterly review — mixed sentiment, 6 items', timestamp: '2026-02-28T05:15:00Z', customer_id: 'cust-008' },
  { id: 'evt-20', type: 'daily_health_check', message: 'Iota Defense health dropped: 48 → 44 — monitoring', timestamp: '2026-02-28T05:00:00Z', customer_id: 'cust-009' },
]

export const seedQuickHealth = [
  { id: 'cust-001', company_name: 'Acme Corp', health_score: 42, risk_level: 'high_risk', trend: -3 },
  { id: 'cust-002', company_name: 'Beta Financial', health_score: 88, risk_level: 'healthy', trend: +2 },
  { id: 'cust-003', company_name: 'Gamma Telecom', health_score: 55, risk_level: 'watch', trend: +1 },
  { id: 'cust-004', company_name: 'Delta Health', health_score: 91, risk_level: 'healthy', trend: 0 },
  { id: 'cust-005', company_name: 'Epsilon Insurance', health_score: 38, risk_level: 'high_risk', trend: -5 },
  { id: 'cust-006', company_name: 'Zeta Retail', health_score: 67, risk_level: 'watch', trend: -1 },
  { id: 'cust-007', company_name: 'Eta Pharma', health_score: 85, risk_level: 'healthy', trend: +1 },
  { id: 'cust-008', company_name: 'Theta Energy', health_score: 72, risk_level: 'healthy', trend: -2 },
  { id: 'cust-009', company_name: 'Iota Defense', health_score: 44, risk_level: 'high_risk', trend: -4 },
  { id: 'cust-010', company_name: 'Kappa Logistics', health_score: 60, risk_level: 'watch', trend: +2 },
  { id: 'cust-002', company_name: 'Beta Financial', health_score: 88, risk_level: 'healthy', trend: +2 },
  { id: 'cust-004', company_name: 'Delta Health', health_score: 91, risk_level: 'healthy', trend: 0 },
]
