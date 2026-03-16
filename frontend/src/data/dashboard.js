// Seed: Dashboard stats, agents summary, events, quick health

export const seedDashboardStats = {
  total_customers: 10,
  healthy: 4,
  watch: 3,
  high_risk: 3,
  avg_health: 64.2,
  total_agents: 13,
  active_agents: 8,
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
  // Tier 1: Supervisor
  { id: 'agent-01', agent_key: 'cso_orchestrator', name: 'cso_orchestrator', human_name: 'Naveen Kapoor', display_name: 'CS Orchestrator', tier: 1, lane: 'control', role: 'CS Manager', status: 'active', tasks_today: 15, manages: ['support_lead', 'value_lead', 'delivery_lead'] },
  // Tier 2: Lane Leads
  { id: 'agent-02', agent_key: 'support_lead', name: 'support_lead', human_name: 'Rachel Torres', display_name: 'Support Lead', tier: 2, lane: 'support', role: 'Support Operations Lead', status: 'active', tasks_today: 12, manages: ['triage_agent', 'troubleshooter_agent', 'escalation_agent'] },
  { id: 'agent-03', agent_key: 'value_lead', name: 'value_lead', human_name: 'Damon Reeves', display_name: 'Value Lead', tier: 2, lane: 'value', role: 'Value & Insights Lead', status: 'active', tasks_today: 9, manages: ['health_monitor_agent', 'fathom_agent', 'qbr_agent'] },
  { id: 'agent-04', agent_key: 'delivery_lead', name: 'delivery_lead', human_name: 'Priya Mehta', display_name: 'Delivery Lead', tier: 2, lane: 'delivery', role: 'Delivery Operations Lead', status: 'idle', tasks_today: 6, manages: ['sow_agent', 'deployment_intel_agent'] },
  // Tier 3: Specialists — Support
  { id: 'agent-05', agent_key: 'triage_agent', name: 'triage_agent', human_name: 'Kai Nakamura', display_name: 'Ticket Triage', tier: 3, lane: 'support', role: 'Triage Specialist', status: 'active', tasks_today: 18, manages: [] },
  { id: 'agent-06', agent_key: 'troubleshooter_agent', name: 'troubleshooter_agent', human_name: 'Leo Petrov', display_name: 'Troubleshooter', tier: 3, lane: 'support', role: 'Troubleshooting Engineer', status: 'active', tasks_today: 11, manages: [] },
  { id: 'agent-07', agent_key: 'escalation_agent', name: 'escalation_agent', human_name: 'Maya Santiago', display_name: 'Escalation Manager', tier: 3, lane: 'support', role: 'Escalation Manager', status: 'idle', tasks_today: 4, manages: [] },
  // Tier 3: Specialists — Value
  { id: 'agent-08', agent_key: 'health_monitor_agent', name: 'health_monitor_agent', human_name: 'Dr. Aisha Okafor', display_name: 'Health Monitor', tier: 3, lane: 'value', role: 'Health Analyst', status: 'active', tasks_today: 14, manages: [] },
  { id: 'agent-09', agent_key: 'fathom_agent', name: 'fathom_agent', human_name: 'Jordan Ellis', display_name: 'Fathom Agent', tier: 3, lane: 'value', role: 'Fathom Agent', status: 'active', tasks_today: 8, manages: [] },
  { id: 'agent-10', agent_key: 'qbr_agent', name: 'qbr_agent', human_name: 'Sofia Marquez', display_name: 'QBR Specialist', tier: 3, lane: 'value', role: 'QBR Specialist', status: 'idle', tasks_today: 2, manages: [] },
  // Tier 3: Specialists — Delivery
  { id: 'agent-11', agent_key: 'sow_agent', name: 'sow_agent', human_name: 'Ethan Brooks', display_name: 'SOW Specialist', tier: 3, lane: 'delivery', role: 'SOW Specialist', status: 'processing', tasks_today: 5, manages: [] },
  { id: 'agent-12', agent_key: 'deployment_intel_agent', name: 'deployment_intel_agent', human_name: 'Zara Kim', display_name: 'Deployment Intel', tier: 3, lane: 'delivery', role: 'Deployment Analyst', status: 'idle', tasks_today: 3, manages: [] },
  // Tier 4: Foundation
  { id: 'agent-13', agent_key: 'customer_memory', name: 'customer_memory', human_name: 'Atlas', display_name: 'Customer Memory', tier: 4, lane: 'control', role: 'Memory Manager', status: 'active', tasks_today: 20, manages: [] },
]

export const seedEvents = [
  { id: 'evt-01', type: 'jira_ticket_created', message: 'New P1 ticket from Acme Corp — Login failures across all regions', timestamp: '2026-02-28T09:45:00Z', customer_id: 'cust-001' },
  { id: 'evt-02', type: 'fathom_call_processed', message: 'Fathom insights extracted for Beta Financial QBR prep call', timestamp: '2026-02-28T09:30:00Z', customer_id: 'cust-002' },
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
]
