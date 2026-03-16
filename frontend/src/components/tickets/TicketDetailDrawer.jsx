import { useEffect, useRef, useCallback, useState } from 'react'
import { m } from 'framer-motion'
import { X, Target, Search, Link2, Loader2 } from 'lucide-react'
import StatusIndicator from '../shared/StatusIndicator'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { getSeverityColor, formatDate, formatRelativeTime } from '../../utils/formatters'

const EMPTY_ARRAY = []

/* ─── Live SLA countdown ─── */
function SlaCountdown({ deadline }) {
  const [sla, setSla] = useState({ text: '—', color: '#5C5C72' })

  useEffect(() => {
    if (!deadline) return
    function update() {
      const diff = new Date(deadline).getTime() - Date.now()
      if (diff <= 0) { setSla({ text: 'SLA BREACHED', color: '#FF5C5C' }); return }
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      if (h > 4) { setSla({ text: `${h}h ${m}m`, color: '#5C5C72' }) }
      else if (h > 1) { setSla({ text: `${h}h ${m}m`, color: '#FFB547' }) }
      else { setSla({ text: `${m}m ${s}s`, color: '#FF5C5C' }) }
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [deadline])

  return (
    <div className="flex items-center gap-2">
      <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: sla.color }} />
      <span className="font-mono text-sm font-bold tabular-nums" style={{ color: sla.color }}>{sla.text}</span>
    </div>
  )
}

/* ─── Confidence bar ─── */
function ConfidenceBar({ value, label }) {
  const pct = Math.round((value || 0) * 100)
  const color = pct > 80 ? '#00E5A0' : pct > 50 ? '#FFB547' : '#FF5C5C'
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono text-[10px] text-text-ghost uppercase">{label}</span>
        <span className="font-mono text-xs font-semibold" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-bg-active overflow-hidden">
        <m.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}

export default function TicketDetailDrawer({
  ticket,
  similarTickets = EMPTY_ARRAY,
  isLoading = false,
  similarLoading = false,
  onClose,
  onTriggerTriage,
  onTriggerTroubleshoot,
}) {
  const drawerRef = useRef(null)
  const [triageLoading, setTriageLoading] = useState(false)
  const [troubleshootLoading, setTroubleshootLoading] = useState(false)

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose?.()
  }, [onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  const handleTriage = async () => {
    if (!ticket?.id || triageLoading) return
    setTriageLoading(true)
    try { await onTriggerTriage?.(ticket.id) } finally { setTriageLoading(false) }
  }

  const handleTroubleshoot = async () => {
    if (!ticket?.id || troubleshootLoading) return
    setTroubleshootLoading(true)
    try { await onTriggerTroubleshoot?.(ticket.id) } finally { setTroubleshootLoading(false) }
  }

  const triage = ticket?.triage_result || null
  const diagnostics = ticket?.diagnostics_result || ticket?.troubleshoot_result || null

  return (
    <>
      {/* Backdrop */}
      <m.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Drawer */}
      <m.div
        data-testid="ticket-detail-drawer"
        ref={drawerRef}
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed right-0 top-0 bottom-0 z-50 w-full md:w-[480px] max-w-lg"
      >
        <div className="card-elevated h-full overflow-y-auto scrollbar-thin rounded-l-2xl border-l border-border">
          {isLoading || !ticket ? (
            <div className="p-5 space-y-4">
              <LoadingSkeleton variant="text" count={3} />
              <LoadingSkeleton variant="card" />
            </div>
          ) : (
            <div className="p-5 space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-lg text-accent font-bold">{ticket.jira_key || `#${ticket.id}`}</span>
                    <div
                      className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase"
                      style={{
                        backgroundColor: `${getSeverityColor(ticket.severity)}15`,
                        color: getSeverityColor(ticket.severity),
                        border: `1px solid ${getSeverityColor(ticket.severity)}30`,
                      }}
                    >
                      {ticket.severity}
                    </div>
                    <StatusIndicator status={ticket.status} size="sm" showLabel />
                  </div>
                  <div className="font-mono text-xs text-text-ghost">
                    {ticket.customer_name} · {formatDate(ticket.created_at)}
                  </div>
                </div>
                <button onClick={onClose} className="p-2 rounded-lg hover:bg-bg-active text-text-ghost hover:text-text-primary transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* SLA */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-bg-active border border-border-subtle">
                <span className="font-mono text-[10px] text-text-ghost uppercase tracking-wider">SLA Countdown</span>
                <SlaCountdown deadline={ticket.sla_deadline} />
              </div>

              {/* Description */}
              {(ticket.description || ticket.summary) && (
                <div>
                  <h4 className="font-mono text-[10px] text-text-ghost uppercase tracking-wider mb-1.5">Description</h4>
                  <p className="text-xs text-text-secondary leading-relaxed">{ticket.description || ticket.summary}</p>
                </div>
              )}

              {/* AI Triage */}
              <div className="card p-3">
                <h4 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-accent" /> AI Triage
                </h4>
                {triage ? (
                  <div className="space-y-2">
                    {triage.category && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-text-ghost font-mono">Category</span>
                        <span className="text-text-primary font-semibold">{triage.category}</span>
                      </div>
                    )}
                    {triage.severity_recommendation && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-text-ghost font-mono">Severity Rec</span>
                        <span style={{ color: getSeverityColor(triage.severity_recommendation) }} className="font-semibold">
                          {triage.severity_recommendation}
                        </span>
                      </div>
                    )}
                    {triage.confidence != null && <ConfidenceBar value={triage.confidence} label="Confidence" />}
                    {triage.suggested_action && (
                      <div className="p-2 rounded-lg bg-accent/5 border border-accent/15">
                        <div className="font-mono text-[10px] text-accent/60 uppercase mb-0.5">Suggested Action</div>
                        <p className="text-xs text-text-secondary">{triage.suggested_action}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-text-ghost font-mono text-center py-2">No triage results yet</p>
                )}
              </div>

              {/* AI Diagnostics */}
              <div className="card p-3">
                <h4 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Search className="w-3.5 h-3.5 text-accent" /> AI Diagnostics
                </h4>
                {diagnostics ? (
                  <div className="space-y-2">
                    {diagnostics.root_cause && (
                      <div>
                        <div className="font-mono text-[10px] text-text-ghost uppercase mb-0.5">Root Cause</div>
                        <p className="text-xs text-text-secondary">{diagnostics.root_cause}</p>
                      </div>
                    )}
                    {diagnostics.confidence != null && <ConfidenceBar value={diagnostics.confidence} label="Confidence" />}
                    {diagnostics.next_steps?.length > 0 && (
                      <div>
                        <div className="font-mono text-[10px] text-text-ghost uppercase mb-1">Next Steps</div>
                        <ol className="space-y-1">
                          {diagnostics.next_steps.map((s, i) => (
                            <li key={typeof s === 'string' ? `step-${i}` : s.description || `step-${i}`} className="text-xs text-text-secondary flex items-start gap-2">
                              <span className="text-accent font-semibold shrink-0">{i + 1}.</span>
                              {typeof s === 'string' ? s : s.description}
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-text-ghost font-mono text-center py-2">No diagnostics yet</p>
                )}
              </div>

              {/* Similar Tickets */}
              <div className="card p-3">
                <h4 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Link2 className="w-3.5 h-3.5 text-accent" /> Similar Tickets
                </h4>
                {similarLoading ? (
                  <LoadingSkeleton variant="text" count={2} />
                ) : similarTickets.length > 0 ? (
                  <div className="space-y-1.5">
                    {similarTickets.map((st, i) => (
                      <div key={st.id || i} className="flex items-center gap-2 p-2 rounded-lg bg-bg-active/50 border border-border-subtle">
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold shrink-0"
                          style={{ backgroundColor: `${getSeverityColor(st.severity)}15`, color: getSeverityColor(st.severity) }}
                        >
                          {st.similarity != null ? `${Math.round(st.similarity * 100)}%` : '—'}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs text-text-primary font-semibold truncate">{st.jira_key || st.id}</div>
                          <div className="text-[10px] text-text-ghost font-mono truncate">{st.customer_name} · {st.resolution || st.status}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-ghost font-mono text-center py-2">No similar tickets found</p>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3 pt-1">
                <button
                  onClick={handleTriage}
                  disabled={triageLoading}
                  className="flex-1 py-2 rounded-lg font-mono text-xs font-semibold uppercase tracking-wider bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {triageLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Target className="w-3 h-3" />}
                  {triageLoading ? 'Running...' : 'Triage'}
                </button>
                <button
                  onClick={handleTroubleshoot}
                  disabled={troubleshootLoading}
                  className="flex-1 py-2 rounded-lg font-mono text-xs font-semibold uppercase tracking-wider bg-status-info/10 text-status-info border border-status-info/20 hover:bg-status-info/20 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {troubleshootLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
                  {troubleshootLoading ? 'Running...' : 'Troubleshoot'}
                </button>
              </div>
            </div>
          )}
        </div>
      </m.div>
    </>
  )
}
