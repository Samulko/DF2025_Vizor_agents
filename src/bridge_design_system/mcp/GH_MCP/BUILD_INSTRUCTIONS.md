# Build Instructions for Grasshopper MCP Bridge

## Fixing Build Errors

If you're getting errors about missing Grasshopper/Rhino references, follow these steps:

### 1. Find Your Rhino Installation

The project expects Rhino 7 to be installed at `C:\Program Files\Rhino 7\`.

Check your actual Rhino installation path:
- **Rhino 7**: Usually `C:\Program Files\Rhino 7\`
- **Rhino 8**: Usually `C:\Program Files\Rhino 8\`
- **Rhino 6**: Usually `C:\Program Files\Rhinoceros 5 (64-bit)\`

### 2. Update Project References

Open `VizorAgents.GH_MCP.csproj` and update the hint paths to match your installation:

```xml
<!-- For Rhino 7 (default) -->
<Reference Include="Grasshopper">
  <HintPath>$(ProgramFiles)\Rhino 7\Plug-ins\Grasshopper\Grasshopper.dll</HintPath>
  <Private>false</Private>
</Reference>

<!-- For Rhino 8 -->
<Reference Include="Grasshopper">
  <HintPath>$(ProgramFiles)\Rhino 8\Plug-ins\Grasshopper\Grasshopper.dll</HintPath>
  <Private>false</Private>
</Reference>
```

### 3. Alternative: Direct Path References

If the above doesn't work, use explicit paths:

```xml
<Reference Include="Grasshopper">
  <HintPath>C:\Program Files\Rhino 7\Plug-ins\Grasshopper\Grasshopper.dll</HintPath>
  <Private>false</Private>
</Reference>
<Reference Include="GH_IO">
  <HintPath>C:\Program Files\Rhino 7\Plug-ins\Grasshopper\GH_IO.dll</HintPath>
  <Private>false</Private>
</Reference>
<Reference Include="RhinoCommon">
  <HintPath>C:\Program Files\Rhino 7\System\RhinoCommon.dll</HintPath>
  <Private>false</Private>
</Reference>
```

### 4. Building the Component

After fixing the references:

1. **In Visual Studio**:
   - Right-click the project → Build
   - Output will be in `bin\Debug\` or `bin\Release\`

2. **From Command Line**:
   ```bash
   cd src/bridge_design_system/mcp/GH_MCP/
   dotnet build
   ```

### 5. Installing the Component

The built .gha file will be automatically copied to:
```
%APPDATA%\Grasshopper\Libraries\
```

If not, manually copy `VizorAgents.GH_MCP.gha` to that folder.

### 6. Restart Grasshopper

Close and reopen Grasshopper to load the new component.

## What the Bridge Does

This simplified MCP Bridge component:
- **Connects** to the Python MCP test server as a client
- **Polls** for commands every second
- **Executes** commands on the Grasshopper canvas
- **Reports** results back to the server

## Component Features

- Only 3 component types for testing: Point, Number, Panel
- Simple clear document command
- Minimal dependencies to avoid build issues
- Based on the working SimpleMCPBridge template

## Troubleshooting

### "Cannot find Grasshopper.dll"
- Check your Rhino installation path
- Update the .csproj file with correct paths
- Make sure Rhino is installed

### "Type or namespace not found"
- Verify all three references are correct:
  - Grasshopper.dll
  - GH_IO.dll
  - RhinoCommon.dll

### Component doesn't appear in Grasshopper
- Check the output folder for the .gha file
- Copy it manually to `%APPDATA%\Grasshopper\Libraries\`
- Restart Grasshopper completely