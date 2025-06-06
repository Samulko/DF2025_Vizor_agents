"""MCP (Model Context Protocol) integration for Grasshopper bridge design.

This module provides HTTP-based MCP communication replacing the previous TCP approach
for seamless integration with smolagents framework.
"""

from .http_adapter import HttpMCPAdapter, get_http_mcp_tools
from .grasshopper_mcp.bridge_http import GrasshopperMCPBridge
from .grasshopper_mcp.http_server import GrasshopperMCPServer

__all__ = [
    "HttpMCPAdapter",
    "get_http_mcp_tools", 
    "GrasshopperMCPBridge",
    "GrasshopperMCPServer"
]