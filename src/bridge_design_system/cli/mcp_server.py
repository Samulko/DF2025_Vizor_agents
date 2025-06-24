"""CLI for starting the HTTP MCP server."""
import logging
import sys

import click
import uvicorn

from ..mcp.grasshopper_mcp.bridge_http import GrasshopperMCPBridge

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--port", 
    default=8001, 
    help="Port for the MCP HTTP server"
)
@click.option(
    "--grasshopper-port", 
    default=8080, 
    help="Port where Grasshopper HTTP server is running"
)
@click.option(
    "--host", 
    default="0.0.0.0", 
    help="Host to bind the server to"
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
@click.option(
    "--reload", 
    is_flag=True, 
    help="Enable auto-reload for development"
)
def start_mcp_server(port, grasshopper_port, host, debug, reload):
    """Start the HTTP MCP server for Grasshopper integration."""
    
    # Configure logging
    log_level = "debug" if debug else "info"
    
    click.echo("🚀 Starting Grasshopper MCP HTTP Server")
    click.echo(f"📡 Server: http://{host}:{port}")
    click.echo(f"🔗 Grasshopper: http://localhost:{grasshopper_port}")
    click.echo(f"📊 Documentation: http://{host}:{port}/docs")
    click.echo(f"💡 Health Check: http://{host}:{port}/health")
    
    if debug:
        click.echo("🐛 Debug mode enabled")
    
    try:
        # Create the bridge application
        bridge = GrasshopperMCPBridge(
            mcp_port=port,
            grasshopper_port=grasshopper_port
        )
        
        # Start the server using uvicorn
        uvicorn.run(
            bridge.get_app(),
            host=host,
            port=port,
            log_level=log_level,
            reload=reload,
            access_log=True
        )
        
    except KeyboardInterrupt:
        click.echo("\n⏹️  MCP Server stopped by user")
    except Exception as e:
        click.echo(f"❌ Failed to start MCP server: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    start_mcp_server()