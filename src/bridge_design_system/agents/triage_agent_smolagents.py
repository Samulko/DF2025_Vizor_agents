"""
Simplified Triage Agent using native smolagents ManagedAgent pattern.

This module provides a factory function that creates a triage system
following smolagents best practices, using native agent delegation
instead of custom coordination code.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from smolagents import CodeAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider

# OLD FILE-BASED MEMORY TOOLS - COMMENTED OUT, USING NATIVE MEMORY INSTEAD
# from ..tools.memory_tools import clear_memory, recall, remember, search_memory

logger = get_logger(__name__)


def create_triage_system(
    component_registry: Optional[Any] = None, 
    model_name: str = "triage", 
    monitoring_callback: Optional[Any] = None,
    **kwargs
) -> CodeAgent:
    """
    Create triage system using smolagents ManagedAgent pattern.

    This replaces the 600+ line TriageAgent class with native smolagents
    delegation. The manager agent automatically handles task routing and
    context management between specialized agents.

    Args:
        component_registry: Registry for tracking components across agents
        model_name: Model configuration name from settings
        monitoring_callback: Optional callback for real-time monitoring
        **kwargs: Additional arguments passed to CodeAgent

    Returns:
        CodeAgent configured as manager with specialized agents
    """
    # Get model
    model = ModelProvider.get_model(model_name)

    # REFACTORED: Removed shared component tracking - geometry agent is now autonomous
    
    # Create autonomous geometry agent with full MCP access (proper smolagents pattern)
    geometry_monitor = None
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback  
        if callable(monitoring_callback) and str(type(monitoring_callback)).find('function') != -1:
            # Remote monitoring - create callback for this agent
            geometry_monitor = monitoring_callback("geometry_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback
            geometry_monitor = create_monitor_callback("geometry_agent", monitoring_callback)
    
    geometry_agent = _create_mcp_enabled_geometry_agent(
        custom_tools=_create_registry_tools(component_registry) if component_registry else None,
        component_registry=component_registry,
        monitoring_callback=geometry_monitor
    )

    # Create autonomous SysLogic agent for structural validation
    from .syslogic_agent_smolagents import create_syslogic_agent
    syslogic_monitor = None
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if callable(monitoring_callback) and str(type(monitoring_callback)).find('function') != -1:
            # Remote monitoring - create callback for this agent
            syslogic_monitor = monitoring_callback("syslogic_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback
            syslogic_monitor = create_monitor_callback("syslogic_agent", monitoring_callback)
    
    syslogic_agent = create_syslogic_agent(
        component_registry=component_registry,
        monitoring_callback=syslogic_monitor
    )

    # Note: Material agent would be created here when available

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

    # Prepare step_callbacks for triage agent monitoring
    step_callbacks = kwargs.pop("step_callbacks", [])
    if monitoring_callback:
        # Check if it's a remote callback factory or local callback
        if callable(monitoring_callback) and str(type(monitoring_callback)).find('function') != -1:
            # Remote monitoring - create callback for this agent
            triage_monitor = monitoring_callback("triage_agent")
        else:
            # Local monitoring - use existing pattern
            from ..monitoring.agent_monitor import create_monitor_callback
            triage_monitor = create_monitor_callback("triage_agent", monitoring_callback)
        step_callbacks.append(triage_monitor)

    manager = CodeAgent(
        tools=manager_tools,  # Coordination tools only
        model=model,
        name="triage_agent",
        description="Coordinates bridge design tasks by delegating to specialized agents",
        max_steps=max_steps,
        step_callbacks=step_callbacks,
        additional_authorized_imports=["typing", "json", "datetime"],
        managed_agents=[geometry_agent, syslogic_agent],  # Pass agents directly in kwargs
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
    custom_tools: Optional[List] = None, 
    component_registry: Optional[Any] = None,
    monitoring_callback: Optional[Any] = None
) -> Any:
    """
    Create geometry agent using existing standalone implementation.
    
    Following smolagents best practices, this imports and configures
    the standalone geometry agent for use in managed_agents.
    
    Args:
        custom_tools: Additional tools to include
        component_registry: Registry for tracking components
        monitoring_callback: Optional callback for real-time monitoring

    Returns:
        SmolagentsGeometryAgent instance configured for managed_agents
    """
    logger.info("Creating geometry agent using standalone implementation")
    
    from .geometry_agent_smolagents import create_geometry_agent
    
    return create_geometry_agent(
        custom_tools=custom_tools,
        component_registry=component_registry,
        monitoring_callback=monitoring_callback
    )


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

    def __init__(self, component_registry: Optional[Any] = None, monitoring_callback: Optional[Any] = None):
        """Initialize wrapper with smolagents manager and direct agent references."""
        # Create the triage manager (without managed_agents to avoid string conversion)
        model = ModelProvider.get_model("triage")
        
        # Create coordination tools
        material_tool = create_material_placeholder()
        structural_tool = create_structural_placeholder()
        basic_coordination_tools = _create_coordination_tools()
        manager_tools = [material_tool, structural_tool] + basic_coordination_tools
        
        # Create triage manager without managed_agents
        self.manager = CodeAgent(
            tools=manager_tools,
            model=model,
            name="triage_agent",
            description="Coordinates bridge design tasks by delegating to specialized agents",
            max_steps=6,
            additional_authorized_imports=["typing", "json", "datetime"],
        )
        
        # Create agents directly and store as instance variables to bypass smolagents issue
        geometry_monitor = None
        syslogic_monitor = None
        
        if monitoring_callback:
            if callable(monitoring_callback) and str(type(monitoring_callback)).find('function') != -1:
                geometry_monitor = monitoring_callback("geometry_agent")
                syslogic_monitor = monitoring_callback("syslogic_agent")
            else:
                from ..monitoring.agent_monitor import create_monitor_callback
                geometry_monitor = create_monitor_callback("geometry_agent", monitoring_callback)
                syslogic_monitor = create_monitor_callback("syslogic_agent", monitoring_callback)
        
        self.geometry_agent = _create_mcp_enabled_geometry_agent(
            custom_tools=_create_registry_tools(component_registry) if component_registry else None,
            component_registry=component_registry,
            monitoring_callback=geometry_monitor
        )
        
        from .syslogic_agent_smolagents import create_syslogic_agent
        self.syslogic_agent = create_syslogic_agent(
            component_registry=component_registry,
            monitoring_callback=syslogic_monitor
        )
        
        self.component_registry = component_registry
        self.logger = logger
        
        logger.info("✅ Created TriageSystemWrapper with direct agent pattern (bypassing smolagents managed_agents issue)")

    def handle_design_request(self, request: str, gaze_id: Optional[str] = None) -> ResponseCompatibilityWrapper:
        """
        Handle design request using three-step orchestrator-parser workflow:
        1. Delegate to GeometryAgent for simple text description
        2. Parse text to structured JSON using TriageAgent's LLM  
        3. Delegate clean structured data to SysLogicAgent

        Args:
            request: Human designer's request
            gaze_id: Optional gaze context from VizorListener (e.g., "dynamic_003")

        Returns:
            ResponseCompatibilityWrapper for backward compatibility
        """
        try:
            # Step 1: Delegate to GeometryAgent for simple text description
            geometry_agent = self._get_geometry_agent()
            if not geometry_agent:
                raise ValueError("Geometry agent not available")
                
            logger.info("🔧 Step 1: Delegating to GeometryAgent for execution")
            geometry_text_result = geometry_agent.run(
                task=request,
                additional_args={"gazed_object_id": gaze_id} if gaze_id and self._validate_gaze_id(gaze_id) else None
            )

            # Step 2: TriageAgent parses text into structured JSON using LLM
            logger.info("📊 Step 2: Parsing geometry output to structured data using LLM")
            element_data = self._parse_with_llm(geometry_text_result)

            # Step 3: Pass clean structured data to SysLogicAgent
            syslogic_agent = self._get_syslogic_agent()
            if syslogic_agent and element_data and element_data.get("elements"):
                logger.info("🔍 Step 3: Delegating to SysLogicAgent for validation")
                syslogic_result = syslogic_agent.run(
                    task="update material stock and validate structural integrity",
                    additional_args={"elements": element_data}
                )
            else:
                syslogic_result = "SysLogic processing skipped - no structural elements to validate"
                logger.info("⚠️ Step 3: SysLogic skipped - no elements to process")

            # Step 4: Combine and return comprehensive response
            final_response = {
                "geometry_outcome": str(geometry_text_result),
                "parsed_elements": element_data,
                "syslogic_analysis": str(syslogic_result),
                "workflow_status": "completed_successfully"
            }
            
            logger.info("✅ Three-step orchestrator workflow completed successfully")
            return ResponseCompatibilityWrapper(final_response, success=True)

        except Exception as e:
            logger.error(f"Orchestrator workflow failed: {e}")
            error_result = {
                "error": str(e), 
                "workflow_status": "failed",
                "error_type": type(e).__name__
            }
            return ResponseCompatibilityWrapper(
                error_result, success=False, error_type=type(e).__name__
            )

    def _validate_gaze_id(self, gaze_id: str) -> bool:
        """
        Validate gaze ID follows expected dynamic_XXX format.
        
        Args:
            gaze_id: Gaze ID string from VizorListener
            
        Returns:
            True if valid format, False otherwise
        """
        import re
        return bool(re.match(r'^dynamic_\d{3}$', gaze_id))

    def _parse_with_llm(self, geometry_text: str) -> Dict[str, Any]:
        """
        Use TriageAgent's LLM to parse geometry description into structured JSON.
        
        This is the critical Step 2 of the orchestrator-parser workflow where
        the TriageAgent transforms descriptive text from GeometryAgent into
        clean structured data for SysLogicAgent.
        
        Args:
            geometry_text: Descriptive text from GeometryAgent
            
        Returns:
            Parsed ElementData v1.0 JSON structure or empty dict if parsing fails
        """
        try:
            parsing_task = (
                "Parse the following geometry description into valid JSON following ElementData contract v1.0. "
                "Extract all structural elements with these properties:\n"
                "- id: element identifier (e.g., '001', '021')\n"
                "- type: element type (e.g., 'green_a', 'blue_b')\n"
                "- length_mm: length in millimeters (convert from meters if needed)\n"
                "- center_point: [x, y, z] coordinates\n"
                "- direction: [x, y, z] direction vector\n\n"
                "Format as JSON with this structure:\n"
                "{\n"
                '  "data_type": "element_collection",\n'
                '  "elements": [\n'
                '    {\n'
                '      "id": "001",\n'
                '      "type": "green_a",\n'
                '      "length_mm": 400,\n'
                '      "center_point": [-187.4, -100, 25],\n'
                '      "direction": [-34.5, -20, 0]\n'
                '    }\n'
                '  ]\n'
                '}\n\n'
                f"Geometry description to parse:\n\n{geometry_text}"
            )
            
            logger.info("🤖 Using TriageAgent LLM for text-to-JSON parsing")
            llm_result = self.manager.run(parsing_task)
            
            # Extract JSON from the LLM's response
            parsed_data = self._extract_json_from_response(str(llm_result))
            
            # Validate the structure
            if parsed_data and "elements" in parsed_data:
                logger.info(f"✅ Successfully parsed {len(parsed_data['elements'])} elements")
                return parsed_data
            else:
                logger.warning("⚠️ LLM parsing returned invalid structure")
                return {"data_type": "element_collection", "elements": []}
                
        except Exception as e:
            logger.error(f"❌ LLM parsing failed: {e}")
            return {"data_type": "element_collection", "elements": []}

    def _extract_json_from_response(self, llm_response: str) -> Dict[str, Any]:
        """
        Extract clean JSON from LLM response text with enhanced robustness.
        
        Args:
            llm_response: Raw LLM response that may contain JSON
            
        Returns:
            Parsed JSON dictionary or empty dict if parsing fails
        """
        import json
        import re
        
        try:
            # Convert to string if needed
            response_text = str(llm_response)
            
            # Method 1: Find JSON block in markdown code fence (multiple patterns)
            json_patterns = [
                r'```json\n(.*?)\n```',  # Standard markdown
                r'```JSON\n(.*?)\n```',  # Uppercase
                r'```\n(.*?)\n```',      # Generic code block
                r'```json(.*?)```'       # No newlines
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(1).strip()
                    try:
                        result = json.loads(json_str)
                        if self._validate_element_data(result):
                            return result
                        logger.debug(f"🔍 Pattern {pattern} found JSON but validation failed")
                    except json.JSONDecodeError:
                        logger.debug(f"🔍 Pattern {pattern} found content but not valid JSON")
                        continue
            
            # Method 2: Find JSON object directly (look for balanced braces)
            json_start = response_text.find('{')
            if json_start != -1:
                # Find matching closing brace
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(response_text[json_start:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = json_start + i + 1
                            break
                
                if json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    try:
                        result = json.loads(json_str)
                        if self._validate_element_data(result):
                            return result
                        logger.debug("🔍 Balanced braces found JSON but validation failed")
                    except json.JSONDecodeError:
                        logger.debug("🔍 Balanced braces found content but not valid JSON")
            
            # Method 3: Try to parse the entire response as JSON
            try:
                result = json.loads(response_text)
                if self._validate_element_data(result):
                    return result
                logger.debug("🔍 Full response is JSON but validation failed")
            except json.JSONDecodeError:
                logger.debug("🔍 Full response is not valid JSON")
            
            # If all methods fail, return empty structure
            logger.warning("⚠️ No valid JSON found in response")
            return {"data_type": "element_collection", "elements": []}
            
        except (AttributeError, IndexError) as e:
            logger.warning(f"⚠️ Failed to extract JSON from response: {e}")
            # Return empty structure that matches expected format
            return {"data_type": "element_collection", "elements": []}

    def _validate_element_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the parsed data follows ElementData v1.0 contract.
        
        Args:
            data: Parsed JSON data to validate
            
        Returns:
            True if data is valid ElementData structure, False otherwise
        """
        try:
            # Check top-level structure
            if not isinstance(data, dict):
                return False
            
            if "elements" not in data:
                return False
            
            elements = data["elements"]
            if not isinstance(elements, list):
                return False
            
            # Validate each element (allow empty list)
            for element in elements:
                if not isinstance(element, dict):
                    return False
                
                # Check required fields
                required_fields = ["id", "type"]
                for field in required_fields:
                    if field not in element:
                        logger.debug(f"🔍 Element missing required field: {field}")
                        return False
                
                # Optional: validate field types if present
                if "length_mm" in element and not isinstance(element["length_mm"], (int, float)):
                    logger.debug("🔍 Element length_mm is not numeric")
                    return False
                
                if "center_point" in element:
                    cp = element["center_point"]
                    if not isinstance(cp, list) or len(cp) != 3:
                        logger.debug("🔍 Element center_point is not [x,y,z] array")
                        return False
            
            logger.debug(f"✅ Validated ElementData with {len(elements)} elements")
            return True
            
        except Exception as e:
            logger.debug(f"🔍 Validation error: {e}")
            return False

    def _get_geometry_agent(self):
        """
        Get geometry agent from direct instance reference.
        
        Returns:
            Geometry agent instance or None if not found
        """
        try:
            if hasattr(self, 'geometry_agent') and self.geometry_agent:
                logger.debug("🔍 Found geometry agent via direct reference")
                return self.geometry_agent
            else:
                logger.warning("⚠️ No geometry agent available in direct reference")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting geometry agent: {e}")
            return None

    def _get_syslogic_agent(self):
        """
        Get syslogic agent from direct instance reference.
        
        Returns:
            SysLogic agent instance or None if not found
        """
        try:
            if hasattr(self, 'syslogic_agent') and self.syslogic_agent:
                logger.debug("🔍 Found syslogic agent via direct reference")
                return self.syslogic_agent
            else:
                logger.warning("⚠️ No syslogic agent available in direct reference")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting syslogic agent: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get status of the triage system."""
        return {
            "triage": {
                "initialized": True,
                "type": "smolagents_orchestrator",
                "direct_agents": 2,  # geometry_agent + syslogic_agent
                "max_steps": self.manager.max_steps,
            },
            "geometry_agent": {
                "initialized": hasattr(self, 'geometry_agent') and self.geometry_agent is not None,
                "type": type(self.geometry_agent).__name__ if hasattr(self, 'geometry_agent') else "Unknown",
                "mcp_integration": "enabled",
            },
            "syslogic_agent": {
                "initialized": hasattr(self, 'syslogic_agent') and self.syslogic_agent is not None,
                "type": type(self.syslogic_agent).__name__ if hasattr(self, 'syslogic_agent') else "Unknown",
                "validation_tools": "enabled",
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

            # Reset managed agents memory
            if hasattr(self.manager, "managed_agents") and self.manager.managed_agents:
                for i, agent in enumerate(self.manager.managed_agents):
                    agent_name = getattr(agent, "name", f"agent_{i}")
                    
                    if hasattr(agent, "memory") and hasattr(agent.memory, "steps"):
                        steps_cleared = len(agent.memory.steps)
                        agent.memory.steps.clear()
                        logger.info(f"✅ Cleared {steps_cleared} {agent_name} memory steps")
                    
                    # Special handling for geometry agent's internal component cache
                    if hasattr(agent, "internal_component_cache"):
                        cache_cleared = len(agent.internal_component_cache)
                        agent.internal_component_cache.clear()
                        logger.info(f"✅ Cleared {cache_cleared} {agent_name} component cache entries")

            logger.info("🔄 All agent memories have been reset - starting fresh session")

        except Exception as e:
            logger.warning(f"⚠️ Error during agent reset: {e}")
            logger.info("🔄 Reset completed with warnings")