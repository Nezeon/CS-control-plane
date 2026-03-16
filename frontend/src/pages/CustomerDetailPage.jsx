import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import useCustomerStore from '../stores/customerStore'
import GlassCard from '../components/shared/GlassCard'
import HealthRing from '../components/shared/HealthRing'
import StatusPill from '../components/shared/StatusPill'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatDate, formatRelativeTime } from '../utils/formatters'

export default function CustomerDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    selectedCustomer: customer, detailLoading, healthHistory,
    customerTickets, customerInsights, fetchAllDetail, clearDetail,
  } = useCustomerStore()

  useEffect(() => {
    if (id) fetchAllDetail(id)
    return () => clearDetail()
  }, [id, fetchAllDetail, clearDetail])

  if (detailLoading && !customer) {
    return (
      <div className="p-6 space-y-6">
        <LoadingSkeleton variant="card" count={3} />
      </div>
    )
  }

  if (!customer) {
    return (
      <div className="p-6">
        <p className="text-text-muted">Customer not found</p>
      </div>
    )
  }

  const healthData = (healthHistory || []).map((h) => ({
    date: h.date || formatDate(h.calculated_at),
    score: h.score,
  }))

  return (
    <div className="p-6 space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/customers')}
        className="flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition-colors"
      >
        <ArrowLeft size={16} />
        Back to Customers
      </button>

      {/* Hero */}
      <GlassCard level="near">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
          <HealthRing score={customer.health_score ?? customer.current_health ?? 0} size={80} strokeWidth={5} />
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-display font-bold text-text-primary">{customer.name}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              {customer.tier && (
                <span className="text-xxs font-mono uppercase px-2 py-0.5 rounded-full bg-bg-active text-text-secondary">
                  {customer.tier}
                </span>
              )}
              <StatusPill status={customer.risk_level || 'healthy'} />
              {customer.industry && (
                <span className="text-xs text-text-muted">{customer.industry}</span>
              )}
            </div>
            <div className="flex flex-wrap gap-6 mt-3 text-xs text-text-muted">
              {customer.contact_email && <span>Contact: {customer.contact_email}</span>}
              {customer.renewal_date && <span>Renewal: {formatDate(customer.renewal_date)}</span>}
              {customer.arr && <span>ARR: ${(customer.arr / 1000).toFixed(0)}K</span>}
            </div>
          </div>
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Health Trend */}
        <GlassCard level="near">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Health Trend</h2>
          {healthData.length < 2 ? (
            <p className="text-sm text-text-muted py-8 text-center">Not enough health data</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={healthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-ghost)', fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-ghost)', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 8 }}
                  labelStyle={{ color: 'var(--text-muted)', fontSize: 11 }}
                />
                <Line type="monotone" dataKey="score" stroke="#00E5C4" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </GlassCard>

        {/* Recent Tickets */}
        <GlassCard level="near">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Tickets ({customerTickets.length})
          </h2>
          {customerTickets.length === 0 ? (
            <p className="text-sm text-text-muted py-4 text-center">No tickets</p>
          ) : (
            <div className="space-y-2 max-h-[250px] overflow-y-auto">
              {customerTickets.slice(0, 10).map((t) => (
                <div key={t.id} className="flex items-center gap-3 p-2 rounded-lg bg-bg-hover/30">
                  <StatusPill status={t.status || 'open'} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-text-primary truncate">{t.summary || t.title}</p>
                    <span className="text-xxs text-text-ghost font-mono">{t.severity || t.priority}</span>
                  </div>
                  <span className="text-xxs text-text-ghost">{formatRelativeTime(t.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Recent Calls / Insights */}
        <GlassCard level="near">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Call Insights ({customerInsights.length})
          </h2>
          {customerInsights.length === 0 ? (
            <p className="text-sm text-text-muted py-4 text-center">No call insights</p>
          ) : (
            <div className="space-y-3 max-h-[250px] overflow-y-auto">
              {customerInsights.slice(0, 8).map((insight) => (
                <div key={insight.id} className="p-2 rounded-lg bg-bg-hover/30">
                  <div className="flex items-center gap-2 mb-1">
                    <StatusPill status={insight.sentiment || 'neutral'} />
                    <span className="text-xxs text-text-ghost font-mono">
                      {formatRelativeTime(insight.processed_at || insight.created_at)}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary line-clamp-2">
                    {insight.summary || 'No summary available'}
                  </p>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Quick Info */}
        <GlassCard level="mid">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Details</h2>
          <div className="space-y-3 text-sm">
            {[
              ['CSM', customer.cs_owner_name || customer.csm_name || '—'],
              ['Contract Start', formatDate(customer.contract_start)],
              ['Deployment', customer.deployment_type || '—'],
              ['Users', customer.users_count || customer.licensed_users || '—'],
              ['Products', (customer.products || []).join(', ') || '—'],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between">
                <span className="text-text-muted">{label}</span>
                <span className="text-text-primary font-medium">{value}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
