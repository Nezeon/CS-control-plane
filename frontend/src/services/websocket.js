import useWebsocketStore from '../stores/websocketStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/api/ws'
const MAX_RECONNECT_ATTEMPTS = 10
const MAX_BACKOFF = 30000

let ws = null
let reconnectTimeout = null
let heartbeatInterval = null
let reconnectAttempts = 0
let currentToken = null

function getBackoffDelay() {
  return Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_BACKOFF)
}

export function connectWebSocket(token) {
  currentToken = token
  if (ws) {
    ws.onclose = null
    ws.close()
  }

  ws = new WebSocket(`${WS_URL}?token=${token}`)
  const store = useWebsocketStore.getState()

  ws.onopen = () => {
    reconnectAttempts = 0
    store.setConnected(true)
    store.setReconnectAttempts(0)

    // Heartbeat
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    heartbeatInterval = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'pong') return
      store.handleMessage(data)
    } catch (e) {
      console.error('[WS] Parse error:', e)
    }
  }

  ws.onclose = () => {
    store.setConnected(false)
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }

    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS && currentToken) {
      reconnectAttempts++
      store.setReconnectAttempts(reconnectAttempts)
      const delay = getBackoffDelay()
      reconnectTimeout = setTimeout(() => connectWebSocket(currentToken), delay)
    }
  }

  ws.onerror = () => {
    // onclose will fire after onerror
  }
}

export function disconnectWebSocket() {
  currentToken = null
  reconnectAttempts = MAX_RECONNECT_ATTEMPTS // prevent reconnect
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }
  if (ws) {
    ws.onclose = null
    ws.close()
    ws = null
  }
  useWebsocketStore.getState().setConnected(false)
}
