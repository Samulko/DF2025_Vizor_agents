"""
Simplified STDIO-only Geometry Agent.

This implementation uses only STDIO transport for 100% reliable operation,
eliminating HTTP complexity and async/sync conflicts.
"""

import logging
import gc
import asyncio
import time
from copy import deepcopy
from pathlib import Path
from typing import List, Optional, Any

from smolagents import CodeAgent, tool
from smolagents.agents import PromptTemplates, SystemPromptStep, EMPTY_PROMPT_TEMPLATES
from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class GeometryAgentSTDIO:
    """STDIO-only Geometry Agent for maximum reliability.
    
    This agent uses only STDIO transport to avoid HTTP timeout issues
    and async/sync conflicts. Tool discovery happens once and is cached
    by the smolagents framework.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "geometry"):
        """Initialize the STDIO Geometry Agent.
        
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
        
        # STDIO-only MCP server parameters
        self.stdio_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "grasshopper_mcp.bridge"],
            env=None
        )
        
        # Get model configuration with low temperature for precise instruction following
        self.model = ModelProvider.get_model(model_name, temperature=0.1)
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Conversation memory for continuous chat
        self.conversation_history = []
        self.persistent_agent = None  # Keep agent instance for conversation continuity
        
        logger.info(f"Initialized {model_name} agent with STDIO-only transport (temperature=0.1 for precise instruction following)")
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt for the geometry agent."""
        try:
            # Get the project root directory
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # Go up to vizor_agents/
            prompt_path = project_root / "system_prompts" / "geometry_agent.md"
            
            if prompt_path.exists():
                return prompt_path.read_text(encoding='utf-8')
            else:
                logger.warning(f"System prompt file not found at {prompt_path}")
                return self._get_default_system_prompt()
        except Exception as e:
            logger.warning(f"Failed to load system prompt: {e}")
            return self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if file loading fails."""
        return """You are a Geometry Agent specialized in creating 3D geometry in Rhino Grasshopper.

Your role:
- Create geometric forms methodically, step by step
- Use MCP tools to generate Python script components in Grasshopper
- Only model what has been specifically requested
- Work precisely and follow instructions exactly
- Use Rhino.Geometry library functions in Python scripts
- Assign geometry outputs to variable 'a' for Grasshopper output

Always use the available MCP tools to create actual geometry in Grasshopper, not just descriptions."""
    
    def run(self, task: str) -> Any:
        """Execute the geometry task using STDIO transport.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from the agent execution
        """
        logger.info(f"🎯 Executing task with STDIO: {task[:100]}...")
        
        try:
            # Use MCPAdapt with STDIO for reliable MCP integration
            with MCPAdapt(
                self.stdio_params,
                SmolAgentsAdapter(),
            ) as mcp_tools:
                logger.info(f"Connected to MCP via STDIO with {len(mcp_tools)} tools")
                
                # Combine MCP tools with custom tools
                all_tools = list(mcp_tools) + self.custom_tools
                
                # Create or reuse persistent agent for conversation continuity
                if self.persistent_agent is None:
                    # TODO: Add custom system prompt when template compilation is fixed
                    self.persistent_agent = CodeAgent(
                        tools=all_tools,
                        model=self.model,
                        add_base_tools=True,
                        max_steps=self.max_steps,
                        additional_authorized_imports=self.SAFE_IMPORTS
                    )
                    logger.info("Created new persistent agent for conversation continuity")
                else:
                    logger.info("Using existing persistent agent (maintains conversation memory)")
                
                # Build conversation context for continuity
                conversation_context = self._build_conversation_context(task)
                
                # Execute task with conversation memory (reset=False for continuity)
                result = self.persistent_agent.run(conversation_context, reset=False)
                
                # Store conversation for future reference
                self._store_conversation(task, result)
                
                logger.info("✅ Task completed successfully with STDIO")
                
            # Force cleanup on Windows to reduce pipe warnings
            if hasattr(asyncio, 'ProactorEventLoop'):
                gc.collect()
                
            return result
                
        except Exception as e:
            logger.error(f"❌ STDIO execution failed: {e}")
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
            
            # Create fallback agent with low temperature
            # TODO: Add custom system prompt when template compilation is fixed
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
                "transport": "stdio",
                "available_tools": ["create_point_fallback", "create_line_fallback", "create_spiral_fallback"],
                "message": "MCP connection unavailable - using fallback tools"
            }
        
        return [create_point_fallback, create_line_fallback, create_spiral_fallback, get_connection_status]
    
    def _build_conversation_context(self, new_task: str) -> str:
        """Build conversation context for continuity.
        
        Args:
            new_task: The new task to execute
            
        Returns:
            Task with conversation context for continuity
        """
        if not self.conversation_history:
            # First interaction - just return the task
            return new_task
        
        # Build context from recent conversation history (last 3 interactions to avoid context overflow)
        recent_history = self.conversation_history[-3:]
        context_parts = []
        
        for i, interaction in enumerate(recent_history):
            context_parts.append(f"Previous interaction {i+1}:")
            context_parts.append(f"Human: {interaction['task']}")
            context_parts.append(f"Assistant: {interaction['result'][:200]}..." if len(str(interaction['result'])) > 200 else f"Assistant: {interaction['result']}")
            context_parts.append("")
        
        context_parts.append("Current task:")
        context_parts.append(new_task)
        
        return "\n".join(context_parts)
    
    def _store_conversation(self, task: str, result: Any) -> None:
        """Store conversation interaction for future reference.
        
        Args:
            task: The task that was executed
            result: The result from the task execution
        """
        self.conversation_history.append({
            "task": task,
            "result": str(result),
            "timestamp": time.time()
        })
        
        # Keep only last 10 interactions to prevent memory overflow
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def reset_conversation(self) -> None:
        """Reset conversation memory and agent state."""
        self.conversation_history = []
        self.persistent_agent = None
        logger.info("🔄 Conversation memory and agent state reset")
    
    def get_tool_info(self) -> dict:
        """Get information about available tools and connection status.
        
        Returns:
            Dictionary with tool and connection information
        """
        # Test MCP connection to get current status
        try:
            with MCPAdapt(self.stdio_params, SmolAgentsAdapter()) as mcp_tools:
                tool_names = [getattr(tool, 'name', str(tool)) for tool in mcp_tools]
                info = {
                    "connected": True,
                    "transport": "stdio",
                    "mcp_tools": len(mcp_tools),
                    "total_tools": len(mcp_tools) + len(self.custom_tools),
                    "mode": "stdio_only",
                    "mcp_tool_names": tool_names[:10],  # First 10 for brevity
                    "custom_tools": len(self.custom_tools),
                    "message": f"STDIO connection active with {len(mcp_tools)} tools",
                    "strategy": "simplified",
                    "agent_type": "STDIO"
                }
                
            # Force cleanup on Windows
            if hasattr(asyncio, 'ProactorEventLoop'):
                gc.collect()
                
            return info
        except Exception as e:
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
                "message": f"STDIO connection unavailable, using fallback tools",
                "strategy": "fallback",
                "agent_type": "STDIO"
            }


# Convenience function for creating the geometry agent
def create_geometry_agent_stdio(custom_tools: Optional[List] = None, model_name: str = "geometry") -> GeometryAgentSTDIO:
    """Create a STDIO-only geometry agent.
    
    Args:
        custom_tools: Additional custom tools to include
        model_name: Model configuration name
        
    Returns:
        GeometryAgentSTDIO instance
    """
    return GeometryAgentSTDIO(custom_tools=custom_tools, model_name=model_name)