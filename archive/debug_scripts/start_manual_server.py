#!/usr/bin/env python3
"""Simple script to start the manual MCP server directly."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bridge_design_system.mcp.manual_mcp_server import ManualMCPServer

if __name__ == "__main__":
    print("🚀 Starting Manual MCP Server directly...")
    print("This bypasses the main.py entry point to avoid import issues")
    print()
    
    # Create and run server
    server = ManualMCPServer(
        grasshopper_url="http://localhost:8080",
        port=8001,
        bridge_mode=True
    )
    
    print("Server configuration:")
    print(f"  Port: 8001")
    print(f"  Bridge mode: True")
    print(f"  Grasshopper URL: http://localhost:8080")
    print()
    
    server.run()