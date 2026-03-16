import { create } from 'zustand'
import { pipelineApi } from '../services/pipelineApi'

const usePipelineStore = create((set, get) => ({
  executions: [],
  activeExecutions: [],
  selectedExecution: null,
  isLoading: false,
  error: null,

  fetchActiveExecutions: async () => {
    set({ isLoading: true, error: null })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedActivePipelines } = await import('../data/pipelines')
        set({ activeExecutions: seedActivePipelines, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    try {
      const { data } = await pipelineApi.getActive()
      const list = data.executions || data || []
      set({ activeExecutions: list, isLoading: false })
    } catch (err) {
      console.error('[Pipeline] Failed to fetch active executions:', err?.response?.status, err?.response?.data || err.message)
      set({ activeExecutions: [], isLoading: false, error: err.message })
    }
  },

  fetchExecutions: async (agentId, params = {}) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await pipelineApi.getAgentExecutions(agentId, params)
      const list = data.executions || data || []
      console.log('[Pipeline] fetchExecutions agent=%s →', agentId, list.length, 'executions')
      set({ executions: list, isLoading: false })
    } catch (err) {
      console.error('[Pipeline] Failed to fetch executions:', err?.response?.status, err?.response?.data || err.message)
      const token = localStorage.getItem('access_token')
      if (token === 'demo-token') {
        try {
          const { seedPipelineExecutions } = await import('../data/pipelines')
          const filtered = agentId
            ? seedPipelineExecutions.filter((e) => e.agent_id === agentId)
            : seedPipelineExecutions
          set({ executions: filtered, isLoading: false })
        } catch {
          set({ isLoading: false, error: err.message })
        }
      } else {
        set({ executions: [], isLoading: false, error: err.message })
      }
    }
  },

  fetchAllExecutions: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await pipelineApi.getRecent({ limit: 20 })
      const list = data.executions || data || []
      console.log('[Pipeline] fetchAllExecutions (recent) →', list.length, 'executions, total:', data.total, list.length > 0 ? list.map((e) => `${e.agent_name}(${e.status})`) : '(empty)')
      set({ executions: list, isLoading: false })
    } catch (err) {
      console.error('[Pipeline] Failed to fetch all executions:', err?.response?.status, err?.response?.data || err.message)
      const token = localStorage.getItem('access_token')
      if (token === 'demo-token') {
        try {
          const { seedPipelineExecutions } = await import('../data/pipelines')
          set({ executions: seedPipelineExecutions, isLoading: false })
        } catch {
          set({ isLoading: false, error: err.message })
        }
      } else {
        set({ executions: [], isLoading: false, error: err.message })
      }
    }
  },

  fetchExecutionDetail: async (executionId) => {
    try {
      const { data } = await pipelineApi.getExecution(executionId)
      console.log('[Pipeline] fetchExecutionDetail →', executionId, 'status:', data.status, 'rounds:', data.rounds?.length)
      set({ selectedExecution: data })
    } catch (err) {
      console.error('[Pipeline] Failed to fetch execution detail:', err?.response?.status, err?.response?.data || err.message)
      const token = localStorage.getItem('access_token')
      if (token === 'demo-token') {
        try {
          const { seedPipelineExecutions, seedActivePipelines } = await import('../data/pipelines')
          const all = [...seedPipelineExecutions, ...seedActivePipelines]
          const execution = all.find((e) => e.execution_id === executionId)
          if (execution) set({ selectedExecution: execution })
        } catch { /* seed unavailable */ }
      }
    }
  },

  selectExecution: (execution) => set({ selectedExecution: execution }),

  clearSelection: () => set({ selectedExecution: null }),

  // Fetch everything at once (for page load)
  fetchAll: async () => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      console.log('[Pipeline] Demo mode — loading seed data directly')
      try {
        const { seedPipelineExecutions, seedActivePipelines } = await import('../data/pipelines')
        set({ executions: seedPipelineExecutions, activeExecutions: seedActivePipelines, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    console.log('[Pipeline] Live mode — fetching active + recent from API')
    await Promise.allSettled([
      get().fetchActiveExecutions(),
      get().fetchAllExecutions(),
    ])
    const state = get()
    console.log('[Pipeline] fetchAll done — active:', state.activeExecutions.length, 'executions:', state.executions.length)
    set({ isLoading: false })
  },

  // WebSocket handlers
  handleStageUpdate: (data) => {
    const { execution_id, round } = data
    set((state) => {
      const updateExecution = (exec) => {
        if (exec.execution_id !== execution_id) return exec
        const rounds = exec.rounds.map((r) =>
          r.round_number === round.round_number ? { ...r, ...round } : r
        )
        return { ...exec, rounds, current_stage: round.stage_type }
      }
      return {
        activeExecutions: state.activeExecutions.map(updateExecution),
        executions: state.executions.map(updateExecution),
        selectedExecution:
          state.selectedExecution?.execution_id === execution_id
            ? updateExecution(state.selectedExecution)
            : state.selectedExecution,
      }
    })
  },

  // WebSocket: update a specific stage status
  updateStageStatus: (executionId, stageName, status) => {
    set((state) => {
      const updateExec = (exec) => {
        if (exec.execution_id !== executionId) return exec
        const rounds = (exec.rounds || []).map((r) =>
          r.stage_type === stageName ? { ...r, status } : r
        )
        return { ...exec, rounds, current_stage: status === 'running' ? stageName : exec.current_stage }
      }
      return {
        activeExecutions: state.activeExecutions.map(updateExec),
        executions: state.executions.map(updateExec),
        selectedExecution:
          state.selectedExecution?.execution_id === executionId
            ? updateExec(state.selectedExecution)
            : state.selectedExecution,
      }
    })
  },

  // WebSocket: record a tool call within a stage
  addToolCall: (executionId, stageName, tool) => {
    set((state) => {
      const updateExec = (exec) => {
        if (exec.execution_id !== executionId) return exec
        const rounds = (exec.rounds || []).map((r) => {
          if (r.stage_type !== stageName) return r
          const tools = [...(r.tools_called || []), tool]
          return { ...r, tools_called: tools }
        })
        return { ...exec, rounds }
      }
      return {
        activeExecutions: state.activeExecutions.map(updateExec),
        executions: state.executions.map(updateExec),
      }
    })
  },

  handleExecutionComplete: (data) => {
    const { execution_id } = data
    set((state) => {
      const completed = state.activeExecutions.find((e) => e.execution_id === execution_id)
      return {
        activeExecutions: state.activeExecutions.filter((e) => e.execution_id !== execution_id),
        executions: completed
          ? [{ ...completed, status: 'completed', ...data }, ...state.executions]
          : state.executions,
      }
    })
  },
}))

export default usePipelineStore
