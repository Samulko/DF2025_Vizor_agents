"""Clean FastMCP server implementation following the reference pattern.

This is a complete rewrite that abandons our complex mounting architecture
in favor of the simple, direct FastMCP approach used in the reference implementation.
"""
import logging
import sys
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime

# Import FastMCP
from mcp.server.fastmcp import FastMCP

# Import Grasshopper communication utilities
from .grasshopper_mcp.utils.communication import GrasshopperHttpClient

# Import Starlette for custom routes
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Create the FastMCP server with HTTP configuration (SSE transport)
# This is the correct way per the crash course documentation
server = None  # Will be initialized with host/port in create_clean_fastmcp_server()

# Global Grasshopper client for tool communication
grasshopper_client = None

def initialize_grasshopper_client(grasshopper_url: str = "http://localhost:8080"):
    """Initialize the Grasshopper HTTP client."""
    global grasshopper_client
    grasshopper_client = GrasshopperHttpClient(grasshopper_url)
    logger.info(f"Initialized Grasshopper client for {grasshopper_url}")

def send_to_grasshopper(command: str, params: dict = None):
    """Send command to Grasshopper via HTTP client."""
    if not grasshopper_client:
        return {
            "success": False,
            "error": "Grasshopper client not initialized"
        }
    
    try:
        import asyncio
        # Run async command in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                grasshopper_client.send_command(command, params or {})
            )
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to send command to Grasshopper: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def register_tools_with_server(mcp_server: FastMCP):
    """Register all MCP tools with the FastMCP server."""
    @mcp_server.tool()
    def add_component(component_type: str, x: float, y: float) -> str:
        """Add a component to the Grasshopper canvas.
        
        Args:
            component_type: Type of component (point, line, circle, slider, panel, etc.)
            x: X coordinate on the canvas
            y: Y coordinate on the canvas
        
        Returns:
            Result message
        """
        logger.info(f"Adding component: {component_type} at ({x}, {y})")
        
        result = send_to_grasshopper("add_component", {
            "component_type": component_type,
            "x": x,
            "y": y
        })
        
        if result.get("success", False):
            return f"Successfully added {component_type} component at ({x}, {y}). Result: {result.get('result', '')}"
        else:
            return f"Failed to add component: {result.get('error', 'Unknown error')}"

    @mcp_server.tool()
    def connect_components(source_id: str, target_id: str, source_param: Optional[str] = None, target_param: Optional[str] = None) -> str:
        """Connect two components in Grasshopper.
        
        Args:
            source_id: ID of the source component
            target_id: ID of the target component
            source_param: Source parameter name (optional)
            target_param: Target parameter name (optional)
        
        Returns:
            Result message
        """
        logger.info(f"Connecting components: {source_id} -> {target_id}")
        
        params = {
            "source_id": source_id,
            "target_id": target_id
        }
        if source_param:
            params["source_param"] = source_param
        if target_param:
            params["target_param"] = target_param
        
        result = send_to_grasshopper("connect_components", params)
        
        if result.get("success", False):
            return f"Successfully connected {source_id} to {target_id}. Result: {result.get('result', '')}"
        else:
            return f"Failed to connect components: {result.get('error', 'Unknown error')}"

    @mcp_server.tool()
    def get_all_components() -> str:
        """Get all components in the Grasshopper document.
        
        Returns:
            JSON string with all component details
        """
        logger.info("Getting all components")
        
        result = send_to_grasshopper("get_all_components", {})
        
        if result.get("success", False):
            import json
            return f"Components retrieved successfully: {json.dumps(result.get('result', []), indent=2)}"
        else:
            return f"Failed to get components: {result.get('error', 'Unknown error')}"

    @mcp_server.tool()
    def set_component_value(component_id: str, parameter_name: str, value) -> str:
        """Set the value of a component parameter.
        
        Args:
            component_id: ID of the component
            parameter_name: Name of the parameter to set
            value: Value to set (string, number, or boolean)
        
        Returns:
            Result message
        """
        logger.info(f"Setting component value: {component_id}.{parameter_name} = {value}")
        
        result = send_to_grasshopper("set_component_value", {
            "component_id": component_id,
            "parameter_name": parameter_name,
            "value": value
        })
        
        if result.get("success", False):
            return f"Successfully set {parameter_name} = {value} on component {component_id}. Result: {result.get('result', '')}"
        else:
            return f"Failed to set component value: {result.get('error', 'Unknown error')}"

    @mcp_server.tool()
    def clear_document() -> str:
        """Clear all components from the Grasshopper document.
        
        Returns:
            Result message
        """
        logger.info("Clearing Grasshopper document")
        
        result = send_to_grasshopper("clear_document", {})
        
        if result.get("success", False):
            return f"Document cleared successfully. Result: {result.get('result', '')}"
        else:
            return f"Failed to clear document: {result.get('error', 'Unknown error')}"

    @mcp_server.tool()
    def save_document(filename: Optional[str] = None) -> str:
        """Save the current Grasshopper document.
        
        Args:
            filename: Filename to save to (optional)
        
        Returns:
            Result message
        """
        logger.info(f"Saving Grasshopper document: {filename or 'default'}")
        
        params = {}
        if filename:
            params["filename"] = filename
        
        result = send_to_grasshopper("save_document", params)
        
        if result.get("success", False):
            return f"Document saved successfully. Result: {result.get('result', '')}"
        else:
            return f"Failed to save document: {result.get('error', 'Unknown error')}"

    # Register FastMCP resources for status and bridge information
    @mcp_server.resource("grasshopper://status")
    def get_grasshopper_status():
        """Get Grasshopper bridge status."""
        try:
            # Get document information
            doc_result = send_to_grasshopper("get_document_info", {})
            components_result = send_to_grasshopper("get_all_components", {})
            
            return {
                "status": "Connected to Grasshopper via FastMCP",
                "server_type": "FastMCP Clean Implementation", 
                "document": doc_result.get("result", {}) if doc_result.get("success") else {},
                "components_count": len(components_result.get("result", [])) if components_result.get("success") else 0,
                "grasshopper_client": grasshopper_client is not None,
                "recommendations": [
                    "This is the clean FastMCP implementation",
                    "Tools are registered directly with FastMCP framework",
                    "No complex mounting or polling architecture needed"
                ]
            }
        except Exception as e:
            logger.error(f"Error getting Grasshopper status: {e}")
            return {
                "status": f"Error: {str(e)}",
                "server_type": "FastMCP Clean Implementation",
                "document": {},
                "components_count": 0,
                "grasshopper_client": grasshopper_client is not None
            }

def create_clean_fastmcp_server(
    grasshopper_url: str = "http://localhost:8080", 
    host: str = "127.0.0.1", 
    port: int = 8001
) -> FastMCP:
    """Create and configure the clean FastMCP server with HTTP transport.
    
    Args:
        grasshopper_url: URL of the Grasshopper HTTP server
        host: Host to bind the HTTP server to
        port: Port to bind the HTTP server to
    
    Returns:
        Configured FastMCP server instance
    """
    global server
    
    # Create FastMCP server with HTTP configuration (per crash course)
    server = FastMCP("Grasshopper Bridge", host=host, port=port)
    
    # Initialize Grasshopper client
    initialize_grasshopper_client(grasshopper_url)
    
    # Register all tools with the server
    register_tools_with_server(server)
    
    logger.info(f"Clean FastMCP server created with Grasshopper at {grasshopper_url}")
    logger.info(f"FastMCP configured for HTTP: {host}:{port}")
    logger.info("All MCP tools registered with FastMCP server")
    return server


def run_clean_fastmcp_server(
    grasshopper_url: str = "http://localhost:8080",
    host: str = "127.0.0.1",
    port: int = 8001
):
    """Run the clean FastMCP server.
    
    Args:
        grasshopper_url: URL of the Grasshopper HTTP server  
        host: Host to bind to
        port: Port to listen on
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr
    )
    
    # Initialize the server with HTTP configuration
    server = create_clean_fastmcp_server(grasshopper_url, host, port)
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Clean FastMCP Grasshopper Server")
    logger.info("=" * 60)
    logger.info(f"📡 MCP Server: http://{host}:{port}/mcp")
    logger.info(f"🔗 Grasshopper: {grasshopper_url}")
    logger.info(f"🛠️  Registered Tools: add_component, connect_components, get_all_components, set_component_value, clear_document, save_document")
    logger.info(f"📊 Resources: grasshopper://status")
    logger.info("🎯 Architecture: Pure FastMCP with direct Grasshopper communication")
    logger.info("=" * 60)
    
    try:
        # Use streamable-http transport as recommended for HTTP servers
        logger.info(f"Starting FastMCP with streamable-http transport on {host}:{port}...")
        server.run(transport="streamable-http")
        
    except Exception as e:
        logger.error(f"Failed to start FastMCP with streamable-http transport: {e}")
        logger.info("Trying alternative transports...")
        
        # Try SSE transport as fallback
        try:
            logger.info("Trying SSE transport...")
            server.run(transport="sse")
        except Exception as e2:
            logger.error(f"SSE transport failed: {e2}")
            
            # Last resort - try default run
            logger.warning("Falling back to default FastMCP run (may use STDIO)")
            server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        # Re-raise so the fallback to manual server can happen
        raise

if __name__ == "__main__":
    import click
    
    @click.command()
    @click.option("--port", default=8001, help="Port to listen on")
    @click.option("--grasshopper-url", default="http://localhost:8080", help="Grasshopper server URL")
    @click.option("--host", default="127.0.0.1", help="Host to bind to")
    @click.option("--log-level", default="INFO", help="Logging level")
    def main(port: int, grasshopper_url: str, host: str, log_level: str):
        """Start the Clean FastMCP Grasshopper server."""
        logging.getLogger().setLevel(getattr(logging, log_level.upper()))
        run_clean_fastmcp_server(grasshopper_url, host, port)
    
    main()