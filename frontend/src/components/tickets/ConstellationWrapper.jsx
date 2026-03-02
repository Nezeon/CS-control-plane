import { useMemo, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { getSeverityColor, getInitials } from '../../utils/formatters'

const statusColorMap = {
  open: '#71717A',
  in_progress: '#6366F1',
  waiting: '#EAB308',
  resolved: '#22C55E',
  closed: '#52525B',
}

const severityX = { P1: 0.9, P2: 0.7, P3: 0.4, P4: 0.15, critical: 0.9, high: 0.7, medium: 0.4, low: 0.15 }
const severityR = { P1: 14, P2: 11, P3: 8, P4: 6, critical: 14, high: 11, medium: 8, low: 6 }

function getAgeDays(dateStr) {
  if (!dateStr) return 0
  return Math.max(0, Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000))
}

/* ─── Tooltip ─── */
function TicketTooltip({ ticket, x, y }) {
  if (!ticket) return null
  return (
    <motion.foreignObject
      x={x + 16} y={y - 30}
      width={200} height={80}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{ pointerEvents: 'none' }}
    >
      <div className="bg-bg-elevated rounded-lg p-2.5 border border-border text-xs">
        <div className="text-text-primary font-semibold truncate">{ticket.jira_key || ticket.id}</div>
        <div className="text-text-ghost font-mono mt-0.5 truncate">{ticket.summary || ticket.title}</div>
        <div className="text-text-ghost font-mono mt-0.5">{ticket.customer_name} · {ticket.severity}</div>
      </div>
    </motion.foreignObject>
  )
}

export default function ConstellationWrapper({ tickets = [], onTicketClick }) {
  const [hovered, setHovered] = useState(null)

  const viewW = 900
  const viewH = 500
  const padX = 60
  const padY = 40

  // Position tickets: X = severity, Y = age
  const nodes = useMemo(() => {
    const maxAge = Math.max(1, ...tickets.map((t) => getAgeDays(t.created_at)))
    return tickets.map((t) => {
      const sx = severityX[t.severity] ?? 0.5
      const age = getAgeDays(t.created_at)
      const x = padX + sx * (viewW - padX * 2) + (Math.random() - 0.5) * 20
      const y = padY + (age / maxAge) * (viewH - padY * 2)
      const r = severityR[t.severity] || 8
      const color = statusColorMap[t.status] || '#71717A'
      const isBreaching = t.sla_deadline && new Date(t.sla_deadline) < new Date()
      return { ticket: t, x, y, r, color, isBreaching }
    })
  }, [tickets])

  // Connect same-customer tickets
  const customerLines = useMemo(() => {
    const grouped = {}
    nodes.forEach((n) => {
      const cid = n.ticket.customer_id || n.ticket.customer_name
      if (cid) {
        if (!grouped[cid]) grouped[cid] = []
        grouped[cid].push(n)
      }
    })
    const lines = []
    Object.values(grouped).forEach((group) => {
      for (let i = 1; i < group.length; i++) {
        lines.push({ x1: group[i - 1].x, y1: group[i - 1].y, x2: group[i].x, y2: group[i].y })
      }
    })
    return lines
  }, [nodes])

  const handleClick = useCallback((ticket) => {
    onTicketClick?.(ticket.id)
  }, [onTicketClick])

  return (
    <div className="card overflow-hidden" data-testid="ticket-constellation" aria-label="Ticket constellation">
      <svg viewBox={`0 0 ${viewW} ${viewH}`} className="w-full" preserveAspectRatio="xMidYMid meet">
        {/* Grid */}
        <defs>
          <pattern id="constGrid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(63,63,70,0.12)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width={viewW} height={viewH} fill="url(#constGrid)" />

        {/* Axis labels */}
        <text x={padX} y={viewH - 8} style={{ fontFamily: '"JetBrains Mono"', fill: '#52525B', fontSize: 10 }}>Low severity →</text>
        <text x={viewW - padX} y={viewH - 8} textAnchor="end" style={{ fontFamily: '"JetBrains Mono"', fill: '#52525B', fontSize: 10 }}>→ High severity</text>
        <text x={12} y={padY + 4} style={{ fontFamily: '"JetBrains Mono"', fill: '#52525B', fontSize: 10 }} transform={`rotate(-90, 12, ${viewH / 2})`}>Age (days)</text>

        {/* Customer connection lines */}
        {customerLines.map((l, i) => (
          <line key={`line-${i}`} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke="rgba(63,63,70,0.15)" strokeWidth={1} strokeDasharray="2 4" />
        ))}

        {/* Ticket nodes */}
        {nodes.map(({ ticket, x, y, r, color, isBreaching }, i) => (
          <g
            key={ticket.id || i}
            style={{ cursor: 'pointer' }}
            onMouseEnter={() => setHovered({ ticket, x, y })}
            onMouseLeave={() => setHovered(null)}
            onClick={() => handleClick(ticket)}
          >
            {/* Breaching pulse ring */}
            {isBreaching && (
              <circle cx={x} cy={y} r={r + 4} fill="none" stroke="#EF4444" strokeWidth={1.5} opacity={0.5}
                style={{ animation: 'pulseConst 1.5s ease-in-out infinite' }} />
            )}
            <circle cx={x} cy={y} r={r} fill={`${color}30`} stroke={color} strokeWidth={1.5}
              style={{ transition: 'all 0.2s' }} />
          </g>
        ))}

        {/* Tooltip */}
        {hovered && <TicketTooltip ticket={hovered.ticket} x={hovered.x} y={hovered.y} />}

        <style>{`
          @keyframes pulseConst { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.7; } }
        `}</style>
      </svg>
    </div>
  )
}
