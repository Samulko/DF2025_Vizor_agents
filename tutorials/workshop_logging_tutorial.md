# Workshop Logging Tutorial: Tracking Agent Conversations with OpenTelemetry

This tutorial shows you how to automatically capture and analyze all agent interactions in your bridge design system, including conversations between agents themselves.

## Learning Objectives

By the end of this tutorial, you will:
- Understand how OpenTelemetry captures agent interactions automatically
- Know how to access and analyze workshop logs 
- Learn to track both user interactions and inter-agent conversations
- Be able to generate comprehensive workshop reports

## Prerequisites

- Basic understanding of the bridge design system
- System running with `start_TEAM.py` or with `--monitoring` flag
- Familiarity with JSON log formats

---

## Step 1: Understanding the Workshop Logging System

The bridge design system uses **OpenTelemetry instrumentation** to automatically capture all agent activities. This means:

✅ **Zero code changes needed** - Just run the system normally  
✅ **Automatic capture** - All agent conversations are logged  
✅ **Structured data** - Easy to analyze with tools  
✅ **Real-time logging** - See activities as they happen  

### What Gets Captured

**Triage Agent Activities:**
- User requests and responses
- Task delegation decisions
- Coordination between agents

**Geometry Agent Activities:**
- MCP tool calls to Grasshopper
- Component creation and modification
- 3D geometry operations

**Rational Agent Activities:**
- Element level validation
- Direction vector corrections
- Engineering analysis

**Inter-Agent Conversations:**
- Task delegation from triage → sub-agents
- Results returned from sub-agents → triage
- Context sharing between agents

---

## Step 2: Accessing Workshop Logs

### Log Directory Structure

```
workshop_logs/
├── README.md                    # Documentation
├── agents/                      # Agent-specific logs
│   ├── triage_agent_traces.jsonl
│   ├── geometry_agent_traces.jsonl
│   └── rational_agent_traces.jsonl
├── daily/                       # Daily aggregated logs
│   ├── 2025-07-03_traces.jsonl  # All agents combined
│   └── 2025-07-03_summary.txt   # Human-readable summary
└── sessions/                    # Complete session files
    └── session_20250703_141530.json
```

### Reading Agent-Specific Logs

**Individual Agent Activity:**
```bash
# View geometry agent activities
cat workshop_logs/agents/geometry_agent_traces.jsonl

# View rational agent activities  
cat workshop_logs/agents/rational_agent_traces.jsonl

# View triage agent activities
cat workshop_logs/agents/triage_agent_traces.jsonl
```

**Combined Daily View:**
```bash
# All agent activities in chronological order
cat workshop_logs/daily/2025-07-03_traces.jsonl

# Human-readable summary
cat workshop_logs/daily/2025-07-03_summary.txt
```

---

## Step 3: Understanding Log Format

Each log entry contains:

```json
{
  "timestamp": "2025-07-03T04:14:04.062442",
  "session_id": "session_20250703_041404", 
  "agent_name": "geometry_agent",
  "step_number": 1,
  "task_description": "Report the number of components currently in Grasshopper",
  "status": "completed",
  "tool_calls": [],
  "response_content": "The number of components currently in Grasshopper is 4...",
  "error_message": null,
  "duration_seconds": 10.636,
  "token_usage": null,
  "memory_size": 0
}
```

### Key Fields Explained

- **agent_name**: Which agent performed this action
- **step_number**: Sequence of actions within this agent
- **status**: `started`, `completed`, or `failed`
- **task_description**: What the agent was asked to do
- **response_content**: What the agent produced
- **duration_seconds**: How long the action took

---

## Step 4: Analyzing Inter-Agent Conversations

### Example: Tracking a Complete Workflow

When a user asks: *"Check if all bridge elements are properly horizontal"*

**Step 1: Triage Receives Request**
```json
{
  "agent_name": "triage_agent",
  "task_description": "Check if all bridge elements are properly horizontal",
  "status": "completed",
  "response_content": "I'll check the horizontal alignment using specialized agents..."
}
```

**Step 2: Triage Delegates to Rational Agent**
```json
{
  "agent_name": "rational_agent", 
  "task_description": "Check if all the bridge elements are properly level (horizontal)...",
  "status": "started"
}
```

**Step 3: Rational Agent Executes Task**
```json
{
  "agent_name": "rational_agent",
  "status": "completed",
  "response_content": "Called Tool: 'get_python3_script' with arguments...",
  "duration_seconds": 26.19
}
```

**Step 4: Triage Coordinates Results**
The triage agent receives the rational agent's analysis and provides a unified response to the user.

### Tracking Tool Usage

Look for `tool_calls` fields to see which tools agents used:
- `get_geometry_agent_components` - Reading Grasshopper components
- `get_python3_script` - Examining component code
- `edit_python3_script` - Modifying components

---

## Step 5: Using Built-in Analysis Tools

### Workshop Session Commands

During a live session, use these commands:

```bash
# Finalize current session with metadata
workshop-finalize

# Generate comprehensive analysis report
workshop-report
```

### Session Finalization

When you run `workshop-finalize`, you'll be prompted for:
- **Participant ID**: Student or researcher identifier
- **Workshop Group**: Class section or research group  
- **Session Notes**: Free-form observations

This creates a complete session file in `workshop_logs/sessions/`.

### Workshop Report Generation

The `workshop-report` command creates:
- Session overview with statistics
- Agent usage patterns
- Performance metrics
- Error analysis

---

## Step 6: Advanced Analysis with Python

### Loading and Analyzing Logs

```python
import json
import pandas as pd
from pathlib import Path

# Load all traces from daily log
traces = []
with open('workshop_logs/daily/2025-07-03_traces.jsonl') as f:
    for line in f:
        traces.append(json.loads(line))

# Convert to DataFrame for analysis
df = pd.DataFrame(traces)

# Agent activity summary
activity_summary = df.groupby('agent_name').agg({
    'step_number': 'count',
    'duration_seconds': ['mean', 'sum'],
    'status': lambda x: (x == 'completed').sum()
}).round(2)

print("Agent Activity Summary:")
print(activity_summary)
```

### Finding Inter-Agent Conversations

```python
# Find sequences where triage delegates to sub-agents
triage_tasks = df[df.agent_name == 'triage_agent']
sub_agent_tasks = df[df.agent_name.isin(['geometry_agent', 'rational_agent'])]

# Match delegations by session_id and timing
for _, triage_task in triage_tasks.iterrows():
    session = triage_task.session_id
    triage_time = pd.to_datetime(triage_task.timestamp)
    
    # Find sub-agent tasks in same session after triage task
    related_tasks = sub_agent_tasks[
        (sub_agent_tasks.session_id == session) & 
        (pd.to_datetime(sub_agent_tasks.timestamp) > triage_time)
    ]
    
    if not related_tasks.empty:
        print(f"\nTriage task: {triage_task.task_description[:50]}...")
        for _, subtask in related_tasks.iterrows():
            print(f"  → {subtask.agent_name}: {subtask.task_description[:50]}...")
```

### Performance Analysis

```python
# Agent performance metrics
performance = df.groupby('agent_name').agg({
    'duration_seconds': ['count', 'mean', 'std', 'min', 'max'],
    'status': lambda x: (x == 'failed').sum()
}).round(2)

performance.columns = ['total_tasks', 'avg_duration', 'duration_std', 
                      'min_duration', 'max_duration', 'failed_tasks']

print("Agent Performance Metrics:")
print(performance)
```

---

## Step 7: Creating Custom Analysis Scripts

### Workshop Session Analyzer

```python
#!/usr/bin/env python3
"""
Custom workshop session analyzer.
Usage: python analyze_session.py session_20250703_141530
"""

import sys
import json
from pathlib import Path

def analyze_session(session_id):
    """Analyze a specific workshop session."""
    
    # Load session file
    session_file = Path(f"workshop_logs/sessions/{session_id}.json")
    if not session_file.exists():
        print(f"Session file not found: {session_file}")
        return
    
    with session_file.open() as f:
        session_data = json.load(f)
    
    metadata = session_data["metadata"]
    traces = session_data["traces"]
    
    print(f"Session Analysis: {session_id}")
    print("=" * 50)
    print(f"Participant: {metadata.get('participant_id', 'Unknown')}")
    print(f"Duration: {metadata['start_time']} to {metadata['end_time']}")
    print(f"Total Interactions: {len(traces)}")
    print(f"Agents Used: {', '.join(metadata['agents_used'])}")
    
    # Agent breakdown
    agent_counts = {}
    for trace in traces:
        agent = trace["agent_name"]
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    
    print("\nAgent Activity Breakdown:")
    for agent, count in agent_counts.items():
        print(f"  {agent}: {count} actions")
    
    # Error analysis
    errors = [t for t in traces if t["error_message"]]
    if errors:
        print(f"\nErrors Encountered: {len(errors)}")
        for error in errors:
            print(f"  {error['agent_name']}: {error['error_message']}")
    
    # Performance summary
    durations = [t["duration_seconds"] for t in traces if t["duration_seconds"]]
    if durations:
        avg_duration = sum(durations) / len(durations)
        print(f"\nAverage Task Duration: {avg_duration:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_session.py <session_id>")
        sys.exit(1)
    
    analyze_session(sys.argv[1])
```

---

## Step 8: Best Practices for Workshop Analysis

### During Workshops

1. **Start each session cleanly**: Use `reset` or `hardreset` to clear previous state
2. **Document context**: Use meaningful session notes in `workshop-finalize`  
3. **Test specific scenarios**: Design tasks that exercise different agent combinations
4. **Monitor in real-time**: Watch log files during sessions to catch issues

### After Workshops

1. **Generate reports immediately**: Run `workshop-report` while session is fresh
2. **Export for analysis**: Convert JSONL to CSV for statistical software
3. **Archive sessions**: Back up session files for longitudinal studies
4. **Share insights**: Use analysis to improve agent design

### Common Analysis Patterns

**Agent Utilization:**
```bash
# Count tasks per agent
grep -o '"agent_name":"[^"]*"' workshop_logs/daily/*.jsonl | sort | uniq -c
```

**Error Patterns:**
```bash
# Find all errors
grep '"error_message":"[^n]' workshop_logs/daily/*.jsonl
```

**Performance Trends:**
```bash
# Extract durations
grep -o '"duration_seconds":[0-9.]*' workshop_logs/daily/*.jsonl
```

---

## Step 9: Troubleshooting Common Issues

### No Logs Being Generated

**Problem**: Empty `workshop_logs/agents/` directory

**Solution**: Ensure monitoring is enabled:
```bash
# Check if system started with monitoring
grep "Workshop trace logging enabled" logs/bridge_design_system.log

# Or restart with explicit monitoring
uv run python -m bridge_design_system.main --interactive --monitoring
```

### Missing Agent Traces

**Problem**: Only `triage_agent_traces.jsonl` exists

**Solution**: This indicates agents aren't being delegated tasks. Try:
- Ask questions that require geometry operations
- Request level validation tasks  
- Use commands that trigger MCP tool usage

### Incomplete Sessions

**Problem**: Sessions missing in `workshop_logs/sessions/`

**Solution**: Always run `workshop-finalize` at end of session:
```bash
# In the interactive system
workshop-finalize
```

### Log File Too Large

**Problem**: Daily logs become unwieldy

**Solution**: Use session-based analysis:
```python
# Process logs in chunks
import json
import itertools

def process_large_log(filename, chunk_size=1000):
    with open(filename) as f:
        while True:
            chunk = list(itertools.islice(f, chunk_size))
            if not chunk:
                break
            # Process chunk
            for line in chunk:
                trace = json.loads(line)
                # Analyze trace...
```

---

## Step 10: Research Applications

### Educational Assessment

**Learning Progression Analysis:**
Track how students improve their problem-solving approaches:
- Early sessions: More triage agent dependency
- Later sessions: More direct sub-agent usage
- Advanced: Complex multi-agent coordination

**Common Mistake Patterns:**
Identify frequent error types for curriculum improvement:
- MCP connection failures
- Incorrect tool parameter usage
- Agent delegation confusion

### System Performance Research

**Agent Efficiency Studies:**
Compare agent performance across different tasks:
- Geometry vs. analysis tasks
- Simple vs. complex operations
- Individual vs. collaborative work

**Tool Usage Analytics:**
Understand which MCP tools are most/least effective:
- Success rates per tool
- Common parameter patterns
- Error-prone operations

### Human-AI Interaction Research

**Delegation Patterns:**
Study how users naturally interact with multi-agent systems:
- Direct requests vs. conversational approaches
- Preference for specific agents
- Task complexity effects

**Trust and Understanding:**
Analyze user confidence in agent capabilities:
- Verification behaviors
- Error recovery patterns
- Learning curve analysis

---

## Conclusion

The OpenTelemetry-based workshop logging system provides comprehensive visibility into agent activities without requiring any code modifications. By understanding the log structure and using the analysis tools, you can:

✅ **Track complete workflows** from user request to final response  
✅ **Analyze inter-agent conversations** and coordination patterns  
✅ **Identify performance bottlenecks** and optimization opportunities  
✅ **Conduct educational research** on human-AI interaction  
✅ **Generate comprehensive reports** for academic analysis  

The automated logging approach is much more reliable than manual instrumentation and captures nuances of agent behavior that would be difficult to track otherwise.

---

## Quick Reference

### Essential Commands
```bash
# Start system with logging
uv run python start_TEAM.py

# View real-time agent activity
tail -f workshop_logs/daily/$(date +%Y-%m-%d)_traces.jsonl

# Finalize session
workshop-finalize

# Generate report
workshop-report

# Analyze specific agent
grep "geometry_agent" workshop_logs/daily/*.jsonl
```

### Important Files
- `workshop_logs/agents/*.jsonl` - Individual agent activities
- `workshop_logs/daily/*.jsonl` - Combined chronological logs
- `workshop_logs/sessions/*.json` - Complete session data
- `workshop_logs/workshop_analysis.csv` - Statistical summary

### Analysis Tips
- Use `jq` for JSON manipulation: `cat traces.jsonl | jq '.agent_name'`
- Import to pandas for statistical analysis
- Track session_id to follow complete workflows
- Monitor duration_seconds for performance analysis
- Check error_message fields for failure patterns

This tutorial provides the foundation for comprehensive workshop analysis using the built-in OpenTelemetry instrumentation, enabling both real-time monitoring and post-session research without requiring any agent modifications.