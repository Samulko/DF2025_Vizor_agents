"""
TCP Command Server for Bridge Design System IPC.

Enables the main.py bridge design system to receive commands from external 
voice interfaces via TCP socket communication.
"""

import asyncio
import json
import logging
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CommandRequest:
    """Represents a command request from external interface."""
    task_id: str
    user_request: str
    timestamp: str
    type: str = "bridge_design_request"


@dataclass  
class CommandResponse:
    """Represents a response to external interface."""
    task_id: str
    success: bool
    message: str
    timestamp: str
    type: str = "bridge_design_response"
    
    def to_json(self) -> str:
        """Convert response to JSON string."""
        return json.dumps({
            "type": self.type,
            "task_id": self.task_id,
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp
        })


class BridgeCommandServer:
    """
    TCP server that receives bridge design commands from external interfaces.
    
    Integrates with main.py's interactive loop to inject commands as if 
    they were typed by the user in the CLI.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8082):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.command_handler: Optional[Callable[[str], Any]] = None
        self.running = False
        
        # Track active connections and pending requests
        self.active_connections: Dict[str, asyncio.StreamWriter] = {}
        self.pending_requests: Dict[str, CommandRequest] = {}
        
        logger.info(f"🚀 Bridge command server initialized on {host}:{port}")
    
    def set_command_handler(self, handler: Callable[[str], Any]):
        """Set the function that processes bridge design commands."""
        self.command_handler = handler
        logger.info("✅ Command handler registered")
    
    async def start(self):
        """Start the TCP command server."""
        if self.running:
            logger.warning("Command server already running")
            return
            
        try:
            self.server = await asyncio.start_server(
                self._handle_client,
                self.host,
                self.port
            )
            self.running = True
            
            logger.info(f"🚀 Bridge command server started on {self.host}:{self.port}")
            logger.info("📡 Ready to receive commands from voice interfaces")
            
            # Keep server running
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"❌ Failed to start command server: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the TCP command server."""
        if not self.running:
            return
            
        self.running = False
        
        # Close all active connections
        for conn_id, writer in self.active_connections.items():
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.warning(f"Error closing connection {conn_id}: {e}")
        
        self.active_connections.clear()
        
        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        logger.info("🛑 Bridge command server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming client connection and commands."""
        client_addr = writer.get_extra_info('peername')
        conn_id = f"{client_addr[0]}:{client_addr[1]}_{int(time.time())}"
        
        logger.info(f"🔗 New connection from {client_addr} (ID: {conn_id})")
        self.active_connections[conn_id] = writer
        
        try:
            while self.running:
                # Read message length (4 bytes)
                length_data = await reader.read(4)
                if not length_data:
                    break
                    
                message_length = int.from_bytes(length_data, byteorder='big')
                if message_length > 10000:  # 10KB limit
                    logger.warning(f"Message too large: {message_length} bytes")
                    break
                
                # Read actual message
                message_data = await reader.read(message_length)
                if not message_data:
                    break
                
                try:
                    # Parse JSON command
                    command_json = message_data.decode('utf-8')
                    command_dict = json.loads(command_json)
                    
                    logger.info(f"📨 Received command from {conn_id}: {command_dict.get('type', 'unknown')}")
                    
                    # Process command
                    await self._process_command(conn_id, command_dict, writer)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON from {conn_id}: {e}")
                    await self._send_error(writer, "invalid_json", "Invalid JSON format")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing command from {conn_id}: {e}")
                    await self._send_error(writer, "processing_error", str(e))
                    
        except asyncio.IncompleteReadError:
            logger.info(f"📪 Connection {conn_id} closed by client")
        except Exception as e:
            logger.error(f"❌ Error handling client {conn_id}: {e}")
        finally:
            # Cleanup
            if conn_id in self.active_connections:
                del self.active_connections[conn_id]
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            logger.info(f"🔌 Connection {conn_id} closed")
    
    async def _process_command(self, conn_id: str, command_dict: Dict[str, Any], writer: asyncio.StreamWriter):
        """Process incoming command and send response."""
        try:
            # Validate command structure
            if command_dict.get("type") != "bridge_design_request":
                await self._send_error(writer, "invalid_type", "Expected bridge_design_request")
                return
                
            required_fields = ["task_id", "user_request", "timestamp"]
            for field in required_fields:
                if field not in command_dict:
                    await self._send_error(writer, "missing_field", f"Missing required field: {field}")
                    return
            
            # Create command request
            request = CommandRequest(
                task_id=command_dict["task_id"],
                user_request=command_dict["user_request"],
                timestamp=command_dict["timestamp"]
            )
            
            logger.info(f"🎯 Processing bridge design request {request.task_id}")
            logger.info(f"📝 User request: {request.user_request[:100]}...")
            
            # Store pending request
            self.pending_requests[request.task_id] = request
            
            # Execute command using registered handler
            if not self.command_handler:
                await self._send_error(writer, "no_handler", "No command handler registered")
                return
            
            # Call the bridge design system
            try:
                response = self.command_handler(request.user_request)
                
                # Create response
                command_response = CommandResponse(
                    task_id=request.task_id,
                    success=response.success if hasattr(response, 'success') else True,
                    message=response.message if hasattr(response, 'message') else str(response),
                    timestamp=datetime.now().isoformat()
                )
                
                # Send response back
                await self._send_response(writer, command_response)
                
                logger.info(f"✅ Command {request.task_id} completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Command handler failed for {request.task_id}: {e}")
                error_response = CommandResponse(
                    task_id=request.task_id,
                    success=False,
                    message=f"Command processing failed: {str(e)}",
                    timestamp=datetime.now().isoformat()
                )
                await self._send_response(writer, error_response)
            
            # Cleanup
            if request.task_id in self.pending_requests:
                del self.pending_requests[request.task_id]
                
        except Exception as e:
            logger.error(f"❌ Error in _process_command: {e}")
            await self._send_error(writer, "internal_error", str(e))
    
    async def _send_response(self, writer: asyncio.StreamWriter, response: CommandResponse):
        """Send response back to client."""
        try:
            response_json = response.to_json()
            response_bytes = response_json.encode('utf-8')
            
            # Send length first, then data
            length_bytes = len(response_bytes).to_bytes(4, byteorder='big')
            writer.write(length_bytes)
            writer.write(response_bytes)
            await writer.drain()
            
            logger.debug(f"📤 Sent response for task {response.task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send response: {e}")
    
    async def _send_error(self, writer: asyncio.StreamWriter, error_type: str, error_message: str):
        """Send error response to client."""
        try:
            error_response = {
                "type": "bridge_design_error",
                "error_type": error_type,
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            
            error_json = json.dumps(error_response)
            error_bytes = error_json.encode('utf-8')
            
            length_bytes = len(error_bytes).to_bytes(4, byteorder='big')
            writer.write(length_bytes)
            writer.write(error_bytes)
            await writer.drain()
            
            logger.warning(f"📤 Sent error: {error_type} - {error_message}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current server status."""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "active_connections": len(self.active_connections),
            "pending_requests": len(self.pending_requests),
            "connection_ids": list(self.active_connections.keys())
        }


# Global server instance
_command_server: Optional[BridgeCommandServer] = None


def get_command_server() -> Optional[BridgeCommandServer]:
    """Get the global command server instance."""
    return _command_server


def start_command_server(host: str = "localhost", port: int = 8082, command_handler: Optional[Callable] = None) -> BridgeCommandServer:
    """Start the global command server."""
    global _command_server
    
    if _command_server and _command_server.running:
        logger.warning("Command server already running")
        return _command_server
    
    _command_server = BridgeCommandServer(host, port)
    
    if command_handler:
        _command_server.set_command_handler(command_handler)
    
    return _command_server


async def stop_command_server():
    """Stop the global command server."""
    global _command_server
    
    if _command_server:
        await _command_server.stop()
        _command_server = None