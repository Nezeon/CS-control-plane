import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Users, Ticket, AlertTriangle, Bot } from 'lucide-react'
import useDashboardStore from '../stores/dashboardStore'
import MetricCard from '../components/shared/MetricCard'
import ActivityFeed from '../components/shared/ActivityFeed'
import AgentStatusBadge from '../components/agents/AgentStatusBadge'
import HealthRing from '../components/shared/HealthRing'
import StatusPill from '../components/shared/StatusPill'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { dashboardApi } from '../services/dashboardApi'

/* 5 agents that are fully operational (keys match backend AGENT_REGISTRY) */
const ACTIVE_AGENT_KEYS = [
  'cso_orchestrator', 'customer_memory', 'presales_funnel',
  'triage_agent', 'health_monitor_agent',
]

export default function DashboardPage() {
  const { stats, quickHealth, events, isLoading, fetchAll } = useDashboardStore()
  const [agents, setAgents] = useState([])

  useEffect(() => { fetchAll() }, [fetchAll])

  /* Fetch real agent list */
  useEffect(() => {
    dashboardApi.getAgents()
      .then(({ data }) => setAgents(Array.isArray(data) ? data : data?.agents || []))
      .catch(() => {})
  }, [])

  if (isLoading && !stats) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <LoadingSkeleton key={i} />)}
        </div>
      </div>
    )
  }

  /* Build activity from real events only */
  const activityItems = (events || []).slice(0, 15).map(evt => ({
    id: evt.id,
    message: evt.description || evt.event_type?.replace(/_/g, ' ') || 'Event',
    type: evt.status === 'error' ? 'error' : 'info',
    timestamp: evt.created_at || evt.timestamp,
    agentName: evt.routed_to || evt.agent_name || '',
  }))

  /* Map agent status for mini grid */
  const activeCount = ACTIVE_AGENT_KEYS.length
  const miniAgents = agents.length > 0
    ? agents.map(a => ({
        id: a.id || a.agent_key,
        name: a.display_name || a.name,
        status: ACTIVE_AGENT_KEYS.includes(a.agent_key)
          ? (a.status === 'active' ? 'running' : a.status || 'idle')
          : 'idle',
      }))
    : []

  const trends = stats?.trends || {}

  return (
    <div className="flex gap-6 h-full">
      {/* Left Column (70%) */}
      <div className="flex-[7] space-y-6 min-w-0">
        {/* KPI Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Active Customers"
            value={stats?.total_customers ?? '—'}
            delta={trends.customers_change != null ? `${trends.customers_change > 0 ? '+' : ''}${trends.customers_change}` : null}
            deltaType={trends.customers_change > 0 ? 'positive' : trends.customers_change < 0 ? 'negative' : 'neutral'}
            icon={Users}
          />
          <MetricCard
            title="Active Agents"
            value={`${activeCount}/10`}
            delta={null}
            deltaType="neutral"
            icon={Bot}
          />
          <MetricCard
            title="Open Jira Tickets"
            value={stats?.open_tickets ?? '—'}
            delta={trends.tickets_change != null ? `${trends.tickets_change > 0 ? '+' : ''}${trends.tickets_change}` : null}
            deltaType={trends.tickets_change < 0 ? 'positive' : trends.tickets_change > 0 ? 'negative' : 'neutral'}
            icon={Ticket}
          />
          <MetricCard
            title="At Risk"
            value={stats?.at_risk_count ?? '—'}
            delta={trends.risk_change != null ? `${trends.risk_change > 0 ? '+' : ''}${trends.risk_change}` : null}
            deltaType={trends.risk_change > 0 ? 'negative' : trends.risk_change < 0 ? 'positive' : 'neutral'}
            icon={AlertTriangle}
          />
        </div>

        {/* Agent Status Grid */}
        {miniAgents.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Agent Status</h2>
              <Link to="/agents" className="text-xs cursor-pointer transition-colors duration-150" style={{ color: 'var(--primary)' }}>
                View all
              </Link>
            </div>
            <motion.div
              className="grid grid-cols-2 md:grid-cols-5 gap-3"
              initial="hidden" animate="visible"
              variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.04 } } }}
            >
              {miniAgents.map(agent => (
                <motion.div
                  key={agent.id}
                  variants={{ hidden: { opacity: 0, y: 8 }, visible: { opacity: 1, y: 0 } }}
                  className="rounded-lg p-3 flex flex-col gap-2 transition-colors duration-150"
                  style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}
                >
                  <span className="text-xs font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                    {agent.name}
                  </span>
                  <AgentStatusBadge status={agent.status} />
                </motion.div>
              ))}
            </motion.div>
          </div>
        )}

        {/* At-Risk Customer Preview */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>At-Risk Customers</h2>
            <Link to="/customers" className="text-xs cursor-pointer transition-colors duration-150" style={{ color: 'var(--primary)' }}>
              View all
            </Link>
          </div>
          <div className="rounded-lg overflow-hidden" style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th className="text-left px-4 py-2.5 text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Customer</th>
                  <th className="text-left px-4 py-2.5 text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Health</th>
                  <th className="text-left px-4 py-2.5 text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Risk</th>
                  <th className="text-left px-4 py-2.5 text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Tickets</th>
                </tr>
              </thead>
              <tbody>
                {(quickHealth || [])
                  .filter(c => c.risk_level && c.risk_level !== 'healthy')
                  .slice(0, 5)
                  .map(c => (
                    <tr key={c.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td className="px-4 py-2.5">
                        <Link to={`/customers/${c.id}`} className="text-sm font-medium transition-colors duration-150" style={{ color: 'var(--text-primary)' }}>
                          {c.name}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <HealthRing score={c.health_score} size={20} strokeWidth={3} />
                          <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{c.health_score ?? '—'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5"><StatusPill status={c.risk_level || 'healthy'} /></td>
                      <td className="px-4 py-2.5 text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{c.open_ticket_count || 0}</td>
                    </tr>
                  ))
                }
                {(!quickHealth || quickHealth.filter(c => c.risk_level && c.risk_level !== 'healthy').length === 0) && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
                      No at-risk customers
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Right Column (30%) */}
      <div className="flex-[3] min-w-[280px]">
        <ActivityFeed items={activityItems} />
      </div>
    </div>
  )
}
