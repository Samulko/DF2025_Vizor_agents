# LCARS Agent Monitoring System

LCARS (Star Trek-styled) monitoring interface for tracking AI agent status and task history in real-time.

## Components

- **`server.py`** - FastAPI server with WebSocket support
- **`status.html`** - LCARS web interface with JavaScript  
- **`agent_monitor.py`** - Core monitoring logic and callbacks
- **`lcars_interface.py`** - Main entry point

## Adding a New Agent

### 1. Register Agent (server.py)
```python
# Around line 37 - uncomment and modify the template
status_tracker.register_agent("your_agent_name", "AgentType")
```
- **CodeAgent**: For code-executing agents (triage_agent, syslogic_agent)
- **ToolCallingAgent**: For tool-using agents (geometry_agent)

Update agent count in print statement.

### 2. Add CSS Colors (status.html)
```css
/* Around line 218 - uncomment and modify the template */
.agent-card[data-agent="your_agent_name"] .lcars-main-panel {
    background: var(--lcars-blue);
}
.agent-card[data-agent="your_agent_name"] .lcars-status-section {
    background: var(--lcars-blue);
}
```

**Available Colors:** `--lcars-blue`, `--lcars-pink`, `--lcars-yellow`  
**Used Colors:** orange (triage), red (geometry), purple (syslogic)

### 3. Update Agent Order (status.html)
```javascript
// Around line 893 - add to array
const agentOrder = ['triage_agent', 'geometry_agent', 'syslogic_agent', 'your_agent_name'];
```

### 4. Set Up Monitoring Callback
```python
from .monitoring.agent_monitor import create_remote_monitor_callback

monitoring_callback = create_remote_monitor_callback("your_agent_name")
```

### 5. Integrate with Agent
```python
# For smolagents
your_agent = YourAgentClass(
    step_callbacks=[monitoring_callback] if monitoring_callback else []
)

# For custom agents
if monitoring_callback:
    monitoring_callback(memory_step, agent)
```

## Agent Status Types

- `ready` → "STANDBY"
- `thinking` → "PROCESSING" 
- `working` → "ACTIVE"
- `delegating` → "COMMANDING"
- `connecting` → "INTERFACING"
- `validating` → "ANALYZING"
- `completed` → "COMPLETE"
- `error` → "ALERT"

## Task History Format

Use structured responses for proper task history:
```
### 1. Task outcome (short version):
[Brief summary]

### 2. Task outcome (extremely detailed version):
[Comprehensive details]

### 3. Additional context (if relevant):
[Additional notes]
```

## Testing

1. Start monitoring: `uv run python -m bridge_design_system.monitoring.lcars_interface`
2. Start agents: `uv run python -m bridge_design_system.main --interactive`
3. Visit: http://localhost:5000

## Troubleshooting

- **Agent missing**: Check registration in server.py and name consistency
- **Wrong colors**: Verify CSS rules and data-agent attributes
- **No status updates**: Check callback integration and WebSocket connection
- **No task history**: Verify structured response format and completion detection