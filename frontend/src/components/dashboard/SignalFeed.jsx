import { m } from 'framer-motion'
import { Radar } from 'lucide-react'
import useDashboardStore from '../../stores/dashboardStore'
import AgentAvatar from '../shared/AgentAvatar'
import { formatRelativeTime } from '../../utils/formatters'

const EVENT_COLORS = {
  jira_ticket_created: { bar: '#3B9EFF', label: 'JIRA' },
  fathom_call_processed: { bar: '#00E5C4', label: 'CALL' },
  daily_health_check: { bar: '#7C5CFC', label: 'HEALTH' },
  alert_fired: { bar: '#FF5C5C', label: 'ALERT' },
  new_alert: { bar: '#FFB547', label: 'WATCH' },
}

const AGENT_MAP = {
  jira_ticket_created: { name: 'Ticket Triage', tier: 3 },
  fathom_call_processed: { name: 'Fathom Agent', tier: 3 },
  daily_health_check: { name: 'Health Monitor', tier: 3 },
  alert_fired: { name: 'Escalation Agent', tier: 3 },
  new_alert: { name: 'Health Monitor', tier: 3 },
}

export default function SignalFeed() {
  const events = useDashboardStore((s) => s.events)
  const displayEvents = events?.slice(0, 10) || []

  return (
    <div className="glass-near gradient-border rounded-2xl p-5 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Radar className="w-4 h-4 text-accent" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-accent animate-pulse-subtle" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary font-display tracking-wide">
            LIVE SIGNALS
          </h2>
        </div>
        <span className="text-xxs text-text-ghost font-mono tabular-nums">
          {events?.length || 0} captured
        </span>
      </div>

      {/* Event list with scanline */}
      <div className="flex-1 overflow-y-auto min-h-0 scanline-overlay relative">
        {displayEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="relative">
              <Radar className="w-10 h-10 text-text-ghost" />
              <span className="absolute inset-0 rounded-full border border-accent/20 animate-idle-ring" />
              <span className="absolute inset-0 rounded-full border border-accent/10 animate-idle-ring" style={{ animationDelay: '0.8s' }} />
            </div>
            <p className="text-sm text-text-muted mt-4">Awaiting signals...</p>
            <p className="text-xxs text-text-ghost mt-1">Events will stream here in real-time</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {displayEvents.map((event, i) => {
              const config = EVENT_COLORS[event.type] || { bar: '#5C5C72', label: 'SYS' }
              const agentInfo = AGENT_MAP[event.type] || { name: 'Orchestrator', tier: 1 }

              return (
                <m.div
                  key={event.id || i}
                  initial={i === 0 ? { opacity: 0, x: -8 } : false}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.25 }}
                  className="flex items-start gap-3 py-2.5 px-2 rounded-lg hover:bg-bg-active/40 transition-colors group relative"
                >
                  {/* Colored left bar */}
                  <div
                    className="w-0.5 self-stretch rounded-full shrink-0"
                    style={{ background: config.bar, boxShadow: `0 0 4px ${config.bar}40` }}
                  />

                  {/* Agent avatar */}
                  <AgentAvatar
                    name={agentInfo.name}
                    tier={agentInfo.tier}
                    size="sm"
                    status="idle"
                    className="mt-0.5 shrink-0"
                  />

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span
                        className="text-xxs font-mono font-semibold tracking-wider"
                        style={{ color: config.bar }}
                      >
                        {config.label}
                      </span>
                      <span className="text-xxs text-text-ghost font-mono tabular-nums">
                        {formatRelativeTime(event.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                      {event.message}
                    </p>
                  </div>

                  {/* Hover glow */}
                  <div
                    className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
                    style={{ boxShadow: `inset 0 0 20px ${config.bar}08` }}
                  />
                </m.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
