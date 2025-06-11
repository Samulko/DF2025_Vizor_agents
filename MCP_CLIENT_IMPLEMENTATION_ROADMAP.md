# MCP Client Implementation Roadmap

> **Objective**: Transform the geometry agent from using placeholder tools to a production-ready MCPClient pattern with persistent MCP connection, proper lifecycle management, and fallback mechanisms.

---

## 📊 **Executive Summary**

### **Current Problem**
- Geometry agent uses 4 dummy tools instead of 49 real MCP tools
- No persistent connection to Grasshopper TCP bridge
- Context lost between geometry operations
- Poor user experience for multi-step design workflows

### **Target Solution**
- Persistent MCPClient connection for entire session
- Health monitoring with auto-reconnection
- Graceful fallback when MCP unavailable
- 10x faster response times for subsequent operations

### **Timeline**: 7-10 hours total development time

---

## 🎯 **Phase 1: Core MCPClient Implementation** (2-3 hours)

### **1.1 Enhance GeometryAgentWithMCP Class**
**File**: `/src/bridge_design_system/agents/geometry_agent_with_mcp.py`

#### **Core Connection Management**
- [ ] Complete the `connect_to_mcp()` method with proper error handling
- [ ] Implement `disconnect()` method with graceful cleanup
- [ ] Add `health_check()` method for connection monitoring
- [ ] Add `auto_reconnect()` with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- [ ] Implement connection timeout handling (10 second default)

#### **Tool Management**
- [ ] Create `_refresh_tools()` method to reload tools from MCP server
- [ ] Add tool validation to ensure all expected tools are available
- [ ] Implement tool caching for performance
- [ ] Add tool availability reporting for debugging

#### **Implementation Pattern**:
```python
class GeometryAgentWithMCP:
    def __init__(self):
        self.mcp_client = None
        self.mcp_tools = []
        self._connected = False
        self._connection_healthy = True
        self._reconnect_attempts = 0
        self._last_health_check = None
    
    def connect_to_mcp(self) -> bool:
        """Establish persistent MCP connection"""
        # Implementation with error handling
    
    def health_check(self) -> bool:
        """Verify connection is alive"""
        # Ping MCP server
    
    def auto_reconnect(self, max_retries: int = 3) -> bool:
        """Reconnect with exponential backoff"""
        # Implementation with backoff logic
```

#### **Testing Requirements**:
- [ ] Test successful connection establishment
- [ ] Test connection failure handling
- [ ] Test auto-reconnection logic
- [ ] Test health check functionality
- [ ] Test graceful disconnection

---

## 🔗 **Phase 2: Agent Integration** (1-2 hours)

### **2.1 Update Triage Agent Integration**
**File**: `/src/bridge_design_system/agents/triage_agent.py`

#### **Agent Initialization**
- [ ] Replace `GeometryAgent()` with `GeometryAgentWithMCP()`
- [ ] Add MCP connection initialization in `initialize_agent()`
- [ ] Add connection retry logic during startup
- [ ] Implement graceful degradation if MCP connection fails

#### **Status Monitoring**
- [ ] Update `get_agent_status()` to include MCP connection info
- [ ] Add connection uptime tracking
- [ ] Add reconnection event logging
- [ ] Include tool count and health status

#### **Implementation Pattern**:
```python
def initialize_agent(self):
    # Import here to avoid circular imports
    from .geometry_agent_with_mcp import GeometryAgentWithMCP
    
    # Initialize with MCP support
    geometry_agent = GeometryAgentWithMCP()
    
    # Attempt MCP connection
    if not geometry_agent.connect_to_mcp():
        self.logger.warning("MCP connection failed, geometry agent will use fallback tools")
    
    self.managed_agents = {
        "geometry": geometry_agent,
        "material": MaterialAgent(),
        "structural": StructuralAgent()
    }
```

#### **Testing Requirements**:
- [ ] Test triage agent initialization with MCP
- [ ] Test fallback when MCP unavailable
- [ ] Test status reporting includes MCP info
- [ ] Test agent coordination with persistent MCP

### **2.2 Add Fallback Mechanisms**
**File**: `/src/bridge_design_system/agents/geometry_agent_with_mcp.py`

#### **Fallback Tool Creation**
- [ ] Create `_create_fallback_tools()` method
- [ ] Implement basic geometry tools when MCP unavailable
- [ ] Add clear user feedback about fallback mode
- [ ] Maintain agent functionality without MCP

#### **Implementation Pattern**:
```python
def _create_fallback_tools(self) -> List[Tool]:
    """Create basic tools when MCP unavailable"""
    @tool
    def create_point_fallback(x: float, y: float, z: float) -> dict:
        return {"type": "point", "coordinates": {"x": x, "y": y, "z": z}}
    
    # Additional fallback tools...
    return [create_point_fallback, ...]

def run_task(self, task: str):
    """Run task with automatic fallback"""
    if not self._connected and not self.auto_reconnect():
        self.logger.warning("Using fallback tools - MCP unavailable")
        return self._run_with_fallback(task)
    
    return self.agent.run(task)
```

#### **Testing Requirements**:
- [ ] Test fallback tool creation
- [ ] Test task execution with fallback tools
- [ ] Test user notification of fallback mode
- [ ] Test MCP recovery from fallback mode

---

## 🧪 **Phase 3: Comprehensive Testing Suite** (2-3 hours)

### **3.1 Unit Tests**
**File**: `/tests/test_mcp_client_geometry_agent.py`

#### **Connection Lifecycle Tests**
- [ ] Test `connect_to_mcp()` success scenario
- [ ] Test `connect_to_mcp()` failure scenarios
- [ ] Test `disconnect()` cleanup
- [ ] Test `health_check()` accuracy
- [ ] Test auto-reconnection with various failure modes

#### **Tool Management Tests**
- [ ] Test tool loading from MCP server
- [ ] Test tool refresh after reconnection
- [ ] Test tool validation and error reporting
- [ ] Test fallback tool functionality

#### **Agent Integration Tests**
- [ ] Test agent creation with MCP connection
- [ ] Test task execution with MCP tools
- [ ] Test graceful degradation scenarios
- [ ] Test status reporting accuracy

### **3.2 Integration Tests**
**File**: `/tests/test_geometry_agent_integration.py`

#### **Multi-Task Scenarios**
- [ ] Test multiple geometry operations in sequence
- [ ] Test context preservation between tasks
- [ ] Test connection stability over time
- [ ] Test recovery from connection interruption

#### **Performance Tests**
- [ ] Benchmark initial connection time
- [ ] Benchmark subsequent task execution times
- [ ] Compare with context manager pattern performance
- [ ] Test memory usage over extended sessions

#### **Real-World Scenarios**
- [ ] Test spiral creation task (from original problem)
- [ ] Test complex geometry workflows
- [ ] Test error handling in production scenarios
- [ ] Test long-running design sessions (30+ minutes)

### **3.3 System Integration Tests**
**File**: `/tests/test_full_system_with_mcp.py`

#### **End-to-End Testing**
- [ ] Test complete CLI workflow with MCP
- [ ] Test triage agent coordination with MCP geometry agent
- [ ] Test system startup and shutdown with MCP
- [ ] Test error recovery across full system

#### **Implementation Pattern**:
```python
def test_persistent_geometry_workflow():
    """Test multiple geometry operations maintain context"""
    with create_triage_agent_with_mcp() as triage:
        # First task
        result1 = triage.handle_design_request("Create a point at (0,0,0)")
        assert "point created" in result1.message.lower()
        
        # Second task using context from first
        result2 = triage.handle_design_request("Create a line from that point to (10,0,0)")
        assert "line created" in result2.message.lower()
        
        # Verify both geometries exist
        status = triage.get_agent_status()
        assert status["geometry"]["mcp_connected"] == True
```

---

## 🔄 **Phase 4: Migration and Utilities** (1 hour)

### **4.1 Create Agent Factory Pattern**
**File**: `/src/bridge_design_system/agents/agent_factory.py`

#### **Centralized Agent Creation**
- [ ] Create `create_geometry_agent()` factory function
- [ ] Add configuration-driven agent instantiation
- [ ] Support both MCPClient and context manager patterns
- [ ] Add proper resource management

#### **Implementation Pattern**:
```python
def create_geometry_agent(pattern: str = "mcp_client") -> GeometryAgent:
    """Factory for creating geometry agents with different patterns"""
    if pattern == "mcp_client":
        agent = GeometryAgentWithMCP()
        agent.connect_to_mcp()
        return agent
    elif pattern == "context_manager":
        return create_geometry_agent_with_mcp_tools()
    else:
        return GeometryAgent()  # Basic agent without MCP
```

### **4.2 Configuration Updates**
**File**: `/src/bridge_design_system/config/settings.py`

#### **MCP Configuration Options**
- [ ] Add `MCP_CONNECTION_TIMEOUT = 10`
- [ ] Add `MCP_HEALTH_CHECK_INTERVAL = 30`
- [ ] Add `MCP_MAX_RECONNECT_ATTEMPTS = 3`
- [ ] Add `MCP_RECONNECT_BACKOFF_BASE = 2`
- [ ] Add `MCP_ENABLE_FALLBACK = True`
- [ ] Add `GEOMETRY_AGENT_PATTERN = "mcp_client"`

#### **Testing Requirements**:
- [ ] Test configuration loading
- [ ] Test different configuration scenarios
- [ ] Test configuration validation

---

## 📚 **Phase 5: Documentation and Polish** (1 hour)

### **5.1 Update Documentation**
**File**: `/CLAUDE.md`

#### **Usage Examples**
- [ ] Add MCPClient pattern examples
- [ ] Document configuration options
- [ ] Add troubleshooting guide
- [ ] Include performance recommendations

#### **Architecture Documentation**
- [ ] Document MCPClient vs context manager patterns
- [ ] Explain when to use each pattern
- [ ] Document connection lifecycle
- [ ] Add error handling best practices

### **5.2 Create Usage Examples**
**File**: `/examples/mcp_client_usage.py`

#### **Demonstration Scripts**
- [ ] Basic MCPClient usage example
- [ ] Multi-task workflow example
- [ ] Error handling demonstration
- [ ] Performance comparison script

---

## ✅ **Success Criteria**

### **Functional Requirements**
- [ ] Geometry agent connects to MCP server and gets 49 tools (not 4 dummy tools)
- [ ] Multiple geometry tasks execute in sequence with preserved context
- [ ] Connection failures automatically trigger reconnection attempts
- [ ] System gracefully falls back to basic tools when MCP unavailable
- [ ] Triage agent reports MCP connection status accurately

### **Performance Requirements**
- [ ] Initial MCP connection completes within 10 seconds
- [ ] Subsequent geometry tasks complete within 5 seconds
- [ ] No memory leaks during extended sessions (30+ minutes)
- [ ] System handles 100+ geometry operations without degradation

### **Reliability Requirements**
- [ ] System recovers from MCP server restarts within 30 seconds
- [ ] Connection health checks accurately detect failures
- [ ] All resources properly cleaned up on shutdown
- [ ] No hanging connections or zombie processes

### **User Experience Requirements**
- [ ] Clear feedback when MCP connection is established/lost
- [ ] Smooth degradation to fallback mode without crashes
- [ ] Consistent behavior across multiple design sessions
- [ ] Fast response times for iterative geometry design

---

## 🚨 **Rollback Plan**

### **Safety Measures**
- [ ] Maintain original `geometry_agent.py` as backup
- [ ] Keep context manager pattern available as fallback
- [ ] Create rollback script to revert changes
- [ ] Test rollback procedure before implementation

### **Rollback Triggers**
- Performance regression > 50%
- Test failure rate > 10%
- User experience significantly degraded
- Memory usage increased > 100%

### **Rollback Steps**
1. [ ] Disable MCPClient pattern in configuration
2. [ ] Revert triage agent to use original GeometryAgent
3. [ ] Restore previous agent initialization code
4. [ ] Run full test suite to verify rollback success

---

## 📈 **Progress Tracking**

### **Overall Progress**
- [ ] Phase 1: Core MCPClient Implementation (0/12 tasks)
- [ ] Phase 2: Agent Integration (0/8 tasks)
- [ ] Phase 3: Testing Suite (0/15 tasks)
- [ ] Phase 4: Migration Utilities (0/6 tasks)
- [ ] Phase 5: Documentation (0/4 tasks)

**Total Progress: 0/45 tasks (0%)**

### **Key Milestones**
- [ ] **Milestone 1**: MCPClient successfully connects and loads 49 tools
- [ ] **Milestone 2**: Triage agent uses MCPClient-based geometry agent
- [ ] **Milestone 3**: Full test suite passes with 95%+ success rate
- [ ] **Milestone 4**: System performs better than context manager pattern
- [ ] **Milestone 5**: Documentation complete and examples working

---

## 🔍 **Next Steps for Implementation**

### **Immediate Actions** (Start Here)
1. [ ] **Review current `geometry_agent_with_mcp.py`** - Understand existing implementation
2. [ ] **Test connection to MCP server** - Verify bridge is working
3. [ ] **Implement basic MCPClient pattern** - Get minimal connection working
4. [ ] **Add to triage agent** - Replace dummy geometry agent
5. [ ] **Create simple test** - Verify 49 tools are loaded

### **Development Environment Setup**
- [ ] Ensure MCP bridge server is running: `uv run python -m grasshopper_mcp.bridge`
- [ ] Verify Grasshopper TCP bridge component is active
- [ ] Run baseline test: `uv run python test_simple_working_solution.py`
- [ ] Check system test: `uv run python -m bridge_design_system.main --test`

### **Debug Commands**
```bash
# Test current system
uv run python -m bridge_design_system.main

# Test working MCP pattern
uv run python test_simple_working_solution.py

# Check MCP server tools
uv run python -c "from smolagents import ToolCollection; from mcp import StdioServerParameters; params = StdioServerParameters(command='uv', args=['run', 'python', '-m', 'grasshopper_mcp.bridge']); with ToolCollection.from_mcp(params, trust_remote_code=True) as tc: print(f'Tools: {len(list(tc.tools))}')"
```

---

**Last Updated**: 2025-01-11 14:35 UTC  
**Status**: Implementation roadmap complete, ready to begin Phase 1  
**Next Action**: Begin Phase 1.1 - Enhance GeometryAgentWithMCP Class