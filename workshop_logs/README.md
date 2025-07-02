# Workshop Logging System

This directory contains comprehensive logs of all workshop sessions for academic analysis and research documentation.

## Directory Structure

```
workshop_logs/
├── README.md                    # This file
├── sessions/                    # Individual session files
│   ├── session_20250702_143000.json
│   └── session_20250702_150000.json
├── daily/                       # Daily aggregated logs
│   ├── 2025-07-02_traces.jsonl  # Raw trace data (JSONL format)
│   └── 2025-07-02_summary.txt   # Human-readable summary
├── agents/                      # Agent-specific logs
│   ├── triage_agent_traces.jsonl
│   ├── geometry_agent_traces.jsonl
│   └── rational_agent_traces.jsonl
├── workshop_analysis.csv        # CSV for statistical analysis
└── workshop_report.md          # Generated analysis report
```

## File Formats

### 1. Session Files (`sessions/*.json`)
Complete session data with metadata and all traces:
```json
{
  "metadata": {
    "session_id": "session_20250702_143000",
    "start_time": "2025-07-02T14:30:00",
    "end_time": "2025-07-02T15:45:00",
    "participant_id": "student_001",
    "workshop_group": "group_a",
    "total_interactions": 25,
    "agents_used": ["triage_agent", "geometry_agent"],
    "session_notes": "First-time user, struggled with complex geometries"
  },
  "traces": [...]
}
```

### 2. Trace Data (`*.jsonl`)
Each line is a JSON trace record:
```json
{
  "timestamp": "2025-07-02T14:30:15",
  "session_id": "session_20250702_143000",
  "agent_name": "triage_agent",
  "step_number": 1,
  "task_description": "Create a simple bridge structure",
  "status": "completed",
  "tool_calls": ["geometry_agent", "final_answer"],
  "response_content": "Bridge structure created successfully...",
  "duration_seconds": 2.34,
  "token_usage": {"input_tokens": 150, "output_tokens": 75, "total_tokens": 225},
  "memory_size": 3
}
```

### 3. Analysis CSV (`workshop_analysis.csv`)
Statistical data for easy analysis:
```csv
session_id,start_time,end_time,participant_id,workshop_group,total_interactions,agents_used,avg_response_time,errors_count,session_notes
session_20250702_143000,2025-07-02T14:30:00,2025-07-02T15:45:00,student_001,group_a,25,"triage_agent;geometry_agent",2.1,3,"First-time user"
```

## Workshop Commands

### During Workshop Session
```bash
# Check current session status
status

# Finalize session with participant info
workshop-finalize

# Generate analysis report
workshop-report
```

### Post-Workshop Analysis
```python
import json
import pandas as pd

# Load session data
with open('sessions/session_20250702_143000.json') as f:
    session = json.load(f)

# Load CSV for statistical analysis
df = pd.read_csv('workshop_analysis.csv')
print(df.describe())
```

## Research Metrics Captured

### Agent Performance
- Response times per agent
- Tool usage patterns
- Error rates and types
- Memory utilization

### User Interaction Patterns
- Session duration
- Command frequency
- Agent delegation patterns
- Task complexity progression

### Workshop Effectiveness
- Learning curve analysis
- Common error patterns
- Feature usage statistics
- Group performance comparison

## Privacy and Ethics

- Participant IDs are optional and can be anonymized
- Session notes should not contain personal information
- All logs are stored locally (no external transmission)
- Participants should consent to data collection for research

## Analysis Tools

### Quick Statistics
```bash
# Count total sessions
ls sessions/*.json | wc -l

# Get session durations
grep "total_interactions" workshop_analysis.csv

# Count agent usage
grep -o "geometry_agent" daily/*.jsonl | wc -l
```

### Python Analysis
```python
import json
from pathlib import Path

# Analyze all sessions
sessions_dir = Path("sessions")
for session_file in sessions_dir.glob("*.json"):
    with session_file.open() as f:
        data = json.load(f)
        print(f"Session: {data['metadata']['session_id']}")
        print(f"Interactions: {data['metadata']['total_interactions']}")
        print(f"Agents: {', '.join(data['metadata']['agents_used'])}")
```

## Academic Usage

This logging system supports:

1. **Quantitative Analysis**: Response times, success rates, usage patterns
2. **Qualitative Analysis**: Session notes, error patterns, user feedback
3. **Comparative Studies**: Group performance, feature effectiveness
4. **Longitudinal Analysis**: Learning progression over time
5. **System Evaluation**: Agent performance, tool effectiveness

## Data Export

For academic papers, export data using:
```bash
# Export to CSV for statistical software
python -c "
import json
import csv
from pathlib import Path

# Combine all traces into CSV
traces = []
for f in Path('sessions').glob('*.json'):
    with f.open() as file:
        data = json.load(file)
        traces.extend(data['traces'])

with open('all_traces.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=traces[0].keys())
    writer.writeheader()
    writer.writerows(traces)
"
```

## Troubleshooting

- **Missing logs**: Check that monitoring is enabled (`--monitoring` flag)
- **Empty sessions**: Ensure `workshop-finalize` is called
- **Large files**: JSONL files can be processed in chunks for big datasets
- **Analysis errors**: Validate JSON format with `jq` or Python json module