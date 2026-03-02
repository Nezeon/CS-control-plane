import api from './api'

export const ticketApi = {
  list: (params) => api.get('/tickets', { params }),
  get: (id) => api.get(`/tickets/${id}`),
  updateStatus: (id, status) => api.put(`/tickets/${id}/status`, { status }),
  assign: (id, assignedToId) => api.put(`/tickets/${id}/assign`, { assigned_to_id: assignedToId }),
  triage: (id) => api.post(`/tickets/${id}/triage`),
  troubleshoot: (id) => api.post(`/tickets/${id}/troubleshoot`),
  getSimilar: (id) => api.get(`/tickets/${id}/similar`),
}
