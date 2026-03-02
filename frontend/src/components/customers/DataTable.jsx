import { useState } from 'react'
import { ArrowUpDown } from 'lucide-react'
import HealthRing from '../shared/HealthRing'
import StatusIndicator from '../shared/StatusIndicator'

function daysUntil(dateStr) {
  if (!dateStr) return null
  return Math.ceil((new Date(dateStr) - Date.now()) / 86400000)
}

function getInitials(name) {
  if (!name) return '?'
  return name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase()
}

const COLUMNS = [
  { key: 'company_name', label: 'Name', sortable: true },
  { key: 'health_score', label: 'Health', sortable: true },
  { key: 'risk_level', label: 'Risk', sortable: true },
  { key: 'tier', label: 'Tier', sortable: false },
  { key: 'open_tickets', label: 'Tickets', sortable: true },
  { key: 'cs_owner', label: 'CS Owner', sortable: false },
  { key: 'contract_end', label: 'Renewal', sortable: true },
]

export default function DataTable({ customers = [], onCustomerClick, onSort, onHover }) {
  const [sortField, setSortField] = useState('health_score')
  const [sortDir, setSortDir] = useState('asc')

  const handleSort = (key) => {
    if (!COLUMNS.find((c) => c.key === key)?.sortable) return
    const newDir = sortField === key && sortDir === 'asc' ? 'desc' : 'asc'
    setSortField(key)
    setSortDir(newDir)
    onSort?.(key, newDir)
  }

  if (!customers.length) {
    return <p className="text-sm text-text-ghost py-12 text-center">No customers match your filters</p>
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-border">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-2.5 text-xxs font-medium text-text-ghost uppercase tracking-wider ${col.sortable ? 'cursor-pointer hover:text-text-muted select-none' : ''}`}
                  onClick={() => handleSort(col.key)}
                >
                  <span className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortField === col.key && (
                      <ArrowUpDown className="w-3 h-3 text-accent" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => {
              const days = daysUntil(c.contract_end || c.renewal_date)

              return (
                <tr
                  key={c.id}
                  onClick={() => onCustomerClick?.(c)}
                  onMouseEnter={() => onHover?.(c)}
                  onMouseLeave={() => onHover?.(null)}
                  className="border-b border-border-subtle hover:bg-bg-active/40 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-md bg-accent/10 flex items-center justify-center text-xxs font-medium text-accent">
                        {getInitials(c.company_name || c.name)}
                      </div>
                      <span className="text-sm font-medium text-text-primary">{c.company_name || c.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <HealthRing score={c.health_score} size="sm" showLabel={false} />
                      <span className="text-sm font-mono tabular-nums text-text-primary">{c.health_score ?? '—'}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusIndicator status={c.risk_level === 'healthy' ? 'active' : c.risk_level === 'watch' ? 'warning' : 'error'} size="sm" showLabel />
                  </td>
                  <td className="px-4 py-3 text-xs text-text-muted capitalize">{(c.tier || '').replace('_', '-')}</td>
                  <td className="px-4 py-3 text-sm font-mono tabular-nums text-text-muted">{c.open_tickets ?? 0}</td>
                  <td className="px-4 py-3 text-xs text-text-muted">{c.cs_owner || '—'}</td>
                  <td className="px-4 py-3">
                    {days != null ? (
                      <span className={`text-xs font-mono tabular-nums ${days < 30 ? 'text-status-danger' : days < 90 ? 'text-status-warning' : 'text-text-muted'}`}>
                        {days}d
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
