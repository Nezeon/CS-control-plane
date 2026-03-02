// Seed: 50 tickets across 10 customers — deterministic

const NOW = Date.now()
const HOUR = 3600000
const DAY = 86400000

const mkDate = (daysAgo, hoursOffset = 0) =>
  new Date(NOW - daysAgo * DAY + hoursOffset * HOUR).toISOString()

const mkSla = (hoursFromNow) =>
  new Date(NOW + hoursFromNow * HOUR).toISOString()

export const seedTickets = [
  // Acme Corp — 8 tickets (high_risk)
  { id: 'TKT-1001', jira_key: 'ACME-401', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'Login failures across all regions after patch deployment', severity: 'P1', status: 'open', type: 'incident', assignee: 'Sarah Chen', sla_deadline: mkSla(2), created_at: mkDate(0, -3), triage_result: { confidence: 0.92, suggested_agent: 'troubleshooter', root_cause_hint: 'Auth service timeout after v3.2.1 deploy', recommended_action: 'Rollback v3.2.1 and investigate auth token expiry' } },
  { id: 'TKT-1002', jira_key: 'ACME-402', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'Dashboard widgets not loading for admin users', severity: 'P2', status: 'in_progress', type: 'bug', assignee: 'Marcus Webb', sla_deadline: mkSla(6), created_at: mkDate(1) },
  { id: 'TKT-1003', jira_key: 'ACME-403', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'API response time degraded > 5s on /reports endpoint', severity: 'P2', status: 'open', type: 'incident', assignee: null, sla_deadline: mkSla(4), created_at: mkDate(1, -6) },
  { id: 'TKT-1004', jira_key: 'ACME-404', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'Request: Add SSO support for Okta', severity: 'P3', status: 'open', type: 'feature_request', assignee: 'Sarah Chen', sla_deadline: mkSla(72), created_at: mkDate(5) },
  { id: 'TKT-1005', jira_key: 'ACME-405', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'Export CSV includes deleted records', severity: 'P3', status: 'resolved', type: 'bug', assignee: 'Marcus Webb', sla_deadline: mkSla(-24), created_at: mkDate(8), resolved_at: mkDate(6) },
  { id: 'TKT-1006', jira_key: 'ACME-406', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'Documentation unclear on webhook setup', severity: 'P4', status: 'open', type: 'support', assignee: null, sla_deadline: mkSla(120), created_at: mkDate(3) },
  { id: 'TKT-1007', jira_key: 'ACME-407', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'Notification emails going to spam folder', severity: 'P3', status: 'in_progress', type: 'bug', assignee: 'Sarah Chen', sla_deadline: mkSla(24), created_at: mkDate(2) },
  { id: 'TKT-1008', jira_key: 'ACME-408', customer_id: 'cust-001', customer_name: 'Acme Corp', summary: 'Request bulk user import via CSV', severity: 'P4', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(168), created_at: mkDate(10) },

  // Beta Financial — 1 ticket (healthy)
  { id: 'TKT-2001', jira_key: 'BETA-201', customer_id: 'cust-002', customer_name: 'Beta Financial', summary: 'Minor UI alignment issue on compliance dashboard', severity: 'P4', status: 'open', type: 'bug', assignee: 'Marcus Webb', sla_deadline: mkSla(120), created_at: mkDate(2) },

  // Gamma Telecom — 5 tickets (watch)
  { id: 'TKT-3001', jira_key: 'GAMA-301', customer_id: 'cust-003', customer_name: 'Gamma Telecom', summary: 'Dashboard slow loading — 10s+ page load times', severity: 'P2', status: 'open', type: 'incident', assignee: 'Sarah Chen', sla_deadline: mkSla(8), created_at: mkDate(0, -5), triage_result: { confidence: 0.85, suggested_agent: 'troubleshooter', root_cause_hint: 'N+1 query on customer_metrics table', recommended_action: 'Add eager loading for metrics relation' } },
  { id: 'TKT-3002', jira_key: 'GAMA-302', customer_id: 'cust-003', customer_name: 'Gamma Telecom', summary: 'Webhook delivery failures — 30% failure rate', severity: 'P2', status: 'in_progress', type: 'bug', assignee: 'Marcus Webb', sla_deadline: mkSla(5), created_at: mkDate(1, -8) },
  { id: 'TKT-3003', jira_key: 'GAMA-303', customer_id: 'cust-003', customer_name: 'Gamma Telecom', summary: 'Feature: Multi-region deployment support', severity: 'P3', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(96), created_at: mkDate(7) },
  { id: 'TKT-3004', jira_key: 'GAMA-304', customer_id: 'cust-003', customer_name: 'Gamma Telecom', summary: 'Report scheduling not triggering on weekends', severity: 'P3', status: 'resolved', type: 'bug', assignee: 'Sarah Chen', sla_deadline: mkSla(-48), created_at: mkDate(12), resolved_at: mkDate(9) },
  { id: 'TKT-3005', jira_key: 'GAMA-305', customer_id: 'cust-003', customer_name: 'Gamma Telecom', summary: 'Need API docs for v3 endpoints', severity: 'P4', status: 'open', type: 'support', assignee: null, sla_deadline: mkSla(168), created_at: mkDate(4) },

  // Delta Health — 0 open (healthy)

  // Epsilon Insurance — 12 tickets (high_risk)
  { id: 'TKT-5001', jira_key: 'EPSI-501', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'Critical: Data loss in claims processing module', severity: 'P1', status: 'open', type: 'incident', assignee: 'Sarah Chen', sla_deadline: mkSla(1), created_at: mkDate(0, -1), triage_result: { confidence: 0.96, suggested_agent: 'troubleshooter', root_cause_hint: 'Race condition in batch processor', recommended_action: 'Emergency: Pause batch processor, restore from 2h backup' } },
  { id: 'TKT-5002', jira_key: 'EPSI-502', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'SSO integration broken after IdP update', severity: 'P1', status: 'in_progress', type: 'incident', assignee: 'Marcus Webb', sla_deadline: mkSla(3), created_at: mkDate(0, -4) },
  { id: 'TKT-5003', jira_key: 'EPSI-503', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'Performance degradation across all modules', severity: 'P2', status: 'open', type: 'incident', assignee: null, sla_deadline: mkSla(6), created_at: mkDate(1) },
  { id: 'TKT-5004', jira_key: 'EPSI-504', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'PDF report generation timing out', severity: 'P2', status: 'open', type: 'bug', assignee: 'Sarah Chen', sla_deadline: mkSla(8), created_at: mkDate(2) },
  { id: 'TKT-5005', jira_key: 'EPSI-505', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'User roles not syncing from LDAP', severity: 'P2', status: 'in_progress', type: 'bug', assignee: 'Marcus Webb', sla_deadline: mkSla(4), created_at: mkDate(1, -6) },
  { id: 'TKT-5006', jira_key: 'EPSI-506', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'Email notifications delayed by 2+ hours', severity: 'P3', status: 'open', type: 'bug', assignee: null, sla_deadline: mkSla(48), created_at: mkDate(3) },
  { id: 'TKT-5007', jira_key: 'EPSI-507', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'Dashboard timezone issues for EU users', severity: 'P3', status: 'open', type: 'bug', assignee: 'Sarah Chen', sla_deadline: mkSla(36), created_at: mkDate(4) },
  { id: 'TKT-5008', jira_key: 'EPSI-508', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'Feature: Automated compliance audit trail', severity: 'P3', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(96), created_at: mkDate(6) },
  { id: 'TKT-5009', jira_key: 'EPSI-509', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'API rate limit too restrictive for batch ops', severity: 'P3', status: 'resolved', type: 'support', assignee: 'Marcus Webb', sla_deadline: mkSla(-72), created_at: mkDate(14), resolved_at: mkDate(10) },
  { id: 'TKT-5010', jira_key: 'EPSI-510', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'Docs: Migration guide for v2 → v3', severity: 'P4', status: 'open', type: 'support', assignee: null, sla_deadline: mkSla(168), created_at: mkDate(7) },
  { id: 'TKT-5011', jira_key: 'EPSI-511', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'UI: Dark mode text contrast issues', severity: 'P4', status: 'open', type: 'bug', assignee: null, sla_deadline: mkSla(120), created_at: mkDate(5) },
  { id: 'TKT-5012', jira_key: 'EPSI-512', customer_id: 'cust-005', customer_name: 'Epsilon Insurance', summary: 'Feature: Custom dashboard widgets', severity: 'P4', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(240), created_at: mkDate(9) },

  // Zeta Retail — 3 tickets (watch)
  { id: 'TKT-6001', jira_key: 'ZETA-601', customer_id: 'cust-006', customer_name: 'Zeta Retail', summary: 'Inventory sync failing with Shopify connector', severity: 'P2', status: 'open', type: 'incident', assignee: 'Marcus Webb', sla_deadline: mkSla(6), created_at: mkDate(0, -6) },
  { id: 'TKT-6002', jira_key: 'ZETA-602', customer_id: 'cust-006', customer_name: 'Zeta Retail', summary: 'Checkout flow analytics not recording', severity: 'P3', status: 'open', type: 'bug', assignee: null, sla_deadline: mkSla(48), created_at: mkDate(3) },
  { id: 'TKT-6003', jira_key: 'ZETA-603', customer_id: 'cust-006', customer_name: 'Zeta Retail', summary: 'Feature: A/B testing for product pages', severity: 'P4', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(168), created_at: mkDate(5) },

  // Eta Pharma — 2 tickets (healthy)
  { id: 'TKT-7001', jira_key: 'ETA-701', customer_id: 'cust-007', customer_name: 'Eta Pharma', summary: 'Report formatting inconsistency in PDF export', severity: 'P3', status: 'in_progress', type: 'bug', assignee: 'Sarah Chen', sla_deadline: mkSla(24), created_at: mkDate(1) },
  { id: 'TKT-7002', jira_key: 'ETA-702', customer_id: 'cust-007', customer_name: 'Eta Pharma', summary: 'Feature: 21 CFR Part 11 compliance module', severity: 'P3', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(96), created_at: mkDate(8) },

  // Theta Energy — 4 tickets (healthy)
  { id: 'TKT-8001', jira_key: 'THET-801', customer_id: 'cust-008', customer_name: 'Theta Energy', summary: 'API rate limiting errors on data ingestion', severity: 'P2', status: 'open', type: 'incident', assignee: 'Marcus Webb', sla_deadline: mkSla(6), created_at: mkDate(0, -8) },
  { id: 'TKT-8002', jira_key: 'THET-802', customer_id: 'cust-008', customer_name: 'Theta Energy', summary: 'SCADA data connector intermittent failures', severity: 'P2', status: 'in_progress', type: 'bug', assignee: 'Sarah Chen', sla_deadline: mkSla(5), created_at: mkDate(1, -4) },
  { id: 'TKT-8003', jira_key: 'THET-803', customer_id: 'cust-008', customer_name: 'Theta Energy', summary: 'Dashboard custom date range not persisting', severity: 'P3', status: 'open', type: 'bug', assignee: null, sla_deadline: mkSla(48), created_at: mkDate(4) },
  { id: 'TKT-8004', jira_key: 'THET-804', customer_id: 'cust-008', customer_name: 'Theta Energy', summary: 'Feature: Real-time alerting for grid anomalies', severity: 'P3', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(96), created_at: mkDate(6) },

  // Iota Defense — 9 tickets (high_risk)
  { id: 'TKT-9001', jira_key: 'IOTA-901', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'Data sync failure in secure zone — classified data at risk', severity: 'P1', status: 'open', type: 'incident', assignee: 'Sarah Chen', sla_deadline: mkSla(1), created_at: mkDate(0, -2), triage_result: { confidence: 0.94, suggested_agent: 'troubleshooter', root_cause_hint: 'TLS certificate expired on secure bridge', recommended_action: 'Renew TLS cert on bridge-01, verify data integrity checksums' } },
  { id: 'TKT-9002', jira_key: 'IOTA-902', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'Audit log gaps — 3 hour window missing', severity: 'P1', status: 'in_progress', type: 'incident', assignee: 'Marcus Webb', sla_deadline: mkSla(2), created_at: mkDate(0, -6) },
  { id: 'TKT-9003', jira_key: 'IOTA-903', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'Access control bypass on staging environment', severity: 'P2', status: 'open', type: 'incident', assignee: 'Sarah Chen', sla_deadline: mkSla(4), created_at: mkDate(1) },
  { id: 'TKT-9004', jira_key: 'IOTA-904', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'Encryption at rest not applied to new partitions', severity: 'P2', status: 'open', type: 'bug', assignee: null, sla_deadline: mkSla(6), created_at: mkDate(2) },
  { id: 'TKT-9005', jira_key: 'IOTA-905', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'FedRAMP compliance scan failing on 3 controls', severity: 'P2', status: 'in_progress', type: 'bug', assignee: 'Marcus Webb', sla_deadline: mkSla(8), created_at: mkDate(3) },
  { id: 'TKT-9006', jira_key: 'IOTA-906', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'User session timeout too short for classified ops', severity: 'P3', status: 'open', type: 'support', assignee: null, sla_deadline: mkSla(48), created_at: mkDate(4) },
  { id: 'TKT-9007', jira_key: 'IOTA-907', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'Feature: Multi-level security clearance mapping', severity: 'P3', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(96), created_at: mkDate(6) },
  { id: 'TKT-9008', jira_key: 'IOTA-908', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'Documentation: Air-gapped deployment guide', severity: 'P4', status: 'open', type: 'support', assignee: null, sla_deadline: mkSla(168), created_at: mkDate(8) },
  { id: 'TKT-9009', jira_key: 'IOTA-909', customer_id: 'cust-009', customer_name: 'Iota Defense', summary: 'Feature: STIG compliance auto-remediation', severity: 'P4', status: 'resolved', type: 'feature_request', assignee: 'Sarah Chen', sla_deadline: mkSla(-120), created_at: mkDate(20), resolved_at: mkDate(14) },

  // Kappa Logistics — 6 tickets (watch)
  { id: 'TKT-10001', jira_key: 'KAPA-1001', customer_id: 'cust-010', customer_name: 'Kappa Logistics', summary: 'Shipment tracking API returning stale data', severity: 'P2', status: 'open', type: 'incident', assignee: 'Marcus Webb', sla_deadline: mkSla(6), created_at: mkDate(0, -4) },
  { id: 'TKT-10002', jira_key: 'KAPA-1002', customer_id: 'cust-010', customer_name: 'Kappa Logistics', summary: 'Route optimization engine timeout on 500+ waypoints', severity: 'P2', status: 'open', type: 'bug', assignee: null, sla_deadline: mkSla(8), created_at: mkDate(1, -2) },
  { id: 'TKT-10003', jira_key: 'KAPA-1003', customer_id: 'cust-010', customer_name: 'Kappa Logistics', summary: 'Webhook for delivery status not firing', severity: 'P3', status: 'in_progress', type: 'bug', assignee: 'Sarah Chen', sla_deadline: mkSla(24), created_at: mkDate(2) },
  { id: 'TKT-10004', jira_key: 'KAPA-1004', customer_id: 'cust-010', customer_name: 'Kappa Logistics', summary: 'Feature: Bulk export of shipment data', severity: 'P4', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(168), created_at: mkDate(5) },
  { id: 'TKT-10005', jira_key: 'KAPA-1005', customer_id: 'cust-010', customer_name: 'Kappa Logistics', summary: 'Map visualization not rendering in Firefox', severity: 'P3', status: 'open', type: 'bug', assignee: null, sla_deadline: mkSla(48), created_at: mkDate(3) },
  { id: 'TKT-10006', jira_key: 'KAPA-1006', customer_id: 'cust-010', customer_name: 'Kappa Logistics', summary: 'Feature: Driver mobile app integration', severity: 'P4', status: 'open', type: 'feature_request', assignee: null, sla_deadline: mkSla(240), created_at: mkDate(10) },
]
