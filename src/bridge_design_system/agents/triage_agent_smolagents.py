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

    # REFACTORED: Removed shared component tracking - geometry agent is now autonomous
    
    # Create autonomous geometry agent with full MCP access (proper smolagents pattern)
    geometry_agent = _create_mcp_enabled_geometry_agent(
        custom_tools=_create_registry_tools(component_registry) if component_registry else None,
        component_registry=component_registry
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

    # REFACTORED: Manager tools simplified - no geometry memory tools needed
    manager_tools = [material_tool, structural_tool] + basic_coordination_tools + memory_tools

    # Create manager agent with managed_agents pattern (smolagents best practice)
    # Extract max_steps from kwargs to avoid duplicate parameter error
    max_steps = kwargs.pop(
        "max_steps", 6
    )  # Increased to allow proper task completion and error handling

    manager = CodeAgent(
        tools=manager_tools,  # Coordination tools only
        managed_agents=[geometry_agent],  # Autonomous geometry agent
        model=model,
        name="triage_agent",
        description="Coordinates bridge design tasks by delegating to specialized agents",
        max_steps=max_steps,
        additional_authorized_imports=["typing", "json", "datetime"],
        **kwargs,
    )
    
    # REFACTORED: Removed geometry memory tools - geometry agent is now autonomous
    # The geometry agent handles its own context resolution and memory management

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
    Create autonomous geometry agent with full MCP toolset for managed_agents pattern.

    Following smolagents best practices, this creates an autonomous ToolCallingAgent
    with name and description attributes that can be used in managed_agents.

    Args:
        custom_tools: Additional tools to include
        component_registry: Registry for tracking components

    Returns:
        Autonomous ToolCallingAgent configured with MCP tools for managed_agents
    """
    logger.info("Creating geometry agent with full MCP toolset (including edit_python3_script)")

    # Use the existing working pattern from geometry_agent_smolagents.py
    # but create a ToolCallingAgent directly instead of a wrapper class
    from mcp import StdioServerParameters
    from mcpadapt.core import MCPAdapt
    from mcpadapt.smolagents_adapter import SmolAgentsAdapter

    from ..config.model_config import ModelProvider
    from ..config.settings import settings

    # Get model configuration
    model = ModelProvider.get_model("geometry", temperature=0.1)

    # Memory tools for persistent context - REMOVED FOR TEST
    # memory_tools = [remember, recall, search_memory, clear_memory]
    memory_tools = []  # Test: Let triage agent handle all memory

    # MCP server configuration (use working pattern)
    stdio_params = StdioServerParameters(
        command=settings.mcp_stdio_command, args=settings.mcp_stdio_args.split(","), env=None
    )

    # Create the base ToolCallingAgent with a static configuration first
    # This will be wrapped to handle MCP connection dynamically per request

    # For managed_agents, smolagents needs the agent to be directly callable
    # We need to create a ToolCallingAgent that has the MCP tools available
    # Let's create a minimal agent instance for the managed_agents pattern

    class MCPGeometryAgent(ToolCallingAgent):
        """Autonomous ToolCallingAgent with persistent MCP connection and internal state management."""

        def __init__(self):
            self.stdio_params = stdio_params
            self.custom_tools = custom_tools or []
            self.memory_tools = memory_tools
            self.component_registry = component_registry
            
            # REFACTORED: Agent now owns its state completely
            self.internal_component_cache = []  # List to store [{id, type, description, timestamp}]
            logger.info("🎯 Initializing autonomous geometry agent with internal state management")

            # Establish persistent MCP connection during initialization
            logger.info("🔗 Establishing persistent MCP connection...")
            try:
                self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
                self.mcp_tools = self.mcp_connection.__enter__()
                logger.info(
                    f"✅ Persistent MCP connection established with {len(self.mcp_tools)} tools"
                )

                # Combine all tools for persistent agent
                all_tools = list(self.mcp_tools) + self.custom_tools + self.memory_tools

                # Initialize with persistent MCP tools - sufficient steps for error detection/fixing
                super().__init__(
                    tools=all_tools,
                    model=model,
                    max_steps=6,  # Allow: check -> modify -> detect errors -> fix -> verify -> finalize
                    name="geometry_agent",
                    description="Creates 3D geometry in Rhino Grasshopper via MCP connection",
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
                    description="Creates 3D geometry (MCP connection failed)",
                )
                self.mcp_connection = None
                self.mcp_tools = []

        def run(self, task: str) -> Any:
            """Execute geometry task with autonomous context resolution and state management."""
            logger.info(f"🎯 Autonomous geometry agent processing task: {task[:100]}...")

            try:
                # REFACTORED: Autonomous context resolution from task description
                resolved_task = self._resolve_context_from_task(task)
                logger.info(f"📋 Resolved task: {resolved_task[:150]}...")
                
                # Check for duplicate/similar recent tasks to prevent loops
                if hasattr(self, "memory") and hasattr(self.memory, "steps"):
                    recent_tasks = [
                        step.task for step in self.memory.steps[-3:] if hasattr(step, "task")
                    ]
                    if any(resolved_task.lower() in recent_task.lower() for recent_task in recent_tasks):
                        logger.warning(
                            f"⚠️ Similar task detected in recent memory, being cautious: {resolved_task[:50]}..."
                        )

                # Use the persistent agent that maintains context and memory
                result = super().run(resolved_task)

                # Track components in internal state after successful execution
                self._track_component_in_state(result, task)
                
                # Log completion for debugging
                logger.info(
                    f"✅ Geometry agent completed task in {len(self.memory.steps) if hasattr(self, 'memory') else 0} total steps"
                )

                # Register components if registry available
                if self.component_registry:
                    self._extract_and_register_components(task, result)

                logger.info("✅ Task completed successfully with autonomous context resolution")
                return result

            except Exception as e:
                logger.error(f"❌ Autonomous geometry agent execution failed: {e}")
                return f"Geometry agent execution failed: {e}"

        def _extract_and_register_components(self, task: str, result: Any) -> None:
            """Extract and register components and store in memory AND tracking cache."""
            try:
                # Extract component IDs from the result and store in memory
                result_str = str(result)
                import re
                from datetime import datetime

                # Look for component ID patterns in the result
                component_id_pattern = (
                    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
                )
                matches = re.findall(component_id_pattern, result_str)

                # Remove duplicates while preserving order
                unique_matches = list(dict.fromkeys(matches))

                if unique_matches:
                    logger.info(
                        f"🔧 Found {len(unique_matches)} unique component IDs (removed {len(matches) - len(unique_matches)} duplicates)"
                    )
                    
                    # Track each component in the shared cache for follow-up requests
                    for component_id in unique_matches:
                        # Determine component type from context
                        comp_type = "unknown"
                        desc_lower = (task + " " + result_str).lower()
                        if "bridge" in desc_lower and "point" in desc_lower:
                            comp_type = "bridge_points"
                        elif "curve" in desc_lower or "line" in desc_lower:
                            comp_type = "bridge_curve"
                        elif "arch" in desc_lower:
                            comp_type = "bridge_arch"
                        elif "deck" in desc_lower:
                            comp_type = "bridge_deck"
                        
                        component_info = {
                            "id": component_id,
                            "type": comp_type,
                            "description": task[:100],
                            "timestamp": datetime.now().isoformat(),
                            "full_result": result_str[:200] + "..." if len(result_str) > 200 else result_str
                        }
                        
                        # REMOVED: No longer using shared recent_components
                        # Track internally instead via _track_component_in_state
                        
                        logger.info(
                            f"📝 Component created and tracked: {component_id} ({comp_type})"
                        )

                if self.component_registry:
                    # NOTE: Component registry is orthogonal to autonomous operation
                    # It's used for cross-agent communication and external tracking,
                    # while internal_component_cache handles autonomous context resolution
                    logger.info(
                        f"📝 Component registration handled by triage agent: {task[:50]}..."
                    )

            except Exception as e:
                logger.warning(f"⚠️ Failed to register/track components: {e}")

        def __del__(self):
            """Cleanup persistent MCP connection on agent destruction."""
            try:
                if hasattr(self, "mcp_connection") and self.mcp_connection:
                    self.mcp_connection.__exit__(None, None, None)
                    logger.info("🔌 Persistent MCP connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing MCP connection: {e}")
        
        def _resolve_context_from_task(self, task: str) -> str:
            """
            REFACTORED: Autonomously resolve ambiguous references in the task.
            
            This method allows the geometry agent to understand conversational requests
            like "modify the curve" or "connect these points" by looking at its own
            memory and internal component cache.
            """
            task_lower = task.lower()
            
            # Enhanced ambiguous references with fuzzy matching capabilities
            ambiguous_terms = [
                # Curve-related references
                ("the curve", "curve"), ("that curve", "curve"), ("this curve", "curve"),
                ("the line", "curve"), ("that line", "curve"), ("the connection", "curve"),
                ("the arch", "arch"), ("that arch", "arch"), ("the span", "curve"),
                
                # Point-related references  
                ("the points", "points"), ("these points", "points"), ("those points", "points"),
                ("the anchors", "points"), ("the foundations", "points"), ("the ends", "points"),
                
                # Component-related references
                ("the component", "component"), ("that component", "component"),
                ("the element", "component"), ("that element", "component"),
                
                # Script-related references
                ("the script", "script"), ("that script", "script"), ("original script", "script"),
                ("the code", "script"), ("the python", "script"),
                
                # Bridge-specific references
                ("the bridge", "bridge"), ("the deck", "deck"), ("the support", "support"),
                ("the structure", "bridge"), ("the platform", "deck"),
                
                # Generic pronouns (need extra context resolution)
                ("it", None), ("them", None), ("that", None), ("this", None)
            ]
            
            needs_resolution = any(term in task_lower for term, _ in ambiguous_terms)
            
            if not needs_resolution:
                # Task is already specific enough
                return task
            
            # Look for context in internal cache first (most recent components)
            context_parts = []
            
            # Search internal component cache for relevant components with fuzzy matching
            for term, component_type in ambiguous_terms:
                if term in task_lower:
                    if component_type and self.internal_component_cache:
                        # Enhanced fuzzy matching for component types
                        matching_components = []
                        
                        for component in reversed(self.internal_component_cache):
                            comp_type = component.get("type", "").lower()
                            comp_desc = component.get("description", "").lower()
                            
                            # Direct type match (highest priority)
                            if component_type in comp_type:
                                matching_components.append((component, 3))
                            
                            # Fuzzy type matching (medium priority)
                            elif self._fuzzy_type_match(component_type, comp_type):
                                matching_components.append((component, 2))
                            
                            # Description-based matching (lower priority)
                            elif component_type in comp_desc:
                                matching_components.append((component, 1))
                        
                        # Sort by priority score and get the best match
                        if matching_components:
                            matching_components.sort(key=lambda x: x[1], reverse=True)
                            latest = matching_components[0][0]
                            context_parts.append(
                                f"(referring to component {latest['id']} - {latest['description']})"
                            )
                            # Replace ambiguous term with specific reference
                            task = task.replace(term, f"component {latest['id']}")
                            logger.debug(f"🔍 Fuzzy matched '{term}' to {latest['type']} component")
            
            # If no context found in cache, search memory steps
            if not context_parts and hasattr(self, "memory") and hasattr(self.memory, "steps"):
                # Search recent memory for component IDs or relevant context
                import re
                component_id_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
                
                for step in reversed(self.memory.steps[-5:]):  # Check last 5 steps
                    step_str = str(step)
                    component_ids = re.findall(component_id_pattern, step_str)
                    if component_ids:
                        # Found component reference in recent memory
                        context_parts.append(f"(likely referring to recent component {component_ids[0]})")
                        break
            
            # Build resolved task with context
            if context_parts:
                resolved_task = f"{task} {' '.join(context_parts)}"
                logger.info(f"🔍 Resolved ambiguous references: {context_parts}")
                return resolved_task
            
            # If still ambiguous, add a note for the agent to check recent work
            if needs_resolution:
                return f"{task} (Note: Check recent memory/components for context if needed)"
            
            return task
        
        def _track_component_in_state(self, result: Any, original_task: str) -> None:
            """
            REFACTORED: Track components in internal state for autonomous operation.
            
            This method parses MCP tool results and maintains the internal component
            cache, allowing the agent to track its own work without external dependencies.
            """
            try:
                import re
                from datetime import datetime
                
                result_str = str(result)
                component_id_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
                matches = re.findall(component_id_pattern, result_str)
                
                # Remove duplicates while preserving order
                unique_matches = list(dict.fromkeys(matches))
                
                if unique_matches:
                    logger.info(f"🔧 Found {len(unique_matches)} component IDs to track internally")
                    
                    for component_id in unique_matches:
                        # Determine component type from context
                        comp_type = self._determine_component_type(result_str, original_task)
                        
                        component_info = {
                            "id": component_id,
                            "type": comp_type,
                            "description": original_task[:100],
                            "timestamp": datetime.now().isoformat(),
                            "full_result": result_str[:200] + "..." if len(result_str) > 200 else result_str
                        }
                        
                        # Add to internal cache (keep last 10)
                        self.internal_component_cache.append(component_info)
                        if len(self.internal_component_cache) > 10:
                            self.internal_component_cache.pop(0)
                        
                        logger.info(
                            f"📝 Internally tracked component: {component_id} ({comp_type})"
                        )
                        logger.debug(f"   Cache size: {len(self.internal_component_cache)} components")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to track component in internal state: {e}")
        
        def _fuzzy_type_match(self, search_type: str, component_type: str) -> bool:
            """
            Helper for fuzzy matching between component types.
            
            Returns True if search_type and component_type are semantically similar.
            """
            # Define semantic relationships between component types
            type_synonyms = {
                "curve": ["line", "path", "connection", "span", "arch"],
                "line": ["curve", "connection", "path"],
                "arch": ["curve", "arc", "bow"], 
                "points": ["anchors", "foundations", "ends", "supports"],
                "script": ["code", "python", "component"],
                "bridge": ["structure", "span"],
                "deck": ["platform", "surface", "roadway"],
                "support": ["column", "pier", "pillar", "post"]
            }
            
            # Check if either type is a synonym of the other
            search_synonyms = type_synonyms.get(search_type, [])
            comp_synonyms = type_synonyms.get(component_type, [])
            
            return (component_type in search_synonyms or 
                    search_type in comp_synonyms or
                    search_type in component_type or
                    component_type in search_type)
        
        def _determine_component_type(self, result_str: str, task: str) -> str:
            """
            Enhanced helper to determine component type from context with fuzzy matching.
            
            Uses multiple matching strategies for robust component type identification.
            """
            context = (task + " " + result_str).lower()
            
            # Define component type patterns with fuzzy matching
            type_patterns = {
                "bridge_points": [
                    ["bridge", "point"], ["bridge", "anchor"], ["bridge", "support", "point"],
                    ["start", "point"], ["end", "point"], ["foundation", "point"]
                ],
                "bridge_curve": [
                    ["curve"], ["line"], ["path"], ["connection", "line"], 
                    ["bridge", "span"], ["connecting", "curve"], ["arch", "curve"]
                ],
                "bridge_arch": [
                    ["arch"], ["curved", "bridge"], ["arched"], ["bow"], 
                    ["arc"], ["semicircle"], ["vault"]
                ],
                "bridge_deck": [
                    ["deck"], ["platform"], ["surface"], ["roadway"], 
                    ["bridge", "surface"], ["walkway"], ["driving", "surface"]
                ],
                "bridge_support": [
                    ["support"], ["column"], ["pier"], ["pillar"], 
                    ["vertical", "support"], ["bridge", "support"], ["post"]
                ],
                "bridge_cable": [
                    ["cable"], ["wire"], ["tension"], ["suspension"], 
                    ["cable", "stay"], ["hanging"], ["string"]
                ],
                "python_script": [
                    ["script"], ["python"], ["code"], ["component", "script"],
                    ["programming"], ["python3"]
                ]
            }
            
            # Score each component type based on pattern matches
            type_scores = {}
            
            for comp_type, pattern_groups in type_patterns.items():
                score = 0
                
                for pattern_group in pattern_groups:
                    # Check if all words in pattern group are present
                    if all(word in context for word in pattern_group):
                        # Give higher score for more specific patterns (more words)
                        score += len(pattern_group) * 2
                    
                    # Check for partial matches (at least half the words)
                    elif len(pattern_group) > 1:
                        matches = sum(1 for word in pattern_group if word in context)
                        if matches >= len(pattern_group) // 2:
                            score += matches
                
                type_scores[comp_type] = score
            
            # Find the best match
            if type_scores:
                best_type = max(type_scores.items(), key=lambda x: x[1])
                if best_type[1] > 0:  # Only return if we found actual matches
                    logger.debug(f"🔍 Component type fuzzy match: '{best_type[0]}' (score: {best_type[1]})")
                    return best_type[0]
            
            # Fallback to simple keyword matching for backwards compatibility
            if "bridge" in context and "point" in context:
                return "bridge_points"
            elif "curve" in context or "line" in context:
                return "bridge_curve" 
            elif "arch" in context:
                return "bridge_arch"
            elif "deck" in context:
                return "bridge_deck"
            elif "script" in context or "python" in context:
                return "python_script"
            else:
                logger.debug(f"🔍 Component type defaulted to 'geometry' for context: {context[:100]}...")
                return "geometry"

    return MCPGeometryAgent()


def _create_coordination_tools() -> List:
    """Create tools for coordination and state management."""""

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
            return (
                "To reset agent memories, please type 'reset' in the command line interface. "
                "This will clear all conversation history and component registry for a fresh start."
            )
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

    @tool
    def debug_component_tracking() -> str:
        """
        Debug tool to show autonomous geometry agent state.
        
        REFACTORED: Now shows the autonomous geometry agent's internal state
        instead of shared component tracking cache.
        
        Returns:
            Debug information about geometry agent state
        """
        try:
            debug_info = []
            debug_info.append("=== AUTONOMOUS GEOMETRY AGENT DEBUG ===")
            debug_info.append("Component tracking: Handled internally by geometry agent")
            
            # Note: We can't directly access the geometry agent's internal cache from here
            # because it's encapsulated. This is by design for the autonomous architecture.
            debug_info.append("\\nTo see component details, delegate a task to the geometry agent")
            debug_info.append("that asks it to report its internal component state.")
            
            debug_info.append("\\n=== END DEBUG ===")
            
            result = "\\n".join(debug_info)
            logger.info("🐛 Autonomous geometry agent debug info requested")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in debug tool: {e}")
            return f"Debug tool error: {e}"

    return [reset_agent_memories, check_design_state, update_design_phase, debug_component_tracking]


# REFACTORED: Removed _create_geometry_memory_tools function entirely
# The geometry agent is now autonomous and handles its own memory/context


def _create_registry_tools(component_registry: Any) -> List:
    """
    Create tools for component registry integration.
    
    NOTE: The component registry is orthogonal to the autonomous agent architecture.
    It serves as a cross-agent communication mechanism and external component tracking,
    while the geometry agent's internal_component_cache handles autonomous context resolution.
    
    This separation allows:
    - Autonomous operation: Agent resolves context internally  
    - Cross-agent communication: Registry enables material/structural agents to access geometry
    - External integration: Registry provides API for external tools/monitoring
    """

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
            if hasattr(self.manager, "memory") and hasattr(self.manager.memory, "steps"):
                steps_cleared = len(self.manager.memory.steps)
                self.manager.memory.steps.clear()
                logger.info(f"✅ Cleared {steps_cleared} triage agent memory steps")

            # Reset geometry agent memory
            if hasattr(self.manager, "managed_agents") and self.manager.managed_agents:
                geometry_agent = None
                if (
                    isinstance(self.manager.managed_agents, dict)
                    and "geometry_agent" in self.manager.managed_agents
                ):
                    geometry_agent = self.manager.managed_agents["geometry_agent"]
                elif (
                    isinstance(self.manager.managed_agents, list)
                    and len(self.manager.managed_agents) > 0
                ):
                    geometry_agent = self.manager.managed_agents[0]

                if (
                    geometry_agent
                    and hasattr(geometry_agent, "memory")
                    and hasattr(geometry_agent.memory, "steps")
                ):
                    geo_steps_cleared = len(geometry_agent.memory.steps)
                    geometry_agent.memory.steps.clear()
                    logger.info(f"✅ Cleared {geo_steps_cleared} geometry agent memory steps")

            logger.info("🔄 All agent memories have been reset - starting fresh session")

        except Exception as e:
            logger.warning(f"⚠️ Error during agent reset: {e}")
            logger.info("🔄 Reset completed with warnings")
