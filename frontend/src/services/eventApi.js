import api from './api'

export const eventApi = {
  list: (params) => api.get('/events', { params }),
  create: (data) => api.post('/events', data),
}
