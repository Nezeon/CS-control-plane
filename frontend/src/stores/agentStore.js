import { create } from 'zustand'
import { agentApi } from '../services/agentApi'
import { hierarchyApi } from '../services/hierarchyApi'

/** Normalize agent name to internal key (snake_case). Works for both backend keys and seed display names. */
const toAgentKey = (name) => {
  if (!name) return name
  // Already snake_case (backend format) — return as-is
  if (/^[a-z_]+$/.test(name)) return name
  // Display name → snake_case: "Fathom Agent" → "fathom_agent"
  return name.toLowerCase().replace(/\s+/g, '_').replace(/_agent$/, '')
}

const matchesAgent = (agent, key) =>
  agent.name === key || agent.agent_key === key || toAgentKey(agent.name) === key

/**
 * Build the 4-tier hierarchy structure from a flat agent list.
 * Returns { supervisor, lanes: { support, value, delivery }, foundation }
 */
const buildHierarchyFromAgents = (agents) => {
  const byKey = {}
  agents.forEach((a) => { byKey[a.agent_key || a.name] = a })

  const supervisor = agents.find((a) => a.tier === 1)?.agent_key || null
  const foundation = agents.filter((a) => a.tier === 4).map((a) => a.agent_key)

  const lanes = {}
  const leads = agents.filter((a) => a.tier === 2)
  leads.forEach((lead) => {
    const laneName = lead.lane
    const specialists = agents
      .filter((a) => a.tier === 3 && a.lane === laneName)
      .map((a) => a.agent_key)
    lanes[laneName] = {
      lead: lead.agent_key,
      specialists,
    }
  })

  return { supervisor, lanes, foundation }
}

const useAgentStore = create((set, get) => ({
  agents: [],
  hierarchy: null,
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
      // Use v2 hierarchy endpoint — returns full YAML profiles with tier, lane, traits, tools
      const { data } = await hierarchyApi.getAgents()
      const raw = data.agents || data || []
      const agents = raw.map((a) => ({
        ...a,
        agent_key: a.agent_key || a.id || a.name,
        name: a.id || a.name,
        human_name: a.human_name || a.name,
        display_name: a.display_name || a.codename || a.role || a.name,
      }))
      set({ agents, isLoading: false })
    } catch (err) {
      console.warn('[Agent] v2 hierarchy failed, trying v1 /api/agents:', err)
      try {
        const { data } = await agentApi.list()
        const agents = data.agents || data || []
        set({ agents, isLoading: false })
      } catch (err2) {
        console.error('[Agent] v1 also failed:', err2)
        set({ isLoading: false, error: err.message })
      }
    }
  },

  fetchHierarchy: async () => {
    try {
      const { data } = await hierarchyApi.getHierarchy()
      set({ hierarchy: data })
    } catch (err) {
      console.error('[Agent] Failed to fetch hierarchy, building from agents:', err)
      // Build hierarchy from already-loaded agents if available
      const agents = get().agents
      if (agents.length > 0) {
        set({ hierarchy: buildHierarchyFromAgents(agents) })
      }
    }
  },

  fetchAgentDetail: async (name) => {
    try {
      // Try v2 hierarchy endpoint first (has full YAML profile)
      const { data } = await hierarchyApi.getAgent(name)
      const detail = {
        ...data,
        agent_key: data.agent_key || data.id || name,
        name: data.id || data.name,
        human_name: data.human_name || data.name,
        display_name: data.display_name || data.codename || data.role || data.name,
      }
      set({ selectedAgentDetail: detail })
    } catch (err) {
      console.warn('[Agent] v2 detail failed, trying v1:', err)
      try {
        const { data } = await agentApi.get(name)
        set({ selectedAgentDetail: data })
      } catch (err2) {
        console.error('[Agent] v1 detail also failed:', err2)
        // Try to find from already-loaded agents
        const agent = get().agents.find((a) => a.name === name || a.agent_key === name)
        if (agent) set({ selectedAgentDetail: agent })
      }
    }
  },

  fetchAgentLogs: async (name, limit = 20) => {
    set({ logsLoading: true })
    try {
      const { data } = await agentApi.getLogs(name, { limit })
      set({ agentLogs: data.logs || data || [], logsLoading: false })
    } catch (err) {
      console.error('[Agent] Failed to fetch agent logs:', err)
      set({ agentLogs: [], logsLoading: false })
    }
  },

  fetchOrchestrationFlow: async (limit = 20) => {
    try {
      const { data } = await agentApi.getOrchestrationFlow({ limit })
      set({ orchestrationFlow: data.flow || data || [] })
    } catch (err) {
      console.error('[Agent] Failed to fetch orchestration flow:', err)
    }
  },

  // Fetch agents + hierarchy together (for page load)
  fetchAll: async () => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      console.log('[Agent] Demo mode — loading seed data directly')
      try {
        const { seedAgentList, seedHierarchy, seedOrchestrationFlow } = await import('../data/agents')
        set({
          agents: seedAgentList,
          hierarchy: seedHierarchy,
          orchestrationFlow: seedOrchestrationFlow,
          isLoading: false,
        })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    await Promise.allSettled([
      get().fetchAgents(),
      get().fetchHierarchy(),
      get().fetchOrchestrationFlow(),
    ])
    set({ isLoading: false })
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
    const key = toAgentKey(name)
    set({ selectedAgent: key, brainPanelOpen: true, selectedAgentDetail: null, agentLogs: [] })
    get().fetchAgentDetail(key)
    get().fetchAgentLogs(key)
  },

  closeBrainPanel: () => {
    set({ brainPanelOpen: false, selectedAgent: null, selectedAgentDetail: null, agentLogs: [] })
  },

  // Computed: get agents grouped by tier
  getAgentsByTier: (tier) => {
    return get().agents.filter((a) => a.tier === tier)
  },

  // Computed: get agents grouped by lane
  getAgentsByLane: (lane) => {
    return get().agents.filter((a) => a.lane === lane)
  },

  // Computed: get a single agent by key
  getAgentByKey: (key) => {
    return get().agents.find((a) => matchesAgent(a, key)) || null
  },

  updateAgentStatus: (agentName, status, task) => {
    const key = toAgentKey(agentName)
    set((state) => {
      const agents = state.agents.map((a) =>
        matchesAgent(a, key) ? { ...a, status, current_task: task } : a
      )
      const selectedAgentDetail =
        state.selectedAgentDetail && matchesAgent(state.selectedAgentDetail, key)
          ? { ...state.selectedAgentDetail, status, current_task: task }
          : state.selectedAgentDetail
      return { agents, selectedAgentDetail }
    })
  },
}))

export default useAgentStore
