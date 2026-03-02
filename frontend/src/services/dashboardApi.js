import api from './api'

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getAgents: () => api.get('/dashboard/agents'),
  getEvents: (params) => api.get('/dashboard/events', { params }),
  getQuickHealth: () => api.get('/dashboard/quick-health'),
}
