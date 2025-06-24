# **Refactor MCPGeometryAgent to Follow Smolagents Best Practices**

## **CORE OBJECTIVE**

Eliminate the unnecessary `MCPGeometryAgent` class from `triage_agent_smolagents.py` and refactor the codebase to follow proper smolagents patterns using the existing standalone geometry agent.

## **🎯 PROBLEM ANALYSIS**

### **Current Architecture Issues**
- **Pattern Violation**: Embedding 400+ line agent class inside triage agent file violates smolagents composition principles
- **Duplication**: Two geometry agent implementations exist (`MCPGeometryAgent` vs `SmolagentsGeometryAgent`)
- **Obsolete Methods**: Several methods solve problems that no longer exist in current workflow
- **Workflow Mismatch**: Complex component tracking for a workflow that only edits existing python3 scripts

### **Current Workflow Reality**
Based on `system_prompts/geometry_agent.md`:
- **FIND** → **SELECT** → **READ** → **MODIFY** → **CHECK** → **PERSIST**
- Only operates on existing `component_1`, `component_2`, etc. python3 script components
- No component creation, just script modification via MCP tools
- Simple workflow that doesn't need complex state management

### **Smolagents Best Practice**
```python
# Correct pattern from smolagents docs
web_agent = ToolCallingAgent(
    tools=[WebSearchTool()],
    model=model,
    name="web_search_agent",  # Required for managed_agents
    description="Runs web searches for you."  # Required for managed_agents
)

manager_agent = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[web_agent]  # Simple reference, no embedding
)
```

## **🛠️ IMPLEMENTATION PHASES**

### **Phase 1: Remove MCPGeometryAgent Class**

**Objective**: Delete the embedded agent class and unnecessary methods

**File to modify**: `src/bridge_design_system/agents/triage_agent_smolagents.py`

**Methods to Remove**:
- `class MCPGeometryAgent` (lines 203-619) - Entire 400+ line class
- `_resolve_context_from_task()` - No longer needed (no script creation)
- `_track_component_in_state()` - Custom approach, use native smolagents memory
- `_extract_and_register_components()` - Barely used, just logs
- `_determine_component_type()` - Obsolete (only classifies bridge components, workflow only edits scripts)
- `_fuzzy_type_match()` - Supporting method for obsolete functionality

**Rationale**:
- Script creation was removed from geometry agent
- Current workflow only edits existing components
- Native smolagents memory (`agent.memory.steps`) handles persistence
- Component classification irrelevant for script editing workflow

### **Phase 2: Update Geometry Agent for Managed Agents**

**Objective**: Ensure existing `SmolagentsGeometryAgent` works with `managed_agents` pattern

**File to modify**: `src/bridge_design_system/agents/geometry_agent_smolagents.py`

**Required Changes**:
```python
class SmolagentsGeometryAgent:
    def __init__(self, ...):
        # Ensure these attributes exist for managed_agents
        self.name = "geometry_agent"  # Already exists (line 41)
        self.description = "Creates 3D geometry in Rhino Grasshopper via persistent MCP connection"  # Already exists (line 42)
        
        # The rest remains the same - no major changes needed
```

**Verification**:
- Check that `name` and `description` attributes are properly set
- Ensure `run(task: str)` method signature is compatible
- Verify MCP connection management works correctly

### **Phase 3: Simplify Triage Agent Creation**

**Objective**: Use composition instead of complex embedding

**File to modify**: `src/bridge_design_system/agents/triage_agent_smolagents.py`

**Replace `_create_mcp_enabled_geometry_agent()` function**:
```python
def _create_mcp_enabled_geometry_agent(
    custom_tools: Optional[List] = None, 
    component_registry: Optional[Any] = None,
    monitoring_callback: Optional[Any] = None
) -> Any:
    """
    Create geometry agent using existing standalone implementation.
    
    Following smolagents best practices, this imports and configures
    the standalone geometry agent for use in managed_agents.
    """
    from .geometry_agent_smolagents import create_geometry_agent
    
    return create_geometry_agent(
        custom_tools=custom_tools,
        component_registry=component_registry,
        monitoring_callback=monitoring_callback
    )
```

**Benefits**:
- ✅ Follows smolagents composition pattern
- ✅ Eliminates 400+ lines of duplicated code
- ✅ Uses existing, tested geometry agent implementation
- ✅ Maintains all current functionality

### **Phase 4: Clean Up Unused Helper Functions**

**Objective**: Remove obsolete helper functions that supported removed methods

**File to modify**: `src/bridge_design_system/agents/triage_agent_smolagents.py`

**Functions to Remove or Simplify**:
- Helper functions that were only used by removed methods
- Any component type classification logic
- Custom memory management utilities (use native smolagents memory)

### **Phase 5: Test Integration**

**Objective**: Verify the refactored system works correctly

**Testing Steps**:
1. **Basic Agent Creation**: Ensure triage system creates without errors
2. **Geometry Agent Delegation**: Test that tasks are properly delegated to geometry agent
3. **MCP Integration**: Verify MCP connection and tool access works
4. **Memory Management**: Confirm native smolagents memory handles conversation state
5. **Error Handling**: Test fallback behavior when MCP connection fails

## **📁 FILES TO MODIFY**

### **Major Changes**
- `src/bridge_design_system/agents/triage_agent_smolagents.py` - Remove MCPGeometryAgent class, simplify creation function

### **Minor Changes**  
- `src/bridge_design_system/agents/geometry_agent_smolagents.py` - Verify managed_agents compatibility

## **🎯 EXPECTED BENEFITS & SUCCESS CRITERIA**

### **Code Quality Improvements**
- ✅ **400+ lines removed** - Eliminate unnecessary complexity
- ✅ **Separation of concerns** - Agents in separate files as intended
- ✅ **Smolagents compliance** - Follow framework best practices
- ✅ **No duplication** - Single geometry agent implementation

### **Maintainability Enhancement**
- ✅ **Cleaner architecture** - Composition over complex inheritance
- ✅ **Easier debugging** - Clear separation between triage and geometry logic
- ✅ **Better testing** - Standalone agents can be tested independently
- ✅ **Framework alignment** - Uses smolagents as intended

### **Functional Preservation**
- ✅ **Same capabilities** - All current functionality preserved
- ✅ **Same performance** - MCP connection management unchanged
- ✅ **Same reliability** - Existing tested geometry agent used
- ✅ **Same monitoring** - Callback system preserved

## **🚀 IMPLEMENTATION ORDER**

1. **Remove MCPGeometryAgent class** - Delete embedded class and obsolete methods
2. **Simplify geometry agent creation** - Use import-based composition
3. **Verify managed_agents compatibility** - Ensure existing agent works properly
4. **Clean up unused helpers** - Remove supporting functions for deleted methods
5. **Test integration** - Validate functionality preservation
6. **Update documentation** - Reflect new simplified architecture

## **💡 TECHNICAL ARCHITECTURE NOTES**

### **Smolagents Pattern Compliance**
```python
# BEFORE (embedded, complex)
class MCPGeometryAgent(ToolCallingAgent):
    # 400+ lines of embedded complexity
    pass

# AFTER (composition, simple)
from .geometry_agent_smolagents import create_geometry_agent
geometry_agent = create_geometry_agent(...)
manager = CodeAgent(managed_agents=[geometry_agent])
```

### **Memory Management**
- **Before**: Custom `internal_component_cache` with manual management
- **After**: Native smolagents `agent.memory.steps` automatic persistence
- **Benefit**: Framework-provided reliability and consistency

### **Workflow Alignment**
- **Current Reality**: Edit existing python3 scripts only
- **Old Code**: Complex component creation and tracking
- **New Code**: Simple script editing focus
- **Result**: Code matches actual usage patterns

This refactoring aligns the codebase with smolagents best practices while eliminating unnecessary complexity that doesn't match the current simplified workflow.