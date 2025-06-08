# Grasshopper MCP Bridge Component (Simplified)

This simplified C# component acts as a bridge/client that connects Grasshopper to the Python MCP server. Based on the working SimpleMCPBridge template, it polls the MCP server for commands and executes them on the Grasshopper canvas.

## Features

- **MCP Client/Bridge** - Connects to Python MCP server as HTTP client
- **Command Polling** - Continuously polls MCP server for pending commands  
- **Real Grasshopper Operations** - Executes MCP commands on actual Grasshopper canvas
- **Thread-safe operations** using Rhino UI thread synchronization
- **Component creation** supporting 3 basic types for testing (Point, Number, Panel)
- **Parameter connection system** for wiring components together
- **Bidirectional communication** - Reports command results back to MCP server
- **Comprehensive logging** for debugging and monitoring

## How It Works

The bridge component operates as a **client** that connects to the Python MCP server:

1. **Polls MCP Server** - Continuously checks for pending commands
2. **Receives Commands** - Gets component creation/manipulation commands  
3. **Executes on Canvas** - Performs actual Grasshopper operations
4. **Reports Results** - Sends success/failure status back to MCP server

## Supported Commands

The bridge can execute the following commands received from the MCP server:

### Component Operations
- `add_component` - Create components on the Grasshopper canvas
- `connect_components` - Wire components together via parameters
- `set_component_value` - Set values on component parameters  
- `clear_document` - Remove all components from the canvas
- `save_document` - Save the Grasshopper document

## Building the Component

### Prerequisites

1. **Rhino 7 or 8** installed
2. **Visual Studio 2019+** or **Visual Studio Code** with C# extension  
3. **.NET Framework 4.8** or later

> **⚠️ Important**: If you get build errors about missing references, see [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for fixing path issues.

### Build Steps

1. **Open project in Visual Studio**:
   ```
   Open VizorAgents.GH_MCP.csproj in Visual Studio
   ```

2. **Restore NuGet packages**:
   ```
   Right-click solution → Restore NuGet Packages
   ```

3. **Build the project**:
   ```
   Build → Build Solution (Ctrl+Shift+B)
   ```

4. **Install component**:
   The post-build event automatically copies the .dll to your Grasshopper Libraries folder:
   ```
   %APPDATA%\Grasshopper\Libraries\
   ```

### Alternative: Command Line Build

If you prefer command line:

```bash
# Navigate to the project directory
cd src/bridge_design_system/mcp/GH_MCP/

# Restore packages
dotnet restore

# Build the project
dotnet build --configuration Release
```

## Usage

### In Grasshopper

1. **Add the bridge component**:
   - Open Grasshopper
   - Find "MCP Bridge" in Params → Util category  
   - Drag it onto the canvas

2. **Configure the bridge**:
   - Connect a `Boolean Toggle` to the "Connect" (C) input
   - Optionally connect a `Text Panel` with MCP server URL to "Server" (S) input (default: http://localhost:8001)
   - Set the toggle to `True` to start the bridge

3. **Monitor bridge activity**:
   - The "Status" (S) output shows connection state
   - The "Log" (L) output shows bridge operations and errors  
   - The "Commands" (C) output shows commands received from MCP server

### From Python (MCP Server)

The bridge connects to the Python MCP server:

```python
# Start the Python MCP server (the bridge connects to this)
uv run python -m bridge_design_system.main --start-streamable-http

# Test the geometry agent (which uses the MCP server)
uv run python test_geometry_agent_safe.py
```

## API Examples

### Add a Point Component

```bash
curl -X POST http://localhost:8080/grasshopper/add_component \
  -H "Content-Type: application/json" \
  -d '{
    "type": "add_component",
    "parameters": {
      "component_type": "point",
      "x": 100,
      "y": 200
    }
  }'
```

### Get All Components

```bash
curl http://localhost:8080/grasshopper/get_all_components
```

### Health Check

```bash
curl http://localhost:8080/health
```

## Integration with MCP

This component works seamlessly with the Python MCP streamable-http server:

1. **Start Grasshopper** and add the MCP Server component
2. **Enable the server** by setting Start=True
3. **Run the Python MCP server**:
   ```bash
   uv run python -m bridge_design_system.main --start-streamable-http
   ```
4. **Test with an agent**:
   ```bash
   uv run python test_geometry_agent_safe.py
   ```

## Implementation Details

### Supported Component Types

The component can create the following Grasshopper component types via the `add_component` endpoint:

| Component Type | Aliases | Description |
|----------------|---------|-------------|
| `point` | `pt` | Point parameter |
| `number` | `num` | Number slider |
| `text` | `string` | Text parameter |
| `boolean` | `bool` | Boolean toggle |
| `integer` | `int` | Integer parameter |
| `vector` | `vec` | Vector parameter |
| `line` | | Line parameter |
| `circle` | | Circle parameter |
| `curve` | | Curve parameter |
| `surface` | `srf` | Surface parameter |
| `brep` | | Brep parameter |
| `mesh` | | Mesh parameter |
| `geometry` | `geo` | Generic geometry parameter |
| `panel` | | Text panel |
| `button` | | Button object |

### Thread Safety

All Grasshopper document operations are properly synchronized using `Rhino.RhinoApp.InvokeOnUiThread()` to ensure thread safety when called from HTTP request handlers.

### Parameter Management

- **Set Values**: Supports setting values on Number, String, Boolean, and Integer parameters
- **Connections**: Wire output parameters to input parameters between components
- **Data Flow**: Automatic solution scheduling after modifications

## Architecture

```
AI Agent → smolagents MCPClient → Python MCP Server → Command Queue
                                           ↓
                    Grasshopper Bridge ← HTTP Polling ← Command Queue
                           ↓
                  Real Grasshopper API
                (GH_Document.AddObject,
                 IGH_Param.AddSource, etc.)
                           ↓
                  Grasshopper Canvas
```

## Troubleshooting

### Component not appearing in Grasshopper
- Check that the .dll was copied to `%APPDATA%\Grasshopper\Libraries\`
- Restart Grasshopper completely
- Check Windows Event Log for assembly loading errors

### HTTP server won't start
- Ensure the port isn't already in use
- Check Windows Firewall settings
- Run Rhino as Administrator if needed

### Connection timeouts
- Verify the port number matches between Python and Grasshopper
- Check that no firewall is blocking localhost connections
- Look at the component's Log output for error messages

## Security Notes

- This HTTP server only binds to `localhost` for security
- CORS headers allow browser-based clients to connect
- No authentication is implemented - suitable for local development only
- Consider network security if deploying in shared environments

## Development

### Extending the Component

To add new endpoints:

1. Add a new case in the `ProcessRequest` method
2. Create a corresponding `Handle*` method
3. Update the MCP server's tool definitions in Python
4. Test with the MCP integration

### Thread Safety

The component uses:
- `lock (_lock)` for log message synchronization
- `async/await` for HTTP operations
- Thread-safe collections for component tracking

## License

This component is part of the VizorAgents bridge design system.