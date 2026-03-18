import { useEffect, useState } from 'react'
import { X, ExternalLink } from 'lucide-react'
import { ticketApi } from '../../services/ticketApi'
import GlassCard from './GlassCard'
import StatusPill from './StatusPill'
import LoadingSkeleton from './LoadingSkeleton'
import { formatDate } from '../../utils/formatters'

export default function TicketDetailDrawer({ ticketId, open, onClose }) {
  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!ticketId || !open) return
    setLoading(true)
    ticketApi.get(ticketId)
      .then(({ data }) => setTicket(data))
      .catch(() => setTicket(null))
      .finally(() => setLoading(false))
  }, [ticketId, open])

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-full max-w-[480px] z-50 glass-near border-l border-border-subtle overflow-y-auto animate-slide-in-right">
        {/* Header */}
        <div className="sticky top-0 z-10 glass-near border-b border-border-subtle px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            {ticket?.jira_id && (
              <span className="font-mono text-xs text-accent shrink-0">{ticket.jira_id}</span>
            )}
            {ticket?.severity && <StatusPill status={ticket.severity} />}
            {ticket?.status && <StatusPill status={ticket.status} />}
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-bg-hover/50 text-text-muted">
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <div className="p-5"><LoadingSkeleton lines={8} /></div>
        ) : !ticket ? (
          <div className="p-5 text-text-muted text-sm">Failed to load ticket details.</div>
        ) : (
          <div className="p-5 space-y-5">
            {/* Summary */}
            <div>
              <h2 className="text-base font-semibold text-text-primary leading-snug">{ticket.summary}</h2>
              {ticket.jira_id && (
                <a
                  href={`https://hivepro.atlassian.net/browse/${ticket.jira_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-1 text-xs text-accent hover:underline"
                >
                  Open in Jira <ExternalLink size={12} />
                </a>
              )}
            </div>

            {/* Description */}
            {ticket.description && (
              <Section title="Description">
                <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
                  {ticket.description}
                </p>
              </Section>
            )}

            {/* AI Triage */}
            {ticket.triage_result && (
              <Section title="AI Triage">
                <JsonKV data={ticket.triage_result} />
              </Section>
            )}

            {/* AI Troubleshoot */}
            {ticket.troubleshoot_result && (
              <Section title="AI Troubleshoot">
                <JsonKV data={ticket.troubleshoot_result} />
              </Section>
            )}

            {/* Escalation */}
            {ticket.escalation_summary && (
              <Section title="Escalation">
                <JsonKV data={ticket.escalation_summary} />
              </Section>
            )}

            {/* Meta */}
            <Section title="Details">
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                <MetaItem label="Type" value={ticket.ticket_type} />
                <MetaItem label="Assigned to" value={ticket.assigned_to?.full_name} />
                <MetaItem label="SLA Deadline" value={ticket.sla_deadline ? formatDate(ticket.sla_deadline) : null} />
                <MetaItem label="SLA Remaining" value={ticket.sla_remaining_hours != null ? `${ticket.sla_remaining_hours}h` : null} breach={ticket.sla_breaching} />
                <MetaItem label="Created" value={formatDate(ticket.created_at)} />
                <MetaItem label="Updated" value={formatDate(ticket.updated_at)} />
                {ticket.resolved_at && <MetaItem label="Resolved" value={formatDate(ticket.resolved_at)} />}
              </div>
            </Section>
          </div>
        )}
      </div>
    </>
  )
}

function Section({ title, children }) {
  return (
    <GlassCard level="mid" className="!p-3">
      <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">{title}</h3>
      {children}
    </GlassCard>
  )
}

function MetaItem({ label, value, breach }) {
  if (value == null) return null
  return (
    <>
      <span className="text-text-ghost">{label}</span>
      <span className={breach ? 'text-status-danger font-medium' : 'text-text-secondary'}>{value}</span>
    </>
  )
}

function JsonKV({ data }) {
  if (!data || typeof data !== 'object') return null
  return (
    <div className="space-y-1.5">
      {Object.entries(data).map(([key, val]) => (
        <div key={key}>
          <span className="text-xs text-text-ghost capitalize">{key.replace(/_/g, ' ')}: </span>
          <span className="text-xs text-text-secondary">
            {typeof val === 'string' ? val : JSON.stringify(val)}
          </span>
        </div>
      ))}
    </div>
  )
}
