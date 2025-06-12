"""
Hybrid Geometry Agent with optimized HTTP/STDIO MCP integration.

This implementation addresses the async/sync bridge problem by using:
1. HTTP for fast tool discovery 
2. STDIO for reliable task execution
3. Proper connection lifecycle management
4. Event loop isolation
"""

import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Any
from threading import Lock

from smolagents import CodeAgent, tool
from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class GeometryAgentHybrid:
    """Hybrid Geometry Agent with optimized MCP transport strategy.
    
    This agent uses a dual transport approach:
    - HTTP for fast tool discovery (60x faster)
    - STDIO for reliable task execution (proven stable)
    
    This solves the async/sync bridge problem by avoiding long-running
    HTTP connections in smolagents execution context.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "geometry"):
        """Initialize the Hybrid Geometry Agent.
        
        Args:
            custom_tools: Additional custom tools to add to the agent
            model_name: Model configuration name (from settings)
        """
        self.custom_tools = custom_tools or []
        self.model_name = model_name
        self.max_steps = getattr(settings, 'AGENT_MAX_STEPS', 10)
        
        # Transport configuration
        self.http_params = {
            "url": settings.mcp_http_url,
            "transport": "streamable-http"
        }
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command,
            args=settings.mcp_stdio_args.split(","),
            env=None
        )
        
        # Connection management
        self._tool_cache = None
        self._cache_lock = Lock()
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes
        
        # Safe imports for code execution
        self.SAFE_IMPORTS = [
            "math", "numpy", "json", "re", "datetime", "collections",
            "itertools", "functools", "operator", "statistics"
        ]
        
        # Get model configuration
        self.model = ModelProvider.get_model(model_name)
        logger.info(f"Initialized hybrid geometry agent with dual transport strategy")
    
    def get_tools_fast(self) -> List:
        """Get tools using fast HTTP discovery with caching.
        
        Returns:
            List of MCP tools compatible with smolagents
        """
        with self._cache_lock:
            current_time = time.time()
            
            # Check cache validity
            if (self._tool_cache is not None and 
                current_time - self._cache_timestamp < self._cache_ttl):
                logger.debug("Using cached tools")
                return self._tool_cache
            
            # Refresh cache
            try:
                logger.info("Discovering tools via HTTP transport...")
                tools = self._discover_tools_http()
                self._tool_cache = tools
                self._cache_timestamp = current_time
                logger.info(f"✅ Cached {len(tools)} tools via HTTP transport")
                return tools
                
            except Exception as e:
                logger.warning(f"HTTP tool discovery failed: {e}")
                # Fallback to STDIO discovery
                try:
                    tools = self._discover_tools_stdio()
                    self._tool_cache = tools
                    self._cache_timestamp = current_time
                    logger.info(f"✅ Cached {len(tools)} tools via STDIO fallback")
                    return tools
                except Exception as e2:
                    logger.error(f"Both HTTP and STDIO tool discovery failed: {e2}")
                    return self._create_fallback_tools()
    
    def _discover_tools_http(self) -> List:
        """Discover tools via HTTP in isolated thread to avoid event loop conflicts.
        
        Returns:
            List of MCP tools
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._async_discover_http)
            return future.result(timeout=30)
    
    def _async_discover_http(self) -> List:
        """HTTP tool discovery in separate event loop.
        
        Returns:
            List of MCP tools
        """
        # Create fresh event loop to avoid conflicts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self._fetch_tools_http())
        finally:
            loop.close()
            # Clean up event loop reference
            asyncio.set_event_loop(None)
    
    async def _fetch_tools_http(self) -> List:
        """Actual HTTP tool fetching.
        
        Returns:
            List of MCP tools
        """
        async with MCPAdapt(self.http_params, SmolAgentsAdapter()) as tools:
            # Convert to list to avoid async context issues
            return list(tools)
    
    def _discover_tools_stdio(self) -> List:
        """Discover tools via STDIO transport.
        
        Returns:
            List of MCP tools
        """
        with MCPAdapt(self.stdio_params, SmolAgentsAdapter()) as tools:
            return list(tools)
    
    def run(self, task: str) -> Any:
        """Execute the geometry task using hybrid transport strategy.
        
        Uses STDIO for execution to avoid async/sync conflicts while
        benefiting from fast HTTP tool discovery.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from the agent execution
        """
        logger.info(f"🎯 Executing task with hybrid strategy: {task[:100]}...")
        
        try:
            # Use STDIO for reliable execution
            with MCPAdapt(self.stdio_params, SmolAgentsAdapter()) as mcp_tools:
                logger.info(f"Connected to MCP via STDIO with {len(mcp_tools)} tools")
                
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
                logger.info("✅ Task completed successfully with hybrid strategy")
                return result
                
        except Exception as e:
            logger.error(f"❌ Hybrid execution failed: {e}")
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
        def create_point_hybrid_fallback(x: float, y: float, z: float) -> dict:
            """Create a point in fallback mode when MCP unavailable.
            
            Args:
                x: X coordinate of the point
                y: Y coordinate of the point  
                z: Z coordinate of the point
                
            Returns:
                Dictionary containing point data and fallback mode indicator
            """
            logger.warning("Using hybrid fallback tool - MCP connection unavailable")
            return {
                "type": "point", 
                "coordinates": {"x": x, "y": y, "z": z},
                "fallback_mode": True,
                "transport": "hybrid_fallback",
                "message": "Point created in hybrid fallback mode - connect to Grasshopper for full functionality"
            }
        
        @tool
        def get_hybrid_connection_status() -> dict:
            """Get current hybrid MCP connection status and health information.
            
            Returns:
                Dictionary containing connection status and diagnostic info
            """
            # Test current tool availability
            try:
                tools = self.get_tools_fast()
                tool_count = len(tools)
                mode = "http_cached" if self._tool_cache else "discovering"
            except Exception:
                tool_count = 0
                mode = "fallback"
                
            return {
                "connected": tool_count > 0,
                "mode": mode,
                "available_tools": tool_count,
                "cache_age": time.time() - self._cache_timestamp if self._tool_cache else None,
                "transport_strategy": "hybrid (HTTP discovery + STDIO execution)",
                "message": f"Hybrid agent with {tool_count} cached tools"
            }
        
        return [create_point_hybrid_fallback, get_hybrid_connection_status]
    
    def get_tool_info(self) -> dict:
        """Get information about available tools and connection status.
        
        Returns:
            Dictionary with tool and connection information
        """
        try:
            # Use fast HTTP tool discovery
            tools = self.get_tools_fast()
            
            return {
                "connected": True,
                "transport": "hybrid",
                "strategy": "HTTP discovery + STDIO execution",
                "mcp_tools": len(tools),
                "total_tools": len(tools) + len(self.custom_tools),
                "mode": "hybrid_optimized",
                "custom_tools": len(self.custom_tools),
                "cache_status": "cached" if self._tool_cache else "discovering",
                "cache_age": time.time() - self._cache_timestamp if self._tool_cache else None,
                "message": f"Hybrid strategy active with {len(tools)} tools (HTTP discovery + STDIO execution)"
            }
            
        except Exception as e:
            fallback_tools = self._create_fallback_tools()
            return {
                "connected": False,
                "transport": "none",
                "strategy": "fallback_only",
                "mcp_tools": 0,
                "total_tools": len(self.custom_tools) + len(fallback_tools),
                "mode": "fallback",
                "error": str(e),
                "fallback_tools": len(fallback_tools),
                "custom_tools": len(self.custom_tools),
                "message": "Hybrid strategy unavailable, using fallback tools"
            }


# Convenience function for creating the hybrid geometry agent
def create_geometry_agent_hybrid(custom_tools: Optional[List] = None, model_name: str = "geometry") -> GeometryAgentHybrid:
    """Create a geometry agent with hybrid transport strategy.
    
    Args:
        custom_tools: Additional custom tools to include
        model_name: Model configuration name
        
    Returns:
        GeometryAgentHybrid instance
    """
    return GeometryAgentHybrid(custom_tools=custom_tools, model_name=model_name)