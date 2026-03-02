import api from './api'

export const reportApi = {
  list: (params) => api.get('/reports', { params }),
  get: (id) => api.get(`/reports/${id}`),
  getAnalytics: () => api.get('/reports/analytics'),
  generate: (data) => api.post('/reports/generate', data),
}
