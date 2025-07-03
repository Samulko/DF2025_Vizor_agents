"""
Workshop Tracker Module - Simple copy-paste logging for student agents.

Just copy this entire file into your project and import it:

```python
from workshop_tracker import WorkshopTracker

class MyAgent:
    def __init__(self):
        self.tracker = WorkshopTracker("my_agent")
    
    def do_task(self, task):
        self.tracker.log_start(task)
        try:
            result = self.work(task)
            self.tracker.log_success(task, str(result))
            return result
        except Exception as e:
            self.tracker.log_error(task, e)
            raise
```
"""

import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


class WorkshopTracker:
    """Simple workshop tracker that logs agent activities."""
    
    def __init__(self, agent_name: str, logs_dir: str = "workshop_logs"):
        """Initialize tracker for an agent.
        
        Args:
            agent_name: Name of your agent (e.g., "geometry_agent", "my_agent")
            logs_dir: Directory to save logs (default: "workshop_logs")
        """
        self.agent_name = agent_name
        self.step_counter = 0
        self._start_time = time.time()
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create logs directory
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        (self.logs_dir / "agents").mkdir(exist_ok=True)
        (self.logs_dir / "daily").mkdir(exist_ok=True)
        
        print(f"📊 WorkshopTracker active for {agent_name}")
    
    def log_step(
        self,
        task_description: Optional[str] = None,
        status: str = "completed",
        tool_calls: List[str] = None,
        response_content: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ):
        """Log a step in your agent's workflow."""
        self.step_counter += 1
        
        # Auto-calculate duration if not provided
        if duration_seconds is None:
            duration_seconds = time.time() - self._start_time
            self._start_time = time.time()
        
        # Create trace record
        trace = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "step_number": self.step_counter,
            "task_description": task_description,
            "status": status,
            "tool_calls": tool_calls or [],
            "response_content": response_content,
            "error_message": error_message,
            "duration_seconds": round(duration_seconds, 2),
            "token_usage": None,
            "memory_size": 0
        }
        
        # Save to files
        self._save_trace(trace)
        
        # Also try to use official workshop system if available
        try:
            # Try to import and use the official logger
            import sys
            if 'bridge_design_system.monitoring.trace_logger' in sys.modules:
                from bridge_design_system.monitoring.trace_logger import log_agent_interaction
                log_agent_interaction(
                    agent_name=self.agent_name,
                    step_number=self.step_counter,
                    task_description=task_description,
                    status=status,
                    tool_calls=tool_calls or [],
                    response_content=response_content,
                    error_message=error_message,
                    duration_seconds=duration_seconds,
                )
        except:
            pass  # Fallback to our own logging
    
    def _save_trace(self, trace):
        """Save trace to log files."""
        try:
            # Agent-specific log
            agent_file = self.logs_dir / "agents" / f"{self.agent_name}_traces.jsonl"
            with agent_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(trace) + "\n")
            
            # Daily log
            daily_file = self.logs_dir / "daily" / f"{datetime.now().strftime('%Y-%m-%d')}_traces.jsonl"
            with daily_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(trace) + "\n")
                
        except Exception as e:
            print(f"⚠️ Failed to save trace: {e}")
    
    # Convenience methods for common patterns:
    
    def log_start(self, task_description: str):
        """Log when starting a task."""
        self.log_step(task_description=task_description, status="started")
    
    def log_success(self, task_description: str, result: str, tools_used: List[str] = None):
        """Log successful completion."""
        self.log_step(
            task_description=task_description,
            status="completed",
            tool_calls=tools_used,
            response_content=result
        )
    
    def log_error(self, task_description: str, error: Exception):
        """Log errors."""
        self.log_step(
            task_description=task_description,
            status="failed",
            error_message=str(error)
        )

    def log_tool_call(self, tool_name: str, params: Dict = None, result: Any = None):
        """Log individual tool calls."""
        params_str = f" with {params}" if params else ""
        result_str = f" → {result}" if result else ""
        
        self.log_step(
            task_description=f"Called {tool_name}{params_str}",
            status="completed",
            tool_calls=[tool_name],
            response_content=f"{tool_name}{result_str}"
        )

    def log_thinking(self, thought: str):
        """Log agent reasoning/thinking steps."""
        self.log_step(
            task_description=f"Thinking: {thought}",
            status="in_progress",
            response_content=thought
        )


# Example usage:
if __name__ == "__main__":
    # Demo of how students can use this
    tracker = WorkshopTracker("demo_agent")
    
    tracker.log_start("Processing user request")
    time.sleep(0.1)  # Simulate work
    
    tracker.log_thinking("I need to analyze the geometry first")
    time.sleep(0.1)  # Simulate thinking
    
    tracker.log_tool_call("create_bridge", {"span": 100, "height": 20}, "Bridge created")
    time.sleep(0.1)  # Simulate tool call
    
    tracker.log_success("Processing user request", "Successfully created bridge with 4 elements")
    
    print(f"\n📋 Check {tracker.logs_dir} for log files!")


"""
STUDENT INSTRUCTIONS:

1. Copy this file (workshop_tracker.py) into your project folder

2. Import and use in your agent:

```python
from workshop_tracker import WorkshopTracker

class MyBridgeAgent:
    def __init__(self):
        self.tracker = WorkshopTracker("my_bridge_agent")
    
    def design_bridge(self, requirements):
        self.tracker.log_start(f"Designing bridge: {requirements}")
        
        try:
            # Your agent logic here
            self.tracker.log_thinking("Analyzing structural requirements")
            
            span = self.calculate_span(requirements)
            self.tracker.log_tool_call("calculate_span", requirements, span)
            
            bridge = self.create_structure(span)
            self.tracker.log_tool_call("create_structure", {"span": span}, "Bridge created")
            
            result = f"Bridge designed with span {span}m"
            self.tracker.log_success(f"Designing bridge: {requirements}", result)
            
            return bridge
            
        except Exception as e:
            self.tracker.log_error(f"Designing bridge: {requirements}", e)
            raise
```

3. Your logs will be saved to workshop_logs/ directory automatically!

4. Use these methods in your agent:
   - tracker.log_start(task) - When starting work
   - tracker.log_success(task, result) - When completing successfully  
   - tracker.log_error(task, error) - When something fails
   - tracker.log_tool_call(tool_name, params, result) - For external calls
   - tracker.log_thinking(thought) - For reasoning steps
"""