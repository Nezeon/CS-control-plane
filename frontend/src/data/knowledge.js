// Seed: Episodic memories and semantic knowledge entries — deterministic

const NOW = Date.now()
const MIN = 60000
const HOUR = 3600000
const DAY = 86400000
const mkTime = (minsAgo) => new Date(NOW - minsAgo * MIN).toISOString()
const mkDay = (daysAgo) => new Date(NOW - daysAgo * DAY).toISOString()

// ---------------------------------------------------------------------------
// Episodic memories — per-agent diary entries from past pipeline executions
// ---------------------------------------------------------------------------
export const seedEpisodicMemories = [
  // Kai Nakamura — Triage Agent
  { id: 'ep_001', agent_id: 'triage_agent', agent_name: 'Kai Nakamura', content: 'Triaged Acme Corp ticket ACM-1234: deployment-related auth failure after OVA 4.2.1 update. Similar to Beta Financial issue from Feb 15 (ACM-1189). Resolution was auth service restart + config rollback. Confidence: 0.92.', customer_name: 'Acme Corp', event_type: 'jira_ticket_created', execution_id: 'exec_001', importance: 8, timestamp: mkTime(56) },
  { id: 'ep_002', agent_id: 'triage_agent', agent_name: 'Kai Nakamura', content: 'Triaged Epsilon Insurance EPSI-501 as P1 Critical. Data loss in claims processing — not a standard ticket. Confidence: 0.96. Immediate escalation recommended. This was the highest-severity triage I have done this quarter.', customer_name: 'Epsilon Insurance', event_type: 'jira_ticket_created', execution_id: 'exec_005', importance: 9, timestamp: mkTime(40) },
  { id: 'ep_003', agent_id: 'triage_agent', agent_name: 'Kai Nakamura', content: 'Triaged Gamma Telecom GAMA-301 as P2 Bug. Dashboard slow loading — recurring issue. Found similar ticket GAMA-287 resolved with query optimization. N+1 query pattern on data endpoint.', customer_name: 'Gamma Telecom', event_type: 'jira_ticket_created', execution_id: null, importance: 5, timestamp: mkTime(230) },
  { id: 'ep_004', agent_id: 'triage_agent', agent_name: 'Kai Nakamura', content: 'Triaged Iota Defense IOTA-901 as P1 Infrastructure. Sync failure in FedRAMP secure zone. Novel issue — no similar tickets found. Secure zone topology is unique. Lower confidence at 0.88.', customer_name: 'Iota Defense', event_type: 'jira_ticket_created', execution_id: null, importance: 8, timestamp: mkTime(22) },

  // Leo Petrov — Troubleshooter
  { id: 'ep_005', agent_id: 'troubleshooter_agent', agent_name: 'Leo Petrov', content: 'Root cause for Acme Corp ACM-1234: OVA 4.2.1 migration script does not update auth_service config checksum. Cache TTL overwritten, breaking token rotation. Fix: restart with forced config reload + cache flush. Published resolution pattern.', customer_name: 'Acme Corp', event_type: 'jira_ticket_created', execution_id: 'exec_002', importance: 9, timestamp: mkTime(50) },
  { id: 'ep_006', agent_id: 'troubleshooter_agent', agent_name: 'Leo Petrov', content: 'EPSI-501 root cause: race condition in batch write path. Concurrent writes from two regional nodes caused partial overwrites. Data recoverable via WAL (98%). Fix: batch write lock patch from 4.2.2-hotfix.', customer_name: 'Epsilon Insurance', event_type: 'jira_ticket_created', execution_id: null, importance: 9, timestamp: mkTime(30) },
  { id: 'ep_007', agent_id: 'troubleshooter_agent', agent_name: 'Leo Petrov', content: 'IOTA-901 partial analysis: TLS cert on bridge-01 expired. Zara found that security patch moved cert-manager cron to different namespace without updating job reference. Combined root cause: namespace migration check missing from FedRAMP security patch playbook.', customer_name: 'Iota Defense', event_type: 'jira_ticket_created', execution_id: null, importance: 8, timestamp: mkTime(8) },

  // Maya Santiago — Escalation Agent
  { id: 'ep_008', agent_id: 'escalation_agent', agent_name: 'Maya Santiago', content: 'Drafted escalation for Epsilon Insurance P1 Critical data loss. VP Engineering notified, #cs-critical alerted, customer communication sent. Learned: include renewal date context in future critical escalations (Epsilon renewal March 31).', customer_name: 'Epsilon Insurance', event_type: 'jira_ticket_created', execution_id: 'exec_005', importance: 8, timestamp: mkTime(40) },
  { id: 'ep_009', agent_id: 'escalation_agent', agent_name: 'Maya Santiago', content: 'Escalation for Iota Defense SOW gaps. Security audit overdue, FedRAMP compliance issues. Prepared notification for Col. Patricia Hayes with impact assessment.', customer_name: 'Iota Defense', event_type: 'daily_health_check', execution_id: null, importance: 7, timestamp: mkTime(340) },

  // Dr. Aisha Okafor — Health Monitor
  { id: 'ep_010', agent_id: 'health_monitor_agent', agent_name: 'Dr. Aisha Okafor', content: 'Epsilon Insurance health dropped to 38 (down 5). Multiple failure signals: 12 open tickets, negative sentiment trend, 2 SLA breaches, declining usage. Consecutive decline pattern — strong churn signal. Alert triggered.', customer_name: 'Epsilon Insurance', event_type: 'daily_health_check', execution_id: 'exec_004', importance: 9, timestamp: mkTime(115) },
  { id: 'ep_011', agent_id: 'health_monitor_agent', agent_name: 'Dr. Aisha Okafor', content: 'Beta Financial factor analysis: 16-point health drop driven by reporting module bugs (ticket volume up 40%), usage down 15%, NPS dropped from 8 to 6. Not structural churn — frustration-driven. Needs immediate bug fixes.', customer_name: 'Beta Financial', event_type: 'daily_health_check', execution_id: null, importance: 7, timestamp: mkTime(110) },
  { id: 'ep_012', agent_id: 'health_monitor_agent', agent_name: 'Dr. Aisha Okafor', content: 'Delta Health daily check: health 91, stable. All signals green for 14 consecutive days. Model customer for benchmarking.', customer_name: 'Delta Health', event_type: 'daily_health_check', execution_id: null, importance: 3, timestamp: mkTime(60) },
  { id: 'ep_013', agent_id: 'health_monitor_agent', agent_name: 'Dr. Aisha Okafor', content: 'Iota Defense health at 44 (down 4). Critical signals: 9 tickets, negative sentiment, FedRAMP gaps. Combined with SOW delays, this is a high-risk account. Recommended escalation to Naveen.', customer_name: 'Iota Defense', event_type: 'daily_health_check', execution_id: null, importance: 8, timestamp: mkTime(45) },

  // Jordan Ellis — Fathom Agent
  { id: 'ep_014', agent_id: 'fathom_agent', agent_name: 'Jordan Ellis', content: 'Beta Financial last 3 calls show downward sentiment. Feb 27 call had CFO mentioning "exploring alternatives" — soft competitor mention. This is a strong churn signal when combined with health decline. Recommended proactive CSM outreach.', customer_name: 'Beta Financial', event_type: 'fathom_call_processed', execution_id: 'exec_003', importance: 8, timestamp: mkTime(105) },
  { id: 'ep_015', agent_id: 'fathom_agent', agent_name: 'Jordan Ellis', content: 'Gamma Telecom 90-day call summary: 8 calls, improving sentiment (+0.12 avg). Key themes: dashboard speed (4 calls), positive on API features. Action item completion at 71%. Good QBR material.', customer_name: 'Gamma Telecom', event_type: 'fathom_call_processed', execution_id: null, importance: 5, timestamp: mkTime(220) },
  { id: 'ep_016', agent_id: 'fathom_agent', agent_name: 'Jordan Ellis', content: 'Theta Energy quarterly review: mixed sentiment (0.52). 6 action items, 1 decision (Q2 Phase 2), 1 risk (April budget review). Budget review comment warrants watch list addition.', customer_name: 'Theta Energy', event_type: 'fathom_call_processed', execution_id: null, importance: 6, timestamp: mkTime(78) },
  { id: 'ep_017', agent_id: 'fathom_agent', agent_name: 'Jordan Ellis', content: 'Epsilon Insurance escalation call: sentiment -0.68. 4 action items. Churn risk HIGH. Customer VP expressed frustration with response times and data integrity concerns.', customer_name: 'Epsilon Insurance', event_type: 'fathom_call_processed', execution_id: null, importance: 9, timestamp: mkTime(10) },

  // Sofia Marquez — QBR Agent
  { id: 'ep_018', agent_id: 'qbr_agent', agent_name: 'Sofia Marquez', content: 'Generated Gamma Telecom Q1 QBR: 14 pages. Health improving (+7 QoQ), tickets down 20%, dashboard perf is recurring theme. Three strategic recommendations. Learned: recurring complaints need dedicated QBR section.', customer_name: 'Gamma Telecom', event_type: 'qbr_scheduled', execution_id: 'exec_006', importance: 6, timestamp: mkTime(195) },
  { id: 'ep_019', agent_id: 'qbr_agent', agent_name: 'Sofia Marquez', content: 'Generated Beta Financial QBR: 12 pages. Incorporated positive call sentiment and expansion signals from Jordan. Customer well-positioned for upsell discussion.', customer_name: 'Beta Financial', event_type: 'qbr_scheduled', execution_id: null, importance: 5, timestamp: mkTime(168) },

  // Ethan Brooks — SOW Agent
  { id: 'ep_020', agent_id: 'sow_agent', agent_name: 'Ethan Brooks', content: 'Iota Defense SOW review: 3/8 milestones on track, 2 at risk, 3 blocked. Security audit 2 weeks overdue. FedRAMP data residency gap identified. Stored defense client SOW patterns for future reference.', customer_name: 'Iota Defense', event_type: 'daily_health_check', execution_id: 'exec_007', importance: 8, timestamp: mkTime(165) },
  { id: 'ep_021', agent_id: 'sow_agent', agent_name: 'Ethan Brooks', content: 'Delta Health SOW alignment for 4.3.0 deployment: milestone 4/6, on track. Post-deployment health check required within 48 hours per SOW.', customer_name: 'Delta Health', event_type: 'deployment_event', execution_id: null, importance: 4, timestamp: mkTime(160) },

  // Zara Kim — Deployment Intel
  { id: 'ep_022', agent_id: 'deployment_intel_agent', agent_name: 'Zara Kim', content: 'Delta Health pre-flight for OVA 4.3.0: all green. Auth fix from Acme incident included in 4.3.0. Certs valid 180+ days. Recommend low-traffic window deployment (2-4am EST).', customer_name: 'Delta Health', event_type: 'deployment_event', execution_id: 'exec_008', importance: 5, timestamp: mkTime(165) },
  { id: 'ep_023', agent_id: 'deployment_intel_agent', agent_name: 'Zara Kim', content: 'Iota Defense IOTA-901 investigation: security patch moved cert-manager cron to different namespace without updating renewal job reference. TLS cert expired, breaking sync tunnel. Critical finding — FedRAMP zones need namespace migration checks during patches.', customer_name: 'Iota Defense', event_type: 'jira_ticket_created', execution_id: null, importance: 9, timestamp: mkTime(14) },
  { id: 'ep_024', agent_id: 'deployment_intel_agent', agent_name: 'Zara Kim', content: 'Environment scan: 8/10 customers healthy. Acme Corp: config drift detected (v3.1.9 vs v3.2.1). Iota Defense: cert expiry flagged 48h before incident. Note: early warning was not acted on in time.', customer_name: null, event_type: 'daily_health_check', execution_id: null, importance: 7, timestamp: mkTime(60) },

  // Atlas — Customer Memory
  { id: 'ep_025', agent_id: 'customer_memory', agent_name: 'Atlas', content: 'Acme Corp incident chain stored: P1 auth failure (ACM-1234), triage to troubleshoot to resolution. 3 embeddings added to knowledge base. Cross-referenced with ACME-389 and BETA-178.', customer_name: 'Acme Corp', event_type: 'jira_ticket_created', execution_id: null, importance: 7, timestamp: mkTime(48) },
  { id: 'ep_026', agent_id: 'customer_memory', agent_name: 'Atlas', content: 'Theta Energy profile updated: quarterly review insights stored. 6 action items, Q2 Phase 2 decision, budget review risk flag. Context refreshed for all agents.', customer_name: 'Theta Energy', event_type: 'fathom_call_processed', execution_id: null, importance: 5, timestamp: mkTime(75) },
]

// ---------------------------------------------------------------------------
// Semantic knowledge entries — shared team knowledge organized by lane
// ---------------------------------------------------------------------------
export const seedKnowledgeEntries = [
  // Support Lane Knowledge
  { id: 'kn_001', content: 'OVA deployments with version 4.2.x commonly cause authentication timeouts. Root cause: auth service config not updated during migration. Fix: restart auth service and verify config checksum.', agent_id: 'troubleshooter_agent', agent_name: 'Leo Petrov', lane: 'support', tags: ['ova', 'authentication', 'deployment', 'timeout', 'config'], importance: 9, knowledge_type: 'resolution_pattern', customer_name: 'Acme Corp', timestamp: mkDay(1) },
  { id: 'kn_002', content: 'Batch write race conditions in claims processing module can cause data loss when concurrent writes hit from multiple regional nodes. Fix: apply batch write lock patch (available in 4.2.2-hotfix). Data recoverable via WAL in most cases (98% recovery rate).', agent_id: 'troubleshooter_agent', agent_name: 'Leo Petrov', lane: 'support', tags: ['data_loss', 'race_condition', 'batch_write', 'wal_recovery'], importance: 9, knowledge_type: 'resolution_pattern', customer_name: 'Epsilon Insurance', timestamp: mkTime(30) },
  { id: 'kn_003', content: 'N+1 query pattern on dashboard data endpoint causes slow loading. Resolution: optimize data aggregation queries with proper JOINs and pagination. This is a recurring issue across multiple customers.', agent_id: 'triage_agent', agent_name: 'Kai Nakamura', lane: 'support', tags: ['dashboard', 'performance', 'n+1', 'query_optimization'], importance: 6, knowledge_type: 'triage_pattern', customer_name: 'Gamma Telecom', timestamp: mkDay(3) },
  { id: 'kn_004', content: 'P1 tickets with auth-related keywords after deployments should be fast-tracked to troubleshooting. Historical resolution rate: 100% when caught within first hour. SLA compliance: 95% when triage-to-troubleshoot handoff is under 15 minutes.', agent_id: 'triage_agent', agent_name: 'Kai Nakamura', lane: 'support', tags: ['triage', 'auth', 'deployment', 'sla', 'fast_track'], importance: 8, knowledge_type: 'triage_pattern', customer_name: null, timestamp: mkDay(2) },

  // Value Lane Knowledge
  { id: 'kn_005', content: 'CFO-level mentions of "exploring alternatives" or "looking at other options" are strong churn predictors. In our data, 3 out of 4 accounts where this was detected required executive intervention within 2 weeks to retain.', agent_id: 'fathom_agent', agent_name: 'Jordan Ellis', lane: 'value', tags: ['churn', 'sentiment', 'cfo', 'competitor_mention', 'retention'], importance: 9, knowledge_type: 'sentiment_pattern', customer_name: null, timestamp: mkDay(1) },
  { id: 'kn_006', content: 'Health score drops driven by reporting module bugs are typically temporary and recover within 2-3 weeks after bug fixes. Key indicator: if usage drops correlate with ticket spikes about specific features, the issue is frustration-driven, not structural churn.', agent_id: 'health_monitor_agent', agent_name: 'Dr. Aisha Okafor', lane: 'value', tags: ['health', 'bugs', 'temporary_decline', 'recovery_pattern'], importance: 7, knowledge_type: 'health_pattern', customer_name: 'Beta Financial', timestamp: mkDay(1) },
  { id: 'kn_007', content: 'QBR packages should include a dedicated section for recurring complaints when the same issue appears in 3+ calls. This shows the customer that their feedback is being tracked systematically and improves perception of responsiveness.', agent_id: 'qbr_agent', agent_name: 'Sofia Marquez', lane: 'value', tags: ['qbr', 'complaints', 'customer_experience', 'best_practice'], importance: 6, knowledge_type: 'best_practice', customer_name: null, timestamp: mkDay(5) },
  { id: 'kn_008', content: 'Accounts with 14+ consecutive days of green health signals can be used as benchmarks for other accounts in the same industry vertical. Delta Health is the current model customer for healthcare vertical.', agent_id: 'health_monitor_agent', agent_name: 'Dr. Aisha Okafor', lane: 'value', tags: ['health', 'benchmark', 'stable_accounts', 'best_practice'], importance: 5, knowledge_type: 'health_pattern', customer_name: 'Delta Health', timestamp: mkDay(2) },

  // Delivery Lane Knowledge
  { id: 'kn_009', content: 'FedRAMP customers require special attention during security patches. Namespace migrations in FedRAMP zones can break cert-manager cron jobs if references are not updated. Always verify cert renewal job status after any namespace change in secure zones.', agent_id: 'deployment_intel_agent', agent_name: 'Zara Kim', lane: 'delivery', tags: ['fedramp', 'security_patch', 'cert_manager', 'namespace', 'cron'], importance: 9, knowledge_type: 'deployment_pattern', customer_name: 'Iota Defense', timestamp: mkTime(8) },
  { id: 'kn_010', content: 'Defense client SOW reviews require FedRAMP compliance mapping as a separate section. Security audit milestones should be tracked with 4-week advance warnings due to the lengthy approval process in defense organizations.', agent_id: 'sow_agent', agent_name: 'Ethan Brooks', lane: 'delivery', tags: ['sow', 'defense', 'fedramp', 'compliance', 'security_audit'], importance: 8, knowledge_type: 'sow_pattern', customer_name: 'Iota Defense', timestamp: mkDay(2) },
  { id: 'kn_011', content: 'OVA 4.3.0 includes the auth config migration fix from Acme Corp incident. No manual intervention needed for auth during 4.3.0 deployments. Always verify by checking release notes against known issues from 4.2.x series.', agent_id: 'deployment_intel_agent', agent_name: 'Zara Kim', lane: 'delivery', tags: ['ova', '4.3.0', 'auth_fix', 'deployment', 'release_notes'], importance: 7, knowledge_type: 'deployment_pattern', customer_name: null, timestamp: mkDay(3) },
  { id: 'kn_012', content: 'Post-deployment health checks within 48 hours are a standard SOW requirement for most enterprise customers. Coordinate with Health Monitor (Dr. Aisha Okafor) to schedule automated checks after any deployment.', agent_id: 'sow_agent', agent_name: 'Ethan Brooks', lane: 'delivery', tags: ['sow', 'deployment', 'health_check', 'post_deployment', 'coordination'], importance: 6, knowledge_type: 'sow_pattern', customer_name: null, timestamp: mkDay(4) },

  // Cross-lane Knowledge
  { id: 'kn_013', content: 'When a customer has simultaneous issues in Support and Delivery lanes (e.g., active P1 tickets and SOW delays), coordinate response through Naveen to avoid conflicting communications. Single-voice principle applies.', agent_id: 'customer_memory', agent_name: 'Atlas', lane: 'control', tags: ['coordination', 'multi_lane', 'communication', 'best_practice'], importance: 8, knowledge_type: 'best_practice', customer_name: null, timestamp: mkDay(7) },
  { id: 'kn_014', content: 'Config drift between deployment versions (e.g., v3.1.9 vs v3.2.1) should trigger a proactive alert even if no customer-reported issue exists. Early detection of drift prevents 73% of deployment-related incidents based on our historical data.', agent_id: 'deployment_intel_agent', agent_name: 'Zara Kim', lane: 'delivery', tags: ['config_drift', 'proactive', 'early_warning', 'prevention'], importance: 7, knowledge_type: 'deployment_pattern', customer_name: 'Acme Corp', timestamp: mkDay(2) },
  { id: 'kn_015', content: 'Cert expiry warnings should be escalated if not acknowledged within 24 hours. The Iota Defense incident (IOTA-901) showed that a 48-hour warning was not acted on in time, leading to a P1 outage.', agent_id: 'escalation_agent', agent_name: 'Maya Santiago', lane: 'support', tags: ['cert', 'expiry', 'escalation', 'warning', 'sla'], importance: 8, knowledge_type: 'escalation_pattern', customer_name: 'Iota Defense', timestamp: mkTime(14) },
]

// ---------------------------------------------------------------------------
// Combined list for unified search — maps both types to a common shape
// ---------------------------------------------------------------------------
export const allKnowledgeItems = [
  ...seedEpisodicMemories.map((m) => ({
    id: m.id,
    type: 'episodic',
    agent_name: m.agent_name,
    agent_id: m.agent_id,
    content: m.content,
    summary: m.content.slice(0, 120),
    customer_name: m.customer_name,
    tags: [],
    importance: m.importance,
    created_at: m.timestamp,
  })),
  ...seedKnowledgeEntries.map((k) => ({
    id: k.id,
    type: 'knowledge',
    published_by_name: k.agent_name,
    published_by: k.agent_id,
    content: k.content,
    summary: k.content.slice(0, 120),
    customer_name: k.customer_name,
    lane: k.lane,
    tags: k.tags,
    importance: k.importance,
    created_at: k.timestamp,
  })),
]
