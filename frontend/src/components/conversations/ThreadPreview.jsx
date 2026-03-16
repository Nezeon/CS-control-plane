import { cn } from '../../utils/cn'
import { formatRelativeTime } from '../../utils/formatters'
import { Users, MessageSquare } from 'lucide-react'

const priorityBorder = {
  critical: 'border-l-status-danger',
  high: 'border-l-status-warning',
  medium: 'border-l-transparent',
  low: 'border-l-transparent',
  normal: 'border-l-transparent',
}

const eventTypeLabels = {
  jira_ticket_created: 'Ticket',
  fathom_call_processed: 'Call',
  daily_health_check: 'Health',
  health_check: 'Health',
  alert_fired: 'Alert',
  qbr_scheduled: 'QBR',
  deployment_event: 'Deploy',
}

const eventTypeBg = {
  jira_ticket_created: 'bg-accent-subtle text-accent',
  fathom_call_processed: 'bg-sky-subtle text-sky',
  daily_health_check: 'bg-teal-subtle text-teal',
  health_check: 'bg-teal-subtle text-teal',
  alert_fired: 'bg-red-500/10 text-status-danger',
  qbr_scheduled: 'bg-teal-subtle text-teal',
  deployment_event: 'bg-sky-subtle text-sky',
}

export default function ThreadPreview({ thread, selected, onClick }) {
  const agentCount = thread.agents_involved?.length ?? thread.agent_count ?? 0
  const messageCount = thread.message_count ?? 0
  const subject = thread.summary ?? thread.subject ?? ''

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-left px-4 py-3 border-l-2 transition-colors',
        'border-b border-border-subtle',
        'hover:bg-bg-hover',
        priorityBorder[thread.priority] || priorityBorder.normal,
        selected && 'bg-accent-subtle border-l-accent'
      )}
    >
      {/* Top row: customer + event badge */}
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm font-semibold text-text-primary truncate flex-1">
          {thread.customer_name}
        </span>
        <span
          className={cn(
            'px-1.5 py-0.5 rounded text-xxs font-mono shrink-0',
            eventTypeBg[thread.event_type] || 'bg-bg-active text-text-muted'
          )}
        >
          {eventTypeLabels[thread.event_type] || thread.event_type}
        </span>
      </div>

      {/* Subject */}
      <p className="text-xs text-text-secondary truncate mb-1.5">
        {subject}
      </p>

      {/* Bottom row: meta info */}
      <div className="flex items-center gap-3 text-xxs text-text-ghost">
        <span className="inline-flex items-center gap-1">
          <Users className="w-3 h-3" />
          {agentCount} agents
        </span>
        <span className="inline-flex items-center gap-1">
          <MessageSquare className="w-3 h-3" />
          {messageCount} msgs
        </span>
        <span className="ml-auto">
          {formatRelativeTime(thread.last_message_at)}
        </span>
      </div>
    </button>
  )
}
