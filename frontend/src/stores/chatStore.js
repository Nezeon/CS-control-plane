import { create } from 'zustand'
import { chatApi } from '../services/chatApi'

const useChatStore = create((set, get) => ({
  // State
  conversations: [],
  activeConversation: null, // { id, title, customer_name, ... }
  messages: [], // Messages in the active conversation
  isLoading: false,
  isSending: false,
  processingMessageId: null,
  activeAgents: [], // [{ agent_id, agent_name, stage }] — currently working
  processingStages: [], // [{ stage, stage_label, stage_number, total_stages, detail }]
  delegationEvents: [], // [{ type, from_agent, to_agent, ... , timestamp }] — real-time thinking chain

  // ── Fetch conversations list ──────────────────────────────────────────
  fetchConversations: async () => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      try {
        const { seedChatConversations } = await import('../data/chat')
        set({ conversations: seedChatConversations, isLoading: false })
      } catch {
        set({ isLoading: false })
      }
      return
    }
    try {
      const { data } = await chatApi.getConversations()
      set({ conversations: data.conversations || [], isLoading: false })
    } catch (err) {
      console.error('[Chat] Failed to fetch conversations:', err)
      set({ isLoading: false })
    }
  },

  // ── Load a specific conversation with messages ─────────────────────────
  loadConversation: async (conversationId) => {
    set({ isLoading: true })
    const token = localStorage.getItem('access_token')

    // Find the conversation in list
    const conv = get().conversations.find((c) => c.id === conversationId)

    if (token === 'demo-token') {
      try {
        const { seedChatMessages, seedChatConversations } = await import('../data/chat')
        const seedConv = seedChatConversations.find((c) => c.id === conversationId)
        set({
          activeConversation: seedConv || conv || { id: conversationId },
          messages: seedChatMessages[conversationId] || [],
          isLoading: false,
        })
      } catch {
        set({ activeConversation: conv || { id: conversationId }, messages: [], isLoading: false })
      }
      return
    }

    try {
      const { data } = await chatApi.getConversation(conversationId)
      set({
        activeConversation: {
          id: data.id,
          title: data.title,
          customer_id: data.customer_id,
          customer_name: data.customer_name,
          status: data.status,
          created_at: data.created_at,
        },
        messages: data.messages || [],
        isLoading: false,
      })
    } catch (err) {
      console.error('[Chat] Failed to load conversation:', err)
      set({ activeConversation: conv || { id: conversationId }, messages: [], isLoading: false })
    }
  },

  // ── Send a message ─────────────────────────────────────────────────────
  sendMessage: async (text, customerId) => {
    const { activeConversation } = get()
    const conversationId = activeConversation?.id

    // Add optimistic user message immediately
    const tempUserMsg = {
      id: `temp_${Date.now()}`,
      conversation_id: conversationId || 'new',
      role: 'user',
      content: text,
      agents_involved: [],
      pipeline_status: null,
      execution_metadata: {},
      created_at: new Date().toISOString(),
    }

    // Add optimistic thinking message
    const tempAssistantMsg = {
      id: `temp_assistant_${Date.now()}`,
      conversation_id: conversationId || 'new',
      role: 'assistant',
      content: 'Thinking...',
      agents_involved: [],
      pipeline_status: 'processing',
      execution_metadata: {},
      created_at: new Date().toISOString(),
    }

    set((state) => ({
      messages: [...state.messages, tempUserMsg, tempAssistantMsg],
      isSending: true,
      processingMessageId: tempAssistantMsg.id,
    }))

    // Demo mode: simulate agent response
    const token = localStorage.getItem('access_token')
    if (token === 'demo-token') {
      setTimeout(() => {
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === tempAssistantMsg.id
              ? {
                  ...m,
                  content:
                    'I\'m currently in demo mode. In production, this query would be routed through the agent orchestration pipeline:\n\n' +
                    '1. **Naveen Kapoor** (Supervisor) would analyze your query\n' +
                    '2. The relevant **Lane Lead** would coordinate the response\n' +
                    '3. **Specialist agents** would fetch and analyze the data\n\n' +
                    'Connect to the backend to see the full AI-powered response.',
                  pipeline_status: 'completed',
                  agents_involved: ['cso_orchestrator'],
                }
              : m
          ),
          isSending: false,
          processingMessageId: null,
          activeAgents: [],
        }))
      }, 1500)
      return
    }

    try {
      const { data } = await chatApi.send(text, customerId, conversationId)

      // Update conversation context
      if (!conversationId || conversationId === 'new') {
        const newConv = {
          id: data.conversation_id,
          title: text.substring(0, 60),
          status: 'active',
          created_at: new Date().toISOString(),
        }
        set((state) => ({
          activeConversation: newConv,
          conversations: [newConv, ...state.conversations],
          messages: state.messages.map((m) => ({
            ...m,
            conversation_id: data.conversation_id,
          })),
        }))
      }

      // API returns immediately with status="processing"
      // The actual answer arrives via WebSocket (chat:message_complete)
      // Set isSending to false so the input is re-enabled, but keep
      // processingMessageId so the "Thinking..." bubble stays visible
      set({ isSending: false })
    } catch (err) {
      console.error('[Chat] Send failed:', err)
      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === tempAssistantMsg.id
            ? {
                ...m,
                content: 'Failed to process your request. Please try again.',
                pipeline_status: 'failed',
              }
            : m
        ),
        isSending: false,
        processingMessageId: null,
        activeAgents: [],
      }))
    }
  },

  // ── Start a new conversation ───────────────────────────────────────────
  newConversation: () => {
    set({
      activeConversation: null,
      messages: [],
      processingMessageId: null,
      activeAgents: [],
      processingStages: [],
      delegationEvents: [],
      isSending: false,
    })
  },

  // ── WebSocket handlers ─────────────────────────────────────────────────

  handleChatProcessing: (data) => {
    const { activeConversation } = get()
    if (activeConversation && String(activeConversation.id) === String(data.conversation_id)) {
      set({
        isSending: true,
        processingMessageId: data.message_id,
      })
    }
  },

  handleChatAgentWorking: (data) => {
    const { activeConversation } = get()
    if (activeConversation && String(activeConversation.id) === String(data.conversation_id)) {
      set((state) => ({
        activeAgents: [
          ...state.activeAgents.filter((a) => a.agent_id !== data.agent_id),
          { agent_id: data.agent_id, agent_name: data.agent_name, stage: data.stage },
        ],
      }))
    }
  },

  handleChatMessageComplete: (data) => {
    const { activeConversation, processingMessageId } = get()
    if (activeConversation && String(activeConversation.id) === String(data.conversation_id)) {
      set((state) => ({
        messages: state.messages.map((m) => {
          // Replace the processing message (either temp or real ID)
          if (
            m.id === processingMessageId ||
            m.id === data.message_id ||
            (m.pipeline_status === 'processing' && m.role === 'assistant')
          ) {
            return {
              ...m,
              id: data.message_id || m.id,
              content: data.content,
              agents_involved: data.agents_involved || [],
              pipeline_status: 'completed',
              event_id: data.event_id || m.event_id,
              execution_metadata: data.execution_metadata || {},
            }
          }
          return m
        }),
        isSending: false,
        processingMessageId: null,
        activeAgents: [],
        processingStages: [],
        delegationEvents: [],
      }))
    }
  },

  handleChatMessageFailed: (data) => {
    const { activeConversation, processingMessageId } = get()
    if (activeConversation && String(activeConversation.id) === String(data.conversation_id)) {
      set((state) => ({
        messages: state.messages.map((m) => {
          if (
            m.id === processingMessageId ||
            m.id === data.message_id ||
            (m.pipeline_status === 'processing' && m.role === 'assistant')
          ) {
            return {
              ...m,
              content: data.error || 'Failed to process request.',
              pipeline_status: 'failed',
            }
          }
          return m
        }),
        isSending: false,
        processingMessageId: null,
        activeAgents: [],
        processingStages: [],
      }))
    }
  },

  handleChatStageUpdate: (data) => {
    const { activeConversation } = get()
    if (activeConversation && String(activeConversation.id) === String(data.conversation_id)) {
      set((state) => ({
        processingStages: [
          ...state.processingStages.filter((s) => s.stage !== data.stage),
          {
            stage: data.stage,
            stage_label: data.stage_label,
            stage_number: data.stage_number,
            total_stages: data.total_stages,
            detail: data.detail,
          },
        ],
      }))
    }
  },

  // ── Delegation event handlers (ThinkingChain) ─────────────────────────
  handleDelegationEvent: (eventType, data) => {
    set((state) => ({
      delegationEvents: [
        ...state.delegationEvents,
        { type: eventType, ...data, timestamp: new Date().toISOString() },
      ],
    }))
  },
}))

export default useChatStore
