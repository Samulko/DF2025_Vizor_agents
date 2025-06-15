# Current Task: Implement JSON Agent for Geometry Operations

## Context & Background

**Problem**: Current CodeAgent-based geometry agent has critical errors:
1. **Memory recall pollution**: Component IDs include metadata causing MCP tool failures
2. **JSON parsing confusion**: Agent treats JSON strings as dictionaries  
3. **Duplicate component creation**: Error handling retries create multiple components
4. **Code execution issues**: smolagents CodeAgent struggles with MCP tool responses

**Root Cause**: CodeAgent architecture adds unnecessary complexity for MCP tool calling

**Solution**: Switch to ToolCallingAgent which is purpose-built for external tool integration

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
- ✅ **Has state management**: ToolCallingAgent maintains state dictionary for variables across steps
- ❌ **Linear execution only**: Follows ReAct pattern - no loops or complex branching across steps  
- ❌ **Single tool per step**: Sequential execution only, no parallel tool calls

**Corrected Facts:**
- **WRONG**: "No intermediate variables" - JSON agents DO have state management
- **TRUE**: "No complex control flow" - Limited to linear ReAct pattern
- **TRUE**: "Single tool per step" - Cannot execute multiple tools in parallel

### Recommendation: **STRONGLY YES - JSON Agent is ideal**

For Geometry Agent tasks (MCP tool calls with dynamically generated scripts), JSON Agent is **significantly better** because:
1. **Eliminates current errors**: No more JSON parsing confusion
2. **Perfect MCP match**: MCP tools expect JSON calls
3. **Same script generation**: LLM creates complex Python scripts dynamically
4. **Simpler architecture**: Direct tool calls without Python execution layer
5. **Native smolagents pattern**: Official documentation shows MCP + JSON agent examples

## Action Plan - Execute in Order

### ✅ CRITICAL: Create JSON Agent Implementation

**File to create**: `src/bridge_design_system/agents/geometry_agent_json.py`

**Requirements**:
- Use `ToolCallingAgent` from smolagents
- Connect to MCP via MCPAdapt with STDIO transport
- Include memory tools (remember, recall, search_memory)
- Same model configuration as current STDIO agent
- Handle conversation context like current implementation

**DO**:
- Use MCPAdapt context manager for connection lifecycle
- Set temperature=0.1 for precise instruction following
- Include all memory tools in agent initialization
- Implement conversation context building
- Use same system prompt approach as current agent

**DON'T**:
- Don't use CodeAgent - we're switching to ToolCallingAgent
- Don't try to fix JSON parsing - JSON agent handles this natively
- Don't add Python execution context - not needed for JSON agent
- Don't modify MCP tools - they work correctly

### ✅ HIGH: Fix Memory Tool Metadata Pollution

**File to modify**: `src/bridge_design_system/tools/memory_tools.py`

**Problem**: `recall()` returns component IDs with metadata like:
```
"270dc13e-b4fb-4802-8441-d4452a8196ae\n(Stored at: 2025-06-15T14:52:25.720584, retrieved in 0.2ms)"
```

**Requirements**:
- Modify `recall()` function to strip metadata from returned values
- Preserve clean UUID format for component IDs
- Maintain backward compatibility

**Implementation**:
```python
# Strip metadata if present
if result and "\n(Stored at:" in result:
    return result.split("\n(Stored at:")[0].strip()
```

### ✅ MEDIUM: Update Triage Agent Integration

**File to modify**: `src/bridge_design_system/agents/triage_agent.py`

**Requirements**:
- Update triage agent to use new `GeometryAgentJSON` instead of `GeometryAgentSTDIO`
- Test integration works correctly
- Ensure no breaking changes to existing workflows

### ✅ LOW: Add Component Deduplication (Optional)

**Goal**: Prevent duplicate component creation in error scenarios

**Implementation**: Add memory checks before component creation:
```python
# Before creating new component, check if similar exists
existing = search_memory("bridge_points")
if not existing:
    # Create new component
```

## TODO Checklist

- [ ] **Create `geometry_agent_json.py`** with ToolCallingAgent implementation
- [ ] **Fix memory recall metadata** in `memory_tools.py` 
- [ ] **Test JSON agent** with simple MCP tool calls
- [ ] **Compare error rates** between JSON and Code agents
- [ ] **Update triage agent** to use JSON agent
- [ ] **Run end-to-end test** of bridge design workflow
- [ ] **Commit working solution** and update documentation

## Success Criteria - Definition of Done

### Primary Goals (Must Have)
- [ ] **Zero component ID parsing errors** - No more "Invalid component ID format" failures
- [ ] **Clean memory recall** - Component IDs returned without metadata pollution
- [ ] **Single component creation** - No duplicate components from error retries
- [ ] **Successful script generation** - JSON agent generates valid Rhino Python scripts
- [ ] **MCP tool integration** - All 6 MCP tools work correctly with JSON agent

### Secondary Goals (Should Have)  
- [ ] **Error rate < 5%** for standard bridge design operations
- [ ] **Same functionality** as current STDIO agent
- [ ] **Faster execution** due to simplified architecture
- [ ] **Maintainable code** with clear separation of concerns

### Test Scenarios
1. **Basic**: "Create two bridge points" - should create single component successfully
2. **Complex**: "Create bridge points and connect with curve" - should handle multi-step operations
3. **Memory**: Component IDs stored and retrieved correctly across agent runs
4. **Error handling**: Graceful failure when MCP server unavailable

## Implementation Templates

### 1. Geometry Agent JSON (Template)
```python
# src/bridge_design_system/agents/geometry_agent_json.py
from smolagents import ToolCallingAgent
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from mcp import StdioServerParameters

class GeometryAgentJSON:
    def __init__(self, model_name: str = "geometry"):
        self.stdio_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "grasshopper_mcp.bridge"], 
            env=None
        )
        self.model = ModelProvider.get_model(model_name, temperature=0.1)
        self.memory_tools = [remember, recall, search_memory, clear_memory]
        self.conversation_history = []
    
    def run(self, task: str):
        try:
            with MCPAdapt(self.stdio_params, SmolAgentsAdapter()) as mcp_tools:
                agent = ToolCallingAgent(
                    tools=list(mcp_tools) + self.memory_tools,
                    model=self.model
                )
                result = agent.run(self._build_conversation_context(task))
                self._store_conversation(task, result)
                return result
        except Exception as e:
            return self._handle_error(e, task)
```

### 2. Memory Tool Fix (Exact Change)
```python
# In src/bridge_design_system/tools/memory_tools.py  
# Find the recall function and update it:

@tool
def recall(category: str = None, key: str = None) -> str:
    """Retrieve information from persistent memory without metadata."""
    memory = MemoryManager.get_instance()
    result = memory.recall(category, key)
    
    # CRITICAL FIX: Strip metadata if present
    if result and "\n(Stored at:" in result:
        return result.split("\n(Stored at:")[0].strip()
    
    return result
```

### 3. Triage Agent Integration (Update)
```python
# In src/bridge_design_system/agents/triage_agent.py
# Replace GeometryAgentSTDIO import with:
from .geometry_agent_json import GeometryAgentJSON

# Update the geometry agent initialization
self.geometry_agent = GeometryAgentJSON(model_name="geometry")
```

## Key Architectural Insight

**Why JSON Agent Eliminates Errors**:
- Current: CodeAgent executes `json.loads(mcp_result)` → parsing errors
- New: ToolCallingAgent directly receives JSON from MCP → no parsing needed
- MCP tools designed for JSON calling, not Python execution context

## Risk Mitigation

**Potential Issues**:
- JSON agent state management might differ from CodeAgent
- Tool call patterns may need adjustment
- System prompts may need optimization for JSON format

**Mitigation**:
- Keep existing CodeAgent as fallback during testing
- Implement identical conversation context handling
- Use same memory tools and system prompt approach