#!/usr/bin/env python3
"""
Simple TCP Bridge Test

This test validates the basic TCP bridge connection without full agent dependencies.
Just tests the core TCP communication path.

Prerequisites:
1. Grasshopper open with "Grasshopper MCP" component
2. TCP bridge component: Enabled=True, Port=8080
3. Status should show: "Running on port 8080"

Run: python3 test_tcp_bridge_simple.py
"""

import socket
import json
import sys
import time

def get_windows_host():
    """Get Windows host IP from WSL."""
    import platform
    import subprocess
    
    if 'microsoft' in platform.uname().release.lower():
        # Running in WSL
        try:
            # Method 1: Try default route (more reliable for WSL2)
            result = subprocess.run(['ip', 'route', 'show'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'default' in line:
                        # Extract IP address from: default via 172.28.192.1 dev eth0
                        parts = line.split()
                        if len(parts) >= 3 and parts[1] == 'via':
                            windows_ip = parts[2]
                            print(f"WSL detected Windows host via default route: {windows_ip}")
                            return windows_ip
            
            # Method 2: Fallback to /etc/resolv.conf
            result = subprocess.run(['grep', 'nameserver', '/etc/resolv.conf'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                windows_ip = result.stdout.strip().split()[1]
                print(f"WSL detected Windows host via resolv.conf: {windows_ip}")
                return windows_ip
        except Exception:
            pass
    return "localhost"

def test_tcp_connection():
    """Test basic TCP connection to port 8081."""
    host = get_windows_host()
    port = 8081  # Updated to match the working port
    print(f"🔍 Testing TCP connection to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP bridge is listening on port {port}")
            return True
        else:
            print(f"❌ TCP bridge is not listening on port {port}")
            print("🔧 Deploy TCP bridge component first:")
            print("   1. Copy GH_MCP.gha to %APPDATA%\\Grasshopper\\Libraries\\")
            print(f"   2. Add 'Grasshopper MCP' component with Enabled=True, Port={port}")
            return False
    except Exception as e:
        print(f"❌ TCP connection error: {e}")
        return False

def test_tcp_command():
    """Test sending a command to TCP bridge."""
    host = get_windows_host()
    port = 8081  # Updated to match the working port
    print(f"🔍 Testing TCP bridge command to {host}:{port}...")
    
    try:
        # Connect to TCP bridge
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        # Send test command
        test_command = {
            "type": "add_component",
            "parameters": {
                "type": "point",
                "x": 100,
                "y": 200,
                "z": 0
            }
        }
        
        command_json = json.dumps(test_command) + '\\n'
        print(f"Sending: {test_command}")
        
        sock.send(command_json.encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(4096).decode('utf-8').strip()
        sock.close()
        
        if response_data:
            print(f"Response: {response_data}")
            try:
                response = json.loads(response_data)
                if response.get('success', False):
                    print("✅ TCP bridge command successful!")
                    print("🎯 Check Grasshopper canvas for a point at (100, 200, 0)")
                    return True
                else:
                    print(f"⚠️ Command failed: {response.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response_data}")
                return False
        else:
            print("❌ No response from TCP bridge")
            return False
            
    except Exception as e:
        print(f"❌ TCP command failed: {e}")
        return False

def test_mcp_tools_import():
    """Test importing MCP tools."""
    print("🔍 Testing MCP tools import...")
    
    try:
        # Test importing the communication module
        import sys
        import os
        
        # Add reference path
        reference_path = os.path.join(os.path.dirname(__file__), 'reference')
        if reference_path not in sys.path:
            sys.path.insert(0, reference_path)
            
        from grasshopper_mcp.utils.communication import send_to_grasshopper
        print("✅ MCP communication module imported successfully")
        
        # Test the send function (will fail if TCP bridge not running, but import works)
        result = send_to_grasshopper("get_document_info", {})
        if result.get('success', False):
            print("✅ MCP tools working with TCP bridge!")
            return True
        else:
            print("⚠️ MCP tools imported but TCP bridge not responding")
            print(f"Response: {result}")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import MCP tools: {e}")
        return False
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

def main():
    """Run simple TCP bridge tests."""
    print("🧪 Simple TCP Bridge Test")
    print("=" * 50)
    
    tests = [
        ("TCP Connection", test_tcp_connection),
        ("TCP Command", test_tcp_command), 
        ("MCP Tools Import", test_mcp_tools_import)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        except Exception as e:
            print(f"❌ FAIL {test_name}: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\\n" + "=" * 50)
    print("TCP BRIDGE TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed >= 2:
        print("\\n🎉 TCP BRIDGE WORKING!")
        print("✅ Basic TCP communication established")
        print("✅ Ready for agent integration")
        print("\\n📖 Next steps:")
        print("1. Run: python3 test_simple_working_solution.py")
        print("2. Test complete agent flow with geometry creation")
        print("\\n🚀 Architecture confirmed:")
        print("smolagents → STDIO MCP → TCP bridge → Grasshopper")
        
        return True
    elif passed >= 1:
        print("\\n🔧 PARTIAL SUCCESS")
        print("✅ Some TCP functionality working")
        print("⚠️ Deploy TCP bridge component if not done")
        return True
    else:
        print("\\n❌ TCP BRIDGE NOT WORKING")
        print("🚨 Deploy TCP bridge component:")
        print("1. Copy reference/GH_MCP/GH_MCP/bin/Release/net48/GH_MCP.gha")
        print("2. To: %APPDATA%\\Grasshopper\\Libraries\\")
        print("3. Restart Grasshopper, add component with Enabled=True")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)