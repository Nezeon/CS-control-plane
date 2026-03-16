import axios from 'axios'
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
      console.log('[Auth] Login successful, token:', access_token.substring(0, 15) + '...')
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
      const isNetworkError = !err.response // No response = connection refused / timeout
      if (isNetworkError) {
        // Demo mode — backend truly unreachable
        console.warn('[Auth] Backend unreachable (network error), entering demo mode')
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
      } else {
        // Backend responded with an error (401, 422, etc.) — show it to user
        const detail = err.response?.data?.detail || 'Login failed'
        console.error('[Auth] Login failed:', detail)
        set({ error: detail, isLoading: false })
      }
    }
  },

  initialize: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.log('[Auth] No token found, not authenticated')
      set({ isLoading: false })
      return
    }

    // Demo mode — user explicitly chose demo, keep them in
    if (token === 'demo-token') {
      console.log('[Auth] Demo mode active')
      set({
        user: { id: 'demo-001', email: 'demo@hivepro.com', full_name: 'Demo User', role: 'cs_manager' },
        accessToken: token,
        isAuthenticated: true,
        isLoading: false,
      })
      return
    }

    console.log('[Auth] Validating stored token:', token.substring(0, 15) + '...')
    set({ isLoading: true, accessToken: token })
    try {
      const { data } = await authApi.me()
      console.log('[Auth] Token valid, user:', data.email)
      set({
        user: data,
        isAuthenticated: true,
        isLoading: false,
      })
      connectWebSocket(token)
    } catch {
      console.warn('[Auth] Token expired, attempting refresh...')
      // Try refresh
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await authApi.refresh(refreshToken)
          console.log('[Auth] Token refreshed successfully')
          localStorage.setItem('access_token', data.access_token)
          set({ accessToken: data.access_token })
          const me = await authApi.me()
          set({ user: me.data, isAuthenticated: true, isLoading: false })
          connectWebSocket(data.access_token)
          return
        } catch {
          console.warn('[Auth] Refresh failed, logging out')
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
