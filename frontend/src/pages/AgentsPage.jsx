import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import AgentCard from '../components/agents/AgentCard'
import EmptyState from '../components/shared/EmptyState'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { Bot } from 'lucide-react'
import { dashboardApi } from '../services/dashboardApi'

/* Only these 5 agents are fully operational (keys match backend AGENT_REGISTRY) */
const ACTIVE_AGENT_KEYS = new Set([
  'cso_orchestrator', 'customer_memory', 'presales_funnel',
  'triage_agent', 'health_monitor_agent',
])

const SOURCE_MAP = {
  cso_orchestrator: ['Jira', 'Fathom', 'HubSpot'],
  customer_memory: [],
  presales_funnel: ['HubSpot'],
  triage_agent: ['Jira', 'Slack'],
  health_monitor_agent: ['Jira', 'Fathom', 'HubSpot'],
  sow_agent: ['HubSpot'],
  deployment_intel_agent: ['Jira'],
  troubleshooter_agent: ['Jira'],
  escalation_agent: ['Jira', 'Slack'],
  qbr_agent: ['Fathom', 'HubSpot'],
}

const FILTERS = ['all', 'running', 'idle', 'inactive']

function mapAgentStatus(agent) {
  if (!ACTIVE_AGENT_KEYS.has(agent.agent_key)) return 'inactive'
  if (agent.status === 'active') return 'running'
  return agent.status || 'idle'
}

export default function AgentsPage() {
  const [filter, setFilter] = useState('all')
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    dashboardApi.getAgents()
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : data?.agents || []
        setAgents(list.map(a => ({
          id: a.id || a.agent_key,
          agentKey: a.agent_key,
          name: a.display_name || a.name,
          status: mapAgentStatus(a),
          description: a.description || a.role || '',
          sources: SOURCE_MAP[a.agent_key] || [],
          successRate: a.success_rate != null ? Math.round(a.success_rate * 100) : null,
          lastRun: a.last_active,
        })))
      })
      .catch((err) => {
        console.error('Failed to fetch agents:', err.message)
        setError('Could not connect to backend. Make sure the API server is running on port 8000.')
        setAgents([])
      })
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all'
    ? agents
    : agents.filter(a => a.status === filter)

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map(i => <LoadingSkeleton key={i} />)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Filter bar */}
      <div className="flex items-center gap-2">
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className="px-3 py-1.5 text-xs font-medium rounded-full cursor-pointer transition-colors duration-150 capitalize"
            style={{
              background: filter === f ? 'var(--primary)' : 'var(--bg-hover)',
              color: filter === f ? 'var(--primary-contrast)' : 'var(--text-secondary)',
            }}
          >
            {f === 'inactive' ? 'Not configured' : f}
            {f !== 'all' && (
              <span className="ml-1 opacity-60">
                ({agents.filter(a => a.status === f).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg p-4 text-sm" style={{ background: 'color-mix(in srgb, var(--status-danger) 10%, transparent)', color: 'var(--status-danger)', border: '1px solid var(--status-danger)' }}>
          {error}
        </div>
      )}

      {/* Agent grid */}
      {filtered.length === 0 && !error ? (
        <EmptyState icon={Bot} title="No agents match filter" description="Try a different filter." />
      ) : (
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5 gap-4"
          initial="hidden" animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.05 } } }}
        >
          {filtered.map(agent => (
            <motion.div
              key={agent.id}
              variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
            >
              <AgentCard agent={agent} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  )
}
