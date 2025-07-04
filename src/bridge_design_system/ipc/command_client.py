"""
TCP Command Client for Bridge Design System IPC.

Enables external interfaces (like voice chat) to send commands to the main
bridge design system via TCP socket communication.
"""

import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CommandResponse:
    """Response from bridge design system."""
    task_id: str
    success: bool
    message: str
    timestamp: str
    

class BridgeCommandClient:
    """
    TCP client for sending bridge design commands to main.py command server.
    
    Used by voice interfaces and other external systems to communicate
    with the bridge design system.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8082, timeout: float = 120.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        
        # Connection state
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        
        logger.info(f"🔗 Bridge command client initialized for {host}:{port}")
    
    async def connect(self) -> bool:
        """Connect to the bridge design command server."""
        if self._connected:
            return True
            
        try:
            logger.info(f"🔌 Connecting to bridge command server at {self.host}:{self.port}...")
            
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0  # Connection timeout
            )
            
            self._connected = True
            logger.info("✅ Connected to bridge command server")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Connection timeout to {self.host}:{self.port}")
            return False
        except ConnectionRefusedError:
            logger.error(f"❌ Connection refused to {self.host}:{self.port}")
            logger.error("💡 Make sure main.py is running with --enable-command-server")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to command server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the command server."""
        if not self._connected:
            return
            
        try:
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
                
            self._reader = None
            self._writer = None
            self._connected = False
            
            logger.info("🔌 Disconnected from bridge command server")
            
        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")
    
    async def send_bridge_design_request(self, user_request: str) -> CommandResponse:
        """
        Send a bridge design request to the main system.
        
        Args:
            user_request: The processed/paraphrased user request
            
        Returns:
            CommandResponse with the result from the bridge design system
        """
        if not self._connected:
            if not await self.connect():
                raise ConnectionError("Failed to connect to bridge command server")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())[:8]
        
        # Create request
        request = {
            "type": "bridge_design_request",
            "task_id": task_id,
            "user_request": user_request,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📤 Sending bridge design request {task_id}")
        logger.info(f"📝 Request: {user_request[:100]}...")
        
        try:
            # Send request
            await self._send_message(request)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(
                self._receive_message(),
                timeout=self.timeout
            )
            
            # Parse response
            if response.get("type") == "bridge_design_response":
                result = CommandResponse(
                    task_id=response["task_id"],
                    success=response["success"],
                    message=response["message"],
                    timestamp=response["timestamp"]
                )
                
                logger.info(f"📨 Received response for {task_id}: {'✅ success' if result.success else '❌ failed'}")
                return result
                
            elif response.get("type") == "bridge_design_error":
                logger.error(f"❌ Server error for {task_id}: {response.get('message', 'Unknown error')}")
                return CommandResponse(
                    task_id=task_id,
                    success=False,
                    message=f"Server error: {response.get('message', 'Unknown error')}",
                    timestamp=datetime.now().isoformat()
                )
            else:
                logger.error(f"❌ Unexpected response type: {response.get('type')}")
                return CommandResponse(
                    task_id=task_id,
                    success=False,
                    message=f"Unexpected response type: {response.get('type')}",
                    timestamp=datetime.now().isoformat()
                )
                
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout waiting for response to {task_id}")
            return CommandResponse(
                task_id=task_id,
                success=False,
                message=f"Request timeout after {self.timeout}s",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"❌ Error sending request {task_id}: {e}")
            # Try to reconnect for next request
            await self.disconnect()
            return CommandResponse(
                task_id=task_id,
                success=False,
                message=f"Communication error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send JSON message to server."""
        if not self._writer:
            raise ConnectionError("Not connected to server")
            
        # Serialize message
        message_json = json.dumps(message)
        message_bytes = message_json.encode('utf-8')
        
        # Send length first, then data
        length_bytes = len(message_bytes).to_bytes(4, byteorder='big')
        
        self._writer.write(length_bytes)
        self._writer.write(message_bytes)
        await self._writer.drain()
        
        logger.debug(f"📤 Sent message: {message.get('type', 'unknown')}")
    
    async def _receive_message(self) -> Dict[str, Any]:
        """Receive JSON message from server."""
        if not self._reader:
            raise ConnectionError("Not connected to server")
            
        # Read message length (4 bytes)
        length_data = await self._reader.read(4)
        if not length_data:
            raise ConnectionError("Server closed connection")
            
        message_length = int.from_bytes(length_data, byteorder='big')
        
        # Read actual message
        message_data = await self._reader.read(message_length)
        if not message_data:
            raise ConnectionError("Server closed connection")
        
        # Parse JSON
        message_json = message_data.decode('utf-8')
        message = json.loads(message_json)
        
        logger.debug(f"📨 Received message: {message.get('type', 'unknown')}")
        return message
    
    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        return self._connected
    
    async def ping(self) -> bool:
        """Test connection to server."""
        try:
            if not self._connected:
                return await self.connect()
            return True
        except Exception as e:
            logger.error(f"❌ Ping failed: {e}")
            return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Global client instance for voice interface
_command_client: Optional[BridgeCommandClient] = None


def get_command_client() -> BridgeCommandClient:
    """Get or create the global command client instance."""
    global _command_client
    
    if _command_client is None:
        _command_client = BridgeCommandClient()
    
    return _command_client


async def send_bridge_design_request(user_request: str) -> CommandResponse:
    """
    Convenience function to send a bridge design request.
    
    Args:
        user_request: The processed/paraphrased user request
        
    Returns:
        CommandResponse with the result
    """
    client = get_command_client()
    return await client.send_bridge_design_request(user_request)