"""Official MCP Server implementation using the official MCP Python SDK.

This replaces our custom FastAPI implementation with the official MCP specification
using SSE (Server-Sent Events) and StreamableHTTP transports.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server.models import InitializeResult
from mcp.server.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    Resource,
    TextContent,
    Tool,
)

from ..tools.core.components import ComponentManager
from ..tools.core.connections import ConnectionManager
from ..tools.core.document import DocumentManager
from .utils.communication import GrasshopperHttpClient

logger = logging.getLogger(__name__)


class GrasshopperMCPServer:
    """Official MCP server for Grasshopper integration using MCP SDK."""
    
    def __init__(self, grasshopper_url: str = "http://localhost:8080"):
        """Initialize the MCP server.
        
        Args:
            grasshopper_url: URL of the Grasshopper HTTP server
        """
        self.grasshopper_url = grasshopper_url
        self.grasshopper_client = GrasshopperHttpClient(grasshopper_url)
        
        # Initialize managers
        self.component_manager = ComponentManager(self.grasshopper_client)
        self.connection_manager = ConnectionManager(self.grasshopper_client)
        self.document_manager = DocumentManager(self.grasshopper_client)
        
        # Create MCP server instance
        self.server = Server("grasshopper-mcp")
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools."""
            tools = [
                Tool(
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
                Tool(
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
                Tool(
                    name="get_all_components",
                    description="Get all components in the Grasshopper document",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
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
                                "type": ["string", "number", "boolean"],
                                "description": "Value to set"
                            }
                        },
                        "required": ["component_id", "parameter_name", "value"]
                    }
                ),
                Tool(
                    name="clear_document",
                    description="Clear all components from the Grasshopper document",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
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
            
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool execution."""
            try:
                logger.info(f"Executing tool: {name} with args: {arguments}")
                
                if name == "add_component":
                    result = await self.component_manager.add_component(
                        component_type=arguments["component_type"],
                        x=arguments["x"],
                        y=arguments["y"]
                    )
                
                elif name == "connect_components":
                    result = await self.connection_manager.connect_components(
                        source_id=arguments["source_id"],
                        target_id=arguments["target_id"],
                        source_param=arguments.get("source_param"),
                        target_param=arguments.get("target_param")
                    )
                
                elif name == "get_all_components":
                    result = await self.component_manager.get_all_components()
                
                elif name == "set_component_value":
                    result = await self.component_manager.set_component_value(
                        component_id=arguments["component_id"],
                        parameter_name=arguments["parameter_name"],
                        value=arguments["value"]
                    )
                
                elif name == "clear_document":
                    result = await self.document_manager.clear_document()
                
                elif name == "save_document":
                    result = await self.document_manager.save_document(
                        filename=arguments.get("filename")
                    )
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Format result for MCP
                if isinstance(result, dict) and result.get("success", True):
                    content = TextContent(
                        type="text",
                        text=f"Tool '{name}' executed successfully. Result: {result}"
                    )
                else:
                    content = TextContent(
                        type="text",
                        text=f"Tool '{name}' failed. Error: {result.get('error', 'Unknown error')}"
                    )
                
                return CallToolResult(content=[content])
                
            except Exception as e:
                logger.error(f"Tool execution failed: {name}, Error: {str(e)}")
                content = TextContent(
                    type="text",
                    text=f"Tool execution failed: {str(e)}"
                )
                return CallToolResult(content=[content])
    
    async def run_stdio(self):
        """Run the MCP server over stdio."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializeResult(
                    protocolVersion="2024-11-05",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    ),
                    serverInfo={
                        "name": "grasshopper-mcp",
                        "version": "0.2.0"
                    }
                )
            )


async def main():
    """Main entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Grasshopper MCP Server")
    parser.add_argument(
        "--grasshopper-url",
        default="http://localhost:8080",
        help="URL of the Grasshopper HTTP server"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = GrasshopperMCPServer(args.grasshopper_url)
    
    logger.info(f"Starting Grasshopper MCP Server")
    logger.info(f"Grasshopper URL: {args.grasshopper_url}")
    logger.info("Server running on stdio...")
    
    try:
        await server.run_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())