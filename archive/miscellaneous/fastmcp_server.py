"""FastMCP-based MCP server for Grasshopper integration.

This implements a proper MCP server using the official FastMCP framework,
avoiding the StreamableHTTPSessionManager issues by using the recommended
approach from the MCP Python SDK.

Features:
- Official MCP protocol compliance with JSON-RPC 2.0
- Streamable HTTP transport (replaces older SSE transport)
- Bridge mode for Grasshopper integration
- Direct mode for immediate Grasshopper calls
- Comprehensive tool set for Grasshopper operations
"""
import asyncio
import contextlib
import logging
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.requests import Request

# Try to import FastMCP, fallback to manual implementation
try:
    from mcp.server.fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

# Always import these for potential fallback use
try:
    from mcp.server.lowlevel import Server
    import mcp.types as types
    MANUAL_MCP_AVAILABLE = True
except ImportError:
    MANUAL_MCP_AVAILABLE = False
    Server = None
    types = None

from .grasshopper_mcp.utils.communication import GrasshopperHttpClient

logger = logging.getLogger(__name__)


class GrasshopperFastMCPServer:
    """FastMCP-based MCP server for Grasshopper integration."""
    
    def __init__(
        self, 
        grasshopper_url: str = "http://localhost:8080", 
        port: int = 8001, 
        bridge_mode: bool = True,
        stateless: bool = False
    ):
        """Initialize the FastMCP server.
        
        Args:
            grasshopper_url: URL of the Grasshopper HTTP server
            port: Port for the MCP server
            bridge_mode: If True, queue commands for bridge. If False, call Grasshopper directly.
            stateless: If True, use stateless HTTP mode
        """
        self.grasshopper_url = grasshopper_url
        self.port = port
        self.bridge_mode = bridge_mode
        self.stateless = stateless
        self.grasshopper_client = GrasshopperHttpClient(grasshopper_url)
        
        # Bridge polling state
        self.pending_commands: List[Dict] = []
        self.command_results: Dict[str, Dict] = {}
        self.command_history: List[Dict] = []
        
        # Create the MCP server
        if FASTMCP_AVAILABLE:
            self.mcp = FastMCP(
                name="grasshopper-mcp-fastmcp",
                stateless_http=stateless,
                json_response=False  # Use streamable HTTP
            )
            self._register_fastmcp_tools()
        elif MANUAL_MCP_AVAILABLE:
            # Fallback to manual implementation
            self.mcp = self._create_manual_server()
        else:
            raise ImportError("Neither FastMCP nor manual MCP server dependencies are available")
        
        # Create FastAPI app for bridge endpoints
        self.bridge_app = self._create_bridge_app()
    
    def _create_manual_server(self):
        """Create manual MCP server if FastMCP not available."""
        if not MANUAL_MCP_AVAILABLE or Server is None:
            raise ImportError("Manual MCP server dependencies not available")
            
        server = Server("grasshopper-mcp-manual")
        
        @server.call_tool()
        async def call_tool(
            name: str, arguments: dict
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution requests."""
            return await self._handle_tool_call(name, arguments)
        
        @server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools."""
            return self._get_tool_definitions()
        
        return server
    
    def _register_fastmcp_tools(self):
        """Register tools with FastMCP."""
        
        @self.mcp.tool(description="Add a component to the Grasshopper canvas")
        def add_component(component_type: str, x: float, y: float) -> str:
            """Add a component to the Grasshopper canvas.
            
            Args:
                component_type: Type of component (point, line, circle, slider, panel, etc.)
                x: X coordinate on the canvas
                y: Y coordinate on the canvas
            
            Returns:
                Success message with component details
            """
            # Queue the tool call for async processing
            return self._sync_tool_wrapper("add_component", {
                "component_type": component_type,
                "x": x,
                "y": y
            })
        
        @self.mcp.tool(description="Connect two components in Grasshopper")
        def connect_components(
            source_id: str, 
            target_id: str, 
            source_param: Optional[str] = None, 
            target_param: Optional[str] = None
        ) -> str:
            """Connect two components in Grasshopper.
            
            Args:
                source_id: ID of the source component
                target_id: ID of the target component
                source_param: Source parameter name (optional)
                target_param: Target parameter name (optional)
            
            Returns:
                Success message with connection details
            """
            params = {
                "source_id": source_id,
                "target_id": target_id
            }
            if source_param:
                params["source_param"] = source_param
            if target_param:
                params["target_param"] = target_param
                
            return self._sync_tool_wrapper("connect_components", params)
        
        @self.mcp.tool(description="Get all components in the Grasshopper document")
        def get_all_components() -> str:
            """Get all components in the Grasshopper document.
            
            Returns:
                JSON string with all component details
            """
            return self._sync_tool_wrapper("get_all_components", {})
        
        @self.mcp.tool(description="Set the value of a component parameter")
        def set_component_value(component_id: str, parameter_name: str, value: Any) -> str:
            """Set the value of a component parameter.
            
            Args:
                component_id: ID of the component
                parameter_name: Name of the parameter to set
                value: Value to set (string, number, or boolean)
            
            Returns:
                Success message with parameter details
            """
            return self._sync_tool_wrapper("set_component_value", {
                "component_id": component_id,
                "parameter_name": parameter_name,
                "value": value
            })
        
        @self.mcp.tool(description="Clear all components from the Grasshopper document")
        def clear_document() -> str:
            """Clear all components from the Grasshopper document.
            
            Returns:
                Success message
            """
            return self._sync_tool_wrapper("clear_document", {})
        
        @self.mcp.tool(description="Save the current Grasshopper document")
        def save_document(filename: Optional[str] = None) -> str:
            """Save the current Grasshopper document.
            
            Args:
                filename: Filename to save to (optional)
            
            Returns:
                Success message with save details
            """
            params = {}
            if filename:
                params["filename"] = filename
            return self._sync_tool_wrapper("save_document", params)
    
    def _sync_tool_wrapper(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Synchronous wrapper for async tool execution."""
        try:
            # In bridge mode, queue the command
            if self.bridge_mode:
                command_id = self._queue_command_for_bridge(tool_name, arguments)
                return f"Command '{tool_name}' queued for bridge execution with ID: {command_id}"
            else:
                # For direct mode, we need to run async operation
                # This is a simplified version - in production you'd want proper async handling
                return f"Command '{tool_name}' would execute directly (async execution not implemented in sync wrapper)"
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}, Error: {str(e)}")
            return f"Tool execution failed: {str(e)}"
    
    async def _handle_tool_call(
        self, name: str, arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests (for manual server)."""
        try:
            logger.info(f"Executing tool: {name} with args: {arguments} (bridge_mode: {self.bridge_mode})")
            
            # Choose execution mode
            if self.bridge_mode:
                result = await self._handle_bridge_mode_tool(name, arguments)
            else:
                # Direct execution mode
                if name == "add_component":
                    result = await self._add_component(
                        component_type=arguments["component_type"],
                        x=arguments["x"],
                        y=arguments["y"]
                    )
                elif name == "connect_components":
                    result = await self._connect_components(
                        source_id=arguments["source_id"],
                        target_id=arguments["target_id"],
                        source_param=arguments.get("source_param"),
                        target_param=arguments.get("target_param")
                    )
                elif name == "get_all_components":
                    result = await self._get_all_components()
                elif name == "set_component_value":
                    result = await self._set_component_value(
                        component_id=arguments["component_id"],
                        parameter_name=arguments["parameter_name"],
                        value=arguments["value"]
                    )
                elif name == "clear_document":
                    result = await self._clear_document()
                elif name == "save_document":
                    result = await self._save_document(
                        filename=arguments.get("filename")
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            # Format success result
            if isinstance(result, dict) and result.get("success", True):
                content = types.TextContent(
                    type="text",
                    text=f"Tool '{name}' executed successfully. Result: {json.dumps(result, indent=2)}"
                )
            else:
                content = types.TextContent(
                    type="text",
                    text=f"Tool '{name}' failed. Error: {result.get('error', 'Unknown error')}"
                )
            
            return [content]
            
        except Exception as e:
            logger.error(f"Tool execution failed: {name}, Error: {str(e)}")
            content = types.TextContent(
                type="text",
                text=f"Tool execution failed: {str(e)}"
            )
            return [content]
    
    def _get_tool_definitions(self) -> List[types.Tool]:
        """Get tool definitions for manual server."""
        return [
            types.Tool(
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
            ),
            types.Tool(
                name="connect_components",
                description="Connect two components in Grasshopper",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_id": {
                            "type": "string",
                            "description": "ID of the source component"
                        },
                        "target_id": {
                            "type": "string",
                            "description": "ID of the target component"
                        },
                        "source_param": {
                            "type": "string",
                            "description": "Source parameter name (optional)"
                        },
                        "target_param": {
                            "type": "string",
                            "description": "Target parameter name (optional)"
                        }
                    },
                    "required": ["source_id", "target_id"]
                }
            ),
            types.Tool(
                name="get_all_components",
                description="Get all components in the Grasshopper document",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="set_component_value",
                description="Set the value of a component parameter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "component_id": {
                            "type": "string",
                            "description": "ID of the component"
                        },
                        "parameter_name": {
                            "type": "string",
                            "description": "Name of the parameter to set"
                        },
                        "value": {
                            "type": "any",
                            "description": "Value to set (string, number, or boolean)"
                        }
                    },
                    "required": ["component_id", "parameter_name", "value"]
                }
            ),
            types.Tool(
                name="clear_document",
                description="Clear all components from the Grasshopper document",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="save_document",
                description="Save the current Grasshopper document",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Filename to save to (optional)"
                        }
                    },
                    "required": []
                }
            )
        ]
    
    # Grasshopper operation methods (same as before)
    async def _add_component(self, component_type: str, x: float, y: float) -> Dict[str, Any]:
        """Add a component to Grasshopper canvas."""
        try:
            response = await self.grasshopper_client.send_command(
                "add_component",
                {
                    "component_type": component_type,
                    "x": x,
                    "y": y
                }
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
            params = {
                "source_id": source_id,
                "target_id": target_id
            }
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
    def _create_bridge_app(self) -> FastAPI:
        """Create FastAPI app for bridge polling endpoints."""
        app = FastAPI(title="Grasshopper Bridge API")
        
        @app.get("/pending_commands")
        async def get_pending_commands() -> List[Dict]:
            """Get pending commands for bridge to execute."""
            commands = self.pending_commands.copy()
            self.pending_commands.clear()  # Clear after sending
            logger.info(f"Bridge requested commands: {len(commands)} pending")
            return commands
        
        @app.post("/command_result")
        async def receive_command_result(request: Request) -> Dict[str, str]:
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
        
        @app.get("/status")
        async def get_bridge_status() -> Dict[str, Any]:
            """Get bridge status and command history."""
            return {
                "pending_commands": len(self.pending_commands),
                "completed_commands": len(self.command_results),
                "command_history": self.command_history[-10:],  # Last 10
                "server_time": datetime.utcnow().isoformat(),
                "bridge_mode": self.bridge_mode
            }
        
        return app
    
    def create_combined_app(self) -> FastAPI:
        """Create combined FastAPI app with MCP and bridge endpoints."""
        # Create main app
        if FASTMCP_AVAILABLE:
            # Get the streamable HTTP app from FastMCP
            main_app = FastAPI(title="Grasshopper MCP Server")
            
            # Mount the MCP server
            main_app.mount("/mcp", self.mcp.streamable_http_app())
            
            # Mount bridge endpoints
            main_app.mount("/grasshopper", self.bridge_app)
            
        else:
            # Manual implementation - create a basic FastAPI app
            main_app = FastAPI(title="Grasshopper MCP Server (Manual)")
            
            # Add a basic health check
            @main_app.get("/health")
            async def health():
                return {"status": "ok", "server": "grasshopper-mcp-manual"}
            
            # Mount bridge endpoints
            main_app.mount("/grasshopper", self.bridge_app)
            
            # TODO: Implement manual MCP endpoints
            logger.warning("FastMCP not available, using manual implementation (limited functionality)")
        
        return main_app
    
    def run(self) -> None:
        """Run the MCP server."""
        if FASTMCP_AVAILABLE:
            # Use FastMCP's built-in run method
            logger.info(f"Starting Grasshopper FastMCP server on port {self.port}")
            logger.info(f"MCP endpoint: http://127.0.0.1:{self.port}/mcp")
            logger.info(f"Bridge endpoints: http://127.0.0.1:{self.port}/grasshopper/")
            logger.info(f"Connected to Grasshopper at: {self.grasshopper_url}")
            logger.info(f"Bridge mode: {self.bridge_mode}")
            
            # Create combined app
            app = self.create_combined_app()
            uvicorn.run(app, host="127.0.0.1", port=self.port)
        else:
            # Manual server run
            logger.info(f"Starting manual MCP server on port {self.port}")
            app = self.create_combined_app()
            uvicorn.run(app, host="127.0.0.1", port=self.port)


def create_grasshopper_mcp_server(
    grasshopper_url: str = "http://localhost:8080",
    port: int = 8001,
    bridge_mode: bool = True,
    stateless: bool = False
) -> GrasshopperFastMCPServer:
    """Create a Grasshopper MCP server instance.
    
    Args:
        grasshopper_url: URL of the Grasshopper HTTP server
        port: Port for the MCP server
        bridge_mode: If True, queue commands for bridge. If False, call Grasshopper directly.
        stateless: If True, use stateless HTTP mode
    
    Returns:
        Configured GrasshopperFastMCPServer instance
    """
    return GrasshopperFastMCPServer(
        grasshopper_url=grasshopper_url,
        port=port,
        bridge_mode=bridge_mode,
        stateless=stateless
    )


if __name__ == "__main__":
    import click
    
    @click.command()
    @click.option("--port", default=8001, help="Port to listen on")
    @click.option("--grasshopper-url", default="http://localhost:8080", help="Grasshopper server URL")
    @click.option("--bridge-mode/--direct-mode", default=True, help="Use bridge mode or direct mode")
    @click.option("--stateless", is_flag=True, help="Use stateless HTTP mode")
    @click.option("--log-level", default="INFO", help="Logging level")
    def main(port: int, grasshopper_url: str, bridge_mode: bool, stateless: bool, log_level: str):
        """Start the Grasshopper FastMCP server."""
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        
        server = create_grasshopper_mcp_server(
            grasshopper_url=grasshopper_url,
            port=port,
            bridge_mode=bridge_mode,
            stateless=stateless
        )
        server.run()
    
    main()