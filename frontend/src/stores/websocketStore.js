import { create } from 'zustand'
import useDashboardStore from './dashboardStore'
import useAlertStore from './alertStore'
import useCustomerStore from './customerStore'
import useAgentStore from './agentStore'
import useTicketStore from './ticketStore'
import useInsightStore from './insightStore'
import usePipelineStore from './pipelineStore'
import useMessageStore from './messageStore'
import useMemoryStore from './memoryStore'
import useChatStore from './chatStore'

const useWebsocketStore = create((set) => ({
  connected: false,
  reconnectAttempts: 0,
  lastMessage: null,

  setConnected: (connected) => set({ connected, reconnectAttempts: connected ? 0 : undefined }),
  setReconnectAttempts: (n) => set({ reconnectAttempts: n }),

  handleMessage: (message) => {
    set({ lastMessage: message })

    switch (message.type) {
      case 'agent_status':
        useDashboardStore.getState().updateAgentStatus(
          message.data.agent,
          message.data.status,
          message.data.task
        )
        useAgentStore.getState().updateAgentStatus(
          message.data.agent,
          message.data.status,
          message.data.task
        )
        break

      case 'event_processed':
        useDashboardStore.getState().prependEvent({
          id: message.data.event_id,
          event_type: message.data.event_type,
          customer_name: message.data.customer,
          routed_to: message.data.routed_to,
          status: message.data.status,
          created_at: new Date().toISOString(),
          description: `${message.data.event_type} routed to ${message.data.routed_to}`,
        })
        break

      case 'new_alert':
        useAlertStore.getState().addAlert(message.data)
        break

      case 'health_update':
        useDashboardStore.getState().updateQuickHealth(
          message.data.customer_id,
          message.data.new_score,
          message.data.risk_level
        )
        useCustomerStore.getState().handleHealthUpdate(
          message.data.customer_id,
          message.data.new_score,
          message.data.risk_level
        )
        break

      case 'ticket_triaged':
        useTicketStore.getState().handleTicketTriaged(message.data)
        break

      case 'insight_ready':
        useInsightStore.getState().handleInsightReady(message.data)
        break

      // ── Pipeline events ──────────────────────────────────────────────
      case 'pipeline:started':
        usePipelineStore.getState().handleStageUpdate?.(message.data)
        break

      case 'pipeline:completed':
        usePipelineStore.getState().handleExecutionComplete?.(message.data)
        break

      case 'pipeline:stage_started':
        usePipelineStore.getState().updateStageStatus?.(
          message.data.execution_id,
          message.data.stage,
          'running'
        )
        break

      case 'pipeline:stage_completed':
        usePipelineStore.getState().updateStageStatus?.(
          message.data.execution_id,
          message.data.stage,
          'completed'
        )
        break

      case 'pipeline:tool_called':
        usePipelineStore.getState().addToolCall?.(
          message.data.execution_id,
          message.data.stage,
          message.data.tool
        )
        break

      // ── Delegation / messaging events ────────────────────────────────
      case 'delegation:task_assigned':
        useMessageStore.getState().addIncomingMessage?.({
          ...message.data,
          message_type: 'task_assignment',
          direction: 'down',
          created_at: new Date().toISOString(),
        })
        useChatStore.getState().handleDelegationEvent('task_assigned', message.data)
        break

      case 'delegation:deliverable':
        useMessageStore.getState().addIncomingMessage?.({
          ...message.data,
          message_type: 'deliverable',
          direction: 'up',
          created_at: new Date().toISOString(),
        })
        useChatStore.getState().handleDelegationEvent('deliverable', message.data)
        break

      case 'delegation:escalation':
        useMessageStore.getState().addIncomingMessage?.({
          ...message.data,
          message_type: 'escalation',
          direction: 'up',
          created_at: new Date().toISOString(),
        })
        useChatStore.getState().handleDelegationEvent('escalation', message.data)
        if (message.data.alert) {
          useAlertStore.getState().addAlert(message.data.alert)
        }
        break

      case 'delegation:rework_requested':
        useChatStore.getState().handleDelegationEvent('rework_requested', message.data)
        break

      case 'delegation:auto_escalation':
        useChatStore.getState().handleDelegationEvent('auto_escalation', message.data)
        break

      case 'delegation:quality_gate_failed':
        useChatStore.getState().handleDelegationEvent('quality_gate_failed', message.data)
        break

      case 'delegation:brief_created':
        useChatStore.getState().handleDelegationEvent('brief_created', message.data)
        break

      // ── Memory events ────────────────────────────────────────────────
      case 'memory:knowledge_published':
        useMemoryStore.getState().addKnowledgeEntry?.({
          ...message.data,
          created_at: new Date().toISOString(),
        })
        break

      // ── Chat events ────────────────────────────────────────────────
      case 'chat:processing':
        useChatStore.getState().handleChatProcessing(message.data)
        break

      case 'chat:stage_update':
        useChatStore.getState().handleChatStageUpdate(message.data)
        break

      case 'chat:agent_working':
        useChatStore.getState().handleChatAgentWorking(message.data)
        break

      case 'chat:message_complete':
        useChatStore.getState().handleChatMessageComplete(message.data)
        break

      case 'chat:message_failed':
        useChatStore.getState().handleChatMessageFailed(message.data)
        break

      default:
        break
    }
  },
}))

export default useWebsocketStore
