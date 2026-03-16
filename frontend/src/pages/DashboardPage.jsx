import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Users, Heart, Ticket, AlertTriangle, ArrowRight } from 'lucide-react'
import useDashboardStore from '../stores/dashboardStore'
import useAlertStore from '../stores/alertStore'
import KpiCard from '../components/shared/KpiCard'
import GlassCard from '../components/shared/GlassCard'
import HealthRing from '../components/shared/HealthRing'
import StatusPill from '../components/shared/StatusPill'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatRelativeTime } from '../utils/formatters'

export default function DashboardPage() {
  const { stats, quickHealth, events, isLoading, fetchAll } = useDashboardStore()
  const { alerts, fetchAll: fetchAlerts } = useAlertStore()

  useEffect(() => {
    fetchAll()
    fetchAlerts()
  }, [fetchAll, fetchAlerts])

  if (isLoading && !stats) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-display font-bold text-text-primary">Command Center</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <LoadingSkeleton key={i} variant="card" />
          ))}
        </div>
      </div>
    )
  }

  const openAlerts = alerts.filter((a) => a.status === 'open' || a.status === 'active')

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-display font-bold text-text-primary">Command Center</h1>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Customers"
          value={stats?.total_customers ?? '—'}
          trend={stats?.trends?.customers_change}
          icon={Users}
          color="accent"
        />
        <KpiCard
          label="Avg Health Score"
          value={stats?.avg_health_score ?? '—'}
          trend={stats?.trends?.health_change}
          icon={Heart}
          color="teal"
        />
        <KpiCard
          label="Open Tickets"
          value={stats?.open_tickets ?? '—'}
          trend={stats?.trends?.tickets_change}
          icon={Ticket}
          color="sky"
        />
        <KpiCard
          label="At Risk"
          value={stats?.at_risk_count ?? '—'}
          trend={stats?.trends?.risk_change}
          icon={AlertTriangle}
          color="accent"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer Health Table */}
        <GlassCard level="near" className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary">Customer Health</h2>
            <Link to="/customers" className="text-xs text-accent hover:text-accent/80 flex items-center gap-1">
              View all <ArrowRight size={12} />
            </Link>
          </div>
          {quickHealth.length === 0 ? (
            <p className="text-sm text-text-muted">No health data available</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-text-muted font-mono text-xxs uppercase tracking-wider border-b border-border-subtle">
                    <th className="pb-2 pr-4">Customer</th>
                    <th className="pb-2 pr-4">Score</th>
                    <th className="pb-2 pr-4">Risk</th>
                    <th className="pb-2">Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {quickHealth.map((c) => (
                    <tr key={c.id} className="border-b border-border-subtle/50 hover:bg-bg-hover/50 transition-colors">
                      <td className="py-2.5 pr-4">
                        <Link to={`/customers/${c.id}`} className="text-text-primary hover:text-accent transition-colors font-medium">
                          {c.name}
                        </Link>
                      </td>
                      <td className="py-2.5 pr-4">
                        <HealthRing score={c.health_score} size={28} strokeWidth={3} />
                      </td>
                      <td className="py-2.5 pr-4">
                        <StatusPill status={c.risk_level || 'healthy'} />
                      </td>
                      <td className="py-2.5">
                        <span className="font-mono text-xs text-text-muted">{c.risk_count || 0}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>

        {/* Recent Events */}
        <GlassCard level="mid">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Recent Events</h2>
          {events.length === 0 ? (
            <p className="text-sm text-text-muted">No recent events</p>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
              {events.slice(0, 15).map((evt) => (
                <div key={evt.id} className="flex items-start gap-3 pb-3 border-b border-border-subtle/50 last:border-0">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-text-secondary truncate">{evt.description || evt.event_type}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {evt.customer_name && (
                        <span className="text-xxs text-text-muted">{evt.customer_name}</span>
                      )}
                      <span className="text-xxs text-text-ghost font-mono">
                        {formatRelativeTime(evt.created_at || evt.timestamp)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Active Alerts */}
      {openAlerts.length > 0 && (
        <GlassCard level="near">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <AlertTriangle size={14} className="text-status-warning" />
              Active Alerts ({openAlerts.length})
            </h2>
            <Link to="/alerts" className="text-xs text-accent hover:text-accent/80 flex items-center gap-1">
              View all <ArrowRight size={12} />
            </Link>
          </div>
          <div className="space-y-2">
            {openAlerts.slice(0, 5).map((alert) => (
              <div key={alert.id} className="flex items-center gap-3 p-2 rounded-lg bg-bg-hover/30">
                <StatusPill status={alert.severity || 'medium'} />
                <span className="text-sm text-text-secondary flex-1 truncate">{alert.title}</span>
                <span className="text-xxs text-text-ghost font-mono">
                  {formatRelativeTime(alert.created_at)}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  )
}
