#!/usr/bin/env python3
"""
Final MCP integration test before commit.

This test verifies the complete integration works:
1. Start MCP server in background
2. Load tools via STDIO
3. Create geometry agent with tools
4. Clean shutdown

Run: python test_mcp_integration_final.py
"""

import sys
import subprocess
import time
import os
from typing import Optional

def start_mcp_server():
    """Start the MCP server in background."""
    print("Starting MCP server in background...")
    
    # Start the MCP server process
    process = subprocess.Popen(
        ["uv", "run", "python", "-m", "grasshopper_mcp.bridge"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()
    )
    
    # Give it time to start
    time.sleep(3)
    
    # Check if it's running
    if process.poll() is None:
        print("✅ MCP server started successfully")
        return process
    else:
        stdout, stderr = process.communicate()
        print(f"❌ MCP server failed to start")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        return None

def test_mcp_tools_with_server(server_process):
    """Test loading MCP tools with server running."""
    print("\nTesting MCP tools loading with running server...")
    
    try:
        from src.bridge_design_system.mcp.mcp_tools_utils import get_grasshopper_tools
        
        # Try to load tools
        tools = get_grasshopper_tools(use_stdio=True)
        
        if tools:
            print(f"✅ Successfully loaded {len(tools)} MCP tools!")
            
            # Show some tools
            tool_names = [tool.name for tool in tools[:10]]
            print(f"Sample tools: {tool_names}")
            
            # Check for expected tools
            expected = ['add_component', 'connect_components', 'get_all_components', 
                       'add_number_slider', 'add_panel', 'add_circle']
            found = [t for t in expected if t in [tool.name for tool in tools]]
            
            print(f"✅ Found {len(found)}/{len(expected)} expected tools: {found}")
            
            return True, tools
        else:
            print("❌ No tools loaded")
            return False, []
            
    except Exception as e:
        print(f"❌ Error loading tools: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def test_geometry_agent_integration(tools):
    """Test geometry agent with MCP tools."""
    print("\nTesting geometry agent integration...")
    
    try:
        from src.bridge_design_system.agents.geometry_agent import GeometryAgent
        
        # Create agent with MCP tools
        agent = GeometryAgent(mcp_tools=tools)
        
        print("✅ Created geometry agent with MCP tools")
        
        # Initialize the agent to load tools
        agent.initialize_agent()
        
        # Check tools
        mcp_tool_count = len([t for t in agent.tools if t.name in [tool.name for tool in tools]])
        
        print(f"✅ Agent has {len(agent.tools)} total tools ({mcp_tool_count} from MCP)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup(server_process):
    """Clean up server process."""
    if server_process:
        print("\nCleaning up...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✅ Server stopped cleanly")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("✅ Server killed")

def main():
    """Run integration test."""
    print("=" * 60)
    print("Final MCP Integration Test")
    print("=" * 60)
    
    server_process = None
    
    try:
        # Start server
        server_process = start_mcp_server()
        if not server_process:
            print("❌ Failed to start MCP server")
            return False
        
        # Test tools loading
        success1, tools = test_mcp_tools_with_server(server_process)
        if not success1:
            print("❌ Failed to load MCP tools")
            return False
        
        # Test agent integration
        success2 = test_geometry_agent_integration(tools)
        
        print("\n" + "=" * 60)
        print("Test Summary:")
        print("=" * 60)
        
        print(f"MCP Server Start: ✅ PASS")
        print(f"MCP Tools Loading: {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"Geometry Agent Integration: {'✅ PASS' if success2 else '❌ FAIL'}")
        
        all_passed = success1 and success2
        
        if all_passed:
            print("\n🎉 All tests passed! Ready to commit.")
            print("\nThe integration is working:")
            print("- grasshopper-mcp installed as local dependency")
            print("- MCP server starts via 'uv run python -m grasshopper_mcp.bridge'")
            print(f"- {len(tools)} MCP tools loaded successfully")
            print("- Geometry agent can use MCP tools")
        else:
            print("\n❌ Some tests failed. Check output above.")
        
        return all_passed
        
    finally:
        cleanup(server_process)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)