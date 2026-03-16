import { AnimatePresence, m } from 'framer-motion'
import { CheckCircle2, XCircle, ChevronDown, Clock, Zap, Target } from 'lucide-react'
import { cn } from '../../utils/cn'
import { formatRelativeTime } from '../../utils/formatters'
import GlassCard from '../shared/GlassCard'
import AgentAvatar from '../shared/AgentAvatar'
import TierBadge from '../shared/TierBadge'
import PipelineTrace from './PipelineTrace'

function formatDuration(ms) {
  if (ms == null) return '--'
  if (ms >= 60000) return `${(ms / 60000).toFixed(1)}m`
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
}

export default function CompletedPipelineCard({ execution, expanded, onToggle }) {
  const isCompleted = execution.status === 'completed'
  const isFailed = execution.status === 'failed'
  const completedStages = execution.rounds?.filter((r) => r.status === 'completed').length || 0
  const totalStages = execution.rounds?.length || 7

  // Calculate duration from timestamps if duration_ms not available at execution level
  const durationMs = execution.duration_ms ?? (
    execution.started_at && execution.completed_at
      ? new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()
      : execution.rounds?.reduce((sum, r) => sum + (r.duration_ms || 0), 0) || null
  )

  return (
    <GlassCard
      level="near"
      interactive
      className={cn('p-0 overflow-hidden', expanded && 'ring-1 ring-accent/20')}
    >
      {/* Collapsed header */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-4 px-4 py-3.5 text-left hover:bg-bg-hover/30 transition-colors"
      >
        {/* Status icon */}
        <div
          className={cn(
            'w-7 h-7 rounded-lg flex items-center justify-center shrink-0',
            isCompleted && 'bg-teal-subtle',
            isFailed && 'bg-red-500/10'
          )}
        >
          {isCompleted ? (
            <CheckCircle2 className="w-4 h-4 text-teal" />
          ) : (
            <XCircle className="w-4 h-4 text-status-danger" />
          )}
        </div>

        {/* Agent info */}
        <div className="flex items-center gap-2.5 w-44 shrink-0">
          <AgentAvatar name={execution.agent_name} tier={execution.tier || execution.agent_tier} size="sm" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{execution.agent_name}</p>
            <div className="flex items-center gap-1.5">
              <TierBadge tier={execution.tier || execution.agent_tier} />
            </div>
          </div>
        </div>

        {/* Customer + event */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="text-xs text-text-secondary truncate">{execution.customer_name}</p>
            {(execution.trigger || execution.event_type || '').startsWith('user_chat_') && (
              <span className="shrink-0 text-xxs px-1.5 py-0.5 rounded bg-accent/10 text-accent border border-accent/20">
                Chat Query
              </span>
            )}
          </div>
          <p className="text-xxs text-text-ghost truncate">{execution.trigger || execution.event_type}</p>
        </div>

        {/* Stages */}
        <span className="text-xs font-mono text-text-muted shrink-0">
          {completedStages}/{totalStages}
        </span>

        {/* Duration */}
        <div className="flex items-center gap-1 shrink-0 w-16">
          <Clock className="w-3 h-3 text-text-ghost" />
          <span className="text-xs font-mono text-text-muted">
            {formatDuration(durationMs)}
          </span>
        </div>

        {/* Tokens */}
        <div className="flex items-center gap-1 shrink-0 w-20">
          <Zap className="w-3 h-3 text-text-ghost" />
          <span className="text-xs font-mono text-text-muted">
            {(execution.total_tokens || 0).toLocaleString()}
          </span>
        </div>

        {/* Confidence / Quality Score */}
        {(execution.confidence != null || execution.quality_score != null) && (
          <div className="flex items-center gap-1 shrink-0 w-16">
            <Target className="w-3 h-3 text-text-ghost" />
            <span className="text-xs font-mono text-teal">
              {Math.round((execution.confidence ?? execution.quality_score) * 100)}%
            </span>
          </div>
        )}

        {/* Chevron */}
        <ChevronDown
          className={cn(
            'w-4 h-4 text-text-ghost transition-transform shrink-0',
            expanded && 'rotate-180'
          )}
        />
      </button>

      {/* Expanded trace */}
      <AnimatePresence>
        {expanded && (
          <m.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <PipelineTrace rounds={execution.rounds} />
          </m.div>
        )}
      </AnimatePresence>
    </GlassCard>
  )
}
