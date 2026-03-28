import { useState, useCallback } from 'react'
import { ChevronUp, ChevronDown, MoreVertical, Eye } from 'lucide-react'
import HealthScoreBadge from './HealthScoreBadge'
import { formatDate, getInitials } from '../../utils/formatters'

export default function CustomerTable({ customers = [], onRowClick }) {
  const [sortCol, setSortCol] = useState('health_score')
  const [sortDir, setSortDir] = useState('asc')

  const toggleSort = (col) => {
    if (sortCol === col) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('desc')
    }
  }

  const sorted = [...customers].sort((a, b) => {
    const aVal = a[sortCol] ?? 0
    const bVal = b[sortCol] ?? 0
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal
  })

  const [hoveredRow, setHoveredRow] = useState(null)

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return null
    return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  return (
    <div className="rounded-lg overflow-hidden" style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Customer
            </th>
            <th
              className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider cursor-pointer"
              style={{ color: 'var(--text-muted)' }}
              onClick={() => toggleSort('health_score')}
            >
              <span className="flex items-center gap-1">Health Score <SortIcon col="health_score" /></span>
            </th>
            <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              CSM Owner
            </th>
            <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Open Tickets
            </th>
            <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Last Meeting
            </th>
            <th
              className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider cursor-pointer"
              style={{ color: 'var(--text-muted)' }}
              onClick={() => toggleSort('arr')}
            >
              <span className="flex items-center gap-1">ARR <SortIcon col="arr" /></span>
            </th>
            <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((c) => (
            <tr
              key={c.id}
              className="cursor-pointer transition-colors duration-100"
              style={{
                borderBottom: '1px solid var(--border)',
                background: hoveredRow === c.id ? 'var(--bg-hover)' : 'transparent',
              }}
              onClick={() => onRowClick?.(c)}
              onMouseEnter={() => setHoveredRow(c.id)}
              onMouseLeave={() => setHoveredRow(null)}
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0"
                    style={{ background: 'var(--chip-bg, rgba(24,199,182,0.1))', color: 'var(--primary)' }}
                  >
                    {getInitials(c.name)}
                  </div>
                  <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{c.name}</span>
                </div>
              </td>
              <td className="px-4 py-3">
                <HealthScoreBadge score={c.health_score} />
              </td>
              <td className="px-4 py-3" style={{ color: 'var(--text-secondary)' }}>{c.csm_owner}</td>
              <td className="px-4 py-3" style={{ color: 'var(--text-secondary)' }}>{c.open_tickets}</td>
              <td className="px-4 py-3" style={{ color: 'var(--text-secondary)' }}>{c.last_meeting ? formatDate(c.last_meeting) : '—'}</td>
              <td className="px-4 py-3 font-mono" style={{ color: 'var(--text-primary)' }}>
                ${(c.arr / 1000).toFixed(0)}K
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
                  <button
                    className="p-1 rounded transition-colors duration-150 cursor-pointer"
                    style={{ color: 'var(--text-muted)' }}
                    onClick={() => onRowClick?.(c)}
                  >
                    <Eye size={14} />
                  </button>
                  <button
                    className="p-1 rounded transition-colors duration-150 cursor-pointer"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    <MoreVertical size={14} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
