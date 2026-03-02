import { create } from 'zustand'
import { agentApi } from '../services/agentApi'

const useAgentStore = create((set, get) => ({
  agents: [],
  isLoading: false,
  error: null,
  orchestrationFlow: [],

  selectedAgent: null,
  selectedAgentDetail: null,
  agentLogs: [],
  logsLoading: false,
  brainPanelOpen: false,

  fetchAgents: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await agentApi.list()
      set({ agents: data.agents || data || [], isLoading: false })
    } catch (err) {
      console.error('[Agent] Failed to fetch agents, loading seed data:', err)
      try {
        const { seedAgentList } = await import('../data/agents')
        set({ agents: seedAgentList, isLoading: false })
      } catch {
        set({ isLoading: false, error: err.message })
      }
    }
  },

  fetchAgentDetail: async (name) => {
    try {
      const { data } = await agentApi.get(name)
      set({ selectedAgentDetail: data })
    } catch (err) {
      console.error('[Agent] Failed to fetch agent detail, loading seed data:', err)
      try {
        const { seedAgentList } = await import('../data/agents')
        const agent = seedAgentList.find((a) => a.name === name || a.agent_key === name)
        if (agent) set({ selectedAgentDetail: agent })
      } catch { /* seed unavailable */ }
    }
  },

  fetchAgentLogs: async (name, limit = 20) => {
    set({ logsLoading: true })
    try {
      const { data } = await agentApi.getLogs(name, { limit })
      set({ agentLogs: data.logs || data || [], logsLoading: false })
    } catch (err) {
      console.error('[Agent] Failed to fetch agent logs, loading seed data:', err)
      try {
        const { seedAgentLogs } = await import('../data/agents')
        const filtered = seedAgentLogs.filter((l) => l.agent_name === name).slice(0, limit)
        set({ agentLogs: filtered, logsLoading: false })
      } catch {
        set({ logsLoading: false })
      }
    }
  },

  fetchOrchestrationFlow: async (limit = 20) => {
    try {
      const { data } = await agentApi.getOrchestrationFlow({ limit })
      set({ orchestrationFlow: data.flow || data || [] })
    } catch (err) {
      console.error('[Agent] Failed to fetch orchestration flow, loading seed data:', err)
      try {
        const { seedOrchestrationFlow } = await import('../data/agents')
        set({ orchestrationFlow: seedOrchestrationFlow })
      } catch { /* seed unavailable */ }
    }
  },

  triggerAgent: async (name, customerId, context) => {
    try {
      const { data } = await agentApi.trigger(name, {
        customer_id: customerId,
        context: context || 'Manual trigger from UI',
      })
      return data.task_id || data.id
    } catch (err) {
      console.error('[Agent] Failed to trigger agent:', err)
      throw err
    }
  },

  selectAgent: (name) => {
    set({ selectedAgent: name, brainPanelOpen: true, selectedAgentDetail: null, agentLogs: [] })
    get().fetchAgentDetail(name)
    get().fetchAgentLogs(name)
  },

  closeBrainPanel: () => {
    set({ brainPanelOpen: false, selectedAgent: null, selectedAgentDetail: null, agentLogs: [] })
  },

  updateAgentStatus: (agentName, status, task) => {
    set((state) => {
      const agents = state.agents.map((a) =>
        a.name === agentName ? { ...a, status, current_task: task } : a
      )
      const selectedAgentDetail =
        state.selectedAgentDetail?.name === agentName
          ? { ...state.selectedAgentDetail, status, current_task: task }
          : state.selectedAgentDetail
      return { agents, selectedAgentDetail }
    })
  },
}))

export default useAgentStore
