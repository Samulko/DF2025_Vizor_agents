# Automatic Agent Tracking: Zero-Code Workshop Logging

This tutorial explains how agent tracking works automatically in the bridge design system and when you need to add manual tracking.

## TL;DR - Most Students Need Zero Code

**If your agent integrates with the triage system (recommended), tracking is 100% automatic.** No code changes needed!

---

## How Automatic Tracking Works

### 1. OpenTelemetry Instrumentation (Built-in)

When you run `start_TEAM.py`, it automatically:
- ✅ Sets `OTEL_BACKEND=phoenix` 
- ✅ Enables smolagents instrumentation
- ✅ Captures all agent interactions
- ✅ Sends traces to Phoenix dashboard at http://localhost:6006

### 2. Workshop Logging (Built-in) 

The system automatically:
- ✅ Creates `workshop_logs/` directory structure
- ✅ Generates agent-specific trace files
- ✅ Aggregates daily logs  
- ✅ Enables `workshop-finalize` and `workshop-report` commands

### 3. Managed Agents Integration (Built-in)

Any agent in the triage system's `managed_agents` list gets:
- ✅ Automatic task delegation logging
- ✅ Response tracking
- ✅ Error handling
- ✅ Performance metrics

---

## For Students: Integration Approaches

### Approach 1: Managed Agent Integration (Recommended)

**What this means:** Your agent becomes part of the triage system and gets called automatically.

**Code needed:** Zero tracking code! Just follow smolagents patterns.

**Example:**
```python
# Your agent (no tracking code needed)
class MyBridgeAnalyzer:
    def __init__(self, model_name="my_analyzer"):
        self.name = "bridge_analyzer" 
        self.description = "Analyzes bridge structural properties"
        
        # Standard smolagents setup
        self.agent = ToolCallingAgent(
            tools=[],  # Your tools
            model=ModelProvider.get_model(model_name),
            name="bridge_analyzer",
            description=self.description
        )
    
    def run(self, task: str):
        """No logging code needed - happens automatically!"""
        return self.agent.run(task)

# Factory function (also no tracking code)
def create_bridge_analyzer(**kwargs):
    wrapper = MyBridgeAnalyzer(**kwargs)
    return wrapper.agent  # Return ToolCallingAgent for managed_agents
```

**Integration:** Add to triage system's managed_agents list:
```python
# In triage_agent_smolagents.py
from .my_bridge_analyzer import create_bridge_analyzer

# Create agent
bridge_analyzer = create_bridge_analyzer()

# Add to managed_agents
managed_agents=[geometry_agent, rational_agent, bridge_analyzer]
```

**Result:** 
- ✅ Automatic task delegation from triage
- ✅ Workshop logs created: `workshop_logs/agents/bridge_analyzer_traces.jsonl`
- ✅ Phoenix dashboard integration
- ✅ Included in workshop reports

### Approach 2: Standalone Agent (Manual Tracking)

**What this means:** Your agent runs independently, outside the triage system.

**Code needed:** 3 lines for workshop tracking (optional).

**When to use:** Testing, research, or specialized workflows.

**Example:**
```python
# Optional manual tracking for standalone agents
from ..monitoring.trace_logger import log_agent_interaction  # 1 line

class MyStandaloneAgent:
    def __init__(self):
        self.step_counter = 0  # 1 line
        # ... your agent setup
    
    def run(self, task: str):
        # Optional manual tracking
        self.step_counter += 1
        log_agent_interaction(
            agent_name="my_standalone_agent",
            step_number=self.step_counter, 
            task_description=task,
            status="completed"
        )  # 1 code block
        
        return self.agent.run(task)
```

---

## What Students See in Practice

### Running `start_TEAM.py`:

```bash
$ python start_TEAM.py
============================================================
🌉 Bridge Design System - TEAM Launch  
============================================================
🚀 Starting Phoenix Server...
✅ Phoenix Server started (PID: 12345)
🚀 Starting LCARS Monitoring...
✅ LCARS Monitoring started (PID: 12346)
============================================================
📊 Phoenix UI:     http://localhost:6006  ← OpenTelemetry dashboard
🖥️  LCARS Monitor:  http://localhost:5000  ← Real-time monitoring
============================================================
```

### Automatic Workshop Logs:

```bash
workshop_logs/
├── agents/
│   ├── triage_agent_traces.jsonl      ← Automatic
│   ├── geometry_agent_traces.jsonl    ← Automatic  
│   ├── rational_agent_traces.jsonl    ← Automatic
│   └── your_agent_traces.jsonl        ← Automatic (if managed agent)
└── daily/
    └── 2025-07-03_traces.jsonl         ← All agents combined
```

### Example Log Entry (Automatic):

```json
{
  "timestamp": "2025-07-03T10:30:15.123456",
  "session_id": "session_20250703_103000", 
  "agent_name": "your_agent",
  "step_number": 1,
  "task_description": "Analyze bridge load distribution",
  "status": "completed",
  "response_content": "Load analysis complete: 4 critical points identified...",
  "duration_seconds": 3.45
}
```

### Workshop Commands (Available Immediately):

```bash
# During session
Designer> workshop-finalize  # Save session with metadata
Designer> workshop-report    # Generate analysis report
```

---

## Technical Details: How It Works Under the Hood

### OpenTelemetry Auto-Instrumentation

The system uses `SmolagentsInstrumentor` which automatically:
1. **Hooks into smolagents framework** at runtime
2. **Captures all agent.run() calls** without code changes
3. **Tracks tool usage and responses** automatically  
4. **Sends traces to Phoenix** for visualization

### Workshop Logging Bridge

The `trace_logger.py` system:
1. **Receives OpenTelemetry data** automatically
2. **Converts to workshop format** (JSON lines)
3. **Organizes by agent and date** for analysis
4. **Integrates with session management** tools

### Managed Agents Pattern

The smolagents framework:
1. **Automatically delegates tasks** to managed agents
2. **Captures delegation and responses** in traces
3. **Maintains context across agents** seamlessly
4. **Provides unified error handling** and logging

---

## Verification: Is My Agent Being Tracked?

### Quick Check:
```bash
# Run your agent through the system
Designer> ask my agent to analyze something

# Check if log file created
ls workshop_logs/agents/your_agent_traces.jsonl

# View traces
cat workshop_logs/agents/your_agent_traces.jsonl
```

### What You Should See:
- ✅ Log file exists with your agent's name
- ✅ JSON entries with timestamps and task descriptions
- ✅ OpenTelemetry traces in Phoenix dashboard
- ✅ Agent listed in workshop reports

### If Nothing Appears:
1. **Check agent name**: Must be consistent and valid
2. **Verify integration**: Is agent in managed_agents list?
3. **Test delegation**: Does triage actually call your agent?
4. **Check logs**: Any errors in system logs?

---

## Best Practices for Students

### For Managed Agents (Recommended):

✅ **Do:**
- Follow standard smolagents patterns
- Use descriptive agent names  
- Test integration with triage system
- Let OpenTelemetry handle tracking automatically

❌ **Don't:**
- Add manual tracking code
- Duplicate logging functionality
- Modify core framework code

### For Standalone Agents (Advanced):

✅ **Do:**
- Add minimal manual tracking if needed
- Use consistent agent naming
- Test tracking independently

❌ **Don't:**
- Over-engineer tracking systems
- Duplicate automatic functionality
- Break compatibility with managed agents

---

## Migration Guide: If You Added Manual Tracking

If you previously added manual tracking code, you can safely remove it:

```python
# REMOVE these lines (now redundant):
from ..monitoring.trace_logger import log_agent_interaction
self.step_counter = 0
log_agent_interaction(...)  # All these calls

# KEEP this (your actual agent logic):
def run(self, task: str):
    return self.agent.run(task)  # This gets tracked automatically
```

**Why?** The OpenTelemetry instrumentation captures everything automatically at a lower level.

---

## Summary

### For 90% of Students:
**Zero tracking code needed.** Just:
1. Create agent following smolagents patterns
2. Add to triage system managed_agents  
3. Run through `start_TEAM.py`
4. Workshop logs appear automatically

### For Advanced Use Cases:
Manual tracking available with 3 lines of code for standalone agents.

### Key Insight:
The bridge design system provides **automatic, comprehensive tracking** for all agents integrated into the triage system. Students can focus on building agent functionality while the system handles all logging, monitoring, and analysis automatically.

---

## Quick Reference

### Zero-Code Tracking Checklist:
- [ ] Agent follows smolagents ToolCallingAgent pattern
- [ ] Agent added to triage system managed_agents list
- [ ] System started with `start_TEAM.py` 
- [ ] Workshop logs appear in `workshop_logs/agents/`

### Tracking Verification:
```bash
# Check automatic tracking is working
tail -f workshop_logs/daily/$(date +%Y-%m-%d)_traces.jsonl
```

### Dashboard Access:
- Phoenix (OpenTelemetry): http://localhost:6006
- LCARS (Real-time): http://localhost:5000

This automatic approach eliminates the need for students to write any tracking code while providing comprehensive workshop analytics and research data.