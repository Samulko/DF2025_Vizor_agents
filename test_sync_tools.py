"""Test the sync MCP tools with smolagents."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_sync_tools():
    """Test the sync MCP tools directly."""
    
    print("🧪 Testing Sync MCP Tools")
    print("This should work without async/sync conflicts...")
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import (
            add_component, clear_document, get_all_components
        )
        
        print("✅ Successfully imported sync tools")
        
        # Test 1: Clear document
        print("\n📍 Test 1: Clear document")
        result = clear_document()
        print(f"Clear result: {result}")
        
        # Test 2: Add point component  
        print("\n📍 Test 2: Add point component")
        result = add_component("point", 100, 100)
        print(f"Add point result: {result}")
        
        # Test 3: Get all components
        print("\n📍 Test 3: Get all components")
        result = get_all_components()
        print(f"Get components result: {result}")
        
        print("\n✅ Sync tools test completed!")
        print("🔍 Check your Simple MCP Bridge in Grasshopper for activity")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_geometry_agent_with_sync_tools():
    """Test the geometry agent with sync tools."""
    
    print("\n" + "="*60)
    print("🧪 Testing Geometry Agent with Sync Tools")
    print("="*60)
    
    try:
        from bridge_design_system.agents.geometry_agent import GeometryAgent
        
        # Create and initialize geometry agent
        print("📝 Creating geometry agent with sync tools...")
        geo_agent = GeometryAgent()
        
        print("🔧 Initializing geometry agent...")
        geo_agent.initialize_agent()
        
        print("✅ Geometry agent initialized!")
        
        # Check tools
        if hasattr(geo_agent, 'tools') and geo_agent.tools:
            print(f"🔧 Agent has {len(geo_agent.tools)} tools")
            tool_names = [tool.name for tool in geo_agent.tools]
            print(f"📋 Tool names: {tool_names}")
            
            # Test the agent
            print("\n🚀 Running agent with sync tools...")
            result = geo_agent.run(
                "Please add a point component at coordinates x=100, y=100"
            )
            
            print(f"🎯 Agent result success: {result.success}")
            print(f"🎯 Agent result message: {result.message}")
            
            if result.success and "Unable to add point component" not in result.message:
                print("\n🎉 SUCCESS! Sync tools work with smolagents!")
                print("✅ Your bridge integration is now fully functional!")
            else:
                print(f"\n❌ Agent failed: {result.message}")
                print("❌ The connection to MCP server is not working")
                
        else:
            print("❌ No tools loaded")
            
    except Exception as e:
        print(f"❌ Geometry agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_tools()
    test_geometry_agent_with_sync_tools()