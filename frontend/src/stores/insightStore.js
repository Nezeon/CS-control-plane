import { create } from 'zustand'
import { insightApi } from '../services/insightApi'

const useInsightStore = create((set, get) => ({
  insights: [],
  total: 0,
  isLoading: false,
  error: null,

  search: '',
  customer_id: '',
  sentiment: '',
  date_from: '',
  date_to: '',

  sentimentTrend: [],
  trendLoading: false,

  actionItems: [],
  actionSummary: { pending: 0, overdue: 0, completed: 0 },
  actionsLoading: false,

  selectedInsight: null,
  expandedInsightId: null,

  setSearch: (search) => set({ search }),
  setCustomerId: (customer_id) => set({ customer_id }),
  setSentiment: (sentiment) => set({ sentiment }),
  setDateFrom: (date_from) => set({ date_from }),
  setDateTo: (date_to) => set({ date_to }),
  setExpandedInsightId: (id) => set((s) => ({
    expandedInsightId: s.expandedInsightId === id ? null : id,
  })),

  fetchInsights: async () => {
    const { search, customer_id, sentiment, date_from, date_to } = get()
    set({ isLoading: true, error: null })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedInsights } = await import('../data/insights')
        set({ insights: seedInsights, total: seedInsights.length, isLoading: false })
      } catch { set({ isLoading: false }) }
      return
    }
    try {
      const params = {}
      if (search) params.search = search
      if (customer_id) params.customer_id = customer_id
      if (sentiment) params.sentiment = sentiment
      if (date_from) params.date_from = date_from
      if (date_to) params.date_to = date_to
      const { data } = await insightApi.list(params)
      const items = data.insights || data.items || data || []
      set({ insights: items, total: data.total ?? items.length, isLoading: false })
    } catch (err) {
      console.error('[Insight] Failed to fetch insights:', err)
      set({ isLoading: false, error: err.message })
    }
  },

  fetchSentimentTrend: async (days = 30, customerId = null) => {
    set({ trendLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedSentimentTrend } = await import('../data/insights')
        set({ sentimentTrend: seedSentimentTrend, trendLoading: false })
      } catch { set({ trendLoading: false }) }
      return
    }
    try {
      const params = { days }
      if (customerId) params.customer_id = customerId
      const { data } = await insightApi.getSentimentTrend(params)
      set({ sentimentTrend: data.trend || data || [], trendLoading: false })
    } catch (err) {
      console.error('[Insight] Failed to fetch sentiment trend:', err)
      set({ trendLoading: false })
    }
  },

  fetchActionItems: async (status = null) => {
    set({ actionsLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedActionItems } = await import('../data/insights')
        set({ actionItems: seedActionItems, actionSummary: { pending: seedActionItems.length, overdue: 0, completed: 0 }, actionsLoading: false })
      } catch { set({ actionsLoading: false }) }
      return
    }
    try {
      const params = {}
      if (status) params.status = status
      const { data } = await insightApi.getActionItems(params)
      const items = data.items || data.action_items || data || []
      const summary = data.summary || {
        pending: items.filter((i) => i.status === 'pending').length,
        overdue: items.filter((i) => i.status === 'overdue' || (i.status === 'pending' && i.deadline && new Date(i.deadline) < new Date())).length,
        completed: items.filter((i) => i.status === 'completed').length,
      }
      set({ actionItems: items, actionSummary: summary, actionsLoading: false })
    } catch (err) {
      console.error('[Insight] Failed to fetch action items:', err)
      set({ actionsLoading: false })
    }
  },

  toggleActionItem: async (id, newStatus) => {
    if (!id) return
    set((state) => ({
      actionItems: state.actionItems.map((i) => (i.id === id ? { ...i, status: newStatus } : i)),
      actionSummary: {
        ...state.actionSummary,
        pending: state.actionSummary.pending + (newStatus === 'pending' ? 1 : -1),
        completed: state.actionSummary.completed + (newStatus === 'completed' ? 1 : -1),
      },
    }))
    try {
      await insightApi.updateActionItem(id, { status: newStatus })
    } catch (err) {
      console.error('[Insight] Failed to update action item:', err)
      get().fetchActionItems()
    }
  },

  syncFathom: async () => {
    try {
      const { data } = await insightApi.syncFathom()
      return data.task_id || data.id
    } catch (err) {
      console.error('[Insight] Failed to sync Fathom:', err)
      throw err
    }
  },

  fetchInsightDetail: async (id) => {
    try {
      const { data } = await insightApi.get(id)
      set({ selectedInsight: data })
    } catch (err) {
      console.error('[Insight] Failed to fetch insight detail:', err)
    }
  },

  fetchAll: async () => {
    await Promise.allSettled([
      get().fetchInsights(),
      get().fetchSentimentTrend(),
      get().fetchActionItems(),
    ])
  },

  handleInsightReady: (data) => {
    set((state) => ({ insights: [data, ...state.insights], total: state.total + 1 }))
  },
}))

export default useInsightStore
