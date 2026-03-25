import { X, Users, AlertTriangle, CheckCircle, FileText } from 'lucide-react'
import GlassCard from './GlassCard'
import StatusPill from './StatusPill'
import { formatDate, formatDateTime } from '../../utils/formatters'

export default function CallDetailDrawer({ insight, open, onClose }) {
  if (!open || !insight) return null

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-full max-w-[480px] z-50 glass-near border-l border-border-subtle overflow-y-auto animate-slide-in-right">
        {/* Header */}
        <div className="sticky top-0 z-10 glass-near border-b border-border-subtle px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <StatusPill status={insight.sentiment || 'neutral'} />
            {insight.sentiment_score != null && (
              <span className="text-xs text-text-ghost font-mono">
                ({(insight.sentiment_score * 100).toFixed(0)}%)
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-bg-hover/50 text-text-muted">
            <X size={18} />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Date & Participants */}
          <Section title="Call Details">
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <span className="text-text-ghost">Date</span>
              <span className="text-text-secondary">{formatDateTime(insight.call_date)}</span>
              {insight.processed_at && (
                <>
                  <span className="text-text-ghost">Processed</span>
                  <span className="text-text-secondary">{formatDate(insight.processed_at)}</span>
                </>
              )}
            </div>
          </Section>

          {/* Participants */}
          {insight.participants?.length > 0 && (
            <Section title="Attendees" icon={<Users size={12} />}>
              <div className="flex flex-wrap gap-1.5">
                {insight.participants.slice(0, 8).map((p, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded bg-bg-hover/50 text-text-secondary">
                    {typeof p === 'string' ? p : p.name || JSON.stringify(p)}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {/* Summary */}
          {insight.summary && (
            <Section title="Summary">
              <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
                {insight.summary}
              </p>
            </Section>
          )}

          {/* Key Topics */}
          {insight.key_topics?.length > 0 && (
            <Section title="Key Topics">
              <div className="flex flex-wrap gap-1.5">
                {insight.key_topics.slice(0, 8).map((t, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded bg-accent/10 text-accent">
                    {t}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {/* Action Items */}
          {insight.action_items?.length > 0 && (
            <Section title="Action Items" icon={<CheckCircle size={12} />}>
              <div className="space-y-1.5">
                {insight.action_items.slice(0, 5).map((a, i) => {
                  const task = typeof a === 'string' ? a : a.task || JSON.stringify(a)
                  const owner = typeof a === 'object' ? a.owner : null
                  const deadline = typeof a === 'object' ? a.deadline : null
                  return (
                    <div key={i} className="text-xs text-text-secondary">
                      <span>
                        {owner && <span className="text-accent font-medium">[{owner}] </span>}
                        {task}
                      </span>
                      {deadline && (
                        <span className="text-text-ghost ml-1">— {deadline}</span>
                      )}
                    </div>
                  )
                })}
              </div>
            </Section>
          )}

          {/* Risks */}
          {insight.risks?.length > 0 && (
            <Section title="Risk Signals" icon={<AlertTriangle size={12} />}>
              <div className="space-y-1.5">
                {insight.risks.slice(0, 3).map((r, i) => {
                  const text = typeof r === 'string' ? r : r.description || JSON.stringify(r)
                  return (
                    <div key={i} className="text-xs text-status-danger flex items-start gap-1.5">
                      <span className="shrink-0 mt-0.5">&#x1F534;</span>
                      <span>{text}</span>
                    </div>
                  )
                })}
              </div>
            </Section>
          )}

          {/* Decisions */}
          {insight.decisions?.length > 0 && (
            <Section title="Decisions">
              <div className="space-y-1.5">
                {insight.decisions.map((d, i) => (
                  <div key={i} className="text-xs text-text-secondary">
                    {typeof d === 'string' ? d : d.description || JSON.stringify(d)}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Customer Recap Draft */}
          {insight.customer_recap_draft && (
            <Section title="Customer Recap Draft" icon={<FileText size={12} />}>
              <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
                {insight.customer_recap_draft}
              </p>
            </Section>
          )}
        </div>
      </div>
    </>
  )
}

function Section({ title, icon, children }) {
  return (
    <GlassCard level="mid" className="!p-3">
      <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center gap-1.5">
        {icon}
        {title}
      </h3>
      {children}
    </GlassCard>
  )
}
