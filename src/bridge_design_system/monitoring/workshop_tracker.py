"""
Simple Workshop Tracker - Copy this class into your agent to enable logging.

Usage:
1. Copy this class into your agent file
2. Add: tracker = WorkshopTracker("your_agent_name")  
3. Call: tracker.log_step() at key points in your agent

Example:
```python
class MyAgent:
    def __init__(self):
        self.tracker = WorkshopTracker("my_agent")
    
    def process_task(self, task):
        self.tracker.log_step(
            task_description=task,
            status="started"
        )
        
        try:
            result = self.do_work(task)
            self.tracker.log_step(
                task_description=task,
                status="completed", 
                response_content=str(result)
            )
            return result
        except Exception as e:
            self.tracker.log_step(
                task_description=task,
                status="failed",
                error_message=str(e)
            )
            raise
```
"""

import time
from datetime import datetime
from typing import List, Optional, Dict, Any


class WorkshopTracker:
    """Simple workshop tracker that students can copy into their agents."""
    
    def __init__(self, agent_name: str):
        """Initialize tracker for an agent.
        
        Args:
            agent_name: Name of your agent (e.g., "geometry_agent", "my_custom_agent")
        """
        self.agent_name = agent_name
        self.step_counter = 0
        self._start_time = time.time()
        
        print(f"📊 WorkshopTracker initialized for {agent_name}")
    
    def log_step(
        self,
        task_description: Optional[str] = None,
        status: str = "completed",
        tool_calls: List[str] = None,
        response_content: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ):
        """Log a step in your agent's workflow.
        
        Args:
            task_description: What task your agent is working on
            status: "started", "completed", "failed", or "in_progress"  
            tool_calls: List of tools/functions your agent called
            response_content: The output/result from your agent
            error_message: Any error that occurred
            duration_seconds: How long this step took (auto-calculated if not provided)
        """
        self.step_counter += 1
        
        # Auto-calculate duration if not provided
        if duration_seconds is None:
            duration_seconds = time.time() - self._start_time
            self._start_time = time.time()  # Reset for next step
        
        # Try to log to the workshop system if available
        try:
            from ..monitoring.trace_logger import log_agent_interaction
            
            log_agent_interaction(
                agent_name=self.agent_name,
                step_number=self.step_counter,
                task_description=task_description,
                status=status,
                tool_calls=tool_calls or [],
                response_content=response_content,
                error_message=error_message,
                duration_seconds=duration_seconds,
                token_usage=None,  # Could be enhanced
                memory_size=0      # Could be enhanced
            )
            
        except ImportError:
            # Fallback: just print to console if workshop system not available
            print(f"📝 [{self.agent_name}] Step {self.step_counter}: {status}")
            if task_description:
                print(f"   Task: {task_description[:100]}...")
            if response_content:
                print(f"   Result: {response_content[:100]}...")
            if error_message:
                print(f"   Error: {error_message}")
    
    def log_start(self, task_description: str):
        """Convenience method to log when starting a task."""
        self.log_step(
            task_description=task_description,
            status="started"
        )
    
    def log_success(self, task_description: str, result: str, tools_used: List[str] = None):
        """Convenience method to log successful completion."""
        self.log_step(
            task_description=task_description,
            status="completed",
            tool_calls=tools_used,
            response_content=result
        )
    
    def log_error(self, task_description: str, error: Exception):
        """Convenience method to log errors."""
        self.log_step(
            task_description=task_description,
            status="failed",
            error_message=str(error)
        )

    def log_tool_call(self, tool_name: str, tool_params: Dict[str, Any] = None, result: Any = None):
        """Convenience method to log individual tool calls."""
        params_str = f" with {tool_params}" if tool_params else ""
        result_str = f" → {result}" if result else ""
        
        self.log_step(
            task_description=f"Called {tool_name}{params_str}",
            status="completed",
            tool_calls=[tool_name],
            response_content=f"{tool_name}{result_str}"
        )


# Example usage for students to copy:
"""
# Copy this into your agent class:

class MyCustomAgent:
    def __init__(self):
        # Add this line to enable workshop tracking:
        self.tracker = WorkshopTracker("my_custom_agent")  # Use your agent's name
    
    def solve_problem(self, problem):
        # Log when starting work:
        self.tracker.log_start(f"Solving: {problem}")
        
        try:
            # Do your agent's work here
            result = self.my_algorithm(problem)
            
            # Log successful completion:
            self.tracker.log_success(
                task_description=f"Solving: {problem}",
                result=str(result),
                tools_used=["my_algorithm"]
            )
            
            return result
            
        except Exception as e:
            # Log errors:
            self.tracker.log_error(f"Solving: {problem}", e)
            raise
    
    def use_external_tool(self, tool_name, params):
        # Log individual tool calls:
        result = external_api.call(tool_name, params)
        self.tracker.log_tool_call(tool_name, params, result)
        return result
"""