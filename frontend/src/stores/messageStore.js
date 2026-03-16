import { create } from 'zustand'
import { messageApi } from '../services/messageApi'

/** Derive thread summaries from a flat list of messages grouped by thread_id */
function _deriveThreads(messages) {
  const threadMap = {}
  for (const msg of messages) {
    const tid = msg.thread_id || msg.id
    if (!threadMap[tid]) {
      threadMap[tid] = {
        thread_id: tid,
        event_type: msg.event_type || null,
        event_id: msg.event_id || null,
        customer_name: msg.customer_name || null,
        summary: (msg.content || '').substring(0, 120),
        agents_involved: new Set(),
        message_count: 0,
        priority: msg.priority >= 8 ? 'critical' : msg.priority >= 6 ? 'high' : 'medium',
        status: msg.status || 'completed',
        created_at: msg.created_at,
        last_message_at: msg.created_at,
      }
    }
    const thread = threadMap[tid]
    thread.message_count++
    if (msg.from_agent) thread.agents_involved.add(msg.from_agent)
    if (msg.to_agent) thread.agents_involved.add(msg.to_agent)
    if (msg.created_at > thread.last_message_at) {
      thread.last_message_at = msg.created_at
    }
  }
  return Object.values(threadMap)
    .map((t) => ({ ...t, agents_involved: [...t.agents_involved] }))
    .sort((a, b) => new Date(b.last_message_at) - new Date(a.last_message_at))
}

const useMessageStore = create((set, get) => ({
  threads: [],
  messages: [],
  selectedThread: null,
  selectedThreadMessages: [],
  filters: { type: 'all', agent: null, lane: null, priority: null },
  isLoading: false,
  error: null,

  fetchThreads: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await messageApi.getMessages({ limit: 100 })
      const rawMessages = data.messages || data || []
      // Derive threads from flat messages by grouping on thread_id
      const threads = _deriveThreads(rawMessages)
      set({ threads, isLoading: false })
    } catch (err) {
      console.error('[Messages] Failed to fetch threads:', err)
      set({ isLoading: false, error: err.message })
    }
  },

  fetchMessages: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await messageApi.getMessages({})
      set({ messages: data.messages || data || [], isLoading: false })
    } catch (err) {
      console.error('[Messages] Failed to fetch messages:', err)
      set({ isLoading: false, error: err.message })
    }
  },

  fetchThread: async (threadId) => {
    try {
      const { data } = await messageApi.getThread(threadId)
      set({ selectedThreadMessages: data.messages || data || [] })
    } catch (err) {
      console.error('[Messages] Failed to fetch thread:', err)
      set({ selectedThreadMessages: [] })
    }
  },

  selectThread: (threadId) => {
    const thread = get().threads.find((t) => t.thread_id === threadId) || null
    set({ selectedThread: thread, selectedThreadMessages: [] })
    if (threadId) get().fetchThread(threadId)
  },

  clearThreadSelection: () => {
    set({ selectedThread: null, selectedThreadMessages: [] })
  },

  setFilter: (key, value) => {
    set((state) => ({ filters: { ...state.filters, [key]: value } }))
  },

  resetFilters: () => {
    set({ filters: { type: 'all', agent: null, lane: null, priority: null } })
  },

  // Computed: filtered threads based on current filters
  getFilteredThreads: () => {
    const { threads, filters } = get()
    return threads.filter((thread) => {
      if (filters.priority && filters.priority !== 'all' && thread.priority !== filters.priority) return false
      if (filters.agent && !thread.agents_involved?.includes(filters.agent)) return false
      return true
    })
  },

  // Computed: filtered messages based on current filters
  getFilteredMessages: () => {
    const { messages, filters } = get()
    return messages.filter((msg) => {
      if (filters.type !== 'all' && msg.message_type !== filters.type) return false
      if (filters.agent && msg.from_agent !== filters.agent && msg.to_agent !== filters.agent) return false
      if (filters.priority && filters.priority !== 'all' && msg.priority !== filters.priority) return false
      return true
    })
  },

  // Fetch everything at once (for page load)
  fetchAll: async () => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      console.log('[Messages] Demo mode — loading seed data directly')
      try {
        const { seedConversationThreads, seedMessages } = await import('../data/conversations')
        set({ threads: seedConversationThreads, messages: seedMessages, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    await Promise.allSettled([
      get().fetchThreads(),
      get().fetchMessages(),
    ])
    set({ isLoading: false })
  },

  // WebSocket handlers
  handleNewMessage: (message) => {
    set((state) => ({
      messages: [message, ...state.messages],
      selectedThreadMessages:
        state.selectedThread?.thread_id === message.thread_id
          ? [...state.selectedThreadMessages, message]
          : state.selectedThreadMessages,
    }))
  },

  // Called by websocketStore for delegation events
  addIncomingMessage: (message) => {
    set((state) => {
      const newMessages = [message, ...state.messages]
      const updatedThreadMessages =
        state.selectedThread?.thread_id === message.thread_id
          ? [...state.selectedThreadMessages, message]
          : state.selectedThreadMessages

      // Also update thread preview if it exists
      const updatedThreads = state.threads.map((t) => {
        if (t.thread_id === message.thread_id) {
          return { ...t, last_message: message, updated_at: message.created_at }
        }
        return t
      })

      return {
        messages: newMessages,
        threads: updatedThreads,
        selectedThreadMessages: updatedThreadMessages,
      }
    })
  },
}))

export default useMessageStore
