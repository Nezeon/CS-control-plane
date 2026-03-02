// Seed: Analytics data — KPIs, ticket volume, agent performance, sentiment stream, health trend, reports

const NOW = Date.now()
const DAY = 86400000
const WEEK = 7 * DAY
const mkDate = (daysAgo) => new Date(NOW - daysAgo * DAY).toISOString().split('T')[0]
const mkWeek = (weeksAgo) => {
  const d = new Date(NOW - weeksAgo * WEEK)
  return `W${String(Math.ceil(d.getDate() / 7)).padStart(2, '0')} ${d.toLocaleDateString('en-US', { month: 'short' })}`
}

export const seedAnalyticsKpis = {
  total_customers: 10,
  customers: 10,
  avg_health: 64,
  average_health: 64,
  tickets_resolved: 147,
  resolved: 147,
  total_calls: 89,
  calls: 89,
  customer_trend: +2,
  health_trend: -1,
  resolved_trend: +12,
  calls_trend: +3,
}

export const seedTicketVolume = [
  { week: mkWeek(7), P1: 2, P2: 5, P3: 8, P4: 4, opened: 19, resolved: 15 },
  { week: mkWeek(6), P1: 1, P2: 6, P3: 7, P4: 5, opened: 19, resolved: 17 },
  { week: mkWeek(5), P1: 3, P2: 4, P3: 9, P4: 3, opened: 19, resolved: 14 },
  { week: mkWeek(4), P1: 2, P2: 7, P3: 6, P4: 6, opened: 21, resolved: 18 },
  { week: mkWeek(3), P1: 4, P2: 5, P3: 8, P4: 4, opened: 21, resolved: 16 },
  { week: mkWeek(2), P1: 1, P2: 8, P3: 7, P4: 5, opened: 21, resolved: 20 },
  { week: mkWeek(1), P1: 3, P2: 6, P3: 10, P4: 3, opened: 22, resolved: 19 },
  { week: mkWeek(0), P1: 5, P2: 7, P3: 6, P4: 4, opened: 22, resolved: 18 },
]

export const seedAgentPerformance = [
  { agent: 'CS Orchestrator', tasks_completed: 1847, avg_duration_ms: 120, lane: 'control' },
  { agent: 'Memory Agent', tasks_completed: 1623, avg_duration_ms: 85, lane: 'control' },
  { agent: 'Health Monitor', tasks_completed: 892, avg_duration_ms: 200, lane: 'control' },
  { agent: 'Escalation Agent', tasks_completed: 234, avg_duration_ms: 150, lane: 'control' },
  { agent: 'Call Intelligence', tasks_completed: 567, avg_duration_ms: 3200, lane: 'value' },
  { agent: 'QBR Generator', tasks_completed: 89, avg_duration_ms: 8500, lane: 'value' },
  { agent: 'Ticket Triage', tasks_completed: 1234, avg_duration_ms: 450, lane: 'support' },
  { agent: 'Troubleshooter', tasks_completed: 678, avg_duration_ms: 2800, lane: 'support' },
  { agent: 'SOW Analyzer', tasks_completed: 156, avg_duration_ms: 1600, lane: 'delivery' },
  { agent: 'Deployment Intel', tasks_completed: 345, avg_duration_ms: 900, lane: 'delivery' },
]

// 30-day sentiment stream (positive / neutral / negative values)
export const seedSentimentStream = Array.from({ length: 30 }, (_, i) => {
  const daysAgo = 29 - i
  const date = mkDate(daysAgo)

  // Deterministic wave patterns for organic look
  const phaseP = i * 0.18
  const phaseN = i * 0.22 + 1.5
  const positive = 3.5 + 1.8 * Math.sin(phaseP) + 0.5 * Math.cos(i * 0.35)
  const negative = 1.2 + 0.8 * Math.sin(phaseN) + 0.3 * Math.cos(i * 0.28 + 0.7)
  const neutral = 2.0 + 0.6 * Math.sin(i * 0.15 + 2.0)

  return {
    date,
    positive: parseFloat(Math.max(0.5, positive).toFixed(2)),
    neutral: parseFloat(Math.max(0.3, neutral).toFixed(2)),
    negative: parseFloat(Math.max(0.2, negative).toFixed(2)),
  }
})

// 10 customers × 30 days health trend matrix
const customerSeeds = [
  { id: 'cust-001', name: 'Acme Corp', startHealth: 60, endHealth: 42, volatility: 3 },
  { id: 'cust-002', name: 'Beta Financial', startHealth: 78, endHealth: 88, volatility: 2 },
  { id: 'cust-003', name: 'Gamma Telecom', startHealth: 50, endHealth: 55, volatility: 4 },
  { id: 'cust-004', name: 'Delta Health', startHealth: 89, endHealth: 91, volatility: 1 },
  { id: 'cust-005', name: 'Epsilon Insurance', startHealth: 55, endHealth: 38, volatility: 5 },
  { id: 'cust-006', name: 'Zeta Retail', startHealth: 72, endHealth: 67, volatility: 3 },
  { id: 'cust-007', name: 'Eta Pharma', startHealth: 80, endHealth: 85, volatility: 2 },
  { id: 'cust-008', name: 'Theta Energy', startHealth: 78, endHealth: 72, volatility: 3 },
  { id: 'cust-009', name: 'Iota Defense', startHealth: 56, endHealth: 44, volatility: 4 },
  { id: 'cust-010', name: 'Kappa Logistics', startHealth: 54, endHealth: 60, volatility: 3 },
]

export const seedHealthTrend = customerSeeds.flatMap((cust) => {
  return Array.from({ length: 30 }, (_, i) => {
    const t = i / 29 // 0 → 1
    const base = cust.startHealth + (cust.endHealth - cust.startHealth) * t
    // Deterministic wobble using sin
    const wobble = cust.volatility * Math.sin(i * 0.5 + cust.startHealth * 0.1)
    const score = Math.round(Math.max(0, Math.min(100, base + wobble)))
    return {
      date: mkDate(29 - i),
      customer_id: cust.id,
      customer_name: cust.name,
      score,
      avg_score: score,
    }
  })
})

// 8 sample reports
export const seedReports = [
  {
    id: 'rpt-001',
    type: 'weekly',
    title: 'Weekly CS Digest — Week of Feb 17',
    period_start: mkDate(11),
    period_end: mkDate(4),
    customer_name: null,
    created_at: new Date(NOW - 4 * DAY).toISOString(),
    sections: [
      { title: 'Health Overview', content: 'Average health across 10 customers: 64.2%. 3 customers in high-risk zone. Epsilon Insurance requires immediate attention.' },
      { title: 'Ticket Summary', content: '22 new tickets opened, 18 resolved. P1 count: 5 (up from 3 last week). SLA compliance: 85%.' },
      { title: 'Key Actions', content: 'Acme Corp login failures resolved via rollback. Iota Defense FedRAMP remediation in progress. Beta Financial QBR scheduled.' },
    ],
  },
  {
    id: 'rpt-002',
    type: 'weekly',
    title: 'Weekly CS Digest — Week of Feb 10',
    period_start: mkDate(18),
    period_end: mkDate(11),
    customer_name: null,
    created_at: new Date(NOW - 11 * DAY).toISOString(),
    sections: [
      { title: 'Health Overview', content: 'Average health: 65.8%. 2 customers improved, 1 declined (Epsilon Insurance: 43 → 38).' },
      { title: 'Ticket Summary', content: '21 new tickets, 20 resolved. Good closure rate. P1 count: 1 (improvement from previous week).' },
    ],
  },
  {
    id: 'rpt-003',
    type: 'monthly',
    title: 'Monthly CS Review — January 2026',
    period_start: '2026-01-01',
    period_end: '2026-01-31',
    customer_name: null,
    created_at: '2026-02-03T10:00:00Z',
    sections: [
      { title: 'Executive Summary', content: 'January saw stable health metrics with 3 customers showing improvement. Agent automation handled 67% of ticket triage.' },
      { title: 'Health Trends', content: 'Beta Financial: 82 → 86 (+4). Delta Health: 90 → 91 (+1). Kappa Logistics: 52 → 58 (+6). Acme Corp: 52 → 48 (-4).' },
      { title: 'Agent Performance', content: 'Total tasks: 6,234. Avg response: 1.2s. Success rate: 95.8%. Top agent: CS Orchestrator (1,847 tasks).' },
    ],
  },
  {
    id: 'rpt-004',
    type: 'qbr',
    title: 'QBR Package — Beta Financial Q1 2026',
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    customer_id: 'cust-002',
    customer_name: 'Beta Financial',
    created_at: '2026-02-25T14:00:00Z',
    sections: [
      { title: 'Account Health', content: 'Health score: 88 (Healthy). Trending up from 78 at start of quarter. All SLAs met. Zero P1 incidents.' },
      { title: 'Platform Adoption', content: '95% feature utilization. Compliance dashboard used daily by 12 users. API integration: 99.9% uptime.' },
      { title: 'Recommendations', content: '1. Upgrade to Enterprise tier for advanced analytics. 2. Implement real-time alerting for compliance. 3. Schedule champion training for new hires.' },
    ],
  },
  {
    id: 'rpt-005',
    type: 'qbr',
    title: 'QBR Package — Acme Corp Q1 2026',
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    customer_id: 'cust-001',
    customer_name: 'Acme Corp',
    created_at: '2026-02-20T16:00:00Z',
    sections: [
      { title: 'Account Health', content: 'Health score: 42 (High Risk). Declined from 60. Contributing factors: 8 open tickets, negative call sentiment, P1 incidents.' },
      { title: 'Critical Issues', content: '3 P1 incidents in 30 days. Login failure incident impacted all regions. Average resolution time: 8 hours (above SLA).' },
      { title: 'Recovery Plan', content: '1. Dedicated support engineer assigned. 2. Weekly stability calls. 3. Root cause review for all P1s. 4. Proactive monitoring implementation.' },
    ],
  },
  {
    id: 'rpt-006',
    type: 'weekly',
    title: 'Weekly CS Digest — Week of Feb 24',
    period_start: mkDate(4),
    period_end: mkDate(0),
    customer_name: null,
    created_at: new Date(NOW - 0.5 * DAY).toISOString(),
    sections: [
      { title: 'Health Overview', content: 'Average health: 64.2%. Epsilon Insurance critical (38). Iota Defense declining (44). Beta Financial strong (88).' },
      { title: 'Ticket Summary', content: '22 tickets opened this week. 5 P1s — highest in 4 weeks. SLA compliance dropped to 82%.' },
    ],
  },
  {
    id: 'rpt-007',
    type: 'monthly',
    title: 'Monthly CS Review — December 2025',
    period_start: '2025-12-01',
    period_end: '2025-12-31',
    customer_name: null,
    created_at: '2026-01-05T10:00:00Z',
    sections: [
      { title: 'Executive Summary', content: 'December was the best month of Q4. Health improved across 7/10 customers. Holiday season handled with zero downtime.' },
      { title: 'Key Wins', content: 'Kappa Logistics onboarding completed. Eta Pharma compliance module deployed. Delta Health renewed for 2 years.' },
    ],
  },
  {
    id: 'rpt-008',
    type: 'qbr',
    title: 'QBR Package — Eta Pharma Q1 2026',
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    customer_id: 'cust-007',
    customer_name: 'Eta Pharma',
    created_at: '2026-02-22T11:00:00Z',
    sections: [
      { title: 'Account Health', content: 'Health score: 85 (Healthy). Stable throughout the quarter. Compliance posture strong.' },
      { title: 'Compliance Progress', content: '21 CFR Part 11: IQ completed, OQ in progress. Validation documentation 80% complete. Target: April certification.' },
      { title: 'Next Steps', content: '1. Complete OQ testing. 2. Schedule FDA mock audit. 3. Prepare PQ documentation. 4. Electronic signature workflow review.' },
    ],
  },
]
