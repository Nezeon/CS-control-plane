import { useState, useEffect, useMemo, useRef } from 'react'
import { Radar } from 'lucide-react'
import useAuthStore from '../../stores/authStore'
import useDashboardStore from '../../stores/dashboardStore'
import { formatRelativeTime } from '../../utils/formatters'

const EVENT_COLORS = {
  jira_ticket_created: '#3B9EFF',
  fathom_call_processed: '#00E5C4',
  daily_health_check: '#7C5CFC',
  alert_fired: '#FF5C5C',
  new_alert: '#FFB547',
}

function useTypewriter(text, speed = 40) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    let i = 0
    const timer = setInterval(() => {
      i++
      setDisplayed(text.slice(0, i))
      if (i >= text.length) {
        clearInterval(timer)
        setDone(true)
      }
    }, speed)
    return () => clearInterval(timer)
  }, [text, speed])

  return { displayed, done }
}

function useClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])
  return now
}

function TickerPill({ event }) {
  const color = EVENT_COLORS[event.type] || '#5C5C72'
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1 mr-6 shrink-0 whitespace-nowrap">
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ background: color, boxShadow: `0 0 6px ${color}50` }}
      />
      <span className="text-xxs text-text-secondary truncate max-w-[200px]">
        {event.message}
      </span>
      <span className="text-xxs text-text-ghost font-mono">
        {formatRelativeTime(event.timestamp)}
      </span>
    </span>
  )
}

export default function CommandBar() {
  const user = useAuthStore((s) => s.user)
  const events = useDashboardStore((s) => s.events)
  const now = useClock()

  const firstName = useMemo(() => {
    if (!user) return 'Operator'
    if (user.first_name) return user.first_name
    if (user.full_name) return user.full_name.split(' ')[0]
    return 'Operator'
  }, [user])

  const greeting = `MISSION CONTROL // Welcome back, ${firstName}`
  const { displayed, done } = useTypewriter(greeting, 35)

  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })

  const tickerEvents = useMemo(() => {
    if (!events?.length) return []
    return events.slice(0, 8)
  }, [events])

  return (
    <div className="glass-far gradient-border-bottom px-4 py-3 flex items-center gap-4">
      {/* Greeting — typewriter */}
      <div className="shrink-0 min-w-0">
        <span className="font-mono text-xs text-text-secondary tracking-wide">
          {displayed}
          {!done && <span className="typewriter-cursor" />}
        </span>
      </div>

      {/* Ticker */}
      <div className="flex-1 overflow-hidden min-w-0 relative mx-4">
        {/* Left fade */}
        <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-[rgba(12,13,22,0.9)] to-transparent z-10 pointer-events-none" />
        {/* Right fade */}
        <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-[rgba(12,13,22,0.9)] to-transparent z-10 pointer-events-none" />

        {tickerEvents.length > 0 ? (
          <div className="ticker-track">
            {/* Duplicate for seamless loop */}
            {tickerEvents.map((e, i) => <TickerPill key={`a-${e.id || i}`} event={e} />)}
            {tickerEvents.map((e, i) => <TickerPill key={`b-${e.id || i}`} event={e} />)}
          </div>
        ) : (
          <div className="flex items-center gap-2 justify-center">
            <Radar className="w-3 h-3 text-text-ghost animate-pulse-subtle" />
            <span className="text-xxs text-text-ghost">Awaiting signals...</span>
          </div>
        )}
      </div>

      {/* Clock */}
      <div className="shrink-0 text-right">
        <div className="font-display text-sm font-semibold text-text-primary tabular-nums tracking-wider">
          {timeStr.split('').map((char, i) => (
            <span key={i} className={char === ':' ? 'animate-breathe-glow text-accent' : ''}>
              {char}
            </span>
          ))}
        </div>
        <div className="font-mono text-xxs text-text-ghost mt-0.5">{dateStr}</div>
      </div>
    </div>
  )
}
