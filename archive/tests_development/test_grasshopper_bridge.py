#!/usr/bin/env python3
"""
Test script for Grasshopper Bridge Component

This script helps test the Grasshopper MCP Bridge by sending commands
and monitoring results.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any
import json


class BridgeTestClient:
    def __init__(self, server_url: str = "http://localhost:8001"):
        self.server_url = server_url
        print(f"🔗 Test client configured for: {self.server_url}")
        
    async def send_test_command(self, endpoint: str) -> Dict[str, Any]:
        """Send a test command to the server"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.server_url}{endpoint}") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Command sent: {endpoint}")
                        print(f"   Command ID: {result.get('command_id', 'N/A')}")
                        return result
                    else:
                        print(f"❌ Failed to send command: {response.status}")
                        return {}
            except Exception as e:
                print(f"❌ Error sending command: {e}")
                return {}
    
    async def check_status(self) -> Dict[str, Any]:
        """Check server status"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.server_url}/test/status") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
            except Exception as e:
                print(f"❌ Error checking status: {e}")
                return {}
    
    async def wait_for_results(self, timeout: int = 30):
        """Wait for command results and display them"""
        print(f"\n⏳ Waiting for bridge to execute commands (timeout: {timeout}s)...")
        
        start_time = time.time()
        last_completed = 0
        
        while (time.time() - start_time) < timeout:
            status = await self.check_status()
            
            if status:
                completed = status.get('completed_commands', 0)
                pending = status.get('pending_commands', 0)
                
                if completed > last_completed:
                    print(f"📈 Progress: {completed} completed, {pending} pending")
                    
                    # Show recent command history
                    history = status.get('command_history', [])
                    for cmd in history[-3:]:  # Show last 3 commands
                        status_icon = "✅" if cmd['success'] else "❌"
                        print(f"   {status_icon} {cmd['command_id'][:8]}: {cmd.get('result', {})}")
                    
                    last_completed = completed
                
                if pending == 0 and completed > 0:
                    print("🎉 All commands completed!")
                    break
            
            await asyncio.sleep(2)
        
        # Final status
        final_status = await self.check_status()
        if final_status:
            print(f"\n📊 Final Status:")
            print(f"   Completed: {final_status.get('completed_commands', 0)}")
            print(f"   Pending: {final_status.get('pending_commands', 0)}")


async def run_interactive_test():
    """Run interactive test menu"""
    client = BridgeTestClient()
    
    print("""
🧪 Grasshopper Bridge Test Client

Make sure:
1. Test server is running: python grasshopper_bridge_test_server.py
2. Grasshopper is open with MCP Bridge component
3. Bridge is connected to http://localhost:8001

Choose a test:
""")
    
    tests = {
        "1": ("Add Point Component", "/test/add_point_component"),
        "2": ("Add Number Slider", "/test/add_number_slider"), 
        "3": ("Add Multiple Components", "/test/batch_commands"),
        "4": ("Clear Document", "/test/clear_document"),
        "5": ("Set Component Value", "/test/set_value"),
        "6": ("Connect Components", "/test/connect_components"),
        "7": ("Check Status Only", None),
        "8": ("Run Full Test Sequence", "sequence")
    }
    
    for key, (description, _) in tests.items():
        print(f"{key}. {description}")
    
    choice = input("\nEnter choice (1-8): ").strip()
    
    if choice in tests:
        description, endpoint = tests[choice]
        print(f"\n🚀 Running: {description}")
        
        if choice == "7":
            # Status check only
            status = await client.check_status()
            print(f"📊 Server Status: {json.dumps(status, indent=2)}")
            
        elif choice == "8":
            # Full sequence test
            await run_full_test_sequence(client)
            
        else:
            # Single command test
            await client.send_test_command(endpoint)
            await client.wait_for_results()
    
    else:
        print("❌ Invalid choice")


async def run_full_test_sequence(client: BridgeTestClient):
    """Run a comprehensive test sequence"""
    print("\n🔄 Running Full Test Sequence...")
    
    sequence = [
        ("Clear document", "/test/clear_document"),
        ("Add point component", "/test/add_point_component"),
        ("Add number slider", "/test/add_number_slider"),
        ("Add batch of components", "/test/batch_commands"),
        ("Set component value", "/test/set_value")
    ]
    
    for step, (description, endpoint) in enumerate(sequence, 1):
        print(f"\n📍 Step {step}: {description}")
        await client.send_test_command(endpoint)
        await asyncio.sleep(2)  # Give bridge time to process
    
    print(f"\n⏳ Waiting for all commands to complete...")
    await client.wait_for_results(timeout=60)


async def monitor_bridge():
    """Continuously monitor bridge activity"""
    client = BridgeTestClient()
    
    print("👀 Monitoring bridge activity (Ctrl+C to stop)...")
    
    try:
        last_completed = 0
        while True:
            status = await client.check_status()
            
            if status:
                completed = status.get('completed_commands', 0)
                pending = status.get('pending_commands', 0)
                
                if completed != last_completed:
                    print(f"📈 Update: {completed} completed, {pending} pending")
                    last_completed = completed
            
            await asyncio.sleep(3)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        asyncio.run(monitor_bridge())
    else:
        asyncio.run(run_interactive_test())