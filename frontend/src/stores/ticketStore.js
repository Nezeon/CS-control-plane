import { create } from 'zustand'
import { ticketApi } from '../services/ticketApi'

const useTicketStore = create((set, get) => ({
  tickets: [],
  total: 0,
  isLoading: false,
  error: null,

  search: '',
  status: '',
  severity: '',
  customer_id: '',
  ticket_type: '',
  sort_by: 'created',
  sort_order: 'desc',

  viewMode: 'table',

  selectedTicket: null,
  drawerOpen: false,
  detailLoading: false,
  similarTickets: [],
  similarLoading: false,

  setSearch: (search) => set({ search }),
  setStatus: (status) => set({ status }),
  setSeverity: (severity) => set({ severity }),
  setCustomerId: (customer_id) => set({ customer_id }),
  setTicketType: (ticket_type) => set({ ticket_type }),
  setSortBy: (sort_by) => set({ sort_by }),
  setSortOrder: (sort_order) => set({ sort_order }),
  setViewMode: (viewMode) => set({ viewMode }),

  fetchTickets: async () => {
    const { search, status, severity, customer_id, ticket_type, sort_by, sort_order } = get()
    set({ isLoading: true, error: null })
    try {
      const params = {}
      if (search) params.search = search
      if (status) params.status = status
      if (severity) params.severity = severity
      if (customer_id) params.customer_id = customer_id
      if (ticket_type) params.ticket_type = ticket_type
      if (sort_by) params.sort_by = sort_by
      if (sort_order) params.sort_order = sort_order
      const { data } = await ticketApi.list(params)
      const items = data.tickets || data.items || data || []
      set({ tickets: items, total: data.total ?? items.length, isLoading: false })
    } catch (err) {
      console.error('[Ticket] Failed to fetch tickets, loading seed data:', err)
      try {
        const { seedTickets } = await import('../data/tickets')
        set({ tickets: seedTickets, total: seedTickets.length, isLoading: false })
      } catch {
        set({ isLoading: false, error: err.message })
      }
    }
  },

  fetchTicketDetail: async (id) => {
    set({ detailLoading: true })
    try {
      const { data } = await ticketApi.get(id)
      set({ selectedTicket: data, detailLoading: false })
    } catch (err) {
      console.error('[Ticket] Failed to fetch ticket detail:', err)
      set({ detailLoading: false })
    }
  },

  fetchSimilarTickets: async (id) => {
    set({ similarLoading: true })
    try {
      const { data } = await ticketApi.getSimilar(id)
      set({ similarTickets: data.similar || data || [], similarLoading: false })
    } catch (err) {
      console.error('[Ticket] Failed to fetch similar tickets:', err)
      set({ similarLoading: false })
    }
  },

  openDrawer: (id) => {
    set({ drawerOpen: true, selectedTicket: null, similarTickets: [] })
    get().fetchTicketDetail(id)
    get().fetchSimilarTickets(id)
  },

  closeDrawer: () => {
    set({ drawerOpen: false, selectedTicket: null, similarTickets: [] })
  },

  updateTicketStatus: async (id, newStatus) => {
    set((state) => ({
      tickets: state.tickets.map((t) => (t.id === id ? { ...t, status: newStatus } : t)),
    }))
    try {
      await ticketApi.updateStatus(id, newStatus)
    } catch (err) {
      console.error('[Ticket] Failed to update ticket status:', err)
      get().fetchTickets()
    }
  },

  triggerTriage: async (id) => {
    try {
      const { data } = await ticketApi.triage(id)
      return data.task_id || data.id
    } catch (err) {
      console.error('[Ticket] Failed to trigger triage:', err)
      throw err
    }
  },

  triggerTroubleshoot: async (id) => {
    try {
      const { data } = await ticketApi.troubleshoot(id)
      return data.task_id || data.id
    } catch (err) {
      console.error('[Ticket] Failed to trigger troubleshoot:', err)
      throw err
    }
  },

  handleTicketTriaged: (data) => {
    set((state) => ({
      tickets: state.tickets.map((t) =>
        (t.id === data.ticket_id || t.jira_key === data.jira_id)
          ? { ...t, triage_result: data, has_triage_result: true, _justTriaged: true }
          : t
      ),
      selectedTicket:
        state.selectedTicket && (state.selectedTicket.id === data.ticket_id || state.selectedTicket.jira_key === data.jira_id)
          ? { ...state.selectedTicket, triage_result: data, has_triage_result: true }
          : state.selectedTicket,
    }))
  },
}))

export default useTicketStore
