import { Users, AlertTriangle, Ticket, HeartPulse } from 'lucide-react'
import useDashboardStore from '../../stores/dashboardStore'
import LoadingSkeleton from '../shared/LoadingSkeleton'

export default function FloatingOrbsGrid() {
  const stats = useDashboardStore((s) => s.stats)

  if (!stats) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <LoadingSkeleton key={i} variant="card" height={88} />
        ))}
      </div>
    )
  }

  const metrics = [
    {
      value: stats.total_customers,
      label: 'Customers',
      trend: stats.trends?.customers_change ?? stats.trend?.customers,
      icon: Users,
      color: 'text-accent',
    },
    {
      value: `${Math.round(stats.avg_health_score ?? stats.avg_health ?? 0)}%`,
      label: 'Avg Health',
      trend: stats.trends?.health_change ?? stats.trend?.health,
      icon: HeartPulse,
      color: 'text-status-success',
    },
    {
      value: stats.open_tickets ?? stats.total_tickets_open ?? 0,
      label: 'Open Tickets',
      trend: stats.trends?.tickets_change ?? stats.trend?.tickets,
      icon: Ticket,
      color: 'text-status-warning',
    },
    {
      value: stats.at_risk_count ?? stats.high_risk ?? 0,
      label: 'At Risk',
      trend: stats.trends?.risk_change,
      icon: AlertTriangle,
      color: 'text-status-danger',
    },
  ]

  return (
    <div data-testid="kpi-bar" className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {metrics.map((m) => (
        <div key={m.label} className="card px-4 py-3.5 flex items-start gap-3">
          <div className={`mt-0.5 ${m.color}`}>
            <m.icon className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-text-muted">{m.label}</p>
            <p className="text-lg font-semibold text-text-primary font-mono tabular-nums mt-0.5">
              {m.value}
            </p>
            {m.trend != null && (
              <p className={`text-xxs font-mono mt-0.5 ${m.trend >= 0 ? 'text-status-success' : 'text-status-danger'}`}>
                {m.trend >= 0 ? '+' : ''}{typeof m.trend === 'number' ? m.trend.toFixed(1) : m.trend}%
                {m.trend >= 0 ? ' ↑' : ' ↓'}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
