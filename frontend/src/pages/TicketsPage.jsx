import { useEffect, useCallback, useRef, useMemo } from 'react'
import { AnimatePresence } from 'framer-motion'
import { Search, List, Sparkles, Ticket, AlertOctagon, Clock, CircleDot } from 'lucide-react'
import useTicketStore from '../stores/ticketStore'
import WarroomTable from '../components/tickets/WarroomTable'
import ConstellationWrapper from '../components/tickets/ConstellationWrapper'
import TicketDetailDrawer from '../components/tickets/TicketDetailDrawer'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'

const statusOptions = [
  { value: '', label: 'All Status' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'waiting', label: 'Waiting' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
]

const severityOptions = [
  { value: '', label: 'All Severity' },
  { value: 'P1', label: 'P1 - Critical' },
  { value: 'P2', label: 'P2 - High' },
  { value: 'P3', label: 'P3 - Medium' },
  { value: 'P4', label: 'P4 - Low' },
]

function KpiCard({ icon: Icon, value, label, color, onClick, active }) {
  return (
    <button
      onClick={onClick}
      className={`card p-3 flex items-center gap-3 transition-all hover:border-border-strong ${active ? 'border-accent/40 bg-accent/5' : ''}`}
    >
      <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}12` }}>
        <Icon className="w-4 h-4" style={{ color }} />
      </div>
      <div className="text-left">
        <div className="text-lg font-bold text-text-primary tabular-nums leading-none">{value}</div>
        <div className="text-[10px] font-mono text-text-ghost uppercase mt-0.5">{label}</div>
      </div>
    </button>
  )
}

export default function TicketsPage() {
  const {
    tickets, total, isLoading, search, status, severity,
    sort_by, sort_order, viewMode, drawerOpen, selectedTicket,
    similarTickets, detailLoading, similarLoading,
    setSearch, setStatus, setSeverity, setSortBy, setSortOrder,
    setViewMode, fetchTickets, openDrawer, closeDrawer,
    triggerTriage, triggerTroubleshoot,
  } = useTicketStore()

  const searchTimer = useRef(null)

  useEffect(() => { fetchTickets() }, [fetchTickets])

  const handleSearchChange = useCallback((e) => {
    const val = e.target.value
    setSearch(val)
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => fetchTickets(), 300)
  }, [setSearch, fetchTickets])

  const handleStatusChange = useCallback((e) => {
    setStatus(e.target.value)
    setTimeout(() => fetchTickets(), 0)
  }, [setStatus, fetchTickets])

  const handleSeverityChange = useCallback((e) => {
    setSeverity(e.target.value)
    setTimeout(() => fetchTickets(), 0)
  }, [setSeverity, fetchTickets])

  const handleSort = useCallback((field) => {
    if (sort_by === field) {
      setSortOrder(sort_order === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
    setTimeout(() => fetchTickets(), 0)
  }, [sort_by, sort_order, setSortBy, setSortOrder, fetchTickets])

  const stats = useMemo(() => {
    const p1 = tickets.filter((t) => t.severity === 'P1' || t.severity === 'critical').length
    const openCount = tickets.filter((t) => t.status === 'open' || t.status === 'in_progress').length
    const breaching = tickets.filter((t) => t.sla_deadline && new Date(t.sla_deadline) < new Date()).length
    return { total: tickets.length, p1, openCount, breaching }
  }, [tickets])

  return (
    <div className="h-full flex flex-col overflow-hidden" data-testid="tickets-page">
      {/* Header */}
      <div className="pb-4 shrink-0">
        <h1 className="text-xl font-semibold text-text-primary mb-4">Tickets</h1>

        {/* KPI row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          <KpiCard icon={Ticket} value={stats.total} label="Total" color="#6366F1" />
          <KpiCard icon={AlertOctagon} value={stats.p1} label="P1 Critical" color="#EF4444" />
          <KpiCard icon={CircleDot} value={stats.openCount} label="Open" color="#EAB308" />
          <KpiCard
            icon={Clock}
            value={stats.breaching}
            label="SLA Breaching"
            color={stats.breaching > 0 ? '#EF4444' : '#71717A'}
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-ghost" />
            <input
              type="text"
              placeholder="Search tickets..."
              value={search}
              onChange={handleSearchChange}
              data-testid="tickets-search"
              className="pl-9 pr-4 py-2 rounded-lg bg-bg-subtle border border-border text-sm text-text-primary placeholder:text-text-ghost focus:border-border-strong focus:outline-none w-52"
            />
          </div>

          <select
            value={status}
            onChange={handleStatusChange}
            data-testid="tickets-status-filter"
            className="px-3 py-2 rounded-lg bg-bg-subtle border border-border text-sm text-text-muted focus:outline-none cursor-pointer"
          >
            {statusOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          <select
            value={severity}
            onChange={handleSeverityChange}
            data-testid="tickets-severity-filter"
            className="px-3 py-2 rounded-lg bg-bg-subtle border border-border text-sm text-text-muted focus:outline-none cursor-pointer"
          >
            {severityOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          <div className="flex-1" />

          <div className="flex items-center gap-1">
            <button
              onClick={() => setViewMode('table')}
              data-testid="tickets-view-table"
              className={`p-2 rounded-lg transition-colors ${viewMode === 'table' ? 'text-accent bg-accent-subtle' : 'text-text-ghost hover:text-text-muted'}`}
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('constellation')}
              data-testid="tickets-view-constellation"
              className={`p-2 rounded-lg transition-colors ${viewMode === 'constellation' ? 'text-accent bg-accent-subtle' : 'text-text-ghost hover:text-text-muted'}`}
            >
              <Sparkles className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pb-6">
        {isLoading ? (
          <LoadingSkeleton variant="card" count={3} />
        ) : viewMode === 'table' ? (
          <WarroomTable tickets={tickets} sortBy={sort_by} sortOrder={sort_order} onSort={handleSort} onTicketClick={openDrawer} />
        ) : (
          <ConstellationWrapper tickets={tickets} onTicketClick={openDrawer} />
        )}
      </div>

      {/* Detail Drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <TicketDetailDrawer
            ticket={selectedTicket}
            similarTickets={similarTickets}
            isLoading={detailLoading}
            similarLoading={similarLoading}
            onClose={closeDrawer}
            onTriggerTriage={triggerTriage}
            onTriggerTroubleshoot={triggerTroubleshoot}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
