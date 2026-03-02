import { create } from 'zustand'

const useAlertStore = create((set) => ({
  alerts: [],
  total: 0,
  unreadCount: 0,
  isLoading: false,

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
