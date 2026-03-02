import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import useDashboardStore from '../../stores/dashboardStore'
import HealthRing from '../shared/HealthRing'
import LoadingSkeleton from '../shared/LoadingSkeleton'

function getTrendArrow(trend) {
  if (trend == null) return { arrow: '→', cls: 'text-text-ghost' }
  if (trend > 0) return { arrow: '↑', cls: 'text-status-success' }
  if (trend < 0) return { arrow: '↓', cls: 'text-status-danger' }
  return { arrow: '→', cls: 'text-text-ghost' }
}

function getRiskStyle(risk) {
  switch (risk) {
    case 'high_risk': return 'border-status-danger/40 bg-status-danger/5'
    case 'watch': return 'border-status-warning/40 bg-status-warning/5'
    default: return 'border-border-subtle bg-transparent'
  }
}

export default function HealthTerrainWrapper() {
  const quickHealth = useDashboardStore((s) => s.quickHealth)
  const navigate = useNavigate()

  const sorted = useMemo(() => {
    if (!quickHealth?.length) return []
    return [...quickHealth].sort((a, b) => (a.health_score ?? 50) - (b.health_score ?? 50))
  }, [quickHealth])

  if (!sorted.length) {
    return (
      <div className="card p-4">
        <LoadingSkeleton variant="rect" width="100%" height={120} />
      </div>
    )
  }

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-medium text-text-primary">Customer Health</h2>
        <button
          onClick={() => navigate('/customers')}
          className="text-xxs text-text-ghost hover:text-accent transition-colors"
        >
          View all →
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2.5">
        {sorted.map((c) => {
          const score = c.health_score ?? 50
          const { arrow, cls } = getTrendArrow(c.trend)

          return (
            <button
              key={c.id}
              onClick={() => navigate(`/customers/${c.id}`)}
              className={`text-left p-3 rounded-lg border ${getRiskStyle(c.risk_level)} hover:border-border-strong transition-colors`}
            >
              <div className="flex items-center gap-2 mb-2">
                <HealthRing score={score} size="sm" showLabel={false} />
                <span className="text-xs font-medium text-text-primary truncate">
                  {c.company_name || c.name}
                </span>
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-lg font-semibold text-text-primary font-mono tabular-nums">{score}</span>
                <span className={`text-xs font-mono ${cls}`}>{arrow}</span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
