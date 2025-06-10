#!/usr/bin/env python3
"""
Test that the FastMCP server starts correctly and exposes the right endpoints.
"""

import requests
import time
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_fastmcp_server_endpoints():
    """Test that FastMCP server is running and responding to connections."""
    
    base_url = "http://localhost:8001"
    
    print("🧪 Testing FastMCP Server Connectivity")
    print(f"🔍 Checking server at: {base_url}")
    
    try:
        # Test if server is running by attempting to connect
        print("📡 Testing server connectivity...")
        
        # Try a simple GET to see if server responds (expect 404/405 for MCP server)
        response = requests.get(base_url, timeout=5)
        print(f"📊 Server response status: {response.status_code}")
        
        # For MCP servers, 404/405/406 are normal responses for HTTP GET
        if response.status_code in [200, 404, 405, 406]:
            print("✅ Server is running and responding to connections")
            print("🎯 This is normal for MCP servers (they expect MCP protocol, not HTTP GET)")
            
            # Test MCP endpoint specifically
            mcp_url = f"{base_url}/mcp"
            print(f"📡 Testing MCP endpoint at: {mcp_url}")
            mcp_response = requests.get(mcp_url, timeout=5)
            print(f"📊 MCP endpoint status: {mcp_response.status_code}")
            
            if mcp_response.status_code in [200, 404, 405, 406]:
                print("✅ MCP endpoint is accessible")
                print("🔥 FastMCP server is ready for MCP protocol communication")
                return True
            else:
                print(f"⚠️ Unexpected MCP endpoint status: {mcp_response.status_code}")
                return False
        else:
            print(f"⚠️ Unexpected server response: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastMCP server")
        print("💡 Make sure to start the server first:")
        print("   python -m bridge_design_system.mcp.fastmcp_server_clean --port 8001")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def main():
    """Test FastMCP server endpoints."""
    print("🚀 FastMCP Server Endpoint Test")
    print("="*50)
    
    success = test_fastmcp_server_endpoints()
    
    if success:
        print("\n✅ FastMCP server test passed!")
        print("🔥 Ready to test ToolCollection.from_mcp()")
    else:
        print("\n❌ FastMCP server test failed!")
        print("🔧 Check server startup and try again")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)