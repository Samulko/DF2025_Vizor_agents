"""Agent status broadcasting system for real-time visualization."""
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol


class AgentStatus(Enum):
    """Agent status types for visualization."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTIVE = "active"
    DELEGATING = "delegating"
    ERROR = "error"


class StatusMessage:
    """Standardized status message format."""
    
    def __init__(
        self,
        agent_name: str,
        status: AgentStatus,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.agent_name = agent_name
        self.status = status
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AgentStatusBroadcaster:
    """Manages real-time agent status broadcasting to visualization clients."""
    
    def __init__(self, port: int = 8765):
        """Initialize the status broadcaster.
        
        Args:
            port: WebSocket server port
        """
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.logger = logging.getLogger(__name__)
        self.server = None
        self.running = False
        
        # Store recent messages for new clients
        self.recent_messages: List[StatusMessage] = []
        self.max_recent_messages = 50
    
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        self.logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send recent messages to new client
        for message in self.recent_messages[-10:]:  # Last 10 messages
            try:
                await websocket.send(message.to_json())
            except websockets.exceptions.ConnectionClosed:
                break
    
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """Unregister a WebSocket client."""
        self.clients.discard(websocket)
        self.logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_status(
        self,
        agent_name: str,
        status: AgentStatus,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Broadcast agent status to all connected clients."""
        status_message = StatusMessage(agent_name, status, message, metadata)
        
        # Store for recent messages
        self.recent_messages.append(status_message)
        if len(self.recent_messages) > self.max_recent_messages:
            self.recent_messages.pop(0)
        
        # Broadcast to all clients
        if self.clients:
            json_message = status_message.to_json()
            disconnected_clients = set()
            
            for client in self.clients:
                try:
                    await client.send(json_message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    self.logger.error(f"Error sending to client: {e}")
                    disconnected_clients.add(client)
            
            # Clean up disconnected clients
            for client in disconnected_clients:
                self.clients.discard(client)
        
        # Log the status update
        self.logger.info(f"[{agent_name}] {status.value}: {message}")
    
    def broadcast_status_sync(
        self,
        agent_name: str,
        status: AgentStatus,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Synchronous wrapper for broadcasting status."""
        # Store the message regardless of server running state
        status_message = StatusMessage(agent_name, status, message, metadata)
        self.recent_messages.append(status_message)
        if len(self.recent_messages) > self.max_recent_messages:
            self.recent_messages.pop(0)
        
        # Log the status update
        self.logger.info(f"[{agent_name}] {status.value}: {message}")
        
        # If server is running, also broadcast to clients
        if self.running:
            # Create a task for the broadcast
            asyncio.create_task(
                self.broadcast_status(agent_name, status, message, metadata)
            )
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket client connection."""
        await self.register_client(websocket)
        try:
            # Keep connection alive and handle any incoming messages
            async for message in websocket:
                # For now, we only broadcast, but we could handle client commands here
                self.logger.debug(f"Received message from client: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    
    async def start_server(self):
        """Start the WebSocket server."""
        self.logger.info(f"Starting status broadcaster on port {self.port}")
        self.server = await websockets.serve(
            self.handle_client,
            "localhost",
            self.port
        )
        self.running = True
        self.logger.info(f"Status broadcaster running on ws://localhost:{self.port}")
        self.logger.info("WebSocket server ready for client connections")
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            self.running = False
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("Status broadcaster stopped")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current broadcaster status."""
        return {
            "running": self.running,
            "port": self.port,
            "connected_clients": len(self.clients),
            "recent_messages_count": len(self.recent_messages)
        }


# Global broadcaster instance
_broadcaster: Optional[AgentStatusBroadcaster] = None


def get_broadcaster() -> AgentStatusBroadcaster:
    """Get the global status broadcaster instance."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = AgentStatusBroadcaster()
    return _broadcaster


def broadcast_agent_status(
    agent_name: str,
    status: AgentStatus,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Convenience function to broadcast agent status."""
    broadcaster = get_broadcaster()
    broadcaster.broadcast_status_sync(agent_name, status, message, metadata)


# Convenience functions for common status updates
def broadcast_agent_thinking(agent_name: str, task: str):
    """Broadcast that an agent is thinking about a task."""
    broadcast_agent_status(
        agent_name,
        AgentStatus.THINKING,
        f"Analyzing: {task[:100]}...",
        {"task_preview": task[:100]}
    )


def broadcast_agent_active(agent_name: str, action: str, tool_used: Optional[str] = None):
    """Broadcast that an agent is actively working."""
    metadata = {}
    if tool_used:
        metadata["tool_used"] = tool_used
    
    broadcast_agent_status(
        agent_name,
        AgentStatus.ACTIVE,
        f"Executing: {action}",
        metadata
    )


def broadcast_agent_delegating(agent_name: str, target_agent: str, task: str):
    """Broadcast that an agent is delegating to another agent."""
    broadcast_agent_status(
        agent_name,
        AgentStatus.DELEGATING,
        f"Delegating to {target_agent}: {task[:50]}...",
        {"target_agent": target_agent, "task_preview": task[:50]}
    )


def broadcast_agent_idle(agent_name: str):
    """Broadcast that an agent is now idle."""
    broadcast_agent_status(
        agent_name,
        AgentStatus.IDLE,
        "Ready for next task"
    )


def broadcast_agent_error(agent_name: str, error_message: str):
    """Broadcast that an agent encountered an error."""
    broadcast_agent_status(
        agent_name,
        AgentStatus.ERROR,
        f"Error: {error_message}",
        {"error": error_message}
    )