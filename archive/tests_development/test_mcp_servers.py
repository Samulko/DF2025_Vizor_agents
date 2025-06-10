#!/usr/bin/env python3
"""Test script for MCP server implementations.

This script tests both FastMCP and Manual MCP servers to verify they work correctly.
"""
import asyncio
import json
import time
import aiohttp
import requests
from typing import Dict, Any


class MCPServerTester:
    """Test MCP server implementations."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.health_url = f"{base_url}/health"
        self.bridge_status_url = f"{base_url}/grasshopper/status"
    
    def test_health_check(self) -> bool:
        """Test server health check."""
        try:
            response = requests.get(self.health_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status')}")
                print(f"   Server: {data.get('server')}")
                print(f"   Active sessions: {data.get('active_sessions', 'N/A')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_bridge_status(self) -> bool:
        """Test bridge status endpoint."""
        try:
            response = requests.get(self.bridge_status_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Bridge status check passed")
                print(f"   Bridge mode: {data.get('bridge_mode')}")
                print(f"   Pending commands: {data.get('pending_commands')}")
                print(f"   Active sessions: {data.get('active_sessions', 'N/A')}")
                return True
            else:
                print(f"❌ Bridge status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Bridge status error: {e}")
            return False
    
    def test_mcp_initialize(self) -> bool:
        """Test MCP initialize request."""
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "clientInfo": {
                        "name": "mcp-tester",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = requests.post(
                self.mcp_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    print(f"✅ MCP initialize passed")
                    print(f"   Protocol version: {data['result'].get('protocolVersion')}")
                    print(f"   Server: {data['result'].get('serverInfo', {}).get('name')}")
                    return True
                else:
                    print(f"❌ MCP initialize failed: {data.get('error')}")
                    return False
            else:
                print(f"❌ MCP initialize HTTP error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ MCP initialize error: {e}")
            return False
    
    def test_mcp_tools_list(self) -> bool:
        """Test MCP tools/list request."""
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/list"
            }
            
            response = requests.post(
                self.mcp_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    print(f"✅ MCP tools/list passed")
                    print(f"   Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"     - {tool.get('name')}: {tool.get('description')}")
                    return True
                else:
                    print(f"❌ MCP tools/list failed: {data.get('error')}")
                    return False
            else:
                print(f"❌ MCP tools/list HTTP error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ MCP tools/list error: {e}")
            return False
    
    def test_mcp_tool_call(self) -> bool:
        """Test MCP tools/call request."""
        try:
            request_data = {
                "jsonrpc": "2.0", 
                "id": "test-3",
                "method": "tools/call",
                "params": {
                    "name": "get_all_components",
                    "arguments": {}
                }
            }
            
            response = requests.post(
                self.mcp_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30  # Tool calls may take longer
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    print(f"✅ MCP tools/call passed")
                    content = data["result"].get("content", [])
                    if content:
                        print(f"   Response: {content[0].get('text', '')[:100]}...")
                    return True
                else:
                    print(f"❌ MCP tools/call failed: {data.get('error')}")
                    return False
            else:
                print(f"❌ MCP tools/call HTTP error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ MCP tools/call error: {e}")
            return False
    
    async def test_sse_connection(self) -> bool:
        """Test SSE connection."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.mcp_url) as response:
                    if response.status == 200:
                        print(f"✅ SSE connection established")
                        
                        # Read a few events
                        event_count = 0
                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                try:
                                    event_data = json.loads(line_str[6:])
                                    print(f"   Event: {event_data.get('type', 'unknown')}")
                                    event_count += 1
                                    if event_count >= 2:  # Get at least 2 events
                                        break
                                except json.JSONDecodeError:
                                    pass
                        
                        return True
                    else:
                        print(f"❌ SSE connection failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ SSE connection error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print(f"🧪 Testing MCP server at {self.base_url}")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Bridge Status", self.test_bridge_status),
            ("MCP Initialize", self.test_mcp_initialize),
            ("MCP Tools List", self.test_mcp_tools_list),
            ("MCP Tool Call", self.test_mcp_tool_call),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            result = test_func()
            results.append((test_name, result))
            if not result:
                print(f"⚠️  {test_name} failed, continuing with other tests...")
        
        # Test SSE separately as it's async
        print(f"\n🔍 Running SSE Connection Test...")
        try:
            sse_result = asyncio.run(self.test_sse_connection())
            results.append(("SSE Connection", sse_result))
        except Exception as e:
            print(f"❌ SSE test error: {e}")
            results.append(("SSE Connection", False))
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 Test Results Summary:")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        print(f"\n📊 Results: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All tests passed! MCP server is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the server implementation.")
            return False


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP server implementations")
    parser.add_argument("--port", type=int, default=8001, help="Server port")
    parser.add_argument("--host", default="localhost", help="Server host")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    tester = MCPServerTester(base_url)
    
    print("🚀 MCP Server Test Suite")
    print(f"🎯 Target: {base_url}")
    print()
    
    success = tester.run_all_tests()
    
    if success:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()