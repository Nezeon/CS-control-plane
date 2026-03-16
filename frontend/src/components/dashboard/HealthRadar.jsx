import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { m } from 'framer-motion'
import { Crosshair } from 'lucide-react'
import useDashboardStore from '../../stores/dashboardStore'
import HealthRing from '../shared/HealthRing'
import LoadingSkeleton from '../shared/LoadingSkeleton'

const RISK_GLOW = {
  high_risk: { border: 'border-status-danger/30', shadow: '0 0 12px rgba(255,92,92,0.15)' },
  watch: { border: 'border-status-warning/20', shadow: '0 0 12px rgba(255,181,71,0.1)' },
  healthy: { border: 'border-teal/15', shadow: '0 0 12px rgba(0,229,196,0.08)' },
}

const RISK_LABELS = {
  high_risk: { text: 'AT RISK', color: 'text-status-danger' },
  watch: { text: 'WATCH', color: 'text-status-warning' },
  healthy: { text: 'STABLE', color: 'text-teal' },
}

export default function HealthRadar() {
  const quickHealth = useDashboardStore((s) => s.quickHealth)
  const navigate = useNavigate()

  const customers = useMemo(() => {
    if (!quickHealth?.length) return []
    return [...quickHealth].sort((a, b) => (a.health_score ?? 50) - (b.health_score ?? 50)).slice(0, 6)
  }, [quickHealth])

  if (!quickHealth?.length) {
    return (
      <div className="glass-near gradient-border rounded-2xl p-5 h-full">
        <div className="flex items-center gap-2 mb-4">
          <Crosshair className="w-4 h-4 text-teal" />
          <h2 className="text-sm font-semibold text-text-primary font-display tracking-wide">HEALTH RADAR</h2>
        </div>
        <LoadingSkeleton variant="card" />
      </div>
    )
  }

  return (
    <div className="glass-near gradient-border rounded-2xl p-5 h-full relative overflow-hidden">
      {/* Gradient mesh background */}
      <div
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{
          background: `
            radial-gradient(circle at 20% 80%, rgba(0,229,196,0.06) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(124,92,252,0.06) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(59,158,255,0.03) 0%, transparent 60%)
          `,
        }}
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center gap-2.5">
          <Crosshair className="w-4 h-4 text-teal" />
          <h2 className="text-sm font-semibold text-text-primary font-display tracking-wide">
            HEALTH RADAR
          </h2>
        </div>
        <button
          onClick={() => navigate('/customers')}
          className="text-xxs text-text-ghost hover:text-accent transition-colors font-mono"
        >
          View all &rarr;
        </button>
      </div>

      {/* Customer health grid — 2x3 */}
      <div className="grid grid-cols-2 gap-2.5 relative z-10">
        {customers.map((customer, i) => {
          const score = customer.health_score ?? 50
          const riskConfig = RISK_GLOW[customer.risk_level] || RISK_GLOW.healthy
          const riskLabel = RISK_LABELS[customer.risk_level] || RISK_LABELS.healthy

          return (
            <m.button
              key={customer.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              onClick={() => navigate(`/customers/${customer.id}`)}
              className={`flex items-center gap-3 p-3 rounded-xl bg-bg-active/20 border ${riskConfig.border} hover:bg-bg-active/40 transition-all group text-left`}
              style={{ boxShadow: riskConfig.shadow }}
            >
              <HealthRing score={score} size={40} strokeWidth={3} className="shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-text-primary truncate group-hover:text-accent transition-colors">
                  {customer.company_name || customer.name}
                </p>
                <span className={`text-xxs font-mono font-semibold tracking-wider ${riskLabel.color}`}>
                  {riskLabel.text}
                </span>
              </div>
            </m.button>
          )
        })}
      </div>
    </div>
  )
}
