"""MCP (Model Context Protocol) integration for Grasshopper bridge design.

This module provides both official MCP SDK integration and custom HTTP-based 
MCP communication for seamless integration with smolagents framework.
"""

# Official MCP implementation (preferred)
from .official_adapter import OfficialMCPAdapter, get_official_mcp_tools

# Legacy HTTP implementation (fallback)
from .http_adapter import HttpMCPAdapter, get_http_mcp_tools
from .grasshopper_mcp.bridge_http import GrasshopperMCPBridge
from .grasshopper_mcp.http_server import GrasshopperMCPServer

__all__ = [
    # Official MCP (preferred)
    "OfficialMCPAdapter",
    "get_official_mcp_tools",
    # Legacy HTTP implementation
    "HttpMCPAdapter",
    "get_http_mcp_tools", 
    "GrasshopperMCPBridge",
    "GrasshopperMCPServer"
]