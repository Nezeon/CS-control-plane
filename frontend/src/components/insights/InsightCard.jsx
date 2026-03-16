import { useState, useCallback } from 'react'
import { m, AnimatePresence } from 'framer-motion'
import { ChevronDown, Copy, Check, AlertTriangle, ExternalLink } from 'lucide-react'
import { formatDate, getInitials } from '../../utils/formatters'

const sentimentColors = {
  positive: '#00E5A0',
  neutral: '#5C5C72',
  negative: '#FF5C5C',
}

function ActionItemCheckbox({ item, onToggle }) {
  const isOverdue = item.status === 'overdue' || (item.status === 'pending' && item.deadline && new Date(item.deadline) < new Date())
  const isCompleted = item.status === 'completed'

  return (
    <label className="flex items-start gap-2 py-1 cursor-pointer group">
      <input
        type="checkbox"
        checked={isCompleted}
        onChange={() => onToggle?.(item.id, isCompleted ? 'pending' : 'completed')}
        className="mt-0.5 accent-accent"
      />
      <span className={`text-xs font-mono flex-1 ${isCompleted ? 'text-text-ghost line-through' : 'text-text-secondary'}`}>
        {item.description || item.text || item.title}
      </span>
      {isOverdue && !isCompleted && (
        <span className="shrink-0 px-1.5 py-0.5 rounded text-[9px] font-semibold bg-status-danger/15 text-status-danger">
          OVERDUE
        </span>
      )}
    </label>
  )
}

export default function InsightCard({ insight, isExpanded, onToggleExpand, onToggleAction }) {
  const [copied, setCopied] = useState(false)

  const sentiment = insight.sentiment || insight.overall_sentiment || 'neutral'
  const sentimentScore = insight.sentiment_score ?? insight.avg_sentiment_score ?? 0
  const actionItems = insight.action_items || []
  const decisions = insight.decisions || []
  const risks = insight.risks || []
  const summary = insight.summary || insight.recap || ''
  const dotColor = sentimentColors[sentiment] || sentimentColors.neutral

  const handleCopyRecap = useCallback(() => {
    navigator.clipboard.writeText(summary).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }, [summary])

  return (
    <div className="card overflow-hidden" data-testid="insight-card">
      {/* Collapsed header */}
      <button
        className="w-full flex items-center gap-3 p-3 hover:bg-bg-active/50 transition-colors text-left"
        onClick={() => onToggleExpand?.(isExpanded ? null : insight.id)}
      >
        <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: dotColor }} />

        <span className="text-xs text-text-primary font-semibold truncate flex-1">
          {insight.customer_name || insight.title || 'Call Insight'}
        </span>

        <span className="text-[10px] font-mono text-text-ghost shrink-0">
          {formatDate(insight.call_date || insight.created_at)}
        </span>

        <span className="text-xs font-mono font-semibold tabular-nums shrink-0" style={{ color: dotColor }}>
          {sentimentScore > 0 ? '+' : ''}{sentimentScore.toFixed(2)}
        </span>

        {actionItems.length > 0 && (
          <span className="text-[10px] font-mono text-text-ghost shrink-0 px-1.5 py-0.5 rounded bg-bg-active">
            {actionItems.length} actions
          </span>
        )}

        <ChevronDown
          className={`w-3.5 h-3.5 text-text-ghost shrink-0 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <m.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3 border-t border-border-subtle pt-3">
              {/* Summary */}
              {summary && (
                <p className="text-xs text-text-secondary leading-relaxed">{summary}</p>
              )}

              {/* Action items */}
              {actionItems.length > 0 && (
                <div>
                  <h4 className="font-mono text-[10px] text-text-ghost uppercase tracking-wider mb-1.5">
                    Action Items ({actionItems.length})
                  </h4>
                  <div className="space-y-0.5">
                    {actionItems.map((item, i) => (
                      <ActionItemCheckbox key={item.id || i} item={item} onToggle={onToggleAction} />
                    ))}
                  </div>
                </div>
              )}

              {/* Decisions */}
              {decisions.length > 0 && (
                <div>
                  <h4 className="font-mono text-[10px] text-text-ghost uppercase tracking-wider mb-1.5">Decisions</h4>
                  <ul className="space-y-1">
                    {decisions.map((d, i) => (
                      <li key={typeof d === 'string' ? d : d.description || d.text || i} className="text-xs text-text-secondary flex items-start gap-2">
                        <span className="text-accent mt-0.5">&#9656;</span>
                        {typeof d === 'string' ? d : d.description || d.text}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Risks */}
              {risks.length > 0 && (
                <div>
                  <h4 className="font-mono text-[10px] text-text-ghost uppercase tracking-wider mb-1.5">Risks</h4>
                  <ul className="space-y-1">
                    {risks.map((r, i) => (
                      <li key={typeof r === 'string' ? r : r.description || r.text || i} className="text-xs text-status-danger/80 flex items-start gap-2">
                        <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                        {typeof r === 'string' ? r : r.description || r.text}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Footer */}
              <div className="flex items-center gap-3 pt-2 border-t border-border-subtle">
                <button
                  onClick={handleCopyRecap}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono text-text-ghost hover:text-text-primary hover:bg-bg-active transition-colors"
                >
                  {copied ? <Check className="w-3 h-3 text-status-success" /> : <Copy className="w-3 h-3" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                {insight.transcript_url && (
                  <a
                    href={insight.transcript_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono text-accent/70 hover:text-accent hover:bg-accent/5 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Transcript
                  </a>
                )}
              </div>
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  )
}
