"""CLI for starting the official MCP server using the MCP Python SDK."""
import asyncio
import logging
import sys

import click

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--grasshopper-url", 
    default="http://localhost:8080", 
    help="URL where Grasshopper HTTP server is running"
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
def start_official_mcp_server(grasshopper_url, debug):
    """Start the official MCP server for Grasshopper integration using MCP SDK."""
    
    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    click.echo("🚀 Starting Official Grasshopper MCP Server")
    click.echo(f"🔗 Grasshopper: {grasshopper_url}")
    click.echo("📡 Protocol: stdio (standard MCP)")
    
    if debug:
        click.echo("🐛 Debug mode enabled")
    
    try:
        # Import here to avoid import issues
        from ..mcp.grasshopper_mcp.official_mcp_server import GrasshopperMCPServer
        
        # Create and run the server
        server = GrasshopperMCPServer(grasshopper_url)
        
        click.echo("⚡ Server starting on stdio...")
        asyncio.run(server.run_stdio())
        
    except KeyboardInterrupt:
        click.echo("\n⏹️  Official MCP Server stopped by user")
    except Exception as e:
        click.echo(f"❌ Failed to start official MCP server: {str(e)}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    start_official_mcp_server()