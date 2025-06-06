"""HTTP-based MCP Server for Grasshopper Bridge Design System.

This module replaces the TCP-based MCP with HTTP for seamless smolagents integration.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import httpx

from .utils.communication import GrasshopperHttpClient

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP request model."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class MCPResponse(BaseModel):
    """MCP response model."""
    success: bool = Field(..., description="Whether the operation succeeded")
    result: Optional[Any] = Field(None, description="Operation result")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GrasshopperMCPServer:
    """HTTP-based MCP server for Grasshopper communication."""
    
    def __init__(self, grasshopper_url: str = "http://localhost:8080"):
        """Initialize the MCP server.
        
        Args:
            grasshopper_url: URL of the Grasshopper HTTP endpoint
        """
        self.app = FastAPI(
            title="Grasshopper MCP Bridge",
            description="HTTP bridge between smolagents and Grasshopper",
            version="0.2.0"
        )
        self.grasshopper_client = GrasshopperHttpClient(grasshopper_url)
        self.setup_middleware()
        self.setup_routes()
        
    def setup_middleware(self):
        """Configure CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Local development only
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup HTTP routes for MCP communication."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            grasshopper_status = await self.grasshopper_client.check_connection()
            return {
                "status": "healthy",
                "grasshopper_connected": grasshopper_status,
                "version": "0.2.0"
            }
        
        @self.app.post("/mcp/tools/{tool_name}", response_model=MCPResponse)
        async def execute_tool(tool_name: str, request: MCPRequest):
            """Execute a tool via MCP.
            
            Args:
                tool_name: Name of the tool to execute
                request: Tool parameters and metadata
                
            Returns:
                MCPResponse with execution results
            """
            try:
                logger.info(f"Executing tool: {tool_name} with params: {request.parameters}")
                
                # Send command to Grasshopper
                result = await self.grasshopper_client.send_command(
                    tool_name, 
                    request.parameters
                )
                
                return MCPResponse(
                    success=True,
                    result=result,
                    metadata={
                        "tool_name": tool_name,
                        "execution_time": result.get("execution_time", 0)
                    }
                )
                
            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name}, Error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Tool execution failed: {str(e)}"
                )
        
        @self.app.get("/mcp/tools")
        async def list_tools():
            """List available tools."""
            try:
                tools = await self.grasshopper_client.get_available_tools()
                return {"tools": tools}
            except Exception as e:
                logger.error(f"Failed to list tools: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to list tools: {str(e)}"
                )
        
        @self.app.get("/mcp/status")
        async def get_status():
            """Get comprehensive system status."""
            try:
                grasshopper_status = await self.grasshopper_client.get_status()
                return {
                    "mcp_server": "running",
                    "grasshopper": grasshopper_status,
                    "components": grasshopper_status.get("components", []),
                    "connections": grasshopper_status.get("connections", [])
                }
            except Exception as e:
                logger.error(f"Failed to get status: {str(e)}")
                return {
                    "mcp_server": "running",
                    "grasshopper": {"status": "disconnected", "error": str(e)},
                    "components": [],
                    "connections": []
                }
        
        # Core Grasshopper tools
        @self.app.post("/mcp/tools/add_component")
        async def add_component(
            component_type: str,
            x: float,
            y: float,
            name: Optional[str] = None
        ):
            """Add a component to the Grasshopper canvas."""
            return await execute_tool("add_component", MCPRequest(
                tool_name="add_component",
                parameters={
                    "component_type": component_type,
                    "x": x,
                    "y": y,
                    "name": name
                }
            ))
        
        @self.app.post("/mcp/tools/connect_components")
        async def connect_components(
            source_id: str,
            target_id: str,
            source_param: Optional[str] = None,
            target_param: Optional[str] = None
        ):
            """Connect two components in Grasshopper."""
            return await execute_tool("connect_components", MCPRequest(
                tool_name="connect_components",
                parameters={
                    "source_id": source_id,
                    "target_id": target_id,
                    "source_param": source_param,
                    "target_param": target_param
                }
            ))
        
        @self.app.get("/mcp/tools/get_all_components")
        async def get_all_components():
            """Get all components in the Grasshopper document."""
            return await execute_tool("get_all_components", MCPRequest(
                tool_name="get_all_components",
                parameters={}
            ))
        
        @self.app.post("/mcp/tools/clear_document")
        async def clear_document():
            """Clear the Grasshopper document."""
            return await execute_tool("clear_document", MCPRequest(
                tool_name="clear_document",
                parameters={}
            ))

    async def start_server(self, host: str = "0.0.0.0", port: int = 8001):
        """Start the HTTP MCP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        logger.info(f"Starting Grasshopper MCP HTTP Server on {host}:{port}")
        await server.serve()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    server = GrasshopperMCPServer()
    return server.app


async def main():
    """Main entry point for running the MCP server."""
    server = GrasshopperMCPServer()
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main())