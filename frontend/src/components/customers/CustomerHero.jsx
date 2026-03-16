import { Calendar, User, Ticket, ShieldAlert } from 'lucide-react'
import GlassCard from '../shared/GlassCard'
import HealthRing from '../shared/HealthRing'
import StatusPill from '../shared/StatusPill'

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

function tierBadgeClass(tier) {
  if (tier === 'enterprise') return 'bg-accent/10 text-accent border-accent/20'
  if (tier === 'mid_market' || tier === 'mid-market') return 'bg-teal/10 text-teal border-teal/20'
  return 'bg-bg-active text-text-muted border-border-subtle'
}

export default function CustomerHero({ customer }) {
  if (!customer) return null

  const days = daysUntil(customer.contract_end || customer.renewal_date)
  const score = customer.health_score ?? 50
  const csOwner = customer.cs_owner
    ? (typeof customer.cs_owner === 'object' ? customer.cs_owner.full_name : customer.cs_owner)
    : null

  return (
    <GlassCard level="near" className="!p-5">
      <div className="flex flex-col md:flex-row md:items-center gap-6 md:gap-8">
        {/* Left: Company identity */}
        <div className="flex-1 min-w-0">
          <h2 className="font-display text-2xl font-semibold text-text-primary truncate">
            {customer.company_name || customer.name}
          </h2>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            {customer.industry && (
              <span className="text-sm text-text-secondary">{customer.industry}</span>
            )}
            <span className={`text-xxs font-medium px-2 py-0.5 rounded-full border ${tierBadgeClass(customer.tier)}`}>
              {tierLabel(customer.tier)}
            </span>
          </div>
        </div>

        {/* Center: Large health ring */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <HealthRing score={score} size={80} strokeWidth={5} />
        </div>

        {/* Right: Stats row */}
        <div className="flex flex-wrap items-center gap-5 md:gap-6">
          {/* Risk status */}
          <StatItem icon={ShieldAlert} label="Risk">
            <StatusPill status={riskToStatus(customer.risk_level)} size="sm" />
          </StatItem>

          {/* Renewal */}
          {days != null && (
            <StatItem icon={Calendar} label="Renewal">
              <span className={`text-sm font-mono font-medium tabular-nums ${
                days < 30 ? 'text-status-danger' : days < 90 ? 'text-status-warning' : 'text-text-primary'
              }`}>
                {days}d
              </span>
            </StatItem>
          )}

          {/* Open tickets */}
          {customer.open_tickets != null && (
            <StatItem icon={Ticket} label="Open Tickets">
              <span className="text-sm font-mono font-medium text-text-primary tabular-nums">
                {customer.open_tickets}
              </span>
            </StatItem>
          )}

          {/* CS Owner */}
          {csOwner && (
            <StatItem icon={User} label="CS Owner">
              <span className="text-sm text-text-primary">{csOwner}</span>
            </StatItem>
          )}
        </div>
      </div>
    </GlassCard>
  )
}

function StatItem({ icon: Icon, label, children }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5">
        <Icon className="w-3 h-3 text-text-ghost" />
        <span className="text-xxs text-text-ghost uppercase tracking-wide">{label}</span>
      </div>
      {children}
    </div>
  )
}
