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
      console.error('[Dashboard] Failed to fetch stats, loading seed data:', err)
      try {
        const { seedDashboardStats } = await import('../data/dashboard')
        set({ stats: seedDashboardStats })
      } catch { /* seed unavailable */ }
    }
  },

  fetchAgents: async () => {
    try {
      const { data } = await dashboardApi.getAgents()
      set({ agents: data.agents || data })
    } catch (err) {
      console.error('[Dashboard] Failed to fetch agents, loading seed data:', err)
      try {
        const { seedAgents } = await import('../data/dashboard')
        set({ agents: seedAgents })
      } catch { /* seed unavailable */ }
    }
  },

  fetchEvents: async (params = { limit: 20 }) => {
    try {
      const { data } = await dashboardApi.getEvents(params)
      set({ events: data.events || data })
    } catch (err) {
      console.error('[Dashboard] Failed to fetch events, loading seed data:', err)
      try {
        const { seedEvents } = await import('../data/dashboard')
        set({ events: seedEvents })
      } catch { /* seed unavailable */ }
    }
  },

  fetchQuickHealth: async () => {
    try {
      const { data } = await dashboardApi.getQuickHealth()
      set({ quickHealth: data.customers || data })
    } catch (err) {
      console.error('[Dashboard] Failed to fetch quick health, loading seed data:', err)
      try {
        const { seedQuickHealth } = await import('../data/dashboard')
        set({ quickHealth: seedQuickHealth })
      } catch { /* seed unavailable */ }
    }
  },

  fetchAll: async () => {
    set({ isLoading: true })
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
