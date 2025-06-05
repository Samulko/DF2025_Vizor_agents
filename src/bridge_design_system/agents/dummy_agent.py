"""Dummy agent - Reference implementation demonstrating agent patterns."""
from typing import List

from smolagents import Tool, tool

from .base_agent import BaseAgent, log_agent_action


class DummyAgent(BaseAgent):
    """Reference implementation demonstrating agent patterns.
    
    This agent serves as a template and testing tool for validating
    the multi-agent system architecture.
    """
    
    def __init__(self):
        """Initialize the dummy agent."""
        super().__init__(
            name="dummy_agent",
            description="Reference agent for testing patterns and communication"
        )
        self.data_store = {}  # Simple in-memory storage for testing
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the dummy agent."""
        return """You are a dummy agent for testing the bridge design system.

Your role is to:
1. Demonstrate proper agent communication patterns
2. Test tool execution and error handling
3. Validate inter-agent communication
4. Provide reference implementations

You have access to simple tools for:
- Processing text
- Storing and retrieving test data
- Simulating computations
- Generating test responses

Always respond clearly and include relevant test data in your responses."""
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize dummy tools for testing."""
        
        @tool
        def process_text(text: str, operation: str = "uppercase") -> str:
            """Process text with various operations.
            
            Args:
                text: Input text to process
                operation: Operation to perform (uppercase, lowercase, reverse)
                
            Returns:
                Processed text
            """
            if operation == "uppercase":
                return text.upper()
            elif operation == "lowercase":
                return text.lower()
            elif operation == "reverse":
                return text[::-1]
            else:
                return f"Unknown operation: {operation}"
        
        @tool
        def store_data(key: str, value: str) -> str:
            """Store test data in memory.
            
            Args:
                key: Storage key
                value: Value to store
                
            Returns:
                Confirmation message
            """
            self.data_store[key] = value
            return f"Stored '{value}' under key '{key}'"
        
        @tool
        def retrieve_data(key: str) -> str:
            """Retrieve test data from memory.
            
            Args:
                key: Storage key
                
            Returns:
                Stored value or error message
            """
            if key in self.data_store:
                return self.data_store[key]
            else:
                return f"No data found for key '{key}'"
        
        @tool
        def simulate_calculation(x: float, y: float, operation: str = "add") -> float:
            """Simulate mathematical calculations.
            
            Args:
                x: First number
                y: Second number
                operation: Operation (add, subtract, multiply, divide)
                
            Returns:
                Calculation result
            """
            operations = {
                "add": lambda a, b: a + b,
                "subtract": lambda a, b: a - b,
                "multiply": lambda a, b: a * b,
                "divide": lambda a, b: a / b if b != 0 else float('inf')
            }
            
            if operation in operations:
                return operations[operation](x, y)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        
        @tool
        def generate_test_response(test_type: str = "success") -> dict:
            """Generate various test responses.
            
            Args:
                test_type: Type of response (success, warning, error)
                
            Returns:
                Test response dictionary
            """
            responses = {
                "success": {
                    "status": "success",
                    "message": "Test completed successfully",
                    "data": {"test_id": "123", "timestamp": "2024-01-01"}
                },
                "warning": {
                    "status": "warning",
                    "message": "Test completed with warnings",
                    "warnings": ["Resource usage high", "Slow response time"]
                },
                "error": {
                    "status": "error",
                    "message": "Test failed",
                    "error": "Simulated error for testing"
                }
            }
            
            return responses.get(test_type, responses["success"])
        
        return [
            process_text,
            store_data,
            retrieve_data,
            simulate_calculation,
            generate_test_response
        ]
    
    @log_agent_action
    def test_pattern(self, pattern_name: str) -> dict:
        """Test specific agent patterns.
        
        Args:
            pattern_name: Name of pattern to test
            
        Returns:
            Test results
        """
        patterns = {
            "tool_execution": self._test_tool_execution,
            "error_handling": self._test_error_handling,
            "state_management": self._test_state_management
        }
        
        if pattern_name in patterns:
            return patterns[pattern_name]()
        else:
            return {"error": f"Unknown pattern: {pattern_name}"}
    
    def _test_tool_execution(self) -> dict:
        """Test tool execution patterns."""
        results = []
        
        # Test each tool
        test_response = self.run("Process the text 'hello world' to uppercase")
        results.append({"tool": "process_text", "success": test_response.success})
        
        test_response = self.run("Store 'test_value' with key 'test_key'")
        results.append({"tool": "store_data", "success": test_response.success})
        
        test_response = self.run("Calculate 10 + 20")
        results.append({"tool": "simulate_calculation", "success": test_response.success})
        
        return {
            "pattern": "tool_execution",
            "results": results,
            "summary": f"{sum(r['success'] for r in results)}/{len(results)} tools tested successfully"
        }
    
    def _test_error_handling(self) -> dict:
        """Test error handling patterns."""
        # Test with invalid operation
        response = self.run("Calculate 10 divided by 0")
        
        return {
            "pattern": "error_handling",
            "handled_gracefully": not response.success,
            "error_message": response.message
        }
    
    def _test_state_management(self) -> dict:
        """Test state management patterns."""
        # Store and retrieve data
        self.run("Store 'state_test' with key 'state_key'")
        response = self.run("Retrieve data for key 'state_key'")
        
        return {
            "pattern": "state_management",
            "state_preserved": "state_test" in response.message,
            "conversation_history_length": len(self.conversation_history)
        }