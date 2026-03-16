import { m } from 'framer-motion'
import { cn } from '../../utils/cn'
import { formatTime } from '../../utils/formatters'
import AgentAvatar from '../shared/AgentAvatar'
import TierBadge from '../shared/TierBadge'
import { AGENT_TIERS, AGENT_NAMES } from '../../data/conversations'

// Tier-based indentation
const tierIndent = {
  1: 'ml-0',
  2: 'ml-6 sm:ml-8',
  3: 'ml-12 sm:ml-16',
  4: 'ml-6 sm:ml-8',
}

// Message type border colors
const typeColors = {
  task_assignment: 'border-l-accent',
  deliverable: 'border-l-teal',
  escalation: 'border-l-status-danger',
  request: 'border-l-status-warning',
  feedback: 'border-l-sky',
}

// Type badge color combos
const typeBadgeColors = {
  task_assignment: 'bg-accent-subtle text-accent',
  deliverable: 'bg-teal-subtle text-teal',
  escalation: 'bg-red-500/10 text-status-danger',
  request: 'bg-amber-500/10 text-status-warning',
  feedback: 'bg-sky-subtle text-sky',
}

// Direction arrows
const directionLabel = {
  down: '\u2193 down',
  up: '\u2191 up',
  sideways: '\u2194 sideways',
}

const directionColors = {
  down: 'text-accent',
  up: 'text-teal',
  sideways: 'text-status-warning',
}

function TypeBadge({ type }) {
  return (
    <span className={cn('px-1.5 py-0.5 rounded text-xxs font-mono', typeBadgeColors[type] || 'bg-bg-active text-text-muted')}>
      {(type || '').replace(/_/g, ' ')}
    </span>
  )
}

function DirectionBadge({ direction }) {
  return (
    <span className={cn('text-xxs font-mono', directionColors[direction] || 'text-text-ghost')}>
      {directionLabel[direction] || direction}
    </span>
  )
}

export default function MessageBubble({ message }) {
  const tier = AGENT_TIERS[message.from_agent] || 3
  const fromName = message.from_name || AGENT_NAMES[message.from_agent] || message.from_agent
  const toName = message.to_name || AGENT_NAMES[message.to_agent] || message.to_agent

  return (
    <m.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn('flex gap-3', tierIndent[tier])}
    >
      <AgentAvatar name={fromName} tier={tier} size="sm" className="mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        {/* Header: name, tier, direction, time */}
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span className="text-sm font-semibold text-text-primary">{fromName}</span>
          <TierBadge tier={tier} />
          <span className="text-xxs text-text-ghost">&rarr; {toName}</span>
          <span className="text-xxs text-text-ghost ml-auto shrink-0">
            {formatTime(message.created_at)}
          </span>
        </div>

        {/* Content */}
        <div
          className={cn(
            'rounded-xl p-3 text-sm text-text-secondary leading-relaxed',
            'border-l-2',
            typeColors[message.message_type] || 'border-l-border'
          )}
          style={{ background: 'rgba(12, 13, 22, 0.5)' }}
        >
          {message.content}
        </div>

        {/* Footer: type badge, direction, priority */}
        <div className="flex items-center gap-2 mt-1.5">
          <TypeBadge type={message.message_type} />
          <DirectionBadge direction={message.direction} />
          {message.priority === 'critical' && (
            <span className="text-xxs text-status-danger font-mono">CRITICAL</span>
          )}
        </div>
      </div>
    </m.div>
  )
}
