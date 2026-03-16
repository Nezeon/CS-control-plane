import api from './api'

export const messageApi = {
  getMessages: (params) => api.get('/v2/messages', { params }),
  getThread: (threadId) => api.get(`/v2/messages/thread/${threadId}`),
  getAgentMessages: (agentId) => api.get(`/v2/messages/agent/${agentId}`),
  getEventMessages: (eventId) => api.get(`/v2/messages/event/${eventId}`),
}
