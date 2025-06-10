#!/usr/bin/env python3
"""
Test STDIO Connection to Existing Grasshopper MCP Server

This test validates that we can connect to your existing Grasshopper MCP server
via STDIO, the same way Cline Desktop does.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bridge_design_system.config.logging_config import get_logger
from bridge_design_system.mcp.mcp_tools_utils import get_mcp_tools_stdio, is_mcp_server_available_stdio

logger = get_logger(__name__)

def test_stdio_connection():
    """Test direct STDIO connection to your existing MCP server."""
    
    print("============================================================")
    print("🚀 Testing STDIO Connection to Existing Grasshopper MCP Server")
    print("============================================================")
    print()
    
    print("🎯 This test connects to your existing MCP server")
    print("📍 Server location: reference/grasshopper_mcp/bridge.py")
    print("🔗 Transport: STDIO (same as Cline Desktop uses)")
    print("⚡ Command: uv run python reference/grasshopper_mcp/bridge.py")
    print()
    
    # Test 1: Check server availability
    print("🧪 Test 1: Check if MCP server can be started")
    
    try:
        server_available = is_mcp_server_available_stdio()
        
        if server_available:
            print("✅ Successfully connected to MCP server via STDIO!")
        else:
            print("❌ Could not connect to MCP server via STDIO")
            return False
            
    except Exception as e:
        print(f"❌ Error checking server availability: {e}")
        return False
    
    # Test 2: Load tools
    print()
    print("🧪 Test 2: Load MCP tools from server")
    
    try:
        tools = get_mcp_tools_stdio()
        
        if tools:
            print(f"✅ Successfully loaded {len(tools)} MCP tools!")
            print()
            print("📋 Available tools:")
            for i, tool in enumerate(tools[:10], 1):  # Show first 10 tools
                print(f"   {i}. {tool.name}")
            
            if len(tools) > 10:
                print(f"   ... and {len(tools) - 10} more tools")
            
            print()
            print("🎉 STDIO connection test successful!")
            print("🔥 Your existing MCP server is working perfectly!")
            print("🔥 Ready to use with smolagents geometry agent!")
            
            return True
        else:
            print("❌ No tools loaded from MCP server")
            return False
            
    except Exception as e:
        print(f"❌ Error loading tools: {e}")
        return False

def main():
    """Run STDIO connection test."""
    
    success = test_stdio_connection()
    
    print()
    print("============================================================")
    print("🏁 Test Results")
    print("============================================================")
    
    if success:
        print("📊 STDIO Connection: ✅ PASS")
        print()
        print("🎉 Excellent! Your existing MCP server is accessible.")
        print("💡 Next step: Run the full geometry agent test:")
        print("   python test_standard_geometry_agent.py")
    else:
        print("📊 STDIO Connection: ❌ FAIL")
        print()
        print("🔧 Troubleshooting steps:")
        print("1. Make sure you're in the vizor_agents project directory")
        print("2. Make sure 'uv' is installed and in your PATH")
        print("3. Make sure fastmcp is installed: uv pip install fastmcp")
        print("4. Try running the MCP server manually:")
        print("   uv run python reference/grasshopper_mcp/bridge.py")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())