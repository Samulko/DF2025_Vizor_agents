# Current Task: Fix Geometry Agent STDIO Issues and Evaluate JSON Agent Alternative

## Problem Summary

The Geometry Agent STDIO implementation has critical issues with:
1. **Memory recall returning metadata-polluted values** causing component ID parsing failures
2. **Agent misunderstanding MCP tool return types** (JSON strings vs dictionaries)
3. **Duplicate component creation** due to improper error handling
4. **Code execution context confusion** in the smolagents framework

## Should We Use JSON Agent Instead of Code Agent?

### Analysis: JSON Agent (ToolCallingAgent) vs Code Agent

**JSON Agent PROS for this use case:**
- ✅ **Simpler data handling**: JSON agents don't need to understand Python types or parse JSON
- ✅ **Native tool integration**: Better suited for calling external tools like MCP
- ✅ **Clearer error boundaries**: Failures are at tool level, not code execution level
- ✅ **No code execution context issues**: Eliminates the dictionary/string confusion

**JSON Agent CONS:**
- ❌ **Limited flexibility**: Can't do complex logic or data transformations
- ❌ **No variable handling**: Can't store intermediate results or build complex scripts
- ❌ **Sequential only**: Can't loop or conditionally execute tools

### Recommendation: **YES, JSON Agent would work better**

For the Geometry Agent's primary tasks (calling MCP tools to create Grasshopper components), a JSON Agent is actually MORE appropriate because:
1. Most operations are simple tool calls with clear parameters
2. No complex logic or loops needed
3. Eliminates the JSON parsing confusion entirely
4. MCP tools are designed for JSON-style invocation

## Immediate Tasks (Priority Order)

### Task 1: Fix Memory Tool Return Format [CRITICAL]
**Problem**: `recall()` returns strings with metadata like `"270dc13e-b4fb-4802-8441-d4452a8196ae\n(Stored at: 2025-06-15T14:52:25.720584, retrieved in 0.2ms)"`

**Solution**: 
- Modify `recall()` in `memory_tools.py` to return only the value without metadata
- Add a `recall_with_metadata()` function if metadata is needed

### Task 2: Test JSON Agent Implementation [HIGH]
**Goal**: Create a proof-of-concept JSON agent for geometry operations

**Steps**:
1. Create `geometry_agent_json.py` using `ToolCallingAgent`
2. Test with simple MCP tool calls
3. Compare error rates with Code Agent

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

### Phase 1: Quick Fixes (Today)
1. **Fix memory recall format** (30 mins)
   - Update `recall()` to strip metadata
   - Test with existing agents

2. **Create JSON agent prototype** (2 hours)
   - Implement `GeometryAgentJSON` class
   - Test basic MCP tool calling
   - Compare with STDIO agent

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

class GeometryAgentJSON:
    def run(self, task: str):
        with MCPAdapt(self.stdio_params, SmolAgentsAdapter()) as mcp_tools:
            agent = ToolCallingAgent(
                tools=list(mcp_tools) + self.memory_tools,
                model=self.model
            )
            return agent.run(task)
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