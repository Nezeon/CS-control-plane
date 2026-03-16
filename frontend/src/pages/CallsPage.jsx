import { useState, useEffect, useMemo } from 'react'
import { AnimatePresence, m } from 'framer-motion'
import {
  Phone,
  Clock,
  Users,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Mic,
  TrendingDown,
  TrendingUp,
  Minus,
} from 'lucide-react'
import { cn } from '../utils/cn'
import GlassCard from '../components/shared/GlassCard'
import StatusPill from '../components/shared/StatusPill'
import PillFilter from '../components/shared/PillFilter'
import { formatRelativeTime, formatDate } from '../utils/formatters'

const NOW = Date.now()
const MIN = 60000
const mkTime = (minsAgo) => new Date(NOW - minsAgo * MIN).toISOString()

const seedCalls = [
  { id: 'call_001', customer_name: 'Acme Corp', title: 'Weekly Sync — Acme Corp', date: mkTime(120), duration_mins: 32, participants: ['Sarah Chen (CSM)', 'Tom Richards (CTO)'], sentiment_score: 0.71, sentiment_label: 'positive', summary: 'Discussed post-incident review for ACM-1234. Customer satisfied with resolution speed. Agreed on config audit schedule.', action_items: ['Schedule config audit by March 10', 'Share incident postmortem doc'], decisions: ['Move to OVA 4.3.0 in next maintenance window'], risk_signals: [], status: 'processed', analyzed_by: 'Jordan Ellis' },
  { id: 'call_002', customer_name: 'Beta Financial', title: 'Executive Check-in — Beta Financial', date: mkTime(180), duration_mins: 45, participants: ['David Park (CSM)', 'Lisa Wang (CFO)', 'Mark Johnson (VP Eng)'], sentiment_score: 0.28, sentiment_label: 'negative', summary: 'CFO expressed frustration with reporting module bugs. Mentioned "exploring alternatives" — strong churn signal. VP Eng more positive on API features.', action_items: ['Fast-track reporting module fixes', 'Send bug fix timeline by March 3', 'Schedule follow-up with VP Eng on API roadmap'], decisions: [], risk_signals: ['CFO mentioned exploring alternatives', 'Reporting module frustration escalating'], status: 'processed', analyzed_by: 'Jordan Ellis' },
  { id: 'call_003', customer_name: 'Gamma Telecom', title: 'QBR Prep — Gamma Telecom', date: mkTime(350), duration_mins: 28, participants: ['Sarah Chen (CSM)', 'Amit Patel (Director of IT)'], sentiment_score: 0.65, sentiment_label: 'positive', summary: 'Reviewed Q1 metrics for upcoming QBR. Dashboard speed improvement acknowledged. Customer wants more self-service analytics.', action_items: ['Prepare QBR deck with speed improvement metrics', 'Demo analytics self-service feature'], decisions: ['QBR scheduled for March 15'], risk_signals: [], status: 'processed', analyzed_by: 'Jordan Ellis' },
  { id: 'call_004', customer_name: 'Epsilon Insurance', title: 'Escalation Call — Epsilon Insurance', date: mkTime(40), duration_mins: 52, participants: ['David Park (CSM)', 'James Miller (VP Claims)', 'Priya Shah (CISO)'], sentiment_score: -0.68, sentiment_label: 'very_negative', summary: 'Critical escalation regarding data loss incident. VP Claims extremely frustrated. CISO raised compliance concerns. Agreed on immediate WAL recovery and post-incident review.', action_items: ['Complete WAL recovery by EOD', 'Deliver incident report within 48hrs', 'Schedule compliance review meeting', 'Assign dedicated support engineer'], decisions: ['Dedicated support engineer assigned'], risk_signals: ['Data integrity concerns', 'Compliance review requested', 'Renewal at risk (March 31)'], status: 'processed', analyzed_by: 'Jordan Ellis' },
  { id: 'call_005', customer_name: 'Delta Health', title: 'Monthly Sync — Delta Health', date: mkTime(480), duration_mins: 25, participants: ['Sarah Chen (CSM)', 'Dr. Angela Roberts (CIO)'], sentiment_score: 0.85, sentiment_label: 'very_positive', summary: 'Model customer check-in. Very happy with platform stability. Interested in expanding to additional departments.', action_items: ['Send expansion proposal for Radiology dept', 'Schedule technical demo for Dr. Roberts team'], decisions: ['Explore Q2 expansion'], risk_signals: [], status: 'processed', analyzed_by: 'Jordan Ellis' },
  { id: 'call_006', customer_name: 'Theta Energy', title: 'Quarterly Review — Theta Energy', date: mkTime(280), duration_mins: 38, participants: ['David Park (CSM)', 'Robert Chen (COO)', 'Maria Gonzales (IT Dir)'], sentiment_score: 0.52, sentiment_label: 'mixed', summary: 'Mixed sentiment. Q2 Phase 2 approved but COO mentioned April budget review. IT Director positive on technical progress.', action_items: ['Confirm Q2 Phase 2 timeline', 'Prepare budget justification materials', 'Send Phase 1 ROI report', 'Schedule technical roadmap review', 'Add to 30-day watch list', 'Prepare renewal defense materials'], decisions: ['Q2 Phase 2 approved'], risk_signals: ['April budget review mentioned'], status: 'processed', analyzed_by: 'Jordan Ellis' },
  { id: 'call_007', customer_name: 'Iota Defense', title: 'Incident Bridge — Iota Defense', date: mkTime(15), duration_mins: 67, participants: ['David Park (CSM)', 'Col. Patricia Hayes (CISO)', 'Mike Torres (Ops Lead)'], sentiment_score: -0.45, sentiment_label: 'negative', summary: 'Emergency bridge call for FedRAMP secure zone outage. Col. Hayes concerned about cert management process. Agreed on immediate cert renewal and process review.', action_items: ['Renew TLS cert on bridge-01', 'Document cert-manager cron migration issue', 'Schedule FedRAMP process review', 'Deliver data integrity report'], decisions: ['Emergency patch approved for immediate deployment'], risk_signals: ['FedRAMP compliance concerns', 'Security process gaps identified'], status: 'processing', analyzed_by: 'Jordan Ellis' },
  { id: 'call_008', customer_name: 'Zeta Retail', title: 'Feature Request Sync — Zeta Retail', date: mkTime(600), duration_mins: 22, participants: ['Sarah Chen (CSM)', 'Kelly Wu (Product Lead)'], sentiment_score: 0.58, sentiment_label: 'positive', summary: 'Reviewed feature requests. Customer happy with recent API improvements. Discussed custom dashboard widget needs.', action_items: ['File feature request for custom widgets', 'Share API documentation updates'], decisions: [], risk_signals: [], status: 'processed', analyzed_by: 'Jordan Ellis' },
]

function isDemoMode() {
  return localStorage.getItem('access_token') === 'demo-token'
}

const sentimentFilters = [
  { value: 'all', label: 'All' },
  { value: 'positive', label: 'Positive' },
  { value: 'mixed', label: 'Mixed' },
  { value: 'negative', label: 'Negative' },
]

function sentimentGroup(label) {
  if (label === 'very_positive' || label === 'positive') return 'positive'
  if (label === 'mixed') return 'mixed'
  return 'negative'
}

function SentimentBar({ score }) {
  const pct = ((score + 1) / 2) * 100
  const color =
    score >= 0.5
      ? '#00E5A0'
      : score >= 0.2
        ? '#4DD5B8'
        : score >= -0.1
          ? '#FFB547'
          : score >= -0.4
            ? '#FF8C5C'
            : '#FF5C5C'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-bg-active overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xxs font-mono font-semibold" style={{ color }}>
        {score >= 0 ? '+' : ''}
        {score.toFixed(2)}
      </span>
    </div>
  )
}

function SentimentIcon({ label }) {
  if (label === 'very_positive' || label === 'positive')
    return <TrendingUp className="w-3.5 h-3.5 text-status-success" />
  if (label === 'mixed') return <Minus className="w-3.5 h-3.5 text-status-warning" />
  return <TrendingDown className="w-3.5 h-3.5 text-status-danger" />
}

function CallListItem({ call, selected, onClick }) {
  return (
    <GlassCard
      level={selected ? 'near' : 'mid'}
      interactive
      className={cn(
        'p-3.5 cursor-pointer transition-all',
        selected && 'ring-1 ring-accent/30'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <h4 className="text-sm font-medium text-text-primary truncate">{call.customer_name}</h4>
        <StatusPill status={call.status} size="sm" />
      </div>
      <p className="text-xs text-text-muted mb-2 truncate">{call.title}</p>
      <div className="flex items-center gap-3 text-xxs text-text-ghost mb-2">
        <span className="inline-flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatRelativeTime(call.date)}
        </span>
        <span>{call.duration_mins}m</span>
        <span className="inline-flex items-center gap-1">
          <Users className="w-3 h-3" />
          {call.participants.length}
        </span>
      </div>
      <SentimentBar score={call.sentiment_score} />
    </GlassCard>
  )
}

function CallDetail({ call }) {
  const sentColor =
    call.sentiment_score >= 0.5
      ? '#00E5A0'
      : call.sentiment_score >= 0.2
        ? '#4DD5B8'
        : call.sentiment_score >= -0.1
          ? '#FFB547'
          : call.sentiment_score >= -0.4
            ? '#FF8C5C'
            : '#FF5C5C'

  return (
    <m.div
      key={call.id}
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -12 }}
      transition={{ duration: 0.2 }}
      className="h-full"
    >
      <GlassCard level="near" className="p-5 h-full overflow-y-auto custom-scrollbar">
        {/* Header */}
        <h2 className="text-base font-display font-semibold text-text-primary mb-1">{call.title}</h2>
        <div className="flex items-center gap-3 text-xs text-text-muted mb-4">
          <span>{call.customer_name}</span>
          <span className="text-text-ghost">{formatDate(call.date)}</span>
          <span>{call.duration_mins} min</span>
        </div>

        {/* Sentiment */}
        <div className="flex items-center gap-3 mb-5 p-3 rounded-xl bg-bg-subtle border border-border-subtle">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center font-display font-bold text-lg"
            style={{ backgroundColor: sentColor + '15', color: sentColor }}
          >
            {call.sentiment_score >= 0 ? '+' : ''}
            {call.sentiment_score.toFixed(1)}
          </div>
          <div>
            <div className="flex items-center gap-1.5 mb-0.5">
              <SentimentIcon label={call.sentiment_label} />
              <span className="text-sm font-medium text-text-primary capitalize">
                {call.sentiment_label.replace('_', ' ')}
              </span>
            </div>
            <p className="text-xxs text-text-ghost">Sentiment analysis by {call.analyzed_by}</p>
          </div>
        </div>

        {/* Summary */}
        <div className="mb-5">
          <h4 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-2">
            Summary
          </h4>
          <p className="text-xs text-text-secondary leading-relaxed">{call.summary}</p>
        </div>

        {/* Participants */}
        <div className="mb-5">
          <h4 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-2">
            Participants
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {call.participants.map((p) => (
              <span
                key={p}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xxs bg-bg-active text-text-secondary border border-border-subtle"
              >
                <Users className="w-3 h-3 text-text-ghost" />
                {p}
              </span>
            ))}
          </div>
        </div>

        {/* Action Items */}
        {call.action_items.length > 0 && (
          <div className="mb-5">
            <h4 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-2">
              Action Items ({call.action_items.length})
            </h4>
            <ul className="space-y-1.5">
              {call.action_items.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                  <CheckCircle2 className="w-3.5 h-3.5 text-text-ghost mt-0.5 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Decisions */}
        {call.decisions.length > 0 && (
          <div className="mb-5">
            <h4 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-2">
              Decisions
            </h4>
            <ul className="space-y-1.5">
              {call.decisions.map((d, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-xs text-teal px-2.5 py-1.5 rounded-lg bg-teal/5 border border-teal/10"
                >
                  <ArrowRight className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  {d}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Risk Signals */}
        {call.risk_signals.length > 0 && (
          <div className="mb-5">
            <h4 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-2">
              Risk Signals ({call.risk_signals.length})
            </h4>
            <ul className="space-y-1.5">
              {call.risk_signals.map((r, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-xs text-status-danger px-2.5 py-1.5 rounded-lg bg-status-danger/5 border border-status-danger/10"
                >
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Footer */}
        <div className="pt-3 border-t border-border-subtle">
          <p className="text-xxs text-text-ghost inline-flex items-center gap-1">
            <Mic className="w-3 h-3" />
            Analyzed by {call.analyzed_by}
          </p>
        </div>
      </GlassCard>
    </m.div>
  )
}

function EmptyDetail() {
  return (
    <GlassCard level="mid" className="p-6 h-full flex flex-col items-center justify-center gap-3">
      <div className="w-12 h-12 rounded-full bg-bg-subtle flex items-center justify-center">
        <Phone className="w-5 h-5 text-text-ghost" />
      </div>
      <p className="text-sm text-text-muted text-center">Select a call to view details</p>
      <p className="text-xs text-text-ghost text-center">Click any recording in the list</p>
    </GlassCard>
  )
}

export default function CallsPage() {
  const [calls, setCalls] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    if (isDemoMode()) {
      setCalls(seedCalls)
      setIsLoading(false)
      return
    }
    // Live mode: fetch from API
    const fetchCalls = async () => {
      try {
        const { default: api } = await import('../services/api')
        const { data } = await api.get('/insights', { params: { type: 'call' } })
        const items = data.insights || data.items || data || []
        setCalls(items)
      } catch (err) {
        console.error('[Calls] Failed to fetch call data:', err)
        setCalls([])
      } finally {
        setIsLoading(false)
      }
    }
    fetchCalls()
  }, [])

  const stats = useMemo(() => {
    const actionItems = calls.reduce((s, c) => s + c.action_items.length, 0)
    const riskSignals = calls.reduce((s, c) => s + c.risk_signals.length, 0)
    return { total: calls.length, actionItems, riskSignals }
  }, [calls])

  const filtered = useMemo(
    () =>
      filter === 'all'
        ? calls
        : calls.filter((c) => sentimentGroup(c.sentiment_label) === filter),
    [calls, filter]
  )

  const selectedCall = useMemo(
    () => calls.find((c) => c.id === selectedId) || null,
    [calls, selectedId]
  )

  return (
    <m.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-5"
    >
      {/* Header */}
      <div>
        <h1 className="text-xl font-display font-semibold text-text-primary mb-1">Fathom Agent</h1>
        <div className="flex items-center gap-5">
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <Phone className="w-3.5 h-3.5 text-accent" />
            <span className="text-accent font-semibold">{stats.total}</span> calls
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal" />
            <span className="text-teal font-semibold">{stats.actionItems}</span> action items
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <AlertTriangle className="w-3.5 h-3.5 text-status-danger" />
            <span className="text-status-danger font-semibold">{stats.riskSignals}</span> risk signals
          </span>
        </div>
      </div>

      {/* Filter */}
      <PillFilter options={sentimentFilters} value={filter} onChange={setFilter} />

      {isLoading && (
        <div className="py-20 text-center">
          <p className="text-sm text-text-muted animate-pulse">Loading calls...</p>
        </div>
      )}

      {!isLoading && calls.length === 0 && (
        <GlassCard level="mid" className="p-12 text-center">
          <div className="w-14 h-14 rounded-full bg-bg-subtle flex items-center justify-center mx-auto mb-4">
            <Phone className="w-6 h-6 text-text-ghost" />
          </div>
          <h3 className="text-sm font-medium text-text-muted mb-1">No call recordings yet</h3>
          <p className="text-xs text-text-ghost">Fathom data will appear here once Fathom syncs recordings.</p>
        </GlassCard>
      )}

      {/* Split view */}
      {!isLoading && calls.length > 0 && <div
        className="grid grid-cols-1 lg:grid-cols-5 gap-4"
        style={{ height: 'calc(100vh - 240px)', minHeight: '500px' }}
      >
        {/* Call list — 3/5 */}
        <div className="lg:col-span-3 overflow-y-auto custom-scrollbar space-y-2 pr-1">
          {filtered.map((call) => (
            <CallListItem
              key={call.id}
              call={call}
              selected={selectedId === call.id}
              onClick={() => setSelectedId(call.id)}
            />
          ))}
          {filtered.length === 0 && (
            <div className="py-16 text-center">
              <p className="text-xs text-text-ghost">No calls matching filter</p>
            </div>
          )}
        </div>

        {/* Detail — 2/5 */}
        <div className="lg:col-span-2 min-h-0">
          <AnimatePresence mode="wait">
            {selectedCall ? (
              <CallDetail key={selectedCall.id} call={selectedCall} />
            ) : (
              <EmptyDetail key="empty" />
            )}
          </AnimatePresence>
        </div>
      </div>}
    </m.div>
  )
}
