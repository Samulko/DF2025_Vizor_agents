"""Geometry Agent with MCPAdapt integration.

This implementation uses mcpadapt for robust MCP server integration,
providing better async/sync handling and connection lifecycle management.
"""

import logging
import time
from typing import List, Optional, Any

from smolagents import CodeAgent, tool
from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class GeometryAgentMCPAdapt:
    """Geometry Agent using MCPAdapt for robust MCP integration.
    
    This agent uses mcpadapt library which provides better async/sync handling
    and connection lifecycle management than direct MCP client usage.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "geometry"):
        """Initialize the Geometry Agent with MCPAdapt support.
        
        Args:
            custom_tools: Additional custom tools to add to the agent
            model_name: Model configuration name (from settings)
        """
        self.custom_tools = custom_tools or []
        self.model_name = model_name
        self.max_steps = getattr(settings, 'AGENT_MAX_STEPS', 10)
        
        # Safe imports for code execution
        self.SAFE_IMPORTS = [
            "math", "numpy", "json", "re", "datetime", "collections",
            "itertools", "functools", "operator", "statistics"
        ]
        
        # Configure MCP server parameters based on transport mode
        self.server_params = settings.get_mcp_server_params()
        self.transport_mode = settings.mcp_transport_mode.lower()
        self.fallback_params = settings.get_mcp_connection_fallback_params()
        
        # Get model configuration
        self.model = ModelProvider.get_model(model_name)
        logger.info(f"Initialized {model_name} agent with MCPAdapt support (transport: {self.transport_mode})")
    
    def run(self, task: str) -> Any:
        """Execute the geometry task using MCPAdapt.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from the agent execution
        """
        logger.info(f"🎯 Executing task with MCPAdapt ({self.transport_mode}): {task[:100]}...")
        
        # Try MCPAdapt integration first
        try:
            # Use MCPAdapt with SmolAgentsAdapter for robust MCP integration
            with MCPAdapt(
                self.server_params,
                SmolAgentsAdapter(),
            ) as mcp_tools:
                logger.info(f"Connected to MCP via MCPAdapt ({self.transport_mode}) with {len(mcp_tools)} tools")
                
                # Combine MCP tools with custom tools
                all_tools = list(mcp_tools) + self.custom_tools
                
                # Create agent with all tools
                agent = CodeAgent(
                    tools=all_tools,
                    model=self.model,
                    add_base_tools=True,
                    max_steps=self.max_steps,
                    additional_authorized_imports=self.SAFE_IMPORTS
                )
                
                # Execute task
                result = agent.run(task)
                logger.info("✅ Task completed successfully with MCPAdapt")
                return result
                
        except Exception as e:
            logger.error(f"❌ MCPAdapt execution failed: {e}")
            
            # Check error type for better diagnostics
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["connection", "timeout", "mcp", "server", "stdio", "http"]):
                logger.warning(f"MCP {self.transport_mode} connection error detected: {e}")
                
                # Try fallback transport if using HTTP
                if self.transport_mode == "http":
                    return self._try_fallback_transport(task)
                else:
                    return self._run_with_fallback(task)
            elif "event loop" in error_str:
                logger.warning("Event loop error detected, falling back to basic tools")
                return self._run_with_fallback(task)
            else:
                logger.warning(f"General error in MCPAdapt execution: {e}")
                return self._run_with_fallback(task)
    
    def _try_fallback_transport(self, task: str) -> Any:
        """Try STDIO transport when HTTP fails.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from fallback transport or basic fallback tools
        """
        logger.warning("🔄 HTTP transport failed, trying STDIO fallback...")
        
        try:
            # Use STDIO fallback parameters
            with MCPAdapt(
                self.fallback_params,
                SmolAgentsAdapter(),
            ) as mcp_tools:
                logger.info(f"Connected to MCP via STDIO fallback with {len(mcp_tools)} tools")
                
                # Combine MCP tools with custom tools
                all_tools = list(mcp_tools) + self.custom_tools
                
                # Create agent with all tools
                agent = CodeAgent(
                    tools=all_tools,
                    model=self.model,
                    add_base_tools=True,
                    max_steps=self.max_steps,
                    additional_authorized_imports=self.SAFE_IMPORTS
                )
                
                # Execute task
                result = agent.run(task)
                logger.info("✅ Task completed successfully with STDIO fallback")
                return result
                
        except Exception as e:
            logger.error(f"❌ STDIO fallback also failed: {e}")
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
                add_base_tools=True,
                max_steps=self.max_steps,
                additional_authorized_imports=self.SAFE_IMPORTS
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
            return {
                "error": "Task execution failed",
                "message": f"Both MCP and fallback execution failed: {e}",
                "fallback_mode": True,
                "suggestion": "Check MCP server connection and try again"
            }
    
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
        def create_spiral_fallback(turns: int = 2, points: int = 20, max_radius: float = 3.0, height: float = 6.0) -> dict:
            """Create a spiral in fallback mode when MCP unavailable.
            
            Args:
                turns: Number of complete turns
                points: Number of points along the spiral
                max_radius: Maximum radius of the spiral
                height: Total height of the spiral
                
            Returns:
                Dictionary containing spiral data and fallback mode indicator
            """
            logger.warning("Using fallback tool - MCP connection unavailable")
            return {
                "type": "spiral",
                "parameters": {
                    "turns": turns,
                    "points": points,
                    "max_radius": max_radius,
                    "height": height
                },
                "fallback_mode": True,
                "message": "Spiral created in fallback mode - connect to Grasshopper for full functionality"
            }
        
        @tool
        def get_connection_status() -> dict:
            """Get current MCP connection status and health information.
            
            Returns:
                Dictionary containing connection status and diagnostic info
            """
            return {
                "connected": False,
                "mode": "fallback",
                "available_tools": ["create_point_fallback", "create_line_fallback", "create_spiral_fallback"],
                "message": "MCP connection unavailable - using fallback tools"
            }
        
        return [create_point_fallback, create_line_fallback, create_spiral_fallback, get_connection_status]
    
    def get_tool_info(self) -> dict:
        """Get information about available tools and connection status.
        
        Returns:
            Dictionary with tool and connection information
        """
        # Test MCP connection to get current status
        try:
            with MCPAdapt(self.server_params, SmolAgentsAdapter()) as mcp_tools:
                tool_names = [getattr(tool, 'name', str(tool)) for tool in mcp_tools]
                return {
                    "connected": True,
                    "transport": self.transport_mode,
                    "mcp_tools": len(mcp_tools),
                    "total_tools": len(mcp_tools) + len(self.custom_tools),
                    "mode": "mcpadapt",
                    "mcp_tool_names": tool_names[:10],  # First 10 for brevity
                    "custom_tools": len(self.custom_tools),
                    "message": f"MCPAdapt {self.transport_mode} connection active with {len(mcp_tools)} tools"
                }
        except Exception as e:
            # Try fallback transport if using HTTP
            if self.transport_mode == "http":
                try:
                    with MCPAdapt(self.fallback_params, SmolAgentsAdapter()) as mcp_tools:
                        tool_names = [getattr(tool, 'name', str(tool)) for tool in mcp_tools]
                        return {
                            "connected": True,
                            "transport": "stdio_fallback",
                            "mcp_tools": len(mcp_tools),
                            "total_tools": len(mcp_tools) + len(self.custom_tools),
                            "mode": "mcpadapt_fallback",
                            "mcp_tool_names": tool_names[:10],
                            "custom_tools": len(self.custom_tools),
                            "message": f"MCPAdapt STDIO fallback active with {len(mcp_tools)} tools (HTTP failed: {e})"
                        }
                except Exception as e2:
                    logger.error(f"Both HTTP and STDIO transports failed: HTTP={e}, STDIO={e2}")
            
            fallback_tools = self._create_fallback_tools()
            return {
                "connected": False,
                "transport": "none",
                "mcp_tools": 0,
                "total_tools": len(self.custom_tools) + len(fallback_tools),
                "mode": "fallback",
                "error": str(e),
                "fallback_tools": len(fallback_tools),
                "custom_tools": len(self.custom_tools),
                "message": f"MCPAdapt {self.transport_mode} connection unavailable, using fallback tools"
            }


# Convenience function for creating the geometry agent
def create_geometry_agent_mcpadapt(custom_tools: Optional[List] = None, model_name: str = "geometry") -> GeometryAgentMCPAdapt:
    """Create a geometry agent with MCPAdapt.
    
    Args:
        custom_tools: Additional custom tools to include
        model_name: Model configuration name
        
    Returns:
        GeometryAgentMCPAdapt instance
    """
    return GeometryAgentMCPAdapt(custom_tools=custom_tools, model_name=model_name)