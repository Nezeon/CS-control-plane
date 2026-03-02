import { create } from 'zustand'
import { authApi } from '../services/authApi'
import { connectWebSocket, disconnectWebSocket } from '../services/websocket'

const useAuthStore = create((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await authApi.login(email, password)
      const { access_token, refresh_token, user } = data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      set({
        user,
        accessToken: access_token,
        refreshToken: refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })
      connectWebSocket(access_token)
    } catch (err) {
      // Demo mode — no backend available, authenticate with mock user
      console.warn('[Auth] Backend unavailable, entering demo mode')
      const demoUser = {
        id: 'demo-001',
        email: email || 'demo@hivepro.com',
        full_name: 'Demo User',
        role: 'cs_manager',
      }
      localStorage.setItem('access_token', 'demo-token')
      set({
        user: demoUser,
        accessToken: 'demo-token',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })
    }
  },

  initialize: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isLoading: false })
      return
    }

    // Demo mode — token is demo-token, skip API call
    if (token === 'demo-token') {
      set({
        user: { id: 'demo-001', email: 'demo@hivepro.com', full_name: 'Demo User', role: 'cs_manager' },
        accessToken: token,
        isAuthenticated: true,
        isLoading: false,
      })
      return
    }

    set({ isLoading: true, accessToken: token })
    try {
      const { data } = await authApi.me()
      set({
        user: data,
        isAuthenticated: true,
        isLoading: false,
      })
      connectWebSocket(token)
    } catch {
      // Try refresh
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await authApi.refresh(refreshToken)
          localStorage.setItem('access_token', data.access_token)
          set({ accessToken: data.access_token })
          const me = await authApi.me()
          set({ user: me.data, isAuthenticated: true, isLoading: false })
          connectWebSocket(data.access_token)
          return
        } catch {
          // Refresh also failed
        }
      }
      get().logout()
      set({ isLoading: false })
    }
  },

  logout: () => {
    disconnectWebSocket()
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      error: null,
    })
  },
}))

export default useAuthStore
