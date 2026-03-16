import { m } from 'framer-motion'
import GlassCard from '../shared/GlassCard'
import HealthRing from '../shared/HealthRing'
import StatusPill from '../shared/StatusPill'
import SparkLine from '../shared/SparkLine'

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

function tierColor(tier) {
  if (tier === 'enterprise') return 'text-accent'
  if (tier === 'mid_market' || tier === 'mid-market') return 'text-teal'
  return 'text-text-muted'
}

const containerVariants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.04 },
  },
}

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
}

export default function PremiumGrid({ customers = EMPTY_ARRAY, onCustomerClick, onHover }) {
  if (!customers.length) {
    return <p className="text-sm text-text-ghost py-12 text-center">No customers match your filters</p>
  }

  return (
    <m.div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      {customers.map((c) => {
        const days = daysUntil(c.contract_end || c.renewal_date)
        const score = c.health_score ?? 50
        const sparkData = c.health_trend || c.spark_data || null

        return (
          <m.div key={c.id} variants={cardVariants}>
            <GlassCard
              interactive
              className="!p-0 cursor-pointer"
              onClick={() => onCustomerClick?.(c)}
              onMouseEnter={() => onHover?.(c)}
              onMouseLeave={() => onHover?.(null)}
            >
              <div className="p-4 space-y-3">
                {/* Company name + industry row */}
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-text-primary truncate">
                      {c.company_name || c.name}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {c.industry && (
                        <span className="text-xs text-text-muted">{c.industry}</span>
                      )}
                      <span className={`text-xxs font-medium px-2 py-0.5 rounded-full border border-border-subtle ${tierColor(c.tier)}`}>
                        {tierLabel(c.tier)}
                      </span>
                    </div>
                  </div>
                  <StatusPill status={riskToStatus(c.risk_level)} size="sm" />
                </div>

                {/* Health ring + score + sparkline row */}
                <div className="flex items-center gap-4">
                  <HealthRing score={score} size={48} strokeWidth={3} />
                  <div className="flex-1 min-w-0">
                    <span className="text-lg font-display font-bold text-text-primary">{score}</span>
                    <span className="text-xxs text-text-ghost ml-1">/ 100</span>
                    {sparkData && sparkData.length >= 2 && (
                      <div className="mt-1">
                        <SparkLine
                          data={sparkData}
                          width={100}
                          height={20}
                          color={score >= 70 ? '#00E5C4' : score >= 40 ? '#FFB547' : '#FF5C5C'}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom stats row */}
                <div className="flex items-center gap-4 pt-2 border-t border-border-subtle">
                  {/* Renewal countdown */}
                  {days != null && (
                    <span className="flex items-center gap-1 text-xs">
                      <span className="text-text-ghost">Renewal:</span>
                      <span className={`font-mono font-medium tabular-nums ${
                        days < 30 ? 'text-status-danger' : days < 90 ? 'text-status-warning' : 'text-status-success'
                      }`}>
                        {days}d
                      </span>
                    </span>
                  )}
                  {c.open_tickets != null && (
                    <span className="text-xs text-text-ghost">
                      <span className="font-mono text-text-muted">{c.open_tickets}</span> tickets
                    </span>
                  )}
                  {c.cs_owner && (
                    <span className="text-xs text-text-ghost truncate ml-auto">
                      {typeof c.cs_owner === 'object' ? c.cs_owner.full_name : c.cs_owner}
                    </span>
                  )}
                </div>
              </div>
            </GlassCard>
          </m.div>
        )
      })}
    </m.div>
  )
}
