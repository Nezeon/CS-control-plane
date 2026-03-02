import api from './api'

export const insightApi = {
  list: (params) => api.get('/insights', { params }),
  get: (id) => api.get(`/insights/${id}`),
  syncFathom: () => api.post('/insights/sync-fathom'),
  getSentimentTrend: (params) => api.get('/insights/sentiment-trend', { params }),
  getActionItems: (params) => api.get('/insights/action-items', { params }),
  updateActionItem: (id, data) => api.put(`/insights/action-items/${id}`, data),
}
