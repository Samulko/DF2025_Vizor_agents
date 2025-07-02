#!/usr/bin/env python3
"""Test actual Grasshopper commands."""

import json
import socket
import os

def send_command(host, port, command_type, params=None):
    """Send a command to Grasshopper."""
    if params is None:
        params = {}
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect((host, port))
        
        command = {"type": command_type, "parameters": params}
        command_json = json.dumps(command)
        client.sendall((command_json + "\n").encode("utf-8"))
        
        response_data = b""
        while len(response_data) < 10240:
            chunk = client.recv(1024)
            if not chunk:
                break
            response_data += chunk
            if response_data.endswith(b"\n"):
                break
        
        client.close()
        
        if response_data:
            return json.loads(response_data.decode("utf-8-sig").strip())
        else:
            return {"success": False, "error": "No response"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    # Use the host that worked
    host = os.environ.get("GRASSHOPPER_HOST", "172.28.192.1")
    port = 8081
    
    print(f"Testing Grasshopper commands on {host}:{port}\n")
    
    # Test different command types that might be supported
    test_commands = [
        ("get_document_info", {}),
        ("get_all_components", {}),
        ("add_component", {"type": "Number Slider", "x": 100, "y": 100}),
        ("execute_script", {"script": "print('test')"}),
        ("list_component_types", {}),
    ]
    
    for cmd_type, params in test_commands:
        print(f"Testing: {cmd_type}")
        response = send_command(host, port, cmd_type, params)
        
        if response.get("success"):
            print(f"  ✓ Success!")
            if "result" in response:
                result = response["result"]
                if isinstance(result, (dict, list)):
                    print(f"  Result: {json.dumps(result, indent=2)[:200]}...")
                else:
                    print(f"  Result: {result}")
        else:
            print(f"  ✗ Failed: {response.get('error', 'Unknown error')}")
        print()
    
    # Now set the environment variable for the system
    print("\nTo use this host, set:")
    print(f"export GRASSHOPPER_HOST={host}")

if __name__ == "__main__":
    main()