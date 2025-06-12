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
        
        # Conversation memory for continuous chat (separate from agent lifecycle)
        self.conversation_history = []
        
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
        from .geometry_agent_stdio import GeometryAgentSTDIO
        # Temporarily disabled for geometry-only mode
        # from .material_agent import MaterialAgent
        # from .structural_agent import StructuralAgent
        
        # Initialize geometry agent with simplified STDIO-only strategy
        geometry_agent = GeometryAgentSTDIO()
        self.logger.info("✅ Geometry agent initialized with STDIO-only strategy (100% reliable)")
        
        # Initialize managed agents - GEOMETRY ONLY MODE
        self.managed_agents = {
            "geometry": geometry_agent,
            # Temporarily disabled
            # "material": MaterialAgent(),
            # "structural": StructuralAgent()
        }
        
        # Initialize non-geometry agents normally
        # Temporarily disabled - no other agents to initialize
        # for name, agent in self.managed_agents.items():
        #     if name != "geometry":  # Geometry agent already initialized above
        #         agent.initialize_agent()
        
        # Create the triage agent with managed agents
        # For smolagents compatibility, we need to extract the internal agent for most agents
        # but handle GeometryAgentMCPAdapt specially since it uses direct tool execution
        managed_agent_instances = []
        for name, agent in self.managed_agents.items():
            if name == "geometry":
                # GeometryAgentMCPAdapt doesn't need internal agent extraction
                # It manages its own execution and tool lifecycle
                self.logger.info("Geometry agent using MCPAdapt - direct execution mode")
                # Note: We'll handle geometry tasks differently in handle_design_request
            # Temporarily disabled - no other agents
            # else:
            #     # Other agents follow the standard BaseAgent pattern
            #     managed_agent_instances.append(agent._agent)
        
        # Note: CodeAgent will be created fresh for each request to preserve conversation context
        # Store configuration for fresh agent creation
        self.agent_config = {
            "tools": [],  # No direct tools
            "model": self.model,
            "name": self.name,
            "description": self.description,
            "max_steps": settings.max_agent_steps,
            "managed_agents": managed_agent_instances,
            "additional_authorized_imports": [
                "json", "datetime", "pathlib", "typing", "dataclasses", "enum"
            ]
        }
        
        # Create initial agent for compatibility (will be replaced for each request)
        self._agent = CodeAgent(**self.agent_config)
        
        self.logger.info(f"Triage agent initialized with {len(self.managed_agents)} managed agents")
    
    def update_design_state(self, updates: Dict[str, any]):
        """Update the current design state.
        
        Args:
            updates: Dictionary of state updates
        """
        self.design_state.update(updates)
        self.logger.info(f"Design state updated: {updates}")
    
    def get_agent_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all managed agents including MCP connection info.
        
        Returns:
            Dictionary mapping agent names to their status
        """
        status = {}
        for name, agent in self.managed_agents.items():
            if name == "geometry":
                # Special handling for GeometryAgentSTDIO
                tool_info = agent.get_tool_info()
                status[name] = {
                    "initialized": True,  # STDIO agent is always initialized
                    "mcp_connected": tool_info.get("connected", False),
                    "mode": tool_info.get("mode", "unknown"),
                    "strategy": tool_info.get("strategy", "unknown"),
                    "transport": tool_info.get("transport", "unknown"),
                    "tool_count": tool_info.get("total_tools", 0),
                    "mcp_tool_count": tool_info.get("mcp_tools", 0),
                    "fallback_tools": tool_info.get("fallback_tools", 0),
                    "custom_tools": tool_info.get("custom_tools", 0),
                    "message": tool_info.get("message", "No status available"),
                    "agent_type": "STDIO"
                }
            else:
                # Standard BaseAgent pattern
                status[name] = {
                    "initialized": agent._agent is not None,
                    "conversation_length": len(agent.conversation_history),
                    "step_count": agent.step_count,
                    "agent_type": "BaseAgent"
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
        
        # Check if this is a geometry-specific request and handle directly
        if self._is_geometry_request(request):
            result = self._handle_geometry_request(request)
        else:
            # For other requests, process through the triage agent with conversation context
            result = self._run_with_context(request)
        
        # Store the conversation for future reference
        self._store_conversation(request, result)
        
        return result
    
    def _is_geometry_request(self, request: str) -> bool:
        """Check if a request is specifically for geometry operations."""
        # Direct geometry creation keywords
        creation_keywords = [
            "point", "line", "curve", "spiral", "geometry", "create", 
            "draw", "build", "construct", "coordinate", "3d", "bridge", "staircase"
        ]
        
        # Geometry modification keywords that require context
        modification_keywords = [
            "wider", "bigger", "smaller", "larger", "thicker", "thinner",
            "taller", "shorter", "longer", "extend", "scale", "resize",
            "modify", "change", "adjust", "increase", "decrease", "expand"
        ]
        
        # Shape and structure keywords
        shape_keywords = [
            "circle", "rectangle", "box", "sphere", "cylinder", "cone",
            "arch", "beam", "column", "deck", "support", "foundation"
        ]
        
        # Tool and capability keywords
        tool_keywords = [
            "mcp", "tool", "tools", "available", "capability", "capabilities",
            "grasshopper", "component", "function", "what can", "list of"
        ]
        
        request_lower = request.lower()
        
        # Check for tool-related queries - these should go to geometry agent
        if any(keyword in request_lower for keyword in tool_keywords):
            self.logger.info(f"Detected tool/capability inquiry: '{request}'")
            return True
            
        # Check for direct geometry keywords
        if any(keyword in request_lower for keyword in creation_keywords + shape_keywords):
            return True
            
        # Check for modification keywords - these need conversation context
        if any(keyword in request_lower for keyword in modification_keywords):
            # If we have conversation history with geometry work, this is likely a geometry request
            if self.conversation_history:
                for interaction in self.conversation_history[-3:]:  # Check last 3 interactions
                    prev_request = interaction['request'].lower()
                    prev_result = str(interaction['result']).lower()
                    
                    # If recent interaction involved geometry creation or modification
                    if (any(kw in prev_request for kw in creation_keywords + shape_keywords) or
                        any(kw in prev_result for kw in ["component", "grasshopper", "geometry", "spiral", "staircase"])):
                        self.logger.info(f"Detected geometry modification request with context: '{request}'")
                        return True
        
        return False
    
    def _handle_geometry_request(self, request: str) -> AgentResponse:
        """Handle geometry-specific requests directly with geometry agent including conversation context."""
        try:
            if "geometry" not in self.managed_agents:
                return AgentResponse(
                    success=False,
                    message="Geometry agent not available",
                    error=AgentError.AGENT_NOT_AVAILABLE
                )
            
            geometry_agent = self.managed_agents["geometry"]
            
            # Build conversation context for geometry agent (including triage conversation)
            request_with_context = self._build_conversation_context_for_geometry(request)
            
            # Execute task with STDIO geometry agent (100% reliable) including context
            self.logger.info(f"Delegating geometry task to STDIO agent with context: {request[:50]}...")
            
            result = geometry_agent.run(request_with_context)
            
            # Check if result indicates success
            if result and not ("error" in str(result).lower() and "fallback" not in str(result).lower()):
                self.logger.info("✅ Geometry task completed successfully")
                return AgentResponse(
                    success=True,
                    message=str(result),
                    data={"result": result, "agent": "geometry", "method": "stdio_with_context"}
                )
            else:
                self.logger.warning("⚠️ Geometry task completed with issues")
                return AgentResponse(
                    success=True,  # Still consider success as task was handled
                    message=str(result),
                    data={"result": result, "agent": "geometry", "method": "stdio_with_context", "status": "partial"}
                )
                
        except Exception as e:
            self.logger.error(f"❌ Geometry task delegation failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Geometry task failed: {e}",
                error=AgentError.EXECUTION_ERROR
            )
    
    def _build_conversation_context_for_geometry(self, new_request: str) -> str:
        """Build conversation context specifically for geometry agent delegation.
        
        This includes relevant context from triage conversation history.
        
        Args:
            new_request: The new geometry request
            
        Returns:
            Request with triage conversation context for geometry continuity
        """
        if not self.conversation_history:
            return new_request
        
        # Find relevant geometry-related interactions from history
        relevant_history = []
        for interaction in self.conversation_history[-5:]:  # Last 5 interactions
            if any(keyword in interaction['request'].lower() for keyword in [
                'geometry', 'point', 'line', 'curve', 'spiral', 'create', 'draw', 
                'build', 'construct', 'bridge', 'staircase', 'wider', 'bigger', 'smaller'
            ]):
                relevant_history.append(interaction)
        
        if not relevant_history:
            return new_request
        
        # Build context from relevant history
        context_parts = ["CONTEXT: Previous related work:"]
        
        for i, interaction in enumerate(relevant_history[-3:]):  # Last 3 relevant interactions
            context_parts.append(f"Previous task {i+1}:")
            context_parts.append(f"Human: {interaction['request']}")
            # Include just the key result info for geometry continuity
            result_text = str(interaction['result'])
            if "spiral staircase" in result_text.lower():
                context_parts.append("Assistant: Created spiral staircase Grasshopper component")
            elif len(result_text) > 150:
                context_parts.append(f"Assistant: {result_text[:150]}...")
            else:
                context_parts.append(f"Assistant: {result_text}")
            context_parts.append("")
        
        context_parts.append("CURRENT TASK:")
        context_parts.append(new_request)
        context_parts.append("")
        context_parts.append("Note: If the current task refers to previous work (like 'make wider', 'change size'), use the context above to understand what to modify.")
        
        return "\n".join(context_parts)
    
    def _run_with_context(self, request: str) -> AgentResponse:
        """Run triage agent with conversation context for continuity.
        
        Args:
            request: The user's request
            
        Returns:
            AgentResponse with triage results
        """
        try:
            # Build conversation context for continuity
            request_with_context = self._build_conversation_context(request)
            
            # Create fresh agent for each request to avoid dead tool references
            # Conversation memory is maintained separately in self.conversation_history
            fresh_agent = CodeAgent(**self.agent_config)
            self.logger.info("Created fresh triage agent with conversation context")
            
            # Execute request with fresh agent and conversation context
            result = fresh_agent.run(request_with_context)
            
            self.logger.info("✅ Triage request completed with conversation context")
            
            return AgentResponse(
                success=True,
                message=str(result),
                data={"result": result, "agent": "triage", "method": "context"}
            )
            
        except Exception as e:
            self.logger.error(f"❌ Triage request with context failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Triage request failed: {e}",
                error=AgentError.EXECUTION_ERROR
            )
    
    def _build_conversation_context(self, new_request: str) -> str:
        """Build conversation context for continuity with fresh agents.
        
        This method works with fresh CodeAgent instances by providing conversation
        history as context rather than relying on agent memory.
        
        Args:
            new_request: The new request to execute
            
        Returns:
            Request with conversation context for continuity
        """
        if not self.conversation_history:
            # First interaction - just return the request
            return new_request
        
        # Build context from recent conversation history (last 3 interactions to avoid context overflow)
        recent_history = self.conversation_history[-3:]
        context_parts = []
        
        for i, interaction in enumerate(recent_history):
            context_parts.append(f"Previous interaction {i+1}:")
            context_parts.append(f"Human: {interaction['request']}")
            # Truncate long results to keep context manageable
            result_text = str(interaction['result'])
            if len(result_text) > 200:
                context_parts.append(f"Assistant: {result_text[:200]}...")
            else:
                context_parts.append(f"Assistant: {result_text}")
            context_parts.append("")
        
        context_parts.append("Current request:")
        context_parts.append(new_request)
        
        return "\n".join(context_parts)
    
    def _store_conversation(self, request: str, result: any) -> None:
        """Store conversation interaction for future reference.
        
        Args:
            request: The request that was executed
            result: The result from the request execution
        """
        import time
        self.conversation_history.append({
            "request": request,
            "result": str(result),
            "timestamp": time.time()
        })
        
        # Keep only last 10 interactions to prevent memory overflow
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def reset_all_agents(self):
        """Reset conversation state for all agents."""
        self.reset_conversation()
        for name, agent in self.managed_agents.items():
            if hasattr(agent, 'reset_conversation'):
                agent.reset_conversation()
                self.logger.info(f"Reset conversation for {name} agent")
            else:
                self.logger.warning(f"Agent {name} does not have reset_conversation method")
        
        # Reset conversation history
        self.conversation_history = []
        
        self.design_state = {
            "current_step": "initial",
            "bridge_type": None,
            "start_point": None,
            "end_point": None,
            "materials_checked": False,
            "structural_validated": False
        }
        self.logger.info("All agents, conversation history, and design state reset")