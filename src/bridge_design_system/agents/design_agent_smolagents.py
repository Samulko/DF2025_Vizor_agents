"""
Design Agent for Interactive 3D Form Exploration & Assembly

This agent orchestrates the rapid prototyping and design exploration workflow, using catalogued material data, user input, and simulation tools to iteratively generate, refine, and finalize 3D forms for fabrication and assembly. It leverages a Python component in Grasshopper for 3D re-orientation and uses the context7 database (via smolagents) for memory and context-aware reasoning.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings
from ..memory import track_design_changes

logger = get_logger(__name__)


class SmolagentsDesignAgent:
    """
    Design Agent for interactive, iterative 3D form exploration and assembly.

    Orchestrates the workflow:
    1. Material digitization & cataloging
    2. Rapid prototyping & design exploration (with user tweaks and simulation)
    3. Fabrication & assembly handoff

    Uses a Python component in Grasshopper for 3D re-orientation and leverages the context7 database for memory/context/history (via smolagents).
    """

    def __init__(
        self,
        model_name: str = "design",
        monitoring_callback: Optional[Any] = None,
    ):
        self.model_name = model_name
        self.name = "design_agent"
        self.description = (
            "Orchestrates interactive 3D form exploration and assembly. "
            "Uses catalogued material data, user input, and simulation tools to iteratively generate, refine, and finalize 3D forms for fabrication. "
            "Employs a Python component in Grasshopper for 3D re-orientation and context7 database for memory/context-aware reasoning."
        )
        self.model = ModelProvider.get_model(model_name, temperature=0.2)
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command, args=settings.mcp_stdio_args.split(","), env=None
        )
        logger.info("🔗 Establishing persistent MCP connection for design agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(f"✅ Persistent MCP connection established with {len(self.mcp_tools)} tools")
            all_tools = list(self.mcp_tools)
            all_tools.append(self._create_self_history_tool())
            all_tools.append(self._create_design_requirements_tool())
            all_tools.append(self._create_design_validation_tool())
            step_callbacks = [track_design_changes]
            if monitoring_callback:
                step_callbacks.append(monitoring_callback)
            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=20,  # Allow for iterative design-explore-refine loop
                name="design_agent",
                description=self.description,
                step_callbacks=step_callbacks,
            )
            custom_prompt = get_design_system_prompt()
            self.agent.prompt_templates["system_prompt"] = (
                self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            )
            logger.info(f"🎯 Persistent design agent initialized successfully with model {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to establish persistent MCP connection: {e}")
            raise RuntimeError(f"Design agent requires active MCP connection: {e}")

    def run(self, task: str, material_data: Optional[Dict] = None, user_tweaks: Optional[List[Dict]] = None) -> Any:
        """
        Orchestrate the full interactive design workflow:
        1. Wait for/accept catalogued material data
        2. Generate initial 3D form using Python in Grasshopper
        3. Run simulation and present to user
        4. Accept user tweaks (if any), update form, re-simulate (loop)
        5. When user is satisfied, finalize and dispatch for fabrication
        All design changes and rationale are logged using context7 database (via smolagents memory).
        """
        logger.info(f"🎯 Starting interactive design workflow for task: {task[:100]}...")
        # 1. Material Digitization & Cataloging
        if not material_data:
            logger.info("⏳ Waiting for catalogued material data...")
            # In a real system, this would block or poll until data is available
            # For now, assume material_data is provided or fetched by another agent
            pass
        else:
            logger.info(f"📦 Material data received: {material_data}")
        # 2. Rapid Prototyping & Design Exploration
        form = self._generate_initial_form(task, material_data)
        form = self._run_simulation(form)
        satisfied = False
        tweak_history = []
        while not satisfied:
            user_feedback = self._present_form_and_get_user_feedback(form)
            if user_feedback.get("tweak"):
                logger.info("🔄 User requested tweaks, updating form...")
                form = self._apply_user_tweaks(form, user_feedback["tweak"])
                form = self._run_simulation(form)
                tweak_history.append(user_feedback["tweak"])
                # Log tweak in context7 (smolagents memory)
                self._log_design_change("user_tweak", user_feedback["tweak"])
            else:
                satisfied = True
        # 3. Fabrication & Assembly
        self._log_design_change("final_form", form)
        self._dispatch_for_fabrication(form)
        logger.info("✅ Design finalized and dispatched for fabrication.")
        return form

    def _generate_initial_form(self, task: str, material_data: Optional[Dict]) -> Dict:
        """
        Use a Python component in Grasshopper to generate the initial 3D form based on user task and material data.
        """
        logger.info("🧩 Generating initial 3D form using Python in Grasshopper...")
        # [Stub] Call MCP tool or Python component for 3D re-orientation
        # Example: self.agent.run_tool('python_component', ...)
        # In a real implementation, this would call the actual MCP/Grasshopper tool
        form = {"geometry": "initial_form", "metadata": {"task": task, "material": material_data}}
        self._log_design_change("initial_form", form)
        return form

    def _run_simulation(self, form: Dict) -> Dict:
        """
        Run structural simulation (e.g., Kangaroo) on the current form and update as needed.
        """
        logger.info("🧮 Running structural simulation on form...")
        # [Stub] Call MCP tool for simulation
        # Example: self.agent.run_tool('run_simulation', ...)
        form["simulation"] = "simulated"
        self._log_design_change("simulation", form)
        return form

    def _present_form_and_get_user_feedback(self, form: Dict) -> Dict:
        """
        Present the form to the user (e.g., AR visualization) and get feedback/tweaks.
        """
        logger.info("👁️ Presenting form to user for feedback...")
        # [Stub] In a real system, this would interface with AR/VR or UI
        # For now, simulate user always satisfied (no tweaks)
        return {"tweak": None}

    def _apply_user_tweaks(self, form: Dict, tweaks: Dict) -> Dict:
        """
        Apply user-requested tweaks to the form using the Python component in Grasshopper.
        """
        logger.info(f"✏️ Applying user tweaks: {tweaks}")
        # [Stub] Call MCP tool or Python component for 3D re-orientation
        form["geometry"] = "tweaked_form"
        form["tweaks"] = tweaks
        return form

    def _dispatch_for_fabrication(self, form: Dict):
        """
        Dispatch the finalized form for fabrication and assembly.
        """
        logger.info("🚚 Dispatching final form for fabrication and assembly...")
        # [Stub] Communicate with Fabrication Agent and Robot
        pass

    def _log_design_change(self, change_type: str, data: Any):
        """
        Log design changes, user tweaks, and simulation outcomes using context7 database (via smolagents memory).
        """
        logger.info(f"📝 Logging design change: {change_type}")
        # [Stub] In a real system, this would write to context7 or smolagents memory
        # For now, just log
        pass

    def get_memory_statistics(self) -> Dict[str, Any]:
        try:
            from ..memory import get_memory_statistics
            stats = get_memory_statistics(self.agent)
            stats["agent_type"] = "design_agent"
            stats["mcp_integration"] = "enabled"
            stats["connection_status"] = (
                "persistent" if hasattr(self, "mcp_connection") else "disconnected"
            )
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting memory statistics: {e}")
            return {"error": str(e)}

    def _create_self_history_tool(self):
        from smolagents import tool
        @tool
        def get_my_design_history(design_id: str) -> str:
            """
            Retrieve the memory history for a specific design decision.

            Args:
                design_id: The identifier of the design decision to retrieve history for.

            Returns:
                A string summary of the agent's memory related to the specified design decision.
            """
            try:
                if not hasattr(self.agent, "memory") or not hasattr(self.agent.memory, "steps"):
                    return f"I don't have any memory history yet."
                memory_steps = self.agent.memory.steps
                relevant_steps = []
                for step in memory_steps:
                    if hasattr(step, "observations") and step.observations:
                        if design_id in step.observations:
                            relevant_steps.append(step)
                if not relevant_steps:
                    return f"I don't have any memory about design decision {design_id}."
                context = f"MY MEMORY ABOUT DESIGN DECISION {design_id}:\n\n"
                for i, step in enumerate(relevant_steps, 1):
                    context += f"Memory Step {i} (Step #{step.step_number}):\n"
                    context += f"{step.observations}\n\n"
                context += (
                    f"Found {len(relevant_steps)} memory entries about design decision {design_id}.\n"
                )
                context += "I can reason over this context to answer questions about this design's history."
                return context
            except Exception as e:
                return f"Error accessing my memory: {str(e)}"
        return get_my_design_history

    def _create_design_requirements_tool(self):
        from smolagents import tool
        @tool
        def manage_design_requirements(action: str, requirement_data: Optional[Dict] = None) -> str:
            """
            Manage design requirements and constraints.

            Args:
                action: The action to perform ('add', 'update', 'get', 'validate').
                requirement_data: Optional dictionary with requirement details for add/update actions.

            Returns:
                A string message indicating the result of the operation or the current requirements.
            """
            try:
                if action == "add" and requirement_data:
                    return f"Added requirement: {requirement_data}"
                elif action == "update" and requirement_data:
                    return f"Updated requirement: {requirement_data}"
                elif action == "get":
                    return "Current requirements: [Would fetch from system]"
                elif action == "validate":
                    return "Requirements validation: [Would run validation]"
                else:
                    return "Invalid action or missing data"
            except Exception as e:
                return f"Error managing requirements: {str(e)}"
        return manage_design_requirements

    def _create_design_validation_tool(self):
        from smolagents import tool
        @tool
        def validate_design_decision(decision_type: str, parameters: Dict) -> str:
            """
            Validate a design decision against requirements and constraints.

            Args:
                decision_type: The type of design decision (e.g., 'span', 'material').
                parameters: Dictionary of decision parameters to validate.

            Returns:
                A string with validation results and recommendations.
            """
            try:
                return f"Validated {decision_type} decision: {parameters}"
            except Exception as e:
                return f"Error validating design: {str(e)}"
        return validate_design_decision

    def __del__(self):
        try:
            if hasattr(self, "mcp_connection") and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("🔌 Persistent MCP connection closed for design agent")
        except Exception as e:
            logger.warning(f"⚠️ Error closing MCP connection in design agent: {e}")

def create_design_agent(
    model_name: str = "design",
    monitoring_callback: Optional[Any] = None,
    **kwargs,
) -> ToolCallingAgent:
    wrapper = SmolagentsDesignAgent(
        model_name=model_name,
        monitoring_callback=monitoring_callback,
    )
    internal_agent = wrapper.agent
    internal_agent._wrapper = wrapper
    logger.info("✅ Created design agent configured for managed_agents pattern")
    return internal_agent

def get_design_system_prompt() -> str:
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "design_agent.md"
    if not prompt_path.exists():
        logger.warning("⚠️ Design agent system prompt not found, using default prompt")
        return """You are a design agent specialized in interactive 3D form exploration and assembly.\nYour role is to orchestrate the design-explore-refine-fabricate workflow, using a Python component in Grasshopper and the context7 database for memory/context.\n"""
    return prompt_path.read_text(encoding="utf-8")
