import { useEffect, useState } from 'react'
import useAgentStore from '../stores/agentStore'
import GlassCard from '../components/shared/GlassCard'
import AgentAvatar from '../components/shared/AgentAvatar'
import TierBadge from '../components/shared/TierBadge'
import StatusPill from '../components/shared/StatusPill'
import PillFilter from '../components/shared/PillFilter'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { getLaneColor, formatRelativeTime } from '../utils/formatters'
import { X } from 'lucide-react'

const TIER_OPTIONS = [
  { value: '', label: 'All Tiers' },
  { value: '1', label: 'T1 Supervisor' },
  { value: '2', label: 'T2 Lane Leads' },
  { value: '3', label: 'T3 Specialists' },
  { value: '4', label: 'T4 Foundation' },
]

export default function AgentsPage() {
  const {
    agents, isLoading, fetchAll,
    selectedAgentDetail, agentLogs, logsLoading,
    brainPanelOpen, selectAgent, closeBrainPanel,
  } = useAgentStore()

  const [tierFilter, setTierFilter] = useState('')

  useEffect(() => { fetchAll() }, [fetchAll])

  const filtered = tierFilter
    ? agents.filter((a) => String(a.tier) === tierFilter)
    : agents

  // Sort by tier
  const sorted = [...filtered].sort((a, b) => (a.tier || 99) - (b.tier || 99))

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-display font-bold text-text-primary">AI Agents</h1>

      <PillFilter options={TIER_OPTIONS} value={tierFilter} onChange={setTierFilter} />

      {isLoading && agents.length === 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <LoadingSkeleton key={i} variant="card" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sorted.map((agent) => (
            <GlassCard
              key={agent.agent_key || agent.name}
              level="near"
              interactive
              className="cursor-pointer hover:border-accent/30 transition-all"
              onClick={() => selectAgent(agent.agent_key || agent.name)}
            >
              <div className="flex items-start gap-3">
                <AgentAvatar
                  name={agent.human_name || agent.display_name || agent.name}
                  tier={agent.tier}
                  status={agent.status}
                  size="md"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-text-primary truncate">
                      {agent.human_name || agent.display_name || agent.name}
                    </h3>
                    <TierBadge tier={agent.tier} />
                  </div>
                  <p className="text-xs text-text-muted mt-0.5 truncate">
                    {agent.role || agent.codename || agent.display_name}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <StatusPill status={agent.status || 'idle'} />
                    {agent.lane && (
                      <span
                        className="text-xxs font-mono px-1.5 py-0.5 rounded"
                        style={{
                          color: getLaneColor(agent.lane),
                          backgroundColor: `${getLaneColor(agent.lane)}15`,
                        }}
                      >
                        {agent.lane}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Traits */}
              {agent.traits && agent.traits.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {agent.traits.slice(0, 4).map((trait) => (
                    <span
                      key={typeof trait === 'string' ? trait : trait.name}
                      className="text-xxs px-1.5 py-0.5 rounded bg-bg-active text-text-ghost"
                    >
                      {typeof trait === 'string' ? trait : trait.name}
                    </span>
                  ))}
                  {agent.traits.length > 4 && (
                    <span className="text-xxs text-text-ghost">+{agent.traits.length - 4}</span>
                  )}
                </div>
              )}

              {/* Tools count */}
              {agent.tools && agent.tools.length > 0 && (
                <p className="text-xxs text-text-ghost mt-2 font-mono">
                  {agent.tools.length} tools available
                </p>
              )}
            </GlassCard>
          ))}
        </div>
      )}

      {/* Agent Detail Panel */}
      {brainPanelOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/40" onClick={closeBrainPanel} />
          <div className="relative w-full max-w-lg bg-bg-subtle border-l border-border-subtle overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-display font-bold text-text-primary">Agent Profile</h2>
                <button onClick={closeBrainPanel} className="p-1 rounded text-text-ghost hover:text-text-primary">
                  <X size={18} />
                </button>
              </div>

              {selectedAgentDetail ? (
                <div className="space-y-5">
                  {/* Identity */}
                  <div className="flex items-center gap-3">
                    <AgentAvatar
                      name={selectedAgentDetail.human_name || selectedAgentDetail.name}
                      tier={selectedAgentDetail.tier}
                      status={selectedAgentDetail.status}
                      size="lg"
                    />
                    <div>
                      <h3 className="text-base font-semibold text-text-primary">
                        {selectedAgentDetail.human_name || selectedAgentDetail.name}
                      </h3>
                      <p className="text-sm text-text-muted">
                        {selectedAgentDetail.role || selectedAgentDetail.codename}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <TierBadge tier={selectedAgentDetail.tier} />
                        <StatusPill status={selectedAgentDetail.status || 'idle'} />
                      </div>
                    </div>
                  </div>

                  {/* Personality */}
                  {selectedAgentDetail.personality && (
                    <GlassCard level="mid">
                      <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Personality</h4>
                      <p className="text-sm text-text-secondary">{selectedAgentDetail.personality}</p>
                    </GlassCard>
                  )}

                  {/* Traits */}
                  {selectedAgentDetail.traits?.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Traits</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedAgentDetail.traits.map((t) => (
                          <span
                            key={typeof t === 'string' ? t : t.name}
                            className="text-xs px-2 py-1 rounded-full bg-accent/10 text-accent"
                          >
                            {typeof t === 'string' ? t : t.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tools */}
                  {selectedAgentDetail.tools?.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Tools</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedAgentDetail.tools.map((tool) => (
                          <span
                            key={typeof tool === 'string' ? tool : tool.name}
                            className="text-xs px-2 py-1 rounded-full bg-bg-active text-text-secondary font-mono"
                          >
                            {typeof tool === 'string' ? tool : tool.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Manages */}
                  {selectedAgentDetail.manages?.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Manages</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedAgentDetail.manages.map((m) => (
                          <span key={m} className="text-xs px-2 py-1 rounded-full bg-bg-active text-text-secondary">
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent Logs */}
                  <div>
                    <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Recent Activity</h4>
                    {logsLoading ? (
                      <LoadingSkeleton variant="text" count={3} />
                    ) : agentLogs.length === 0 ? (
                      <p className="text-xs text-text-ghost">No recent activity</p>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {agentLogs.slice(0, 10).map((log, i) => (
                          <div key={log.id || i} className="p-2 rounded-lg bg-bg-hover/30">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-text-secondary">{log.action || log.event_type}</span>
                              <span className="text-xxs text-text-ghost font-mono">
                                {formatRelativeTime(log.created_at)}
                              </span>
                            </div>
                            {log.customer_name && (
                              <span className="text-xxs text-text-muted">{log.customer_name}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <LoadingSkeleton variant="text" count={5} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
