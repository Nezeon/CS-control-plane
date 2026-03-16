import api from './api'

export const memoryApi = {
  getEpisodic: (agentId, params) => api.get(`/v2/memory/${agentId}/episodic`, { params }),
  getWorking: (agentId) => api.get(`/v2/memory/${agentId}/working`),
  getKnowledge: (lane, params) => api.get(`/v2/memory/knowledge/${lane}`, { params }),
  search: (params) => api.get('/v2/memory/search', { params: { q: params.query || params.q, ...params, query: undefined } }),
}
