import { useState } from 'react'
import { ChevronUp, ChevronDown, MoreVertical, Eye } from 'lucide-react'
import HealthScoreBadge from './HealthScoreBadge'
import { formatDate, getInitials } from '../../utils/formatters'

function formatAmount(amount) {
  if (amount == null) return '—'
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`
  return `$${amount.toFixed(0)}`
}

const ACTIVE_COLUMNS = [
  { key: 'name', label: 'Customer' },
  { key: 'health_score', label: 'Health Score', sortable: true },
  { key: 'csm_owner', label: 'CSM Owner' },
  { key: 'open_tickets', label: 'Open Tickets' },
  { key: 'last_meeting', label: 'Last Meeting' },
  { key: 'arr', label: 'ARR', sortable: true },
  { key: 'actions', label: 'Actions' },
]

const PROSPECT_COLUMNS = [
  { key: 'name', label: 'Company' },
  { key: 'deal_stage', label: 'Deal Stage' },
  { key: 'deal_amount', label: 'Deal Amount', sortable: true },
  { key: 'primary_contact_name', label: 'Contact' },
  { key: 'csm_owner', label: 'CSM Owner' },
  { key: 'industry', label: 'Industry' },
  { key: 'actions', label: 'Actions' },
]

export default function CustomerTable({ customers = [], onRowClick, variant = 'active' }) {
  const isProspect = variant === 'prospect'
  const columns = isProspect ? PROSPECT_COLUMNS : ACTIVE_COLUMNS

  const [sortCol, setSortCol] = useState(isProspect ? 'deal_amount' : 'health_score')
  const [sortDir, setSortDir] = useState(isProspect ? 'desc' : 'asc')
  const [hoveredRow, setHoveredRow] = useState(null)

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
    if (typeof aVal === 'string') return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal
  })

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return null
    return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  const renderCell = (c, col) => {
    switch (col.key) {
      case 'name':
        return (
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0"
              style={{
                background: isProspect ? 'rgba(139,92,246,0.1)' : 'var(--chip-bg, rgba(24,199,182,0.1))',
                color: isProspect ? '#8B5CF6' : 'var(--primary)',
              }}
            >
              {getInitials(c.name)}
            </div>
            <div className="min-w-0">
              <span className="font-medium block" style={{ color: 'var(--text-primary)' }}>{c.name}</span>
              {isProspect && c.deal_name && (
                <span className="text-xxs block truncate" style={{ color: 'var(--text-muted)' }}>{c.deal_name}</span>
              )}
            </div>
          </div>
        )
      case 'health_score':
        return <HealthScoreBadge score={c.health_score} />
      case 'deal_stage':
        return c.deal_stage ? (
          <span
            className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ background: 'rgba(139,92,246,0.1)', color: '#8B5CF6' }}
          >
            {c.deal_stage}
          </span>
        ) : <span style={{ color: 'var(--text-muted)' }}>—</span>
      case 'deal_amount':
        return <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{formatAmount(c.deal_amount)}</span>
      case 'primary_contact_name':
        return <span style={{ color: 'var(--text-secondary)' }}>{c.primary_contact_name || '—'}</span>
      case 'industry':
        return <span style={{ color: 'var(--text-secondary)' }}>{c.industry || '—'}</span>
      case 'csm_owner':
        return <span style={{ color: 'var(--text-secondary)' }}>{c.csm_owner}</span>
      case 'open_tickets':
        return <span style={{ color: 'var(--text-secondary)' }}>{c.open_tickets}</span>
      case 'last_meeting':
        return <span style={{ color: 'var(--text-secondary)' }}>{c.last_meeting ? formatDate(c.last_meeting) : '—'}</span>
      case 'arr':
        return <span className="font-mono" style={{ color: 'var(--text-primary)' }}>${(c.arr / 1000).toFixed(0)}K</span>
      case 'actions':
        return (
          <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
            <button className="p-1 rounded transition-colors duration-150 cursor-pointer" style={{ color: 'var(--text-muted)' }} onClick={() => onRowClick?.(c)}>
              <Eye size={14} />
            </button>
            <button className="p-1 rounded transition-colors duration-150 cursor-pointer" style={{ color: 'var(--text-muted)' }}>
              <MoreVertical size={14} />
            </button>
          </div>
        )
      default:
        return null
    }
  }

  if (customers.length === 0) {
    return (
      <div className="rounded-lg p-8 text-center" style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {isProspect
            ? 'No prospects found. Run a HubSpot sync to import prospect data.'
            : 'No customers found.'}
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg overflow-hidden" style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}>
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`text-left px-4 py-3 text-xs font-medium uppercase tracking-wider ${col.sortable ? 'cursor-pointer' : ''}`}
                style={{ color: 'var(--text-muted)' }}
                onClick={col.sortable ? () => toggleSort(col.key) : undefined}
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && <SortIcon col={col.key} />}
                </span>
              </th>
            ))}
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
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3">{renderCell(c, col)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
