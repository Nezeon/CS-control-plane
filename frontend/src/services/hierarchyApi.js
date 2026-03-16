import api from './api'

export const hierarchyApi = {
  getHierarchy: () => api.get('/v2/hierarchy'),
  getAgents: (params) => api.get('/v2/hierarchy/agents', { params }),
  getAgent: (agentId) => api.get(`/v2/hierarchy/agents/${agentId}`),
  getAgentsByTier: (tier) => api.get('/v2/hierarchy/agents', { params: { tier } }),
  getAgentsByLane: (lane) => api.get('/v2/hierarchy/agents', { params: { lane } }),
}
