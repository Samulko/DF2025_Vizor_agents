"""Utility functions for getting MCP tools at application level."""

import os
from typing import List, Optional
from smolagents import Tool, ToolCollection
from mcp import StdioServerParameters

from ..config.logging_config import get_logger

logger = get_logger(__name__)


def get_mcp_tools_stdio(
    command: str = "uv",
    args: List[str] = None,
    working_directory: str = None,
    trust_remote_code: bool = True
) -> List[Tool]:
    """
    Get MCP tools from STDIO server for use in smolagents agents.
    
    This connects to your existing Grasshopper MCP server using STDIO transport,
    the same way Cline Desktop connects to it.
    
    Args:
        command: Command to run the MCP server (default: "uv")
        args: Arguments for the command (default: connects to local bridge.py via uv)
        working_directory: Directory to run command from
        trust_remote_code: Whether to trust remote code execution
        
    Returns:
        List of smolagents Tool objects from the MCP server
    """
    if args is None:
        # Default to your existing Grasshopper MCP server in current project
        # Use the exact same command that works manually: uv run python reference/grasshopper_mcp/bridge.py
        args = [
            "run",
            "python", 
            "-m", 
            "grasshopper_mcp.bridge"
        ]
    
    try:
        logger.info(f"Connecting to MCP server via STDIO: {command} {' '.join(args)}")
        
        # Create STDIO server parameters (proper uv run approach)
        server_parameters = StdioServerParameters(
            command=command,
            args=args,
            env=os.environ,  # Use clean environment - let uv handle everything
            cwd=os.getcwd()  # Ensure we're in the right directory
        )
        
        # Use ToolCollection.from_mcp() with STDIO parameters
        with ToolCollection.from_mcp(server_parameters, trust_remote_code=trust_remote_code) as tool_collection:
            
            # Extract tools from the collection
            tools = list(tool_collection.tools)
            
            logger.info(f"Successfully loaded {len(tools)} MCP tools via STDIO")
            tool_names = [tool.name for tool in tools]
            logger.info(f"Available MCP tools: {tool_names}")
            
            return tools
            
    except Exception as e:
        logger.warning(f"Failed to load MCP tools via STDIO: {e}")
        return []


def get_mcp_tools_http(server_url: str = "http://localhost:8001/mcp", trust_remote_code: bool = True) -> List[Tool]:
    """
    Get MCP tools from HTTP server for use in smolagents agents.
    
    This function handles HTTP MCP connections (fallback method).
    
    Args:
        server_url: URL of the MCP server
        trust_remote_code: Whether to trust remote code execution
        
    Returns:
        List of smolagents Tool objects from the MCP server
    """
    try:
        logger.info(f"Connecting to MCP server at {server_url}")
        
        # Use ToolCollection.from_mcp() as context manager (correct usage)
        with ToolCollection.from_mcp({
            "url": server_url, 
            "transport": "streamable-http"
        }, trust_remote_code=trust_remote_code) as tool_collection:
            
            # Extract tools from the collection
            tools = list(tool_collection.tools)
            
            logger.info(f"Successfully loaded {len(tools)} MCP tools")
            tool_names = [tool.name for tool in tools]
            logger.info(f"Available MCP tools: {tool_names}")
            
            return tools
            
    except Exception as e:
        logger.warning(f"Failed to load MCP tools from {server_url}: {e}")
        return []


def get_grasshopper_tools(use_stdio: bool = True) -> List[Tool]:
    """
    Get Grasshopper MCP tools specifically.
    
    Args:
        use_stdio: Whether to use STDIO transport (True) or HTTP (False)
        
    Returns:
        List of Grasshopper-specific smolagents Tool objects
    """
    if use_stdio:
        # Connect to your existing Grasshopper MCP server via STDIO (recommended)
        return get_mcp_tools_stdio(trust_remote_code=True)
    else:
        # Fallback to HTTP method
        return get_mcp_tools_http("http://localhost:8001/mcp", trust_remote_code=True)


def is_mcp_server_available_stdio() -> bool:
    """
    Check if STDIO MCP server is available without loading tools.
    
    Returns:
        True if server is available, False otherwise
    """
    try:
        # Quick test to see if we can connect via STDIO
        tools = get_mcp_tools_stdio()
        return len(tools) > 0
    except:
        return False


def is_mcp_server_available_http(server_url: str = "http://localhost:8001/mcp") -> bool:
    """
    Check if HTTP MCP server is available without loading tools.
    
    Args:
        server_url: URL of the MCP server to check
        
    Returns:
        True if server is available, False otherwise
    """
    try:
        # Quick test to see if we can connect
        tools = get_mcp_tools_http(server_url)
        return len(tools) > 0
    except:
        return False


def is_mcp_server_available(use_stdio: bool = True, server_url: str = "http://localhost:8001/mcp") -> bool:
    """
    Check if MCP server is available.
    
    Args:
        use_stdio: Whether to check STDIO transport (True) or HTTP (False)
        server_url: URL of the MCP server to check (for HTTP mode)
        
    Returns:
        True if server is available, False otherwise
    """
    if use_stdio:
        return is_mcp_server_available_stdio()
    else:
        return is_mcp_server_available_http(server_url)