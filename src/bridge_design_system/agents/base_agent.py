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
    """Standard error types for agent operations."""
    GEOMETRY_INVALID = "geometry_invalid"
    MATERIAL_INSUFFICIENT = "material_insufficient"
    STRUCTURAL_FAILURE = "structural_failure"
    MCP_CONNECTION_LOST = "mcp_connection_lost"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    CONTEXT_OVERFLOW = "context_overflow"
    INVALID_REQUEST = "invalid_request"


@dataclass
class AgentResponse:
    """Standard response format for agent operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[AgentError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        result = {
            "success": self.success,
            "message": self.message
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error.value
        return result


def log_agent_action(func):
    """Decorator for logging agent actions."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logger = logging.getLogger(self.__class__.__name__)
        logger.info(f"Executing {func.__name__} with args: {args[:2]}...")  # Limit arg logging
        try:
            result = func(self, *args, **kwargs)
            logger.info(f"Success: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper


class BaseAgent(ABC):
    """Base class for all agents in the bridge design system."""
    
    def __init__(self, name: str, description: str):
        """Initialize base agent.
        
        Args:
            name: Agent name for identification
            description: Agent description for multi-agent coordination
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize model from configuration
        self.model = ModelProvider.get_model(name.replace("_agent", ""))
        
        # Tools will be set by subclasses
        self.tools: List[Tool] = []
        
        # Agent will be initialized after tools are set
        self._agent: Optional[CodeAgent] = None
        
        # Track conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.step_count = 0
        
        self.logger.info(f"Initialized {name} with model {ModelProvider.get_model_info(name.replace('_agent', ''))}")
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent.
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def _initialize_tools(self) -> List[Tool]:
        """Initialize tools specific to this agent.
        
        Returns:
            List of tools for this agent
        """
        pass
    
    def initialize_agent(self):
        """Initialize the smolagents CodeAgent with tools and configuration."""
        self.tools = self._initialize_tools()
        
        self._agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            name=self.name,
            description=self.description,
            max_steps=settings.max_agent_steps,
            additional_authorized_imports=[
                "json", "datetime", "pathlib", "typing", "dataclasses", "enum", "asyncio"
            ]
        )
        
        self.logger.info(f"Agent initialized with {len(self.tools)} tools")
    
    @log_agent_action
    def run(self, task: str, reset: bool = True) -> AgentResponse:
        """Run the agent with a given task.
        
        Args:
            task: Task description or request
            reset: Whether to reset conversation state
            
        Returns:
            AgentResponse with results
        """
        if not self._agent:
            self.initialize_agent()
        
        # Import here to avoid circular imports
        from ..api.status_broadcaster import broadcast_agent_thinking, broadcast_agent_active, broadcast_agent_idle, broadcast_agent_error
        
        try:
            # Broadcast thinking status
            broadcast_agent_thinking(self.name.replace("_agent", ""), task)
            
            # Check step count
            if self.step_count >= settings.max_agent_steps:
                broadcast_agent_error(self.name.replace("_agent", ""), "Maximum steps reached")
                return AgentResponse(
                    success=False,
                    message="Maximum steps reached, please start a new conversation",
                    error=AgentError.CONTEXT_OVERFLOW
                )
            
            # Broadcast active status
            broadcast_agent_active(self.name.replace("_agent", ""), "Processing task")
            
            # Run the agent
            result = self._agent.run(task, reset=reset)
            
            # Update state
            self.step_count += 1
            self.conversation_history.append({
                "task": task,
                "result": result,
                "step": self.step_count
            })
            
            # Broadcast completion
            broadcast_agent_idle(self.name.replace("_agent", ""))
            
            return AgentResponse(
                success=True,
                message=str(result),
                data={"step_count": self.step_count}
            )
            
        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}")
            broadcast_agent_error(self.name.replace("_agent", ""), str(e))
            return AgentResponse(
                success=False,
                message=f"Agent execution failed: {str(e)}",
                error=AgentError.TOOL_EXECUTION_FAILED
            )
    
    def reset_conversation(self):
        """Reset conversation state."""
        self.conversation_history = []
        self.step_count = 0
        self.logger.info("Conversation state reset")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation.
        
        Returns:
            Dictionary with conversation statistics and recent history
        """
        return {
            "agent": self.name,
            "total_steps": self.step_count,
            "recent_history": self.conversation_history[-5:],  # Last 5 interactions
            "tools_available": [tool.name for tool in self.tools]
        }
    
    def validate_request(self, request: Dict[str, Any]) -> Optional[str]:
        """Validate incoming request format.
        
        Args:
            request: Request dictionary
            
        Returns:
            Error message if invalid, None if valid
        """
        if not isinstance(request, dict):
            return "Request must be a dictionary"
        
        if "task" not in request:
            return "Request must contain 'task' field"
        
        if not isinstance(request["task"], str):
            return "Task must be a string"
        
        if len(request["task"]) > 1000:
            return "Task description too long (max 1000 characters)"
        
        return None