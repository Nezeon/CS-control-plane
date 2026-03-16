import { create } from 'zustand'
import { customerApi } from '../services/customerApi'

const useCustomerStore = create((set, get) => ({
  selectedCustomer: null,
  detailLoading: false,
  healthHistory: [],
  customerTickets: [],
  customerInsights: [],

  fetchAllDetail: async (id) => {
    set({ detailLoading: true, selectedCustomer: null })
    await Promise.allSettled([
      customerApi.get(id).then(({ data }) => set({ selectedCustomer: data })).catch(() => {}),
      customerApi.getHealthHistory(id, { days: 90 }).then(({ data }) => set({ healthHistory: data.history || [] })).catch(() => set({ healthHistory: [] })),
      customerApi.getTickets(id).then(({ data }) => set({ customerTickets: data.tickets || [] })).catch(() => set({ customerTickets: [] })),
      customerApi.getInsights(id).then(({ data }) => set({ customerInsights: data.insights || [] })).catch(() => set({ customerInsights: [] })),
    ])
    set({ detailLoading: false })
  },

  clearDetail: () => set({
    selectedCustomer: null, healthHistory: [], customerTickets: [], customerInsights: [],
  }),
}))

export default useCustomerStore
