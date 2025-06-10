"""Geometry Agent with proper MCP integration using MCPClient.

This implementation uses smolagents' MCPClient for proper connection lifecycle management,
treating the external MCP server as a toolbox that the agent can draw from.
"""

import logging
from typing import List, Optional, Any
from contextlib import contextmanager

from smolagents import MCPClient, CodeAgent
from mcp import StdioServerParameters

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class GeometryAgentWithMCP:
    """Geometry Agent that connects to external MCP server as a toolbox.
    
    This agent treats the external MCP server (grasshopper_mcp.bridge) as an external
    toolbox, connecting when needed and managing the connection lifecycle properly.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "geometry"):
        """Initialize the Geometry Agent with MCP support.
        
        Args:
            custom_tools: Additional custom tools to add to the agent
            model_name: Model configuration name (from settings)
        """
        self.custom_tools = custom_tools or []
        self.model_name = model_name
        self.mcp_client: Optional[MCPClient] = None
        self.agent: Optional[CodeAgent] = None
        self._connected = False
        
        # Get model configuration
        self.model = ModelProvider.get_model(model_name)
        logger.info(f"Initialized {model_name} agent with MCP toolbox support")
    
    def connect_to_mcp(self) -> bool:
        """Connect to the external MCP toolbox.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self._connected:
            logger.debug("Already connected to MCP toolbox")
            return True
        
        try:
            logger.info("Connecting to external MCP toolbox...")
            
            # Configure connection to external grasshopper_mcp.bridge
            server_params = StdioServerParameters(
                command="uv",
                args=["run", "python", "-m", "grasshopper_mcp.bridge"],
                env=None  # Use current environment
            )
            
            # Create and connect MCPClient
            self.mcp_client = MCPClient(server_params)
            self.mcp_client.connect()
            
            # Get tools from external MCP toolbox
            mcp_tools = self.mcp_client.get_tools()
            logger.info(f"Retrieved {len(mcp_tools)} tools from external MCP toolbox")
            
            # Combine MCP tools with any custom tools
            all_tools = list(mcp_tools) + self.custom_tools
            
            # Create agent with tools from external toolbox
            self.agent = CodeAgent(
                tools=all_tools,
                model=self.model,
                add_base_tools=True  # Include basic smolagents tools
            )
            
            self._connected = True
            logger.info(f"✅ Connected to MCP toolbox with {len(all_tools)} total tools")
            
            # Log available tool names for debugging
            tool_names = [tool.name for tool in mcp_tools]
            logger.debug(f"MCP tools available: {tool_names}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP toolbox: {e}")
            self._cleanup()
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MCP toolbox and clean up resources."""
        if not self._connected:
            return
        
        logger.info("Disconnecting from MCP toolbox...")
        self._cleanup()
        logger.info("✅ Disconnected from MCP toolbox")
    
    def _cleanup(self) -> None:
        """Internal cleanup of MCP resources."""
        if self.mcp_client:
            try:
                self.mcp_client.disconnect()
            except Exception as e:
                logger.warning(f"Error during MCP disconnect: {e}")
            self.mcp_client = None
        
        self.agent = None
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to MCP toolbox."""
        return self._connected
    
    def run(self, task: str) -> Any:
        """Run a task using tools from the external MCP toolbox.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from the agent execution
            
        Raises:
            RuntimeError: If not connected to MCP toolbox
        """
        if not self._connected:
            logger.info("Not connected to MCP toolbox, attempting to connect...")
            if not self.connect_to_mcp():
                raise RuntimeError(
                    "Cannot execute task: Failed to connect to MCP toolbox. "
                    "Ensure the grasshopper_mcp.bridge server is available."
                )
        
        if not self.agent:
            raise RuntimeError("Agent not initialized despite successful MCP connection")
        
        logger.info(f"Executing task using MCP toolbox: {task}")
        
        try:
            result = self.agent.run(task)
            logger.info("✅ Task completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            # Re-raise the exception for the caller to handle
            raise
    
    def get_tool_info(self) -> dict:
        """Get information about available tools.
        
        Returns:
            Dictionary with tool information
        """
        if not self._connected or not self.mcp_client:
            return {
                "connected": False,
                "mcp_tools": 0,
                "custom_tools": len(self.custom_tools),
                "total_tools": len(self.custom_tools)
            }
        
        try:
            mcp_tools = self.mcp_client.get_tools()
            return {
                "connected": True,
                "mcp_tools": len(mcp_tools),
                "custom_tools": len(self.custom_tools),
                "total_tools": len(mcp_tools) + len(self.custom_tools),
                "mcp_tool_names": [tool.name for tool in mcp_tools[:10]]  # First 10 for brevity
            }
        except Exception as e:
            logger.error(f"Error getting tool info: {e}")
            return {
                "connected": True,
                "error": str(e)
            }
    
    # Context manager support for clean resource management
    def __enter__(self):
        """Enter context manager - connect to MCP toolbox."""
        if not self.connect_to_mcp():
            raise RuntimeError("Failed to connect to MCP toolbox")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - disconnect from MCP toolbox."""
        self.disconnect()


@contextmanager
def create_geometry_agent_with_mcp(custom_tools: Optional[List] = None, model_name: str = "geometry"):
    """Context manager for creating a geometry agent with MCP toolbox.
    
    Args:
        custom_tools: Additional custom tools to include
        model_name: Model configuration name
        
    Yields:
        GeometryAgentWithMCP: Connected geometry agent
        
    Example:
        with create_geometry_agent_with_mcp() as agent:
            result = agent.run("Create a point at coordinates (0, 0, 0)")
            print(result)
    """
    agent = GeometryAgentWithMCP(custom_tools=custom_tools, model_name=model_name)
    try:
        if not agent.connect_to_mcp():
            raise RuntimeError("Failed to connect to MCP toolbox")
        yield agent
    finally:
        agent.disconnect()


# Convenience functions for different usage patterns
def create_geometry_agent(auto_connect: bool = True, custom_tools: Optional[List] = None) -> GeometryAgentWithMCP:
    """Create a geometry agent with MCP toolbox.
    
    Args:
        auto_connect: Whether to automatically connect to MCP on creation
        custom_tools: Additional custom tools to include
        
    Returns:
        GeometryAgentWithMCP instance
    """
    agent = GeometryAgentWithMCP(custom_tools=custom_tools)
    
    if auto_connect:
        if not agent.connect_to_mcp():
            logger.warning("Failed to auto-connect to MCP toolbox")
    
    return agent