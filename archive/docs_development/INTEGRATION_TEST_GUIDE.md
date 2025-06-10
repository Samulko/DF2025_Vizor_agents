# Vizor Agents - Complete Integration Test Guide

This guide provides step-by-step instructions for testing the complete Geometry Agent → Grasshopper integration.

## Overview

The integration consists of 4 phases:

1. **Phase 1**: Build C# Grasshopper Component (User handles this)
2. **Phase 2**: Connect Python MCP Server to Grasshopper  
3. **Phase 3**: Test Geometry Agent Control
4. **Phase 4**: Full System Validation

## Prerequisites

### System Requirements
- Windows 10/11 (for Grasshopper/Rhino compatibility)
- Python 3.10+ with UV package manager
- Rhino 7+ with Grasshopper
- Visual Studio or VS Code with C# support

### Environment Setup
```powershell
# Clone and setup project
cd C:\path\to\vizor_agents
uv venv
.venv\Scripts\activate
uv pip install -e .

# Verify installation
python -m bridge_design_system.main --test
```

### API Keys
Create `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here  # Optional
```

## Phase 1: Build C# Grasshopper Component (User Task)

**⚠️ This phase is handled by the user - not automated.**

### What You Need To Build

A C# Grasshopper component that:
1. Connects to HTTP MCP server at `http://localhost:8001`
2. Polls `/grasshopper/pending_commands` every 1 second
3. Executes commands in Grasshopper
4. Posts results to `/grasshopper/command_result`

### Reference Implementation

See `/src/bridge_design_system/mcp/GH_MCP/SimpleMCPBridge.cs` for a complete working example.

### Key Features Required

```csharp
// Polling timer
Timer pollingTimer = new Timer(1000); // 1 second interval

// HTTP client for MCP server
HttpClient httpClient = new HttpClient();
httpClient.BaseAddress = new Uri("http://localhost:8001");

// Command execution
private void ExecuteCommand(string commandType, JObject parameters)
{
    switch (commandType)
    {
        case "add_component":
            // Add component to Grasshopper canvas
            break;
        case "connect_components":
            // Connect two components
            break;
        // ... other commands
    }
}
```

### Building Instructions

1. Open `/src/bridge_design_system/mcp/GH_MCP/VizorAgents.GH_MCP.sln`
2. Build in Release mode
3. Copy `.gha` file to Grasshopper components folder
4. Restart Rhino/Grasshopper
5. Add component to canvas and configure

## Phase 2: Connect Python MCP Server to Grasshopper

### Start MCP Server

```powershell
# Terminal 1: Start MCP Server
python -m bridge_design_system.main --start-streamable-http --mcp-port 8001
```

Server should start without "Task group not initialized" errors.

### Run Phase 2 Tests

```powershell
# Terminal 2: Run tests
python test_phase2_mcp_server_connection.py
```

### Expected Results

```
🚀 Starting Phase 2: MCP Server Connection Tests
✅ PASS Server Health
✅ PASS MCP Protocol Init  
✅ PASS MCP Tools List
✅ PASS Bridge Endpoints
✅ PASS Command Queueing

🎯 Overall: 5/5 tests passed
🎉 Phase 2 COMPLETE - MCP server is ready for Grasshopper!
```

### Troubleshooting Phase 2

**Server won't start:**
```powershell
# Check port availability
netstat -an | findstr :8001

# Try different port
python -m bridge_design_system.main --start-streamable-http --mcp-port 8002
```

**"Task group not initialized" error:**
- This indicates StreamableHTTPSessionManager issues
- The system should automatically fall back to working implementations
- Check server logs for details

## Phase 3: Test Geometry Agent Control

### Prerequisites

1. Phase 2 tests pass ✅
2. MCP server running ✅
3. Grasshopper component connected and polling ✅

### Connect Grasshopper Bridge

1. Open Grasshopper
2. Add your SimpleMCPBridge component to canvas
3. Set server URL to `http://localhost:8001`
4. Verify component shows "Connected" and "Polling: Active"

### Run Phase 3 Tests

```powershell
# Terminal 2: Run geometry agent tests
python test_phase3_geometry_agent_control.py
```

### Expected Results

```
🚀 Starting Phase 3: Geometry Agent Control Tests
✅ PASS Simple Geometry Creation
✅ PASS Component Listing
✅ PASS Complex Geometry Operations
✅ PASS Parameter Manipulation
✅ PASS Document Management
✅ PASS Bridge Communication Validation

🎯 Overall: 6/6 tests passed
🎉 Phase 3 SUBSTANTIALLY COMPLETE - Geometry Agent can control Grasshopper!
```

### Troubleshooting Phase 3

**Agent can't connect to MCP:**
```powershell
# Check MCP server status
curl http://localhost:8001/grasshopper/status

# Debug session issues
python debug_session_id.py
```

**Commands not reaching Grasshopper:**
1. Check Grasshopper component status
2. Verify polling is active
3. Check Windows firewall settings
4. Review Grasshopper component logs

**Geometry not appearing:**
- Check Grasshopper canvas for new components
- Verify component creation parameters
- Check Grasshopper error messages

## Phase 4: Full System Validation

### Prerequisites

1. All previous phases pass ✅
2. System running stably for 10+ minutes ✅
3. Multiple successful command executions ✅

### Run Phase 4 Tests

```powershell
# Terminal 2: Run full system validation
python test_phase4_full_system_validation.py
```

### Expected Results

```
🚀 Starting Phase 4: Full System Validation
✅ PASS Simple Bridge Design
✅ PASS Multi-Step Bridge Design
✅ PASS Geometry Modification
✅ PASS Agent Delegation Workflow
✅ PASS System Error Handling
✅ PASS System Performance
✅ PASS Grasshopper Integration

🎯 Overall: 7/7 tests passed
🎉 PHASE 4 COMPLETE - FULL SYSTEM VALIDATED!
```

### Success Criteria

- **80%+ test pass rate** (acceptable for complex integration)
- **Bridge geometry created** in Grasshopper
- **Multi-agent orchestration** working
- **Error recovery** functional
- **Performance** acceptable (<5s response times)

## Validation Checklist

### Phase 2 Validation ✅
- [ ] MCP server starts without errors
- [ ] HTTP endpoints respond (port 8001)
- [ ] Bridge polling endpoints work
- [ ] Session management functional
- [ ] Tool listing returns 6 tools

### Phase 3 Validation ✅  
- [ ] Geometry Agent initializes with MCP tools
- [ ] Simple geometry creation works
- [ ] Component listing returns results
- [ ] Complex multi-step operations work
- [ ] Bridge processes commands successfully
- [ ] Grasshopper canvas shows created geometry

### Phase 4 Validation ✅
- [ ] Triage agent delegates to Geometry Agent
- [ ] Complex bridge design scenarios work
- [ ] Multi-step workflows complete
- [ ] Error handling recovers gracefully
- [ ] System performance acceptable
- [ ] Integration stable over time

## Common Issues and Solutions

### MCP Server Issues

**"Task group not initialized":**
```powershell
# Use alternative FastMCP server
python -m bridge_design_system.cli.fastmcp_server --port 8001 --bridge-mode
```

**Session ID problems:**
```powershell
# Debug session handling
python debug_session_id.py

# Check server logs for session creation
```

### Bridge Connection Issues

**Grasshopper component not polling:**
1. Check component input parameters
2. Verify HTTP client configuration  
3. Review C# component error messages
4. Check Windows firewall/antivirus

**Commands not executing:**
1. Verify JSON parsing in C# component
2. Check Grasshopper document access
3. Review command parameter validation
4. Test individual command types

### Agent Issues

**Agent can't get MCP tools:**
```powershell
# Test MCP tools directly
python -c "
from src.bridge_design_system.mcp.sync_mcp_tools import get_sync_grasshopper_tools
tools = get_sync_grasshopper_tools()
print(f'Got {len(tools)} tools')
"
```

**Agent responses timeout:**
- Increase timeout values in agent config
- Check MCP server responsiveness
- Verify bridge is processing commands
- Review agent system prompts

## Performance Optimization

### MCP Server Performance
- Use FastMCP server for better performance
- Enable connection pooling
- Optimize session management
- Monitor memory usage

### Bridge Performance  
- Adjust polling interval (1s default)
- Implement command batching
- Add connection retry logic
- Cache frequently used operations

### Agent Performance
- Optimize tool descriptions
- Reduce unnecessary tool calls
- Implement response caching
- Use efficient model providers

## Development Tips

### Debugging Commands

```powershell
# Monitor MCP server logs
python -m bridge_design_system.main --start-streamable-http --mcp-port 8001 --log-level DEBUG

# Test individual MCP tools
python test_sync_tools.py

# Check bridge status
curl http://localhost:8001/grasshopper/status

# Monitor network traffic
netstat -an | findstr :8001
```

### Visual Debugging

1. **Grasshopper Component**: Add visual feedback (status lights, command counters)
2. **MCP Server**: Enable verbose logging mode
3. **Agent Responses**: Log all tool calls and responses
4. **Network Monitor**: Use Fiddler or similar for HTTP debugging

### Code Modifications

When modifying the system:

1. **Test individual components** before integration
2. **Maintain backward compatibility** with existing tools
3. **Add comprehensive logging** for debugging
4. **Update test scripts** to match changes
5. **Document configuration changes**

## Success Metrics

### Technical Metrics
- **Response Time**: <5 seconds for simple operations
- **Reliability**: >95% command success rate
- **Stability**: System runs >1 hour without restart
- **Scalability**: Handles 10+ concurrent operations

### Functional Metrics
- **Geometry Creation**: All basic shapes work
- **Component Connection**: Proper dataflow
- **Parameter Setting**: Values update correctly
- **Document Management**: Save/load functions

### Integration Metrics
- **Agent Delegation**: Triage routes correctly
- **Multi-Step Workflows**: Complex operations complete
- **Error Recovery**: System recovers from failures
- **User Experience**: Intuitive and responsive

## Next Steps After Validation

Once all phases pass:

1. **Production Deployment**
   - Configure for production environment
   - Implement proper error monitoring
   - Add user authentication
   - Scale for multiple users

2. **Feature Enhancement**
   - Add Material and Structural agents
   - Implement AR visualization
   - Add database persistence
   - Create web interface

3. **Performance Optimization**
   - Profile and optimize bottlenecks
   - Implement caching strategies
   - Add load balancing
   - Monitor resource usage

4. **Documentation**
   - Create user guides
   - Document API endpoints
   - Write deployment guides
   - Maintain troubleshooting docs

## Conclusion

This integration test guide provides comprehensive validation of the Vizor Agents system. Following these phases ensures a robust, reliable AI-powered bridge design system that seamlessly integrates with Grasshopper.

The successful completion of all phases demonstrates:
- ✅ **Working MCP Integration**: Python agents control Grasshopper
- ✅ **Multi-Agent Orchestration**: Triage agent delegates properly
- ✅ **Real-World Functionality**: Complex bridge design scenarios
- ✅ **Production Readiness**: Error handling and performance

Your AI-powered parametric design system is ready for real-world bridge design projects! 🌉🤖