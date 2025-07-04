# Adding Workshop Tracking to New Agents: Step-by-Step Guide

This tutorial shows you how to add automatic workshop logging to any new agent you create. The tracking will capture all agent activities just like the existing geometry_agent and rational_agent.

## Learning Objectives

By the end of this tutorial, you will:
- Add workshop tracking to any agent in 3 simple steps
- Understand the modular tracking implementation
- See your agent's activities in workshop logs automatically
- Be able to analyze your agent's performance and usage patterns

## Prerequisites

- A working agent implementation (following smolagents patterns)
- Basic understanding of Python imports
- Familiarity with the workshop logging system

---

## Overview: How Agent Tracking Works

The workshop tracking system uses a simple 3-step pattern:

1. **Import the logger** → Add one import line
2. **Initialize step counter** → Add one line to `__init__`
3. **Add logging to run method** → Wrap your execution with logging calls

**That's it!** The system automatically handles:
- ✅ File creation and management
- ✅ Session tracking and aggregation  
- ✅ Error handling and cleanup
- ✅ Integration with workshop reports

---

## Step 1: Import the Trace Logger

Add this import to your agent file:

```python
from ..monitoring.trace_logger import log_agent_interaction
```

**Example - Add to your agent file:**
```python
# Your existing imports
from pathlib import Path
from typing import Any, Dict, List, Optional
from smolagents import ToolCallingAgent

# ADD THIS LINE:
from ..monitoring.trace_logger import log_agent_interaction

# Rest of your agent code...
```

---

## Step 2: Initialize Step Counter

Add a step counter to your agent's `__init__` method:

```python
def __init__(self, model_name: str = "my_agent", **kwargs):
    """Initialize your agent."""
    self.model_name = model_name
    self.step_counter = 0  # ADD THIS LINE
    
    # Rest of your initialization...
```

**Complete Example:**
```python
class MyCustomAgent:
    def __init__(self, model_name: str = "my_agent", **kwargs):
        self.model_name = model_name
        self.step_counter = 0  # Workshop tracking counter
        
        # Agent identification
        self.name = "my_custom_agent"
        self.description = "My specialized agent for custom tasks"
        
        # Initialize your agent components...
```

---

## Step 3: Add Logging to Run Method

Wrap your agent's `run` method with logging calls:

```python
def run(self, task: str) -> Any:
    """Execute task with automatic logging."""
    
    # STEP 3A: Initialize logging
    self.step_counter += 1
    import time
    start_time = time.time()
    
    # STEP 3B: Log task start
    log_agent_interaction(
        agent_name="my_custom_agent",  # Use your agent's name
        step_number=self.step_counter,
        task_description=task[:200] + "..." if len(task) > 200 else task,
        status="started"
    )

    try:
        # STEP 3C: Your original agent logic here
        result = self.agent.run(task)  # Your existing code
        
        # STEP 3D: Log successful completion
        duration = time.time() - start_time
        result_str = str(result) if result else ""
        log_agent_interaction(
            agent_name="my_custom_agent",  # Use your agent's name
            step_number=self.step_counter,
            task_description=task[:200] + "..." if len(task) > 200 else task,
            status="completed",
            response_content=result_str[:500] + "..." if len(result_str) > 500 else result_str,
            duration_seconds=duration
        )
        
        return result
        
    except Exception as e:
        # STEP 3E: Log errors
        duration = time.time() - start_time
        log_agent_interaction(
            agent_name="my_custom_agent",  # Use your agent's name
            step_number=self.step_counter,
            task_description=task[:200] + "..." if len(task) > 200 else task,
            status="failed",
            error_message=str(e),
            duration_seconds=duration
        )
        
        # Re-raise the exception
        raise
```

---

## Complete Implementation Example

Here's a full example showing how to add tracking to a new agent:

```python
"""
My Custom Agent - With Workshop Tracking
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings
from ..monitoring.trace_logger import log_agent_interaction  # STEP 1: Import

logger = get_logger(__name__)


class MyCustomAgent:
    """My specialized agent with automatic workshop tracking."""

    def __init__(self, model_name: str = "my_agent", **kwargs):
        """Initialize the agent with tracking enabled."""
        self.model_name = model_name
        self.step_counter = 0  # STEP 2: Initialize counter
        
        # Agent identification
        self.name = "my_custom_agent"
        self.description = "My specialized agent for custom tasks"
        
        # Initialize model
        self.model = ModelProvider.get_model(model_name, temperature=0.1)
        
        # Your agent setup code here...
        self.agent = ToolCallingAgent(
            tools=[],  # Your tools
            model=self.model,
            max_steps=8,
            name="my_custom_agent",
            description=self.description,
        )
        
        logger.info("My custom agent initialized successfully")

    def run(self, task: str) -> Any:
        """Execute task with automatic workshop tracking."""
        logger.info(f"Executing custom task: {task[:100]}...")
        
        # STEP 3A: Initialize logging
        self.step_counter += 1
        import time
        start_time = time.time()
        
        # STEP 3B: Log task start
        log_agent_interaction(
            agent_name="my_custom_agent",
            step_number=self.step_counter,
            task_description=task[:200] + "..." if len(task) > 200 else task,
            status="started"
        )

        try:
            # STEP 3C: Your original agent logic
            result = self.agent.run(task)
            
            # STEP 3D: Log successful completion
            duration = time.time() - start_time
            result_str = str(result) if result else ""
            log_agent_interaction(
                agent_name="my_custom_agent",
                step_number=self.step_counter,
                task_description=task[:200] + "..." if len(task) > 200 else task,
                status="completed",
                response_content=result_str[:500] + "..." if len(result_str) > 500 else result_str,
                duration_seconds=duration
            )
            
            logger.info("Custom task completed successfully")
            return result
            
        except Exception as e:
            # STEP 3E: Log errors
            duration = time.time() - start_time
            log_agent_interaction(
                agent_name="my_custom_agent",
                step_number=self.step_counter,
                task_description=task[:200] + "..." if len(task) > 200 else task,
                status="failed",
                error_message=str(e),
                duration_seconds=duration
            )
            
            logger.error(f"Custom task failed: {e}")
            raise RuntimeError(f"My custom agent execution failed: {e}")


def create_my_custom_agent(model_name: str = "my_agent", **kwargs) -> ToolCallingAgent:
    """Factory function for creating custom agent instances."""
    logger.info("Creating my custom agent...")
    
    wrapper = MyCustomAgent(model_name=model_name, **kwargs)
    
    # Extract the internal ToolCallingAgent
    internal_agent = wrapper.agent
    
    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper
    
    logger.info("My custom agent created successfully")
    return internal_agent
```

---

## Step 4: Testing Your Implementation

### Test the Tracking

1. **Create and test your agent:**
```python
# Test your agent
from your_module import create_my_custom_agent

agent = create_my_custom_agent()
result = agent.run("Test task for my custom agent")
print(result)
```

2. **Check the logs:**
```bash
# Check if your agent's log file was created
ls workshop_logs/agents/

# Should now include: my_custom_agent_traces.jsonl

# View your agent's activities
cat workshop_logs/agents/my_custom_agent_traces.jsonl
```

3. **Verify log entries:**
```json
{
  "timestamp": "2025-07-03T10:30:15.123456",
  "session_id": "session_20250703_103000",
  "agent_name": "my_custom_agent",
  "step_number": 1,
  "task_description": "Test task for my custom agent",
  "status": "completed",
  "response_content": "Task completed successfully...",
  "duration_seconds": 2.45
}
```

---

## Step 5: Integration with Workshop Analysis

Once your agent has tracking, it automatically integrates with all workshop tools:

### Appears in Workshop Reports
```bash
# Your agent will be included in reports
workshop-report

# Output will include:
# - my_custom_agent: X interactions
# - Average response time: X.X seconds
# - Success rate: XX%
```

### Included in Daily Logs
```bash
# Combined with all other agents
cat workshop_logs/daily/2025-07-03_traces.jsonl | grep "my_custom_agent"
```

### Session Analysis
```python
# Your agent data in session files
import json
with open('workshop_logs/sessions/session_20250703_103000.json') as f:
    session = json.load(f)
    agents_used = session['metadata']['agents_used']
    # Will include "my_custom_agent"
```

---

## Advanced Customization

### Adding Tool Call Tracking

If your agent uses specific tools, track them:

```python
# In your run method, after getting result:
tools_used = getattr(result, 'tool_calls', [])  # If available
log_agent_interaction(
    agent_name="my_custom_agent",
    step_number=self.step_counter,
    task_description=task,
    status="completed",
    tool_calls=tools_used,  # Add this line
    response_content=result_str,
    duration_seconds=duration
)
```

### Custom Status Types

Use different status values for complex workflows:

```python
# For multi-step agents
log_agent_interaction(status="in_progress")  # During processing
log_agent_interaction(status="validating")  # During validation
log_agent_interaction(status="completed")   # When finished
```

### Memory Size Tracking

Track agent memory usage:

```python
# Calculate memory size if available
memory_size = len(self.agent.memory.steps) if hasattr(self.agent, 'memory') else 0

log_agent_interaction(
    agent_name="my_custom_agent",
    step_number=self.step_counter,
    memory_size=memory_size,  # Add this
    # ... other parameters
)
```

---

## Best Practices

### Naming Conventions
- Use `snake_case` for agent names: `my_custom_agent`
- Keep names descriptive but concise
- Avoid spaces or special characters

### Task Description Handling
- Always truncate long task descriptions to 200 chars
- Include `...` when truncated for clarity
- Preserve essential context in the truncation

### Error Handling
- Always re-raise exceptions after logging
- Include full error message in `error_message` field
- Log duration even for failed tasks

### Performance Considerations
- Time tracking adds minimal overhead (~0.001 seconds)
- Truncate large response content to avoid log bloat
- Use appropriate log levels (info for start/success, error for failures)

---

## Troubleshooting

### Problem: No log files created
**Solution:** Check import path and agent name:
```python
# Verify import works
from ..monitoring.trace_logger import log_agent_interaction

# Verify agent name is unique and valid
agent_name = "my_custom_agent"  # No spaces, no special chars
```

### Problem: Logs appear but agent not in reports  
**Solution:** Ensure agent name is consistent:
```python
# Use same name in all log_agent_interaction calls
agent_name = "my_custom_agent"  # Always the same
```

### Problem: Duration always zero
**Solution:** Check timing logic:
```python
import time
start_time = time.time()  # Before work
# ... do work ...
duration = time.time() - start_time  # After work
```

### Problem: Too much log data
**Solution:** Truncate appropriately:
```python
# Truncate task description
task_desc = task[:200] + "..." if len(task) > 200 else task

# Truncate response content  
response = response[:500] + "..." if len(response) > 500 else response
```

---

## Template for Quick Implementation

Copy this template and replace the placeholders:

```python
# STEP 1: Add import
from ..monitoring.trace_logger import log_agent_interaction

class YOUR_AGENT_CLASS:
    def __init__(self, ...):
        # STEP 2: Add counter
        self.step_counter = 0
        # ... your init code ...

    def run(self, task: str) -> Any:
        # STEP 3: Add logging wrapper
        self.step_counter += 1
        import time
        start_time = time.time()
        
        log_agent_interaction(
            agent_name="YOUR_AGENT_NAME",  # Change this
            step_number=self.step_counter,
            task_description=task[:200] + "..." if len(task) > 200 else task,
            status="started"
        )

        try:
            # YOUR EXISTING CODE HERE
            result = YOUR_EXISTING_CODE
            
            # Log success
            duration = time.time() - start_time
            result_str = str(result) if result else ""
            log_agent_interaction(
                agent_name="YOUR_AGENT_NAME",  # Change this
                step_number=self.step_counter,
                task_description=task[:200] + "..." if len(task) > 200 else task,
                status="completed",
                response_content=result_str[:500] + "..." if len(result_str) > 500 else result_str,
                duration_seconds=duration
            )
            return result
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            log_agent_interaction(
                agent_name="YOUR_AGENT_NAME",  # Change this
                step_number=self.step_counter,
                task_description=task[:200] + "..." if len(task) > 200 else task,
                status="failed",
                error_message=str(e),
                duration_seconds=duration
            )
            raise
```

**Replacement Checklist:**
- [ ] `YOUR_AGENT_CLASS` → Your agent class name
- [ ] `YOUR_AGENT_NAME` → Your agent identifier (3 places)
- [ ] `YOUR_EXISTING_CODE` → Your actual agent logic

---

## Conclusion

Adding workshop tracking to any agent requires just:

1. **One import** → `from ..monitoring.trace_logger import log_agent_interaction`
2. **One variable** → `self.step_counter = 0`
3. **One wrapper** → Around your `run` method

This modular approach ensures:
- ✅ **Consistent tracking** across all agents
- ✅ **Minimal code changes** to existing agents  
- ✅ **Automatic integration** with workshop analysis tools
- ✅ **Standardized log format** for easy analysis

Your agent will immediately appear in workshop reports, daily logs, and session analysis alongside the existing geometry_agent and rational_agent, providing complete visibility into your agent's performance and usage patterns.

---

## Quick Reference

### Essential Code Snippets

**Import:**
```python
from ..monitoring.trace_logger import log_agent_interaction
```

**Initialize:**
```python
self.step_counter = 0
```

**Log Start:**
```python
log_agent_interaction(agent_name="my_agent", step_number=self.step_counter, 
                     task_description=task, status="started")
```

**Log Success:**
```python
log_agent_interaction(agent_name="my_agent", step_number=self.step_counter,
                     task_description=task, status="completed", 
                     response_content=result, duration_seconds=duration)
```

**Log Error:**
```python
log_agent_interaction(agent_name="my_agent", step_number=self.step_counter,
                     task_description=task, status="failed",
                     error_message=str(e), duration_seconds=duration)
```

### Files Created
- `workshop_logs/agents/YOUR_AGENT_NAME_traces.jsonl`
- Entries in `workshop_logs/daily/YYYY-MM-DD_traces.jsonl`
- Inclusion in `workshop_logs/sessions/session_*.json`

This tutorial provides everything needed to add comprehensive workshop tracking to any new agent using the same proven pattern as the existing geometry and rational agents.