"""Test the geometry agent and MCP bridge integration."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_geometry_agent_direct():
    """Test the geometry agent which connects to MCP successfully."""
    
    print("🧪 Testing Geometry Agent MCP Integration (Direct)")
    print("The geometry agent successfully connected to MCP!")
    print("Now testing if we can make it use the MCP tools...")
    
    try:
        from bridge_design_system.agents.geometry_agent import GeometryAgent
        
        # Create and initialize geometry agent
        print("📝 Creating geometry agent...")
        geo_agent = GeometryAgent()
        
        print("🔧 Initializing geometry agent...")
        geo_agent.initialize_agent()
        
        print("✅ Geometry agent initialized successfully!")
        
        # Check if the agent has tools
        if hasattr(geo_agent, '_agent') and geo_agent._agent:
            print(f"🔧 Agent has {len(geo_agent.tools)} tools available")
            tool_names = [tool.name for tool in geo_agent.tools]
            print(f"📋 Tool names: {tool_names}")
            
            # Test the agent by running it with a simple request
            print("\n📍 Testing direct agent run...")
            
            print("🚀 Running agent with geometry request...")
            result = geo_agent.run(
                "Please add a point component to the Grasshopper canvas at coordinates x=100, y=100. "
                "Use the add_component tool with component_type='point'."
            )
            
            print(f"🎯 Agent result success: {result.success}")
            print(f"🎯 Agent result message: {result.message}")
            
            if result.success:
                print("\n✅ Agent run completed successfully!")
                print("🔍 Check your Simple MCP Bridge in Grasshopper for new point component")
                print("🔍 Check your Python MCP server logs for command execution")
            else:
                print(f"\n❌ Agent run failed: {result.message}")
            
        else:
            print("❌ Agent not properly initialized")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_geometry_agent_direct()