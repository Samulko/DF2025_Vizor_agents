"""MCP (Model Context Protocol) integration for Grasshopper bridge design.

This module provides official MCP SDK integration using streamable-http transport
for seamless integration with smolagents framework.
"""

# Official MCP streamable-http implementation (recommended)
from .smolagents_integration import (
    GrasshopperMCPIntegration,
    get_grasshopper_tools,
    get_mcp_client_with_tools
)
from .streamable_http_server import GrasshopperMCPStreamableServer

# Legacy implementations (for backward compatibility)
from .official_adapter import OfficialMCPAdapter, get_official_mcp_tools
from .http_adapter import HttpMCPAdapter, get_http_mcp_tools
from .grasshopper_mcp.bridge_http import GrasshopperMCPBridge
from .grasshopper_mcp.http_server import GrasshopperMCPServer

__all__ = [
    # Official MCP streamable-http (recommended)
    "GrasshopperMCPIntegration",
    "get_grasshopper_tools",
    "get_mcp_client_with_tools",
    "GrasshopperMCPStreamableServer",
    # Legacy implementations
    "OfficialMCPAdapter",
    "get_official_mcp_tools",
    "HttpMCPAdapter",
    "get_http_mcp_tools", 
    "GrasshopperMCPBridge",
    "GrasshopperMCPServer"
]