import { useEffect, useCallback, useRef, lazy, Suspense } from 'react'
import { m } from 'framer-motion'
import { Search, Phone, AlertTriangle } from 'lucide-react'
import useInsightStore from '../stores/insightStore'
const SentimentSpectrum = lazy(() => import('../components/insights/SentimentSpectrum'))
import InsightCard from '../components/insights/InsightCard'
import ActionTracker from '../components/insights/ActionTracker'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'

const sentimentFilters = [
  { value: '', label: 'All' },
  { value: 'positive', label: 'Positive', color: '#22C55E' },
  { value: 'neutral', label: 'Neutral', color: '#71717A' },
  { value: 'negative', label: 'Negative', color: '#EF4444' },
]

export default function InsightsPage() {
  const {
    insights, isLoading, sentimentTrend, trendLoading,
    actionItems, actionSummary, actionsLoading,
    search, sentiment, expandedInsightId,
    setSearch, setSentiment, setExpandedInsightId,
    toggleActionItem, fetchAll, fetchInsights,
  } = useInsightStore()

  const searchTimer = useRef(null)

  useEffect(() => { fetchAll() }, [fetchAll])

  const handleSearchChange = useCallback((e) => {
    const val = e.target.value
    setSearch(val)
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => fetchInsights(), 300)
  }, [setSearch, fetchInsights])

  const handleSentimentFilter = useCallback((val) => {
    setSentiment(val)
    setTimeout(() => fetchInsights(), 0)
  }, [setSentiment, fetchInsights])

  const overdueCount = actionSummary?.overdue || 0

  return (
    <div className="h-full flex flex-col overflow-hidden" data-testid="insights-page">
      {/* Header */}
      <div className="pb-4 shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-text-primary">Insights</h1>
            <div className="flex items-center gap-4 mt-1">
              <span className="flex items-center gap-1.5 text-xs text-text-muted">
                <Phone className="w-3 h-3" />
                <span className="text-text-primary font-semibold">{insights.length}</span> calls
              </span>
              {overdueCount > 0 && (
                <span className="flex items-center gap-1.5 text-xs text-status-danger">
                  <AlertTriangle className="w-3 h-3" />
                  <span className="font-semibold">{overdueCount}</span> overdue
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-ghost" />
            <input
              type="text"
              placeholder="Search insights..."
              value={search}
              onChange={handleSearchChange}
              data-testid="insights-search"
              className="pl-9 pr-4 py-2 rounded-lg bg-bg-subtle border border-border text-sm text-text-primary placeholder:text-text-ghost focus:border-border-strong focus:outline-none transition-colors w-56"
            />
          </div>

          <div className="flex items-center gap-1">
            {sentimentFilters.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleSentimentFilter(opt.value)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
                  sentiment === opt.value
                    ? 'bg-accent/15 text-accent border border-accent/20'
                    : 'bg-bg-active text-text-ghost/60 border border-transparent hover:text-text-ghost hover:border-border-subtle'
                }`}
              >
                {opt.color && (
                  <span className="inline-block w-1.5 h-1.5 rounded-full mr-1.5" style={{ backgroundColor: opt.color }} />
                )}
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pb-6">
        {/* Sentiment chart */}
        <div className="mb-4">
          <Suspense fallback={<LoadingSkeleton variant="chart" />}>
            <SentimentSpectrum data={sentimentTrend} isLoading={trendLoading} />
          </Suspense>
        </div>

        {/* Two columns: cards + action tracker */}
        <div className="flex gap-4">
          <div className="flex-1 min-w-0 space-y-3">
            {isLoading ? (
              <div className="space-y-3"><LoadingSkeleton variant="card" count={4} /></div>
            ) : insights.length === 0 ? (
              <div className="flex items-center justify-center py-16">
                <div className="text-center">
                  <p className="text-sm text-text-muted mb-1">No insights found</p>
                  <p className="text-xs text-text-ghost">
                    {search || sentiment ? 'Try adjusting your filters' : 'Insights will appear after calls are processed'}
                  </p>
                </div>
              </div>
            ) : (
              <m.div className="space-y-2">
                {insights.map((insight, i) => (
                  <m.div
                    key={insight.id || i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.02 }}
                  >
                    <InsightCard
                      insight={insight}
                      isExpanded={expandedInsightId === insight.id}
                      onToggleExpand={setExpandedInsightId}
                      onToggleAction={toggleActionItem}
                    />
                  </m.div>
                ))}
              </m.div>
            )}
          </div>

          {/* Action Tracker sidebar */}
          <div className="hidden lg:block shrink-0 sticky top-0 self-start">
            <ActionTracker
              actionItems={actionItems}
              summary={actionSummary}
              isLoading={actionsLoading}
              onToggleAction={toggleActionItem}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
