"""CLI for starting the FastMCP-based MCP server."""
import logging
import sys

import click

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--port", 
    default=8001, 
    help="Port for the MCP server"
)
@click.option(
    "--grasshopper-url", 
    default="http://localhost:8080",
    help="URL where Grasshopper HTTP server is running"
)
@click.option(
    "--bridge-mode/--direct-mode",
    default=True,
    help="Use bridge mode (queue commands) or direct mode (immediate execution)"
)
@click.option(
    "--stateless",
    is_flag=True,
    help="Use stateless HTTP mode"
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
def start_fastmcp_server(port, grasshopper_url, bridge_mode, stateless, log_level, debug):
    """Start the FastMCP-based MCP server for Grasshopper integration."""
    
    # Configure logging
    if debug:
        log_level = "DEBUG"
        
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    click.echo("🚀 Starting FastMCP-based MCP Server")
    click.echo(f"📡 MCP endpoint: http://127.0.0.1:{port}/mcp")
    click.echo(f"🌉 Bridge endpoints: http://127.0.0.1:{port}/grasshopper/")
    click.echo(f"🔗 Grasshopper: {grasshopper_url}")
    click.echo("📊 Transport: streamable-http (FastMCP)")
    click.echo(f"🏗️  Mode: {'Bridge' if bridge_mode else 'Direct'}")
    click.echo(f"🔄 Stateless: {stateless}")
    
    if debug:
        click.echo("🐛 Debug mode enabled")
    
    try:
        # Import here to avoid import issues
        from ..mcp.fastmcp_server import create_grasshopper_mcp_server
        
        # Create and run the server
        server = create_grasshopper_mcp_server(
            grasshopper_url=grasshopper_url,
            port=port,
            bridge_mode=bridge_mode,
            stateless=stateless
        )
        
        click.echo("⚡ Server starting...")
        server.run()
        
    except KeyboardInterrupt:
        click.echo("\n⏹️  FastMCP Server stopped by user")
    except Exception as e:
        click.echo(f"❌ Failed to start FastMCP server: {str(e)}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    start_fastmcp_server()