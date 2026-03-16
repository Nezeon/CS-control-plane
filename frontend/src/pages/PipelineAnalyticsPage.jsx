import { useEffect, useState } from 'react'
import api from '../services/api'
import GlassCard from '../components/shared/GlassCard'
import StatusPill from '../components/shared/StatusPill'
import { formatRelativeTime } from '../utils/formatters'

export default function PipelineAnalyticsPage() {
  const [drafts, setDrafts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/drafts?limit=50').then(({ data }) => {
      setDrafts(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const pending = drafts.filter(d => d.status === 'pending').length
  const approved = drafts.filter(d => d.status === 'approved').length
  const dismissed = drafts.filter(d => d.status === 'dismissed').length

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-display font-bold text-[var(--text-primary)]">Pipeline Analytics</h1>

      {/* Draft Status Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <GlassCard level="near">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Pending</span>
          <p className="text-3xl font-display font-bold text-[var(--status-warning)] mt-1">{pending}</p>
        </GlassCard>
        <GlassCard level="near">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Approved</span>
          <p className="text-3xl font-display font-bold text-[var(--status-success)] mt-1">{approved}</p>
        </GlassCard>
        <GlassCard level="near">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Dismissed</span>
          <p className="text-3xl font-display font-bold text-[var(--text-muted)] mt-1">{dismissed}</p>
        </GlassCard>
      </div>

      {/* Drafts Table */}
      <GlassCard level="near">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Agent Drafts</h2>
        {loading ? (
          <p className="text-sm text-[var(--text-muted)] py-8 text-center">Loading...</p>
        ) : drafts.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)] py-8 text-center">No agent drafts yet. Drafts are created when the AI triage agent processes Jira tickets or call recordings. Trigger a manual Jira sync or wait for incoming webhooks.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--text-muted)] font-mono text-[10px] uppercase tracking-wider border-b border-[var(--border)]">
                  <th className="pb-2 pr-3">Agent</th>
                  <th className="pb-2 pr-3">Type</th>
                  <th className="pb-2 pr-3">Channel</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3">Confidence</th>
                  <th className="pb-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {drafts.map((d) => (
                  <tr key={d.id} className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-hover)]/50 transition-colors">
                    <td className="py-2.5 pr-3 text-[var(--text-primary)] font-medium">{d.agent_id}</td>
                    <td className="py-2.5 pr-3 text-xs text-[var(--text-secondary)]">{d.draft_type}</td>
                    <td className="py-2.5 pr-3 font-mono text-xs text-[var(--text-muted)]">{d.slack_channel || '—'}</td>
                    <td className="py-2.5 pr-3"><StatusPill status={d.status} /></td>
                    <td className="py-2.5 pr-3 font-mono text-xs text-[var(--text-secondary)]">
                      {d.confidence != null ? `${(d.confidence * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td className="py-2.5 text-[10px] text-[var(--text-ghost)] font-mono">{formatRelativeTime(d.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  )
}
