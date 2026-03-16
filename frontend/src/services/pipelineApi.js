import api from './api'

export const pipelineApi = {
  getActive: () => api.get('/v2/pipeline/active'),
  getRecent: (params) => api.get('/v2/pipeline/recent', { params }),
  getAgentExecutions: (agentId, params) => api.get(`/v2/pipeline/agent/${agentId}`, { params }),
  getExecution: (executionId) => api.get(`/v2/pipeline/${executionId}`),
  getRounds: (executionId, params) => api.get(`/v2/pipeline/${executionId}/rounds`, { params }),
}
