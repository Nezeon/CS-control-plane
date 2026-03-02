import { create } from 'zustand'
import useDashboardStore from './dashboardStore'
import useAlertStore from './alertStore'
import useCustomerStore from './customerStore'
import useAgentStore from './agentStore'
import useTicketStore from './ticketStore'
import useInsightStore from './insightStore'

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

      default:
        break
    }
  },
}))

export default useWebsocketStore
