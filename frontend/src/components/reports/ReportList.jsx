import { useState, useCallback, useEffect, useRef, memo } from 'react'
import { AnimatePresence, m } from 'framer-motion'
import { X, Plus, FileText, Calendar, ChevronDown } from 'lucide-react'
import useReportStore from '../../stores/reportStore'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { formatDate, formatRelativeTime } from '../../utils/formatters'

const TYPE_LABELS = {
  weekly: 'Weekly',
  monthly: 'Monthly',
  qbr: 'QBR',
  ad_hoc: 'Ad Hoc',
}

const FILTER_TABS = ['', 'weekly', 'monthly', 'qbr']
const FILTER_LABELS = { '': 'All', weekly: 'Weekly', monthly: 'Monthly', qbr: 'QBR' }

/* ─── Generate Report Modal ─── */
function GenerateReportModal({ onClose }) {
  const generating = useReportStore((s) => s.generating)
  const generateReport = useReportStore((s) => s.generateReport)
  const [type, setType] = useState('weekly')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [error, setError] = useState(null)
  const modalRef = useRef(null)

  useEffect(() => {
    const end = new Date()
    const start = new Date()
    start.setDate(end.getDate() - (type === 'weekly' ? 7 : type === 'monthly' ? 30 : 90))
    setPeriodStart(start.toISOString().split('T')[0])
    setPeriodEnd(end.toISOString().split('T')[0])
  }, [type])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const handleSubmit = useCallback(async () => {
    if (!periodStart || !periodEnd) { setError('Please select dates'); return }
    setError(null)
    try {
      await generateReport(type, periodStart, periodEnd, customerId || null)
    } catch (err) {
      setError(err.message || 'Failed to generate report')
    }
  }, [type, periodStart, periodEnd, customerId, generateReport])

  return (
    <m.div
      className="fixed inset-0 z-50 flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <m.div
        ref={modalRef}
        className="relative bg-bg-elevated rounded-xl border border-border p-5 w-full max-w-[440px] mx-4"
        initial={{ scale: 0.95, y: 16 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 16 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        role="dialog"
        aria-label="Generate report"
        aria-modal="true"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm text-text-primary font-semibold uppercase tracking-wider">Generate Report</h3>
          <button onClick={onClose} className="text-text-ghost hover:text-text-primary transition-colors" aria-label="Close">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Type pills */}
        <div className="flex gap-2 mb-4">
          {['weekly', 'monthly', 'qbr'].map((t) => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={`px-3 py-1.5 rounded-full text-xs font-mono transition-all duration-200 ${
                type === t
                  ? 'bg-accent/20 text-accent border border-accent/30'
                  : 'bg-bg-active text-text-ghost border border-border hover:border-border-strong'
              }`}
            >
              {TYPE_LABELS[t]}
            </button>
          ))}
        </div>

        {/* Date inputs */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-[10px] font-mono text-text-ghost uppercase tracking-wider mb-1">Start</label>
            <input
              type="date"
              value={periodStart}
              onChange={(e) => setPeriodStart(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono text-text-primary bg-bg-subtle focus:border-accent focus:outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block text-[10px] font-mono text-text-ghost uppercase tracking-wider mb-1">End</label>
            <input
              type="date"
              value={periodEnd}
              onChange={(e) => setPeriodEnd(e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono text-text-primary bg-bg-subtle focus:border-accent focus:outline-none transition-colors"
            />
          </div>
        </div>

        {type === 'qbr' && (
          <div className="mb-4">
            <label className="block text-[10px] font-mono text-text-ghost uppercase tracking-wider mb-1">Customer ID (optional)</label>
            <input
              type="text"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              placeholder="e.g. acme-corp"
              className="w-full rounded-lg border border-border px-3 py-2 text-xs font-mono text-text-primary bg-bg-subtle placeholder:text-text-ghost/30 focus:border-accent focus:outline-none transition-colors"
            />
          </div>
        )}

        {error && <div className="text-status-danger text-xs font-mono mb-3">{error}</div>}

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-xs font-mono text-text-ghost hover:text-text-primary bg-bg-active border border-border hover:border-border-strong transition-all">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={generating}
            className="px-5 py-2 rounded-lg text-xs font-mono font-semibold bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating...
              </span>
            ) : 'Generate'}
          </button>
        </div>
      </m.div>
    </m.div>
  )
}

/* ─── Report Row ─── */
function ReportRow({ report }) {
  const [expanded, setExpanded] = useState(false)
  const typeKey = report.type || report.report_type || 'ad_hoc'

  return (
    <div className="border-b border-border-subtle last:border-0">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full text-left px-4 py-2.5 flex items-center gap-3 hover:bg-bg-active/50 transition-colors group"
      >
        <FileText className="w-3.5 h-3.5 text-text-ghost shrink-0" />
        <span className="w-16 text-[10px] font-mono text-text-ghost uppercase">{TYPE_LABELS[typeKey] || typeKey}</span>
        <span className="flex-1 text-xs text-text-primary truncate group-hover:text-accent transition-colors">
          {report.title || report.name || `${TYPE_LABELS[typeKey] || typeKey} Report`}
        </span>
        <span className="hidden sm:flex items-center gap-1 text-[10px] font-mono text-text-ghost">
          <Calendar className="w-3 h-3" />
          {report.period_start && report.period_end
            ? `${formatDate(report.period_start)} — ${formatDate(report.period_end)}`
            : '—'}
        </span>
        <span className="w-16 text-right text-[10px] font-mono text-text-ghost/60">
          {formatRelativeTime(report.created_at || report.generated_at)}
        </span>
        <ChevronDown className={`w-3 h-3 text-text-ghost/40 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {expanded && (
          <m.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pl-12">
              {report.sections?.length > 0 ? (
                report.sections.map((section, i) => (
                  <div key={i} className="mb-2">
                    <div className="text-[10px] font-mono text-accent uppercase tracking-wider mb-0.5">
                      {section.title || `Section ${i + 1}`}
                    </div>
                    <div className="text-xs text-text-muted leading-relaxed line-clamp-3">
                      {section.content || section.body || '—'}
                    </div>
                  </div>
                ))
              ) : report.content ? (
                <div className="text-xs text-text-muted leading-relaxed line-clamp-4">{report.content}</div>
              ) : (
                <div className="text-xs text-text-ghost/40 font-mono">No content preview available</div>
              )}
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ─── Main Component ─── */
export default memo(function ReportList({ reports = [], isLoading }) {
  const generateModalOpen = useReportStore((s) => s.generateModalOpen)
  const openGenerateModal = useReportStore((s) => s.openGenerateModal)
  const closeGenerateModal = useReportStore((s) => s.closeGenerateModal)
  const reportTypeFilter = useReportStore((s) => s.reportTypeFilter)
  const setReportTypeFilter = useReportStore((s) => s.setReportTypeFilter)

  const filteredReports = reports.filter((r) => {
    if (!reportTypeFilter) return true
    return (r.type || r.report_type || '') === reportTypeFilter
  })

  if (isLoading) {
    return <div className="card p-4"><LoadingSkeleton variant="rect" width="100%" height="160px" /></div>
  }

  return (
    <div className="card p-0 overflow-hidden" data-testid="report-list">
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <h3 className="text-xs text-text-primary font-semibold uppercase tracking-wider">Reports</h3>
        <button
          onClick={openGenerateModal}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-mono font-semibold bg-accent text-white hover:bg-accent-hover transition-all"
        >
          <Plus className="w-3 h-3" /> Generate
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-1.5 px-4 pb-2">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab || 'all'}
            onClick={() => setReportTypeFilter(tab)}
            className={`px-2.5 py-1 rounded-full text-[10px] font-mono transition-all duration-200 ${
              reportTypeFilter === tab
                ? 'bg-accent/15 text-accent border border-accent/20'
                : 'bg-bg-active text-text-ghost/60 border border-transparent hover:text-text-ghost hover:border-border-subtle'
            }`}
          >
            {FILTER_LABELS[tab]}
          </button>
        ))}
      </div>

      {/* Table */}
      {filteredReports.length > 0 ? (
        <div className="max-h-[280px] overflow-y-auto scrollbar-thin border-t border-border-subtle">
          {filteredReports.map((report, i) => (
            <ReportRow key={report.id || i} report={report} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-10 border-t border-border-subtle">
          <FileText className="w-6 h-6 text-text-ghost/30 mb-2" />
          <div className="text-text-ghost font-mono text-xs mb-0.5">No reports generated yet</div>
          <div className="text-text-ghost/40 font-mono text-[10px]">Click Generate to create your first report</div>
        </div>
      )}

      <AnimatePresence>
        {generateModalOpen && <GenerateReportModal onClose={closeGenerateModal} />}
      </AnimatePresence>
    </div>
  )
})
