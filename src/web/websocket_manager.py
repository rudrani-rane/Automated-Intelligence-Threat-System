"""
WebSocket Manager for Real-Time Updates
Handles WebSocket connections, broadcasts, and live notifications
"""

from typing import Dict, Set, List
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        # Active connections by connection_id
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Subscriptions: {topic: set of connection_ids}
        self.subscriptions: Dict[str, Set[str]] = {
            'threat_updates': set(),
            'watchlist': set(),
            'alerts': set(),
            'system_status': set()
        }
        
        # User connections: {user_email: connection_id}
        self.user_connections: Dict[str, str] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, 
                     user_email: str = None) -> None:
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            'connected_at': datetime.utcnow().isoformat(),
            'user_email': user_email,
            'subscriptions': []
        }
        
        if user_email:
            self.user_connections[user_email] = connection_id
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_email or 'anonymous'})")
        
        # Send welcome message
        await self.send_personal_message({
            'type': 'connection',
            'status': 'connected',
            'connection_id': connection_id,
            'timestamp': datetime.utcnow().isoformat()
        }, connection_id)
    
    def disconnect(self, connection_id: str) -> None:
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            # Remove from all subscriptions
            for topic in self.subscriptions:
                self.subscriptions[topic].discard(connection_id)
            
            # Remove from user connections
            metadata = self.connection_metadata.get(connection_id, {})
            user_email = metadata.get('user_email')
            if user_email and self.user_connections.get(user_email) == connection_id:
                del self.user_connections[user_email]
            
            # Remove connection
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    def subscribe(self, connection_id: str, topic: str) -> bool:
        """Subscribe connection to a topic"""
        if topic not in self.subscriptions:
            logger.warning(f"Unknown topic: {topic}")
            return False
        
        self.subscriptions[topic].add(connection_id)
        
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]['subscriptions'].append(topic)
        
        logger.info(f"Connection {connection_id} subscribed to {topic}")
        return True
    
    def unsubscribe(self, connection_id: str, topic: str) -> bool:
        """Unsubscribe connection from a topic"""
        if topic not in self.subscriptions:
            return False
        
        self.subscriptions[topic].discard(connection_id)
        
        if connection_id in self.connection_metadata:
            subscriptions = self.connection_metadata[connection_id]['subscriptions']
            if topic in subscriptions:
                subscriptions.remove(topic)
        
        logger.info(f"Connection {connection_id} unsubscribed from {topic}")
        return True
    
    async def send_personal_message(self, message: dict, connection_id: str) -> None:
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_user(self, message: dict, user_email: str) -> None:
        """Send message to specific user (by email)"""
        connection_id = self.user_connections.get(user_email)
        if connection_id:
            await self.send_personal_message(message, connection_id)
    
    async def broadcast(self, message: dict, topic: str = None) -> None:
        """Broadcast message to all connections or topic subscribers"""
        if topic and topic in self.subscriptions:
            # Broadcast to topic subscribers
            connection_ids = list(self.subscriptions[topic])
        else:
            # Broadcast to all
            connection_ids = list(self.active_connections.keys())
        
        disconnected = []
        
        for connection_id in connection_ids:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    async def broadcast_threat_update(self, asteroid_data: dict) -> None:
        """Broadcast threat score update"""
        message = {
            'type': 'threat_update',
            'data': asteroid_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast(message, topic='threat_updates')
    
    async def broadcast_alert(self, alert_data: dict) -> None:
        """Broadcast high-priority alert"""
        message = {
            'type': 'alert',
            'data': alert_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast(message, topic='alerts')
    
    async def broadcast_system_status(self, status_data: dict) -> None:
        """Broadcast system status update"""
        message = {
            'type': 'system_status',
            'data': status_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast(message, topic='system_status')
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_subscription_stats(self) -> Dict[str, int]:
        """Get subscription statistics"""
        return {
            topic: len(subscribers) 
            for topic, subscribers in self.subscriptions.items()
        }
    
    def get_connection_info(self, connection_id: str) -> Dict:
        """Get connection metadata"""
        return self.connection_metadata.get(connection_id, {})


# Global connection manager instance
connection_manager = ConnectionManager()


async def handle_client_message(message: dict, connection_id: str) -> None:
    """Handle incoming client messages"""
    message_type = message.get('type')
    
    if message_type == 'subscribe':
        topic = message.get('topic')
        if topic:
            success = connection_manager.subscribe(connection_id, topic)
            await connection_manager.send_personal_message({
                'type': 'subscription_response',
                'topic': topic,
                'success': success
            }, connection_id)
    
    elif message_type == 'unsubscribe':
        topic = message.get('topic')
        if topic:
            success = connection_manager.unsubscribe(connection_id, topic)
            await connection_manager.send_personal_message({
                'type': 'unsubscription_response',
                'topic': topic,
                'success': success
            }, connection_id)
    
    elif message_type == 'ping':
        # Heartbeat
        await connection_manager.send_personal_message({
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat()
        }, connection_id)
    
    elif message_type == 'get_stats':
        # Send connection statistics
        await connection_manager.send_personal_message({
            'type': 'stats',
            'data': {
                'total_connections': connection_manager.get_connection_count(),
                'subscriptions': connection_manager.get_subscription_stats(),
                'your_connection': connection_manager.get_connection_info(connection_id)
            }
        }, connection_id)


async def broadcast_periodic_updates():
    """Background task to broadcast periodic updates"""
    from src.web.state import THREAT, SPKIDS, MOID
    from src.web.sbdb_client import get_asteroid_name
    
    while True:
        try:
            # Wait 30 seconds
            await asyncio.sleep(30)
            
            # Get top 5 threats
            top_indices = THREAT.argsort()[-5:][::-1]
            
            top_threats = []
            for idx in top_indices:
                spkid = int(SPKIDS[idx])
                top_threats.append({
                    'spkid': spkid,
                    'name': get_asteroid_name(spkid),
                    'threat_score': float(THREAT[idx]),
                    'moid': float(MOID[idx])
                })
            
            # Broadcast to watchlist subscribers
            await connection_manager.broadcast({
                'type': 'watchlist_update',
                'data': top_threats,
                'timestamp': datetime.utcnow().isoformat()
            }, topic='watchlist')
            
            # System status
            await connection_manager.broadcast_system_status({
                'active_connections': connection_manager.get_connection_count(),
                'subscriptions': connection_manager.get_subscription_stats(),
                'last_update': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(30)
