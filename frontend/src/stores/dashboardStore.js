import { create } from 'zustand'
import { dashboardApi } from '../services/dashboardApi'

const useDashboardStore = create((set, get) => ({
  stats: null,
  events: [],
  quickHealth: [],
  isLoading: false,

  fetchAll: async () => {
    set({ isLoading: true })
    await Promise.allSettled([
      dashboardApi.getStats().then(({ data }) => set({ stats: data })).catch(() => {}),
      dashboardApi.getEvents({ limit: 20 }).then(({ data }) => set({ events: data.events || data })).catch(() => {}),
      dashboardApi.getQuickHealth().then(({ data }) => set({ quickHealth: data.customers || data })).catch(() => {}),
    ])
    set({ isLoading: false })
  },

  prependEvent: (event) => {
    set((state) => ({ events: [event, ...state.events].slice(0, 50) }))
  },
}))

export default useDashboardStore
