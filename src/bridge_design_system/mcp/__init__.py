"""MCP (Model Context Protocol) integration for Grasshopper bridge design.

This module provides multiple MCP implementations:
- FastMCP-based server (recommended, requires FastMCP)
- Manual HTTP server (fallback, pure HTTP + JSON-RPC)
- StreamableHTTPSessionManager server (legacy, may have issues)
"""

# New implementations (recommended)
# from .fastmcp_server import GrasshopperFastMCPServer, create_grasshopper_mcp_server  # Commented out - has import issues
# from .manual_http_server import GrasshopperManualMCPServer, create_manual_mcp_server  # Commented out - not implemented yet

# Clean FastMCP implementation (recommended)
# Use smolagents' built-in ToolCollection.from_mcp() instead of custom integration
from .mcp_tools_utils import (
    get_grasshopper_tools,
    get_mcp_tools_http,
    get_mcp_tools_stdio,
    is_mcp_server_available,
    is_mcp_server_available_http,
    is_mcp_server_available_stdio,
)

# Legacy implementations (for backward compatibility) - disabled due to import issues
# from .streamable_http_server import GrasshopperMCPStreamableServer
# from .official_adapter import OfficialMCPAdapter, get_official_mcp_tools
# from .http_adapter import HttpMCPAdapter, get_http_mcp_tools
# from .grasshopper_mcp.bridge_http import GrasshopperMCPBridge
# from .grasshopper_mcp.http_server import GrasshopperMCPServer

# New HTTP MCP server implementation
try:
    from .http_mcp_server import create_http_mcp_server, run_http_mcp_server
except ImportError as e:
    print(f"Warning: HTTP MCP server import failed: {e}")
    create_http_mcp_server = None
    run_http_mcp_server = None

__all__ = [
    # Clean FastMCP utilities (recommended)
    "get_mcp_tools_stdio",
    "get_mcp_tools_http", 
    "get_grasshopper_tools", 
    "is_mcp_server_available",
    "is_mcp_server_available_stdio",
    "is_mcp_server_available_http",
    # New HTTP MCP server
    "create_http_mcp_server",
    "run_http_mcp_server"
]