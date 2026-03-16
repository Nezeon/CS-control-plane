import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart } from 'lucide-react'
import useDashboardStore from '../../stores/dashboardStore'
import GlassCard from '../shared/GlassCard'
import HealthRing from '../shared/HealthRing'
import SparkLine from '../shared/SparkLine'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { cn } from '../../utils/cn'

const riskBadgeStyles = {
  high_risk: 'bg-status-danger/10 text-status-danger border-status-danger/20',
  watch: 'bg-status-warning/10 text-status-warning border-status-warning/20',
  healthy: 'bg-teal/10 text-teal border-teal/20',
}

function generateSparkData(score, trend) {
  // Generate a simple sparkline based on score and trend direction
  const base = score
  const points = []
  for (let i = 0; i < 7; i++) {
    const noise = (Math.random() - 0.5) * 8
    const trendEffect = trend ? (trend / 7) * i : 0
    points.push(Math.max(0, Math.min(100, base - trendEffect * 2 + noise)))
  }
  // Make last point closer to actual score
  points[points.length - 1] = score
  return points
}

function getRiskLabel(risk) {
  switch (risk) {
    case 'high_risk': return 'At Risk'
    case 'watch': return 'Watch'
    case 'healthy': return 'Healthy'
    default: return risk
  }
}

function getSparkColor(risk) {
  switch (risk) {
    case 'high_risk': return '#FF5C5C'
    case 'watch': return '#FFB547'
    default: return '#00E5C4'
  }
}

export default function HealthOverview() {
  const quickHealth = useDashboardStore((s) => s.quickHealth)
  const navigate = useNavigate()

  const sorted = useMemo(() => {
    if (!quickHealth?.length) return []
    return [...quickHealth].sort((a, b) => (a.health_score ?? 50) - (b.health_score ?? 50)).slice(0, 8)
  }, [quickHealth])

  if (!quickHealth?.length) {
    return (
      <GlassCard level="near" className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-text-primary font-display">Customer Health</h2>
        </div>
        <LoadingSkeleton variant="card" />
      </GlassCard>
    )
  }

  return (
    <GlassCard level="near" className="p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Heart className="w-3.5 h-3.5 text-teal" />
          <h2 className="text-sm font-semibold text-text-primary font-display">Customer Health</h2>
        </div>
        <button
          onClick={() => navigate('/customers')}
          className="text-xxs text-text-ghost hover:text-accent transition-colors"
        >
          View all &rarr;
        </button>
      </div>

      {/* Customer mini cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {sorted.map((customer) => {
          const score = customer.health_score ?? 50
          const sparkData = generateSparkData(score, customer.trend)
          const riskStyle = riskBadgeStyles[customer.risk_level] || riskBadgeStyles.healthy
          const sparkColor = getSparkColor(customer.risk_level)

          return (
            <button
              key={customer.id}
              onClick={() => navigate(`/customers/${customer.id}`)}
              className="flex items-center gap-3 p-3 rounded-xl bg-bg-active/30 border border-border-subtle hover:border-border-strong transition-all group text-left"
            >
              {/* Health ring */}
              <HealthRing score={score} size={36} strokeWidth={3} className="flex-shrink-0" />

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-text-primary truncate group-hover:text-accent transition-colors">
                  {customer.company_name || customer.name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={cn(
                      'inline-flex items-center px-1.5 py-0.5 rounded text-xxs font-medium border',
                      riskStyle
                    )}
                  >
                    {getRiskLabel(customer.risk_level)}
                  </span>
                  <SparkLine
                    data={sparkData}
                    width={48}
                    height={14}
                    color={sparkColor}
                  />
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </GlassCard>
  )
}
