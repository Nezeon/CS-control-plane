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

    // First fetch customer detail to know if it's a prospect
    let customer = null
    try {
      const { data } = await customerApi.get(id)
      customer = data
      set({ selectedCustomer: data })
    } catch {
      set({ detailLoading: false })
      return
    }

    // Fetch tickets + calls for all customers; health only for non-prospects
    const fetches = [
      customerApi.getTickets(id).then(({ data }) => set({ customerTickets: data.tickets || [] })).catch(() => set({ customerTickets: [] })),
      customerApi.getInsights(id).then(({ data }) => set({ customerInsights: data.insights || [] })).catch(() => set({ customerInsights: [] })),
    ]
    if (!customer.is_prospect) {
      fetches.push(
        customerApi.getHealthHistory(id, { days: 90 }).then(({ data }) => set({ healthHistory: data.history || [] })).catch(() => set({ healthHistory: [] })),
      )
    } else {
      set({ healthHistory: [] })
    }

    await Promise.allSettled(fetches)
    set({ detailLoading: false })
  },

  clearDetail: () => set({
    selectedCustomer: null, healthHistory: [], customerTickets: [], customerInsights: [],
  }),
}))

export default useCustomerStore
