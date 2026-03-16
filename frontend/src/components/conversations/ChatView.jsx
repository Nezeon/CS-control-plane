import { useRef, useEffect } from 'react'
import { cn } from '../../utils/cn'
import { formatRelativeTime } from '../../utils/formatters'
import GlassCard from '../shared/GlassCard'
import MessageBubble from './MessageBubble'

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

export default function ChatView({ thread, messages }) {
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  return (
    <GlassCard level="near" className="flex flex-col h-full p-0 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border-subtle flex items-center gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <h3 className="text-sm font-semibold text-text-primary truncate">
              {thread.customer_name}
            </h3>
            <span
              className={cn(
                'px-1.5 py-0.5 rounded text-xxs font-mono shrink-0',
                eventTypeBg[thread.event_type] || 'bg-bg-active text-text-muted'
              )}
            >
              {eventTypeLabels[thread.event_type] || thread.event_type}
            </span>
            {thread.priority === 'critical' && (
              <span className="px-1.5 py-0.5 rounded text-xxs font-mono bg-red-500/10 text-status-danger shrink-0">
                CRITICAL
              </span>
            )}
          </div>
          <p className="text-xs text-text-muted truncate">
            {thread.summary ?? thread.subject ?? ''}
          </p>
        </div>
        <span className="text-xxs text-text-ghost font-mono shrink-0">
          {formatRelativeTime(thread.started_at ?? thread.created_at)}
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </GlassCard>
  )
}
