import json
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from backend.app.services.events import BaseEvent

class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.unauthenticated_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.unauthenticated_connections.append(websocket)

    def authenticate_connection(self, websocket: WebSocket, user_id: int):
        if websocket in self.unauthenticated_connections:
            self.unauthenticated_connections.remove(websocket)
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int = None):
        if websocket in self.unauthenticated_connections:
            self.unauthenticated_connections.remove(websocket)
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

    async def broadcast_event(self, event: BaseEvent):
        payload = {
            "type": "NEW_NOTIFICATION",
            "event_type": event.event_type,
            "entity_id": event.entity_id
        }
        message = json.dumps(payload)
        
        for user_conns in self.active_connections.values():
            for connection in user_conns:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass

notification_manager = NotificationManager()
