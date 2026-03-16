import { useEffect, useRef, useCallback } from 'react'
import { m } from 'framer-motion'
import { X, Zap, Clock, CheckCircle, Activity } from 'lucide-react'
import StatusIndicator from '../shared/StatusIndicator'
import ReasoningLog from './ReasoningLog'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { getLaneColor, formatRelativeTime } from '../../utils/formatters'

function StatBox({ icon: Icon, label, value, color }) {
  return (
    <div className="p-3 rounded-lg bg-bg-active border border-border-subtle text-center">
      <Icon className="w-3.5 h-3.5 mx-auto mb-1" style={{ color: color || 'var(--text-ghost)' }} />
      <div className="text-sm font-bold text-text-primary tabular-nums">{value}</div>
      <div className="text-[9px] font-mono text-text-ghost uppercase">{label}</div>
    </div>
  )
}

export default function AgentBrainPanel({ agent, logs, logsLoading, onClose }) {
  const panelRef = useRef(null)

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose?.()
  }, [onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (!agent) return null

  const laneColor = getLaneColor(agent.lane)

  return (
    <>
      {/* Backdrop */}
      <m.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Drawer (right side) */}
      <m.div
        data-testid="agent-brain-panel"
        ref={panelRef}
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed right-0 top-0 bottom-0 z-50 w-full md:w-[420px] max-w-md"
      >
        <div className="card-elevated h-full overflow-y-auto scrollbar-thin rounded-l-2xl border-l border-border">
          <div className="p-5 space-y-5">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg shrink-0"
                  style={{
                    backgroundColor: `${laneColor}15`,
                    border: `1px solid ${laneColor}30`,
                    color: laneColor,
                  }}
                >
                  {(agent.display_name || agent.name || '?')[0]?.toUpperCase()}
                </div>
                <div className="min-w-0">
                  <div className="font-semibold text-text-primary text-sm truncate">
                    {(agent.display_name || agent.name || '').replace(/_/g, ' ')}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusIndicator status={agent.status} size="sm" showLabel />
                    {agent.lane && (
                      <span
                        className="px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold uppercase"
                        style={{ backgroundColor: `${laneColor}12`, color: laneColor }}
                      >
                        {agent.lane}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <button onClick={onClose} className="p-2 rounded-lg hover:bg-bg-active text-text-ghost hover:text-text-primary transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-2">
              <StatBox icon={Zap} label="Tasks" value={agent.tasks_today ?? 0} color={laneColor} />
              <StatBox icon={Clock} label="Avg" value={agent.avg_response_ms != null ? `${(agent.avg_response_ms / 1000).toFixed(1)}s` : '—'} color="#3B9EFF" />
              <StatBox icon={CheckCircle} label="Success" value={agent.success_rate != null ? `${Math.round(agent.success_rate)}%` : '—'} color="#00E5A0" />
              <StatBox icon={Activity} label="Total" value={agent.total_executions ?? 0} />
            </div>

            {/* Current task */}
            {agent.current_task && (
              <div className="p-3 rounded-lg bg-accent/5 border border-accent/15">
                <div className="text-[10px] text-accent/60 font-mono uppercase mb-1">Current Task</div>
                <div className="text-xs text-text-primary">{agent.current_task}</div>
              </div>
            )}

            {/* Last active */}
            {agent.last_active && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-text-ghost font-mono">Last active</span>
                <span className="text-text-muted">{formatRelativeTime(agent.last_active)}</span>
              </div>
            )}

            {/* Description */}
            {agent.description && (
              <div>
                <h4 className="text-[10px] font-mono text-text-ghost uppercase tracking-wider mb-1">Description</h4>
                <p className="text-xs text-text-secondary leading-relaxed">{agent.description}</p>
              </div>
            )}

            {/* Capabilities */}
            {agent.capabilities?.length > 0 && (
              <div>
                <h4 className="text-[10px] font-mono text-text-ghost uppercase tracking-wider mb-2">Capabilities</h4>
                <div className="flex flex-wrap gap-1.5">
                  {agent.capabilities.map((cap, i) => (
                    <span key={cap} className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-bg-active text-text-muted border border-border-subtle">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Reasoning Log */}
            <div>
              <h4 className="text-[10px] font-mono text-text-ghost uppercase tracking-wider mb-2">Reasoning Log</h4>
              <div className="rounded-lg border border-border overflow-hidden" style={{ maxHeight: 300 }}>
                <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border bg-bg-active/50">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-status-danger/60" />
                    <span className="w-2 h-2 rounded-full bg-status-warning/60" />
                    <span className="w-2 h-2 rounded-full bg-status-success/60" />
                  </div>
                  <span className="font-mono text-[10px] text-text-ghost uppercase tracking-wider">terminal</span>
                </div>
                <ReasoningLog logs={logs} isLoading={logsLoading} />
              </div>
            </div>
          </div>
        </div>
      </m.div>
    </>
  )
}
