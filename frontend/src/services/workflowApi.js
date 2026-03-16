import api from './api'

export const workflowApi = {
  getDefinitions: () => api.get('/v2/workflows/'),
  getActive: () => api.get('/v2/workflows/active'),
  getInstanceStatus: (instanceId) => api.get(`/v2/workflows/${instanceId}/status`),
}
