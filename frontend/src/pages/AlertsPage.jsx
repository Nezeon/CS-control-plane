import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Eye, AlertTriangle } from 'lucide-react'
import useAlertStore from '../stores/alertStore'
import GlassCard from '../components/shared/GlassCard'
import StatusPill from '../components/shared/StatusPill'
import PillFilter from '../components/shared/PillFilter'
import GradientButton from '../components/shared/GradientButton'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatRelativeTime, getSeverityColor } from '../utils/formatters'
import api from '../services/api'

const STATUS_OPTIONS = [
  { value: '', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'resolved', label: 'Resolved' },
]

const SEVERITY_OPTIONS = [
  { value: '', label: 'All Severity' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

export default function AlertsPage() {
  const { alerts, isLoading, fetchAll, acknowledgeAlert, resolveAlert, dismissAlert } = useAlertStore()
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')

  useEffect(() => { fetchAll() }, [fetchAll])

  const filtered = alerts.filter((a) => {
    if (statusFilter && a.status !== statusFilter) return false
    if (severityFilter && a.severity !== severityFilter) return false
    return true
  })

  const handleAcknowledge = async (id) => {
    acknowledgeAlert(id)
    try { await api.put(`/alerts/${id}/status`, { status: 'acknowledged' }) } catch { /* optimistic */ }
  }

  const handleResolve = async (id) => {
    resolveAlert(id)
    try { await api.put(`/alerts/${id}/status`, { status: 'resolved' }) } catch { /* optimistic */ }
  }

  const handleDismiss = (id) => {
    dismissAlert(id)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-bold text-text-primary">Alerts</h1>
        <span className="text-sm text-text-muted">
          {filtered.length} alert{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="flex flex-wrap gap-4">
        <PillFilter options={STATUS_OPTIONS} value={statusFilter} onChange={setStatusFilter} />
        <PillFilter options={SEVERITY_OPTIONS} value={severityFilter} onChange={setSeverityFilter} />
      </div>

      {isLoading && alerts.length === 0 ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <LoadingSkeleton key={i} variant="card" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-12 text-center">
          <AlertTriangle size={32} className="mx-auto text-text-ghost mb-3" />
          <p className="text-sm text-text-muted">No alerts match your filters</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => (
            <GlassCard key={alert.id} level="near" className="relative overflow-hidden">
              {/* Severity color bar */}
              <div
                className="absolute top-0 left-0 w-1 h-full rounded-l"
                style={{ backgroundColor: getSeverityColor(alert.severity) }}
              />

              <div className="pl-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <StatusPill status={alert.status || 'open'} />
                      <span
                        className="text-xxs font-mono font-medium"
                        style={{ color: getSeverityColor(alert.severity) }}
                      >
                        {(alert.severity || 'medium').toUpperCase()}
                      </span>
                      {alert.slack_notified && (
                        <span className="text-xxs text-text-ghost">Slack sent</span>
                      )}
                    </div>
                    <h3 className="text-sm font-semibold text-text-primary">{alert.title}</h3>
                    {alert.customer_name && (
                      <p className="text-xs text-text-muted mt-0.5">{alert.customer_name}</p>
                    )}
                    {alert.description && (
                      <p className="text-xs text-text-secondary mt-1">{alert.description}</p>
                    )}
                    {alert.suggested_action && (
                      <p className="text-xs text-accent/80 mt-1 italic">{alert.suggested_action}</p>
                    )}
                    <span className="text-xxs text-text-ghost font-mono mt-2 block">
                      {formatRelativeTime(alert.created_at)}
                    </span>
                  </div>

                  {/* Action buttons */}
                  <div className="flex flex-col gap-1.5 flex-shrink-0">
                    {alert.status === 'open' && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="flex items-center gap-1 text-xxs px-2 py-1 rounded bg-status-warning/10 text-status-warning hover:bg-status-warning/20 transition-colors"
                      >
                        <Eye size={12} /> Ack
                      </button>
                    )}
                    {(alert.status === 'open' || alert.status === 'acknowledged') && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="flex items-center gap-1 text-xxs px-2 py-1 rounded bg-teal/10 text-teal hover:bg-teal/20 transition-colors"
                      >
                        <CheckCircle size={12} /> Resolve
                      </button>
                    )}
                    <button
                      onClick={() => handleDismiss(alert.id)}
                      className="flex items-center gap-1 text-xxs px-2 py-1 rounded bg-status-danger/10 text-status-danger hover:bg-status-danger/20 transition-colors"
                    >
                      <XCircle size={12} /> Dismiss
                    </button>
                  </div>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  )
}
