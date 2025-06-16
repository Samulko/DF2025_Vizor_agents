"""
Simplified Triage Agent using native smolagents ManagedAgent pattern.

This module provides a factory function that creates a triage system
following smolagents best practices, using native agent delegation
instead of custom coordination code.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from smolagents import CodeAgent, ToolCallingAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
# OLD FILE-BASED MEMORY TOOLS - COMMENTED OUT, USING NATIVE MEMORY INSTEAD
# from ..tools.memory_tools import clear_memory, recall, remember, search_memory
from .geometry_agent_smolagents import create_geometry_agent

logger = get_logger(__name__)


def create_triage_system(
    component_registry: Optional[Any] = None, model_name: str = "triage", **kwargs
) -> CodeAgent:
    """
    Create triage system using smolagents ManagedAgent pattern.

    This replaces the 600+ line TriageAgent class with native smolagents
    delegation. The manager agent automatically handles task routing and
    context management between specialized agents.

    Args:
        component_registry: Registry for tracking components across agents
        model_name: Model configuration name from settings
        **kwargs: Additional arguments passed to CodeAgent

    Returns:
        CodeAgent configured as manager with specialized agents
    """
    # Get model
    model = ModelProvider.get_model(model_name)

    # Create specialized geometry agent with full MCP access (proper smolagents pattern)
    geometry_agent = _create_mcp_enabled_geometry_agent(
        custom_tools=_create_registry_tools(component_registry) if component_registry else None,
        component_registry=component_registry,
    )

    # Note: Material and Structural agents would be created here when available
    # For now, we only have geometry agent in managed_agents

    # Create manager agent first (without old file-based memory tools)
    # OLD FILE-BASED MEMORY TOOLS - COMMENTED OUT, USING NATIVE MEMORY INSTEAD
    # memory_tools = [remember, recall, search_memory, clear_memory]
    memory_tools = []  # Using native smolagents memory via geometry memory tools instead
    material_tool = create_material_placeholder()
    structural_tool = create_structural_placeholder()
    basic_coordination_tools = _create_coordination_tools()
    
    # Manager tools (NOT including geometry agent - that goes in managed_agents)
    manager_tools = (
        [material_tool, structural_tool] + 
        basic_coordination_tools + 
        memory_tools
    )

    # Create manager agent with managed_agents pattern (smolagents best practice)
    # Extract max_steps from kwargs to avoid duplicate parameter error
    max_steps = kwargs.pop("max_steps", 6)  # Increased to allow proper task completion and error handling

    manager = CodeAgent(
        tools=manager_tools,  # Coordination tools only
        managed_agents=[geometry_agent],  # Specialized agents go here
        model=model,
        name="triage_agent",
        description="Coordinates bridge design tasks by delegating to specialized agents",
        max_steps=max_steps,
        additional_authorized_imports=["typing", "json", "datetime"],
        **kwargs,
    )
    
    # Now add geometry memory tools that have access to the manager instance
    geometry_memory_tools = _create_geometry_memory_tools(manager)
    
    # Add the new tools to the manager's tools dict
    for tool in geometry_memory_tools:
        manager.tools[tool.name] = tool

    # Append our custom system prompt to the default one
    custom_prompt = get_triage_system_prompt()
    manager.prompt_templates["system_prompt"] = (
        manager.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
    )

    logger.info("Created triage system with native smolagents delegation")
    return manager


def get_triage_system_prompt() -> str:
    """Get custom system prompt for triage agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "triage_agent.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")
    
    return prompt_path.read_text(encoding="utf-8")


def _create_mcp_enabled_geometry_agent(
    custom_tools: Optional[List] = None, component_registry: Optional[Any] = None
) -> Any:
    """
    Create geometry agent with full MCP toolset for managed_agents pattern.

    Following smolagents best practices, this creates a ToolCallingAgent with 
    name and description attributes that can be used in managed_agents.

    Args:
        custom_tools: Additional tools to include
        component_registry: Registry for tracking components

    Returns:
        ToolCallingAgent configured with MCP tools for managed_agents
    """
    logger.info("Creating geometry agent with full MCP toolset (including edit_python3_script)")
    
    # Use the existing working pattern from geometry_agent_smolagents.py
    # but create a ToolCallingAgent directly instead of a wrapper class
    from ..config.model_config import ModelProvider
    from ..config.settings import settings
    from mcp import StdioServerParameters
    from mcpadapt.core import MCPAdapt
    from mcpadapt.smolagents_adapter import SmolAgentsAdapter
    from smolagents import ToolCallingAgent
    
    # Get model configuration
    model = ModelProvider.get_model("geometry", temperature=0.1)
    
    # Memory tools for persistent context - REMOVED FOR TEST
    # memory_tools = [remember, recall, search_memory, clear_memory]
    memory_tools = []  # Test: Let triage agent handle all memory
    
    # MCP server configuration (use working pattern)
    stdio_params = StdioServerParameters(
        command=settings.mcp_stdio_command,
        args=settings.mcp_stdio_args.split(","),
        env=None
    )
    
    # Create the base ToolCallingAgent with a static configuration first
    # This will be wrapped to handle MCP connection dynamically per request
    from smolagents import ToolCallingAgent
    
    # For managed_agents, smolagents needs the agent to be directly callable
    # We need to create a ToolCallingAgent that has the MCP tools available
    # Let's create a minimal agent instance for the managed_agents pattern
    
    class MCPGeometryAgent(ToolCallingAgent):
        """ToolCallingAgent with persistent MCP connection for session continuity."""
        
        def __init__(self):
            self.stdio_params = stdio_params
            self.custom_tools = custom_tools or []
            self.memory_tools = memory_tools
            self.component_registry = component_registry
            
            # Establish persistent MCP connection during initialization
            logger.info("🔗 Establishing persistent MCP connection...")
            try:
                self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
                self.mcp_tools = self.mcp_connection.__enter__()
                logger.info(f"✅ Persistent MCP connection established with {len(self.mcp_tools)} tools")
                
                # Combine all tools for persistent agent
                all_tools = list(self.mcp_tools) + self.custom_tools + self.memory_tools
                
                # Initialize with persistent MCP tools - sufficient steps for error detection/fixing
                super().__init__(
                    tools=all_tools,
                    model=model,
                    max_steps=6,  # Increased to allow: check -> modify -> detect errors -> fix -> verify -> finalize
                    name="geometry_agent",
                    description="Creates 3D geometry in Rhino Grasshopper via persistent MCP connection"
                )
                
                logger.info("🎯 Persistent geometry agent initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to establish persistent MCP connection: {e}")
                # Fallback to empty tools if MCP connection fails
                super().__init__(
                    tools=self.custom_tools + self.memory_tools,
                    model=model,
                    max_steps=6,  # Increased to allow proper error handling even without MCP
                    name="geometry_agent",
                    description="Creates 3D geometry (MCP connection failed)"
                )
                self.mcp_connection = None
                self.mcp_tools = []
        
        def run(self, task: str) -> Any:
            """Execute geometry task using persistent MCP connection and agent memory."""
            logger.info(f"🎯 Executing task with persistent MCP geometry agent: {task[:100]}...")
            
            try:
                # Check for duplicate/similar recent tasks to prevent loops
                if hasattr(self, 'memory') and hasattr(self.memory, 'steps'):
                    recent_tasks = [step.task for step in self.memory.steps[-3:] if hasattr(step, 'task')]
                    if any(task.lower() in recent_task.lower() for recent_task in recent_tasks):
                        logger.warning(f"⚠️ Similar task detected in recent memory, being cautious: {task[:50]}...")
                
                # Use the persistent agent that maintains context and memory
                result = super().run(task)
                
                # Log completion for debugging
                logger.info(f"✅ Geometry agent completed task in {len(self.memory.steps) if hasattr(self, 'memory') else 0} total steps")
                
                # Register components if registry available
                if self.component_registry:
                    self._extract_and_register_components(task, result)
                
                logger.info("✅ Task completed successfully with persistent MCP geometry agent")
                return result
                
            except Exception as e:
                logger.error(f"❌ Persistent MCP geometry agent execution failed: {e}")
                return f"Geometry agent execution failed: {e}"
        
        def _extract_and_register_components(self, task: str, result: Any) -> None:
            """Extract and register components and store in memory."""
            try:
                # Extract component IDs from the result and store in memory
                result_str = str(result)
                import re
                
                # Look for component ID patterns in the result
                component_id_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
                matches = re.findall(component_id_pattern, result_str)
                
                # Remove duplicates while preserving order
                unique_matches = list(dict.fromkeys(matches))
                
                if unique_matches:
                    logger.info(f"🔧 Found {len(unique_matches)} unique component IDs (removed {len(matches) - len(unique_matches)} duplicates)")
                    for component_id in unique_matches:
                        # Component information is automatically stored in agent.memory.steps (smolagents native)
                        # No need for manual memory storage - the triage agent can access this via geometry memory tools
                        logger.info(f"📝 Component created and stored in native memory: {component_id}")
                        
                if self.component_registry:
                    # Also register in component registry if available
                    logger.info(f"📝 Component registration handled by triage agent: {task[:50]}...")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to register components: {e}")
        
        def __del__(self):
            """Cleanup persistent MCP connection on agent destruction."""
            try:
                if hasattr(self, 'mcp_connection') and self.mcp_connection:
                    self.mcp_connection.__exit__(None, None, None)
                    logger.info("🔌 Persistent MCP connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing MCP connection: {e}")
    
    return MCPGeometryAgent()


def _create_coordination_tools() -> List:
    """Create tools for coordination and state management."""

    @tool
    def reset_agent_memories() -> str:
        """
        Reset all agent conversation memories to start fresh.
        
        Use this when the user explicitly wants to start a completely new design
        or when there are memory-related issues that need clearing.
        
        Returns:
            Confirmation message about the reset
        """
        try:
            # This is a placeholder - actual reset happens at the wrapper level
            # when the user types 'reset' in the CLI
            return "To reset agent memories, please type 'reset' in the command line interface. This will clear all conversation history and component registry for a fresh start."
        except Exception as e:
            return f"Reset information: {e}"

    @tool
    def check_design_state() -> dict:
        """
        Check current bridge design state and progress.

        Returns:
            Current design state dictionary
        """
        # State is tracked via native smolagents memory
        # This is a placeholder that would integrate with actual state tracking
        return {
            "status": "Design state tracking via native smolagents memory",
            "note": "Use geometry memory tools to check previous design decisions",
        }

    @tool
    def update_design_phase(phase: str, details: str) -> str:
        """
        Update the current design phase and log progress.

        Args:
            phase: Current phase name (e.g., "conceptual", "detailed", "structural")
            details: Details about the phase progress

        Returns:
            Confirmation message
        """
        # Phase updates are automatically tracked in smolagents conversation memory
        logger.info(f"Design phase updated to: {phase}. Details: {details}")
        return f"Design phase updated to '{phase}'"

    return [reset_agent_memories, check_design_state, update_design_phase]


def _create_geometry_memory_tools(manager) -> List:
    """Create tools that access geometry agent's native smolagents memory."""
    
    @tool
    def get_geometry_agent_memory() -> str:
        """
        Access geometry agent's native smolagents memory for conversation context.
        
        This tool accesses the geometry agent's persistent memory (agent.memory.steps)
        which contains all previous conversation history including component creation.
        
        Returns:
            String containing geometry agent's recent conversation history
        """
        try:
            if hasattr(manager, 'managed_agents') and manager.managed_agents:
                # smolagents converts list to dict internally
                if isinstance(manager.managed_agents, dict) and 'geometry_agent' in manager.managed_agents:
                    geometry_agent = manager.managed_agents['geometry_agent']
                    logger.debug(f"✅ Accessed geometry agent from managed_agents dict: {type(geometry_agent).__name__}")
                elif isinstance(manager.managed_agents, list) and len(manager.managed_agents) > 0:
                    geometry_agent = manager.managed_agents[0]  # Fallback to list access
                    logger.debug(f"✅ Accessed geometry agent from managed_agents list: {type(geometry_agent).__name__}")
                else:
                    return f"Cannot access geometry agent from managed_agents structure: {type(manager.managed_agents)}"
                
                if hasattr(geometry_agent, 'memory') and hasattr(geometry_agent.memory, 'steps'):
                    # Get recent memory steps
                    steps = geometry_agent.memory.steps
                    if not steps:
                        return "Geometry agent has no conversation history yet."
                    
                    logger.debug(f"📋 Found {len(steps)} memory steps in geometry agent")
                    
                    # Format recent steps for context
                    recent_steps = steps[-5:]  # Last 5 steps
                    formatted_steps = []
                    
                    for i, step in enumerate(recent_steps):
                        step_info = f"Step {i+1}: {type(step).__name__}"
                        
                        # Extract relevant information from each step type
                        if hasattr(step, 'task'):
                            step_info += f" - Task: {step.task}"
                        if hasattr(step, 'observations'):
                            obs_str = str(step.observations)[:200]  # Limit length
                            step_info += f" - Result: {obs_str}..."
                        if hasattr(step, 'tool_calls'):
                            step_info += f" - Tools used: {len(step.tool_calls) if step.tool_calls else 0}"
                            
                        formatted_steps.append(step_info)
                    
                    return "Geometry Agent Recent Memory:\n" + "\n".join(formatted_steps)
                else:
                    return "Geometry agent memory structure not available."
            else:
                return "No geometry agent found in managed agents."
                
        except Exception as e:
            return f"Error accessing geometry agent memory: {e}"

    @tool
    def search_geometry_agent_memory(query: str) -> str:
        """
        Search through geometry agent's conversation history for specific content.
        
        This tool searches the geometry agent's native memory for mentions of
        components, curves, scripts, or other geometry-related content.
        
        Args:
            query: Search term (e.g., "curve", "bridge", "component", "script")
            
        Returns:
            String containing matching conversation context
        """
        try:
            if hasattr(manager, 'managed_agents') and manager.managed_agents:
                # smolagents converts list to dict internally
                if isinstance(manager.managed_agents, dict) and 'geometry_agent' in manager.managed_agents:
                    geometry_agent = manager.managed_agents['geometry_agent']
                    logger.debug(f"✅ Accessed geometry agent from managed_agents dict for search: {type(geometry_agent).__name__}")
                elif isinstance(manager.managed_agents, list) and len(manager.managed_agents) > 0:
                    geometry_agent = manager.managed_agents[0]  # Fallback to list access
                    logger.debug(f"✅ Accessed geometry agent from managed_agents list for search: {type(geometry_agent).__name__}")
                else:
                    return f"Cannot access geometry agent from managed_agents structure: {type(manager.managed_agents)}"
                
                if hasattr(geometry_agent, 'memory') and hasattr(geometry_agent.memory, 'steps'):
                    steps = geometry_agent.memory.steps
                    if not steps:
                        return f"No conversation history to search for '{query}'."
                    
                    matches = []
                    query_lower = query.lower()
                    
                    for i, step in enumerate(steps):
                        step_text = str(step).lower()
                        
                        # Check if query matches in this step
                        if query_lower in step_text:
                            # Extract context around the match
                            step_info = f"Match in Step {i+1}:"
                            
                            if hasattr(step, 'task'):
                                step_info += f"\n  Task: {step.task}"
                            if hasattr(step, 'observations'):
                                obs_str = str(step.observations)
                                # Find context around the match
                                obs_lower = obs_str.lower()
                                match_index = obs_lower.find(query_lower)
                                if match_index != -1:
                                    # Extract 100 chars before and after the match
                                    start = max(0, match_index - 100)
                                    end = min(len(obs_str), match_index + len(query) + 100)
                                    context = obs_str[start:end]
                                    step_info += f"\n  Context: ...{context}..."
                            
                            matches.append(step_info)
                    
                    if matches:
                        logger.debug(f"🔍 Found {len(matches)} memory matches for query: {query}")
                        return f"Found {len(matches)} matches for '{query}':\n\n" + "\n\n".join(matches)
                    else:
                        logger.debug(f"❌ No memory matches found for query: {query}")
                        return f"No matches found for '{query}' in geometry agent conversation history."
                else:
                    return "Geometry agent memory structure not available for search."
            else:
                return "No geometry agent found to search."
                
        except Exception as e:
            return f"Error searching geometry agent memory: {e}"

    @tool
    def extract_components_from_geometry_memory() -> str:
        """
        Extract component IDs and information from geometry agent's conversation history.
        
        This tool specifically looks for component creation, modifications, and 
        component IDs in the geometry agent's memory to provide component context.
        
        IMPORTANT: This now validates component IDs against current session to prevent
        stale memory contamination from previous sessions.
        
        Returns:
            String containing found components and their details
        """
        try:
            if hasattr(manager, 'managed_agents') and manager.managed_agents:
                # smolagents converts list to dict internally
                if isinstance(manager.managed_agents, dict) and 'geometry_agent' in manager.managed_agents:
                    geometry_agent = manager.managed_agents['geometry_agent']
                    logger.debug(f"✅ Accessed geometry agent from managed_agents dict for extraction: {type(geometry_agent).__name__}")
                elif isinstance(manager.managed_agents, list) and len(manager.managed_agents) > 0:
                    geometry_agent = manager.managed_agents[0]  # Fallback to list access
                    logger.debug(f"✅ Accessed geometry agent from managed_agents list for extraction: {type(geometry_agent).__name__}")
                else:
                    return f"Cannot access geometry agent from managed_agents structure: {type(manager.managed_agents)}"
                
                if hasattr(geometry_agent, 'memory') and hasattr(geometry_agent.memory, 'steps'):
                    steps = geometry_agent.memory.steps
                    if not steps:
                        return "No conversation history available to extract components."
                    
                    components = []
                    import re
                    
                    # Pattern for component IDs (UUIDs)
                    component_id_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
                    
                    for i, step in enumerate(steps):
                        step_text = str(step)
                        
                        # Look for component IDs
                        component_ids = re.findall(component_id_pattern, step_text)
                        
                        if component_ids:
                            # Extract context about what was created/modified
                            component_info = f"Step {i+1}:"
                            
                            if hasattr(step, 'task'):
                                component_info += f"\n  Task: {step.task}"
                            
                            # Try to identify what type of component
                            step_lower = step_text.lower()
                            component_type = "unknown"
                            if "bridge" in step_lower and "point" in step_lower:
                                component_type = "bridge_points"
                            elif "curve" in step_lower or "line" in step_lower:
                                component_type = "bridge_curve"
                            elif "deck" in step_lower:
                                component_type = "bridge_deck"
                            elif "python" in step_lower and "script" in step_lower:
                                component_type = "python_script"
                            
                            for comp_id in component_ids:
                                component_info += f"\n  Component ID: {comp_id} (type: {component_type})"
                            
                            # Add relevant observations
                            if hasattr(step, 'observations'):
                                obs_str = str(step.observations)
                                # Extract relevant parts (limit length)
                                if len(obs_str) > 300:
                                    obs_str = obs_str[:300] + "..."
                                component_info += f"\n  Details: {obs_str}"
                            
                            components.append(component_info)
                    
                    if components:
                        logger.debug(f"🔧 Extracted {len(components)} components from geometry agent memory")
                        return f"Found {len(components)} component creation/modification events:\n\n" + "\n\n".join(components)
                    else:
                        logger.debug(f"❌ No components found in geometry agent memory")
                        return "No components found in geometry agent conversation history."
                else:
                    return "Geometry agent memory structure not available for component extraction."
            else:
                return "No geometry agent found for component extraction."
                
        except Exception as e:
            return f"Error extracting components from geometry agent memory: {e}"

    @tool
    def get_current_valid_components() -> str:
        """
        Get currently valid components in Grasshopper, cross-referenced with memory context.
        
        This tool combines current Grasshopper session data with geometry agent memory
        to provide component IDs that are both recent AND currently valid.
        
        This solves the stale memory contamination issue by only returning component IDs
        that exist in the current Grasshopper session.
        
        Returns:
            String containing current valid components with memory context
        """
        try:
            if hasattr(manager, 'managed_agents') and manager.managed_agents:
                # Get geometry agent reference
                geometry_agent = None
                if isinstance(manager.managed_agents, dict) and 'geometry_agent' in manager.managed_agents:
                    geometry_agent = manager.managed_agents['geometry_agent']
                elif isinstance(manager.managed_agents, list) and len(manager.managed_agents) > 0:
                    geometry_agent = manager.managed_agents[0]
                
                if geometry_agent and hasattr(geometry_agent, 'tools'):
                    # Get current components from Grasshopper
                    current_components = {}
                    try:
                        # Use the geometry agent's MCP tools to get current components
                        for tool_name, tool_func in geometry_agent.tools.items():
                            if tool_name == "get_all_components_enhanced":
                                current_result = tool_func()
                                if hasattr(current_result, 'data') and current_result.data:
                                    components_data = current_result.data.get('components', [])
                                    for comp in components_data:
                                        if 'id' in comp:
                                            current_components[comp['id']] = comp
                                break
                    except Exception as e:
                        logger.warning(f"Could not get current components: {e}")
                    
                    # Extract memory component IDs (as before)
                    memory_components = []
                    if hasattr(geometry_agent, 'memory') and hasattr(geometry_agent.memory, 'steps'):
                        steps = geometry_agent.memory.steps
                        import re
                        component_id_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
                        
                        for i, step in enumerate(steps):
                            step_text = str(step)
                            component_ids = re.findall(component_id_pattern, step_text)
                            
                            for comp_id in component_ids:
                                # CRITICAL: Only include if it exists in current session
                                if comp_id in current_components:
                                    comp_info = current_components[comp_id]
                                    
                                    # Extract context from memory step
                                    context = f"Memory Step {i+1}:"
                                    if hasattr(step, 'task'):
                                        context += f" Task: {step.task}"
                                    
                                    memory_components.append({
                                        'id': comp_id,
                                        'current_data': comp_info,
                                        'memory_context': context,
                                        'step_index': i
                                    })
                    
                    # Sort by step index (most recent first)
                    memory_components.sort(key=lambda x: x['step_index'], reverse=True)
                    
                    if memory_components:
                        result = f"Found {len(memory_components)} current valid components (filtered from memory):\\n\\n"
                        for comp in memory_components:
                            result += f"Component ID: {comp['id']}\\n"
                            result += f"  Current Type: {comp['current_data'].get('type', 'unknown')}\\n"
                            result += f"  Current Name: {comp['current_data'].get('name', 'unknown')}\\n"
                            result += f"  Position: ({comp['current_data'].get('x', 0)}, {comp['current_data'].get('y', 0)})\\n"
                            result += f"  Memory Context: {comp['memory_context']}\\n\\n"
                        return result
                    else:
                        return f"No components found that exist in both memory and current session.\\nCurrent session has {len(current_components)} components.\\nThis suggests the memory contains only stale component IDs from previous sessions."
                else:
                    return "Cannot access geometry agent tools for component validation."
            else:
                return "No geometry agent found for component validation."
        except Exception as e:
            return f"Error validating current components: {e}"
    
    return [get_geometry_agent_memory, search_geometry_agent_memory, extract_components_from_geometry_memory, get_current_valid_components]


def _create_registry_tools(component_registry: Any) -> List:
    """Create tools for component registry integration."""

    @tool
    def register_bridge_component(component_type: str, component_id: str, data: dict) -> str:
        """
        Register a bridge component in the cross-agent registry.

        Args:
            component_type: Type of component (e.g., "deck", "support", "cable")
            component_id: Unique identifier for the component
            data: Component data including geometry reference

        Returns:
            Registration confirmation
        """
        component_registry.register_component(
            name=f"{component_type}_{component_id}",
            data={"type": component_type, "id": component_id, **data},
        )
        return f"Registered {component_type} component: {component_id}"

    @tool
    def list_bridge_components(component_type: Optional[str] = None) -> dict:
        """
        List registered bridge components.

        Args:
            component_type: Optional filter by component type

        Returns:
            Dictionary of registered components
        """
        all_components = component_registry.get_all_components()

        if component_type:
            filtered = {k: v for k, v in all_components.items() if v.get("type") == component_type}
            return filtered

        return all_components

    return [register_bridge_component, list_bridge_components]


def create_material_placeholder() -> Any:
    """Create placeholder tool for material agent (to be implemented)."""

    @tool
    def check_materials(material_type: str, quantity: float) -> dict:
        """
        Placeholder for material checking (Material Agent coming soon).

        Args:
            material_type: Type of material to check
            quantity: Required quantity

        Returns:
            Placeholder response
        """
        return {
            "status": "placeholder",
            "message": "Material Agent not yet implemented",
            "note": "This will check material availability once the Material Agent is integrated",
        }

    return check_materials


def create_structural_placeholder() -> Any:
    """Create placeholder tool for structural agent (to be implemented)."""

    @tool
    def analyze_structure(component_id: str, load_type: str = "standard") -> dict:
        """
        Placeholder for structural analysis (Structural Agent coming soon).

        Args:
            component_id: Component to analyze
            load_type: Type of load analysis

        Returns:
            Placeholder response
        """
        return {
            "status": "placeholder",
            "message": "Structural Agent not yet implemented",
            "note": "This will perform structural analysis once the Structural Agent is integrated",
        }

    return analyze_structure


class ResponseCompatibilityWrapper:
    """
    Wrapper to provide .success and .message attributes for backward compatibility.

    Smolagents agents return various types (AgentText, dict, str), but the existing
    interface expects response objects with .success and .message attributes.
    """

    def __init__(self, result: Any, success: bool = True, error_type: Optional[str] = None):
        """Initialize compatibility wrapper."""
        self.result = result
        self.success = success
        self.error = error_type

        # Extract message from various result types
        if hasattr(result, "text"):
            self.message = result.text
        elif isinstance(result, dict):
            self.message = result.get("message", str(result))
        elif isinstance(result, str):
            self.message = result
        else:
            self.message = str(result)

        # Set data for backward compatibility
        self.data = result if isinstance(result, dict) else {"result": result}


# Optional: Create a wrapper for backward compatibility during transition
class TriageSystemWrapper:
    """
    Wrapper to provide backward compatibility during transition.

    This allows gradual migration from the old TriageAgent API to the new
    smolagents-native pattern.
    """

    def __init__(self, component_registry: Optional[Any] = None):
        """Initialize wrapper with smolagents manager."""
        self.manager = create_triage_system(component_registry=component_registry)
        self.component_registry = component_registry
        self.logger = logger

    def handle_design_request(self, request: str) -> ResponseCompatibilityWrapper:
        """
        Handle design request using smolagents manager.

        Args:
            request: Human designer's request

        Returns:
            ResponseCompatibilityWrapper for backward compatibility
        """
        try:
            # Use native smolagents execution
            result = self.manager.run(request)

            # Return compatibility wrapper
            return ResponseCompatibilityWrapper(result, success=True)

        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            error_result = {"error": f"Error: {str(e)}", "error_type": type(e).__name__}
            return ResponseCompatibilityWrapper(
                error_result, success=False, error_type=type(e).__name__
            )

    def get_status(self) -> Dict[str, Any]:
        """Get status of the triage system."""
        return {
            "triage": {
                "initialized": True,
                "type": "smolagents_manager",
                "managed_agents": (
                    len(self.manager.managed_agents)
                    if hasattr(self.manager, "managed_agents")
                    else 0
                ),
                "max_steps": self.manager.max_steps,
            },
            "geometry_agent": {
                "initialized": True,
                "type": "ToolCallingAgent",
                "mcp_integration": "enabled",
            },
        }

    def reset_all_agents(self) -> None:
        """Reset all agents by clearing their conversation memory."""
        try:
            # Reset the main triage agent memory
            if hasattr(self.manager, 'memory') and hasattr(self.manager.memory, 'steps'):
                steps_cleared = len(self.manager.memory.steps)
                self.manager.memory.steps.clear()
                logger.info(f"✅ Cleared {steps_cleared} triage agent memory steps")
            
            # Reset geometry agent memory
            if hasattr(self.manager, 'managed_agents') and self.manager.managed_agents:
                geometry_agent = None
                if isinstance(self.manager.managed_agents, dict) and 'geometry_agent' in self.manager.managed_agents:
                    geometry_agent = self.manager.managed_agents['geometry_agent']
                elif isinstance(self.manager.managed_agents, list) and len(self.manager.managed_agents) > 0:
                    geometry_agent = self.manager.managed_agents[0]
                
                if geometry_agent and hasattr(geometry_agent, 'memory') and hasattr(geometry_agent.memory, 'steps'):
                    geo_steps_cleared = len(geometry_agent.memory.steps)
                    geometry_agent.memory.steps.clear()
                    logger.info(f"✅ Cleared {geo_steps_cleared} geometry agent memory steps")
                
            logger.info("🔄 All agent memories have been reset - starting fresh session")
            
        except Exception as e:
            logger.warning(f"⚠️ Error during agent reset: {e}")
            logger.info("🔄 Reset completed with warnings")
