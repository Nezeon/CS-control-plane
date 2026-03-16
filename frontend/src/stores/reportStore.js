import { create } from 'zustand'
import { reportApi } from '../services/reportApi'
import { insightApi } from '../services/insightApi'
import { AGENT_LANE_MAP } from '../utils/chartHelpers'

const useReportStore = create((set, get) => ({
  // Analytics data
  kpis: null,
  healthTrend: [],
  ticketVolume: [],
  sentimentStream: [],
  agentPerformance: [],
  isLoading: false,
  error: null,

  // Reports
  reports: [],
  reportsTotal: 0,
  reportsLoading: false,
  reportTypeFilter: '',

  // Cross-filter
  crossFilter: null,

  // Generate modal
  generateModalOpen: false,
  generating: false,

  // Cross-filter actions
  setCrossFilter: (filter) => set({ crossFilter: filter }),
  clearCrossFilter: () => set({ crossFilter: null }),

  // Modal actions
  openGenerateModal: () => set({ generateModalOpen: true }),
  closeGenerateModal: () => set({ generateModalOpen: false }),
  setReportTypeFilter: (filter) => set({ reportTypeFilter: filter }),

  fetchAnalytics: async () => {
    set({ isLoading: true, error: null })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedAnalyticsKpis, seedTicketVolume, seedHealthTrend, seedAgentPerformance, seedSentimentStream } = await import('../data/analytics')
        set({
          kpis: seedAnalyticsKpis,
          ticketVolume: seedTicketVolume,
          healthTrend: seedHealthTrend,
          agentPerformance: seedAgentPerformance,
          sentimentStream: seedSentimentStream,
          isLoading: false,
        })
      } catch { set({ isLoading: false }) }
      return
    }
    try {
      const [analyticsRes, sentimentRes] = await Promise.allSettled([
        reportApi.getAnalytics(),
        insightApi.getSentimentTrend({ days: 30 }),
      ])

      const updates = {}

      if (analyticsRes.status === 'fulfilled') {
        const data = analyticsRes.value.data
        updates.kpis = data.kpis || null

        // Map ticket volume: flatten by_severity
        const tv = data.ticket_volume || []
        updates.ticketVolume = tv.map((w) => ({
          week: w.week,
          P1: w.by_severity?.P1 ?? w.P1 ?? 0,
          P2: w.by_severity?.P2 ?? w.P2 ?? 0,
          P3: w.by_severity?.P3 ?? w.P3 ?? 0,
          P4: w.by_severity?.P4 ?? w.P4 ?? 0,
          opened: w.opened ?? 0,
          resolved: w.resolved ?? 0,
        }))

        // Map health trend (pass-through — may be aggregate or per-customer)
        updates.healthTrend = data.health_trend || []

        // Map agent performance: enrich with lane color
        const ap = data.agent_performance || []
        updates.agentPerformance = ap.map((a) => {
          const key = a.agent?.toLowerCase().replace(/\s+/g, '_')
          const lane = AGENT_LANE_MAP[key] || 'control'
          return { ...a, lane }
        })
      }

      if (sentimentRes.status === 'fulfilled') {
        const raw = sentimentRes.value.data.trend || sentimentRes.value.data || []
        // Transform to stream data: { date, positive, neutral, negative }
        updates.sentimentStream = raw.map((d) => {
          const score = d.avg_sentiment_score ?? 0
          const count = d.call_count ?? 1
          return {
            date: d.date || d.day,
            positive: Math.max(0, score) * count,
            neutral: (1 - Math.abs(score)) * count,
            negative: Math.max(0, -score) * count,
          }
        })
      }

      set({ ...updates, isLoading: false })
    } catch (err) {
      console.error('[Report] Failed to fetch analytics:', err)
      set({ isLoading: false, error: err.message })
    }
  },

  fetchReports: async () => {
    set({ reportsLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedReports } = await import('../data/analytics')
        set({ reports: seedReports, reportsTotal: seedReports.length, reportsLoading: false })
      } catch { set({ reportsLoading: false }) }
      return
    }
    try {
      const params = {}
      const { reportTypeFilter } = get()
      if (reportTypeFilter) params.report_type = reportTypeFilter
      const { data } = await reportApi.list(params)
      const items = data.reports || data.items || data || []
      set({ reports: items, reportsTotal: data.total ?? items.length, reportsLoading: false })
    } catch (err) {
      console.error('[Report] Failed to fetch reports:', err)
      set({ reportsLoading: false })
    }
  },

  generateReport: async (type, periodStart, periodEnd, customerId = null) => {
    set({ generating: true })
    try {
      const payload = { report_type: type, period_start: periodStart, period_end: periodEnd }
      if (customerId) payload.customer_id = customerId
      const { data } = await reportApi.generate(payload)
      set({ generating: false, generateModalOpen: false })
      return data.task_id || data.id
    } catch (err) {
      console.error('[Report] Failed to generate report:', err)
      set({ generating: false })
      throw err
    }
  },

  fetchAll: async () => {
    await Promise.allSettled([
      get().fetchAnalytics(),
      get().fetchReports(),
    ])
  },
}))

export default useReportStore
