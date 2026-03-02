import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Cpu, Network, Zap, Clock, CheckCircle } from 'lucide-react'
import useAgentStore from '../stores/agentStore'
import NeuralNetwork from '../components/agents/NeuralNetwork'
import AgentBrainPanel from '../components/agents/AgentBrainPanel'
import StatusIndicator from '../components/shared/StatusIndicator'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { getLaneColor, formatRelativeTime } from '../utils/formatters'

function AgentCard({ agent, onClick }) {
  const laneColor = getLaneColor(agent.lane)
  const isActive = agent.status === 'active' || agent.status === 'processing'

  return (
    <motion.button
      onClick={() => onClick?.(agent.name || agent.agent_key || agent.id)}
      className="card-interactive p-4 text-left w-full"
      whileHover={{ y: -2 }}
      transition={{ duration: 0.15 }}
    >
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm shrink-0"
          style={{
            backgroundColor: `${laneColor}15`,
            border: `1px solid ${laneColor}30`,
            color: laneColor,
          }}
        >
          {(agent.display_name || agent.name || '?')[0]?.toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-text-primary truncate">
              {(agent.display_name || agent.name || '').replace(/_/g, ' ')}
            </span>
            <div className={`w-2 h-2 rounded-full shrink-0 ${isActive ? 'bg-status-success animate-pulse' : 'bg-text-ghost/30'}`} />
          </div>
          {agent.lane && (
            <span
              className="inline-block px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold uppercase"
              style={{ backgroundColor: `${laneColor}12`, color: laneColor }}
            >
              {agent.lane}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-border-subtle">
        <div className="text-center">
          <div className="text-sm font-bold text-text-primary tabular-nums">{agent.tasks_today ?? 0}</div>
          <div className="text-[9px] font-mono text-text-ghost uppercase">Tasks</div>
        </div>
        <div className="text-center">
          <div className="text-sm font-bold text-text-primary tabular-nums">
            {agent.success_rate != null ? `${Math.round(agent.success_rate)}%` : '—'}
          </div>
          <div className="text-[9px] font-mono text-text-ghost uppercase">Success</div>
        </div>
        <div className="text-center">
          <div className="text-sm font-bold text-text-primary tabular-nums">
            {agent.avg_response_ms != null ? `${(agent.avg_response_ms / 1000).toFixed(1)}s` : '—'}
          </div>
          <div className="text-[9px] font-mono text-text-ghost uppercase">Avg</div>
        </div>
      </div>
    </motion.button>
  )
}

export default function AgentsPage() {
  const location = useLocation()
  const [viewMode, setViewMode] = useState('grid')

  const {
    agents, isLoading, selectedAgent, selectedAgentDetail,
    agentLogs, logsLoading, brainPanelOpen,
    fetchAgents, fetchOrchestrationFlow, selectAgent, closeBrainPanel,
  } = useAgentStore()

  useEffect(() => {
    fetchAgents()
    fetchOrchestrationFlow()
  }, [fetchAgents, fetchOrchestrationFlow])

  useEffect(() => {
    if (location.state?.agent && agents.length > 0) {
      selectAgent(location.state.agent)
    }
  }, [location.state, agents.length, selectAgent])

  const stats = useMemo(() => {
    const active = agents.filter((a) => a.status === 'active' || a.status === 'processing').length
    const idle = agents.filter((a) => a.status === 'idle').length
    const totalTasks = agents.reduce((sum, a) => sum + (a.tasks_today || 0), 0)
    return { total: agents.length, active, idle, totalTasks }
  }, [agents])

  return (
    <div className="relative h-full flex flex-col overflow-hidden" data-testid="agents-page">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Agents</h1>
          <div className="flex items-center gap-4 mt-1">
            <span className="text-xs text-text-muted">
              <span className="text-status-success font-semibold">{stats.active}</span> active
            </span>
            <span className="text-xs text-text-muted">
              <span className="text-text-ghost font-semibold">{stats.idle}</span> idle
            </span>
            <span className="text-xs text-text-muted">
              <span className="text-accent font-semibold">{stats.totalTasks}</span> tasks today
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'text-accent bg-accent-subtle' : 'text-text-ghost hover:text-text-muted'}`}
          >
            <Cpu className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('network')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'network' ? 'text-accent bg-accent-subtle' : 'text-text-ghost hover:text-text-muted'}`}
          >
            <Network className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pb-6">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="card p-4"><LoadingSkeleton variant="text" count={4} /></div>
            ))}
          </div>
        ) : agents.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-sm text-text-muted mb-1">No agents configured</p>
              <p className="text-xs text-text-ghost">Agent data will appear once the backend is connected</p>
            </div>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="space-y-6">
            {/* Agent grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
              {agents.map((agent) => (
                <AgentCard key={agent.id || agent.name} agent={agent} onClick={selectAgent} />
              ))}
            </div>

            {/* Recent activity */}
            <div className="card p-0 overflow-hidden">
              <div className="flex items-center justify-between px-4 pt-4 pb-2">
                <h3 className="text-xs text-text-primary font-semibold uppercase tracking-wider">Recent Activity</h3>
              </div>
              <div className="max-h-[240px] overflow-y-auto scrollbar-thin">
                {agentLogs.length > 0 ? (
                  agentLogs.slice(0, 15).map((log, i) => (
                    <div key={log.id || i} className="flex items-center gap-3 px-4 py-2 border-b border-border-subtle last:border-0">
                      <div className="flex items-center gap-2 w-28 shrink-0">
                        <Zap className="w-3 h-3 text-accent" />
                        <span className="text-[10px] font-mono text-accent truncate">{log.agent_name || log.agent}</span>
                      </div>
                      <span className="text-xs text-text-secondary truncate flex-1">{log.message || log.action || log.event_type}</span>
                      <span className="text-[10px] font-mono text-text-ghost shrink-0">{formatRelativeTime(log.timestamp || log.created_at)}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-text-ghost text-xs font-mono">No recent activity</div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full min-h-[400px]">
            <NeuralNetwork agents={agents} selectedAgent={selectedAgent} onAgentClick={selectAgent} />
          </div>
        )}
      </div>

      {/* Brain Panel (right drawer) */}
      <AnimatePresence>
        {brainPanelOpen && (
          <AgentBrainPanel agent={selectedAgentDetail} logs={agentLogs} logsLoading={logsLoading} onClose={closeBrainPanel} />
        )}
      </AnimatePresence>
    </div>
  )
}
