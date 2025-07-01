#!/usr/bin/env python3
"""
Quick diagnostics script for Grasshopper connection issues.
Run this script to test your WSL-Windows Grasshopper connection.
"""

import socket
import json
import time
import platform
import subprocess

def test_connection(host: str, port: int, timeout: float = 2.0) -> bool:
    """Test if we can connect to host:port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def test_grasshopper_response(host: str, port: int) -> dict:
    """Test if host responds like Grasshopper."""
    result = {"tcp_connect": False, "grasshopper_response": False, "error": None}
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        
        if sock.connect_ex((host, port)) == 0:
            result["tcp_connect"] = True
            
            # Test with actual Grasshopper command
            test_msg = '{"type":"get_components_in_group","parameters":{"groupName":"test"}}\n'
            sock.sendall(test_msg.encode('utf-8'))
            
            response_data = b""
            try:
                while len(response_data) < 1024:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response_data += chunk
                    if response_data.endswith(b"\n"):
                        break
                
                if response_data:
                    response_str = response_data.decode('utf-8-sig').strip()
                    parsed = json.loads(response_str)
                    if parsed.get("success") is not None:
                        result["grasshopper_response"] = True
                    else:
                        result["error"] = "Response not in Grasshopper format"
                else:
                    result["error"] = "No response"
                    
            except (socket.timeout, json.JSONDecodeError):
                result["error"] = "Timeout or invalid response"
        else:
            result["error"] = "Connection refused"
            
        sock.close()
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def get_wsl_candidates():
    """Get potential Windows host IPs from WSL."""
    candidates = []
    
    if "microsoft" in platform.uname().release.lower():
        # Method 1: ip route
        try:
            result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "default" in line and "via" in line:
                        parts = line.split()
                        via_idx = parts.index("via")
                        if via_idx + 1 < len(parts):
                            candidates.append(parts[via_idx + 1])
        except Exception:
            pass
        
        # Method 2: /etc/resolv.conf
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.startswith("nameserver") and not "127.0.0.53" in line:
                        candidates.append(line.split()[1])
        except Exception:
            pass
    
    # Add common ranges
    candidates.extend([
        "172.17.0.1", "172.18.0.1", "172.19.0.1", "172.20.0.1",
        "172.28.0.1", "172.28.192.1", "localhost"
    ])
    
    # Remove duplicates
    return list(dict.fromkeys(candidates))

def main():
    print("🔍 Grasshopper Connection Diagnostics")
    print("=" * 50)
    print()
    
    port = 8081
    candidates = get_wsl_candidates()
    
    print(f"Testing {len(candidates)} potential Windows hosts on port {port}:")
    print()
    
    working_hosts = []
    grasshopper_hosts = []
    
    for host in candidates:
        print(f"Testing {host}:{port}... ", end="", flush=True)
        result = test_grasshopper_response(host, port)
        
        if result["grasshopper_response"]:
            print("✅ GRASSHOPPER FOUND!")
            grasshopper_hosts.append(host)
            working_hosts.append(host)
        elif result["tcp_connect"]:
            print(f"⚠️ TCP OK, but {result.get('error', 'not Grasshopper')}")
            working_hosts.append(host)
        else:
            print(f"❌ {result.get('error', 'Failed')}")
    
    print()
    print("=" * 50)
    print("🏁 Diagnostics Complete!")
    print("=" * 50)
    
    if grasshopper_hosts:
        print(f"✅ Found Grasshopper on: {', '.join(grasshopper_hosts)}")
        print()
        print("📝 To fix the connection issue, run:")
        print(f"   export GRASSHOPPER_HOST={grasshopper_hosts[0]}")
        print("   # Add to ~/.bashrc or ~/.zshrc for persistence")
    elif working_hosts:
        print(f"⚠️ TCP connections work on: {', '.join(working_hosts)}")
        print("   But none are responding as Grasshopper servers")
        print()
        print("🛠️ Troubleshooting:")
        print("   1. Check if Grasshopper TCP component is loaded")
        print("   2. Verify component shows 'Listening on 0.0.0.0:8081'")
        print("   3. Try reloading the component")
    else:
        print("❌ No working connections found")
        print()
        print("🛠️ Next steps:")
        print("   1. Start Rhino Grasshopper on Windows")
        print("   2. Load the TCP bridge component")
        print("   3. Check Windows Firewall settings")
        print("   4. Verify WSL can reach Windows")

if __name__ == "__main__":
    main()