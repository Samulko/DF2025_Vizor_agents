"""HRC Agent - Integrates human-robot collaboration process planning into the design process."""
import logging
import gc
import asyncio
import time
from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from smolagents import CodeAgent, tool
from smolagents.agents import PromptTemplates, SystemPromptStep, EMPTY_PROMPT_TEMPLATES
from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger
from ..config.settings import settings
from .base_agent import BaseAgent, AgentResponse, AgentError

logger = get_logger(__name__)


class TaskType(Enum):
    """Types of assembly tasks."""
    PLACEMENT = "placement"
    JOINING = "joining"
    VERIFICATION = "verification"


class ActorType(Enum):
    """Types of actors that can perform tasks."""
    HUMAN = "human" # place and screw beam
    ROBOT = "robot" # place and hold beam
    COLLABORATIVE = "collaborative" # implemented as a parallel human/robot task


@dataclass
class AssemblyElement:
    """Represents a timber element in the assembly."""
    id: str
    length: float
    width: float
    height: float
    position: Dict[str, float]  # x, y, z coordinates
    orientation: Dict[str, float]  # roll, pitch, yaw
    connections: List[str]  # IDs of connected elements


@dataclass
class AssemblyTask:
    """Represents a single assembly task."""
    id: str
    type: TaskType
    assigned_to: ActorType
    element_id: str
    description: str
    dependencies: List[str]  # IDs of tasks that must complete first
    estimated_duration: float  # in seconds
    status: str = "pending"


class HRCAgentSTDIO:
    """STDIO-only HRC Agent for maximum reliability.
    
    This agent uses only STDIO transport to avoid HTTP timeout issues
    and async/sync conflicts. Tool discovery happens once and is cached
    by the smolagents framework.
    """
    
    def __init__(self, custom_tools: Optional[List] = None, model_name: str = "hrc"):
        """Initialize the STDIO HRC Agent.
        
        Args:
            custom_tools: Additional custom tools to add to the agent
            model_name: Model configuration name (from settings)
        """
        self.custom_tools = custom_tools or []
        self.model_name = model_name
        self.max_steps = getattr(settings, 'AGENT_MAX_STEPS', 10)
        
        # Robot constraints
        self.robot_constraints = {
            "max_reach": 1.2,  # meters
            "beam_length_limits": {
                "min": 0.2,  # meters
                "min_hold": 0.4, # meters
                "max": 0.6   # meters
            }
        }
        
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
        
        # Conversation memory for continuous chat (separate from agent lifecycle)
        self.conversation_history = []
        
        # Task sequence tracking
        self.current_sequence: List[AssemblyTask] = []
        self.completed_tasks: List[AssemblyTask] = []
        
        # Assembly state
        self.assembly_elements: Dict[str, AssemblyElement] = {}
        
        logger.info(f"Initialized {model_name} agent with STDIO-only transport (temperature=0.1 for precise instruction following)")
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt for the HRC agent."""
        try:
            # Get the project root directory
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # Go up to vizor_agents/
            prompt_path = project_root / "system_prompts" / "hrc_agent.md"
            
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
        return """You are an expert Human-Robot Collaboration (HRC) Process Planning Agent.

Your role:
- Integrate assembly process planning into the design phase
- Analyze design requirements for robotic manufacturability
- Provide feedback for fabrication feasibility
- Generate task sequences 
- Generate task documentation

Key considerations:
- Robot reach limit: 1.2 meters
- Beam length limits: 20cm to 70cm
- Beam length limit for holding the beam: 40cm
- Task sequencing and consideration of limitations

Operating principles:
- Proactively identify potential assembly challenges
- Balance human and robot capabilities
- Optimize for efficiency
- Provide clear assembly instructions
- Communicate constraints to the triage agent

You have access to tools for:
- Analyzing design requirements
- Generating task sequences
- Evaluating manufacturability
- Optimizing assembly processes
- Providing design feedback"""

    def run(self, task: str) -> Any:
        """Execute the HRC task using STDIO transport.
        
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
                
                # Create fresh agent for each request to avoid dead tool references
                # Conversation memory is maintained separately in self.conversation_history
                fresh_agent = CodeAgent(
                    tools=all_tools,
                    model=self.model,
                    add_base_tools=True,
                    max_steps=self.max_steps,
                    additional_authorized_imports=self.SAFE_IMPORTS
                )
                logger.info("Created fresh agent with live MCP tools for reliable execution")
                
                # Build conversation context for continuity
                conversation_context = self._build_conversation_context(task)
                
                # Execute task with fresh agent and conversation context
                result = fresh_agent.run(conversation_context)
                
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
You have access to basic HRC tools that return data structures instead of creating actual assembly sequences.
Please inform the user that full HRC functionality requires MCP connection restoration.
"""
            
            result = fallback_agent.run(fallback_task)
            logger.info("✅ Task completed in fallback mode")
            return result
            
        except Exception as e:
            logger.error(f"❌ Even fallback execution failed: {e}")
            return {
                "error": "Task execution failed",
                "message": f"Both MCP and fallback execution failed: {e}",
                "fallback_mode": True
            }
    
    def _create_fallback_tools(self) -> List:
        """Create fallback tools for when MCP is unavailable."""
        
        @tool
        def analyze_design_requirements_fallback(design_data: Dict[str, Any]) -> Dict[str, Any]:
            """Fallback version of design requirements analysis.
            
            Args:
                design_data: Dictionary containing design information
                
            Returns:
                Dictionary with analysis results
            """
            return {
                "status": "fallback_mode",
                "message": "Using fallback analysis - MCP unavailable",
                "elements_analyzed": len(design_data.get("elements", [])),
                "manufacturability_issues": [],
                "recommendations": [
                    "Ensure beam lengths are between 30cm and 40cm",
                    "Keep element positions within robot reach (1.2m)"
                ]
            }
        
        @tool
        def generate_assembly_sequence_fallback(design_data: Dict[str, Any]) -> Dict[str, Any]:
            """Fallback version of assembly sequence generation.
            
            Args:
                design_data: Dictionary containing design information
                
            Returns:
                Dictionary with assembly sequence
            """
            return {
                "status": "fallback_mode",
                "message": "Using fallback sequence generation - MCP unavailable",
                "sequence": [],
                "total_tasks": 0,
                "estimated_duration": 0
            }
        
        @tool
        def notify_triage_agent_fallback(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Fallback version of triage agent notification.
            
            Args:
                issues: List of design issues to report
                
            Returns:
                Dictionary with notification status
            """
            return {
                "status": "fallback_mode",
                "message": "Using fallback notification - MCP unavailable",
                "issues_reported": len(issues)
            }
        
        return [
            analyze_design_requirements_fallback,
            generate_assembly_sequence_fallback,
            notify_triage_agent_fallback
        ]
    
    def _build_conversation_context(self, new_task: str) -> str:
        """Build conversation context from history.
        
        Args:
            new_task: New task to add to context
            
        Returns:
            Formatted conversation context
        """
        if not self.conversation_history:
            return new_task
        
        # Build context from recent history
        context = "Previous conversation:\n"
        for entry in self.conversation_history[-3:]:  # Last 3 interactions
            context += f"\nUser: {entry['task']}\n"
            context += f"Assistant: {entry['result']}\n"
        
        context += f"\nNew task: {new_task}"
        return context
    
    def _store_conversation(self, task: str, result: Any) -> None:
        """Store conversation for future reference.
        
        Args:
            task: Task that was executed
            result: Result from task execution
        """
        self.conversation_history.append({
            "task": task,
            "result": result,
            "timestamp": time.time()
        })
        
        # Keep only last 10 interactions
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def reset_conversation(self) -> None:
        """Reset conversation history."""
        self.conversation_history = []
        logger.info("Conversation history reset")
    
    def get_tool_info(self) -> dict:
        """Get information about available tools.
        
        Returns:
            Dictionary with tool information
        """
        return {
            "tools": [
                "analyze_design_requirements",
                "generate_assembly_sequence",
                "notify_triage_agent"
            ],
            "fallback_tools": [
                "analyze_design_requirements_fallback",
                "generate_assembly_sequence_fallback",
                "notify_triage_agent_fallback"
            ]
        }


def create_hrc_agent_stdio(custom_tools: Optional[List] = None, model_name: str = "hrc") -> HRCAgentSTDIO:
    """Create a new HRC agent with STDIO transport.
    
    Args:
        custom_tools: Additional custom tools to add to the agent
        model_name: Model configuration name (from settings)
        
    Returns:
        Initialized HRC agent
    """
    return HRCAgentSTDIO(custom_tools=custom_tools, model_name=model_name)

