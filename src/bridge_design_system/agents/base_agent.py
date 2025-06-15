"""Base agent class providing common functionality for all agents."""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional

from smolagents import CodeAgent, Tool

from ..config.model_config import ModelProvider
from ..config.settings import settings


class AgentError(Enum):
    """Standard error types for agent operations.
    
    This enum defines all possible error conditions that can occur during agent
    execution. Using an enum ensures consistent error handling across all agents
    and makes it easier to categorize and respond to different types of failures.
    """
    GEOMETRY_INVALID = "geometry_invalid"           # Bridge geometry calculations failed
    MATERIAL_INSUFFICIENT = "material_insufficient" # Not enough materials for construction
    STRUCTURAL_FAILURE = "structural_failure"       # Structural analysis indicates failure
    MCP_CONNECTION_LOST = "mcp_connection_lost"     # Lost connection to MCP server
    TOOL_EXECUTION_FAILED = "tool_execution_failed" # A tool failed to execute properly
    CONTEXT_OVERFLOW = "context_overflow"           # Too many conversation steps
    INVALID_REQUEST = "invalid_request"             # Request format is invalid


@dataclass
class AgentResponse:
    """Standard response format for agent operations.
    
    This class ensures all agents return responses in a consistent format,
    making it easier to handle results in the UI and other components.
    The standardized format includes success status, message, optional data,
    and error information when things go wrong.
    """
    success: bool                                   # Whether the operation succeeded
    message: str                                    # Human-readable result message
    data: Optional[Dict[str, Any]] = None          # Additional structured data
    error: Optional[AgentError] = None             # Error type if operation failed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for JSON serialization.
        
        This method is used when sending responses over the API or storing
        them in logs. It creates a clean dictionary representation that
        can be easily serialized to JSON.
        """
        result = {
            "success": self.success,
            "message": self.message
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error.value  # Convert enum to string
        return result


def log_agent_action(func):
    """Decorator for logging agent actions.
    
    This decorator automatically logs when agent methods start and complete,
    including any errors that occur. It provides consistent logging across
    all agent operations without requiring manual logging in each method.
    
    Usage: @log_agent_action above any method you want to track
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logger = logging.getLogger(self.__class__.__name__)
        logger.info(f"Executing {func.__name__} with args: {args[:2]}...")  # Limit arg logging for privacy
        try:
            result = func(self, *args, **kwargs)
            logger.info(f"Success: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper


class BaseAgent(ABC):
    """Base class for all agents in the bridge design system.
    
    This abstract base class provides the common functionality that all specialized
    agents (like StructuralAgent, GeometryAgent, etc.) need. It handles:
    
    1. Agent initialization and configuration
    2. Integration with the smolagents framework
    3. Conversation state management
    4. Error handling and logging
    5. Tool management
    6. Status broadcasting for the UI
    
    The BaseAgent follows the Template Method pattern - it defines the overall
    structure and flow, while subclasses implement the specific details through
    abstract methods.
    """
    
    def __init__(self, name: str, description: str):
        """Initialize base agent with core configuration.
        
        This constructor sets up the fundamental components every agent needs:
        - Unique identification (name)
        - Description for multi-agent coordination
        - Logging system
        - Model configuration from settings
        - Conversation tracking
        
        Args:
            name: Agent name for identification (e.g., "structural_agent")
            description: Agent description for multi-agent coordination
        """
        self.name = name
        self.description = description
        
        # Set up logging with the agent's class name for easy identification
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Get the appropriate AI model from configuration
        # The model name is derived from the agent name (removes "_agent" suffix)
        self.model = ModelProvider.get_model(name.replace("_agent", ""))
        
        # Tools will be populated by subclasses in _initialize_tools()
        self.tools: List[Tool] = []
        
        # The actual smolagents CodeAgent instance (initialized later)
        # This separation allows us to set up tools first, then create the agent
        self._agent: Optional[CodeAgent] = None
        
        # Track conversation state for multi-turn interactions
        self.conversation_history: List[Dict[str, Any]] = []
        self.step_count = 0  # Prevent infinite loops by limiting steps
        
        self.logger.info(f"Initialized {name} with model {ModelProvider.get_model_info(name.replace('_agent', ''))}")
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent.
        
        Each agent type needs its own specialized system prompt that defines:
        - The agent's role and expertise
        - How it should approach problems
        - What outputs are expected
        - Any domain-specific guidelines
        
        This method must be implemented by each subclass.
        
        Returns:
            System prompt string that will guide the agent's behavior
        """
        pass
    
    @abstractmethod
    def _initialize_tools(self) -> List[Tool]:
        """Initialize tools specific to this agent.
        
        Each agent type has different capabilities and needs different tools.
        For example:
        - StructuralAgent might have tools for load calculations
        - GeometryAgent might have tools for shape operations
        - MaterialAgent might have tools for material property lookups
        
        This method must be implemented by each subclass.
        
        Returns:
            List of smolagents Tool objects that this agent can use
        """
        pass
    
    def initialize_agent(self):
        """Initialize the smolagents CodeAgent with tools and configuration.
        
        This method is called after the BaseAgent constructor completes.
        It follows this sequence:
        1. Get tools from the subclass (_initialize_tools)
        2. Create the smolagents CodeAgent with all configuration
        3. Set up authorized imports for code execution
        4. Log the successful initialization
        
        The separation between __init__ and initialize_agent allows subclasses
        to set up their specific requirements before the agent is created.
        """
        # Get the tools specific to this agent type
        self.tools = self._initialize_tools()
        
        # Create the actual smolagents CodeAgent that will do the work
        self._agent = CodeAgent(
            tools=self.tools,                          # Agent's available tools
            model=self.model,                          # AI model to use
            name=self.name,                            # Agent identifier
            description=self.description,              # For multi-agent coordination
            max_steps=settings.max_agent_steps,        # Prevent infinite loops
            additional_authorized_imports=[            # Python modules the agent can import
                "json", "datetime", "pathlib", "typing", "dataclasses", "enum", "asyncio",
                "re", "collections", "functools", "operator", "itertools"
            ]
        )
        
        self.logger.info(f"Agent initialized with {len(self.tools)} tools")
    
    @log_agent_action
    def run(self, task: str, reset: bool = True) -> AgentResponse:
        """Run the agent with a given task.
        
        This is the main method that executes agent requests. The flow is:
        1. Initialize agent if not already done
        2. Broadcast status updates to the UI
        3. Check safety limits (max steps)
        4. Execute the task using smolagents
        5. Update conversation state
        6. Return standardized response
        
        The method handles all the orchestration while the actual AI work
        is done by the smolagents framework.
        
        Args:
            task: Task description or request from the user
            reset: Whether to reset conversation state (True for new conversations)
            
        Returns:
            AgentResponse with results, data, and any error information
        """
        # Ensure the agent is properly initialized before running
        if not self._agent:
            self.initialize_agent()
        
        # Import status broadcasting functions here to avoid circular imports
        # These functions update the UI to show what the agent is doing
        from ..api.status_broadcaster import broadcast_agent_thinking, broadcast_agent_active, broadcast_agent_idle, broadcast_agent_error
        
        try:
            # Update UI to show the agent is thinking about the task
            broadcast_agent_thinking(self.name.replace("_agent", ""), task)
            
            # Safety check: prevent infinite loops by limiting conversation steps
            if self.step_count >= settings.max_agent_steps:
                broadcast_agent_error(self.name.replace("_agent", ""), "Maximum steps reached")
                return AgentResponse(
                    success=False,
                    message="Maximum steps reached, please start a new conversation",
                    error=AgentError.CONTEXT_OVERFLOW
                )
            
            # Update UI to show the agent is actively processing
            broadcast_agent_active(self.name.replace("_agent", ""), "Processing task")
            
            # Execute the actual task using the smolagents framework
            # This is where the AI model processes the request and uses tools
            result = self._agent.run(task, reset=reset)
            
            # Update conversation state for multi-turn interactions
            self.step_count += 1
            self.conversation_history.append({
                "task": task,
                "result": result,
                "step": self.step_count
            })
            
            # Update UI to show the agent has completed the task
            broadcast_agent_idle(self.name.replace("_agent", ""))
            
            # Return success response with the result
            return AgentResponse(
                success=True,
                message=str(result),
                data={"step_count": self.step_count}
            )
            
        except Exception as e:
            # Handle any errors that occur during execution
            self.logger.error(f"Agent execution failed: {e}")
            broadcast_agent_error(self.name.replace("_agent", ""), str(e))
            return AgentResponse(
                success=False,
                message=f"Agent execution failed: {str(e)}",
                error=AgentError.TOOL_EXECUTION_FAILED
            )
    
    def reset_conversation(self):
        """Reset conversation state for a fresh start.
        
        This method clears the conversation history and step count,
        effectively starting a new conversation. This is useful when:
        - Starting a completely new task
        - The conversation has gotten too long
        - An error occurred and you want to start fresh
        """
        self.conversation_history = []
        self.step_count = 0
        self.logger.info("Conversation state reset")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation state.
        
        This method provides insights into the agent's current state,
        including conversation history and available capabilities.
        Useful for debugging and monitoring agent performance.
        
        Returns:
            Dictionary with conversation statistics and recent history
        """
        return {
            "agent": self.name,
            "total_steps": self.step_count,
            "recent_history": self.conversation_history[-5:],  # Last 5 interactions only
            "tools_available": [tool.name for tool in self.tools]
        }
    
    def validate_request(self, request: Dict[str, Any]) -> Optional[str]:
        """Validate incoming request format before processing.
        
        This method checks that requests are properly formatted and safe
        to process. It prevents common errors and potential security issues
        by validating the request structure and content.
        
        Args:
            request: Request dictionary from the API
            
        Returns:
            Error message if invalid, None if valid
        """
        # Check basic type
        if not isinstance(request, dict):
            return "Request must be a dictionary"
        
        # Check required fields
        if "task" not in request:
            return "Request must contain 'task' field"
        
        # Check task format
        if not isinstance(request["task"], str):
            return "Task must be a string"
        
        # Check reasonable limits to prevent abuse
        if len(request["task"]) > 1000:
            return "Task description too long (max 1000 characters)"
        
        return None  # Request is valid