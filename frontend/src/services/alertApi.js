import api from './api'

export const alertApi = {
  list: (params) => api.get('/alerts', { params }),
  acknowledge: (id) => api.put(`/alerts/${id}/acknowledge`),
  resolve: (id) => api.put(`/alerts/${id}/resolve`),
  dismiss: (id) => api.put(`/alerts/${id}/dismiss`),
}
