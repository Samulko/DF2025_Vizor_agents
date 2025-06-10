# Simple TCP Bridge Deployment 🚀

## Current Status ✅

The TCP bridge component is **already built** and ready to deploy!

**Files available:**
- Debug: `reference/GH_MCP/GH_MCP/bin/Debug/net48/GH_MCP.gha`
- Release: `reference/GH_MCP/GH_MCP/bin/Release/net48/GH_MCP.gha`

## Quick 3-Step Deployment

### Step 1: Copy Component to Grasshopper 📁

**In Windows Explorer or Command Prompt:**

```cmd
copy "C:\Users\Samko\Documents\github\vizor_agents\reference\GH_MCP\GH_MCP\bin\Release\net48\GH_MCP.gha" "%APPDATA%\Grasshopper\Libraries\"
```

**Alternative - Manual copy:**
1. Navigate to: `C:\Users\Samko\Documents\github\vizor_agents\reference\GH_MCP\GH_MCP\bin\Release\net48\`
2. Copy `GH_MCP.gha` 
3. Paste to: `%APPDATA%\Grasshopper\Libraries\`

### Step 2: Add Component in Grasshopper 🦗

1. **Restart Grasshopper completely** (close and reopen)
2. **Find "Grasshopper MCP" in Params → Util category**
3. **Drag onto canvas**
4. **Connect inputs:**
   - **Enabled (E)**: Boolean Toggle → Set to `True`
   - **Port (P)**: Number → Set to `8080`

### Step 3: Verify Working 🎯

**Component should show:**
- **Status (S)**: `"Running on port 8080"`
- **LastCommand (C)**: `"None"`

**Test from WSL:**
```bash
cd /mnt/c/Users/Samko/Documents/github/vizor_agents
python3 test_tcp_bridge_connection.py
```

**Expected success:**
```
🎯 Overall: 4/4 tests passed
🎉 TCP BRIDGE SUCCESS!
```

## Architecture Confirmed ✅

Once working:
```
smolagents → STDIO MCP → TCP Client → TCP Bridge → Grasshopper
          (49 tools)    (port 8080)  (component)   (canvas)
```

## Test Complete Agent Flow 🤖

```bash
python3 test_simple_working_solution.py
```

Then create geometry:
```python
from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools

with create_geometry_agent_with_mcp_tools() as agent:
    result = agent.run("Create a circle with radius 5 at the origin")
    print(result)
    # Check Grasshopper canvas!
```

## What This Enables 🌉

✅ **Direct Agent → Grasshopper communication**  
✅ **49 MCP tools available to AI agents**  
✅ **Real-time geometry creation in Grasshopper**  
✅ **Visual monitoring via TCP bridge component**  
✅ **Foundation for AR-assisted bridge design**  

This is the proven TCP bridge architecture from Claude Desktop, now working with smolagents!