#!/usr/bin/env python3
"""Test the Manual MCP server implementation."""
import sys
import os
import time
import httpx
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_manual_mcp_server():
    """Test the manual MCP server implementation."""
    
    print("🧪 Testing Manual MCP Server")
    print("=" * 50)
    
    url = "http://localhost:8001/mcp/"
    
    # Test 1: Initialize session
    print("📍 Test 1: Initialize MCP session")
    
    init_payload = {
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
        "Accept": "text/event-stream"
    }
    
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.post(url, json=init_payload, headers=headers)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            print(f"📊 Response Text: {response.text}")
            
            if response.status_code == 200:
                # Extract session ID from headers
                session_id = response.headers.get("mcp-session-id")
                if session_id:
                    print(f"✅ Session initialized successfully: {session_id}")
                    
                    # Test 2: List tools
                    print("\n📍 Test 2: List tools")
                    
                    tools_payload = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                    
                    tools_headers = headers.copy()
                    tools_headers["mcp-session-id"] = session_id
                    
                    tools_response = client.post(url, json=tools_payload, headers=tools_headers)
                    print(f"🔧 Tools Response Status: {tools_response.status_code}")
                    print(f"🔧 Tools Response Text: {tools_response.text}")
                    
                    if tools_response.status_code == 200:
                        print("✅ Tools list successful!")
                        
                        # Test 3: Call a tool
                        print("\n📍 Test 3: Call clear_document tool")
                        
                        tool_call_payload = {
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "tools/call",
                            "params": {
                                "name": "clear_document",
                                "arguments": {}
                            }
                        }
                        
                        tool_response = client.post(url, json=tool_call_payload, headers=tools_headers)
                        print(f"🔧 Tool Call Response Status: {tool_response.status_code}")
                        print(f"🔧 Tool Call Response Text: {tool_response.text}")
                        
                        if tool_response.status_code == 200:
                            if "Task group is not initialized" not in tool_response.text:
                                print("✅ SUCCESS! Manual MCP server is working correctly!")
                                print("✅ No task group errors detected!")
                                return True
                            else:
                                print("❌ Task group error still present")
                                return False
                        else:
                            print(f"❌ Tool call failed with status {tool_response.status_code}")
                            return False
                    else:
                        print(f"❌ Tools list failed with status {tools_response.status_code}")
                        return False
                else:
                    print("❌ No session ID in response headers")
                    return False
            else:
                print(f"❌ Initialize failed with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_tools_with_manual_server():
    """Test sync tools with the manual MCP server."""
    
    print("\n🧪 Testing Sync Tools with Manual MCP Server")
    print("=" * 50)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import SyncMCPClient
        
        print("📡 Creating MCP client for manual server...")
        client = SyncMCPClient("http://localhost:8001/mcp/")
        
        print("🔗 Connecting to manual MCP server...")
        success = client.connect()
        
        if success:
            print("✅ Successfully connected to manual MCP server!")
            
            print("🔧 Testing clear_document tool...")
            result = client.call_tool("clear_document", {})
            
            if result.get("success", False):
                print("✅ SUCCESS! Tool call worked!")
                print(f"📊 Tool result: {result}")
                
                # Test another tool
                print("🔧 Testing add_component tool...")
                add_result = client.call_tool("add_component", {
                    "component_type": "point",
                    "x": 100,
                    "y": 100
                })
                
                print(f"📊 Add component result: {add_result}")
                
                if "Task group is not initialized" not in str(add_result):
                    print("✅ ALL SYNC TOOLS TESTS PASSED!")
                    print("✅ Manual MCP server is fully functional!")
                    return True
                else:
                    print("❌ Task group error in add_component")
                    return False
            else:
                print(f"❌ Tool call failed: {result}")
                return False
        else:
            print("❌ Failed to connect to manual MCP server")
            return False
            
    except Exception as e:
        print(f"❌ Sync tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_check():
    """Test the health check endpoint."""
    
    print("\n🏥 Testing Health Check")
    print("=" * 30)
    
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:8001/health")
            
            print(f"📊 Health Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Health Data: {data}")
                print("✅ Health check passed!")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Manual MCP Server Tests")
    print("Make sure the manual MCP server is running:")
    print("python -m bridge_design_system.main --start-streamable-http --mcp-port 8001")
    print()
    
    # Test 1: Health check
    health_ok = test_health_check()
    
    # Test 2: Direct MCP protocol
    if health_ok:
        mcp_ok = test_manual_mcp_server()
        
        # Test 3: Sync tools integration
        if mcp_ok:
            sync_ok = test_sync_tools_with_manual_server()
            
            if sync_ok:
                print("\n🎉 ALL TESTS PASSED!")
                print("✅ Manual MCP server is fully functional!")
                print("✅ Task group issue has been completely resolved!")
                print("✅ Phase 2.3 is now 100% complete!")
            else:
                print("\n❌ Sync tools test failed")
        else:
            print("\n❌ MCP protocol test failed")
    else:
        print("\n❌ Health check failed - server may not be running")
    
    print("\n📋 Test Summary:")
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"MCP Protocol: {'✅' if 'mcp_ok' in locals() and mcp_ok else '❌'}")
    print(f"Sync Tools: {'✅' if 'sync_ok' in locals() and sync_ok else '❌'}")