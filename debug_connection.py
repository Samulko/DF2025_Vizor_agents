#!/usr/bin/env python3
"""
Debug specific connection issue with Grasshopper.
This will test the exact host that was detected and provide detailed error info.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_specific_host():
    from bridge_design_system.mcp.grasshopper_mcp.utils.communication import test_connection_verbose
    
    # Test the host that was detected in the error log
    host = "172.19.144.1"
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