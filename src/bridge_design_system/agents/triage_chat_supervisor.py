"""
Pure Bridge Design Supervisor - No chat, no voice, just bridge engineering coordination.

This supervisor coordinates between geometry and rational agents for bridge design tasks.
It's called by chat agents via tools, following the OpenAI realtime agents pattern.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from smolagents import CodeAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..memory import track_design_changes
from .rational_smolagents import create_rational_agent

logger = get_logger(__name__)


class BridgeDesignSupervisor:
    """
    Pure bridge design supervisor - no voice, no chat, just engineering coordination.
    
    Follows OpenAI realtime agents supervisor pattern where complex reasoning
    is handled by a dedicated supervisor called via tools from chat agents.
    """
    
    def __init__(self, component_registry=None, monitoring_callback=None):
        """Initialize bridge design supervisor with specialized agents."""
        # Create model
        model = ModelProvider.get_model("triage")
        
        # Create managed agents
        self.geometry_agent = self._create_geometry_agent(monitoring_callback)
        self.rational_agent = self._create_rational_agent(monitoring_callback)
        
        # Create coordination tools
        coordination_tools = self._create_coordination_tools()
        
        # Prepare step callbacks for supervisor monitoring
        step_callbacks = [track_design_changes]
        if monitoring_callback:
            if (
                callable(monitoring_callback)
                and hasattr(monitoring_callback, "__name__")
                and "create" in monitoring_callback.__name__
            ):
                supervisor_monitor = monitoring_callback("bridge_design_supervisor")
            else:
                from ..monitoring.agent_monitor import create_monitor_callback
                supervisor_monitor = create_monitor_callback("bridge_design_supervisor", monitoring_callback)
            step_callbacks.append(supervisor_monitor)
        
        # Create supervisor agent with managed agents pattern
        self.supervisor = CodeAgent(
            tools=coordination_tools,
            model=model,
            name="bridge_design_supervisor",
            description="Coordinates bridge design tasks between specialized agents",
            max_steps=6,
            step_callbacks=step_callbacks,
            additional_authorized_imports=["typing", "json", "datetime"],
            managed_agents=[self.geometry_agent, self.rational_agent],
        )
        
        # Add bridge design system prompt
        custom_prompt = self._get_bridge_design_prompt()
        self.supervisor.prompt_templates["system_prompt"] = (
            self.supervisor.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
        )
        
        self.component_registry = component_registry
        logger.info("✅ Bridge Design Supervisor initialized with managed agents")
    
    def handle_bridge_design_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle bridge design task - pure engineering coordination.
        
        This is the main entry point called by chat agents via tools.
        
        Args:
            task: Bridge design task description
            context: Optional context (gaze data, previous conversation, etc.)
            
        Returns:
            Structured response with task results
        """
        try:
            # Enhance task with context if provided
            enhanced_task = task
            if context:
                if context.get("gaze_id"):
                    enhanced_task += f"\n\nGaze context: focusing on {context['gaze_id']}"
                if context.get("conversation_context"):
                    enhanced_task += f"\n\nConversation context: {context['conversation_context']}"
                if context.get("component_type"):
                    enhanced_task += f"\n\nComponent focus: {context['component_type']}"
            
            logger.info(f"🔧 Supervisor handling bridge design task: {task[:100]}...")
            
            # Execute via supervisor with managed agents
            result = self.supervisor.run(enhanced_task)
            
            logger.info("✅ Bridge design task completed successfully")
            return {
                "success": True,
                "result": result,
                "task_type": "bridge_design",
                "supervisor": "bridge_design_supervisor",
                "agents_used": ["geometry_agent", "rational_agent"]
            }
            
        except Exception as e:
            logger.error(f"❌ Bridge design task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "task_type": "bridge_design"
            }
    
    def get_design_status(self) -> Dict[str, Any]:
        """Get current bridge design status."""
        return {
            "supervisor_active": True,
            "supervisor_type": "smolagents_managed_agents",
            "geometry_agent": {
                "status": "active", 
                "type": "mcp_enabled",
                "name": "geometry_agent"
            },
            "rational_agent": {
                "status": "active", 
                "type": "structural_analysis",
                "name": "rational_agent"
            },
            "total_memory_steps": (
                len(self.supervisor.memory.steps) 
                if hasattr(self.supervisor, 'memory') else 0
            ),
            "managed_agents_count": 2
        }
    
    def reset_design_session(self) -> Dict[str, Any]:
        """Reset all design agents for fresh session."""
        try:
            agents_cleared = 0
            
            # Reset the main supervisor memory
            if hasattr(self.supervisor, "memory") and hasattr(self.supervisor.memory, "steps"):
                steps_cleared = len(self.supervisor.memory.steps)
                self.supervisor.memory.steps.clear()
                logger.info(f"✅ Cleared {steps_cleared} supervisor memory steps")
                agents_cleared += 1

            # Reset managed agents memory
            if hasattr(self.supervisor, "managed_agents") and self.supervisor.managed_agents:
                for i, agent in enumerate(self.supervisor.managed_agents):
                    agent_name = getattr(agent, "name", f"agent_{i}")

                    # Reset agent memory directly
                    if hasattr(agent, "memory") and hasattr(agent.memory, "steps"):
                        steps_cleared = len(agent.memory.steps)
                        agent.memory.steps.clear()
                        logger.info(f"✅ Cleared {steps_cleared} {agent_name} memory steps")
                        agents_cleared += 1

                    # Special handling for geometry agent's internal component cache
                    if hasattr(agent, "_wrapper"):
                        wrapper = agent._wrapper
                        if hasattr(wrapper, "internal_component_cache"):
                            cache_cleared = len(wrapper.internal_component_cache)
                            wrapper.internal_component_cache.clear()
                            logger.info(f"✅ Cleared {cache_cleared} {agent_name} component cache entries")

            logger.info("🔄 All bridge design agent memories reset - fresh design session")
            return {
                "reset": "completed", 
                "agents_cleared": agents_cleared,
                "session_state": "fresh"
            }

        except Exception as e:
            logger.error(f"⚠️ Error during reset: {e}")
            return {
                "reset": "completed_with_warnings",
                "error": str(e),
                "session_state": "reset_attempted"
            }

    def _create_geometry_agent(self, monitoring_callback: Optional[Any] = None):
        """Create geometry agent using existing standalone implementation."""
        logger.info("Creating geometry agent for supervisor")
        
        from .geometry_agent_smolagents import create_geometry_agent
        
        geometry_monitor = None
        if monitoring_callback:
            if (
                callable(monitoring_callback)
                and hasattr(monitoring_callback, "__name__")
                and "create" in monitoring_callback.__name__
            ):
                geometry_monitor = monitoring_callback("geometry_agent")
            else:
                from ..monitoring.agent_monitor import create_monitor_callback
                geometry_monitor = create_monitor_callback("geometry_agent", monitoring_callback)
        
        return create_geometry_agent(monitoring_callback=geometry_monitor)

    def _create_rational_agent(self, monitoring_callback: Optional[Any] = None):
        """Create rational agent for structural analysis."""
        logger.info("Creating rational agent for supervisor")
        
        rational_monitor = None
        if monitoring_callback:
            if (
                callable(monitoring_callback)
                and hasattr(monitoring_callback, "__name__")
                and "create" in monitoring_callback.__name__
            ):
                rational_monitor = monitoring_callback("rational_agent")
            else:
                from ..monitoring.agent_monitor import create_monitor_callback
                rational_monitor = create_monitor_callback("rational_agent", monitoring_callback)
        
        return create_rational_agent(monitoring_callback=rational_monitor)

    def _create_coordination_tools(self) -> List:
        """Create tools for coordination and state management."""
        
        # Import the context-based recall tools from memory_tools
        from ..tools.memory_tools import delegate_element_history_query, create_two_step_delegation_task

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
        def check_design_state() -> dict:
            """
            Check current bridge design state and progress.

            Returns:
                Current design state dictionary
            """
            # State is tracked via native smolagents memory
            return {
                "status": "Bridge design state tracked via smolagents memory",
                "note": "Use geometry memory tools to check previous design decisions",
                "supervisor": "active",
                "managed_agents": 2
            }

        @tool
        def debug_component_tracking() -> str:
            """
            Debug tool to show autonomous geometry agent state.

            Returns:
                Debug information about geometry agent state
            """
            try:
                debug_info = []
                debug_info.append("=== BRIDGE DESIGN SUPERVISOR DEBUG ===")
                debug_info.append("Architecture: Chat-Supervisor Pattern")
                debug_info.append("Supervisor: Bridge Design Coordination")
                debug_info.append("Managed Agents: geometry_agent, rational_agent")
                debug_info.append("Component tracking: Handled internally by geometry agent")
                debug_info.append("\nTo see component details, ask the geometry agent directly")
                debug_info.append("or use delegation tools for specific element queries.")
                debug_info.append("\n=== END DEBUG ===")

                result = "\n".join(debug_info)
                logger.info("🐛 Bridge design supervisor debug info requested")
                return result

            except Exception as e:
                logger.error(f"❌ Error in debug tool: {e}")
                return f"Debug tool error: {e}"

        return [
            update_design_phase,
            check_design_state,
            debug_component_tracking,
            # Context-based delegation tools for true smol-agents native solution
            delegate_element_history_query,
            create_two_step_delegation_task,
        ]

    def _get_bridge_design_prompt(self) -> str:
        """Get bridge design system prompt from file."""
        try:
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            prompt_path = project_root / "system_prompts" / "triage_agent.md"

            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8")
            else:
                # Fallback prompt for bridge design coordination
                return """You are a bridge design supervisor that coordinates specialized agents for bridge engineering tasks.

You manage geometry agents for 3D modeling and Grasshopper integration, and rational agents for structural analysis.

Your role is pure coordination - delegate tasks to the appropriate specialized agents and synthesize their results.

For bridge design tasks:
- Geometry creation/modification → delegate to geometry agent
- Structural analysis → delegate to rational agent  
- Multi-step workflows → coordinate between agents

Be technical, precise, and focused on engineering coordination."""
                
        except Exception as e:
            logger.warning(f"Could not load system prompt: {e}")
            return "You are a bridge design supervisor coordinating specialized engineering agents."


def create_bridge_design_supervisor_tools(supervisor: BridgeDesignSupervisor):
    """Create tools that chat agents can use to invoke the bridge design supervisor."""
    
    @tool
    def design_bridge_component(task_description: str, component_type: str = "general") -> Dict[str, Any]:
        """
        Design or modify bridge components using the bridge design supervisor.
        
        Use this for complex bridge engineering tasks that require coordination
        between geometry and structural analysis agents.
        
        Args:
            task_description: Natural language description of the bridge design task
            component_type: Type of component (deck, support, cable, general)
            
        Returns:
            Results from bridge design coordination
        """
        context = {"component_type": component_type}
        result = supervisor.handle_bridge_design_task(task_description, context)
        
        # Extract key information for chat agent
        if result["success"]:
            return {
                "status": "completed",
                "summary": f"Bridge design task completed successfully",
                "details": result.get("result", "Task completed"),
                "agents_used": result.get("agents_used", [])
            }
        else:
            return {
                "status": "failed", 
                "error": result.get("error", "Unknown error"),
                "suggestion": "Try breaking down the task into smaller components"
            }
    
    @tool
    def get_bridge_design_status() -> Dict[str, Any]:
        """
        Get current status of bridge design system and agents.
        
        Use this to check if the bridge design system is ready and
        to see memory/session status.
        """
        return supervisor.get_design_status()
    
    @tool
    def reset_bridge_design() -> Dict[str, Any]:
        """
        Reset bridge design system for a fresh design session.
        
        Use this when starting a completely new bridge design or
        when the user wants to clear all previous work.
        """
        return supervisor.reset_design_session()
    
    return [design_bridge_component, get_bridge_design_status, reset_bridge_design]


# Factory function for backward compatibility
def create_bridge_design_supervisor(component_registry=None, monitoring_callback=None) -> BridgeDesignSupervisor:
    """
    Factory function to create bridge design supervisor.
    
    This replaces the TriageSystemWrapper for pure bridge design coordination.
    """
    return BridgeDesignSupervisor(
        component_registry=component_registry,
        monitoring_callback=monitoring_callback
    ) 