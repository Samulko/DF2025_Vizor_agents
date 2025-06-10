#!/usr/bin/env python3
"""
Simple STDIO Connection Test

Quick test to verify the fix works.

Run: python test_simple_stdio.py
"""

import os
from mcp import StdioServerParameters
from smolagents import ToolCollection

def test_fixed_connection():
    """Test the fixed STDIO connection."""
    print("Testing fixed STDIO connection...")
    
    try:
        # Use the fixed configuration
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "grasshopper_mcp.bridge"],
            env=os.environ.copy()
        )
        
        print("Connecting to MCP server...")
        
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
            tools = list(tool_collection.tools)
            
            print(f"✅ SUCCESS! Loaded {len(tools)} tools")
            print(f"Sample tools: {[tool.name for tool in tools[:5]]}")
            
            return True
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_geometry_agent():
    """Test with geometry agent."""
    print("\nTesting geometry agent integration...")
    
    try:
        from src.bridge_design_system.mcp.mcp_tools_utils import get_grasshopper_tools
        
        tools = get_grasshopper_tools(use_stdio=True)
        
        if tools:
            print(f"✅ Geometry agent integration successful: {len(tools)} tools")
            return True
        else:
            print("❌ No tools loaded by geometry agent")
            return False
            
    except Exception as e:
        print(f"❌ Geometry agent test failed: {e}")
        return False

def main():
    """Run simple tests."""
    print("=" * 50)
    print("Simple STDIO Connection Test")
    print("=" * 50)
    
    # Test 1: Direct connection
    success1 = test_fixed_connection()
    
    # Test 2: Geometry agent integration
    success2 = test_geometry_agent()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("The STDIO connection is working correctly.")
        print("\nNext step: Run full integration test")
        print("  python test_mcp_integration_final.py")
    elif success1:
        print("✅ STDIO connection works")
        print("❌ Geometry agent integration needs fixing")
        print("\nCheck mcp_tools_utils.py configuration")
    else:
        print("❌ STDIO connection still failing")
        print("\nRun detailed diagnostics:")
        print("  python test_stdio_diagnostic.py")
        print("  python test_stdio_connection_robust.py")

if __name__ == "__main__":
    main()