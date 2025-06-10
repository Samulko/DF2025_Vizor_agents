"""Manual MCP HTTP server implementation.

This implements a complete MCP server using standard HTTP and JSON-RPC 2.0,
without relying on the StreamableHTTPSessionManager or FastMCP dependencies.

Features:
- Pure HTTP + SSE implementation
- JSON-RPC 2.0 compliance
- Server-Sent Events for streaming responses
- Session management for stateful connections
- Backward compatibility with older MCP clients

Based on the official MCP specification:
https://spec.modelcontextprotocol.io/specification/2025-03-26/basic/transports/
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass, asdict

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware

from .grasshopper_mcp.utils.communication import GrasshopperHttpClient

logger = logging.getLogger(__name__)


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


@dataclass
class JsonRpcResponse:
    """JSON-RPC 2.0 response."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class JsonRpcError:
    """JSON-RPC 2.0 error."""
    code: int
    message: str
    data: Optional[Any] = None


@dataclass
class MCPTool:
    """MCP Tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class MCPTextContent:
    """MCP Text content."""
    type: str = "text"
    text: str = ""


class MCPSession:
    """MCP session state."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.initialized = False
        self.client_info: Optional[Dict[str, Any]] = None
        self.server_capabilities: Dict[str, Any] = {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
            "experimental": {}
        }


class GrasshopperManualMCPServer:
    """Manual MCP HTTP server implementation."""
    
    def __init__(
        self,
        grasshopper_url: str = "http://localhost:8080",
        port: int = 8001,
        bridge_mode: bool = True
    ):
        """Initialize the manual MCP server.
        
        Args:
            grasshopper_url: URL of the Grasshopper HTTP server
            port: Port for the MCP server
            bridge_mode: If True, queue commands for bridge
        """
        self.grasshopper_url = grasshopper_url
        self.port = port
        self.bridge_mode = bridge_mode
        self.grasshopper_client = GrasshopperHttpClient(grasshopper_url)
        
        # Session management
        self.sessions: Dict[str, MCPSession] = {}
        
        # Bridge polling state
        self.pending_commands: List[Dict] = []
        self.command_results: Dict[str, Dict] = {}
        self.command_history: List[Dict] = []
        
        # Create FastAPI app
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title="Grasshopper Manual MCP Server",
            description="Manual MCP HTTP server for Grasshopper integration",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # MCP endpoints
        app.post("/mcp")(self.handle_mcp_request)
        app.get("/mcp")(self.handle_mcp_sse)
        
        # Bridge endpoints
        app.get("/grasshopper/pending_commands")(self.get_pending_commands)
        app.post("/grasshopper/command_result")(self.receive_command_result)
        app.get("/grasshopper/status")(self.get_bridge_status)
        
        # Health check
        app.get("/health")(self.health_check)
        
        return app
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "server": "grasshopper-manual-mcp",
            "bridge_mode": self.bridge_mode,
            "grasshopper_url": self.grasshopper_url,
            "active_sessions": len(self.sessions),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def handle_mcp_request(self, request: Request) -> JSONResponse:
        """Handle MCP HTTP POST requests."""
        try:
            # Get session ID from headers
            session_id = request.headers.get("mcp-session-id")
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Get or create session
            if session_id not in self.sessions:
                self.sessions[session_id] = MCPSession(session_id)
            
            session = self.sessions[session_id]
            session.last_activity = datetime.utcnow()
            
            # Parse JSON-RPC request
            body = await request.json()
            
            # Handle single request or batch
            if isinstance(body, list):
                # Batch request
                responses = []
                for req_data in body:
                    response = await self._process_jsonrpc_request(req_data, session)
                    if response:
                        responses.append(response)
                return JSONResponse(responses)
            else:
                # Single request
                response = await self._process_jsonrpc_request(body, session)
                if response:
                    return JSONResponse(asdict(response))
                else:
                    # Notification - no response
                    return JSONResponse({})
        
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            error_response = JsonRpcResponse(
                id=None,
                error=asdict(JsonRpcError(
                    code=-32603,
                    message="Internal error",
                    data=str(e)
                ))
            )
            return JSONResponse(asdict(error_response), status_code=500)
    
    async def handle_mcp_sse(self, request: Request) -> StreamingResponse:
        """Handle MCP SSE connections."""
        session_id = request.headers.get("mcp-session-id", str(uuid.uuid4()))
        
        async def event_stream():
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connection', 'session_id': session_id})}\n\n"
            
            # Keep connection alive
            try:
                while True:
                    # Send periodic heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except asyncio.CancelledError:
                logger.info(f"SSE connection closed for session {session_id}")
                # Clean up session if needed
                if session_id in self.sessions:
                    del self.sessions[session_id]
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    async def _process_jsonrpc_request(
        self, 
        req_data: Dict[str, Any], 
        session: MCPSession
    ) -> Optional[JsonRpcResponse]:
        """Process a single JSON-RPC request."""
        try:
            request = JsonRpcRequest(**req_data)
            
            # Handle different MCP methods
            if request.method == "initialize":
                return await self._handle_initialize(request, session)
            elif request.method == "tools/list":
                return await self._handle_tools_list(request, session)
            elif request.method == "tools/call":
                return await self._handle_tools_call(request, session)
            elif request.method == "resources/list":
                return await self._handle_resources_list(request, session)
            elif request.method == "prompts/list":
                return await self._handle_prompts_list(request, session)
            else:
                return JsonRpcResponse(
                    id=request.id,
                    error=asdict(JsonRpcError(
                        code=-32601,
                        message=f"Method not found: {request.method}"
                    ))
                )
        
        except Exception as e:
            logger.error(f"Error processing JSON-RPC request: {e}")
            return JsonRpcResponse(
                id=req_data.get("id"),
                error=asdict(JsonRpcError(
                    code=-32603,
                    message="Internal error",
                    data=str(e)
                ))
            )
    
    async def _handle_initialize(
        self, 
        request: JsonRpcRequest, 
        session: MCPSession
    ) -> JsonRpcResponse:
        """Handle MCP initialize request."""
        params = request.params or {}
        
        # Store client info
        session.client_info = params.get("clientInfo", {})
        session.initialized = True
        
        # Return server capabilities
        result = {
            "protocolVersion": "2025-03-26",
            "capabilities": session.server_capabilities,
            "serverInfo": {
                "name": "grasshopper-manual-mcp",
                "version": "1.0.0"
            }
        }
        
        logger.info(f"Initialized session {session.session_id} for client: {session.client_info}")
        
        return JsonRpcResponse(id=request.id, result=result)
    
    async def _handle_tools_list(
        self, 
        request: JsonRpcRequest, 
        session: MCPSession
    ) -> JsonRpcResponse:
        """Handle tools/list request."""
        if not session.initialized:
            return JsonRpcResponse(
                id=request.id,
                error=asdict(JsonRpcError(
                    code=-32002,
                    message="Session not initialized"
                ))
            )
        
        tools = [
            asdict(MCPTool(
                name="add_component",
                description="Add a component to the Grasshopper canvas",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "component_type": {
                            "type": "string",
                            "description": "Type of component (point, line, circle, slider, panel, etc.)"
                        },
                        "x": {
                            "type": "number",
                            "description": "X coordinate on the canvas"
                        },
                        "y": {
                            "type": "number",
                            "description": "Y coordinate on the canvas"
                        }
                    },
                    "required": ["component_type", "x", "y"]
                }
            )),
            asdict(MCPTool(
                name="connect_components",
                description="Connect two components in Grasshopper",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_id": {"type": "string", "description": "ID of the source component"},
                        "target_id": {"type": "string", "description": "ID of the target component"},
                        "source_param": {"type": "string", "description": "Source parameter name (optional)"},
                        "target_param": {"type": "string", "description": "Target parameter name (optional)"}
                    },
                    "required": ["source_id", "target_id"]
                }
            )),
            asdict(MCPTool(
                name="get_all_components",
                description="Get all components in the Grasshopper document",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )),
            asdict(MCPTool(
                name="set_component_value",
                description="Set the value of a component parameter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "component_id": {"type": "string", "description": "ID of the component"},
                        "parameter_name": {"type": "string", "description": "Name of the parameter to set"},
                        "value": {"description": "Value to set (string, number, or boolean)"}
                    },
                    "required": ["component_id", "parameter_name", "value"]
                }
            )),
            asdict(MCPTool(
                name="clear_document",
                description="Clear all components from the Grasshopper document",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )),
            asdict(MCPTool(
                name="save_document",
                description="Save the current Grasshopper document",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Filename to save to (optional)"}
                    },
                    "required": []
                }
            ))
        ]
        
        return JsonRpcResponse(id=request.id, result={"tools": tools})
    
    async def _handle_tools_call(
        self, 
        request: JsonRpcRequest, 
        session: MCPSession
    ) -> JsonRpcResponse:
        """Handle tools/call request."""
        if not session.initialized:
            return JsonRpcResponse(
                id=request.id,
                error=asdict(JsonRpcError(
                    code=-32002,
                    message="Session not initialized"
                ))
            )
        
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return JsonRpcResponse(
                id=request.id,
                error=asdict(JsonRpcError(
                    code=-32602,
                    message="Invalid params: 'name' is required"
                ))
            )
        
        try:
            # Execute the tool
            result = await self._execute_tool(tool_name, arguments)
            
            # Format result as MCP content
            content = [asdict(MCPTextContent(
                type="text",
                text=f"Tool '{tool_name}' executed. Result: {json.dumps(result, indent=2)}"
            ))]
            
            return JsonRpcResponse(
                id=request.id,
                result={"content": content}
            )
        
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}, Error: {str(e)}")
            return JsonRpcResponse(
                id=request.id,
                error=asdict(JsonRpcError(
                    code=-32603,
                    message=f"Tool execution failed: {str(e)}"
                ))
            )
    
    async def _handle_resources_list(
        self, 
        request: JsonRpcRequest, 
        session: MCPSession
    ) -> JsonRpcResponse:
        """Handle resources/list request."""
        return JsonRpcResponse(
            id=request.id,
            result={"resources": []}  # No resources for now
        )
    
    async def _handle_prompts_list(
        self, 
        request: JsonRpcRequest, 
        session: MCPSession
    ) -> JsonRpcResponse:
        """Handle prompts/list request."""
        return JsonRpcResponse(
            id=request.id,
            result={"prompts": []}  # No prompts for now
        )
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool."""
        logger.info(f"Executing tool: {tool_name} with args: {arguments} (bridge_mode: {self.bridge_mode})")
        
        if self.bridge_mode:
            return await self._handle_bridge_mode_tool(tool_name, arguments)
        else:
            # Direct execution mode
            if tool_name == "add_component":
                return await self._add_component(
                    component_type=arguments["component_type"],
                    x=arguments["x"],
                    y=arguments["y"]
                )
            elif tool_name == "connect_components":
                return await self._connect_components(
                    source_id=arguments["source_id"],
                    target_id=arguments["target_id"],
                    source_param=arguments.get("source_param"),
                    target_param=arguments.get("target_param")
                )
            elif tool_name == "get_all_components":
                return await self._get_all_components()
            elif tool_name == "set_component_value":
                return await self._set_component_value(
                    component_id=arguments["component_id"],
                    parameter_name=arguments["parameter_name"],
                    value=arguments["value"]
                )
            elif tool_name == "clear_document":
                return await self._clear_document()
            elif tool_name == "save_document":
                return await self._save_document(
                    filename=arguments.get("filename")
                )
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
    
    # Grasshopper operation methods
    async def _add_component(self, component_type: str, x: float, y: float) -> Dict[str, Any]:
        """Add a component to Grasshopper canvas."""
        try:
            response = await self.grasshopper_client.send_command(
                "add_component",
                {"component_type": component_type, "x": x, "y": y}
            )
            return response
        except Exception as e:
            logger.error(f"Failed to add component: {e}")
            return {"success": False, "error": str(e)}
    
    async def _connect_components(
        self, 
        source_id: str, 
        target_id: str, 
        source_param: Optional[str] = None, 
        target_param: Optional[str] = None
    ) -> Dict[str, Any]:
        """Connect two components in Grasshopper."""
        try:
            params = {"source_id": source_id, "target_id": target_id}
            if source_param:
                params["source_param"] = source_param
            if target_param:
                params["target_param"] = target_param
                
            response = await self.grasshopper_client.send_command("connect_components", params)
            return response
        except Exception as e:
            logger.error(f"Failed to connect components: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_all_components(self) -> Dict[str, Any]:
        """Get all components from Grasshopper document."""
        try:
            response = await self.grasshopper_client.send_command("get_all_components", {})
            return response
        except Exception as e:
            logger.error(f"Failed to get components: {e}")
            return {"success": False, "error": str(e)}
    
    async def _set_component_value(
        self, 
        component_id: str, 
        parameter_name: str, 
        value: Any
    ) -> Dict[str, Any]:
        """Set a component parameter value."""
        try:
            response = await self.grasshopper_client.send_command(
                "set_component_value",
                {
                    "component_id": component_id,
                    "parameter_name": parameter_name,
                    "value": value
                }
            )
            return response
        except Exception as e:
            logger.error(f"Failed to set component value: {e}")
            return {"success": False, "error": str(e)}
    
    async def _clear_document(self) -> Dict[str, Any]:
        """Clear the Grasshopper document."""
        try:
            response = await self.grasshopper_client.send_command("clear_document", {})
            return response
        except Exception as e:
            logger.error(f"Failed to clear document: {e}")
            return {"success": False, "error": str(e)}
    
    async def _save_document(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Save the Grasshopper document."""
        try:
            params = {}
            if filename:
                params["filename"] = filename
                
            response = await self.grasshopper_client.send_command("save_document", params)
            return response
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return {"success": False, "error": str(e)}
    
    # Bridge mode methods
    def _queue_command_for_bridge(self, command_type: str, parameters: Dict[str, Any]) -> str:
        """Queue a command for the bridge to execute."""
        command_id = str(uuid.uuid4())
        command = {
            "id": command_id,
            "type": command_type,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.pending_commands.append(command)
        logger.info(f"Queued command for bridge: {command_type} [{command_id}]")
        return command_id
    
    async def _handle_bridge_mode_tool(self, name: str, arguments: dict) -> Dict[str, Any]:
        """Handle tool execution in bridge mode (queue for bridge)."""
        try:
            command_id = self._queue_command_for_bridge(name, arguments)
            
            # Wait for result with timeout
            max_wait = 30  # seconds
            wait_interval = 0.5
            waited = 0
            
            while waited < max_wait:
                if command_id in self.command_results:
                    result = self.command_results[command_id]
                    # Clean up
                    del self.command_results[command_id]
                    return result
                
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Timeout
            return {"success": False, "error": "Bridge execution timeout"}
            
        except Exception as e:
            logger.error(f"Bridge mode tool execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Bridge API endpoints
    async def get_pending_commands(self) -> List[Dict]:
        """Get pending commands for bridge to execute."""
        commands = self.pending_commands.copy()
        self.pending_commands.clear()  # Clear after sending
        logger.info(f"Bridge requested commands: {len(commands)} pending")
        return commands
    
    async def receive_command_result(self, request: Request) -> Dict[str, str]:
        """Receive command execution result from bridge."""
        try:
            data = await request.json()
            command_id = data["command_id"]
            success = data["success"]
            result = data["result"]
            
            # Store result
            self.command_results[command_id] = {
                "success": success,
                "result": result
            }
            
            # Add to history
            self.command_history.append({
                "command_id": command_id,
                "success": success,
                "result": result,
                "timestamp": data.get("timestamp", datetime.utcnow().isoformat())
            })
            
            # Keep only last 100 in history
            if len(self.command_history) > 100:
                self.command_history.pop(0)
            
            logger.info(f"Received result from bridge: {command_id} - {'SUCCESS' if success else 'FAILED'}")
            return {"status": "received"}
            
        except Exception as e:
            logger.error(f"Error receiving command result: {e}")
            return {"error": str(e)}
    
    async def get_bridge_status(self) -> Dict[str, Any]:
        """Get bridge status and command history."""
        return {
            "pending_commands": len(self.pending_commands),
            "completed_commands": len(self.command_results),
            "command_history": self.command_history[-10:],  # Last 10
            "server_time": datetime.utcnow().isoformat(),
            "bridge_mode": self.bridge_mode,
            "active_sessions": len(self.sessions)
        }
    
    def run(self) -> None:
        """Run the MCP server."""
        logger.info(f"Starting Grasshopper Manual MCP server on port {self.port}")
        logger.info(f"MCP endpoint: http://127.0.0.1:{self.port}/mcp")
        logger.info(f"Bridge endpoints: http://127.0.0.1:{self.port}/grasshopper/")
        logger.info(f"Connected to Grasshopper at: {self.grasshopper_url}")
        logger.info(f"Bridge mode: {self.bridge_mode}")
        
        uvicorn.run(self.app, host="127.0.0.1", port=self.port)


def create_manual_mcp_server(
    grasshopper_url: str = "http://localhost:8080",
    port: int = 8001,
    bridge_mode: bool = True
) -> GrasshopperManualMCPServer:
    """Create a manual MCP server instance.
    
    Args:
        grasshopper_url: URL of the Grasshopper HTTP server
        port: Port for the MCP server
        bridge_mode: If True, queue commands for bridge
    
    Returns:
        Configured GrasshopperManualMCPServer instance
    """
    return GrasshopperManualMCPServer(
        grasshopper_url=grasshopper_url,
        port=port,
        bridge_mode=bridge_mode
    )


if __name__ == "__main__":
    import click
    
    @click.command()
    @click.option("--port", default=8001, help="Port to listen on")
    @click.option("--grasshopper-url", default="http://localhost:8080", help="Grasshopper server URL")
    @click.option("--bridge-mode/--direct-mode", default=True, help="Use bridge mode or direct mode")
    @click.option("--log-level", default="INFO", help="Logging level")
    def main(port: int, grasshopper_url: str, bridge_mode: bool, log_level: str):
        """Start the manual MCP server."""
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        
        server = create_manual_mcp_server(
            grasshopper_url=grasshopper_url,
            port=port,
            bridge_mode=bridge_mode
        )
        server.run()
    
    main()