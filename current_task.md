# Current Task: Fix Geometry Agent STDIO Issues and Evaluate JSON Agent Alternative

## Problem Summary

The Geometry Agent STDIO implementation has critical issues with:
1. **Memory recall returning metadata-polluted values** causing component ID parsing failures
2. **Agent misunderstanding MCP tool return types** (JSON strings vs dictionaries)
3. **Duplicate component creation** due to improper error handling
4. **Code execution context confusion** in the smolagents framework

## Should We Use JSON Agent Instead of Code Agent?

### 🚨 **CRITICAL DISCOVERY: JSON Agents CAN Generate Dynamic Code!**

**Previous assumption was WRONG**: JSON agents are NOT limited to pre-made templates. The LLM dynamically generates the entire Python script as part of the JSON tool call!

**Example JSON Agent Flow:**
1. User: "Create a spiral in Grasshopper"
2. LLM generates: 
```json
{
  "name": "add_python3_script",
  "arguments": {
    "x": 100, "y": 100,
    "name": "Spiral Generator",
    "script": "import Rhino.Geometry as rg\nimport math\n\npoints = []\nfor i in range(100):\n    angle = i * 0.1\n    radius = i * 0.5\n    x = radius * math.cos(angle)\n    y = radius * math.sin(angle)\n    z = i * 0.2\n    points.append(rg.Point3d(x, y, z))\n\nspiral = rg.Curve.CreateInterpolatedCurve(points, 3)\na = spiral"
  }
}
```

### Analysis: JSON Agent (ToolCallingAgent) vs Code Agent

**JSON Agent PROS for this use case:**
- ✅ **Simpler data handling**: No Python execution context confusion
- ✅ **Native tool integration**: Perfect for calling external MCP tools
- ✅ **Clearer error boundaries**: Failures are at tool level, not code execution level
- ✅ **No JSON parsing issues**: Eliminates dictionary/string confusion entirely
- ✅ **Same code generation capability**: LLM generates Python scripts dynamically
- ✅ **Better suited for MCP**: Tools expect JSON calls, not Python execution

**JSON Agent CONS:**
- ❌ **No intermediate variables**: Can't store results between tool calls in Python
- ❌ **No complex control flow**: Can't do loops across multiple tool calls
- ❌ **Single tool per step**: Can't combine multiple operations in one execution

### Recommendation: **STRONGLY YES - JSON Agent is ideal**

For Geometry Agent tasks (MCP tool calls with dynamically generated scripts), JSON Agent is **significantly better** because:
1. **Eliminates current errors**: No more JSON parsing confusion
2. **Perfect MCP match**: MCP tools expect JSON calls
3. **Same script generation**: LLM creates complex Python scripts dynamically
4. **Simpler architecture**: Direct tool calls without Python execution layer
5. **Native smolagents pattern**: Official documentation shows MCP + JSON agent examples

## Immediate Tasks (Priority Order)

### Task 1: Create JSON Agent Prototype [CRITICAL - NEW PRIORITY]
**Goal**: Implement `ToolCallingAgent` for geometry operations to eliminate all current errors

**Why This Is Now Priority #1:**
- JSON agents eliminate the JSON parsing confusion that's causing all the errors
- Perfect match for MCP tool calling architecture
- Official smolagents pattern for MCP integration
- Same dynamic code generation capability as CodeAgent

**Steps**:
1. Create `geometry_agent_json.py` using `ToolCallingAgent`
2. Test with MCP tool calls for script generation
3. Compare error rates with current STDIO agent

### Task 2: Fix Memory Tool Return Format [HIGH]
**Problem**: `recall()` returns strings with metadata like `"270dc13e-b4fb-4802-8441-d4452a8196ae\n(Stored at: 2025-06-15T14:52:25.720584, retrieved in 0.2ms)"`

**Solution**: 
- Modify `recall()` in `memory_tools.py` to return only the value without metadata
- Add a `recall_with_metadata()` function if metadata is needed

**Note**: This is still needed for both agent types

### Task 3: Update System Prompts [HIGH]
**Goal**: Add explicit instructions for handling MCP responses

**For Code Agent (if kept)**:
```
IMPORTANT MCP Tool Instructions:
- ALL MCP tools return JSON strings that must be parsed with json.loads()
- ALWAYS check tool response success before using data
- Component IDs are UUIDs without any additional formatting
- If a tool call succeeds, do NOT retry the same operation
```

### Task 4: Implement Deduplication Logic [MEDIUM]
**Goal**: Prevent duplicate component creation

**Solution**:
- Before creating components, search memory for existing ones
- Add component existence checking in the agent logic

## Detailed Implementation Plan

### Phase 1: JSON Agent Prototype (Today)
1. **Create JSON agent prototype** (2 hours) - **NEW PRIORITY**
   - Implement `GeometryAgentJSON` using `ToolCallingAgent`
   - Test dynamic script generation with MCP tools
   - Validate no JSON parsing errors occur

2. **Fix memory recall format** (30 mins)
   - Update `recall()` to strip metadata
   - Test with JSON agent

### Phase 2: Evaluation (Tomorrow)
1. **Side-by-side testing** (2 hours)
   - Run same tasks on both agents
   - Measure error rates
   - Document pros/cons

2. **Decision point**
   - Choose JSON or Code agent based on results
   - Plan migration if needed

### Phase 3: Production Ready (This Week)
1. **Implement chosen solution**
2. **Update all system prompts**
3. **Add comprehensive error handling**
4. **Full integration testing**

## Success Criteria

- [ ] No more "Invalid component ID format" errors
- [ ] No duplicate component creation
- [ ] Clean component ID storage and retrieval
- [ ] Agent understands MCP tool responses correctly
- [ ] Error rate < 5% for standard operations

## Code Examples

### Memory Tool Fix
```python
# In memory_tools.py
@tool
def recall(category: str = None, key: str = None) -> str:
    """Retrieve information from memory without metadata."""
    memory = MemoryManager.get_instance()
    result = memory.recall(category, key)
    
    # Strip metadata if present
    if result and "\n(Stored at:" in result:
        return result.split("\n(Stored at:")[0]
    return result
```

### JSON Agent Example
```python
from smolagents import ToolCallingAgent
from mcpadapt.core import MCPAdapt
from mcp import StdioServerParameters

class GeometryAgentJSON:
    def __init__(self):
        self.stdio_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "grasshopper_mcp.bridge"],
            env=None
        )
        self.model = ModelProvider.get_model("geometry", temperature=0.1)
        self.memory_tools = [remember, recall, search_memory]
    
    def run(self, task: str):
        with MCPAdapt(self.stdio_params, SmolAgentsAdapter()) as mcp_tools:
            # ToolCallingAgent will generate JSON like:
            # {
            #   "name": "add_python3_script",
            #   "arguments": {
            #     "script": "import Rhino.Geometry as rg\npt1 = rg.Point3d(0,0,0)\n..."
            #   }
            # }
            agent = ToolCallingAgent(
                tools=list(mcp_tools) + self.memory_tools,
                model=self.model
            )
            return agent.run(task)
```

### Expected JSON Agent Output Example
When user says "Create two bridge points connected by a curve":
```json
{
  "name": "add_python3_script",
  "arguments": {
    "x": 100,
    "y": 100,
    "name": "Bridge Points and Curve",
    "script": "import Rhino.Geometry as rg\n\n# Define bridge start and end points\nstart_point = rg.Point3d(0, 0, 0)\nend_point = rg.Point3d(10, 0, 0)\n\n# Create connecting curve\nbridge_curve = rg.Line(start_point, end_point)\n\n# Output geometry\na = [start_point, end_point, bridge_curve]",
    "input_parameters": []
  }
}
```

## Not Doing
- ❌ Complex agent architectures
- ❌ Rewriting the entire system
- ❌ Adding more complexity to Code Agent

## Timeline
- **Today**: Fix memory recall, create JSON agent prototype
- **Tomorrow**: Test and evaluate both approaches
- **Day 3**: Implement chosen solution
- **Day 4-5**: Testing and documentation

**ESTIMATED COMPLETION**: 3-5 days for full fix and optimization