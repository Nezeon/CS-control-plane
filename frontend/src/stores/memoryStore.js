import { create } from 'zustand'
import { memoryApi } from '../services/memoryApi'

const useMemoryStore = create((set, get) => ({
  episodicMemories: [],
  knowledgeEntries: [],
  searchResults: [],
  selectedAgent: null,
  selectedLane: 'support',
  searchQuery: '',
  isLoading: false,
  error: null,

  fetchEpisodicMemory: async (agentId) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await memoryApi.getEpisodic(agentId, {})
      const list = data.memories || data || []
      console.log('[Memory] fetchEpisodicMemory agent=%s →', agentId, list.length, 'memories, total:', data.total)
      set({ episodicMemories: list, isLoading: false })
    } catch (err) {
      console.error('[Memory] Failed to fetch episodic memory:', err?.response?.status, err?.response?.data || err.message)
      const token = localStorage.getItem('access_token')
      if (token === 'demo-token') {
        try {
          const { seedEpisodicMemories } = await import('../data/knowledge')
          const filtered = agentId
            ? seedEpisodicMemories.filter((m) => m.agent_id === agentId)
            : seedEpisodicMemories
          set({ episodicMemories: filtered, isLoading: false })
        } catch {
          set({ isLoading: false, error: err.message })
        }
      } else {
        set({ episodicMemories: [], isLoading: false, error: err.message })
      }
    }
  },

  fetchAllEpisodicMemories: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await memoryApi.getEpisodic('all', {})
      const list = data.memories || data || []
      console.log('[Memory] fetchAllEpisodicMemories →', list.length, 'memories, total:', data.total)
      set({ episodicMemories: list, isLoading: false })
    } catch (err) {
      console.error('[Memory] Failed to fetch all episodic memories:', err?.response?.status, err?.response?.data || err.message)
      const token = localStorage.getItem('access_token')
      if (token === 'demo-token') {
        try {
          const { seedEpisodicMemories } = await import('../data/knowledge')
          set({ episodicMemories: seedEpisodicMemories, isLoading: false })
        } catch {
          set({ isLoading: false, error: err.message })
        }
      } else {
        set({ episodicMemories: [], isLoading: false, error: err.message })
      }
    }
  },

  fetchKnowledge: async (lane) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await memoryApi.getKnowledge(lane, {})
      const list = data.entries || data || []
      console.log('[Memory] fetchKnowledge lane=%s →', lane, list.length, 'entries, total:', data.total)
      set({ knowledgeEntries: list, isLoading: false })
    } catch (err) {
      console.error('[Memory] Failed to fetch knowledge:', err?.response?.status, err?.response?.data || err.message)
      const token = localStorage.getItem('access_token')
      if (token === 'demo-token') {
        try {
          const { seedKnowledgeEntries } = await import('../data/knowledge')
          const filtered = lane && lane !== 'all'
            ? seedKnowledgeEntries.filter((k) => k.lane === lane)
            : seedKnowledgeEntries
          set({ knowledgeEntries: filtered, isLoading: false })
        } catch {
          set({ isLoading: false, error: err.message })
        }
      } else {
        set({ knowledgeEntries: [], isLoading: false, error: err.message })
      }
    }
  },

  searchMemory: async (query) => {
    if (!query || !query.trim()) {
      set({ searchResults: [], searchQuery: '' })
      return
    }
    set({ isLoading: true, searchQuery: query })
    try {
      const { data } = await memoryApi.search({ query })
      set({ searchResults: data.results || data || [], isLoading: false })
    } catch (err) {
      console.error('[Memory] Failed to search memory:', err)
      const token = localStorage.getItem('access_token')
      if (token === 'demo-token') {
        try {
          const { seedEpisodicMemories, seedKnowledgeEntries } = await import('../data/knowledge')
          const lowerQ = query.toLowerCase()
          const episodicMatches = seedEpisodicMemories.filter(
            (m) => m.content.toLowerCase().includes(lowerQ) || (m.customer_name && m.customer_name.toLowerCase().includes(lowerQ))
          )
          const knowledgeMatches = seedKnowledgeEntries.filter(
            (k) => k.content.toLowerCase().includes(lowerQ) || k.tags.some((t) => t.toLowerCase().includes(lowerQ))
          )
          set({
            searchResults: [
              ...episodicMatches.map((m) => ({ ...m, source: 'episodic' })),
              ...knowledgeMatches.map((k) => ({ ...k, source: 'semantic' })),
            ],
            isLoading: false,
          })
        } catch {
          set({ isLoading: false })
        }
      } else {
        set({ searchResults: [], isLoading: false })
      }
    }
  },

  setSelectedAgent: (agentId) => {
    set({ selectedAgent: agentId })
    if (agentId) get().fetchEpisodicMemory(agentId)
  },

  setSelectedLane: (lane) => {
    set({ selectedLane: lane })
    get().fetchKnowledge(lane)
  },

  setSearchQuery: (query) => set({ searchQuery: query }),

  // Fetch everything at once (for page load)
  fetchAll: async () => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      console.log('[Memory] Demo mode — loading seed data directly')
      try {
        const { seedEpisodicMemories, seedKnowledgeEntries } = await import('../data/knowledge')
        set({ episodicMemories: seedEpisodicMemories, knowledgeEntries: seedKnowledgeEntries, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    console.log('[Memory] Live mode — fetching episodic + knowledge from API')
    await Promise.allSettled([
      get().fetchAllEpisodicMemories(),
      get().fetchKnowledge(get().selectedLane),
    ])
    const state = get()
    console.log('[Memory] fetchAll done — episodic:', state.episodicMemories.length, 'knowledge:', state.knowledgeEntries.length)
    set({ isLoading: false })
  },

  // WebSocket handlers
  handleNewMemory: (memory) => {
    set((state) => ({
      episodicMemories: [memory, ...state.episodicMemories],
    }))
  },

  handleNewKnowledge: (entry) => {
    set((state) => ({
      knowledgeEntries: [entry, ...state.knowledgeEntries],
    }))
  },

  // Called by websocketStore for memory:knowledge_published events
  addKnowledgeEntry: (entry) => {
    set((state) => ({
      knowledgeEntries: [entry, ...state.knowledgeEntries],
    }))
  },
}))

export default useMemoryStore
