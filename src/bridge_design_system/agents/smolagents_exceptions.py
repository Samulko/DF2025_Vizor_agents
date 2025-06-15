"""Smolagents exception handling utilities and migration helpers.

This module provides utilities for migrating from custom AgentError enum
to native smolagents exceptions, plus helper functions for proper error
handling following smolagents best practices.
"""
import logging
from typing import Optional, Dict, Any, Union
from enum import Enum

from smolagents import (
    AgentError,
    AgentExecutionError,
    AgentParsingError,
    AgentMaxStepsError,
    AgentGenerationError
)

logger = logging.getLogger(__name__)


class LegacyAgentError(Enum):
    """Legacy custom error types for migration reference.
    
    THIS IS DEPRECATED - Use smolagents exceptions instead.
    Kept for migration compatibility only.
    """
    GEOMETRY_INVALID = "geometry_invalid"           # → AgentExecutionError
    MATERIAL_INSUFFICIENT = "material_insufficient" # → AgentExecutionError  
    STRUCTURAL_FAILURE = "structural_failure"       # → AgentExecutionError
    MCP_CONNECTION_LOST = "mcp_connection_lost"     # → AgentExecutionError
    TOOL_EXECUTION_FAILED = "tool_execution_failed" # → AgentExecutionError
    CONTEXT_OVERFLOW = "context_overflow"           # → AgentMaxStepsError
    INVALID_REQUEST = "invalid_request"             # → AgentParsingError


class SmolagentsExceptionMapper:
    """Maps legacy errors to appropriate smolagents exceptions."""
    
    @staticmethod
    def map_legacy_error(
        legacy_error: LegacyAgentError,
        message: str,
        original_exception: Optional[Exception] = None
    ) -> AgentError:
        """Map legacy error to appropriate smolagents exception.
        
        Args:
            legacy_error: Legacy error type
            message: Error message
            original_exception: Original exception if available
            
        Returns:
            Appropriate smolagents exception
        """
        # Map to specific smolagents exceptions
        if legacy_error == LegacyAgentError.CONTEXT_OVERFLOW:
            return AgentMaxStepsError(
                f"Context overflow: {message}",
                original_exception
            )
        
        elif legacy_error == LegacyAgentError.INVALID_REQUEST:
            return AgentParsingError(
                f"Invalid request: {message}",
                original_exception
            )
        
        elif legacy_error in [
            LegacyAgentError.GEOMETRY_INVALID,
            LegacyAgentError.MATERIAL_INSUFFICIENT,
            LegacyAgentError.STRUCTURAL_FAILURE,
            LegacyAgentError.MCP_CONNECTION_LOST,
            LegacyAgentError.TOOL_EXECUTION_FAILED
        ]:
            return AgentExecutionError(
                f"Execution error ({legacy_error.value}): {message}",
                original_exception
            )
        
        else:
            # Fallback to base AgentError
            return AgentError(
                f"Agent error ({legacy_error.value}): {message}",
                original_exception
            )
    
    @staticmethod
    def create_geometry_error(message: str, original_exception: Optional[Exception] = None) -> AgentExecutionError:
        """Create geometry-specific execution error."""
        from smolagents import AgentLogger
        return AgentExecutionError(f"Geometry operation failed: {message}", AgentLogger())
    
    @staticmethod
    def create_material_error(message: str, original_exception: Optional[Exception] = None) -> AgentExecutionError:
        """Create material-specific execution error."""
        return AgentExecutionError(f"Material operation failed: {message}", original_exception)
    
    @staticmethod
    def create_structural_error(message: str, original_exception: Optional[Exception] = None) -> AgentExecutionError:
        """Create structural-specific execution error."""
        return AgentExecutionError(f"Structural analysis failed: {message}", original_exception)
    
    @staticmethod
    def create_mcp_error(message: str, original_exception: Optional[Exception] = None) -> AgentExecutionError:
        """Create MCP connection error."""
        return AgentExecutionError(f"MCP connection failed: {message}", original_exception)


class LegacyAgentResponse:
    """Legacy response format for migration reference.
    
    THIS IS DEPRECATED - Use direct agent responses instead.
    Kept for migration compatibility only.
    """
    
    def __init__(
        self,
        success: bool,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[LegacyAgentError] = None
    ):
        self.success = success
        self.message = message
        self.data = data
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        result = {
            "success": self.success,
            "message": self.message
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error.value
        return result


class SmolagentsResponseHelper:
    """Helper for creating proper smolagents responses."""
    
    @staticmethod
    def create_success_response(
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create successful response in smolagents format.
        
        Args:
            result: The successful result
            metadata: Optional metadata to include
            
        Returns:
            Formatted success response
        """
        response = {
            "success": True,
            "result": result
        }
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def handle_agent_error(
        error: Union[AgentError, Exception],
        context: str = ""
    ) -> Dict[str, Any]:
        """Handle and format agent errors properly.
        
        Args:
            error: The error that occurred
            context: Additional context about the error
            
        Returns:
            Formatted error response
        """
        # Log the error
        logger.error(f"Agent error in {context}: {error}", exc_info=True)
        
        # Format response based on error type
        if isinstance(error, AgentMaxStepsError):
            return {
                "success": False,
                "error_type": "max_steps",
                "message": f"Agent exceeded maximum steps: {error}",
                "context": context,
                "recoverable": True,
                "suggestion": "Try resetting the conversation or reducing task complexity"
            }
        
        elif isinstance(error, AgentParsingError):
            return {
                "success": False,
                "error_type": "parsing",
                "message": f"Failed to parse agent response: {error}",
                "context": context,
                "recoverable": True,
                "suggestion": "Try rephrasing the request or checking input format"
            }
        
        elif isinstance(error, AgentExecutionError):
            return {
                "success": False,
                "error_type": "execution",
                "message": f"Agent execution failed: {error}",
                "context": context,
                "recoverable": True,
                "suggestion": "Check tool availability and try again"
            }
        
        elif isinstance(error, AgentGenerationError):
            return {
                "success": False,
                "error_type": "generation",
                "message": f"Agent failed to generate response: {error}",
                "context": context,
                "recoverable": True,
                "suggestion": "Try simplifying the request or checking model availability"
            }
        
        elif isinstance(error, AgentError):
            return {
                "success": False,
                "error_type": "agent",
                "message": f"Agent error: {error}",
                "context": context,
                "recoverable": True,
                "suggestion": "Check agent configuration and try again"
            }
        
        else:
            # Non-agent exception
            return {
                "success": False,
                "error_type": "system",
                "message": f"System error: {error}",
                "context": context,
                "recoverable": False,
                "suggestion": "Contact system administrator"
            }


class ErrorHandlingPatterns:
    """Examples of proper error handling patterns with smolagents."""
    
    @staticmethod
    def tool_error_pattern():
        """Example of proper tool error handling."""
        
        from smolagents import tool
        
        @tool
        def example_tool_with_error_handling(input_data: str) -> str:
            """Example tool with proper error handling.
            
            Args:
                input_data: Input data to process
                
            Returns:
                Processed result
                
            Raises:
                ValueError: If input data is invalid
            """
            try:
                # Validate input
                if not input_data or not isinstance(input_data, str):
                    raise ValueError("Input data must be a non-empty string")
                
                # Process data
                result = input_data.upper()
                
                # Log success
                logger.info(f"Tool processed: {len(input_data)} chars → {len(result)} chars")
                
                return result
                
            except Exception as e:
                # Log error for debugging
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                # Re-raise with clear message for agent
                raise ValueError(f"Failed to process input: {e}")
    
    @staticmethod
    def agent_error_pattern():
        """Example of proper agent error handling."""
        
        def run_agent_with_error_handling(agent, task: str):
            """Run agent with proper error handling."""
            try:
                # Run the agent
                result = agent.run(task)
                
                # Handle success
                return SmolagentsResponseHelper.create_success_response(
                    result=result,
                    metadata={"task": task, "agent": type(agent).__name__}
                )
                
            except AgentMaxStepsError as e:
                return SmolagentsResponseHelper.handle_agent_error(e, "agent_execution")
            
            except AgentExecutionError as e:
                return SmolagentsResponseHelper.handle_agent_error(e, "agent_execution")
            
            except AgentParsingError as e:
                return SmolagentsResponseHelper.handle_agent_error(e, "agent_execution")
            
            except AgentError as e:
                return SmolagentsResponseHelper.handle_agent_error(e, "agent_execution")
            
            except Exception as e:
                # Unexpected system error
                return SmolagentsResponseHelper.handle_agent_error(e, "system_error")
    
    @staticmethod
    def migration_example():
        """Example of migrating from legacy to smolagents patterns."""
        
        print("❌ OLD PATTERN (Custom AgentError enum):")
        print("""
        # Old way - custom enum and response
        from .base_agent import AgentError, AgentResponse
        
        try:
            result = agent.run(task)
            return AgentResponse(
                success=True,
                message=str(result),
                data={"step_count": 1}
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Agent failed: {e}",
                error=AgentError.TOOL_EXECUTION_FAILED
            )
        """)
        
        print("✅ NEW PATTERN (Smolagents exceptions):")
        print("""
        # New way - smolagents exceptions
        from smolagents import AgentError, AgentExecutionError
        from .smolagents_exceptions import SmolagentsResponseHelper
        
        try:
            result = agent.run(task)
            return SmolagentsResponseHelper.create_success_response(
                result=result,
                metadata={"step_count": 1}
            )
        except AgentExecutionError as e:
            return SmolagentsResponseHelper.handle_agent_error(e, "task_execution")
        except AgentError as e:
            return SmolagentsResponseHelper.handle_agent_error(e, "task_execution")
        """)


def validate_smolagents_integration() -> Dict[str, Any]:
    """Validate that smolagents exceptions are properly available."""
    try:
        from smolagents import AgentLogger
        
        # Test exception imports
        test_exceptions = [
            AgentError,
            AgentExecutionError,
            AgentParsingError,
            AgentMaxStepsError,
            AgentGenerationError
        ]
        
        # Create a dummy logger for testing
        test_logger = AgentLogger()
        
        available_exceptions = []
        for exc_class in test_exceptions:
            try:
                # Test that we can create the exception with logger
                test_exc = exc_class("test message", test_logger)
                available_exceptions.append(exc_class.__name__)
            except Exception as e:
                logger.error(f"Failed to create {exc_class.__name__}: {e}")
        
        return {
            "integration_valid": len(available_exceptions) == len(test_exceptions),
            "available_exceptions": available_exceptions,
            "total_expected": len(test_exceptions),
            "smolagents_version": "latest"  # Could be enhanced to check actual version
        }
        
    except Exception as e:
        return {
            "integration_valid": False,
            "error": str(e),
            "suggestion": "Ensure smolagents is properly installed and up to date"
        }


if __name__ == "__main__":
    # Validate integration
    validation = validate_smolagents_integration()
    print(f"Smolagents integration: {validation}")
    
    # Show migration patterns
    ErrorHandlingPatterns.migration_example()