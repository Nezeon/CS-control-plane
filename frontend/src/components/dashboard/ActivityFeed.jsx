import { m } from 'framer-motion'
import { Radio } from 'lucide-react'
import useDashboardStore from '../../stores/dashboardStore'
import GlassCard from '../shared/GlassCard'
import AgentAvatar from '../shared/AgentAvatar'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { formatRelativeTime } from '../../utils/formatters'

const eventTypeIcons = {
  jira_ticket_created: { name: 'Ticket Triage', tier: 3 },
  fathom_call_processed: { name: 'Fathom Agent', tier: 3 },
  daily_health_check: { name: 'Health Monitor', tier: 3 },
  alert_fired: { name: 'Escalation Agent', tier: 3 },
  new_alert: { name: 'Health Monitor', tier: 3 },
}

export default function ActivityFeed() {
  const events = useDashboardStore((s) => s.events)

  if (!events) {
    return (
      <GlassCard level="near" className="h-full p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-text-primary font-display">Live Activity</h2>
        </div>
        <LoadingSkeleton variant="text" count={6} />
      </GlassCard>
    )
  }

  const displayEvents = events.slice(0, 12)

  return (
    <GlassCard level="near" className="h-full p-5 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Radio className="w-3.5 h-3.5 text-accent" />
          <h2 className="text-sm font-semibold text-text-primary font-display">Live Activity</h2>
        </div>
        <span className="text-xxs text-text-ghost font-mono tabular-nums">
          {events.length} events
        </span>
      </div>

      {/* Event list */}
      <div className="flex-1 overflow-y-auto space-y-1 min-h-0 -mx-1 px-1" style={{ maxHeight: 340 }}>
        {displayEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Radio className="w-8 h-8 text-text-ghost mb-3" />
            <p className="text-sm text-text-muted">No recent activity</p>
            <p className="text-xxs text-text-ghost mt-1">Events will appear here in real-time</p>
          </div>
        ) : (
          displayEvents.map((event, i) => {
            const agentInfo = eventTypeIcons[event.type] || { name: 'CS Orchestrator', tier: 1 }

            return (
              <m.div
                key={event.id || i}
                initial={i === 0 ? { opacity: 0, y: -6 } : false}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className="flex items-start gap-3 py-2 px-2 rounded-lg hover:bg-bg-active/40 transition-colors group"
              >
                <AgentAvatar
                  name={agentInfo.name}
                  tier={agentInfo.tier}
                  size="sm"
                  status="idle"
                  className="mt-0.5 flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                    {event.message}
                  </p>
                  <p className="text-xxs text-text-ghost font-mono tabular-nums mt-0.5">
                    {formatRelativeTime(event.timestamp)}
                  </p>
                </div>
              </m.div>
            )
          })
        )}
      </div>
    </GlassCard>
  )
}
