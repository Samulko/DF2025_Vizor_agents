#!/usr/bin/env python3
"""
Test creating a 3D spiral in Grasshopper using DIRECT smolagents MCP integration.

This bypasses MCPAdapt and uses smolagents' built-in ToolCollection.from_mcp()
which is more stable for HTTP transport.
"""

import sys
sys.path.insert(0, 'src')

import os
from mcp import StdioServerParameters
from smolagents import CodeAgent  
from smolagents.tools import ToolCollection
from bridge_design_system.config.model_config import ModelProvider

def main():
    print("🦗 Testing Grasshopper 3D Spiral via DIRECT smolagents MCP")
    print("=" * 60)
    
    # Check transport mode
    transport_mode = os.getenv('MCP_TRANSPORT_MODE', 'stdio').lower()
    print(f"Transport mode: {transport_mode}")
    
    if transport_mode == "http":
        print("❌ HTTP transport not supported with direct smolagents integration")
        print("🔄 Falling back to STDIO transport...")
        transport_mode = "stdio"
    
    # Create model for agent
    print("Creating model...")
    model = ModelProvider.get_model("geometry")
    print(f"✅ Model created: {type(model)}")
    
    # Create STDIO server parameters for MCP connection
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "grasshopper_mcp.bridge"],
        env=None  # Use current environment
    )
    
    print(f"✅ Server params: {server_params}")
    
    try:
        print("\n🔌 Connecting to MCP server...")
        
        # Use smolagents' built-in MCP support (more stable than MCPAdapt)
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
            print(f"✅ Connected! Available tools: {len(list(tool_collection.tools))}")
            
            # Show tool names
            tool_names = [getattr(tool, 'name', str(tool)) for tool in tool_collection.tools]
            print(f"✅ Tool names: {tool_names[:5]}...")
            
            # Create agent with MCP tools
            agent = CodeAgent(
                tools=[*tool_collection.tools],
                model=model,
                add_base_tools=False,  # Keep it simple
                max_steps=10
            )
            
            print(f"✅ Agent created with {len(list(tool_collection.tools))} MCP tools")
            
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
            
            result = agent.run(task)
            print("\n✅ Task completed!")
            print("Result:", str(result)[:500] + "..." if len(str(result)) > 500 else str(result))
            
            print("\n🎉 Success! Check Grasshopper for:")
            print("   - New Python script component on canvas")
            print("   - 3D spiral geometry in Rhino viewport")
            print("   - TCP bridge component showing active connections")
            
    except Exception as e:
        print(f"\n❌ Task failed: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        print("\nTroubleshooting:")
        print("1. Make sure Grasshopper is running with TCP bridge on port 8081")
        print("2. Check if the STDIO MCP server can connect to TCP bridge")
        print("3. Verify uv and python environment are working")

if __name__ == "__main__":
    main()