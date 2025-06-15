"""
JSON-based Geometry Agent using ToolCallingAgent for MCP integration.

This implementation uses ToolCallingAgent instead of CodeAgent to eliminate
JSON parsing issues and provide native MCP tool integration. The agent
generates Python scripts dynamically as JSON tool arguments.
"""

import logging
import gc
import asyncio
import time
from copy import deepcopy
from pathlib import Path
from typing import List, Optional, Any

from smolagents import ToolCallingAgent, MCPClient
from mcp import StdioServerParameters

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings
from ..state.component_registry import ComponentRegistry
from ..tools.memory_tools import remember, recall, search_memory, clear_memory

logger = get_logger(__name__)


class GeometryAgentJSON:
    """JSON-based Geometry Agent using ToolCallingAgent for maximum reliability.
    
    This agent uses ToolCallingAgent which handles JSON tool calls natively,
    eliminating the JSON parsing confusion that occurs with CodeAgent when
    using MCP tools. The LLM dynamically generates Python scripts as JSON
    tool arguments.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "geometry", 
                 component_registry: Optional[ComponentRegistry] = None):
        """Initialize the JSON Geometry Agent.
        
        Args:
            custom_tools: Additional custom tools to add to the agent
            model_name: Model configuration name (from settings)
            component_registry: Registry for tracking components across agents
        """
        self.custom_tools = custom_tools or []
        self.model_name = model_name
        self.max_steps = getattr(settings, 'AGENT_MAX_STEPS', 10)
        self.component_registry = component_registry
        
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
        
        # Conversation memory for continuous chat (separate from agent lifecycle)
        self.conversation_history = []
        
        # Memory tools for persistent context
        self.memory_tools = [remember, recall, search_memory, clear_memory]
        
        logger.info(f"Initialized {model_name} JSON agent with ToolCallingAgent (temperature=0.1 for precise instruction following)")
    
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

Key differences from CodeAgent:
- You make tool calls using JSON format, not Python code
- You can generate complex Python scripts as arguments to tools
- Each tool call is separate and sequential (ReAct pattern)
- You maintain state across steps through your internal memory

Always use the available MCP tools to create actual geometry in Grasshopper, not just descriptions."""
    
    def run(self, task: str) -> Any:
        """Execute the geometry task using ToolCallingAgent.
        
        Args:
            task: The task description for the agent to execute
            
        Returns:
            Result from the agent execution
        """
        logger.info(f"🎯 Executing task with JSON agent: {task[:100]}...")
        
        try:
            # Use MCPClient for native smolagents MCP integration
            with MCPClient(self.stdio_params) as mcp_tools:
                logger.info(f"Connected to MCP via MCPClient with {len(mcp_tools)} tools")
                
                # Combine MCP tools with custom tools and memory tools
                all_tools = list(mcp_tools) + self.custom_tools + self.memory_tools
                
                # Create ToolCallingAgent for JSON-based tool calling
                # ToolCallingAgent handles JSON natively, eliminating parsing issues
                json_agent = ToolCallingAgent(
                    tools=all_tools,
                    model=self.model,
                    max_steps=self.max_steps
                )
                logger.info("Created ToolCallingAgent with native JSON tool calling")
                
                # Build conversation context for continuity
                conversation_context = self._build_conversation_context(task)
                
                # Execute task with JSON agent and conversation context
                result = json_agent.run(conversation_context)
                
                # Extract and register components if registry is available
                if self.component_registry:
                    self._extract_and_register_components(task, result)
                
                # Store conversation for future reference
                self._store_conversation(task, result)
                
                logger.info("✅ Task completed successfully with JSON agent")
                
            # Force cleanup on Windows to reduce pipe warnings
            if hasattr(asyncio, 'ProactorEventLoop'):
                gc.collect()
                
            return result
                
        except Exception as e:
            logger.error(f"❌ JSON agent execution failed: {e}")
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
            
            # Create fallback ToolCallingAgent
            fallback_agent = ToolCallingAgent(
                tools=fallback_tools + self.memory_tools,
                model=self.model,
                max_steps=self.max_steps
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
        from smolagents import tool
        
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
        """Build conversation context for continuity with ToolCallingAgent.
        
        ToolCallingAgent maintains state internally but we provide conversation
        history as context for better continuity. The new_task may already
        include structured component references from the TriageAgent.
        
        Args:
            new_task: The new task to execute (may include component references)
            
        Returns:
            Task with conversation context for continuity
        """
        # Check if task already has structured component references from TriageAgent
        if "COMPONENT REFERENCES:" in new_task:
            logger.info("Task includes component references from registry")
        
        # Try to get previous context from memory
        memory_context = ""
        try:
            # Get component memories
            component_memories = recall("components")
            if component_memories and "No memories found" not in component_memories:
                memory_context += f"\nSTORED COMPONENTS:\n{component_memories}\n"
            
            # Get geometry context
            geometry_context = recall("geometry", "current_work")
            if geometry_context and "No memory found" not in geometry_context:
                memory_context += f"\nCURRENT GEOMETRY WORK:\n{geometry_context}\n"
        except:
            pass
            
        if not self.conversation_history:
            # First interaction - include memory prompt
            return f"""{new_task}

You have access to memory tools to maintain context:
- remember(category, key, value) - Store important information
- recall(category, key) - Retrieve stored information  
- search_memory(query) - Search all memories

IMPORTANT: Use remember() to store:
- Component IDs when created (category: "components")
- Current geometry work (category: "geometry", key: "current_work")
- Any errors and solutions (category: "errors")

Remember: You are a ToolCallingAgent that makes JSON tool calls.
The LLM generates Python scripts dynamically as tool arguments.
{memory_context}"""
        
        # Build context from recent conversation history (last 3 interactions to avoid context overflow)
        recent_history = self.conversation_history[-3:]
        context_parts = []
        
        for i, interaction in enumerate(recent_history):
            context_parts.append(f"Previous interaction {i+1}:")
            context_parts.append(f"Human: {interaction['task']}")
            # Truncate long results to keep context manageable
            result_text = str(interaction['result'])
            if len(result_text) > 200:
                context_parts.append(f"Assistant: {result_text[:200]}...")
            else:
                context_parts.append(f"Assistant: {result_text}")
            context_parts.append("")
        
        context_parts.append("Current task:")
        context_parts.append(new_task)
        context_parts.append("\nRemember to use memory tools to store component IDs and geometry work!")
        
        return memory_context + "\n".join(context_parts)
    
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
        """Reset conversation memory."""
        self.conversation_history = []
        logger.info("🔄 Conversation memory reset")
    
    def get_tool_info(self) -> dict:
        """Get information about available tools and connection status.
        
        Returns:
            Dictionary with tool and connection information
        """
        # Test MCP connection to get current status
        try:
            with MCPClient(self.stdio_params) as mcp_tools:
                tool_names = [getattr(tool, 'name', str(tool)) for tool in mcp_tools]
                info = {
                    "connected": True,
                    "transport": "stdio",
                    "mcp_tools": len(mcp_tools),
                    "total_tools": len(mcp_tools) + len(self.custom_tools),
                    "mode": "json_agent",
                    "mcp_tool_names": tool_names[:10],  # First 10 for brevity
                    "custom_tools": len(self.custom_tools),
                    "message": f"JSON agent active with {len(mcp_tools)} MCP tools",
                    "strategy": "json_calling",
                    "agent_type": "ToolCallingAgent"
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
                "message": f"MCP connection unavailable, using fallback tools",
                "strategy": "json_calling_fallback",
                "agent_type": "ToolCallingAgent"
            }
    
    def _extract_and_register_components(self, task: str, result: Any) -> None:
        """
        Extract component IDs from ToolCallingAgent results and register them.
        
        Args:
            task: The original task description
            result: Result from ToolCallingAgent execution
        """
        try:
            result_str = str(result)
            
            # Look for component ID patterns in the result
            # Pattern 1: {"id": "uuid-here", ...}
            import re
            import json
            
            # Try to find JSON with 'id' field
            json_pattern = r'\{[^{}]*"id"\s*:\s*"([^"]+)"[^{}]*\}'
            matches = re.findall(json_pattern, result_str)
            
            for component_id in matches:
                # Infer component type and name from task
                component_type = self._infer_component_type(task)
                component_name = self._generate_component_name(task, component_type)
                
                # Register the component
                success = self.component_registry.register_component(
                    component_id=component_id,
                    component_type=component_type,
                    name=component_name,
                    description=task[:200],  # First 200 chars of task as description
                    properties={"source_task": task, "agent_type": "ToolCallingAgent"}
                )
                
                if success:
                    logger.info(f"📝 Registered component: {component_id} ({component_type}) - {component_name}")
                else:
                    logger.warning(f"⚠️ Failed to register component: {component_id}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract components from result: {e}")
    
    def _infer_component_type(self, task: str) -> str:
        """
        Infer component type from task description.
        Specialized for timber truss bridge components.
        
        Args:
            task: Task description
            
        Returns:
            Inferred component type
        """
        task_lower = task.lower()
        
        # Timber truss bridge specific components
        
        # Truss elements
        if any(word in task_lower for word in ["top chord", "upper chord", "compression chord"]):
            return "top_chord"
        elif any(word in task_lower for word in ["bottom chord", "lower chord", "tension chord"]):
            return "bottom_chord"
        elif any(word in task_lower for word in ["web member", "diagonal member"]):
            return "web_member"
        elif any(word in task_lower for word in ["diagonal", "brace", "cross brace"]):
            return "diagonal"
        elif any(word in task_lower for word in ["vertical", "post", "vertical post"]):
            return "vertical"
        elif any(word in task_lower for word in ["strut", "compression member"]):
            return "strut"
        elif any(word in task_lower for word in ["tie", "tension member"]):
            return "tie"
        
        # Bridge structure
        elif any(word in task_lower for word in ["truss", "triangular truss"]):
            return "truss"
        elif any(word in task_lower for word in ["span", "main span"]):
            return "span"
        elif any(word in task_lower for word in ["deck", "bridge deck", "roadway"]):
            return "deck"
        elif any(word in task_lower for word in ["bearing", "support bearing"]):
            return "bearing"
        elif any(word in task_lower for word in ["abutment", "end support"]):
            return "abutment"
        elif any(word in task_lower for word in ["pier", "intermediate support"]):
            return "pier"
        
        # Timber elements
        elif any(word in task_lower for word in ["beam", "timber beam", "rectangular beam"]):
            return "timber_beam"
        elif any(word in task_lower for word in ["timber post", "wooden post"]):
            return "timber_post"
        elif any(word in task_lower for word in ["plank", "deck plank", "timber plank"]):
            return "timber_plank"
        elif any(word in task_lower for word in ["joint", "timber joint", "connection"]):
            return "timber_joint"
        elif any(word in task_lower for word in ["gusset", "gusset plate", "connection plate"]):
            return "gusset_plate"
        
        # Generic structural elements (fallback)
        elif any(word in task_lower for word in ["beam", "girder"]):
            return "beam"
        elif any(word in task_lower for word in ["column", "pillar", "support"]):
            return "column"
        elif any(word in task_lower for word in ["foundation", "footing"]):
            return "foundation"
        elif any(word in task_lower for word in ["cable", "wire"]):
            return "cable"
        elif any(word in task_lower for word in ["railing", "barrier", "guard"]):
            return "railing"
        elif any(word in task_lower for word in ["point"]):
            return "point"
        elif any(word in task_lower for word in ["line", "curve"]):
            return "curve"
        elif any(word in task_lower for word in ["spiral", "stair"]):
            return "spiral_staircase"
        
        # Grasshopper component types
        elif any(word in task_lower for word in ["python script", "script component", "python component"]):
            return "python3_script"
        elif any(word in task_lower for word in ["slider", "number slider"]):
            return "slider"
        elif any(word in task_lower for word in ["panel", "text panel"]):
            return "panel"
        elif any(word in task_lower for word in ["parameter", "input parameter"]):
            return "input_parameter"
        elif any(word in task_lower for word in ["grasshopper component", "gh component"]):
            return "grasshopper_component"
        else:
            return "geometry"  # Generic fallback
    
    def _generate_component_name(self, task: str, component_type: str) -> str:
        """
        Generate a human-readable component name.
        
        Args:
            task: Task description
            component_type: Inferred component type
            
        Returns:
            Human-readable component name
        """
        # Extract key descriptors from task
        import re
        
        # Remove common words and extract meaningful parts
        task_words = re.findall(r'\b\w+\b', task.lower())
        meaningful_words = [w for w in task_words if w not in {
            'create', 'make', 'add', 'build', 'generate', 'the', 'a', 'an', 
            'with', 'using', 'script', 'component', 'python'
        }]
        
        # Take first few meaningful words + component type
        if meaningful_words:
            descriptors = '_'.join(meaningful_words[:2])
            return f"{descriptors}_{component_type}"
        else:
            return component_type


# Convenience function for creating the JSON geometry agent
def create_geometry_agent_json(custom_tools: Optional[List] = None, model_name: str = "geometry", 
                              component_registry: Optional[ComponentRegistry] = None) -> GeometryAgentJSON:
    """Create a JSON-based geometry agent.
    
    Args:
        custom_tools: Additional custom tools to include
        model_name: Model configuration name
        component_registry: Registry for tracking components
        
    Returns:
        GeometryAgentJSON instance
    """
    return GeometryAgentJSON(custom_tools=custom_tools, model_name=model_name, 
                            component_registry=component_registry)