import { Ticket, Phone, Search } from 'lucide-react'
import SeverityMarker from '../shared/SeverityMarker'
import { formatRelativeTime } from '../../utils/formatters'

export default function IntelPanels({ tickets = [], insights = [], similarIssues = [] }) {
  return (
    <div className="space-y-4">
      {/* Tickets + Calls — 2 col */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Open Tickets */}
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Ticket className="w-3.5 h-3.5 text-text-ghost" />
              <h3 className="text-sm font-medium text-text-primary">Open Tickets</h3>
            </div>
            <span className="text-xxs font-mono text-text-ghost tabular-nums">{tickets.length}</span>
          </div>
          {tickets.length > 0 ? (
            <div className="space-y-1 max-h-[240px] overflow-y-auto">
              {tickets.slice(0, 8).map((t) => (
                <div key={t.id} className="flex items-center gap-2.5 py-2 px-2 rounded-md hover:bg-bg-active/40 transition-colors">
                  <SeverityMarker severity={t.severity} variant="badge" />
                  <span className="text-xxs font-mono text-accent">{t.jira_key}</span>
                  <span className="text-xs text-text-secondary truncate flex-1">{t.summary}</span>
                  <span className="text-xxs text-text-ghost font-mono shrink-0">{formatRelativeTime(t.created_at)}</span>
                </div>
              ))}
              {tickets.length > 8 && (
                <p className="text-xxs text-text-ghost py-1 pl-2">+{tickets.length - 8} more</p>
              )}
            </div>
          ) : (
            <p className="text-xs text-text-ghost py-6 text-center">No open tickets</p>
          )}
        </div>

        {/* Recent Calls */}
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Phone className="w-3.5 h-3.5 text-text-ghost" />
              <h3 className="text-sm font-medium text-text-primary">Recent Calls</h3>
            </div>
            <span className="text-xxs font-mono text-text-ghost tabular-nums">{insights.length}</span>
          </div>
          {insights.length > 0 ? (
            <div className="space-y-1 max-h-[240px] overflow-y-auto">
              {insights.slice(0, 6).map((ins) => {
                const sentiment = ins.sentiment_score ?? 0
                const sentColor = sentiment > 0.2 ? 'text-status-success' : sentiment < -0.2 ? 'text-status-danger' : 'text-text-muted'

                return (
                  <div key={ins.id} className="py-2 px-2 rounded-md hover:bg-bg-active/40 transition-colors">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-text-secondary truncate flex-1">
                        {ins.summary?.slice(0, 60) || 'Call insight'}
                        {ins.summary?.length > 60 ? '...' : ''}
                      </span>
                      <span className={`text-xxs font-mono shrink-0 ${sentColor}`}>
                        {sentiment > 0 ? '+' : ''}{sentiment.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xxs text-text-ghost">
                        {ins.call_date ? new Date(ins.call_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}
                      </span>
                      {ins.action_items?.length > 0 && (
                        <span className="text-xxs text-text-ghost">{ins.action_items.length} actions</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-xs text-text-ghost py-6 text-center">No recent calls</p>
          )}
        </div>
      </div>

      {/* Similar Issues (RAG) */}
      {similarIssues?.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Search className="w-3.5 h-3.5 text-text-ghost" />
            <h3 className="text-sm font-medium text-text-primary">Similar Issues from Other Customers</h3>
          </div>
          <div className="space-y-2">
            {similarIssues.slice(0, 3).map((issue, i) => (
              <div key={issue.id || i} className="py-2 px-3 rounded-md bg-bg-active/30 border border-border-subtle">
                <p className="text-xs text-text-secondary">{issue.summary || issue.text || issue.content}</p>
                {(issue.customer_name || issue.similarity) && (
                  <p className="text-xxs text-text-ghost mt-1">
                    {issue.customer_name}
                    {issue.similarity != null && ` · ${Math.round(issue.similarity * 100)}% similar`}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
