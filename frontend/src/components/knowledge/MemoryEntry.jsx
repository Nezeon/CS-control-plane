import { cn } from '../../utils/cn'
import { formatRelativeTime } from '../../utils/formatters'
import GlassCard from '../shared/GlassCard'
import AgentAvatar from '../shared/AgentAvatar'
import { AGENT_TIERS } from '../../data/conversations'

function ImportanceBar({ value, max = 10 }) {
  const pct = Math.min(100, (value / max) * 100)
  const color =
    value >= 8 ? 'bg-status-danger' : value >= 5 ? 'bg-status-warning' : 'bg-teal'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 rounded-full bg-bg-active overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xxs font-mono text-text-ghost w-4 text-right">{value}</span>
    </div>
  )
}

export default function MemoryEntry({ entry, variant = 'episodic' }) {
  const isEpisodic = variant === 'episodic'
  const tier = AGENT_TIERS[entry.agent_id || entry.published_by] || 3
  const agentName = isEpisodic ? entry.agent_name : entry.published_by_name
  const content = isEpisodic ? entry.summary : entry.content
  const tags = entry.tags || []

  return (
    <GlassCard level="near" className="p-3.5">
      {/* Header */}
      <div className="flex items-start gap-2.5 mb-2">
        <AgentAvatar name={agentName || ''} tier={tier} size="sm" className="mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-text-primary">{agentName}</span>
            {isEpisodic && entry.customer_name && (
              <span className="text-xxs text-text-ghost font-mono">{entry.customer_name}</span>
            )}
            <span className="text-xxs text-text-ghost ml-auto shrink-0">
              {formatRelativeTime(entry.created_at)}
            </span>
          </div>
          {isEpisodic && entry.event_type && (
            <span className="text-xxs text-text-ghost font-mono">
              {entry.event_type.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <p className="text-xs text-text-secondary leading-relaxed mb-2.5">
        {content}
      </p>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 rounded text-xxs font-mono bg-bg-active text-text-muted border border-border-subtle"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* References (knowledge only) */}
      {!isEpisodic && entry.references && entry.references.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {entry.references.map((ref) => (
            <span
              key={ref}
              className="px-1.5 py-0.5 rounded text-xxs font-mono bg-accent-subtle text-accent"
            >
              {ref}
            </span>
          ))}
        </div>
      )}

      {/* Footer: importance + confidence */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <p className="text-xxs font-mono text-text-ghost mb-0.5">Importance</p>
          <ImportanceBar value={entry.importance || 0} />
        </div>
        {entry.confidence != null && (
          <div className="text-right">
            <p className="text-xxs font-mono text-text-ghost mb-0.5">Confidence</p>
            <span className="text-xs font-mono text-teal">{Math.round(entry.confidence * 100)}%</span>
          </div>
        )}
      </div>
    </GlassCard>
  )
}
