import { create } from 'zustand'
import { workflowApi } from '../services/workflowApi'

const useWorkflowStore = create((set, get) => ({
  definitions: [],
  instances: [],
  isLoading: false,
  error: null,

  fetchDefinitions: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await workflowApi.getDefinitions()
      set({ definitions: data.workflows || data || [], isLoading: false })
    } catch (err) {
      console.error('[Workflows] Failed to fetch definitions:', err)
      set({ isLoading: false, error: err.message })
    }
  },

  fetchActive: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await workflowApi.getActive()
      set({ instances: data.instances || data || [], isLoading: false })
    } catch (err) {
      console.error('[Workflows] Failed to fetch active:', err)
      set({ isLoading: false, error: err.message })
    }
  },

  fetchAll: async () => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      console.log('[Workflows] Demo mode — loading seed data directly')
      try {
        const { seedWorkflowDefinitions, seedActiveWorkflows } = await import('../data/workflows')
        set({ definitions: seedWorkflowDefinitions, instances: seedActiveWorkflows, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    await Promise.allSettled([
      get().fetchDefinitions(),
      get().fetchActive(),
    ])
    set({ isLoading: false })
  },
}))

export default useWorkflowStore
