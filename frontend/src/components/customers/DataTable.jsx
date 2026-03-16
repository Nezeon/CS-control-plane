import { useState, useCallback } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import GlassCard from '../shared/GlassCard'
import HealthRing from '../shared/HealthRing'
import StatusPill from '../shared/StatusPill'
import { getInitials } from '../../utils/formatters'

const EMPTY_ARRAY = []

function daysUntil(dateStr) {
  if (!dateStr) return null
  return Math.ceil((new Date(dateStr) - Date.now()) / 86400000)
}

function riskToStatus(risk) {
  switch (risk) {
    case 'high_risk': return 'critical'
    case 'watch': return 'acknowledged'
    default: return 'active'
  }
}

function tierLabel(tier) {
  if (!tier) return ''
  if (tier === 'enterprise') return 'Enterprise'
  if (tier === 'mid_market' || tier === 'mid-market') return 'Mid-Market'
  return 'SMB'
}

function tierBadgeClass(tier) {
  if (tier === 'enterprise') return 'bg-accent/10 text-accent border-accent/20'
  if (tier === 'mid_market' || tier === 'mid-market') return 'bg-teal/10 text-teal border-teal/20'
  return 'bg-bg-active text-text-muted border-border-subtle'
}

function formatRenewalDate(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const COLUMNS = [
  { key: 'company_name', label: 'Company', sortable: true },
  { key: 'health_score', label: 'Health', sortable: true },
  { key: 'risk_level', label: 'Risk', sortable: true },
  { key: 'tier', label: 'Tier', sortable: false },
  { key: 'contract_end', label: 'Renewal', sortable: true },
  { key: 'cs_owner', label: 'CS Owner', sortable: false },
]

export default function DataTable({ customers = EMPTY_ARRAY, onCustomerClick, onHover }) {
  const [sortField, setSortField] = useState('health_score')
  const [sortDir, setSortDir] = useState('asc')

  const handleSort = useCallback((key) => {
    if (!COLUMNS.find((c) => c.key === key)?.sortable) return
    const newDir = sortField === key && sortDir === 'asc' ? 'desc' : 'asc'
    setSortField(key)
    setSortDir(newDir)
  }, [sortField, sortDir])

  // Local sorting
  const sorted = [...customers].sort((a, b) => {
    let aVal = a[sortField]
    let bVal = b[sortField]
    // Handle nested cs_owner
    if (sortField === 'cs_owner') {
      aVal = typeof aVal === 'object' ? aVal?.full_name : aVal
      bVal = typeof bVal === 'object' ? bVal?.full_name : bVal
    }
    if (aVal == null) return 1
    if (bVal == null) return -1
    if (typeof aVal === 'string') {
      const cmp = aVal.localeCompare(bVal)
      return sortDir === 'asc' ? cmp : -cmp
    }
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal
  })

  if (!customers.length) {
    return <p className="text-sm text-text-ghost py-12 text-center">No customers match your filters</p>
  }

  return (
    <GlassCard className="!p-0 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-bg-subtle">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-xxs font-medium text-text-ghost uppercase tracking-wider whitespace-nowrap ${
                    col.sortable ? 'cursor-pointer select-none hover:text-text-muted transition-colors' : ''
                  }`}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortField === col.key && (
                      sortDir === 'asc'
                        ? <ChevronUp className="w-3 h-3 text-accent" />
                        : <ChevronDown className="w-3 h-3 text-accent" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((c) => {
              const days = daysUntil(c.contract_end || c.renewal_date)
              const dateFormatted = formatRenewalDate(c.contract_end || c.renewal_date)

              return (
                <tr
                  key={c.id}
                  onClick={() => onCustomerClick?.(c)}
                  onMouseEnter={() => onHover?.(c)}
                  onMouseLeave={() => onHover?.(null)}
                  className="border-b border-border-subtle hover:bg-bg-hover cursor-pointer transition-colors"
                >
                  {/* Company */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-md bg-accent/10 flex items-center justify-center text-xxs font-medium text-accent flex-shrink-0">
                        {getInitials(c.company_name || c.name)}
                      </div>
                      <span className="text-sm font-medium text-text-primary">{c.company_name || c.name}</span>
                    </div>
                  </td>

                  {/* Health */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <HealthRing score={c.health_score ?? 0} size={28} strokeWidth={2.5} />
                      <span className="text-sm font-mono tabular-nums text-text-primary">{c.health_score ?? '--'}</span>
                    </div>
                  </td>

                  {/* Risk */}
                  <td className="px-4 py-3">
                    <StatusPill status={riskToStatus(c.risk_level)} size="sm" />
                  </td>

                  {/* Tier */}
                  <td className="px-4 py-3">
                    <span className={`text-xxs font-medium px-2 py-0.5 rounded-full border ${tierBadgeClass(c.tier)}`}>
                      {tierLabel(c.tier)}
                    </span>
                  </td>

                  {/* Renewal */}
                  <td className="px-4 py-3">
                    {days != null ? (
                      <div className="flex flex-col">
                        <span className={`text-xs font-mono tabular-nums ${
                          days < 30 ? 'text-status-danger' : days < 90 ? 'text-status-warning' : 'text-text-muted'
                        }`}>
                          {days}d
                        </span>
                        {dateFormatted && (
                          <span className="text-xxs text-text-ghost">{dateFormatted}</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-text-ghost">--</span>
                    )}
                  </td>

                  {/* CS Owner */}
                  <td className="px-4 py-3 text-xs text-text-muted">
                    {c.cs_owner
                      ? (typeof c.cs_owner === 'object' ? c.cs_owner.full_name : c.cs_owner)
                      : '--'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </GlassCard>
  )
}
