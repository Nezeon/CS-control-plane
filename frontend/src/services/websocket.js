const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/api/ws'

let ws = null
let reconnectTimeout = null

export function connectWebSocket() {
  if (ws) { ws.onclose = null; ws.close() }

  ws = new WebSocket(WS_URL)

  ws.onopen = () => console.log('[WS] Connected')

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'pong') return
      // Broadcast to any listeners
      window.dispatchEvent(new CustomEvent('ws-message', { detail: data }))
    } catch {}
  }

  ws.onclose = () => {
    console.log('[WS] Disconnected, reconnecting in 5s...')
    reconnectTimeout = setTimeout(connectWebSocket, 5000)
  }
}

export function disconnectWebSocket() {
  if (reconnectTimeout) clearTimeout(reconnectTimeout)
  if (ws) { ws.onclose = null; ws.close(); ws = null }
}
