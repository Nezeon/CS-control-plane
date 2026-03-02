import api from './api'

export const agentApi = {
  list: () => api.get('/agents'),
  get: (name) => api.get(`/agents/${name}`),
  getLogs: (name, params) => api.get(`/agents/${name}/logs`, { params }),
  getOrchestrationFlow: (params) => api.get('/agents/orchestration-flow', { params }),
  trigger: (name, data) => api.post(`/agents/${name}/trigger`, data),
}
