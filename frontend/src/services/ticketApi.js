import api from './api'

export const ticketApi = {
  get: (id) => api.get(`/tickets/${id}`),
}
