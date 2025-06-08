"""Test the MCP bridge using smolagents framework."""
import asyncio
import logging
from smolagents import CodeAgent, MCPClient

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_smolagents():
    """Test the MCP integration using smolagents framework."""
    
    print("🧪 Testing MCP Bridge with smolagents")
    print("This uses the proper MCP client to send commands...")
    
    try:
        # Create MCP client pointing to our streamable HTTP server
        mcp_client = MCPClient("http://localhost:8001/mcp")
        
        # Initialize the client
        await mcp_client.initialize()
        
        print("✅ MCP client initialized successfully!")
        
        # List available tools
        tools = await mcp_client.list_tools()
        print(f"📋 Available tools: {[tool.name for tool in tools]}")
        
        # Test 1: Clear document
        print("\n📍 Test 1: Clearing document...")
        result = await mcp_client.call_tool("clear_document", {})
        print(f"Clear result: {result}")
        
        # Wait a moment for the bridge to process
        await asyncio.sleep(2)
        
        # Test 2: Add point component
        print("\n📍 Test 2: Adding point component...")
        result = await mcp_client.call_tool("add_component", {
            "component_type": "point",
            "x": 100,
            "y": 100
        })
        print(f"Add point result: {result}")
        
        # Wait a moment for the bridge to process
        await asyncio.sleep(2)
        
        # Test 3: Add number slider
        print("\n📍 Test 3: Adding number slider...")
        result = await mcp_client.call_tool("add_component", {
            "component_type": "number",
            "x": 200,
            "y": 100
        })
        print(f"Add slider result: {result}")
        
        print("\n🎉 Test completed! Check Grasshopper for new components.")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")
        print("\nThis might be because smolagents MCPClient doesn't support")
        print("streamable HTTP transport. Let's try the geometry agent instead...")
        
        # Fallback: Test with geometry agent
        await test_with_geometry_agent()

async def test_with_geometry_agent():
    """Test using the geometry agent which should have MCP integration."""
    
    print("\n🔄 Testing with GeometryAgent...")
    
    try:
        # Import and test geometry agent
        from bridge_design_system.agents.geometry_agent import GeometryAgent
        
        # Create geometry agent
        geo_agent = GeometryAgent()
        geo_agent.initialize_agent()
        
        print("✅ Geometry agent initialized!")
        
        # Test a simple command
        response = geo_agent.handle_geometry_request(
            "Please add a point component at coordinates (100, 100)"
        )
        
        print(f"Geometry agent response: {response.message}")
        
        if response.success:
            print("🎉 Geometry agent successfully handled the request!")
        else:
            print(f"❌ Geometry agent failed: {response.message}")
        
    except Exception as e:
        logger.error(f"Geometry agent test failed: {e}", exc_info=True)
        print(f"❌ Geometry agent test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_with_smolagents())