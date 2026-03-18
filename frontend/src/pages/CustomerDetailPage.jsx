import { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Shield, Phone, FileText, Activity, BarChart3 } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import useCustomerStore from '../stores/customerStore'
import GlassCard from '../components/shared/GlassCard'
import HealthRing from '../components/shared/HealthRing'
import StatusPill from '../components/shared/StatusPill'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatDate, formatRelativeTime } from '../utils/formatters'
import TicketDetailDrawer from '../components/shared/TicketDetailDrawer'

const TABS = [
  { key: 'overview', label: 'Overview', icon: Shield },
  { key: 'tickets', label: 'Tickets', icon: FileText },
  { key: 'calls', label: 'Calls', icon: Phone },
  { key: 'health', label: 'Health History', icon: Activity },
  { key: 'qbr', label: 'QBR', icon: BarChart3 },
]

function daysUntil(dateStr) {
  if (!dateStr) return null
  return Math.ceil((new Date(dateStr) - new Date()) / (1000 * 60 * 60 * 24))
}

export default function CustomerDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = searchParams.get('tab') || 'overview'
  const [activeTab, setActiveTab] = useState(initialTab)

  const {
    selectedCustomer: customer, detailLoading, healthHistory,
    customerTickets, customerInsights, fetchAllDetail, clearDetail,
  } = useCustomerStore()

  useEffect(() => {
    if (id) fetchAllDetail(id)
    return () => clearDetail()
  }, [id, fetchAllDetail, clearDetail])

  // Sync tab with URL
  const switchTab = (tab) => {
    setActiveTab(tab)
    setSearchParams({ tab })
  }

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

  const renewalDays = daysUntil(customer.renewal_date)

  return (
    <div className="p-6 space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/customers')}
        className="flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition-colors"
      >
        <ArrowLeft size={16} /> Back to Customers
      </button>

      {/* Customer Header — per ARCHITECTURE.md Section 7.2 */}
      <GlassCard level="near">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
          <HealthRing score={customer.health?.current_score ?? customer.health_score ?? 0} size={80} strokeWidth={5} />
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-display font-bold text-text-primary">{customer.name}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              {customer.tier && (
                <span className="text-xxs font-mono uppercase px-2 py-0.5 rounded-full bg-bg-active text-text-secondary">
                  {customer.tier}
                </span>
              )}
              <StatusPill status={customer.health?.risk_level || customer.risk_level || 'healthy'} />
              {customer.industry && (
                <span className="text-xs text-text-muted">{customer.industry}</span>
              )}
            </div>
            <div className="flex flex-wrap gap-6 mt-3 text-xs text-text-muted">
              {customer.cs_owner?.full_name && <span>CSM: {customer.cs_owner.full_name}</span>}
              {renewalDays != null && (
                <span className={renewalDays <= 90 ? 'text-status-warning font-semibold' : ''}>
                  Renewal: {renewalDays}d ({formatDate(customer.renewal_date)})
                </span>
              )}
              {customer.deployment?.mode && <span>Deploy: {customer.deployment.mode}</span>}
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 border-b border-border-subtle overflow-x-auto">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => switchTab(key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm transition-colors whitespace-nowrap border-b-2 ${
              activeTab === key
                ? 'border-accent text-accent'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab customer={customer} />}
      {activeTab === 'tickets' && <TicketsTab tickets={customerTickets} />}
      {activeTab === 'calls' && <CallsTab insights={customerInsights} />}
      {activeTab === 'health' && <HealthTab history={healthHistory} />}
      {activeTab === 'qbr' && <QBRTab customer={customer} />}
    </div>
  )
}

// ── Tab Components ──────────────────────────────────────────────────

function OverviewTab({ customer }) {
  const deployment = customer.deployment || {}
  const health = customer.health || {}

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <GlassCard level="near">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Deployment</h3>
        <div className="space-y-2 text-sm">
          {[
            ['Mode', deployment.mode || customer.deployment_mode || '—'],
            ['Version', deployment.product_version || customer.product_version || '—'],
            ['Integrations', (deployment.integrations || customer.integrations || []).join(', ') || '—'],
            ['Constraints', (deployment.known_constraints || customer.known_constraints || []).join(', ') || '—'],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between">
              <span className="text-text-muted">{label}</span>
              <span className="text-text-primary text-right max-w-[60%]">{value}</span>
            </div>
          ))}
        </div>
      </GlassCard>

      <GlassCard level="near">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Health & Risk</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-muted">Health Score</span>
            <span className="text-text-primary font-semibold">{health.current_score ?? customer.health_score ?? '—'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Risk Level</span>
            <StatusPill status={health.risk_level || customer.risk_level || 'healthy'} />
          </div>
          <div className="flex justify-between items-start">
            <span className="text-text-muted">Risk Flags</span>
            <div className="flex flex-wrap gap-1 justify-end max-w-[60%]">
              {(health.risk_flags || []).length > 0 ? (
                health.risk_flags.map((f) => (
                  <span key={f} className="text-xxs px-1.5 py-0.5 rounded bg-status-danger/10 text-status-danger">
                    {f}
                  </span>
                ))
              ) : (
                <span className="text-text-ghost text-xs">None</span>
              )}
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard level="mid" className="lg:col-span-2">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Customer Info</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          {[
            ['Contact', customer.primary_contact_name || '—'],
            ['Email', customer.primary_contact_email || '—'],
            ['Contract Start', formatDate(customer.contract_start)],
            ['Renewal', formatDate(customer.renewal_date)],
            ['Open Tickets', customer.open_ticket_count ?? '—'],
            ['Recent Calls', customer.recent_call_count ?? '—'],
            ['Pending Actions', customer.pending_action_items ?? '—'],
            ['Industry', customer.industry || '—'],
          ].map(([label, value]) => (
            <div key={label}>
              <span className="text-xxs text-text-ghost uppercase tracking-wider">{label}</span>
              <p className="text-text-primary mt-0.5">{value}</p>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  )
}

function TicketsTab({ tickets }) {
  const [selectedTicketId, setSelectedTicketId] = useState(null)

  return (
    <>
      <GlassCard level="near">
        <h3 className="text-sm font-semibold text-text-primary mb-4">Tickets ({tickets.length})</h3>
        {tickets.length === 0 ? (
          <p className="text-sm text-text-muted py-4 text-center">No tickets</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-muted font-mono text-xxs uppercase tracking-wider border-b border-border-subtle">
                  <th className="pb-2 pr-3">ID</th>
                  <th className="pb-2 pr-3">Summary</th>
                  <th className="pb-2 pr-3">Severity</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3">SLA</th>
                  <th className="pb-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-border-subtle/50 hover:bg-bg-hover/50 cursor-pointer transition-colors"
                    onClick={() => setSelectedTicketId(t.id)}
                  >
                    <td className="py-2 pr-3 font-mono text-xs text-accent">{t.jira_id || '—'}</td>
                    <td className="py-2 pr-3 text-text-primary max-w-[300px] truncate">{t.summary}</td>
                    <td className="py-2 pr-3"><StatusPill status={t.severity || 'P3'} /></td>
                    <td className="py-2 pr-3"><StatusPill status={t.status || 'open'} /></td>
                    <td className="py-2 pr-3">
                      {t.sla_remaining_hours != null ? (
                        <span className={`font-mono text-xs ${t.sla_breaching ? 'text-status-danger' : 'text-text-muted'}`}>
                          {t.sla_remaining_hours}h
                        </span>
                      ) : '—'}
                    </td>
                    <td className="py-2 text-xxs text-text-ghost">{formatRelativeTime(t.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      <TicketDetailDrawer
        ticketId={selectedTicketId}
        open={!!selectedTicketId}
        onClose={() => setSelectedTicketId(null)}
      />
    </>
  )
}

function CallsTab({ insights }) {
  return (
    <GlassCard level="near">
      <h3 className="text-sm font-semibold text-text-primary mb-4">Call Insights ({insights.length})</h3>
      {insights.length === 0 ? (
        <p className="text-sm text-text-muted py-4 text-center">No call insights</p>
      ) : (
        <div className="space-y-4">
          {insights.map((insight) => (
            <div key={insight.id} className="p-3 rounded-lg bg-bg-hover/30 border border-border-subtle/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <StatusPill status={insight.sentiment || 'neutral'} />
                  {insight.sentiment_score != null && (
                    <span className="text-xxs text-text-ghost font-mono">
                      ({(insight.sentiment_score * 100).toFixed(0)}%)
                    </span>
                  )}
                </div>
                <span className="text-xxs text-text-ghost">{formatDate(insight.call_date)}</span>
              </div>
              <p className="text-xs text-text-secondary mb-2">{insight.summary || 'No summary'}</p>
              {insight.key_topics?.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {insight.key_topics.map((t, i) => (
                    <span key={i} className="text-xxs px-1.5 py-0.5 rounded bg-accent/10 text-accent">{t}</span>
                  ))}
                </div>
              )}
              {insight.action_items?.length > 0 && (
                <div className="mt-2 text-xs text-text-muted">
                  <span className="font-semibold">Actions:</span>
                  {insight.action_items.slice(0, 3).map((a, i) => (
                    <p key={i} className="ml-2">- {typeof a === 'string' ? a : a.task || JSON.stringify(a)}</p>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  )
}

function HealthTab({ history }) {
  const healthData = (history || []).map((h) => ({
    date: h.date || formatDate(h.calculated_at),
    score: h.score,
  }))

  return (
    <GlassCard level="near">
      <h3 className="text-sm font-semibold text-text-primary mb-4">Health Score Over Time</h3>
      {healthData.length < 2 ? (
        <p className="text-sm text-text-muted py-8 text-center">Not enough health data</p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
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
      {/* Risk Flag Timeline */}
      {history?.length > 0 && (
        <div className="mt-6">
          <h4 className="text-xs font-semibold text-text-muted mb-2">Risk Flag History</h4>
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {history.filter((h) => h.risk_flags?.length > 0).slice(0, 10).map((h, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="text-text-ghost font-mono w-20">{h.date}</span>
                <div className="flex gap-1 flex-wrap">
                  {h.risk_flags.map((f) => (
                    <span key={f} className="px-1.5 py-0.5 rounded bg-status-danger/10 text-status-danger text-xxs">{f}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </GlassCard>
  )
}

function QBRTab({ customer }) {
  return (
    <GlassCard level="near">
      <h3 className="text-sm font-semibold text-text-primary mb-4">QBR / Value Narrative</h3>
      <p className="text-sm text-text-muted py-8 text-center">
        QBR drafts will appear here once generated by the QBR Agent (Sofia Marquez).
        Trigger a QBR via the agent system or wait for the quarterly schedule.
      </p>
      <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div>
          <span className="text-xxs text-text-ghost uppercase">Sentiment Bucket</span>
          <p className="text-text-primary mt-0.5">{customer.sentiment_bucket || '—'}</p>
        </div>
        <div>
          <span className="text-xxs text-text-ghost uppercase">Health Score</span>
          <p className="text-text-primary mt-0.5">{customer.health?.current_score ?? customer.health_score ?? '—'}</p>
        </div>
      </div>
    </GlassCard>
  )
}
