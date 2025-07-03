#!/usr/bin/env python3
"""
Debug specific connection issue with Grasshopper.
This will test the exact host that was detected and provide detailed error info.
"""

import sys
import os
<<<<<<< HEAD
import socket
import json
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_connection_verbose(host: str, port: int, timeout: float = 2.0) -> dict:
    """Test connection with detailed error information."""
    result = {
        "host": host,
        "port": port,
        "connected": False,
        "error": None,
        "error_code": None,
        "response_time_ms": None
    }
    
    start_time = time.time()
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        connect_result = sock.connect_ex((host, port))
        response_time = (time.time() - start_time) * 1000
        result["response_time_ms"] = round(response_time, 2)
        
        if connect_result == 0:
            result["connected"] = True
            # Try to send a valid Grasshopper command to test if it's actually Grasshopper
            try:
                test_msg = '{"type":"get_components_in_group","parameters":{"groupName":"test"}}\n'
                sock.sendall(test_msg.encode('utf-8'))
                sock.settimeout(3.0)  # Give Grasshopper time to respond
                
                response_data = b""
                while len(response_data) < 10240:  # Read up to 10KB
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response_data += chunk
                    if response_data.endswith(b"\n"):
                        break
                
                if response_data:
                    response_str = response_data.decode('utf-8-sig').strip()
                    result["grasshopper_response"] = True
                    try:
                        parsed = json.loads(response_str)
                        if parsed.get("success") is not None:  # Valid Grasshopper response format
                            result["response_preview"] = f"Valid Grasshopper: {str(parsed)[:100]}"
                        else:
                            result["response_preview"] = f"Unknown response: {str(parsed)[:100]}"
                    except json.JSONDecodeError:
                        result["response_preview"] = f"Non-JSON response: {response_str[:100]}"
                else:
                    result["grasshopper_response"] = False
                    result["error"] = "No response to valid command"
            except socket.timeout:
                result["grasshopper_response"] = False
                result["error"] = "No response to valid command (timeout)"
            except Exception as e:
                result["grasshopper_response"] = False
                result["error"] = f"Response test failed: {e}"
        else:
            result["connected"] = False
            result["error_code"] = connect_result
            # Common error codes
            error_messages = {
                10061: "Connection refused (service not running)",
                10060: "Connection timeout",
                10065: "Host unreachable",
                111: "Connection refused (Linux)",
                110: "Connection timeout (Linux)"
            }
            result["error"] = error_messages.get(connect_result, f"Connection failed (code {connect_result})")
        
        sock.close()
        
    except socket.timeout:
        result["error"] = "Socket timeout"
        result["response_time_ms"] = timeout * 1000
    except Exception as e:
        result["error"] = str(e)
    
    return result

def test_specific_host():
    # Test the host that was detected as working
    host = "172.28.192.1"
=======
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_specific_host():
    from bridge_design_system.mcp.grasshopper_mcp.utils.communication import test_connection_verbose
    
    # Test the host that was detected in the error log
    host = "172.19.144.1"
>>>>>>> ICD_dev
    port = 8081
    
    print(f"🔍 Testing specific host: {host}:{port}")
    print("=" * 50)
    
    result = test_connection_verbose(host, port, timeout=5.0)
    
    print(f"Host: {result['host']}")
    print(f"Port: {result['port']}")
    print(f"Connected: {'✅' if result['connected'] else '❌'} {result['connected']}")
    print(f"Response time: {result['response_time_ms']}ms")
    
    if result['error']:
        print(f"Error: {result['error']}")
    if result['error_code']:
        print(f"Error code: {result['error_code']}")
    
    if result.get('grasshopper_response'):
        print(f"Grasshopper response: ✅ {result.get('response_preview', 'OK')}")
    elif 'grasshopper_response' in result:
        print(f"Grasshopper response: ❌ {result.get('error', 'No response')}")
    
    print("\n🔧 Debugging suggestions:")
    
    if result['connected']:
        print("✅ TCP connection successful!")
        if not result.get('grasshopper_response'):
            print("❌ But no valid Grasshopper response")
            print("   → Check if Grasshopper TCP component is properly loaded")
            print("   → Verify component shows correct port (8081)")
    else:
        if result.get('error_code') == 111 or 'refused' in str(result.get('error', '')):
            print("❌ Connection refused - service not listening")
            print("   → Grasshopper TCP component not running")
            print("   → Check component is loaded and shows 'Listening on 0.0.0.0:8081'")
        elif 'timeout' in str(result.get('error', '')):
            print("❌ Connection timeout - host unreachable")
            print("   → Windows Firewall might be blocking WSL")
            print("   → Try disabling Windows Firewall temporarily")
        else:
            print(f"❌ Other network error: {result.get('error')}")
    
    # Test other common ports
    print(f"\n🔍 Testing other common ports on {host}:")
    common_ports = [8080, 8082, 3000, 5000]
    
    for test_port in common_ports:
        quick_result = test_connection_verbose(host, test_port, timeout=2.0)
        status = "✅" if quick_result['connected'] else "❌"
        print(f"   Port {test_port}: {status}")

if __name__ == "__main__":
    test_specific_host()