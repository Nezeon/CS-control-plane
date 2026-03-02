import { create } from 'zustand'
import { customerApi } from '../services/customerApi'

const useCustomerStore = create((set, get) => ({
  // List state
  customers: [],
  total: 0,
  isLoading: false,
  error: null,

  // Filters
  search: '',
  risk_level: '',
  tier: '',
  cs_owner_id: '',
  sort_by: 'health_score',
  sort_order: 'asc',

  // View mode
  viewMode: 'grid', // 'grid' | 'table' | 'solar'

  // Detail state
  selectedCustomer: null,
  detailLoading: false,
  healthHistory: [],
  customerTickets: [],
  customerInsights: [],
  actionItems: [],
  similarIssues: [],

  // Hover state for QuickIntelPanel
  hoveredCustomer: null,

  // --- Actions ---

  setSearch: (search) => set({ search }),
  setRiskLevel: (risk_level) => set({ risk_level }),
  setTier: (tier) => set({ tier }),
  setCsOwner: (cs_owner_id) => set({ cs_owner_id }),
  setSortBy: (sort_by) => set({ sort_by }),
  setSortOrder: (sort_order) => set({ sort_order }),
  setViewMode: (viewMode) => set({ viewMode }),
  setHoveredCustomer: (hoveredCustomer) => set({ hoveredCustomer }),

  fetchCustomers: async () => {
    const { search, risk_level, tier, cs_owner_id, sort_by, sort_order } = get()
    set({ isLoading: true, error: null })
    try {
      const params = { sort_by, sort_order }
      if (search) params.search = search
      if (risk_level) params.risk_level = risk_level
      if (tier) params.tier = tier
      if (cs_owner_id) params.cs_owner_id = cs_owner_id

      const { data } = await customerApi.list(params)
      const customers = data.customers || data.items || data
      const total = data.total ?? (Array.isArray(customers) ? customers.length : 0)
      set({ customers, total, isLoading: false })
    } catch (err) {
      console.error('[Customer] Failed to fetch customers, loading seed data:', err)
      try {
        const { seedCustomers } = await import('../data/customers')
        set({ customers: seedCustomers, total: seedCustomers.length, isLoading: false })
      } catch {
        set({ isLoading: false, error: 'Failed to load customers' })
      }
    }
  },

  fetchCustomerDetail: async (id) => {
    set({ detailLoading: true, selectedCustomer: null })
    try {
      const { data } = await customerApi.get(id)
      set({ selectedCustomer: data, detailLoading: false })
    } catch (err) {
      console.error('[Customer] Failed to fetch detail, loading seed data:', err)
      try {
        const { seedCustomerDetail } = await import('../data/customers')
        set({ selectedCustomer: seedCustomerDetail(id), detailLoading: false })
      } catch {
        set({ detailLoading: false, error: 'Failed to load customer' })
      }
    }
  },

  fetchHealthHistory: async (id) => {
    try {
      const { data } = await customerApi.getHealthHistory(id, { days: 90 })
      set({ healthHistory: data.history || data || [] })
    } catch {
      try {
        const { seedHealthHistory } = await import('../data/healthHistory')
        set({ healthHistory: seedHealthHistory[id] || [] })
      } catch {
        set({ healthHistory: [] })
      }
    }
  },

  fetchCustomerTickets: async (id) => {
    try {
      const { data } = await customerApi.getTickets(id)
      set({ customerTickets: data.tickets || data || [] })
    } catch {
      try {
        const { seedTickets } = await import('../data/tickets')
        set({ customerTickets: seedTickets.filter((t) => t.customer_id === id) })
      } catch {
        set({ customerTickets: [] })
      }
    }
  },

  fetchCustomerInsights: async (id) => {
    try {
      const { data } = await customerApi.getInsights(id)
      set({ customerInsights: data.insights || data || [] })
    } catch {
      try {
        const { seedInsights } = await import('../data/insights')
        set({ customerInsights: seedInsights.filter((i) => i.customer_id === id) })
      } catch {
        set({ customerInsights: [] })
      }
    }
  },

  fetchActionItems: async (id) => {
    try {
      const { data } = await customerApi.getActionItems(id)
      set({ actionItems: data.items || data || [] })
    } catch {
      try {
        const { seedInsights } = await import('../data/insights')
        const items = seedInsights
          .filter((i) => i.customer_id === id)
          .flatMap((i) => i.action_items || [])
        set({ actionItems: items })
      } catch {
        set({ actionItems: [] })
      }
    }
  },

  fetchSimilarIssues: async (id) => {
    try {
      const { data } = await customerApi.getSimilarIssues(id)
      set({ similarIssues: data.issues || data || [] })
    } catch {
      try {
        const { seedTickets } = await import('../data/tickets')
        const similar = seedTickets
          .filter((t) => t.customer_id !== id)
          .slice(0, 5)
          .map((t) => ({ id: t.id, title: t.summary, similarity_score: 0.85, status: t.status, severity: t.severity }))
        set({ similarIssues: similar })
      } catch {
        set({ similarIssues: [] })
      }
    }
  },

  // Fetch all detail data in parallel
  fetchAllDetail: async (id) => {
    const store = get()
    set({ detailLoading: true })
    await Promise.all([
      store.fetchCustomerDetail(id),
      store.fetchHealthHistory(id),
      store.fetchCustomerTickets(id),
      store.fetchCustomerInsights(id),
      store.fetchActionItems(id),
      store.fetchSimilarIssues(id),
    ])
    set({ detailLoading: false })
  },

  // WebSocket handler for real-time health updates
  handleHealthUpdate: (customerId, newScore, riskLevel) => {
    set((state) => ({
      customers: state.customers.map((c) =>
        c.id === customerId
          ? { ...c, health_score: newScore, risk_level: riskLevel }
          : c
      ),
      selectedCustomer:
        state.selectedCustomer?.id === customerId
          ? { ...state.selectedCustomer, health_score: newScore, risk_level: riskLevel }
          : state.selectedCustomer,
    }))
  },

  // Clear detail state
  clearDetail: () =>
    set({
      selectedCustomer: null,
      healthHistory: [],
      customerTickets: [],
      customerInsights: [],
      actionItems: [],
      similarIssues: [],
    }),
}))

export default useCustomerStore
