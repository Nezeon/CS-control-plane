import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowUpDown, Bot } from 'lucide-react'
import SeverityMarker from '../shared/SeverityMarker'
import { getSeverityColor, formatRelativeTime, getInitials } from '../../utils/formatters'

/* ─── SLA countdown hook ─── */
function useSlaCountdown(slaDeadline) {
  const [remaining, setRemaining] = useState('—')
  const [urgency, setUrgency] = useState('normal')

  useEffect(() => {
    if (!slaDeadline) return

    function update() {
      const diff = new Date(slaDeadline).getTime() - Date.now()
      if (diff <= 0) {
        setRemaining('BREACHED')
        setUrgency('breached')
        return
      }
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      if (h > 4) { setRemaining(`${h}h ${m}m`); setUrgency('normal') }
      else if (h > 1) { setRemaining(`${h}h ${m}m`); setUrgency('warning') }
      else { setRemaining(`${m}m ${s}s`); setUrgency('critical') }
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [slaDeadline])

  return { remaining, urgency }
}

function SlaCell({ deadline }) {
  const { remaining, urgency } = useSlaCountdown(deadline)
  const colorMap = { normal: '#71717A', warning: '#EAB308', critical: '#EF4444', breached: '#EF4444' }

  return (
    <span
      className={`font-mono text-xs tabular-nums font-semibold ${urgency === 'breached' ? 'animate-pulse' : ''}`}
      style={{ color: colorMap[urgency] }}
    >
      {remaining}
    </span>
  )
}

function SortHeader({ label, field, currentSort, currentOrder, onSort }) {
  const isActive = currentSort === field
  return (
    <th
      className="px-3 py-2.5 text-left cursor-pointer hover:text-text-primary transition-colors select-none"
      onClick={() => onSort(field)}
    >
      <span className="flex items-center gap-1">
        {label}
        <ArrowUpDown className={`w-3 h-3 ${isActive ? 'text-accent' : 'text-text-ghost/30'}`} />
      </span>
    </th>
  )
}

function StatusText({ status }) {
  const color = status === 'resolved' || status === 'closed' ? '#22C55E'
    : status === 'in_progress' ? '#6366F1'
    : status === 'waiting' ? '#EAB308'
    : '#71717A'

  return (
    <span className="flex items-center gap-1.5">
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="font-mono text-[10px] uppercase" style={{ color }}>{status?.replace('_', ' ') || '—'}</span>
    </span>
  )
}

export default function WarroomTable({ tickets = [], sortBy, sortOrder, onSort, onTicketClick }) {
  return (
    <div className="card overflow-hidden" data-testid="warroom-table">
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-border text-text-ghost uppercase tracking-wider text-[10px]">
              <th className="w-1 px-0" />
              <SortHeader label="ID" field="jira_key" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <SortHeader label="Customer" field="customer" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <th className="px-3 py-2.5 text-left">Summary</th>
              <SortHeader label="Severity" field="severity" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <SortHeader label="Status" field="status" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <th className="px-3 py-2.5 text-left">Assignee</th>
              <SortHeader label="SLA" field="sla_deadline" currentSort={sortBy} currentOrder={sortOrder} onSort={onSort} />
              <th className="px-3 py-2.5 text-left w-8">AI</th>
            </tr>
          </thead>
          <tbody>
            {tickets.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-12 text-text-ghost">No tickets found</td>
              </tr>
            ) : (
              tickets.map((ticket, i) => {
                const isTriaged = ticket.has_triage_result || ticket._justTriaged
                return (
                  <motion.tr
                    key={ticket.id || i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.015 }}
                    className="border-b border-border-subtle cursor-pointer transition-colors hover:bg-bg-active/50"
                    onClick={() => onTicketClick?.(ticket.id)}
                  >
                    <td className="relative w-1 px-0"><SeverityMarker severity={ticket.severity} /></td>

                    <td className="px-3 py-2.5">
                      <span className="text-accent font-semibold">{ticket.jira_key || ticket.id}</span>
                    </td>

                    <td className="px-3 py-2.5 text-text-secondary max-w-[120px] truncate">
                      {ticket.customer_name || '—'}
                    </td>

                    <td className="px-3 py-2.5 text-text-primary max-w-[220px] truncate">
                      {ticket.summary || ticket.title || '—'}
                    </td>

                    <td className="px-3 py-2.5">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: getSeverityColor(ticket.severity) }} />
                        <span style={{ color: getSeverityColor(ticket.severity) }}>{ticket.severity || '—'}</span>
                      </span>
                    </td>

                    <td className="px-3 py-2.5"><StatusText status={ticket.status} /></td>

                    <td className="px-3 py-2.5">
                      {ticket.assignee ? (
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded-full bg-bg-active flex items-center justify-center text-[9px] text-text-ghost font-semibold">
                            {getInitials(ticket.assignee)}
                          </div>
                          <span className="text-text-ghost truncate max-w-[60px]">{ticket.assignee}</span>
                        </div>
                      ) : (
                        <span className="text-text-ghost/40">—</span>
                      )}
                    </td>

                    <td className="px-3 py-2.5"><SlaCell deadline={ticket.sla_deadline} /></td>

                    <td className="px-3 py-2.5">
                      {isTriaged && (
                        <Bot className="w-3.5 h-3.5 text-accent" />
                      )}
                    </td>
                  </motion.tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
