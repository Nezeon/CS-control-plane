import { useRef, useEffect } from 'react'
import { AnimatePresence, m } from 'framer-motion'
import {
  ArrowDown, ArrowUp, RefreshCw, AlertTriangle,
  CheckCircle2, Zap, FileText, Brain,
} from 'lucide-react'
import { cn } from '../../utils/cn'
import AgentAvatar from './AgentAvatar'

const AGENT_NAMES = {
  cso_orchestrator: 'Naveen Kapoor',
  support_lead: 'Rachel Torres',
  value_lead: 'Damon Reeves',
  delivery_lead: 'Priya Mehta',
  triage_agent: 'Kai Nakamura',
  troubleshooter: 'Leo Petrov',
  escalation_summary: 'Maya Santiago',
  health_monitor: 'Dr. Aisha Okafor',
  fathom_agent: 'Jordan Ellis',
  qbr_value: 'Sofia Marquez',
  sow_prerequisite: 'Ethan Brooks',
  deployment_intelligence: 'Zara Kim',
  customer_memory: 'Atlas',
  meeting_followup: 'Riley Park',
}

const AGENT_TIERS = {
  cso_orchestrator: 1,
  support_lead: 2, value_lead: 2, delivery_lead: 2,
  triage_agent: 3, troubleshooter: 3, escalation_summary: 3,
  health_monitor: 3, fathom_agent: 3, qbr_value: 3,
  sow_prerequisite: 3, deployment_intelligence: 3,
  customer_memory: 4, meeting_followup: 3,
}

const EVENT_CONFIG = {
  task_assigned: {
    icon: ArrowDown,
    color: 'text-teal',
    bg: 'bg-teal/10',
    border: 'border-teal/20',
    label: 'Task Assigned',
  },
  deliverable: {
    icon: ArrowUp,
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    border: 'border-emerald-400/20',
    label: 'Deliverable',
  },
  rework_requested: {
    icon: RefreshCw,
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
    border: 'border-amber-400/20',
    label: 'Rework Requested',
  },
  auto_escalation: {
    icon: AlertTriangle,
    color: 'text-rose-400',
    bg: 'bg-rose-400/10',
    border: 'border-rose-400/20',
    label: 'Auto-Escalated',
  },
  quality_gate_failed: {
    icon: RefreshCw,
    color: 'text-orange-400',
    bg: 'bg-orange-400/10',
    border: 'border-orange-400/20',
    label: 'Quality Gate Failed',
  },
  brief_created: {
    icon: FileText,
    color: 'text-violet-400',
    bg: 'bg-violet-400/10',
    border: 'border-violet-400/20',
    label: 'Brief Created',
  },
  escalation: {
    icon: AlertTriangle,
    color: 'text-rose-400',
    bg: 'bg-rose-400/10',
    border: 'border-rose-400/20',
    label: 'Escalation',
  },
}

function ChainEvent({ event, isLast }) {
  const config = EVENT_CONFIG[event.type] || EVENT_CONFIG.task_assigned
  const Icon = config.icon
  const fromName = AGENT_NAMES[event.from_agent] || event.from_agent || '?'
  const toName = AGENT_NAMES[event.to_agent] || event.to_agent || event.specialist || ''

  // Build description based on event type
  let description = ''
  if (event.type === 'task_assigned') {
    description = event.brief_objective || `Delegated to ${toName}`
  } else if (event.type === 'rework_requested') {
    description = event.feedback || 'Output did not meet criteria'
  } else if (event.type === 'auto_escalation') {
    description = event.reason || `Low confidence`
  } else if (event.type === 'quality_gate_failed') {
    description = event.feedback || 'Quality gate failed'
  } else if (event.type === 'brief_created') {
    description = event.brief_objective || 'Structured brief generated'
  } else if (event.type === 'deliverable') {
    description = event.summary || 'Results delivered'
  } else if (event.type === 'escalation') {
    description = event.reason || 'Escalated to supervisor'
  }

  return (
    <m.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
      className="flex gap-3 relative"
    >
      {/* Timeline connector */}
      <div className="flex flex-col items-center shrink-0">
        <div className={cn(
          'w-7 h-7 rounded-full flex items-center justify-center',
          config.bg, 'border', config.border,
        )}>
          <Icon className={cn('w-3.5 h-3.5', config.color)} />
        </div>
        {!isLast && (
          <div className="w-px flex-1 min-h-[16px] bg-border-subtle/50 mt-1" />
        )}
      </div>

      {/* Content */}
      <div className="pb-3 flex-1 min-w-0">
        {/* Header: label + agents */}
        <div className="flex items-center gap-2 mb-0.5">
          <span className={cn('text-xxs font-semibold uppercase tracking-wider', config.color)}>
            {config.label}
          </span>
          {event.score != null && (
            <span className={cn(
              'text-xxs font-mono px-1.5 py-0.5 rounded',
              event.score >= 0.7 ? 'bg-emerald-500/10 text-emerald-400' :
              event.score >= 0.4 ? 'bg-amber-500/10 text-amber-400' :
              'bg-rose-500/10 text-rose-400',
            )}>
              {(event.score * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {/* Agent avatars */}
        <div className="flex items-center gap-1.5 mb-1">
          {event.from_agent && (
            <div className="flex items-center gap-1">
              <AgentAvatar
                name={fromName}
                tier={AGENT_TIERS[event.from_agent] || 3}
                size="sm"
                className="!w-5 !h-5 !text-[8px]"
              />
              <span className="text-xxs text-text-muted">{fromName}</span>
            </div>
          )}
          {event.to_agent && (
            <>
              <ArrowDown className="w-3 h-3 text-text-ghost" />
              <div className="flex items-center gap-1">
                <AgentAvatar
                  name={toName}
                  tier={AGENT_TIERS[event.to_agent] || 3}
                  size="sm"
                  className="!w-5 !h-5 !text-[8px]"
                />
                <span className="text-xxs text-text-muted">{toName}</span>
              </div>
            </>
          )}
        </div>

        {/* Description */}
        {description && (
          <p className="text-xxs text-text-ghost leading-relaxed line-clamp-2">
            {description}
          </p>
        )}

        {/* Success criteria pills */}
        {event.brief_success_criteria?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {event.brief_success_criteria.slice(0, 3).map((c, i) => (
              <span
                key={i}
                className="px-1.5 py-0.5 rounded text-xxs bg-white/5 text-text-ghost border border-white/5 truncate max-w-[200px]"
              >
                {c}
              </span>
            ))}
          </div>
        )}
      </div>
    </m.div>
  )
}

export default function ThinkingChain({ events = [] }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events.length])

  if (events.length === 0) return null

  return (
    <m.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.25 }}
      className="border-t border-border-subtle"
    >
      <div className="px-4 py-2 flex items-center gap-2 border-b border-border-subtle/50">
        <Brain className="w-3.5 h-3.5 text-violet-400" />
        <span className="text-xxs font-semibold text-text-muted uppercase tracking-wider">
          Agent Thinking Chain
        </span>
        <span className="text-xxs font-mono text-text-ghost ml-auto">
          {events.length} step{events.length !== 1 ? 's' : ''}
        </span>
      </div>
      <div ref={scrollRef} className="px-4 py-3 max-h-[200px] overflow-y-auto">
        <AnimatePresence>
          {events.map((event, i) => (
            <ChainEvent
              key={`${event.type}-${event.timestamp}-${i}`}
              event={event}
              isLast={i === events.length - 1}
            />
          ))}
        </AnimatePresence>
      </div>
    </m.div>
  )
}
