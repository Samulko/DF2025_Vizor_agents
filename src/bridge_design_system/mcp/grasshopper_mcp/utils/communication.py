"""
Communication utilities for Grasshopper MCP.

This module contains functions for communicating with the Grasshopper MCP server.
"""

import json
import os
import time

# Grasshopper MCP connection parameters
import platform
import socket
import subprocess
import sys
import traceback
from typing import Any, Dict, Optional, Tuple


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
    """Get Windows host IP from WSL with lazy detection."""
    # Priority 1: Environment variable (fastest)
    if "GRASSHOPPER_HOST" in os.environ:
        return os.environ["GRASSHOPPER_HOST"]
    
    # Priority 2: Simple WSL detection for immediate use
    if "microsoft" in platform.uname().release.lower():
        # Quick method: try /etc/resolv.conf first
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.startswith("nameserver") and not "127.0.0.53" in line:
                        return line.split()[1]
        except Exception:
            pass
        
        # Quick method: try default route
        try:
            result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "default" in line and "via" in line:
                        parts = line.split()
                        via_idx = parts.index("via")
                        if via_idx + 1 < len(parts):
                            return parts[via_idx + 1]
        except Exception:
            pass
    
    return "localhost"


def get_windows_host_enhanced():
    """Enhanced Windows host detection with comprehensive testing."""
    candidates = []
    port = int(os.environ.get("GRASSHOPPER_PORT", "8081"))
    
    # Priority 1: Environment variable
    if "GRASSHOPPER_HOST" in os.environ:
        return os.environ["GRASSHOPPER_HOST"]
    
    if "microsoft" in platform.uname().release.lower():
        # Running in WSL
        print("WSL detected, trying multiple methods to find Windows host...", file=sys.stderr)
        
        # Method 1: PowerShell interop to get WSL adapter IP
        try:
            result = subprocess.run(
                ["powershell.exe", "-Command", 
                 "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like '*WSL*'} | Select-Object -First 1).IPAddress"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0 and result.stdout.strip():
                wsl_ip = result.stdout.strip()
                # The WSL adapter IP is on Windows side, we need the gateway
                # Extract network prefix and use .1
                parts = wsl_ip.split('.')
                if len(parts) == 4:
                    gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
                    candidates.append(gateway)
        except Exception:
            pass
        
        # Method 2: ip route (default gateway)
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
        
        # Method 3: /etc/resolv.conf (DNS = Windows host in WSL2)
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.startswith("nameserver") and not "127.0.0.53" in line:
                        ip = line.split()[1]
                        candidates.append(ip)
        except Exception:
            pass
        
        # Method 4: host.docker.internal resolution
        try:
            import socket as resolver_socket
            docker_host = resolver_socket.gethostbyname("host.docker.internal")
            if docker_host and not docker_host.startswith("127."):
                candidates.append(docker_host)
        except Exception:
            pass
        
        # Method 5: Common WSL2 gateways
        common_gateways = [
            "172.17.0.1",    # Docker default
            "172.18.0.1",    # Docker alternate
            "172.19.0.1",    # Docker alternate
            "172.20.0.1",    # Docker alternate
            "172.21.0.1",    # Docker alternate
            "172.22.0.1",    # Docker alternate
            "172.23.0.1",    # Docker alternate
            "172.24.0.1",    # Docker alternate
            "172.25.0.1",    # Docker alternate
            "172.26.0.1",    # Docker alternate
            "172.27.0.1",    # Docker alternate
            "172.28.0.1",    # Docker alternate
            "172.29.0.1",    # Docker alternate
            "172.30.0.1",    # Docker alternate
            "172.31.0.1",    # Docker alternate
            "192.168.65.2",  # Docker Desktop
        ]
        candidates.extend(common_gateways)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique_candidates.append(c)
        
        # Test each candidate
        print(f"Testing {len(unique_candidates)} candidate IPs for Grasshopper on port {port}...", file=sys.stderr)
        for ip in unique_candidates:
            if test_connection(ip, port):
                print(f"Found working Windows host: {ip}", file=sys.stderr)
                return ip
        
        # Fallback: localhost (might work with port forwarding)
        if test_connection("localhost", port):
            print("Using localhost (port forwarding detected)", file=sys.stderr)
            return "localhost"
            
        print("WARNING: Could not find Windows host. Set GRASSHOPPER_HOST environment variable.", file=sys.stderr)
        print("Tried IPs:", ", ".join(unique_candidates[:10]), "...", file=sys.stderr)
    
    return "localhost"


GRASSHOPPER_HOST = os.environ.get("GRASSHOPPER_HOST", get_windows_host())
GRASSHOPPER_PORT = int(os.environ.get("GRASSHOPPER_PORT", "8081"))

# Log the connection target
print(f"Grasshopper TCP bridge target: {GRASSHOPPER_HOST}:{GRASSHOPPER_PORT}", file=sys.stderr)


def send_to_grasshopper(
    command_type: str, params: Optional[Dict[str, Any]] = None, retry_count: int = 3
) -> Dict[str, Any]:
    """
    Send a command to the Grasshopper MCP server.

    Args:
        command_type: The type of command to send
        params: Optional parameters for the command

    Returns:
        Dict[str, Any]: The response from the Grasshopper MCP server
    """
    if params is None:
        params = {}

    # Create command
    command = {"type": command_type, "parameters": params}
    
    last_error = None
    for attempt in range(retry_count):
        if attempt > 0:
            print(f"Retry attempt {attempt + 1}/{retry_count}...", file=sys.stderr)
            time.sleep(1)  # Brief pause between retries
            
            # On retry, try enhanced detection if simple method failed
            if attempt == 1:
                print("Trying enhanced host detection...", file=sys.stderr)
                global GRASSHOPPER_HOST
                enhanced_host = get_windows_host_enhanced()
                if enhanced_host != GRASSHOPPER_HOST:
                    GRASSHOPPER_HOST = enhanced_host
                    print(f"Switching to enhanced detected host: {GRASSHOPPER_HOST}", file=sys.stderr)
    
        try:
            print(
                f"Sending command to Grasshopper: {command_type} with params: {params}", file=sys.stderr
            )

            # Log script parameter specifically for debugging
            if "script" in params:
                print(f"Script parameter found! Length: {len(params['script'])}", file=sys.stderr)
                print(f"Script preview: {params['script'][:100]}...", file=sys.stderr)

            # Connect to Grasshopper MCP with timeout
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0)  # 5 second timeout
            
            try:
                client.connect((GRASSHOPPER_HOST, GRASSHOPPER_PORT))
            except socket.timeout:
                raise Exception(f"Connection timeout to {GRASSHOPPER_HOST}:{GRASSHOPPER_PORT}")
            except socket.error as e:
                raise Exception(f"Connection failed to {GRASSHOPPER_HOST}:{GRASSHOPPER_PORT}: {e}")

            # Send command
            command_json = json.dumps(command)
            client.sendall((command_json + "\n").encode("utf-8"))
            print(f"Command sent to {GRASSHOPPER_HOST}:{GRASSHOPPER_PORT}", file=sys.stderr)
            print(f"Command type: {command_type}, JSON length: {len(command_json)}", file=sys.stderr)

            # Receive response with larger buffer and timeout
            client.settimeout(10.0)  # 10 second timeout for response
            response_data = b""
            max_size = 1024 * 1024  # 1MB max response
            
            while len(response_data) < max_size:
                try:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                    if response_data.endswith(b"\n"):
                        break
                except socket.timeout:
                    if response_data:
                        # We got partial data, might be enough
                        break
                    else:
                        raise Exception("Response timeout - no data received")

            client.close()
            
            if not response_data:
                raise Exception("Empty response from Grasshopper")
                
            # Handle potential BOM and parse
            response_str = response_data.decode("utf-8-sig").strip()
            print(f"Response received, length: {len(response_str)}", file=sys.stderr)

            # Parse JSON response
            try:
                response = json.loads(response_str)
                return response
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}", file=sys.stderr)
                print(f"Raw response: {response_str[:200]}...", file=sys.stderr)
                raise Exception(f"Invalid JSON response: {e}")
        except Exception as e:
            last_error = e
            print(f"Error communicating with Grasshopper: {str(e)}", file=sys.stderr)
            if attempt == retry_count - 1:
                traceback.print_exc(file=sys.stderr)
            continue
    
    # All retries failed
    return {
        "success": False, 
        "error": f"Failed after {retry_count} attempts: {str(last_error)}",
        "host_tried": GRASSHOPPER_HOST,
        "port_tried": GRASSHOPPER_PORT
    }


def diagnose_connection() -> Dict[str, Any]:
    """Run diagnostics to help troubleshoot connection issues."""
    print("\n=== Grasshopper Connection Diagnostics ===", file=sys.stderr)
    
    diagnostics = {
        "platform": platform.system(),
        "is_wsl": "microsoft" in platform.uname().release.lower(),
        "environment": {
            "GRASSHOPPER_HOST": os.environ.get("GRASSHOPPER_HOST", "not set"),
            "GRASSHOPPER_PORT": os.environ.get("GRASSHOPPER_PORT", "not set")
        },
        "detected_hosts": [],
        "connection_tests": {}
    }
    
    # Get list of potential hosts
    print("\nDetecting potential Windows hosts...", file=sys.stderr)
    original_host = os.environ.get("GRASSHOPPER_HOST")
    if original_host:
        os.environ.pop("GRASSHOPPER_HOST")  # Temporarily remove to test detection
    
    detected_host = get_windows_host()
    diagnostics["detected_hosts"].append(detected_host)
    
    if original_host:
        os.environ["GRASSHOPPER_HOST"] = original_host
        diagnostics["detected_hosts"].insert(0, original_host)
    
    # Test each potential host
    port = int(os.environ.get("GRASSHOPPER_PORT", "8081"))
    print(f"\nTesting connections on port {port}...", file=sys.stderr)
    
    for host in set(diagnostics["detected_hosts"]):
        print(f"Testing {host}:{port}... ", end="", file=sys.stderr)
        
        # Basic connectivity test
        can_connect = test_connection(host, port, timeout=2.0)
        print("OK" if can_connect else "FAILED", file=sys.stderr)
        
        # Try actual Grasshopper command
        if can_connect:
            try:
                global GRASSHOPPER_HOST, GRASSHOPPER_PORT
                old_host = GRASSHOPPER_HOST
                GRASSHOPPER_HOST = host
                GRASSHOPPER_PORT = port
                
                response = send_to_grasshopper("ping", {}, retry_count=1)
                grasshopper_works = response.get("success", False)
                
                GRASSHOPPER_HOST = old_host
            except Exception as e:
                grasshopper_works = False
                response = {"error": str(e)}
        else:
            grasshopper_works = False
            response = {"error": "Connection failed"}
        
        diagnostics["connection_tests"][host] = {
            "tcp_connect": can_connect,
            "grasshopper_ping": grasshopper_works,
            "response": response
        }
    
    # Additional WSL-specific checks
    if diagnostics["is_wsl"]:
        print("\nWSL-specific information:", file=sys.stderr)
        
        # Check Windows Defender Firewall rules
        try:
            result = subprocess.run(
                ["powershell.exe", "-Command", 
                 "Get-NetFirewallRule -DisplayName '*Grasshopper*' | Select-Object DisplayName,Enabled"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                diagnostics["firewall_rules"] = result.stdout.strip()
        except Exception:
            diagnostics["firewall_rules"] = "Could not check firewall rules"
        
        # Get WSL network info
        try:
            result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "inet " in line and "eth0" in result.stdout:
                        diagnostics["wsl_ip"] = line.strip()
                        break
        except Exception:
            pass
    
    print("\n=== Diagnostics Complete ===", file=sys.stderr)
    return diagnostics
