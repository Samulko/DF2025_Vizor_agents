#!/usr/bin/env python3
"""
Simple Grasshopper connection debug without any dependencies.
Run with: python simple_debug.py
"""

import socket
import json
import time

def test_host(host, port):
    """Test a specific host and port."""
    print(f"Testing {host}:{port}...")
    
    try:
        # Test basic connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        start_time = time.time()
        result = sock.connect_ex((host, port))
        response_time = (time.time() - start_time) * 1000
        
        if result == 0:
            print(f"✅ TCP connection successful ({response_time:.1f}ms)")
            
            # Test if it's actually Grasshopper
            try:
                test_msg = '{"type":"get_components_in_group","parameters":{"groupName":"test"}}\n'
                sock.sendall(test_msg.encode('utf-8'))
                sock.settimeout(3.0)
                
                response_data = b""
                while len(response_data) < 10240:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response_data += chunk
                    if response_data.endswith(b"\n"):
                        break
                
                if response_data:
                    response_str = response_data.decode('utf-8-sig', errors='ignore').strip()
                    print(f"✅ Grasshopper responded! ({len(response_str)} chars)")
                    
                    # Try to parse as JSON
                    try:
                        parsed = json.loads(response_str)
                        if parsed.get("success"):
                            print("✅ Valid Grasshopper response!")
                        else:
                            print(f"⚠️ Grasshopper error: {parsed.get('error', 'Unknown')}")
                    except json.JSONDecodeError:
                        print("⚠️ Response not valid JSON, but server is responding")
                        print(f"Raw response preview: {response_str[:100]}...")
                else:
                    print("❌ No response from server")
                    
            except socket.timeout:
                print("❌ Server connected but no response (timeout)")
            except Exception as e:
                print(f"❌ Error testing Grasshopper: {e}")
        else:
            error_msgs = {
                111: "Connection refused (service not running)",
                110: "Connection timeout",
                113: "No route to host"
            }
            error_msg = error_msgs.get(result, f"Connection failed (error {result})")
            print(f"❌ {error_msg}")
            
        sock.close()
        
    except Exception as e:
        print(f"❌ Network error: {e}")
        
    print()

def main():
    print("🔍 Simple Grasshopper Connection Debug")
    print("=" * 40)
    print()
    
    # Test the problematic host from the error log
    test_host("172.19.144.1", 8081)
    
    # Test other common possibilities
    print("Testing other common configurations:")
    hosts_to_test = [
        ("172.28.192.1", 8081),  # Common WSL gateway
        ("172.17.0.1", 8081),    # Docker default
        ("localhost", 8081),     # Port forwarding
        ("127.0.0.1", 8081),     # Localhost
        ("172.19.144.1", 8080),  # Different port
        ("172.19.144.1", 3000),  # Web service port
    ]
    
    for host, port in hosts_to_test:
        test_host(host, port)
    
    print("🏁 Debug complete!")
    print()
    print("💡 If any host showed a successful TCP connection:")
    print("   Set: export GRASSHOPPER_HOST=<working_host>")
    print()
    print("💡 If no connections worked:")
    print("   1. Check Rhino Grasshopper is running")
    print("   2. Load TCP bridge component in Grasshopper")
    print("   3. Verify component shows 'Listening on 0.0.0.0:8081'")
    print("   4. Check Windows Firewall settings")

if __name__ == "__main__":
    main()