#!/usr/bin/env python3
"""Direct test of Grasshopper connection without full imports."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only what we need
import json
import socket
import subprocess
import platform
import time

def test_connection(host: str, port: int, timeout: float = 1.0) -> bool:
    """Test if we can connect to host:port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def get_windows_host():
    """Minimal version to detect Windows host."""
    candidates = []
    
    if "microsoft" in platform.uname().release.lower():
        print("WSL detected, trying to find Windows host...")
        
        # Try PowerShell
        try:
            result = subprocess.run(
                ["powershell.exe", "-Command", 
                 "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like '*WSL*'} | Select-Object -First 1).IPAddress"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0 and result.stdout.strip():
                wsl_ip = result.stdout.strip()
                parts = wsl_ip.split('.')
                if len(parts) == 4:
                    gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
                    candidates.append(gateway)
                    print(f"  PowerShell method found: {gateway}")
        except Exception as e:
            print(f"  PowerShell method failed: {e}")
        
        # Try ip route
        try:
            result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "default" in line and "via" in line:
                        parts = line.split()
                        via_idx = parts.index("via")
                        if via_idx + 1 < len(parts):
                            candidates.append(parts[via_idx + 1])
                            print(f"  IP route method found: {parts[via_idx + 1]}")
        except Exception as e:
            print(f"  IP route method failed: {e}")
        
        # Try /etc/resolv.conf
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.startswith("nameserver") and not "127.0.0.53" in line:
                        ip = line.split()[1]
                        candidates.append(ip)
                        print(f"  resolv.conf method found: {ip}")
        except Exception as e:
            print(f"  resolv.conf method failed: {e}")
    
    return candidates

def main():
    print("=== Direct Grasshopper Connection Test ===\n")
    
    port = 8081
    print(f"Testing on port {port}\n")
    
    # Get candidates
    candidates = get_windows_host()
    if not candidates:
        candidates = ["localhost", "127.0.0.1"]
        print("No WSL hosts detected, trying localhost")
    
    # Remove duplicates
    candidates = list(dict.fromkeys(candidates))
    
    print(f"\nTesting {len(candidates)} host candidates:")
    for host in candidates:
        connected = test_connection(host, port)
        print(f"  {host}:{port} - {'✓ CONNECTED' if connected else '✗ Failed'}")
        
        if connected:
            # Try to send a ping command
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(5.0)
                client.connect((host, port))
                
                command = {"type": "ping", "parameters": {}}
                command_json = json.dumps(command)
                client.sendall((command_json + "\n").encode("utf-8"))
                
                response_data = b""
                while len(response_data) < 1024:
                    chunk = client.recv(1024)
                    if not chunk:
                        break
                    response_data += chunk
                    if response_data.endswith(b"\n"):
                        break
                
                client.close()
                
                if response_data:
                    response = json.loads(response_data.decode("utf-8-sig").strip())
                    if response.get("success"):
                        print(f"    ✓ Grasshopper responded successfully!")
                        print(f"    Set these environment variables:")
                        print(f"      export GRASSHOPPER_HOST={host}")
                        print(f"      export GRASSHOPPER_PORT={port}")
                        return
                    else:
                        print(f"    ✗ Grasshopper error: {response.get('error')}")
                else:
                    print(f"    ✗ No response from Grasshopper")
                    
            except Exception as e:
                print(f"    ✗ Error sending command: {e}")
    
    print("\n❌ Could not connect to Grasshopper!")
    print("\nTroubleshooting:")
    print("1. Is the Grasshopper TCP bridge component loaded in Rhino?")
    print("2. Is it listening on port 8081?")
    print("3. Check Windows Firewall - allow connections from WSL")
    print("4. Try running this on Windows side to test locally")

if __name__ == "__main__":
    main()