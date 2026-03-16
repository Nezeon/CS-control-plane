import { create } from 'zustand'
import { dashboardApi } from '../services/dashboardApi'

const useDashboardStore = create((set, get) => ({
  stats: null,
  agents: [],
  events: [],
  quickHealth: [],
  isLoading: false,
  error: null,

  fetchStats: async () => {
    try {
      const { data } = await dashboardApi.getStats()
      set({ stats: data })
    } catch (err) {
      console.error('[Dashboard] Failed to fetch stats:', err)
    }
  },

  fetchAgents: async () => {
    try {
      const { data } = await dashboardApi.getAgents()
      set({ agents: data.agents || data })
    } catch (err) {
      console.error('[Dashboard] Failed to fetch agents:', err)
    }
  },

  fetchEvents: async (params = { limit: 20 }) => {
    try {
      const { data } = await dashboardApi.getEvents(params)
      set({ events: data.events || data })
    } catch (err) {
      console.error('[Dashboard] Failed to fetch events:', err)
    }
  },

  fetchQuickHealth: async () => {
    try {
      const { data } = await dashboardApi.getQuickHealth()
      set({ quickHealth: data.customers || data })
    } catch (err) {
      console.error('[Dashboard] Failed to fetch quick health:', err)
    }
  },

  fetchAll: async () => {
    set({ isLoading: true })
    // In demo mode, skip API calls entirely — load seed data directly
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      console.log('[Dashboard] Demo mode — loading seed data directly (skipping API calls)')
      try {
        const { seedDashboardStats, seedAgents, seedEvents, seedQuickHealth } = await import('../data/dashboard')
        set({ stats: seedDashboardStats, agents: seedAgents, events: seedEvents, quickHealth: seedQuickHealth, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    console.log('[Dashboard] Fetching live data from backend...')
    await Promise.allSettled([
      get().fetchStats(),
      get().fetchAgents(),
      get().fetchEvents(),
      get().fetchQuickHealth(),
    ])
    set({ isLoading: false })
  },

  // WebSocket handlers
  updateAgentStatus: (agentName, status, task) => {
    set((state) => ({
      agents: state.agents.map((a) =>
        a.name === agentName ? { ...a, status, current_task: task } : a
      ),
    }))
  },

  prependEvent: (event) => {
    set((state) => ({
      events: [event, ...state.events].slice(0, 50),
    }))
  },

  updateQuickHealth: (customerId, newScore, riskLevel) => {
    set((state) => ({
      quickHealth: state.quickHealth.map((c) =>
        c.id === customerId ? { ...c, health_score: newScore, risk_level: riskLevel || c.risk_level } : c
      ),
    }))
  },
}))

export default useDashboardStore
