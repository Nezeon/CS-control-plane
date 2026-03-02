import api from './api'

export const healthApi = {
  getScores: (params) => api.get('/health/scores', { params }),
  getAtRisk: () => api.get('/health/at-risk'),
  getTrends: (params) => api.get('/health/trends', { params }),
  runCheck: () => api.post('/health/run-check'),
}
