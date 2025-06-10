# Grasshopper Bridge Testing Instructions

This guide helps you test the Grasshopper MCP Bridge component with the streamable-http MCP server.

**Current Status**: ✅ **95% Complete** - Authentication and session management working. Final server fix needed for command execution.

## Setup

### 1. Compile the Grasshopper Component

1. **Open Visual Studio** (or Visual Studio Code with C# extension)
2. **Open the project**: `VizorAgents.GH_MCP.csproj`
3. **Fix references if needed**: See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) if you get build errors
4. **Build the project**: Build → Build Solution (Ctrl+Shift+B)
5. **Verify installation**: The .gha file should be copied to `%APPDATA%\Grasshopper\Libraries\`

### 2. Start the MCP Streamable-HTTP Server

```bash
# Navigate to project root
cd /path/to/vizor_agents

# Start the official MCP streamable-http server
python -m bridge_design_system.main --start-streamable-http --mcp-port 8001
```

The server will start on `http://localhost:8001/mcp/` with official MCP protocol support.

### 3. Setup Grasshopper

1. **Open Rhino** and start **Grasshopper**
2. **Find the component**: Look for "Simple MCP Bridge" in the component library
3. **Add to canvas**: Drag the component onto the Grasshopper canvas
4. **Setup inputs**:
   - Connect a **Boolean Toggle** to "Connect" input  
   - Server URL defaults to "http://localhost:8001" (MCP server endpoint)

## Supported MCP Tools

The bridge supports the full set of MCP tools:
- **add_component** - Create components (point, line, circle, slider, panel, etc.)
- **connect_components** - Wire components together
- **get_all_components** - List all components in document
- **set_component_value** - Set parameter values
- **clear_document** - Clear the canvas
- **save_document** - Save the document

## Testing Phases

### Phase 1: Basic Connectivity Test

**Goal**: Verify the bridge can connect to the test server

1. **Start test server** (see Setup step 2)
2. **In Grasshopper**: Set the Boolean Toggle to `True`
3. **Check outputs**:
   - **Status** should show "Connected to MCP server at http://localhost:8001"
   - **Log** should show connection messages
4. **Verify in terminal**: Test server should show polling activity

✅ **Success**: Bridge shows "Connected" and server logs show polling requests  
❌ **Failure**: Check firewall, port conflicts, or server URL

### Phase 2: MCP Tool Integration Test

**Goal**: Test sync MCP tools integration

1. **Ensure bridge is connected** (Phase 1 complete)
2. **Test sync MCP tools**:
   ```bash
   # In another terminal
   cd /path/to/vizor_agents
   python test_sync_tools.py
   ```
3. **Expected behavior**:
   - Session authentication should work ✅
   - Commands should be sent to MCP server ✅
   - Bridge should receive polling commands ✅
   - **Current Issue**: Server task group error prevents execution

✅ **Success**: Commands reach bridge, authentication works  
🔧 **Current Status**: 95% complete, server fix needed for execution

### Phase 3: Multiple Components Test

**Goal**: Test creating multiple different components

1. **Run batch test**:
   ```bash
   uv run python test_grasshopper_bridge.py
   # Choose option 3: Add Multiple Components
   ```
2. **Expected results**:
   - Point component at (100, 100)
   - Number slider at (300, 100)  
   - Text panel at (200, 300)

✅ **Success**: Multiple components appear in correct positions  
❌ **Failure**: Check component type mapping and positioning

### Phase 4: Document Management Test

**Goal**: Test clearing and managing the document

1. **Clear document test**:
   ```bash
   uv run python test_grasshopper_bridge.py
   # Choose option 4: Clear Document
   ```
2. **Expected result**: All components except the bridge should be removed

✅ **Success**: Canvas is cleared except for MCP Bridge component  
❌ **Failure**: Check document access and component removal logic

### Phase 5: Full Integration Test

**Goal**: Test complete workflow

1. **Run full sequence**:
   ```bash
   uv run python test_grasshopper_bridge.py
   # Choose option 8: Run Full Test Sequence
   ```
2. **Watch the sequence**:
   - Document clear
   - Point component creation
   - Number slider creation
   - Batch component creation
   - Parameter value setting

✅ **Success**: All commands execute successfully in sequence  
❌ **Failure**: Identify which step fails and debug

## Monitoring and Debugging

### Real-time Monitoring

**Monitor bridge activity**:
```bash
uv run python test_grasshopper_bridge.py monitor
```

This shows real-time command processing and results.

### Debug Information

**Check bridge status**:
- **Grasshopper Log output**: Shows detailed bridge operations
- **Commands output**: Shows received commands from server
- **Status output**: Shows connection state

**Check server status**:
- **Terminal output**: Shows command queuing and results
- **HTTP GET**: `http://localhost:8001/test/status` (in browser)

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Connection Failed** | Status shows "Not connected" | Check test server is running on port 8001 |
| **No Commands Received** | Commands output empty | Verify polling is working, check server logs |
| **Components Not Created** | Commands received but no canvas changes | Check Grasshopper document access and UI thread |
| **Position Issues** | Components created at wrong positions | Verify coordinate system and Pivot setting |
| **Parameter Errors** | Component creation fails | Only 3 types supported: point, number, panel |

## Test Results Checklist

**Basic Functionality** ✅/❌
- [ ] Bridge connects to test server
- [ ] Commands are received and logged
- [ ] Point components can be created
- [ ] Number sliders can be created
- [ ] Components appear at correct positions

**Advanced Functionality** ✅/❌
- [ ] Multiple component types work
- [ ] Document can be cleared
- [ ] Parameter values can be set
- [ ] Component connections work (if tested)
- [ ] Error handling works properly

**Performance & Reliability** ✅/❌
- [ ] Polling is consistent (no missed commands)
- [ ] Commands execute in reasonable time (<5 seconds)
- [ ] No memory leaks during extended use
- [ ] Bridge handles server disconnections gracefully

## Next Steps

After successful testing:

1. **Integration with Real MCP**: Modify the Python MCP server to include the polling endpoints
2. **Geometry Agent Testing**: Test with actual geometry agent commands
3. **Error Handling**: Test error scenarios (server down, invalid commands, etc.)
4. **Performance Optimization**: Adjust polling rates and optimize for real usage

## Troubleshooting Commands

**Restart test server**:
```bash
# Ctrl+C to stop, then restart
uv run python src/bridge_design_system/mcp/grasshopper_bridge_test_server.py
```

**Reset bridge**:
- Set Boolean Toggle to `False`, then `True` again

**Clear Grasshopper**:
- File → New (or use clear document test)

**Check network**:
```bash
curl http://localhost:8001/test/status
```