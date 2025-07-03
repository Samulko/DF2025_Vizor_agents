"""Official MCP Streamable HTTP Server for Grasshopper integration.

This implements the official MCP streamable-http transport protocol
for seamless integration with smolagents framework.

Also includes polling endpoints for Grasshopper bridge component.
"""

import contextlib
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Dict, List, Optional

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from .grasshopper_mcp.utils.communication import GrasshopperHttpClient

# Configure logging
logger = logging.getLogger(__name__)


class GrasshopperMCPStreamableServer:
    """Official MCP streamable-http server for Grasshopper integration."""

    def __init__(
        self,
        grasshopper_url: str = "http://localhost:8080",
        port: int = 8001,
        bridge_mode: bool = True,
    ):
        """Initialize the streamable MCP server.

        Args:
            grasshopper_url: URL of the Grasshopper HTTP server (for direct mode)
            port: Port for the MCP server
            bridge_mode: If True, queue commands for bridge. If False, call Grasshopper directly.
        """
        self.grasshopper_url = grasshopper_url
        self.port = port
        self.bridge_mode = bridge_mode
        self.grasshopper_client = GrasshopperHttpClient(grasshopper_url)

        # Bridge polling state
        self.pending_commands: List[Dict] = []
        self.command_results: Dict[str, Dict] = {}
        self.command_history: List[Dict] = []

        # Create MCP server instance
        self.app = Server("grasshopper-mcp-streamable")

        # Register handlers
        self._register_handlers()

        # Create session manager with polling endpoints
        # Note: Using default event store to avoid task group issues
        self.session_manager = StreamableHTTPSessionManager(
            app=self.app,
            # event_store=None,  # Default store to ensure proper initialization
            json_response=False,  # Use streamable HTTP, not JSON
        )

        # Add polling endpoints to the session manager's app
        self._add_polling_endpoints()

    def _register_handlers(self):
        """Register MCP tool handlers."""

        @self.app.call_tool()
        async def call_tool(
            name: str, arguments: dict
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution requests."""
            try:
                logger.info(
                    f"Executing tool: {name} with args: {arguments} (bridge_mode: {self.bridge_mode})"
                )

                # Choose execution mode
                if self.bridge_mode:
                    result = await self._handle_bridge_mode_tool(name, arguments)
                else:
                    # Direct execution mode
                    if name == "add_component":
                        result = await self._add_component(
                            component_type=arguments["component_type"],
                            x=arguments["x"],
                            y=arguments["y"],
                        )
                    elif name == "connect_components":
                        result = await self._connect_components(
                            source_id=arguments["source_id"],
                            target_id=arguments["target_id"],
                            source_param=arguments.get("source_param"),
                            target_param=arguments.get("target_param"),
                        )
                    elif name == "get_all_components":
                        result = await self._get_all_components()
                    elif name == "set_component_value":
                        result = await self._set_component_value(
                            component_id=arguments["component_id"],
                            parameter_name=arguments["parameter_name"],
                            value=arguments["value"],
                        )
                    elif name == "clear_document":
                        result = await self._clear_document()
                    elif name == "save_document":
                        result = await self._save_document(filename=arguments.get("filename"))
                    else:
                        raise ValueError(f"Unknown tool: {name}")

                # Format success result
                if isinstance(result, dict) and result.get("success", True):
                    content = types.TextContent(
                        type="text", text=f"Tool '{name}' executed successfully. Result: {result}"
                    )
                else:
                    content = types.TextContent(
                        type="text",
                        text=f"Tool '{name}' failed. Error: {result.get('error', 'Unknown error')}",
                    )

                return [content]

            except Exception as e:
                logger.error(f"Tool execution failed: {name}, Error: {str(e)}")
                content = types.TextContent(type="text", text=f"Tool execution failed: {str(e)}")
                return [content]

        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="add_component",
                    description="Add a component to the Grasshopper canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component_type": {
                                "type": "string",
                                "description": "Type of component (point, line, circle, slider, panel, etc.)",
                            },
                            "x": {"type": "number", "description": "X coordinate on the canvas"},
                            "y": {"type": "number", "description": "Y coordinate on the canvas"},
                        },
                        "required": ["component_type", "x", "y"],
                    },
                ),
                types.Tool(
                    name="connect_components",
                    description="Connect two components in Grasshopper",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "type": "string",
                                "description": "ID of the source component",
                            },
                            "target_id": {
                                "type": "string",
                                "description": "ID of the target component",
                            },
                            "source_param": {
                                "type": "string",
                                "description": "Source parameter name (optional)",
                            },
                            "target_param": {
                                "type": "string",
                                "description": "Target parameter name (optional)",
                            },
                        },
                        "required": ["source_id", "target_id"],
                    },
                ),
                types.Tool(
                    name="get_all_components",
                    description="Get all components in the Grasshopper document",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                types.Tool(
                    name="set_component_value",
                    description="Set the value of a component parameter",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component_id": {
                                "type": "string",
                                "description": "ID of the component",
                            },
                            "parameter_name": {
                                "type": "string",
                                "description": "Name of the parameter to set",
                            },
                            "value": {
                                "type": "any",
                                "description": "Value to set (string, number, or boolean)",
                            },
                        },
                        "required": ["component_id", "parameter_name", "value"],
                    },
                ),
                types.Tool(
                    name="clear_document",
                    description="Clear all components from the Grasshopper document",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                types.Tool(
                    name="save_document",
                    description="Save the current Grasshopper document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Filename to save to (optional)",
                            }
                        },
                        "required": [],
                    },
                ),
            ]

    async def _add_component(self, component_type: str, x: float, y: float) -> Dict[str, Any]:
        """Add a component to Grasshopper canvas."""
        try:
            response = await self.grasshopper_client.send_command(
                "add_component", {"component_type": component_type, "x": x, "y": y}
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
        target_param: Optional[str] = None,
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
        self, component_id: str, parameter_name: str, value: Any
    ) -> Dict[str, Any]:
        """Set a component parameter value."""
        try:
            response = await self.grasshopper_client.send_command(
                "set_component_value",
                {"component_id": component_id, "parameter_name": parameter_name, "value": value},
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

    def _add_polling_endpoints(self):
        """Add polling endpoints for bridge integration."""
        # This will be implemented in create_app method
        pass

    def _queue_command_for_bridge(self, command_type: str, parameters: Dict[str, Any]) -> str:
        """Queue a command for the bridge to execute."""
        command_id = str(uuid.uuid4())
        command = {
            "id": command_id,
            "type": command_type,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat(),
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

                await anyio.sleep(wait_interval)
                waited += wait_interval

            # Timeout
            return {"success": False, "error": "Bridge execution timeout"}

        except Exception as e:
            logger.error(f"Bridge mode tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    # ASGI handler for streamable HTTP connections
    async def handle_streamable_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle incoming streamable HTTP requests."""
        await self.session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(self, app: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        async with self.session_manager.run():
            logger.info(f"Grasshopper MCP Streamable HTTP server started on port {self.port}")
            logger.info(f"Connected to Grasshopper at: {self.grasshopper_url}")
            try:
                yield
            finally:
                logger.info("Grasshopper MCP server shutting down...")

    async def get_pending_commands(self, request: Request) -> JSONResponse:
        """Get pending commands for bridge to execute."""
        commands = self.pending_commands.copy()
        self.pending_commands.clear()  # Clear after sending
        logger.info(f"Bridge requested commands: {len(commands)} pending")
        return JSONResponse(commands)

    async def receive_command_result(self, request: Request) -> JSONResponse:
        """Receive command execution result from bridge."""
        try:
            data = await request.json()
            command_id = data["command_id"]
            success = data["success"]
            result = data["result"]

            # Store result
            self.command_results[command_id] = {"success": success, "result": result}

            # Add to history
            self.command_history.append(
                {
                    "command_id": command_id,
                    "success": success,
                    "result": result,
                    "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
                }
            )

            # Keep only last 100 in history
            if len(self.command_history) > 100:
                self.command_history.pop(0)

            logger.info(
                f"Received result from bridge: {command_id} - {'SUCCESS' if success else 'FAILED'}"
            )
            return JSONResponse({"status": "received"})

        except Exception as e:
            logger.error(f"Error receiving command result: {e}")
            return JSONResponse({"error": str(e)}, status_code=400)

    async def get_bridge_status(self, request: Request) -> JSONResponse:
        """Get bridge status and command history."""
        return JSONResponse(
            {
                "pending_commands": len(self.pending_commands),
                "completed_commands": len(self.command_results),
                "command_history": self.command_history[-10:],  # Last 10
                "server_time": datetime.utcnow().isoformat(),
            }
        )

    def create_app(self) -> Starlette:
        """Create the ASGI application."""

        # Custom ASGI app that properly handles the session manager context
        async def mcp_handler(scope, receive, send):
            """Custom MCP handler that ensures session manager context."""
            try:
                await self.session_manager.handle_request(scope, receive, send)
            except RuntimeError as e:
                if "Task group is not initialized" in str(e):
                    # Fallback error response
                    if scope["type"] == "http":
                        await send(
                            {
                                "type": "http.response.start",
                                "status": 500,
                                "headers": [[b"content-type", b"text/plain"]],
                            }
                        )
                        await send(
                            {
                                "type": "http.response.body",
                                "body": b"MCP session manager not properly initialized",
                            }
                        )
                else:
                    raise

        return Starlette(
            debug=True,
            routes=[
                Mount("/mcp", app=mcp_handler),
                # Bridge polling endpoints
                Route("/grasshopper/pending_commands", self.get_pending_commands, methods=["GET"]),
                Route("/grasshopper/command_result", self.receive_command_result, methods=["POST"]),
                Route("/grasshopper/status", self.get_bridge_status, methods=["GET"]),
            ],
            lifespan=self.lifespan,
        )

    def run(self) -> None:
        """Run the MCP server."""
        import uvicorn

        app = self.create_app()
        logger.info(f"Starting Grasshopper MCP Streamable HTTP server on port {self.port}")
        uvicorn.run(app, host="127.0.0.1", port=self.port)


@click.command()
@click.option("--port", default=8001, help="Port to listen on for HTTP")
@click.option(
    "--grasshopper-url", default="http://localhost:8080", help="URL of the Grasshopper HTTP server"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(port: int, grasshopper_url: str, log_level: str) -> int:
    """Start the Grasshopper MCP Streamable HTTP server."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run server
    server = GrasshopperMCPStreamableServer(grasshopper_url, port)
    server.run()

    return 0


if __name__ == "__main__":
    main()
