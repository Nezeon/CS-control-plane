import { Calendar, User, Building2, DollarSign, Ticket, AlertTriangle } from 'lucide-react'
import HealthRing from '../shared/HealthRing'

function daysUntil(dateStr) {
  if (!dateStr) return null
  return Math.ceil((new Date(dateStr) - Date.now()) / 86400000)
}

function getRiskBadge(risk) {
  switch (risk) {
    case 'high_risk': return { label: 'High Risk', cls: 'bg-status-danger/10 text-status-danger border-status-danger/20' }
    case 'watch': return { label: 'Watch', cls: 'bg-status-warning/10 text-status-warning border-status-warning/20' }
    default: return { label: 'Healthy', cls: 'bg-status-success/10 text-status-success border-status-success/20' }
  }
}

export default function CustomerHero({ customer }) {
  if (!customer) return null

  const days = daysUntil(customer.contract_end || customer.renewal_date)
  const risk = getRiskBadge(customer.risk_level)
  const score = customer.health_score ?? 50

  return (
    <div className="card p-5">
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        {/* Left — identity */}
        <div className="flex items-start gap-4 flex-1 min-w-0">
          <HealthRing score={score} size="lg" />
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-text-primary truncate">
              {customer.company_name || customer.name}
            </h2>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xs text-text-muted capitalize">{(customer.tier || '').replace('_', '-')}</span>
              {customer.industry && (
                <>
                  <span className="text-text-ghost">·</span>
                  <span className="text-xs text-text-muted">{customer.industry}</span>
                </>
              )}
              <span className={`text-xxs px-2 py-0.5 rounded-md border ${risk.cls}`}>{risk.label}</span>
            </div>
          </div>
        </div>

        {/* Right — key stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2 text-xs sm:text-right">
          {customer.cs_owner && (
            <Stat icon={User} label="CS Owner" value={customer.cs_owner} />
          )}
          {customer.arr != null && (
            <Stat icon={DollarSign} label="ARR" value={`$${(customer.arr / 1000000).toFixed(1)}M`} />
          )}
          {days != null && (
            <Stat
              icon={Calendar}
              label="Renewal"
              value={`${days}d`}
              valueClass={days < 30 ? 'text-status-danger' : days < 90 ? 'text-status-warning' : ''}
            />
          )}
          {customer.open_tickets != null && (
            <Stat icon={Ticket} label="Tickets" value={customer.open_tickets} />
          )}
          {customer.deployment?.deployment_mode && (
            <Stat icon={Building2} label="Deploy" value={customer.deployment.deployment_mode} />
          )}
        </div>
      </div>
    </div>
  )
}

function Stat({ icon: Icon, label, value, valueClass = '' }) {
  return (
    <div className="flex items-center gap-1.5 sm:justify-end">
      <Icon className="w-3 h-3 text-text-ghost" />
      <span className="text-text-ghost">{label}:</span>
      <span className={`font-medium text-text-primary font-mono ${valueClass}`}>{value}</span>
    </div>
  )
}
