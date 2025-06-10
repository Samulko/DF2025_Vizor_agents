#!/usr/bin/env python3
"""
Test Standard Geometry Agent with MCP Tools

This test validates the clean approach: a standard smolagents agent
that uses MCP tools as just one source of tools among many.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bridge_design_system.config.logging_config import get_logger
from bridge_design_system.agents.geometry_agent import GeometryAgent
from bridge_design_system.mcp.mcp_tools_utils import get_grasshopper_tools, is_mcp_server_available

logger = get_logger(__name__)

def test_standard_geometry_agent():
    """Test geometry agent as standard smolagents agent with MCP tools."""
    
    print("🎯 Testing Standard Geometry Agent (smolagents + existing MCP server)")
    print("This will connect to your existing Grasshopper MCP server via STDIO")
    print("(The same server that Cline uses)")
    print()
    
    # Test 1: Check MCP server availability
    print("🧪 Test 1: Check MCP Server Availability (STDIO)")
    
    server_available = is_mcp_server_available(use_stdio=True)
    
    if server_available:
        print("✅ MCP server is available via STDIO")
    else:
        print("⚠️ MCP server not available via STDIO")
        print("Make sure your VizorGH project is accessible and uv is installed")
        print("Agent will use only custom tools")
    
    # Test 2: Get MCP tools at application level
    print()
    print("🧪 Test 2: Get MCP Tools at Application Level (STDIO)")
    
    mcp_tools = []
    if server_available:
        try:
            mcp_tools = get_grasshopper_tools(use_stdio=True)
            print(f"✅ Successfully loaded {len(mcp_tools)} MCP tools via STDIO")
            
            # List MCP tool names
            mcp_tool_names = [tool.name for tool in mcp_tools]
            print(f"📋 MCP tool names: {mcp_tool_names}")
            
        except Exception as e:
            print(f"❌ Failed to load MCP tools: {e}")
    
    # Test 3: Create standard geometry agent with mixed tools
    print()
    print("🧪 Test 3: Create Standard Geometry Agent")
    
    try:
        # Create agent with MCP tools (if available)
        geometry_agent = GeometryAgent(mcp_tools=mcp_tools)
        
        total_tools = len(geometry_agent.tools)
        print(f"✅ Geometry agent created successfully")
        print(f"🛠️  Total tools available: {total_tools}")
        
        # List all tool names
        all_tool_names = [tool.name for tool in geometry_agent.tools]
        print(f"📋 All tool names: {all_tool_names}")
        
        # Identify which tools are from MCP vs custom
        mcp_count = len(mcp_tools)
        custom_count = total_tools - mcp_count
        print(f"📊 MCP tools: {mcp_count}, Custom tools: {custom_count}")
        
    except Exception as e:
        print(f"❌ Failed to create geometry agent: {e}")
        return False
    
    # Test 4: Use the agent (test both MCP and custom tools)
    print()
    print("🧪 Test 4: Test Agent Tool Usage")
    
    try:
        # Test custom tool (always available)
        print("📍 Testing custom tool...")
        result1 = geometry_agent.run("Create a point at coordinates (100, 200, 300) using any available tool")
        print(f"Custom tool result: {result1}")
        
        # Test MCP tool (if available)
        if mcp_tools:
            print("📍 Testing MCP tool...")
            result2 = geometry_agent.run("Clear the document and add a component at (50, 75, 0)")
            print(f"MCP tool result: {result2}")
        
        print("✅ Agent tool usage successful!")
        
    except Exception as e:
        print(f"❌ Agent tool usage failed: {e}")
        return False
    
    return True

def test_agent_without_mcp():
    """Test geometry agent works fine without MCP tools."""
    
    print()
    print("============================================================")
    print("🧪 Testing Geometry Agent Without MCP Tools")
    print("============================================================")
    
    try:
        # Create agent with no MCP tools
        geometry_agent = GeometryAgent(mcp_tools=[])
        
        print(f"✅ Agent created with {len(geometry_agent.tools)} custom tools only")
        
        # Test that it still works
        result = geometry_agent.run("Create a point at (1, 2, 3) and analyze its properties")
        print(f"Custom-only result: {result}")
        
        print("✅ Agent works perfectly without MCP tools")
        return True
        
    except Exception as e:
        print(f"❌ Agent without MCP tools failed: {e}")
        return False

def main():
    """Run all standard geometry agent tests."""
    
    print("============================================================")
    print("🚀 Standard Geometry Agent Tests (Clean Architecture)")
    print("============================================================")
    print()
    
    # Run tests
    test1_passed = test_standard_geometry_agent()
    test2_passed = test_agent_without_mcp()
    
    # Results summary
    print()
    print("============================================================")
    print("🏁 Test Results Summary")
    print("============================================================")
    
    print(f"📊 Standard Agent + MCP: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"📊 Agent Without MCP: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print()
    
    if test1_passed and test2_passed:
        print("🎉 All tests passed! Clean architecture is working correctly.")
        print("🔥 Agent is standard smolagents agent!")
        print("🔥 MCP tools are just one source among many!")
        print("🔥 No complex MCP coupling!")
        print("🔥 Application-level MCP management!")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())