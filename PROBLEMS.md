# PROBLEMS.md - Context Continuity for Claude

> **Purpose**: This file provides context for Claude when sessions reset, tracking ongoing problems, solutions in progress, and current system state.

---

## 🎯 **Current Main Problem: Geometry Agent MCP Integration**

### **Root Cause Identified** ✅
The geometry agent in the Bridge Design System is **NOT using actual MCP tools** - it's using placeholder/dummy tools instead.

**Evidence:**
- Test output shows only 5 tools: `create_point`, `create_line`, `create_curve`, `analyze_geometry`, `final_answer`
- Working test (`test_simple_working_solution.py`) gets 40+ real MCP tools
- Current system creates geometry agent without MCP connection

### **Working vs Broken Comparison**

#### ✅ **Working Pattern** (`test_simple_working_solution.py`):
- Uses `simple_geometry_agent.py` with `ToolCollection.from_mcp()`
- Gets **49 real MCP tools** from grasshopper bridge
- Agent created INSIDE MCP context where tools are alive
- Actually connects to Grasshopper via TCP bridge

#### ❌ **Current Broken System**:
- Triage agent creates `GeometryAgent()` with NO MCP tools passed
- Only gets **4 placeholder tools** that return dummy dictionaries
- Never connects to actual MCP server
- No TCP bridge communication

### **Solution Approved**: MCPClient Pattern (Option 2)
- Implement persistent MCP connection for entire session
- Use `GeometryAgentWithMCP` class with proper lifecycle management
- Add health monitoring, auto-reconnection, and fallback mechanisms
- Maintain context between multiple geometry operations

---

## 📋 **Current Implementation Status**

### **Phase 1: Analysis Complete** ✅
- [x] Root cause identified: geometry agent not using MCP tools
- [x] Working test pattern analyzed (`simple_geometry_agent.py`)
- [x] MCPClient pattern chosen for long-term solution
- [x] Implementation plan approved

### **Phase 2: Implementation In Progress** 🔄
- [ ] Create detailed implementation roadmap
- [ ] Implement persistent MCPClient connection
- [ ] Update triage agent to use GeometryAgentWithMCP
- [ ] Add health monitoring and auto-reconnection
- [ ] Create comprehensive test suite

---

## 🔧 **System Architecture Overview**

### **Current Working Components** ✅
- **Triage Agent**: Working, coordinates between agents
- **Multi-Agent System**: 4 agents (triage, geometry, material, structural) 
- **Model Configuration**: Gemini 2.5 Flash working for all agents
- **TCP Bridge**: C# component working (`GH_MCPComponent.cs`)
- **MCP Tools**: 49 tools available but only 6 currently enabled in bridge.py

### **MCP Integration Stack**:
```
smolagents → STDIO MCP Server → TCP Client → TCP Bridge → Grasshopper
          (grasshopper_mcp.bridge)  (communication.py)  (GH_MCPComponent.cs)
           6 enabled tools         JSON over TCP       C# TCP server
```

### **File Structure**:
- **Bridge**: `/src/bridge_design_system/mcp/grasshopper_mcp/bridge.py` (6/49 tools enabled)
- **Geometry Agent**: `/src/bridge_design_system/agents/geometry_agent.py` (using dummy tools)
- **Working Test**: `/test_simple_working_solution.py` (using real MCP tools)
- **Triage Agent**: `/src/bridge_design_system/agents/triage_agent.py` (needs MCP integration)

---

## 🚨 **Known Issues & Workarounds**

### **Issue 1: Limited MCP Tools** ⚠️
- **Problem**: Only 6/49 MCP tools currently enabled in bridge.py
- **Status**: Intentionally disabled for testing
- **Tools Available**: `add_python3_script`, `get_python3_script`, `edit_python3_script`, `get_python3_script_errors`, `get_component_info_enhanced`, `get_all_components_enhanced`
- **Solution**: Re-enable tools as needed for geometry operations

### **Issue 2: Context Manager vs MCPClient** 🔄
- **Problem**: Two different MCP integration patterns exist
- **Current**: Context manager pattern (working but not persistent)
- **Target**: MCPClient pattern (persistent, better for sessions)
- **Status**: Migration in progress

### **Issue 3: Agent Factory Pattern** 📋
- **Problem**: No centralized agent creation with MCP support
- **Impact**: Inconsistent MCP integration across agents
- **Solution**: Create agent factory for consistent MCP-enabled agent creation

---

## 🧪 **Testing Status**

### **Working Tests** ✅
- `test_simple_working_solution.py`: Proves MCP integration works
- System startup test: All 4 agents initialize correctly
- Basic task execution: Triage agent coordinates successfully

### **Tests Needed** 📝
- MCPClient lifecycle management
- Persistent connection across multiple tasks
- Auto-reconnection on connection failure
- Fallback to dummy tools when MCP unavailable
- Integration test with full geometry workflow

---

## 📈 **Performance Metrics**

### **Current Performance**:
- **Agent Initialization**: ~3-4 seconds (all 4 agents)
- **Task Execution**: ~30 seconds (includes calculation + dummy tools)
- **MCP Connection**: Not persistent (creates new each time)

### **Target Performance** (Post-MCPClient):
- **Initial Connection**: ~3-5 seconds (one-time)
- **Subsequent Tasks**: ~2-5 seconds (persistent connection)
- **Context Preservation**: Geometry persists between operations

---

## 🎯 **Next Actions for New Claude Session**

1. **Review Implementation Roadmap**: Check `MCP_CLIENT_IMPLEMENTATION_ROADMAP.md`
2. **Verify Current State**: Run `uv run python -m bridge_design_system.main --test`
3. **Check Progress**: Review todo list and completed checkboxes
4. **Continue Implementation**: Follow roadmap phases
5. **Test Integration**: Validate each phase with specific tests

---

## 💡 **Key Insights for Context**

### **Architecture Decision**: TCP Bridge (Proven) ✅
- Same architecture that worked with Claude Desktop
- Direct JSON over TCP socket, no HTTP complexity
- Fast execution, immediate request-response pattern
- Visual monitoring in Grasshopper bridge component

### **Model Configuration**: Gemini 2.5 Flash ✅
- Cost-efficient: 21x cheaper than Claude
- Working for all 4 agents
- Optimal price-performance ratio for production

### **Critical Files to Monitor**:
- `/src/bridge_design_system/agents/triage_agent.py` - Main orchestrator
- `/src/bridge_design_system/agents/geometry_agent.py` - Needs MCP integration
- `/src/bridge_design_system/mcp/grasshopper_mcp/bridge.py` - MCP tool definitions
- `/test_simple_working_solution.py` - Working MCP pattern reference

---

## 📞 **Contact Points for User**

### **Commands to Test System**:
```bash
# Test system functionality
uv run python -m bridge_design_system.main --test

# Run interactive system
uv run python -m bridge_design_system.main

# Test working MCP pattern
uv run python test_simple_working_solution.py
```

### **Key Questions to Ask User**:
1. "Should I continue with the MCPClient implementation?"
2. "Any new issues or changes to priorities?"
3. "Need to re-enable more MCP tools in bridge.py?"
4. "Ready for testing phase or still implementing?"

---

**Last Updated**: 2025-01-11 14:30 UTC  
**Status**: MCPClient implementation roadmap creation in progress  
**Next Phase**: Implement persistent MCP connection pattern