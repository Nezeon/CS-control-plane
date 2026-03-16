// Seed: Demo chat conversations for offline/demo mode

const NOW = Date.now()
const MIN = 60000
const mkTime = (minsAgo) => new Date(NOW - minsAgo * MIN).toISOString()

export const seedChatConversations = [
  {
    id: 'chat_001',
    title: 'Key takeaways from Acme Corp call',
    customer_id: null,
    customer_name: 'Acme Corp',
    message_count: 2,
    last_message_at: mkTime(30),
    status: 'active',
    created_at: mkTime(35),
  },
  {
    id: 'chat_002',
    title: 'Beta Financial health trend',
    customer_id: null,
    customer_name: 'Beta Financial',
    message_count: 2,
    last_message_at: mkTime(120),
    status: 'active',
    created_at: mkTime(125),
  },
  {
    id: 'chat_003',
    title: 'Gamma Telecom open tickets',
    customer_id: null,
    customer_name: 'Gamma Telecom',
    message_count: 2,
    last_message_at: mkTime(360),
    status: 'active',
    created_at: mkTime(365),
  },
]

export const seedChatMessages = {
  chat_001: [
    {
      id: 'cmsg_001',
      conversation_id: 'chat_001',
      role: 'user',
      content: 'What were the key takeaways from the last Acme Corp call?',
      agents_involved: [],
      pipeline_status: null,
      execution_metadata: {},
      created_at: mkTime(35),
    },
    {
      id: 'cmsg_002',
      conversation_id: 'chat_001',
      role: 'assistant',
      content:
        'Here\'s a summary of the latest Acme Corp call from yesterday\'s QBR meeting:\n\n' +
        'The call focused on their upcoming OVA 4.3 migration timeline and the recent P1 authentication issues they experienced. ' +
        'VP of Engineering Sarah Chen expressed concern about deployment risk given the 4.2.1 incident.\n\n' +
        '**Key Decisions:**\n' +
        '- Migration postponed to Q2 pending stability verification\n' +
        '- Weekly check-in calls established (every Tuesday 2pm)\n' +
        '- Dedicated support engineer assigned for migration window\n\n' +
        '**Action Items:**\n' +
        '- Send updated migration runbook by Friday\n' +
        '- Schedule pre-migration health check for March 15\n' +
        '- Share root cause analysis from P1 incident\n\n' +
        '**Sentiment:** Cautiously optimistic — they value the partnership but need reassurance on stability.\n\n' +
        '**Next Steps:**\n' +
        '- Follow up on migration runbook delivery\n' +
        '- Prepare health trend report for Tuesday call',
      agents_involved: ['cso_orchestrator', 'value_lead', 'fathom_agent'],
      pipeline_status: 'completed',
      execution_metadata: {
        intent: 'fathom',
        event_type: 'user_chat_fathom',
        lanes_used: ['value'],
        customer_name: 'Acme Corp',
      },
      created_at: mkTime(30),
    },
  ],
  chat_002: [
    {
      id: 'cmsg_003',
      conversation_id: 'chat_002',
      role: 'user',
      content: 'How is Beta Financial\'s health score trending? Should I be worried?',
      agents_involved: [],
      pipeline_status: null,
      execution_metadata: {},
      created_at: mkTime(125),
    },
    {
      id: 'cmsg_004',
      conversation_id: 'chat_002',
      role: 'assistant',
      content:
        'Beta Financial\'s health has been declining over the past 2 weeks and warrants attention.\n\n' +
        '**Health Score:** 62/100 (down from 78 two weeks ago)\n' +
        '**Risk Level:** at_risk\n\n' +
        'The decline is driven by:\n' +
        '- 3 open P2 tickets unresolved past SLA (support engagement dropped)\n' +
        '- Missed last QBR meeting (stakeholder disengagement signal)\n' +
        '- Product usage down 15% month-over-month\n\n' +
        '**Recommendations:**\n' +
        '- Schedule urgent check-in call with their CSM Lisa Park\n' +
        '- Prioritize the 3 overdue P2 tickets for resolution this week\n' +
        '- Prepare a value summary highlighting ROI metrics before the call',
      agents_involved: ['cso_orchestrator', 'value_lead', 'health_monitor'],
      pipeline_status: 'completed',
      execution_metadata: {
        intent: 'health',
        event_type: 'user_chat_health',
        lanes_used: ['value'],
        customer_name: 'Beta Financial',
      },
      created_at: mkTime(120),
    },
  ],
  chat_003: [
    {
      id: 'cmsg_005',
      conversation_id: 'chat_003',
      role: 'user',
      content: 'What are the open tickets for Gamma Telecom? Any escalations?',
      agents_involved: [],
      pipeline_status: null,
      execution_metadata: {},
      created_at: mkTime(365),
    },
    {
      id: 'cmsg_006',
      conversation_id: 'chat_003',
      role: 'assistant',
      content:
        'Gamma Telecom currently has 5 open tickets. Here\'s the breakdown:\n\n' +
        '**Escalations (1):**\n' +
        '- GAM-892 (P1): Network scan timeout on segments >10K hosts — escalated 2 days ago, engineering investigating\n\n' +
        '**Active Tickets:**\n' +
        '- GAM-901 (P2): Dashboard export failing for custom date ranges — assigned, fix in progress\n' +
        '- GAM-898 (P3): False positive rate spike after signature update 2024.3.1\n' +
        '- GAM-905 (P3): LDAP sync delay affecting user provisioning\n' +
        '- GAM-910 (P4): Feature request — bulk asset tagging from CSV\n\n' +
        '**Suggested Actions:**\n' +
        '- Follow up on GAM-892 escalation — check engineering ETA\n' +
        '- Prioritize GAM-901 as it impacts their monthly reporting workflow\n' +
        '- Monitor false positive rate after next signature update',
      agents_involved: ['cso_orchestrator', 'support_lead', 'triage_agent'],
      pipeline_status: 'completed',
      execution_metadata: {
        intent: 'ticket',
        event_type: 'user_chat_ticket',
        lanes_used: ['support'],
        customer_name: 'Gamma Telecom',
      },
      created_at: mkTime(360),
    },
  ],
}
