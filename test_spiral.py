#!/usr/bin/env python3
"""
Test creating a 3D spiral in Grasshopper via HTTP MCP.

This test demonstrates the complete chain:
HTTP MCP Agent → HTTP MCP Server → TCP Bridge → Grasshopper
"""

import sys
sys.path.insert(0, 'src')

from bridge_design_system.agents.geometry_agent_mcpadapt import GeometryAgentMCPAdapt

def main():
    print("🦗 Testing Grasshopper 3D Spiral Creation via HTTP MCP")
    print("=" * 60)
    
    # Create agent with current transport mode
    print("Creating geometry agent...")
    agent = GeometryAgentMCPAdapt()
    print(f'✅ Agent created with transport: {agent.transport_mode}')
    
    # Get connection status
    print("\nChecking MCP connection...")
    status = agent.get_tool_info()
    print(f"✅ Connection status: {status['message']}")
    print(f"✅ Available tools: {status['mcp_tools']}")
    print(f"✅ Transport: {status.get('transport', 'unknown')}")
    
    # Test creating a 3D spiral in Grasshopper
    task = '''
Create a beautiful 3D spiral in Grasshopper using Python. The spiral should:
1. Have 50 points along its path
2. Make 3 complete turns (rotations)
3. Grow from radius 0 to 5 units (expanding outward)
4. Rise from height 0 to 10 units (going upward)

Use the add_python3_script tool to create a Python component that generates this spiral.
The Python code should use Rhino.Geometry to create the spiral points and return them as a curve.
'''

    print("\n🎯 Running spiral creation task...")
    print("Task:", task[:100] + "...")
    
    try:
        result = agent.run(task)
        print("\n✅ Task completed!")
        print("Result:", str(result)[:500] + "..." if len(str(result)) > 500 else str(result))
        
        print("\n🎉 Success! Check Grasshopper for:")
        print("   - New Python script component on canvas")
        print("   - 3D spiral geometry in Rhino viewport")
        print("   - TCP bridge component showing active connections")
        
    except Exception as e:
        print(f"\n❌ Task failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Grasshopper is running with TCP bridge on port 8081")
        print("2. Make sure HTTP MCP server is running: uv run python -m bridge_design_system.mcp.http_mcp_server --port 8001")
        print("3. Check if MCP_TRANSPORT_MODE is set to 'http'")

if __name__ == "__main__":
    main()