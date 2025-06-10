# Deploy TCP Bridge Instructions

## Current Status 🎯

✅ **STDIO MCP Server**: Working (49 tools loaded)  
✅ **TCP Client**: Ready (`communication.py` → port 8080)  
❌ **TCP Bridge**: Needs to be built and deployed  
❌ **Grasshopper Component**: Not installed  

## Quick Deployment Steps

### Step 1: Build TCP Bridge Component

**In Windows Command Prompt or PowerShell (NOT WSL):**

```cmd
cd C:\Users\Samko\Documents\github\vizor_agents\reference\GH_MCP\GH_MCP\
dotnet build --configuration Release
```

Expected output:
```
Build succeeded.
    0 Warning(s)
    0 Error(s)
```

### Step 2: Install in Grasshopper

1. **Find built files:**
   ```
   reference\GH_MCP\GH_MCP\bin\Release\net48\GH_MCP.gha
   ```

2. **Copy to Grasshopper Libraries:**
   ```cmd
   copy "bin\Release\net48\GH_MCP.gha" "%APPDATA%\Grasshopper\Libraries\"
   ```

3. **Restart Grasshopper completely**

### Step 3: Add TCP Bridge Component

1. **Open Grasshopper**
2. **Find "Grasshopper MCP" component in Params → Util**
3. **Drag onto canvas**
4. **Configure:**
   - **Enabled (E)**: Connect Boolean Toggle → Set to `True`
   - **Port (P)**: Connect Number → Set to `8080`

### Step 4: Verify TCP Bridge Status

Component outputs should show:
- **Status (S)**: `"Running on port 8080"`
- **LastCommand (C)**: `"None"` (initially)

### Step 5: Test Complete Flow

**In WSL, run:**
```bash
cd /mnt/c/Users/Samko/Documents/github/vizor_agents
python3 test_tcp_bridge_connection.py
```

Expected success:
```
🎯 Overall: 4/4 tests passed
🎉 TCP BRIDGE SUCCESS!
✅ TCP bridge architecture is working
✅ STDIO MCP → TCP bridge → Grasshopper flow functional
```

## Architecture Verification

Once working, you should see this flow:

```
smolagents → STDIO MCP → TCP Client → TCP Bridge → Grasshopper
          (49 tools)    (port 8080)  (GH component)  (canvas)
          ✅            ✅           ✅              ✅
```

## Test the Complete Agent Flow

```bash
python3 test_simple_working_solution.py
```

Should show:
```
✅ DeepSeek Model Config
✅ MCP Connection Simple  
✅ Simple Agent Creation
✅ Simple Task Execution
🎯 Overall: 4/4 tests passed
```

Then you can run:
```python
from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools

with create_geometry_agent_with_mcp_tools() as agent:
    result = agent.run("Create a point at coordinates (0, 0, 0)")
    print(result)
    # Check Grasshopper canvas for the point!
```

## Troubleshooting

**If TCP bridge won't start:**
- Check Grasshopper console for errors
- Verify port 8080 is not in use: `netstat -an | findstr 8080`
- Try different port (like 8081) in both component and `communication.py`

**If build fails:**
- Ensure .NET SDK installed
- Try in Visual Studio instead of command line
- Check Rhino/Grasshopper version compatibility

**If component not found:**
- Verify file copied to correct Grasshopper libraries folder
- Restart Grasshopper completely (close and reopen)
- Check Windows permissions on Libraries folder

## Next Steps After Success

1. **Integrate with Triage Agent** for multi-agent workflows
2. **Test complex bridge design patterns**
3. **Scale to full AR integration workflow**

The TCP bridge provides the proven foundation for AR-assisted bridge design!