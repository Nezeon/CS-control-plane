import HealthRing from '../shared/HealthRing'

function getRiskBorder(risk) {
  switch (risk) {
    case 'high_risk': return 'border-l-status-danger'
    case 'watch': return 'border-l-status-warning'
    default: return 'border-l-status-success'
  }
}

function daysUntil(dateStr) {
  if (!dateStr) return null
  const diff = Math.ceil((new Date(dateStr) - Date.now()) / 86400000)
  return diff
}

export default function PremiumGrid({ customers = [], onCustomerClick, onHover }) {
  if (!customers.length) {
    return <p className="text-sm text-text-ghost py-12 text-center">No customers match your filters</p>
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
      {customers.map((c) => {
        const days = daysUntil(c.contract_end || c.renewal_date)
        const score = c.health_score ?? 50

        return (
          <button
            key={c.id}
            onClick={() => onCustomerClick?.(c)}
            onMouseEnter={() => onHover?.(c)}
            onMouseLeave={() => onHover?.(null)}
            className={`card-interactive text-left p-4 border-l-2 ${getRiskBorder(c.risk_level)}`}
          >
            <div className="flex items-start gap-3">
              <HealthRing score={score} size="sm" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">{c.company_name || c.name}</p>
                <p className="text-xs text-text-muted mt-0.5">
                  {c.tier === 'enterprise' ? 'Enterprise' : c.tier === 'mid_market' ? 'Mid-Market' : 'SMB'}
                  {c.industry ? ` · ${c.industry}` : ''}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 mt-3 pt-2.5 border-t border-border-subtle">
              {c.open_tickets != null && (
                <span className="text-xxs text-text-ghost">
                  <span className="font-mono text-text-muted">{c.open_tickets}</span> tickets
                </span>
              )}
              {c.cs_owner && (
                <span className="text-xxs text-text-ghost truncate">{c.cs_owner}</span>
              )}
              {days != null && (
                <span className={`text-xxs font-mono ml-auto ${days < 30 ? 'text-status-danger' : days < 90 ? 'text-status-warning' : 'text-text-ghost'}`}>
                  {days}d
                </span>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
