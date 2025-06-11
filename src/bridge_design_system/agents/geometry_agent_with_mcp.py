"""Geometry Agent with proper MCP integration using MCPClient.

This implementation uses smolagents' MCPClient for proper connection lifecycle management,
treating the external MCP server as a toolbox that the agent can draw from.
"""

import logging
import time
from typing import List, Optional, Any
from contextlib import contextmanager

from smolagents import ToolCollection, CodeAgent, tool
from mcp import StdioServerParameters

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings

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
        self._max_reconnect_attempts = getattr(settings, 'MCP_MAX_RECONNECT_ATTEMPTS', 3)
        self._connection_timeout = getattr(settings, 'MCP_CONNECTION_TIMEOUT', 10)
        self.max_steps = getattr(settings, 'AGENT_MAX_STEPS', 10)
        
        # Safe imports for code execution
        self.SAFE_IMPORTS = [
            "math", "numpy", "json", "re", "datetime", "collections",
            "itertools", "functools", "operator", "statistics"
        ]
        
        # Configure MCP server parameters
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "grasshopper_mcp.bridge"],
            env=None  # Use current environment
        )
        
        # Get model configuration
        self.model = ModelProvider.get_model(model_name)
        logger.info(f"Initialized {model_name} agent with MCP toolbox support")
    
    def connect_to_mcp(self) -> bool:
        """Connect to the external MCP toolbox using ToolCollection pattern.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self._connected and self.health_check():
            logger.debug("Already connected to MCP toolbox and healthy")
            return True
        
        try:
            logger.info("Connecting to external MCP toolbox...")
            
            # Configure connection to external grasshopper_mcp.bridge
            server_params = StdioServerParameters(
                command="uv",
                args=["run", "python", "-m", "grasshopper_mcp.bridge"],
                env=None  # Use current environment
            )
            
            # Use ToolCollection.from_mcp (the working pattern)
            start_time = time.time()
            
            with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
                # Get tools from the collection
                mcp_tools = list(tool_collection.tools)
                
                # Check if connection took too long
                connection_time = time.time() - start_time
                if connection_time > self._connection_timeout:
                    logger.warning(f"Connection took {connection_time:.1f}s, longer than timeout {self._connection_timeout}s")
                
                if not mcp_tools:
                    logger.warning("No tools retrieved from MCP server")
                    return False
                    
                logger.info(f"Retrieved {len(mcp_tools)} tools from external MCP toolbox")
                
                # Validate tools
                if not self._validate_tools(mcp_tools):
                    logger.error("Tool validation failed")
                    return False
                
                # Store tools for later use
                self.mcp_tools = mcp_tools
                
                # Combine MCP tools with any custom tools
                all_tools = list(mcp_tools) + self.custom_tools
                
                # Create agent with tools from external toolbox
                self.agent = CodeAgent(
                    tools=all_tools,
                    model=self.model,
                    add_base_tools=True  # Include basic smolagents tools
                )
                
                self._connected = True
                self._connection_healthy = True
                self._reconnect_attempts = 0
                self._last_health_check = time.time()
                
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
        # With ToolCollection pattern, cleanup is automatic via context manager
        self.mcp_tools = []
        self.agent = None
        self._connected = False
        self._connection_healthy = False
    
    def health_check(self) -> bool:
        """Verify connection is alive and healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if not self._connected:
            return False
        
        # Rate limit health checks
        if (self._last_health_check and 
            time.time() - self._last_health_check < self._health_check_interval):
            return self._connection_healthy
        
        # With ToolCollection pattern, we check if we have tools and agent
        healthy = (len(self.mcp_tools) > 0 and self.agent is not None)
        
        self._connection_healthy = healthy
        self._last_health_check = time.time()
        
        if not healthy:
            logger.warning("Health check failed: No tools or agent available")
        else:
            logger.debug(f"Health check passed: {len(self.mcp_tools)} tools available")
        
        return healthy
    
    def auto_reconnect(self, max_retries: int = None) -> bool:
        """Reconnect with exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts (uses config default if None)
            
        Returns:
            True if reconnection successful, False otherwise
        """
        if max_retries is None:
            max_retries = self._max_reconnect_attempts
            
        logger.info(f"Attempting auto-reconnection (attempt {self._reconnect_attempts + 1}/{max_retries})")
        
        if self._reconnect_attempts >= max_retries:
            logger.error(f"Maximum reconnection attempts ({max_retries}) exceeded")
            return False
        
        # Calculate backoff delay
        backoff_delay = min(30, self._reconnect_backoff_base ** self._reconnect_attempts)
        
        if self._reconnect_attempts > 0:
            logger.info(f"Waiting {backoff_delay}s before reconnection attempt...")
            time.sleep(backoff_delay)
        
        # Clean up existing connection
        self._cleanup()
        
        # Attempt reconnection
        self._reconnect_attempts += 1
        
        if self.connect_to_mcp():
            logger.info(f"✅ Auto-reconnection successful after {self._reconnect_attempts} attempts")
            return True
        else:
            logger.warning(f"❌ Auto-reconnection attempt {self._reconnect_attempts} failed")
            return False
    
    def _validate_tools(self, tools: List) -> bool:
        """Validate that retrieved tools are valid.
        
        Args:
            tools: List of tools to validate
            
        Returns:
            True if tools are valid, False otherwise
        """
        if not tools:
            logger.error("No tools provided for validation")
            return False
        
        # Check for expected minimum number of tools
        min_expected_tools = 5  # Adjust based on your requirements
        if len(tools) < min_expected_tools:
            logger.warning(f"Only {len(tools)} tools available, expected at least {min_expected_tools}")
        
        # Validate that tools have expected attributes
        for i, tool in enumerate(tools[:3]):  # Check first 3 tools
            if not hasattr(tool, 'name'):
                logger.error(f"Tool {i} missing 'name' attribute")
                return False
        
        logger.debug(f"Tool validation passed: {len(tools)} tools validated")
        return True
    
    def _refresh_tools(self) -> bool:
        """Refresh tools from MCP server.
        
        Returns:
            True if tools refreshed successfully, False otherwise
        """
        if not self._connected:
            logger.warning("Cannot refresh tools: not connected to MCP")
            return False
        
        try:
            logger.debug("Refreshing tools by reconnecting to MCP server...")
            
            # With ToolCollection pattern, we need to reconnect to refresh
            return self.connect_to_mcp()
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh tools: {e}")
            return False
    
    def _create_fallback_tools(self) -> List:
        """Create basic fallback tools when MCP unavailable.
        
        Returns:
            List of fallback tools
        """
        @tool
        def create_point_fallback(x: float, y: float, z: float) -> dict:
            """Create a point in fallback mode when MCP unavailable.
            
            Args:
                x: X coordinate of the point
                y: Y coordinate of the point  
                z: Z coordinate of the point
                
            Returns:
                Dictionary containing point data and fallback mode indicator
            """
            logger.warning("Using fallback tool - MCP connection unavailable")
            return {
                "type": "point", 
                "coordinates": {"x": x, "y": y, "z": z},
                "fallback_mode": True,
                "message": "Point created in fallback mode - connect to Grasshopper for full functionality"
            }
        
        @tool
        def create_line_fallback(start_x: float, start_y: float, start_z: float, 
                                end_x: float, end_y: float, end_z: float) -> dict:
            """Create a line in fallback mode when MCP unavailable.
            
            Args:
                start_x: X coordinate of line start point
                start_y: Y coordinate of line start point
                start_z: Z coordinate of line start point
                end_x: X coordinate of line end point
                end_y: Y coordinate of line end point
                end_z: Z coordinate of line end point
                
            Returns:
                Dictionary containing line data and fallback mode indicator
            """
            logger.warning("Using fallback tool - MCP connection unavailable")
            return {
                "type": "line",
                "start": {"x": start_x, "y": start_y, "z": start_z},
                "end": {"x": end_x, "y": end_y, "z": end_z},
                "fallback_mode": True,
                "message": "Line created in fallback mode - connect to Grasshopper for full functionality"
            }
        
        @tool
        def get_connection_status() -> dict:
            """Get current MCP connection status and health information.
            
            Returns:
                Dictionary containing connection status, health, and diagnostic info
            """
            return {
                "connected": self._connected,
                "healthy": self._connection_healthy,
                "reconnect_attempts": self._reconnect_attempts,
                "last_health_check": self._last_health_check,
                "message": "MCP connection unavailable - using fallback tools"
            }
        
        return [create_point_fallback, create_line_fallback, get_connection_status]
    
    def is_connected(self) -> bool:
        """Check if connected to MCP toolbox."""
        return self._connected
    
    def run(self, task: str) -> Any:
        """Run a task using tools from the external MCP toolbox with fallback support.
        
        This method creates a fresh ToolCollection context for each run to avoid 
        "Event loop is closed" errors. The agent is created and used entirely within
        the active context.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from the agent execution
        """
        logger.info(f"🎯 Executing task: {task[:100]}...")
        
        # Try MCP connection first
        try:
            # Create agent inside ToolCollection context (the working pattern)
            with ToolCollection.from_mcp(self.server_params, trust_remote_code=True) as tool_collection:
                # Get tools and combine with custom tools
                mcp_tools = list(tool_collection.tools)
                all_tools = mcp_tools + self.custom_tools
                
                logger.info(f"Connected to MCP with {len(mcp_tools)} tools")
                
                # Create agent inside the active context
                agent = CodeAgent(
                    tools=all_tools,
                    model=self.model,
                    add_base_tools=True,
                    max_steps=self.max_steps,
                    additional_authorized_imports=self.SAFE_IMPORTS
                )
                
                # Execute task while context is active
                result = agent.run(task)
                logger.info("✅ Task completed successfully with MCP tools")
                return result
                
        except Exception as e:
            logger.error(f"❌ MCP execution failed: {e}")
            
            # Check if it's a connection-related error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["connection", "timeout", "mcp", "server", "stdio"]):
                logger.warning("MCP connection error detected, falling back to basic tools")
            elif "event loop" in error_str:
                logger.warning("Event loop error detected, falling back to basic tools")
            else:
                logger.warning(f"General error in MCP execution: {e}")
            
            # Fall back to basic tools
            return self._run_with_fallback(task)
    
    def _run_with_fallback(self, task: str) -> Any:
        """Run task with fallback tools when MCP unavailable.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from fallback agent execution
        """
        logger.warning("🔄 Using fallback mode - MCP unavailable")
        
        try:
            # Create agent with fallback tools
            fallback_tools = self._create_fallback_tools() + self.custom_tools
            
            fallback_agent = CodeAgent(
                tools=fallback_tools,
                model=self.model,
                add_base_tools=True
            )
            
            # Add context about fallback mode to the task
            fallback_task = f"""
{task}

IMPORTANT: You are currently in fallback mode because the Grasshopper MCP connection is unavailable. 
You have access to basic geometry tools that return data structures instead of creating actual geometry.
Please inform the user that full Grasshopper functionality requires MCP connection restoration.
"""
            
            result = fallback_agent.run(fallback_task)
            logger.info("✅ Task completed in fallback mode")
            return result
            
        except Exception as e:
            logger.error(f"❌ Even fallback execution failed: {e}")
            # Return a helpful error message
            return {
                "error": "Task execution failed",
                "message": f"Both MCP and fallback execution failed: {e}",
                "fallback_mode": True,
                "suggestion": "Check MCP server connection and try again"
            }
    
    def get_tool_info(self) -> dict:
        """Get comprehensive information about available tools and connection status.
        
        Returns:
            Dictionary with detailed tool and connection information
        """
        base_info = {
            "connected": self._connected,
            "healthy": self._connection_healthy,
            "reconnect_attempts": self._reconnect_attempts,
            "last_health_check": self._last_health_check,
            "custom_tools": len(self.custom_tools),
            "fallback_available": True
        }
        
        if not self._connected:
            fallback_tools = self._create_fallback_tools()
            return {
                **base_info,
                "mcp_tools": 0,
                "total_tools": len(self.custom_tools) + len(fallback_tools),
                "mode": "fallback",
                "message": "MCP connection unavailable, using fallback tools"
            }
        
        try:
            tool_names = [tool.name for tool in self.mcp_tools] if self.mcp_tools else []
            
            return {
                **base_info,
                "mcp_tools": len(self.mcp_tools),
                "total_tools": len(self.mcp_tools) + len(self.custom_tools),
                "mode": "mcp" if len(self.mcp_tools) > 0 else "fallback",
                "mcp_tool_names": tool_names[:10],  # First 10 for brevity
                "all_tool_names": tool_names if len(tool_names) <= 20 else tool_names[:20] + ["..."],
                "message": f"MCP connection active with {len(self.mcp_tools)} tools"
            }
        except Exception as e:
            logger.error(f"Error getting tool info: {e}")
            return {
                **base_info,
                "mcp_tools": 0,
                "total_tools": len(self.custom_tools),
                "mode": "error",
                "error": str(e),
                "message": "Error retrieving MCP tools"
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