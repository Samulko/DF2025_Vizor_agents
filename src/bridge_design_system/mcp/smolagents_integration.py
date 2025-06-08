"""Direct smolagents MCPClient integration for streamable-http transport.

This module provides seamless integration with smolagents using the official
MCPClient with streamable-http transport - no custom adapters needed.
"""
import logging
from typing import Any, Dict, List, Optional

from smolagents import MCPClient, Tool

logger = logging.getLogger(__name__)


class GrasshopperMCPIntegration:
    """Direct integration with smolagents MCPClient using streamable-http transport."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8001/mcp"):
        """Initialize the MCP integration.
        
        Args:
            mcp_server_url: URL of the MCP streamable-http server
        """
        self.mcp_server_url = mcp_server_url
        self.mcp_client: Optional[MCPClient] = None
        self.tools: List[Tool] = []
        self.connected = False
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCPClient configuration for streamable-http transport."""
        return {
            "url": self.mcp_server_url,
            "transport": "streamable-http"  # Official recommended transport
        }
    
    def connect(self) -> bool:
        """Connect to the MCP server using smolagents MCPClient.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Use smolagents MCPClient directly with streamable-http transport
            self.mcp_client = MCPClient(self.get_mcp_config())
            self.tools = self.mcp_client.get_tools()
            self.connected = True
            
            logger.info(f"Connected to MCP server at {self.mcp_server_url}")
            logger.info(f"Available tools: {[tool.name for tool in self.tools]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.mcp_client:
            try:
                self.mcp_client.disconnect()
                logger.info("Disconnected from MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {e}")
            finally:
                self.mcp_client = None
                self.tools = []
                self.connected = False
    
    def get_tools(self) -> List[Tool]:
        """Get the list of available tools.
        
        Returns:
            List of smolagents Tool instances
        """
        if not self.connected:
            logger.warning("Not connected to MCP server. Call connect() first.")
            return []
        
        return self.tools
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self.connected
    
    def __enter__(self):
        """Context manager entry."""
        if self.connect():
            return self.tools
        else:
            raise ConnectionError(f"Failed to connect to MCP server at {self.mcp_server_url}")
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit."""
        self.disconnect()


def get_grasshopper_tools(mcp_server_url: str = "http://localhost:8001/mcp") -> List[Tool]:
    """Get Grasshopper tools using smolagents MCPClient.
    
    This is the recommended way to get tools for use with smolagents agents.
    
    Args:
        mcp_server_url: URL of the MCP streamable-http server
        
    Returns:
        List of Tool instances ready for use with smolagents agents
        
    Example:
        ```python
        # Use with smolagents CodeAgent
        tools = get_grasshopper_tools()
        agent = CodeAgent(tools=tools, model=model)
        
        # Or use context manager for automatic connection management
        with GrasshopperMCPIntegration() as tools:
            agent = CodeAgent(tools=tools, model=model)
            agent.run("Create a point at coordinates (0, 0, 0)")
        ```
    """
    integration = GrasshopperMCPIntegration(mcp_server_url)
    
    if integration.connect():
        try:
            return integration.get_tools()
        finally:
            integration.disconnect()
    else:
        logger.error(f"Failed to connect to MCP server at {mcp_server_url}")
        return []


def get_mcp_client_with_tools(mcp_server_url: str = "http://localhost:8001/mcp") -> Optional[MCPClient]:
    """Get a connected MCPClient instance.
    
    This provides direct access to the MCPClient for advanced use cases.
    
    Args:
        mcp_server_url: URL of the MCP streamable-http server
        
    Returns:
        Connected MCPClient instance or None if connection failed
        
    Example:
        ```python
        # Direct MCPClient usage
        mcp_client = get_mcp_client_with_tools()
        if mcp_client:
            with mcp_client as tools:
                agent = CodeAgent(tools=tools, model=model)
                agent.run("Connect component A to component B")
        ```
    """
    try:
        config = {
            "url": mcp_server_url,
            "transport": "streamable-http"
        }
        
        # MCPClient automatically connects on creation
        mcp_client = MCPClient(config)
        logger.info(f"MCPClient connected to {mcp_server_url}")
        return mcp_client
        
    except Exception as e:
        logger.error(f"Failed to create MCPClient: {e}")
        return None