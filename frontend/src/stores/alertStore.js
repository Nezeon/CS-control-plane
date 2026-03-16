import { create } from 'zustand'

const useAlertStore = create((set) => ({
  alerts: [],
  total: 0,
  unreadCount: 0,
  isLoading: false,

  fetchAll: async () => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedAlerts } = await import('../data/alerts')
        set({ alerts: seedAlerts, total: seedAlerts.length, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    try {
      const { default: api } = await import('../services/api')
      const { data } = await api.get('/alerts')
      const alerts = data.alerts || data || []
      set({ alerts, total: alerts.length, isLoading: false })
    } catch (err) {
      console.error('[Alerts] Failed to fetch alerts:', err)
      set({ isLoading: false })
    }
  },

  setAlerts: (alerts, total) => set({ alerts, total }),

  addAlert: (alert) => {
    set((state) => ({
      alerts: [alert, ...state.alerts],
      total: state.total + 1,
      unreadCount: state.unreadCount + 1,
    }))
  },

  acknowledgeAlert: (id) => {
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, status: 'acknowledged' } : a
      ),
    }))
  },

  resolveAlert: (id) => {
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, status: 'resolved' } : a
      ),
    }))
  },

  dismissAlert: (id) => {
    set((state) => ({
      alerts: state.alerts.filter((a) => a.id !== id),
      total: state.total - 1,
    }))
  },

  clearUnread: () => set({ unreadCount: 0 }),
}))

export default useAlertStore
