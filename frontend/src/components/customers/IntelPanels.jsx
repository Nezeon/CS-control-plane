import { Ticket, Phone, Search, ExternalLink } from 'lucide-react'
import GlassCard from '../shared/GlassCard'
import SeverityMarker from '../shared/SeverityMarker'
import StatusPill from '../shared/StatusPill'
import { formatRelativeTime, formatDate } from '../../utils/formatters'

const EMPTY_ARRAY = []

/**
 * TicketsPanel -- Displays customer tickets as a table-like list
 */
export function TicketsPanel({ tickets = EMPTY_ARRAY }) {
  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Ticket className="w-4 h-4 text-text-ghost" />
          <h3 className="text-sm font-medium text-text-primary">Open Tickets</h3>
        </div>
        <span className="text-xxs font-mono text-text-ghost tabular-nums">{tickets.length}</span>
      </div>

      {tickets.length > 0 ? (
        <div className="space-y-1 max-h-[400px] overflow-y-auto">
          {tickets.map((t) => (
            <div
              key={t.id}
              className="flex items-center gap-2.5 py-2.5 px-3 rounded-lg hover:bg-bg-hover transition-colors"
            >
              <SeverityMarker severity={t.severity} variant="badge" />
              <span className="text-xxs font-mono text-accent flex-shrink-0">{t.jira_key}</span>
              <span className="text-xs text-text-secondary truncate flex-1">{t.summary}</span>
              <StatusPill status={t.status || 'open'} size="sm" />
              <span className="text-xxs text-text-ghost font-mono flex-shrink-0">
                {formatRelativeTime(t.created_at)}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-text-ghost py-12 text-center">No open tickets</p>
      )}
    </GlassCard>
  )
}

/**
 * CallsPanel -- Displays customer call insights
 */
export function CallsPanel({ insights = EMPTY_ARRAY }) {
  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Phone className="w-4 h-4 text-text-ghost" />
          <h3 className="text-sm font-medium text-text-primary">Recent Calls</h3>
        </div>
        <span className="text-xxs font-mono text-text-ghost tabular-nums">{insights.length}</span>
      </div>

      {insights.length > 0 ? (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {insights.map((ins) => {
            const sentiment = ins.sentiment_score ?? 0
            const sentColor = sentiment > 0.2 ? 'text-status-success' : sentiment < -0.2 ? 'text-status-danger' : 'text-text-muted'

            return (
              <div
                key={ins.id}
                className="py-3 px-3 rounded-lg hover:bg-bg-hover transition-colors"
              >
                <div className="flex items-start gap-2">
                  <span className="text-xs text-text-secondary flex-1">
                    {ins.summary || 'Call insight'}
                  </span>
                  <span className={`text-xxs font-mono flex-shrink-0 ${sentColor}`}>
                    {sentiment > 0 ? '+' : ''}{sentiment.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1.5">
                  <span className="text-xxs text-text-ghost">
                    {ins.call_date
                      ? new Date(ins.call_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                      : '--'}
                  </span>
                  {ins.action_items?.length > 0 && (
                    <span className="text-xxs text-accent font-mono">{ins.action_items.length} actions</span>
                  )}
                  {ins.duration && (
                    <span className="text-xxs text-text-ghost font-mono">{ins.duration}min</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <p className="text-xs text-text-ghost py-12 text-center">No recent calls</p>
      )}
    </GlassCard>
  )
}

/**
 * SimilarIssuesPanel -- RAG-powered similar issues from other customers
 */
export function SimilarIssuesPanel({ similarIssues = EMPTY_ARRAY }) {
  return (
    <GlassCard>
      <div className="flex items-center gap-2 mb-4">
        <Search className="w-4 h-4 text-text-ghost" />
        <h3 className="text-sm font-medium text-text-primary">Similar Issues from Other Customers</h3>
      </div>

      {similarIssues.length > 0 ? (
        <div className="space-y-3">
          {similarIssues.map((issue, i) => (
            <div
              key={issue.id || i}
              className="py-3 px-4 rounded-lg bg-bg-subtle border border-border-subtle"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-text-secondary">{issue.summary || issue.text || issue.content}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    {issue.customer_name && (
                      <span className="text-xxs text-text-ghost">{issue.customer_name}</span>
                    )}
                    {issue.status && (
                      <StatusPill status={issue.status} size="sm" />
                    )}
                    {issue.severity && (
                      <SeverityMarker severity={issue.severity} variant="badge" />
                    )}
                  </div>
                </div>
                {(issue.similarity != null || issue.similarity_score != null) && (
                  <span className="text-xxs font-mono text-accent flex-shrink-0">
                    {Math.round((issue.similarity ?? issue.similarity_score) * 100)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-text-ghost py-12 text-center">No similar issues found</p>
      )}
    </GlassCard>
  )
}

/**
 * Legacy default export -- renders all panels together (for backwards compatibility)
 */
export default function IntelPanels({ tickets = EMPTY_ARRAY, insights = EMPTY_ARRAY, similarIssues = EMPTY_ARRAY }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TicketsPanel tickets={tickets} />
        <CallsPanel insights={insights} />
      </div>
      {similarIssues?.length > 0 && (
        <SimilarIssuesPanel similarIssues={similarIssues} />
      )}
    </div>
  )
}
