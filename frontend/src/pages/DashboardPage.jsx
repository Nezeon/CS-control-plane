import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Users, Heart, Ticket, AlertTriangle, ArrowRight, Filter, ChevronUp, ChevronDown } from 'lucide-react'
import useDashboardStore from '../stores/dashboardStore'
import useAlertStore from '../stores/alertStore'
import KpiCard from '../components/shared/KpiCard'
import GlassCard from '../components/shared/GlassCard'
import HealthRing from '../components/shared/HealthRing'
import StatusPill from '../components/shared/StatusPill'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatRelativeTime } from '../utils/formatters'

const RISK_FILTERS = ['all', 'critical', 'high_risk', 'medium_risk', 'healthy']

function healthColor(score) {
  if (score == null) return 'text-text-muted'
  if (score >= 70) return 'text-status-success'
  if (score >= 50) return 'text-status-warning'
  return 'text-status-danger'
}

function daysToRenewal(renewalDate) {
  if (!renewalDate) return null
  const diff = Math.ceil((new Date(renewalDate) - new Date()) / (1000 * 60 * 60 * 24))
  return diff
}

export default function DashboardPage() {
  const { stats, quickHealth, events, isLoading, fetchAll } = useDashboardStore()
  const { alerts, fetchAll: fetchAlerts } = useAlertStore()
  const [searchParams] = useSearchParams()

  // Filters
  const initialFilter = searchParams.get('filter') || 'all'
  const [riskFilter, setRiskFilter] = useState(initialFilter)
  const [sortCol, setSortCol] = useState('health_score')
  const [sortDir, setSortDir] = useState('asc')

  useEffect(() => {
    fetchAll()
    fetchAlerts()
  }, [fetchAll, fetchAlerts])

  if (isLoading && !stats) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-display font-bold text-text-primary">At-Risk Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <LoadingSkeleton key={i} variant="card" />
          ))}
        </div>
      </div>
    )
  }

  const openAlerts = alerts.filter((a) => a.status === 'open' || a.status === 'active')

  // Filter customers
  let filtered = [...(quickHealth || [])]
  if (riskFilter !== 'all') {
    filtered = filtered.filter((c) => c.risk_level === riskFilter)
  }

  // Sort
  filtered.sort((a, b) => {
    let valA, valB
    if (sortCol === 'name') {
      valA = (a.name || '').toLowerCase()
      valB = (b.name || '').toLowerCase()
      return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
    }
    if (sortCol === 'renewal') {
      valA = a.renewal_date ? new Date(a.renewal_date).getTime() : Infinity
      valB = b.renewal_date ? new Date(b.renewal_date).getTime() : Infinity
    } else {
      valA = a[sortCol] ?? -1
      valB = b[sortCol] ?? -1
    }
    return sortDir === 'asc' ? valA - valB : valB - valA
  })

  const toggleSort = (col) => {
    if (sortCol === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return null
    return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-display font-bold text-text-primary">At-Risk Dashboard</h1>

      {/* KPI Row — 4 cards per ARCHITECTURE.md Section 7.1 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Customers"
          value={stats?.total_customers ?? '—'}
          trend={stats?.trends?.customers_change}
          icon={Users}
          color="accent"
        />
        <KpiCard
          label="At-Risk Count"
          value={stats?.at_risk_count ?? '—'}
          trend={stats?.trends?.risk_change}
          icon={AlertTriangle}
          color="accent"
        />
        <KpiCard
          label="Open P0/P1 Tickets"
          value={stats?.open_tickets ?? '—'}
          trend={stats?.trends?.tickets_change}
          icon={Ticket}
          color="sky"
        />
        <KpiCard
          label="Avg Health Score"
          value={stats?.avg_health_score ?? '—'}
          trend={stats?.trends?.health_change}
          icon={Heart}
          color="teal"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* At-Risk Customer Table (3/4 width) */}
        <GlassCard level="near" className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary">At-Risk Customers</h2>
            <div className="flex items-center gap-2">
              <Filter size={12} className="text-text-muted" />
              {RISK_FILTERS.map((f) => (
                <button
                  key={f}
                  onClick={() => setRiskFilter(f)}
                  className={`text-xxs px-2 py-0.5 rounded-full transition-colors ${
                    riskFilter === f
                      ? 'bg-accent/20 text-accent border border-accent/40'
                      : 'bg-bg-hover text-text-muted hover:text-text-secondary border border-transparent'
                  }`}
                >
                  {f === 'all' ? 'All' : f.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
          {filtered.length === 0 ? (
            <p className="text-sm text-text-muted">No customers match the current filter</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-text-muted font-mono text-xxs uppercase tracking-wider border-b border-border-subtle">
                    <th className="pb-2 pr-3 cursor-pointer select-none" onClick={() => toggleSort('name')}>
                      <span className="flex items-center gap-1">Customer <SortIcon col="name" /></span>
                    </th>
                    <th className="pb-2 pr-3 cursor-pointer select-none" onClick={() => toggleSort('health_score')}>
                      <span className="flex items-center gap-1">Health <SortIcon col="health_score" /></span>
                    </th>
                    <th className="pb-2 pr-3">Sentiment</th>
                    <th className="pb-2 pr-3 cursor-pointer select-none" onClick={() => toggleSort('open_ticket_count')}>
                      <span className="flex items-center gap-1">Tickets <SortIcon col="open_ticket_count" /></span>
                    </th>
                    <th className="pb-2 pr-3 cursor-pointer select-none" onClick={() => toggleSort('renewal')}>
                      <span className="flex items-center gap-1">Renewal <SortIcon col="renewal" /></span>
                    </th>
                    <th className="pb-2 pr-3">Risk</th>
                    <th className="pb-2">Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c) => {
                    const days = daysToRenewal(c.renewal_date)
                    return (
                      <tr key={c.id} className="border-b border-border-subtle/50 hover:bg-bg-hover/50 transition-colors">
                        <td className="py-2.5 pr-3">
                          <Link to={`/customers/${c.id}`} className="text-text-primary hover:text-accent transition-colors font-medium">
                            {c.name}
                          </Link>
                        </td>
                        <td className="py-2.5 pr-3">
                          <div className="flex items-center gap-2">
                            <HealthRing score={c.health_score} size={24} strokeWidth={3} />
                            <span className={`font-mono text-xs ${healthColor(c.health_score)}`}>
                              {c.health_score ?? '—'}
                            </span>
                          </div>
                        </td>
                        <td className="py-2.5 pr-3">
                          <span className="text-xs text-text-secondary">
                            {c.sentiment_bucket || '—'}
                          </span>
                        </td>
                        <td className="py-2.5 pr-3">
                          <span className="font-mono text-xs text-text-secondary">{c.open_ticket_count || 0}</span>
                        </td>
                        <td className="py-2.5 pr-3">
                          {days != null ? (
                            <span className={`font-mono text-xs ${days <= 90 ? 'text-status-warning' : 'text-text-muted'}`}>
                              {days}d
                            </span>
                          ) : (
                            <span className="text-xxs text-text-ghost">—</span>
                          )}
                        </td>
                        <td className="py-2.5 pr-3">
                          <StatusPill status={c.risk_level || 'healthy'} />
                        </td>
                        <td className="py-2.5">
                          <span className="font-mono text-xs text-text-muted">{c.risk_count || 0}</span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>

        {/* Right Sidebar: Alert Feed */}
        <div className="space-y-4">
          <GlassCard level="mid">
            <h2 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
              <AlertTriangle size={14} className="text-status-warning" />
              Live Alerts ({openAlerts.length})
            </h2>
            {openAlerts.length === 0 ? (
              <p className="text-xs text-text-muted">No active alerts</p>
            ) : (
              <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
                {openAlerts.slice(0, 10).map((alert) => (
                  <div key={alert.id} className="flex items-start gap-2 pb-2 border-b border-border-subtle/50 last:border-0">
                    <StatusPill status={alert.severity || 'medium'} size="sm" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs text-text-secondary truncate">{alert.title}</p>
                      <span className="text-xxs text-text-ghost font-mono">
                        {formatRelativeTime(alert.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Link to="/alerts" className="text-xs text-accent hover:text-accent/80 flex items-center gap-1 mt-3">
              View all alerts <ArrowRight size={12} />
            </Link>
          </GlassCard>

          {/* Recent Events */}
          <GlassCard level="far">
            <h2 className="text-xs font-semibold text-text-muted mb-3">Recent Events</h2>
            {events.length === 0 ? (
              <p className="text-xs text-text-muted">No recent events</p>
            ) : (
              <div className="space-y-2 max-h-[250px] overflow-y-auto pr-1">
                {events.slice(0, 8).map((evt) => (
                  <div key={evt.id} className="flex items-start gap-2 pb-2 border-b border-border-subtle/50 last:border-0">
                    <div className="w-1 h-1 rounded-full bg-accent mt-1.5 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xxs text-text-secondary truncate">{evt.description || evt.event_type}</p>
                      <span className="text-xxs text-text-ghost font-mono">
                        {formatRelativeTime(evt.created_at || evt.timestamp)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  )
}
