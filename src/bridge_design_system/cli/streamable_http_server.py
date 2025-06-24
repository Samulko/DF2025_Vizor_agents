"""CLI for starting the official MCP streamable-http server."""
import logging
import sys

import click

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--port", 
    default=8001, 
    help="Port for the MCP streamable-http server"
)
@click.option(
    "--grasshopper-url", 
    default="http://localhost:8080",
    help="URL where Grasshopper HTTP server is running"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
def start_streamable_http_server(port, grasshopper_url, log_level, debug):
    """Start the official MCP streamable-http server for Grasshopper integration."""
    
    # Configure logging
    if debug:
        log_level = "DEBUG"
        
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    click.echo("🚀 Starting Official MCP Streamable-HTTP Server")
    click.echo(f"📡 Server: http://127.0.0.1:{port}/mcp")
    click.echo(f"🔗 Grasshopper: {grasshopper_url}")
    click.echo("📊 Transport: streamable-http (official MCP)")
    
    if debug:
        click.echo("🐛 Debug mode enabled")
    
    try:
        # Import here to avoid import issues
        from ..mcp.streamable_http_server import GrasshopperMCPStreamableServer
        
        # Create and run the server
        server = GrasshopperMCPStreamableServer(grasshopper_url, port)
        
        click.echo("⚡ Server starting...")
        server.run()
        
    except KeyboardInterrupt:
        click.echo("\n⏹️  MCP Streamable-HTTP Server stopped by user")
    except Exception as e:
        click.echo(f"❌ Failed to start MCP server: {str(e)}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    start_streamable_http_server()