import api from './api'

export const customerApi = {
  list: (params) => api.get('/customers', { params }),
  listProspects: (params) => api.get('/customers', { params: { ...params, customer_type: 'prospect' } }),
  get: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post('/customers', data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  getHealthHistory: (id, params) => api.get(`/customers/${id}/health-history`, { params }),
  getInsights: (id, params) => api.get(`/customers/${id}/insights`, { params }),
  getTickets: (id, params) => api.get(`/customers/${id}/tickets`, { params }),
  getActionItems: (id) => api.get(`/customers/${id}/action-items`),
  getSimilarIssues: (id) => api.get(`/customers/${id}/similar-issues`),
}
