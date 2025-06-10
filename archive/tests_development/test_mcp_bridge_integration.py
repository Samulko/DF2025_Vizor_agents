import asyncio
import json
import aiohttp

async def test_mcp_integration():
    """Test the MCP bridge integration by sending MCP tool calls."""
    
    async def send_mcp_tool(tool_name, arguments):
        """Send a tool call through MCP protocol."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/mcp",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                result = await response.json()
                print(f"Tool: {tool_name}, Result: {result}")
                return result
    
    print("🧪 Testing MCP Bridge Integration")
    print("Bridge should be polling and ready...")
    
    # Test 1: Clear document
    await send_mcp_tool("clear_document", {})
    
    # Test 2: Add point
    await send_mcp_tool("add_component", {
        "component_type": "point",
        "x": 100,
        "y": 100
    })
    
    # Test 3: Add slider
    await send_mcp_tool("add_component", {
        "component_type": "number", 
        "x": 200,
        "y": 100
    })

if __name__ == "__main__":
    asyncio.run(test_mcp_integration())