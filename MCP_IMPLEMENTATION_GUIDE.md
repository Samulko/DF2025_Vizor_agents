# MCP HTTP Server Implementation Guide

This guide provides a complete working MCP (Model Context Protocol) server over HTTP implementation for the vizor_agents project, solving the "Task group is not initialized" errors from StreamableHTTPSessionManager.

## Overview

We have implemented **three different MCP server approaches** to ensure compatibility and reliability:

1. **FastMCP Server** (Recommended) - Uses official FastMCP framework
2. **Manual HTTP Server** (Fallback) - Pure HTTP + JSON-RPC 2.0 implementation  
3. **Legacy StreamableHTTPSessionManager** (Deprecated) - Original implementation with known issues

## Implementation Details

### 1. FastMCP Server (Recommended)

**File:** `/src/bridge_design_system/mcp/fastmcp_server.py`

**Official Documentation:** [FastMCP GitHub](https://github.com/jlowin/fastmcp) | [FastMCP Docs](https://gofastmcp.com)

**Features:**
- Uses **FastMCP v2** - The standard framework for working with MCP
- **Pythonic Interface**: High-level, clean API design
- **Automatic Protocol Handling**: JSON-RPC 2.0, session management, error handling
- **Multiple Transports**: Streamable HTTP, SSE, STDIO, In-Memory
- **Production Ready**: Authentication, proxying, composition, testing tools
- **Bridge Mode**: Custom integration for Grasshopper component polling
- **Advanced Features**: OpenAPI generation, FastAPI integration, proxy servers

**Why FastMCP?**
> FastMCP aims to be the **simplest path to production** for MCP servers. While the core MCP protocol requires significant boilerplate, FastMCP handles all complex protocol details so you can focus on building great tools.

**Key Advantages:**
- 🚀 **Fast Development**: Minimal boilerplate - decorating functions is often all you need
- 🍀 **Simple**: High-level interface means less code 
- 🐍 **Pythonic**: Feels natural to Python developers
- 🔍 **Complete**: Comprehensive platform from dev to production

**Usage:**
```python
from bridge_design_system.mcp import create_grasshopper_mcp_server

# Create server
server = create_grasshopper_mcp_server(
    grasshopper_url="http://localhost:8080",
    port=8001,
    bridge_mode=True,
    stateless=False
)

# Run server
server.run()
```

**CLI (Recommended - Uses FastMCP when available):**
```bash
python -m bridge_design_system.main --start-streamable-http --mcp-port 8001
```

**Direct CLI:**
```bash
python -m bridge_design_system.cli.fastmcp_server --port 8001 --bridge-mode
```

**Endpoints:**
- `POST/GET http://localhost:8001/mcp` - MCP protocol endpoint
- `GET http://localhost:8001/grasshopper/pending_commands` - Bridge polling
- `POST http://localhost:8001/grasshopper/command_result` - Bridge results
- `GET http://localhost:8001/grasshopper/status` - Bridge status

### 2. Manual HTTP Server (Fallback)

**File:** `/src/bridge_design_system/mcp/manual_http_server.py`

**Features:**
- Pure HTTP + JSON-RPC 2.0 implementation
- No external MCP dependencies beyond basic types
- Server-Sent Events (SSE) support
- Full MCP protocol compliance
- Session management with cleanup

**Usage:**
```python
from bridge_design_system.mcp import create_manual_mcp_server

# Create server
server = create_manual_mcp_server(
    grasshopper_url="http://localhost:8080",
    port=8001,
    bridge_mode=True
)

# Run server
server.run()
```

**CLI:**
```bash
python -m bridge_design_system.cli.manual_mcp_server --port 8001 --bridge-mode
```

**Endpoints:**
- `POST http://localhost:8001/mcp` - JSON-RPC requests
- `GET http://localhost:8001/mcp` - SSE connection
- `GET http://localhost:8001/grasshopper/pending_commands` - Bridge polling
- `POST http://localhost:8001/grasshopper/command_result` - Bridge results
- `GET http://localhost:8001/grasshopper/status` - Bridge status
- `GET http://localhost:8001/health` - Health check

### 3. Legacy StreamableHTTPSessionManager (Deprecated)

**File:** `/src/bridge_design_system/mcp/streamable_http_server.py`

**Issues:**
- "Task group is not initialized" errors
- Complex session manager lifecycle
- Dependency on StreamableHTTPSessionManager

**Status:** Deprecated - use FastMCP or Manual server instead

## MCP Protocol Implementation

All servers implement the official MCP protocol with JSON-RPC 2.0:

### Protocol Flow

1. **Initialize:** Client sends `initialize` request
2. **Capabilities:** Server responds with available tools/resources
3. **Tool Listing:** Client requests `tools/list`
4. **Tool Execution:** Client sends `tools/call` requests
5. **Streaming:** Server uses SSE for real-time responses

### JSON-RPC Message Format

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "add_component",
    "arguments": {
      "component_type": "point",
      "x": 100,
      "y": 200
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool 'add_component' executed successfully. Result: {...}"
      }
    ]
  }
}
```

### Available Tools

All implementations provide these Grasshopper tools:

1. **add_component** - Add component to canvas
2. **connect_components** - Connect two components
3. **get_all_components** - List all components
4. **set_component_value** - Set parameter value
5. **clear_document** - Clear all components
6. **save_document** - Save document

## Bridge vs Direct Mode

### Bridge Mode (Recommended)
- Commands are queued for Grasshopper bridge component
- Bridge polls `/grasshopper/pending_commands` endpoint
- Results returned via `/grasshopper/command_result` endpoint
- Allows for complex Grasshopper operations

### Direct Mode
- Commands sent directly to Grasshopper HTTP server
- Immediate execution (when Grasshopper server available)
- Simpler but limited functionality

## smolagents Integration

The servers work seamlessly with smolagents:

```python
from smolagents import CodeAgent
from bridge_design_system.mcp import get_grasshopper_tools

# Get tools from MCP server
tools = get_grasshopper_tools("http://localhost:8001/mcp")

# Use with agent
agent = CodeAgent(tools=tools, model="gpt-4")
result = agent.run("Create a point at coordinates (100, 200, 0)")
```

## Server-Sent Events (SSE)

Both FastMCP and Manual servers support SSE for streaming:

**Connection:**
```javascript
const eventSource = new EventSource('http://localhost:8001/mcp');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('MCP Event:', data);
};
```

**Event Types:**
- `connection` - Initial connection
- `heartbeat` - Keep-alive signals
- `response` - JSON-RPC responses
- `notification` - Server notifications

## Error Handling

### Common Error Codes

- `-32600` - Invalid Request
- `-32601` - Method not found
- `-32602` - Invalid params
- `-32603` - Internal error
- `-32002` - Session not initialized

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "error": {
    "code": -32601,
    "message": "Method not found: unknown_method",
    "data": "Additional error details"
  }
}
```

## Session Management

### FastMCP Server
- Automatic session management via FastMCP
- Stateless or stateful modes supported
- Session cleanup handled internally

### Manual Server
- Custom session tracking with MCPSession class
- Session timeouts and cleanup
- Manual session lifecycle management

## Performance Considerations

### Resource Usage
- **FastMCP**: Lower overhead, optimized by FastMCP
- **Manual**: Higher control, custom optimization possible
- **Memory**: Sessions cleaned up automatically

### Scalability
- Single-threaded async processing
- Connection pooling for Grasshopper client
- Session limits for memory management

## Deployment

### Development
```bash
# Start FastMCP server
python -m bridge_design_system.cli.fastmcp_server --debug

# Start Manual server
python -m bridge_design_system.cli.manual_mcp_server --debug
```

### Production
```bash
# Production FastMCP server
python -m bridge_design_system.cli.fastmcp_server \
  --port 8001 \
  --bridge-mode \
  --log-level INFO

# Production Manual server  
python -m bridge_design_system.cli.manual_mcp_server \
  --port 8001 \
  --bridge-mode \
  --log-level INFO
```

### Docker Deployment
```dockerfile
FROM python:3.10

COPY . /app
WORKDIR /app

RUN pip install -e .

EXPOSE 8001

CMD ["python", "-m", "bridge_design_system.cli.fastmcp_server", "--port", "8001"]
```

## Testing

### Health Check
```bash
curl http://localhost:8001/health
```

### MCP Protocol Test
```bash
# Initialize session
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'

# List tools
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2", 
    "method": "tools/list"
  }'
```

### Bridge Status
```bash
curl http://localhost:8001/grasshopper/status
```

## Troubleshooting

### Common Issues

1. **"Task group is not initialized"**
   - Solution: Use FastMCP or Manual server instead of StreamableHTTPSessionManager

2. **Connection refused**
   - Check server is running: `curl http://localhost:8001/health`
   - Verify port is available: `netstat -an | grep 8001`

3. **Tool execution timeout**
   - Check Grasshopper server is running
   - Verify bridge mode configuration
   - Check bridge polling status

4. **JSON-RPC errors**
   - Verify request format matches specification
   - Check session initialization
   - Validate tool parameters

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python -m bridge_design_system.cli.fastmcp_server --debug --log-level DEBUG
```

### Log Analysis

Key log messages to monitor:
- Session initialization
- Tool execution requests
- Bridge command queuing
- Error responses
- Connection lifecycle

## Conclusion

This implementation provides a robust, working MCP HTTP server that:

1. ✅ **Solves StreamableHTTPSessionManager issues**
2. ✅ **Implements complete MCP protocol compliance**
3. ✅ **Provides multiple fallback options**
4. ✅ **Integrates seamlessly with smolagents**
5. ✅ **Supports both bridge and direct modes**
6. ✅ **Includes comprehensive error handling**
7. ✅ **Offers production-ready deployment options**

The FastMCP server is recommended for production use, with the Manual server as a reliable fallback that requires no external MCP dependencies beyond basic types.