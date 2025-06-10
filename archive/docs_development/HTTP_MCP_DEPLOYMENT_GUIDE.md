# HTTP MCP Deployment Guide

This guide walks you through deploying the **HTTP MCP transport solution** for connecting smolagents to SimpleMCPBridge.cs in Grasshopper.

## Architecture Overview

```
smolagents → HTTP MCP Server → SimpleMCPBridge.cs → Grasshopper
           (streamable-http)    (HTTP polling)     (UI thread)
           Port 8001           Every 1 second      Real Canvas
```

## Prerequisites

✅ **Python Environment**
- UV package manager installed
- Project dependencies installed: `uv pip install -e .`

✅ **DeepSeek API Key** 
- Added to `.env` file: `DEEPSEEK_API_KEY=your_key_here`
- Configured for geometry agent in `.env`

✅ **Grasshopper**
- Rhino 7 or 8 installed
- SimpleMCPBridge.cs component built and installed

## Step-by-Step Deployment

### Step 1: Build SimpleMCPBridge.cs Component

1. **Navigate to C# project:**
   ```bash
   cd src/bridge_design_system/mcp/GH_MCP/
   ```

2. **Build the component:**
   ```bash
   dotnet build --configuration Release
   ```

3. **Install in Grasshopper:**
   - The post-build event should automatically copy the `.dll` to:
   - `%APPDATA%\Grasshopper\Libraries\`
   - If not, manually copy `bin/Release/*.dll` to that folder

4. **Restart Grasshopper completely**

### Step 2: Start HTTP MCP Server

Open a terminal in the project root and run:

```bash
python -m bridge_design_system.main --start-streamable-http --mcp-port 8001
```

**Expected Output:**
```
🔍 Checking for FastMCP server availability...
✅ FastMCP framework available
🚀 Starting Clean FastMCP server (pure FastMCP architecture)
🎯 Architecture: FastMCP with @custom_route decorators for bridge endpoints
✅ Note: Using FastMCP @custom_route for bridge compatibility

Server running on http://127.0.0.1:8001
MCP endpoint: http://127.0.0.1:8001/mcp
Bridge endpoints:
- GET /grasshopper/pending_commands
- POST /grasshopper/command_result  
- GET /grasshopper/status
- GET /health
```

### Step 3: Configure Grasshopper SimpleMCPBridge

1. **Open Grasshopper**

2. **Add SimpleMCPBridge component:**
   - Find "Simple MCP Bridge" in Params → Util category
   - Drag it onto the canvas

3. **Configure inputs:**
   - **Connect (C)**: Connect a Boolean Toggle, set to `True`
   - **Server (S)**: Connect a Text Panel with `http://localhost:8001`

4. **Monitor outputs:**
   - **Status (S)**: Should show "Connected to http://localhost:8001"
   - **Log (L)**: Should show connection and polling messages
   - **Commands (C)**: Will show commands when they arrive

**Expected SimpleMCPBridge Logs:**
```
Connected to MCP server at http://localhost:8001
📥 Processing 0 commands on UI thread (normal when idle)
```

### Step 4: Test the Integration

Run the HTTP test suite:

```bash
python test_http_grasshopper_control.py
```

**Expected Results:**
```
✅ HTTP Server Connection
✅ HTTP MCP Tools Connection  
✅ HTTP Agent Creation
✅ Bridge Status Check
✅ HTTP Task Execution
✅ SimpleMCPBridge Integration

🎯 Overall: 6/6 tests passed
🎉 HTTP MCP SOLUTION SUCCESS!
```

### Step 5: Use HTTP Geometry Agent

Create a simple test script:

```python
from src.bridge_design_system.agents.http_geometry_agent import run_http_geometry_task

# This will send commands to SimpleMCPBridge.cs
result = run_http_geometry_task("Create a point at coordinates (0, 0, 0)")
print(result)
```

Or use the context manager:

```python
from src.bridge_design_system.agents.http_geometry_agent import create_http_geometry_agent_with_mcp_tools

with create_http_geometry_agent_with_mcp_tools() as agent:
    result = agent.run("Create a circle with radius 5")
    print(result)
```

## Monitoring and Debugging

### Check HTTP MCP Server Status

**Health Check:**
```bash
curl http://localhost:8001/health
```

**Bridge Status:**
```bash
curl http://localhost:8001/grasshopper/status
```

**Pending Commands (what SimpleMCPBridge polls):**
```bash
curl http://localhost:8001/grasshopper/pending_commands
```

### SimpleMCPBridge Component Debugging

**Status Indicators:**
- **Green Status**: "Connected to http://localhost:8001"
- **Active Logs**: Regular polling messages every second
- **Command Activity**: Commands appear in Commands output

**Common Issues:**
- **Red Status**: Check if HTTP MCP server is running
- **No Commands**: Verify agent is sending tasks
- **Connection Timeouts**: Check Windows Firewall settings

### Server Logs

The HTTP MCP server provides detailed logging:
- Connection events
- Tool executions  
- Bridge polling activity
- Error messages

## Production Configuration

### Security Settings

For production deployment:

1. **Bind to specific IP:**
   ```bash
   # Modify server startup to bind to specific interface
   python -m bridge_design_system.main --start-streamable-http --mcp-port 8001 --host 192.168.1.100
   ```

2. **Firewall Rules:**
   - Allow port 8001 for localhost connections
   - Restrict external access if not needed

### Performance Tuning

**SimpleMCPBridge Polling:**
- Default: 1 second intervals
- Modify in `SimpleMCPBridge.cs` line 88: `new Timer(PollServer, null, 0, 1000)`

**Agent Configuration:**
- Use DeepSeek for cost efficiency (21x cheaper than Claude)
- Configure in `.env`: `GEOMETRY_AGENT_PROVIDER=deepseek`

## Troubleshooting

### Common Issues

**1. HTTP MCP Server Won't Start**
```bash
# Solution: Check port availability
netstat -an | grep 8001

# Solution: Try different port
python -m bridge_design_system.main --start-streamable-http --mcp-port 8002
```

**2. SimpleMCPBridge Can't Connect**
```bash
# Check server accessibility
curl http://localhost:8001/health

# Check Windows Firewall
# Add exception for Python.exe if needed
```

**3. Agent Gets "Connection Refused"**
- Ensure HTTP MCP server is running
- Verify URL in agent configuration
- Check Windows Firewall blocking localhost connections

**4. Commands Not Reaching Grasshopper**
- Check SimpleMCPBridge Status output
- Verify Connect=True in SimpleMCPBridge
- Look at SimpleMCPBridge Log output for errors

### Advanced Debugging

**Enable Debug Logging:**
```python
import logging
logging.getLogger('bridge_design_system').setLevel(logging.DEBUG)
```

**Manual Command Testing:**
```bash
# Send test command to bridge queue
curl -X POST http://localhost:8001/grasshopper/command_result \
  -H "Content-Type: application/json" \
  -d '{"id": "test-1", "result": "Test command"}'
```

## Success Indicators

✅ **HTTP MCP Server Running**: Health endpoint returns 200
✅ **SimpleMCPBridge Connected**: Status shows "Connected"  
✅ **Tools Available**: smolagents loads 49 tools via HTTP
✅ **Commands Flow**: Tasks from agent appear in SimpleMCPBridge logs
✅ **Grasshopper Integration**: Components appear on canvas

When all indicators are green, your HTTP MCP solution is fully operational and ready for AR-assisted bridge design workflows!

## Next Steps

Once the HTTP solution is working:

1. **Integrate with Triage Agent** for multi-agent workflows
2. **Add Material and Structural Agents** 
3. **Implement AR visualization** components
4. **Scale to multiple Grasshopper instances** if needed

The HTTP architecture provides a solid foundation for these advanced features.