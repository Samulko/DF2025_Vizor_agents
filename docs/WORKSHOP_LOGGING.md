# Workshop Logging for Student Agents

Add comprehensive logging to any smolagents agent with just **1 line of code**!

## Quick Start

```python
from bridge_design_system.monitoring.workshop_logging import add_workshop_logging

# Create your agent normally
agent = CodeAgent(tools=[...], model=model, ...)

# Add workshop logging - just 1 line!
add_workshop_logging(agent, "my_agent_name")

# That's it! Now agent.run() automatically logs everything
```

## What Gets Logged

The workshop logging system automatically tracks:

- ✅ **Task Start/Completion**: When each task begins and ends
- ⏱️ **Execution Time**: How long each task takes
- 📝 **Task Descriptions**: What the agent was asked to do
- 💬 **Responses**: What the agent returned (truncated for readability)
- ❌ **Errors**: Any failures with full error messages
- 🔢 **Step Numbers**: Sequential numbering of agent interactions

## Where Logs Are Saved

All logs are automatically saved to the `workshop_logs/` directory:

```
workshop_logs/
├── agents/
│   ├── my_agent_name_traces.jsonl      # Agent-specific logs
│   ├── category_agent_traces.jsonl
│   └── geometry_agent_traces.jsonl
├── daily/
│   ├── 2025-07-03_traces.jsonl         # All agents for today
│   └── 2025-07-03_summary.txt          # Human-readable summary
├── sessions/
│   └── session_20250703_110600.json    # Complete session data
└── workshop_analysis.csv               # Statistics for analysis
```

## Complete Example

```python
#!/usr/bin/env python3
"""Example: My Custom Analysis Agent with Workshop Logging"""

from smolagents import CodeAgent, tool
from bridge_design_system.config.model_config import ModelProvider
from bridge_design_system.monitoring.workshop_logging import add_workshop_logging

@tool
def analyze_data(data: str) -> str:
    """Analyze some data and return insights."""
    return f"Analysis complete: Found {len(data)} characters"

def create_my_agent():
    """Create my custom agent."""
    model = ModelProvider.get_model("category")
    
    agent = CodeAgent(
        tools=[analyze_data],
        model=model,
        name="data_analyzer",
        description="Analyzes data and provides insights",
        max_steps=5
    )
    
    # Add workshop logging
    add_workshop_logging(agent, "data_analyzer")
    
    return agent

# Use the agent
agent = create_my_agent()
result = agent.run("Analyze this sample data: Hello World!")
print(result)

# Logs automatically saved to:
# workshop_logs/agents/data_analyzer_traces.jsonl
# workshop_logs/daily/2025-07-03_traces.jsonl
```

## Integration Patterns

### Pattern 1: Add to Factory Function (Recommended)

```python
def create_category_agent(model_name: str = None, monitoring_callback = None):
    agent = CodeAgent(...)
    
    # Add workshop logging - just 1 line!
    add_workshop_logging(agent, "category_agent")
    
    return agent
```

### Pattern 2: Add After Creation

```python
# Create agent normally
agent = create_some_agent()

# Add logging later
from bridge_design_system.monitoring.workshop_logging import add_workshop_logging
add_workshop_logging(agent, "my_agent")
```

### Pattern 3: Conditional Logging

```python
def create_agent(enable_logging: bool = True):
    agent = CodeAgent(...)
    
    if enable_logging:
        add_workshop_logging(agent, "conditional_agent")
    
    return agent
```

## Log File Formats

### JSONL Format (for analysis)
```json
{"timestamp": "2025-07-03T12:34:56", "agent_name": "my_agent", "step_number": 1, "status": "started", "task_description": "Calculate something..."}
{"timestamp": "2025-07-03T12:34:57", "agent_name": "my_agent", "step_number": 1, "status": "completed", "response_content": "Result: 42", "duration_seconds": 1.23}
```

### Human-Readable Summary
```
[2025-07-03T12:34:56] my_agent - Step 1
Status: started
Task: Calculate something...
Response: Result: 42
Duration: 1.23s
--------------------------------------------------------------------------------
```

## Benefits for Students

1. **Zero Overhead**: Just add one line of code
2. **Automatic**: No need to manually add logging calls
3. **Comprehensive**: Captures everything needed for analysis
4. **Multiple Formats**: Both machine-readable (JSON) and human-readable
5. **Workshop Ready**: Perfect for academic analysis and research

## Advanced Usage

### Remove Logging
```python
from bridge_design_system.monitoring.workshop_logging import remove_workshop_logging

# Remove logging if needed
remove_workshop_logging(agent)
```

### Check If Logging Enabled
```python
if hasattr(agent, '_workshop_logging_enabled'):
    print("Logging is enabled!")
```

## OpenTelemetry Integration

Workshop logging works **alongside** OpenTelemetry:

- **OpenTelemetry**: Provides distributed tracing across the entire system
- **Workshop Logging**: Provides detailed, workshop-specific analysis files

Both systems work together to give you complete observability into your agents' behavior.

## Example Output

After running a few tasks, you'll see files like:

```bash
$ ls workshop_logs/agents/
my_agent_traces.jsonl
category_agent_traces.jsonl

$ tail -1 workshop_logs/agents/my_agent_traces.jsonl
{"timestamp": "2025-07-03T12:34:57.123456", "session_id": "session_20250703_123456", "agent_name": "my_agent", "step_number": 3, "task_description": "Calculate the meaning of life", "status": "completed", "response_content": "42", "duration_seconds": 1.42}
```

Perfect for analyzing agent behavior, performance, and success rates in your workshop or research!