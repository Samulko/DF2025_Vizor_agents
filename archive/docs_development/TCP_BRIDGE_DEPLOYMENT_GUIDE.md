# TCP Bridge Deployment Guide

This guide deploys the **TCP Bridge architecture** for connecting smolagents to Grasshopper via the proven TCP bridge that worked with Claude Desktop.

## Architecture Overview

```
smolagents → STDIO MCP Server → TCP Client → TCP Bridge → Grasshopper
          (grasshopper_mcp.bridge)  (communication.py)  (GH_MCPComponent.cs)
           49 tools via STDIO      JSON over TCP      C# TCP server
```

## Why TCP Bridge (Not HTTP)

✅ **Proven Architecture**: Already worked with Claude Desktop as host  
✅ **Simple Protocol**: Direct JSON over TCP, no polling complexity  
✅ **Reliable**: TCP socket connection, no HTTP overhead  
✅ **Fast Response**: Direct request-response pattern  
✅ **No Bugs**: HTTP bridge had issues, TCP bridge is stable  

## Step-by-Step Deployment

### Step 1: Build TCP Bridge Component

1. **Navigate to TCP Bridge project:**
   ```bash
   cd reference/GH_MCP/GH_MCP/
   ```

2. **Build the C# component:**
   ```bash
   dotnet build --configuration Release
   ```

3. **Install in Grasshopper:**
   - Copy `bin/Release/*.dll` to `%APPDATA%\Grasshopper\Libraries\`
   - Restart Grasshopper completely

### Step 2: Configure TCP Bridge in Grasshopper

1. **Add TCP Bridge component:**
   - Open Grasshopper
   - Find "Grasshopper MCP" in Params → Util category
   - Drag onto canvas

2. **Configure TCP server:**
   - **Enabled (E)**: Connect Boolean Toggle, set to `True`
   - **Port (P)**: Connect Number, set to `8080` (default)

3. **Monitor outputs:**
   - **Status (S)**: Should show "Running on port 8080"
   - **LastCommand (C)**: Will show commands as they arrive

**Expected TCP Bridge Status:**
```
Running on port 8080
GrasshopperMCPBridge started on port 8080.
```

### Step 3: Test STDIO MCP Server Connection

The STDIO MCP server should already be working:

```bash
# Test STDIO MCP connection (should show 49 tools)
python test_simple_working_solution.py
```

**Expected Results:**
```
✅ DeepSeek Model Config
✅ MCP Connection Simple  
✅ Simple Agent Creation
✅ Simple Task Execution
🎯 Overall: 4/4 tests passed
```

### Step 4: Test TCP Bridge Communication

Create a simple TCP test:

```bash
python test_tcp_bridge_connection.py
```

This will:
1. Test direct TCP connection to `localhost:8080`
2. Send test command to TCP bridge
3. Verify Grasshopper receives and executes command
4. Confirm point appears on Grasshopper canvas

### Step 5: Test Complete Agent → TCP → Grasshopper Flow

```python
from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools

# This uses STDIO MCP → TCP Bridge → Grasshopper
with create_geometry_agent_with_mcp_tools() as agent:
    result = agent.run("Create a point at coordinates (0, 0, 0)")
    print(result)
    # Check Grasshopper canvas for the point!
```

## TCP Communication Protocol

### Command Format (Python → Grasshopper)
```json
{
  "type": "add_component",
  "parameters": {
    "type": "point",
    "x": 100,
    "y": 200,
    "z": 0
  }
}
```

### Response Format (Grasshopper → Python)
```json
{
  "success": true,
  "data": {
    "component_id": "12345",
    "message": "Point created successfully"
  }
}
```

### Supported Commands

The TCP bridge supports these commands:
- `add_component` - Create components (point, line, circle, etc.)
- `connect_components` - Connect component parameters
- `set_component_value` - Set parameter values
- `get_component_info` - Get component details
- `add_python3_script` - Add Python script components
- `set_python_script_content` - Modify Python scripts

## Monitoring and Debugging

### Check TCP Bridge Status

**In Grasshopper:**
- TCP Bridge Status output should show "Running on port 8080"
- LastCommand output shows recent commands

**Test TCP Connection:**
```bash
telnet localhost 8080
# Type: {"type": "test", "parameters": {}}
# Should get response from TCP bridge
```

### Debug TCP Communication

**Check if port is open:**
```bash
netstat -an | findstr 8080
# Should show: TCP 127.0.0.1:8080 LISTENING
```

**Monitor TCP traffic:**
- Use Wireshark on localhost interface
- Filter: tcp.port == 8080
- Watch JSON commands flowing

### Common Issues

**1. TCP Bridge Won't Start**
- Check Grasshopper console for errors
- Verify port 8080 is not in use
- Restart Grasshopper after installing component

**2. STDIO MCP Server Connection Fails**
- Run: `python test_simple_working_solution.py`
- Check if 49 tools are loaded
- Verify DeepSeek API key is working

**3. TCP Communication Timeout**
- Check Windows Firewall settings
- Verify localhost connections allowed
- Test with `telnet localhost 8080`

**4. Commands Not Reaching Grasshopper**
- Check TCP Bridge LastCommand output
- Verify JSON format in communication.py
- Test direct TCP connection

## Success Indicators

✅ **TCP Bridge Running**: Status shows "Running on port 8080"  
✅ **STDIO MCP Working**: 49 tools loaded successfully  
✅ **Agent Connection**: Agent can list available tools  
✅ **TCP Communication**: Commands reach TCP bridge  
✅ **Grasshopper Execution**: Components appear on canvas  

## Architecture Benefits

### vs HTTP Bridge:
- ✅ **No Polling**: Direct TCP connection, no 1-second delays
- ✅ **No HTTP Bugs**: TCP bridge is proven stable
- ✅ **Simple Protocol**: Just JSON over TCP socket
- ✅ **Fast Response**: Immediate command execution

### vs STDIO Direct:
- ✅ **Visual Monitoring**: TCP bridge component shows status
- ✅ **Grasshopper Integration**: Real components on canvas
- ✅ **Proven Architecture**: Worked with Claude Desktop

## Next Steps

Once TCP bridge is working:
1. **Integrate with Triage Agent** for multi-agent workflows
2. **Add specialized tools** for bridge design
3. **Scale to complex geometries** with multiple components
4. **Document proven patterns** for other integrations

The TCP bridge provides a solid, proven foundation for AR-assisted bridge design workflows!