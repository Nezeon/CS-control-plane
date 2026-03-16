import { useEffect, useCallback } from 'react'
import { Search, X } from 'lucide-react'
import useTicketStore from '../stores/ticketStore'
import PillFilter from '../components/shared/PillFilter'
import StatusPill from '../components/shared/StatusPill'
import GlassCard from '../components/shared/GlassCard'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatRelativeTime, getSeverityColor } from '../utils/formatters'

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
]

const SEVERITY_OPTIONS = [
  { value: '', label: 'All Severity' },
  { value: 'P1', label: 'P1' },
  { value: 'P2', label: 'P2' },
  { value: 'P3', label: 'P3' },
  { value: 'P4', label: 'P4' },
]

export default function TicketsPage() {
  const {
    tickets, isLoading, search, status, severity,
    setSearch, setStatus, setSeverity, fetchTickets,
    drawerOpen, selectedTicket, detailLoading, openDrawer, closeDrawer,
  } = useTicketStore()

  useEffect(() => { fetchTickets() }, [fetchTickets])

  const handleSearch = useCallback((e) => setSearch(e.target.value), [setSearch])

  useEffect(() => {
    const timeout = setTimeout(() => fetchTickets(), 300)
    return () => clearTimeout(timeout)
  }, [search, status, severity, fetchTickets])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-display font-bold text-text-primary">Tickets</h1>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-ghost" />
          <input
            type="text"
            value={search}
            onChange={handleSearch}
            placeholder="Search tickets..."
            className="w-full pl-9 pr-3 py-2 text-sm bg-bg-subtle border border-border rounded-lg text-text-primary placeholder:text-text-ghost focus:outline-none focus:border-accent"
          />
        </div>
        <PillFilter options={STATUS_OPTIONS} value={status} onChange={setStatus} />
        <PillFilter options={SEVERITY_OPTIONS} value={severity} onChange={setSeverity} />
      </div>

      {/* Table */}
      {isLoading && tickets.length === 0 ? (
        <LoadingSkeleton variant="card" count={3} />
      ) : tickets.length === 0 ? (
        <p className="text-sm text-text-muted py-8 text-center">No tickets found</p>
      ) : (
        <div className="glass-near rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-muted font-mono text-xxs uppercase tracking-wider border-b border-border-subtle">
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Summary</th>
                  <th className="px-4 py-3">Customer</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => openDrawer(t.id)}
                    className="border-b border-border-subtle/50 hover:bg-bg-hover/50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-accent">{t.jira_key || t.id?.slice(0, 8)}</td>
                    <td className="px-4 py-3 text-text-primary max-w-xs truncate">{t.summary || t.title}</td>
                    <td className="px-4 py-3 text-text-muted">{t.customer_name || '—'}</td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xxs font-mono font-medium px-2 py-0.5 rounded-full"
                        style={{
                          color: getSeverityColor(t.severity || t.priority),
                          backgroundColor: `${getSeverityColor(t.severity || t.priority)}15`,
                        }}
                      >
                        {t.severity || t.priority || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill status={t.status || 'open'} />
                    </td>
                    <td className="px-4 py-3 text-text-ghost text-xs font-mono">
                      {formatRelativeTime(t.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Ticket Detail Drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/40" onClick={closeDrawer} />
          <div className="relative w-full max-w-lg bg-bg-subtle border-l border-border-subtle overflow-y-auto animate-slide-in-right">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-display font-bold text-text-primary">Ticket Details</h2>
                <button onClick={closeDrawer} className="p-1 rounded text-text-ghost hover:text-text-primary">
                  <X size={18} />
                </button>
              </div>

              {detailLoading ? (
                <LoadingSkeleton variant="text" count={6} />
              ) : selectedTicket ? (
                <div className="space-y-4">
                  <div>
                    <span className="text-xxs font-mono text-text-ghost uppercase">ID</span>
                    <p className="text-sm text-accent font-mono">{selectedTicket.jira_key || selectedTicket.id}</p>
                  </div>
                  <div>
                    <span className="text-xxs font-mono text-text-ghost uppercase">Summary</span>
                    <p className="text-sm text-text-primary">{selectedTicket.summary || selectedTicket.title}</p>
                  </div>
                  <div className="flex gap-4">
                    <div>
                      <span className="text-xxs font-mono text-text-ghost uppercase">Severity</span>
                      <p className="text-sm" style={{ color: getSeverityColor(selectedTicket.severity) }}>
                        {selectedTicket.severity || '—'}
                      </p>
                    </div>
                    <div>
                      <span className="text-xxs font-mono text-text-ghost uppercase">Status</span>
                      <StatusPill status={selectedTicket.status || 'open'} size="md" />
                    </div>
                  </div>
                  {selectedTicket.description && (
                    <div>
                      <span className="text-xxs font-mono text-text-ghost uppercase">Description</span>
                      <p className="text-sm text-text-secondary mt-1 whitespace-pre-wrap">
                        {selectedTicket.description}
                      </p>
                    </div>
                  )}
                  {selectedTicket.customer_name && (
                    <div>
                      <span className="text-xxs font-mono text-text-ghost uppercase">Customer</span>
                      <p className="text-sm text-text-primary">{selectedTicket.customer_name}</p>
                    </div>
                  )}
                  {selectedTicket.triage_result && (
                    <GlassCard level="mid" className="mt-4">
                      <h3 className="text-xs font-semibold text-accent mb-2">AI Triage Result</h3>
                      <p className="text-xs text-text-secondary whitespace-pre-wrap">
                        {typeof selectedTicket.triage_result === 'string'
                          ? selectedTicket.triage_result
                          : JSON.stringify(selectedTicket.triage_result, null, 2)}
                      </p>
                    </GlassCard>
                  )}
                </div>
              ) : (
                <p className="text-sm text-text-muted">Ticket not found</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
