"""HTTP-based Grasshopper MCP Bridge for smolagents integration.

This is the main entry point that replaces the TCP-based bridge.py.
It provides HTTP endpoints compatible with smolagents MCPClient.
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .http_server import GrasshopperMCPServer, create_app
from .utils.communication import GrasshopperHttpClient

logger = logging.getLogger(__name__)


class GrasshopperMCPBridge:
    """Main bridge class for HTTP-based MCP communication."""
    
    def __init__(self, mcp_port: int = 8001, grasshopper_port: int = 8080):
        """Initialize the MCP bridge.
        
        Args:
            mcp_port: Port for the MCP HTTP server
            grasshopper_port: Port where Grasshopper HTTP server is running
        """
        self.mcp_port = mcp_port
        self.grasshopper_url = f"http://localhost:{grasshopper_port}"
        self.server = GrasshopperMCPServer(self.grasshopper_url)
        
    async def start(self):
        """Start the MCP bridge server."""
        logger.info(f"Starting Grasshopper MCP Bridge on port {self.mcp_port}")
        logger.info(f"Connecting to Grasshopper at {self.grasshopper_url}")
        
        try:
            await self.server.start_server(port=self.mcp_port)
        except Exception as e:
            logger.error(f"Failed to start MCP bridge: {str(e)}")
            raise
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application."""
        return self.server.app


# Create the FastAPI app for deployment
app = create_app()


@app.get("/")
async def root():
    """Root endpoint with bridge information."""
    return {
        "name": "Grasshopper MCP Bridge",
        "version": "0.2.0",
        "description": "HTTP bridge between smolagents and Grasshopper",
        "endpoints": {
            "health": "/health",
            "tools": "/mcp/tools",
            "status": "/mcp/status",
            "execute_tool": "/mcp/tools/{tool_name}"
        },
        "documentation": "/docs"
    }


# Tool registry for smolagents integration
AVAILABLE_TOOLS = [
    {
        "name": "add_component",
        "description": "Add a component to the Grasshopper canvas",
        "parameters": {
            "component_type": {"type": "string", "description": "Type of component"},
            "x": {"type": "number", "description": "X coordinate"},
            "y": {"type": "number", "description": "Y coordinate"}
        }
    },
    {
        "name": "connect_components", 
        "description": "Connect two components in Grasshopper",
        "parameters": {
            "source_id": {"type": "string", "description": "Source component ID"},
            "target_id": {"type": "string", "description": "Target component ID"},
            "source_param": {"type": "string", "description": "Source parameter name"},
            "target_param": {"type": "string", "description": "Target parameter name"}
        }
    },
    {
        "name": "get_all_components",
        "description": "Get all components in the document",
        "parameters": {}
    },
    {
        "name": "clear_document",
        "description": "Clear the Grasshopper document",
        "parameters": {}
    },
    {
        "name": "add_number_slider",
        "description": "Add a number slider component",
        "parameters": {
            "x": {"type": "number", "description": "X coordinate"},
            "y": {"type": "number", "description": "Y coordinate"},
            "min_value": {"type": "number", "description": "Minimum value"},
            "max_value": {"type": "number", "description": "Maximum value"},
            "value": {"type": "number", "description": "Current value"}
        }
    },
    {
        "name": "create_bridge_span",
        "description": "Create a bridge span between two points",
        "parameters": {
            "start_point_id": {"type": "string", "description": "Start point component ID"},
            "end_point_id": {"type": "string", "description": "End point component ID"},
            "span_type": {"type": "string", "description": "Type of span (beam, truss, cable)"}
        }
    }
]


@app.get("/mcp/tools/registry")
async def get_tool_registry():
    """Get the tool registry for smolagents."""
    return {"tools": AVAILABLE_TOOLS}


async def main():
    """Main entry point for running the HTTP MCP bridge."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Grasshopper MCP HTTP Bridge")
    parser.add_argument("--port", type=int, default=8001, help="MCP server port")
    parser.add_argument("--grasshopper-port", type=int, default=8080, help="Grasshopper server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("mcp_bridge.log")
        ]
    )
    
    # Create and start the bridge
    bridge = GrasshopperMCPBridge(
        mcp_port=args.port,
        grasshopper_port=args.grasshopper_port
    )
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("MCP Bridge stopped by user")
    except Exception as e:
        logger.error(f"MCP Bridge failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())