#!/usr/bin/env python3
"""Test the geometry agent with the manual MCP server."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_geometry_agent():
    """Test the geometry agent with manual MCP server."""
    
    print("🧪 Testing Geometry Agent with Manual MCP Server")
    print("=" * 60)
    
    try:
        from bridge_design_system.agents.geometry_agent import GeometryAgent
        from bridge_design_system.config.settings import Settings
        
        # Update settings to use manual MCP server
        settings = Settings()
        settings.grasshopper_mcp_url = "http://localhost:8001"
        
        print("📝 Creating geometry agent...")
        geo_agent = GeometryAgent()
        
        print("🔧 Initializing geometry agent...")
        geo_agent.initialize_agent()
        
        print("✅ Geometry agent initialized!")
        
        # Check tools
        if hasattr(geo_agent, 'tools') and geo_agent.tools:
            print(f"🔧 Agent has {len(geo_agent.tools)} tools")
            tool_names = [tool.name for tool in geo_agent.tools]
            print(f"📋 Tool names: {tool_names}")
            
            # Test 1: Clear document
            print("\n📍 Test 1: Clear document")
            result = geo_agent.run("Clear the Grasshopper document")
            print(f"Result: {result.message}")
            
            # Test 2: Add a point
            print("\n📍 Test 2: Add a point")
            result = geo_agent.run("Add a point at coordinates x=150, y=150")
            print(f"Result: {result.message}")
            
            # Test 3: Add multiple components
            print("\n📍 Test 3: Add multiple components")
            result = geo_agent.run(
                "Add three components: a point at (200, 100), "
                "a circle at (300, 100), and a number slider at (100, 200)"
            )
            print(f"Result: {result.message}")
            
            # Test 4: Get all components
            print("\n📍 Test 4: List all components")
            result = geo_agent.run("List all components in the document")
            print(f"Result: {result.message}")
            
            print("\n✅ All tests completed!")
            
        else:
            print("❌ No tools loaded in geometry agent")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_sync_tools_directly():
    """Test sync MCP tools directly."""
    
    print("\n🧪 Testing Sync MCP Tools Directly")
    print("=" * 60)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import (
            add_component, clear_document, get_all_components, 
            connect_components, set_component_value
        )
        
        print("✅ Successfully imported sync tools")
        
        # Test 1: Get current components
        print("\n📍 Getting current components...")
        result = get_all_components()
        print(f"Components result: {result}")
        
        # Test 2: Add different component types
        print("\n📍 Adding different component types...")
        
        # Add a line
        print("Adding line...")
        line_result = add_component("line", 400, 100)
        print(f"Line result: {line_result}")
        
        # Add a slider
        print("Adding slider...")
        slider_result = add_component("slider", 400, 200)
        print(f"Slider result: {slider_result}")
        
        # Add a panel
        print("Adding panel...")
        panel_result = add_component("panel", 400, 300)
        print(f"Panel result: {panel_result}")
        
        print("\n✅ Direct sync tools test completed!")
        
    except Exception as e:
        print(f"❌ Sync tools test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Geometry Agent Tests with Manual MCP Server")
    print("Make sure the manual MCP server is running on port 8001")
    print()
    
    # Test sync tools directly first
    test_sync_tools_directly()
    
    # Then test through geometry agent
    test_geometry_agent()