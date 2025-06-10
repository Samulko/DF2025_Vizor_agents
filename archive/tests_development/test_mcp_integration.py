"""Test script for MCP streamable-http integration."""
import asyncio
from smolagents import MCPClient

async def test_mcp_connection():
    """Test the MCP streamable-http connection."""
    print("Testing MCP streamable-http integration...")
    
    try:
        # Create MCPClient with streamable-http transport
        config = {
            "url": "http://localhost:8001/mcp",
            "transport": "streamable-http"
        }
        
        print(f"Connecting to MCP server at {config['url']}...")
        
        # Use MCPClient context manager
        with MCPClient(config) as tools:
            print(f"✅ Connected! Found {len(tools)} tools:")
            
            # List all available tools
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test a simple tool if available
            if tools:
                print("\nTesting 'get_all_components' tool...")
                result = tools[2].forward()  # get_all_components is usually the 3rd tool
                print(f"Result: {result}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. The MCP server is running (--start-streamable-http)")
        print("2. The Grasshopper server is accessible")
        print("3. The MCP server URL is correct")

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())