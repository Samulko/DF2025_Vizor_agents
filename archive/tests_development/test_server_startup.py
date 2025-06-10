#!/usr/bin/env python3
"""Test server startup to verify FastMCP/Manual fallback works."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_server_imports():
    """Test if we can import and identify which server will be used."""
    
    print("🧪 Testing MCP Server Import Capabilities")
    print("=" * 60)
    
    # Test FastMCP availability
    print("\n📍 Testing FastMCP availability:")
    fastmcp_available = False
    try:
        from mcp.server.fastmcp import FastMCP
        print("✅ FastMCP framework is available")
        fastmcp_available = True
    except ImportError as e:
        print(f"❌ FastMCP framework not available: {e}")
    
    # Test Manual MCP availability
    print("\n📍 Testing Manual MCP availability:")
    manual_available = False
    try:
        from bridge_design_system.mcp.manual_mcp_server import ManualMCPServer
        print("✅ Manual MCP server is available")
        manual_available = True
    except ImportError as e:
        print(f"❌ Manual MCP server not available: {e}")
    
    # Test our FastMCP server wrapper
    if fastmcp_available:
        print("\n📍 Testing FastMCP server wrapper:")
        try:
            from bridge_design_system.mcp.fastmcp_server import create_grasshopper_mcp_server
            print("✅ FastMCP server wrapper imports successfully")
            
            # Try to create (but not run) the server
            print("📍 Testing FastMCP server creation:")
            try:
                server = create_grasshopper_mcp_server(
                    grasshopper_url="http://localhost:8080",
                    port=8001,
                    bridge_mode=True,
                    stateless=False
                )
                print("✅ FastMCP server creates successfully")
            except Exception as e:
                print(f"❌ FastMCP server creation failed: {e}")
                fastmcp_available = False
        except ImportError as e:
            print(f"❌ FastMCP server wrapper import failed: {e}")
            fastmcp_available = False
    
    # Summary
    print("\n📊 Summary:")
    print(f"FastMCP Available: {'✅ Yes' if fastmcp_available else '❌ No'}")
    print(f"Manual MCP Available: {'✅ Yes' if manual_available else '❌ No'}")
    
    if fastmcp_available:
        print("🎯 Recommended: Will use FastMCP server (per MCP_IMPLEMENTATION_GUIDE.md)")
    elif manual_available:
        print("🔄 Fallback: Will use Manual MCP server")
    else:
        print("💥 Error: No MCP server available")
        return False
        
    return True

if __name__ == "__main__":
    print("🚀 Testing Server Import Capabilities")
    print("This verifies which MCP server implementation will be used")
    print()
    
    success = test_server_imports()
    
    if success:
        print("\n✅ Server import test passed!")
        print("💡 You can now start the server with:")
        print("   python -m bridge_design_system.main --start-streamable-http --mcp-port 8001")
    else:
        print("\n❌ Server import test failed!")
        print("💡 Try installing missing dependencies")
    
    print("\n🎉 Test complete!")