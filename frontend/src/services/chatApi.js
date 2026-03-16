import api from './api'

export const chatApi = {
  send: (message, customerId, conversationId) =>
    api.post('/chat/send', {
      message,
      customer_id: customerId || undefined,
      conversation_id: conversationId || undefined,
    }),

  getConversations: (limit = 20, offset = 0) =>
    api.get('/chat/conversations', { params: { limit, offset } }),

  getConversation: (id) =>
    api.get(`/chat/conversations/${id}`),

  archiveConversation: (id) =>
    api.delete(`/chat/conversations/${id}`),
}
