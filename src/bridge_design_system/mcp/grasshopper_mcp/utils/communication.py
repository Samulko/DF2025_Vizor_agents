"""
Communication utilities for Grasshopper MCP.

This module contains functions for communicating with the Grasshopper MCP server.
"""

import json

# Grasshopper MCP connection parameters
import platform
import socket
import subprocess
import sys
import traceback
from typing import Any, Dict, Optional


def get_windows_host():
    """Get Windows host IP from WSL."""
    if "microsoft" in platform.uname().release.lower():
        # Running in WSL
        try:
            # Method 1: Try default route (more reliable for WSL2)
            result = subprocess.run(["ip", "route", "show"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "default" in line:
                        # Extract IP address from: default via 172.28.192.1 dev eth0
                        parts = line.split()
                        if len(parts) >= 3 and parts[1] == "via":
                            windows_ip = parts[2]
                            print(
                                f"WSL detected Windows host via default route: {windows_ip}",
                                file=sys.stderr,
                            )
                            return windows_ip

            # Method 2: Fallback to /etc/resolv.conf
            result = subprocess.run(
                ["grep", "nameserver", "/etc/resolv.conf"], capture_output=True, text=True
            )
            if result.returncode == 0:
                windows_ip = result.stdout.strip().split()[1]
                print(f"WSL detected Windows host via resolv.conf: {windows_ip}", file=sys.stderr)
                return windows_ip
        except Exception as e:
            print(f"Error detecting Windows host: {e}", file=sys.stderr)
    return "localhost"


GRASSHOPPER_HOST = get_windows_host()
GRASSHOPPER_PORT = 8081  # TCP bridge port (GH_MCPComponent listens on 8081)

# Log the connection target
print(f"Grasshopper TCP bridge target: {GRASSHOPPER_HOST}:{GRASSHOPPER_PORT}", file=sys.stderr)


def send_to_grasshopper(
    command_type: str, params: Optional[Dict[str, Any]] = None
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

    try:
        print(
            f"Sending command to Grasshopper: {command_type} with params: {params}", file=sys.stderr
        )

        # Log script parameter specifically for debugging
        if "script" in params:
            print(f"Script parameter found! Length: {len(params['script'])}", file=sys.stderr)
            print(f"Script preview: {params['script'][:100]}...", file=sys.stderr)

        # Connect to Grasshopper MCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((GRASSHOPPER_HOST, GRASSHOPPER_PORT))

        # Send command
        command_json = json.dumps(command)
        client.sendall((command_json + "\n").encode("utf-8"))
        print(f"Command sent: {command_json}", file=sys.stderr)
        print(f"Command JSON length: {len(command_json)}", file=sys.stderr)

        # Receive response
        response_data = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response_data += chunk
            if response_data.endswith(b"\n"):
                break

        # Handle potential BOM
        response_str = response_data.decode("utf-8-sig").strip()
        print(f"Response received: {response_str}", file=sys.stderr)

        # Parse JSON response
        response = json.loads(response_str)
        client.close()
        return response
    except Exception as e:
        print(f"Error communicating with Grasshopper: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"success": False, "error": f"Error communicating with Grasshopper: {str(e)}"}
