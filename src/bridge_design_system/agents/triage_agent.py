"""Triage Agent - Main orchestrator for the bridge design system."""
from typing import Dict, List, Optional

from smolagents import CodeAgent, Tool

from ..config.model_config import ModelProvider
from ..config.settings import settings
from .base_agent import AgentError, AgentResponse, BaseAgent


class TriageAgent(BaseAgent):
    """Main orchestrator agent that coordinates specialized agents.
    
    The Triage Agent receives human requests, clarifies requirements,
    and delegates tasks to appropriate specialized agents.
    """
    
    def __init__(self):
        """Initialize the triage agent."""
        super().__init__(
            name="triage_agent",
            description="Expert AI Triage Agent that coordinates bridge design tasks"
        )
        
        # Managed agents will be initialized later
        self.managed_agents: Dict[str, BaseAgent] = {}
        
        # Track current design state
        self.design_state = {
            "current_step": "initial",
            "bridge_type": None,
            "start_point": None,
            "end_point": None,
            "materials_checked": False,
            "structural_validated": False
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the triage agent."""
        # Read from file for easy updates
        try:
            with open("system_prompts/triage_agent.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to embedded prompt
            return """You are an expert AI Triage Agent. Your primary mission is to assist a human designer and builder in the step-by-step creation of a bridge. You will achieve this by understanding human instructions, breaking them down into actionable tasks, and strategically delegating these tasks to a team of specialized agents under your coordination.

**Your Core Responsibilities as Triage Agent:**

1. Receive and Analyze Human Input: Carefully interpret the designer's requests.
2. Task Clarification: If any part of the human's input is vague, ambiguous, or incomplete, you MUST ask clarifying questions before proceeding. **Prioritize asking the single most critical question required to take the next logical step.** DO NOT MAKE ASSUMPTIONS.
3. Agent Selection & Delegation: Based on the clarified request, determine the appropriate specialized agent to handle the task. You will explicitly state which agent you are assigning the task to.
4. Contextual Instruction: Provide the selected agent with all necessary information and context from the human's request and the current state of the bridge design to perform its task effectively.
5. Monitor & Report: Receive the output or status from the specialized agent and clearly communicate this back to the human designer.
6. Maintain Project Continuity: Keep track of the design progress and ensure that steps are followed logically.

**You coordinate and delegate tasks to the following specialized agents:**

* **Geometry Agent:**
  * Function: Generates and manipulates geometric forms. The geometry agent works methodically step by step.
  * Environment: Operates within a Rhino 8 Grasshopper environment.
  * Capability: Can write and execute Python scripts to create, modify, and analyze geometry for the bridge.
  * Your Interaction: You will instruct this agent on what geometric operations to perform.

* **Material Management Agent:**
  * Function: Tracks available construction materials.
  * Environment: Accesses and queries a material stock database.
  * Capability: Can report on current quantities of specified materials and flag potential shortages.
  * Your Interaction: You will instruct this agent to check for or report on specific material availability.

* **Structural Agent:**
  * Function: Assesses the structural integrity of the bridge design.
  * Environment: Utilizes simulation software.
  * Capability: Can run structural analyses, identify stress points, evaluate stability, and suggest adjustments.
  * Your Interaction: You will instruct this agent to perform structural evaluations.

**CRITICAL OPERATING RULES:**

1. Adherence to Role: Strictly follow your role as a Triage Agent. Do not attempt to perform the tasks of the specialized agents yourself.
2. Prioritize Clarity: Always seek clarification for ambiguous requests.
3. No Assumptions: Do not invent details not explicitly provided.
4. Transparency in Delegation: When delegating, inform: "I will now ask the [Agent Name] to [perform specific task]."
5. Sequential Processing: Address tasks step-by-step.
6. Report Limitations: If a request cannot be fulfilled, clearly state this limitation.
7. Focus on Execution: Facilitate the execution of the human's design intentions.
8. Conciseness and Focus: Keep responses concise, focusing on the immediate next step.
9. Incremental Clarification: Ask only one or two clarifying questions at a time.
10. Human-Led Pacing: Await human input after each response.
11. Reduced Redundancy: Avoid repeatedly explaining your role unless asked."""
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize tools for the triage agent.
        
        The triage agent doesn't use tools directly but coordinates other agents.
        """
        return []  # No direct tools, uses managed agents instead
    
    def initialize_agent(self):
        """Initialize the triage agent with managed agents."""
        # Import here to avoid circular imports
        from .geometry_agent import GeometryAgent
        from .material_agent import MaterialAgent
        from .structural_agent import StructuralAgent
        
        # Initialize managed agents (only the three specialized agents)
        self.managed_agents = {
            "geometry": GeometryAgent(),
            "material": MaterialAgent(),
            "structural": StructuralAgent()
        }
        
        # Initialize each managed agent
        for agent in self.managed_agents.values():
            agent.initialize_agent()
        
        # Create the triage agent with managed agents
        managed_agent_instances = list(self.managed_agents.values())
        
        self._agent = CodeAgent(
            tools=[],  # No direct tools
            model=self.model,
            name=self.name,
            description=self.description,
            max_steps=settings.max_agent_steps,
            managed_agents=[agent._agent for agent in managed_agent_instances],
            additional_authorized_imports=[
                "json", "datetime", "pathlib", "typing", "dataclasses", "enum"
            ]
        )
        
        self.logger.info(f"Triage agent initialized with {len(self.managed_agents)} managed agents")
    
    def update_design_state(self, updates: Dict[str, any]):
        """Update the current design state.
        
        Args:
            updates: Dictionary of state updates
        """
        self.design_state.update(updates)
        self.logger.info(f"Design state updated: {updates}")
    
    def get_agent_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all managed agents.
        
        Returns:
            Dictionary mapping agent names to their status
        """
        status = {}
        for name, agent in self.managed_agents.items():
            status[name] = {
                "initialized": agent._agent is not None,
                "conversation_length": len(agent.conversation_history),
                "step_count": agent.step_count
            }
        return status
    
    def handle_design_request(self, request: str) -> AgentResponse:
        """Handle a design request by coordinating specialized agents.
        
        Args:
            request: Human designer's request
            
        Returns:
            AgentResponse with coordination results
        """
        # Validate request
        validation_error = self.validate_request({"task": request})
        if validation_error:
            return AgentResponse(
                success=False,
                message=validation_error,
                error=AgentError.INVALID_REQUEST
            )
        
        # Import here to avoid circular imports  
        from ..api.status_broadcaster import broadcast_agent_delegating
        
        # Example of delegation broadcasting (when agent determines delegation)
        # This is a simplified example - in practice, the triage agent would
        # analyze the request and determine which agent to delegate to
        if "geometry" in request.lower() or "point" in request.lower() or "bridge" in request.lower():
            broadcast_agent_delegating("triage", "geometry", request)
        elif "material" in request.lower() or "stock" in request.lower():
            broadcast_agent_delegating("triage", "material", request)
        elif "structural" in request.lower() or "analysis" in request.lower():
            broadcast_agent_delegating("triage", "structural", request)
        
        # Process through the triage agent
        return self.run(request)
    
    def reset_all_agents(self):
        """Reset conversation state for all agents."""
        self.reset_conversation()
        for agent in self.managed_agents.values():
            agent.reset_conversation()
        self.design_state = {
            "current_step": "initial",
            "bridge_type": None,
            "start_point": None,
            "end_point": None,
            "materials_checked": False,
            "structural_validated": False
        }
        self.logger.info("All agents and design state reset")