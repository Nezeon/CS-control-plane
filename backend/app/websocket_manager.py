import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict

from fastapi import WebSocket

logger = logging.getLogger("websocket")


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str | None = None) -> str:
        """Accept connection and register it. Returns connection_id."""
        await websocket.accept()
        connection_id = client_id or str(uuid.uuid4())
        async with self._lock:
            self.active_connections[connection_id] = websocket
        logger.info(
            f"WebSocket connected: {connection_id} "
            f"(total: {len(self.active_connections)})"
        )
        return connection_id

    async def disconnect(self, connection_id: str):
        """Remove a connection by ID."""
        async with self._lock:
            self.active_connections.pop(connection_id, None)
        logger.info(
            f"WebSocket disconnected: {connection_id} "
            f"(total: {len(self.active_connections)})"
        )

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast a typed event to ALL connected clients."""
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        disconnected = []
        async with self._lock:
            for conn_id, ws in self.active_connections.items():
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(conn_id)
        for conn_id in disconnected:
            await self.disconnect(conn_id)

    async def send_to(self, connection_id: str, event_type: str, data: dict):
        """Send to a specific connection."""
        ws = self.active_connections.get(connection_id)
        if ws:
            try:
                await ws.send_text(json.dumps({
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }))
            except Exception:
                await self.disconnect(connection_id)


manager = ConnectionManager()
