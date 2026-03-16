import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Users, Heart, Ticket, AlertTriangle, ChevronUp, ChevronDown, Filter } from 'lucide-react'
import useDashboardStore from '../stores/dashboardStore'
import KpiCard from '../components/shared/KpiCard'
import GlassCard from '../components/shared/GlassCard'
import HealthRing from '../components/shared/HealthRing'
import StatusPill from '../components/shared/StatusPill'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatRelativeTime } from '../utils/formatters'

const RISK_FILTERS = ['all', 'critical', 'high_risk', 'medium_risk', 'healthy']

function healthColor(score) {
  if (score == null) return 'text-[var(--text-muted)]'
  if (score >= 70) return 'text-[var(--status-success)]'
  if (score >= 50) return 'text-[var(--status-warning)]'
  return 'text-[var(--status-danger)]'
}

function daysToRenewal(d) {
  if (!d) return null
  return Math.ceil((new Date(d) - new Date()) / 86400000)
}

export default function DashboardPage() {
  const { stats, quickHealth, events, isLoading, fetchAll } = useDashboardStore()
  const [searchParams] = useSearchParams()
  const [riskFilter, setRiskFilter] = useState(searchParams.get('filter') || 'all')
  const [sortCol, setSortCol] = useState('health_score')
  const [sortDir, setSortDir] = useState('asc')

  useEffect(() => { fetchAll() }, [fetchAll])

  if (isLoading && !stats) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-display font-bold text-[var(--text-primary)]">At-Risk Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <LoadingSkeleton key={i} />)}
        </div>
      </div>
    )
  }

  let filtered = [...(quickHealth || [])]
  if (riskFilter !== 'all') filtered = filtered.filter((c) => c.risk_level === riskFilter)

  filtered.sort((a, b) => {
    let va, vb
    if (sortCol === 'name') {
      va = (a.name || '').toLowerCase(); vb = (b.name || '').toLowerCase()
      return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va)
    }
    if (sortCol === 'renewal') {
      va = a.renewal_date ? new Date(a.renewal_date).getTime() : Infinity
      vb = b.renewal_date ? new Date(b.renewal_date).getTime() : Infinity
    } else { va = a[sortCol] ?? -1; vb = b[sortCol] ?? -1 }
    return sortDir === 'asc' ? va - vb : vb - va
  })

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('asc') }
  }

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return null
    return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-display font-bold text-[var(--text-primary)]">At-Risk Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total Customers" value={stats?.total_customers ?? '—'} trend={stats?.trends?.customers_change} icon={Users} color="accent" />
        <KpiCard label="At-Risk Count" value={stats?.at_risk_count ?? '—'} trend={stats?.trends?.risk_change} icon={AlertTriangle} color="accent" />
        <KpiCard label="Open P0/P1 Tickets" value={stats?.open_tickets ?? '—'} trend={stats?.trends?.tickets_change} icon={Ticket} color="sky" />
        <KpiCard label="Avg Health Score" value={stats?.avg_health_score ?? '—'} trend={stats?.trends?.health_change} icon={Heart} color="teal" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Customer Table */}
        <GlassCard level="near" className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">At-Risk Customers</h2>
            <div className="flex items-center gap-1.5">
              <Filter size={12} className="text-[var(--text-muted)]" />
              {RISK_FILTERS.map((f) => (
                <button
                  key={f}
                  onClick={() => setRiskFilter(f)}
                  className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                    riskFilter === f
                      ? 'bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/30'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] border border-transparent'
                  }`}
                >
                  {f === 'all' ? 'All' : f.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <p className="text-sm text-[var(--text-muted)] py-8 text-center">No customers match filter</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[var(--text-muted)] font-mono text-[10px] uppercase tracking-wider border-b border-[var(--border)]">
                    {[['name','Customer'],['health_score','Health'],['','Sentiment'],['open_ticket_count','Tickets'],['renewal','Renewal'],['','Risk'],['','Flags']].map(([col, label]) => (
                      <th key={label} className={`pb-2 pr-3 ${col ? 'cursor-pointer select-none' : ''}`} onClick={col ? () => toggleSort(col) : undefined}>
                        <span className="flex items-center gap-1">{label} {col && <SortIcon col={col} />}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c) => {
                    const days = daysToRenewal(c.renewal_date)
                    return (
                      <tr key={c.id} className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-hover)]/50 transition-colors">
                        <td className="py-2.5 pr-3">
                          <Link to={`/customers/${c.id}`} className="text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors font-medium">{c.name}</Link>
                        </td>
                        <td className="py-2.5 pr-3">
                          <div className="flex items-center gap-2">
                            <HealthRing score={c.health_score} size={22} strokeWidth={3} />
                            <span className={`font-mono text-xs ${healthColor(c.health_score)}`}>{c.health_score ?? '—'}</span>
                          </div>
                        </td>
                        <td className="py-2.5 pr-3 text-xs text-[var(--text-secondary)]">{c.sentiment_bucket || '—'}</td>
                        <td className="py-2.5 pr-3 font-mono text-xs text-[var(--text-secondary)]">{c.open_ticket_count || 0}</td>
                        <td className="py-2.5 pr-3">
                          {days != null
                            ? <span className={`font-mono text-xs ${days <= 90 ? 'text-[var(--status-warning)]' : 'text-[var(--text-muted)]'}`}>{days}d</span>
                            : <span className="text-[var(--text-ghost)]">—</span>}
                        </td>
                        <td className="py-2.5 pr-3"><StatusPill status={c.risk_level || 'healthy'} /></td>
                        <td className="py-2.5 font-mono text-xs text-[var(--text-muted)]">{c.risk_count || 0}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>

        {/* Sidebar: Events */}
        <GlassCard level="mid">
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Recent Events</h2>
          {(events || []).length === 0 ? (
            <p className="text-xs text-[var(--text-muted)]">No recent events</p>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {events.slice(0, 15).map((evt) => (
                <div key={evt.id} className="flex items-start gap-2 pb-2 border-b border-[var(--border-subtle)] last:border-0">
                  <div className="w-1 h-1 rounded-full bg-[var(--accent)] mt-1.5 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] text-[var(--text-secondary)] truncate">{evt.description || evt.event_type}</p>
                    <span className="text-[10px] text-[var(--text-ghost)] font-mono">{formatRelativeTime(evt.created_at || evt.timestamp)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
