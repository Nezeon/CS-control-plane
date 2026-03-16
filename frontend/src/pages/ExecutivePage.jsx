import { useEffect, useState } from 'react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'
import { TrendingDown, TrendingUp, RefreshCw, ShieldAlert } from 'lucide-react'
import GlassCard from '../components/shared/GlassCard'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import StatusPill from '../components/shared/StatusPill'
import GradientButton from '../components/shared/GradientButton'
import PillFilter from '../components/shared/PillFilter'
import { formatDate } from '../utils/formatters'
import api from '../services/api'

const PERIOD_OPTIONS = [
  { value: '7', label: '7 days' },
  { value: '14', label: '14 days' },
  { value: '30', label: '30 days' },
  { value: '60', label: '60 days' },
  { value: '90', label: '90 days' },
]

export default function ExecutivePage() {
  const [days, setDays] = useState('30')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [rulesLoading, setRulesLoading] = useState(false)
  const [rulesResult, setRulesResult] = useState(null)

  const fetchSummary = async () => {
    setLoading(true)
    try {
      const { data: result } = await api.get('/executive/summary', { params: { days: parseInt(days) } })
      setData(result)
    } catch (err) {
      console.error('[Executive] Failed to fetch summary:', err)
    }
    setLoading(false)
  }

  useEffect(() => { fetchSummary() }, [days])

  const runAlertRules = async () => {
    setRulesLoading(true)
    try {
      const { data: result } = await api.post('/executive/check-rules')
      setRulesResult(result)
    } catch (err) {
      console.error('[Executive] Failed to run alert rules:', err)
    }
    setRulesLoading(false)
  }

  const snapshot = data?.snapshot
  const health = data?.health
  const tickets = data?.tickets
  const sentiment = data?.sentiment

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-2xl font-display font-bold text-text-primary">Executive Summary</h1>
        <div className="flex items-center gap-3">
          <PillFilter options={PERIOD_OPTIONS} value={days} onChange={setDays} />
          <GradientButton size="sm" icon={RefreshCw} onClick={fetchSummary} loading={loading}>
            Refresh
          </GradientButton>
          <GradientButton size="sm" icon={ShieldAlert} onClick={runAlertRules} loading={rulesLoading}>
            Run Rules
          </GradientButton>
        </div>
      </div>

      {/* Rules result banner */}
      {rulesResult && (
        <GlassCard level="mid" className="flex items-center gap-3">
          <ShieldAlert size={16} className="text-accent" />
          <span className="text-sm text-text-secondary">
            Checked {rulesResult.rules_checked} rules, created {rulesResult.alerts_created} new alert{rulesResult.alerts_created !== 1 ? 's' : ''}.
          </span>
          <button onClick={() => setRulesResult(null)} className="ml-auto text-xs text-text-ghost hover:text-text-muted">
            Dismiss
          </button>
        </GlassCard>
      )}

      {loading && !data ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <LoadingSkeleton key={i} variant="chart" />)}
        </div>
      ) : !data ? (
        <p className="text-sm text-text-muted text-center py-8">No data available</p>
      ) : (
        <>
          {/* Portfolio Snapshot KPIs */}
          {snapshot && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Total Customers', value: snapshot.total_customers },
                { label: 'Critical', value: snapshot.risk_distribution?.critical || 0, color: 'text-status-danger' },
                { label: 'High Risk', value: snapshot.risk_distribution?.high_risk || 0, color: 'text-status-warning' },
                { label: 'Healthy', value: snapshot.risk_distribution?.healthy || 0, color: 'text-teal' },
              ].map((kpi) => (
                <GlassCard key={kpi.label} level="near">
                  <span className="font-mono text-xxs uppercase text-text-ghost">{kpi.label}</span>
                  <p className={`text-2xl font-display font-bold mt-1 ${kpi.color || 'text-text-primary'}`}>
                    {kpi.value}
                  </p>
                </GlassCard>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Health Trend */}
            {health?.daily_avg?.length > 0 && (
              <GlassCard level="near">
                <h2 className="text-sm font-semibold text-text-primary mb-4">Health Trend (Daily Avg)</h2>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={health.daily_avg}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                    <XAxis dataKey="date" tick={{ fill: 'var(--text-ghost)', fontSize: 10 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-ghost)', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 8 }}
                    />
                    <Line type="monotone" dataKey="avg_score" stroke="#00E5C4" strokeWidth={2} dot={false} name="Avg Score" />
                  </LineChart>
                </ResponsiveContainer>
              </GlassCard>
            )}

            {/* Ticket Velocity */}
            {tickets?.daily?.length > 0 && (
              <GlassCard level="near">
                <h2 className="text-sm font-semibold text-text-primary mb-4">Ticket Velocity</h2>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={tickets.daily}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                    <XAxis dataKey="date" tick={{ fill: 'var(--text-ghost)', fontSize: 10 }} />
                    <YAxis tick={{ fill: 'var(--text-ghost)', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 8 }}
                    />
                    <Legend />
                    <Bar dataKey="created" fill="#FF5C5C" name="Created" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="resolved" fill="#00E5C4" name="Resolved" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                {tickets.totals && (
                  <div className="flex gap-6 mt-3 text-xs">
                    <span className="text-text-muted">Created: <strong className="text-status-danger">{tickets.totals.created}</strong></span>
                    <span className="text-text-muted">Resolved: <strong className="text-teal">{tickets.totals.resolved}</strong></span>
                    <span className="text-text-muted">Net Open: <strong className="text-text-primary">{tickets.totals.net_open}</strong></span>
                  </div>
                )}
              </GlassCard>
            )}

            {/* Biggest Drops / Gains */}
            {health && (
              <GlassCard level="near">
                <h2 className="text-sm font-semibold text-text-primary mb-4">Health Changes</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-xxs font-mono uppercase text-status-danger mb-2 flex items-center gap-1">
                      <TrendingDown size={12} /> Biggest Drops
                    </h3>
                    {(health.biggest_drops || []).length === 0 ? (
                      <p className="text-xs text-text-ghost">None</p>
                    ) : (
                      <div className="space-y-1.5">
                        {health.biggest_drops.map((d) => (
                          <div key={d.customer_id} className="flex items-center justify-between">
                            <span className="text-xs text-text-secondary truncate">{d.name}</span>
                            <span className="text-xs font-mono text-status-danger">{d.delta}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-xxs font-mono uppercase text-teal mb-2 flex items-center gap-1">
                      <TrendingUp size={12} /> Biggest Gains
                    </h3>
                    {(health.biggest_gains || []).length === 0 ? (
                      <p className="text-xs text-text-ghost">None</p>
                    ) : (
                      <div className="space-y-1.5">
                        {health.biggest_gains.map((d) => (
                          <div key={d.customer_id} className="flex items-center justify-between">
                            <span className="text-xs text-text-secondary truncate">{d.name}</span>
                            <span className="text-xs font-mono text-teal">+{d.delta}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </GlassCard>
            )}

            {/* Sentiment */}
            {sentiment && (
              <GlassCard level="near">
                <h2 className="text-sm font-semibold text-text-primary mb-4">Call Sentiment</h2>
                {sentiment.avg_score != null && (
                  <p className="text-xs text-text-muted mb-3">
                    Average Score: <strong className="text-text-primary">{sentiment.avg_score}</strong>
                  </p>
                )}
                {sentiment.distribution && Object.keys(sentiment.distribution).length > 0 ? (
                  <div className="flex gap-3 mb-4">
                    {Object.entries(sentiment.distribution).map(([key, val]) => (
                      <div key={key} className="flex-1 text-center">
                        <p className="text-lg font-display font-bold text-text-primary">{val}</p>
                        <span className="text-xxs font-mono uppercase text-text-ghost">{key}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-ghost">No sentiment data</p>
                )}
                {sentiment.recent_negative?.length > 0 && (
                  <div>
                    <h3 className="text-xxs font-mono uppercase text-text-ghost mb-2">Recent Negative</h3>
                    <div className="space-y-1.5">
                      {sentiment.recent_negative.slice(0, 5).map((n) => (
                        <div key={n.id} className="flex items-center gap-2">
                          <StatusPill status={n.sentiment} />
                          <span className="text-xs text-text-secondary truncate flex-1">{n.customer_name}</span>
                          <span className="text-xxs text-text-ghost truncate max-w-[200px]">{n.summary}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </GlassCard>
            )}
          </div>

          {/* Upcoming Renewals */}
          {snapshot?.upcoming_renewals?.length > 0 && (
            <GlassCard level="near">
              <h2 className="text-sm font-semibold text-text-primary mb-4">
                Upcoming Renewals (Next 90 Days)
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-text-muted font-mono text-xxs uppercase tracking-wider border-b border-border-subtle">
                      <th className="pb-2 pr-4">Customer</th>
                      <th className="pb-2 pr-4">Tier</th>
                      <th className="pb-2 pr-4">Renewal Date</th>
                      <th className="pb-2 pr-4">Health</th>
                      <th className="pb-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {snapshot.upcoming_renewals.map((r) => (
                      <tr key={r.customer_id} className="border-b border-border-subtle/50">
                        <td className="py-2 pr-4 text-text-primary font-medium">{r.name}</td>
                        <td className="py-2 pr-4 text-text-muted text-xs">{r.tier || '—'}</td>
                        <td className="py-2 pr-4 text-text-muted text-xs">{formatDate(r.renewal_date)}</td>
                        <td className="py-2 pr-4 font-mono text-xs">{r.health_score ?? '—'}</td>
                        <td className="py-2">
                          <StatusPill status={r.risk_level || 'healthy'} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>
          )}
        </>
      )}
    </div>
  )
}
