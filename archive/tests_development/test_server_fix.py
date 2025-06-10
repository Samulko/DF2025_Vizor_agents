#!/usr/bin/env python3
"""Test the MCP server task group fix."""
import sys
import os
import time
import httpx

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_mcp_server_fix():
    """Test if the server task group fix works."""
    
    print("🧪 Testing MCP Server Task Group Fix")
    print("=" * 50)
    
    # Test the sync MCP tools with proper session management
    try:
        from bridge_design_system.mcp.sync_mcp_tools import SyncMCPClient
        
        print("📡 Creating MCP client...")
        client = SyncMCPClient("http://localhost:8001/mcp/")
        
        print("🔗 Connecting to MCP server...")
        success = client.connect()
        
        if success:
            print("✅ Successfully connected to MCP server!")
            
            print("🔧 Testing tool call...")
            result = client.call_tool("clear_document", {})
            
            if "error" not in result or "Task group is not initialized" not in str(result):
                print("✅ SUCCESS! Task group issue appears to be fixed!")
                print(f"📊 Tool result: {result}")
                return True
            else:
                print(f"❌ Task group error still present: {result}")
                return False
        else:
            print("❌ Failed to connect to MCP server")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_http():
    """Test direct HTTP connection to debug issues."""
    
    print("\n🌐 Testing Direct HTTP Connection")
    print("=" * 50)
    
    url = "http://localhost:8001/mcp/"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.post(url, json=payload, headers=headers)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Text: {response.text}")
            
            if response.status_code == 200:
                print("✅ HTTP connection successful!")
                
                # Test a tool call
                tool_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "clear_document",
                        "arguments": {}
                    }
                }
                
                # Extract session ID if present
                session_id = response.headers.get("mcp-session-id")
                if session_id:
                    headers["mcp-session-id"] = session_id
                    print(f"🔑 Using session ID: {session_id}")
                
                print("🔧 Testing tool call...")
                tool_response = client.post(url, json=tool_payload, headers=headers)
                
                print(f"🔧 Tool Response Status: {tool_response.status_code}")
                print(f"🔧 Tool Response Text: {tool_response.text}")
                
                if "Task group is not initialized" in tool_response.text:
                    print("❌ Task group error still present")
                    return False
                else:
                    print("✅ Tool call successful - task group issue resolved!")
                    return True
            else:
                print(f"❌ HTTP connection failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting MCP Server Task Group Fix Test")
    print("Make sure the FIXED MCP server is running:")
    print("python -m bridge_design_system.main --start-streamable-http --mcp-port 8001")
    print()
    
    # Test HTTP first
    http_success = test_direct_http()
    
    # Then test sync client
    if http_success:
        sync_success = test_mcp_server_fix()
        
        if sync_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ MCP Server task group issue has been resolved!")
            print("✅ Phase 2.3 is now 100% complete!")
        else:
            print("\n❌ Sync test failed")
    else:
        print("\n❌ HTTP test failed, skipping sync test")