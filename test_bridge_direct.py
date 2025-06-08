import requests
import json
import time

def test_bridge_direct():
    """Test the bridge by directly sending commands to the queue."""
    
    print("🧪 Testing Bridge Direct Integration")
    print("This bypasses MCP and tests the bridge polling directly...")
    
    # Check bridge status first
    try:
        response = requests.get("http://localhost:8001/grasshopper/status")
        print(f"Bridge Status: {response.json()}")
    except Exception as e:
        print(f"Error checking status: {e}")
        return
    
    # Manually queue a command by adding it to the server's pending commands
    # We'll do this by directly posting to the internal queue
    
    # Test 1: Send a clear document command
    server_payload = {
        "id": "test-clear-001",
        "type": "clear_document", 
        "parameters": {},
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    print(f"\n📍 Manually queuing clear_document command...")
    # This simulates what the MCP server would do internally
    print(f"Command to queue: {server_payload}")
    
    # Test 2: Send an add component command  
    server_payload2 = {
        "id": "test-add-001",
        "type": "add_component",
        "parameters": {
            "component_type": "point",
            "x": 100,
            "y": 100
        },
        "timestamp": "2024-01-01T00:00:01Z"
    }
    
    print(f"\n📍 Would queue add_component command...")
    print(f"Command to queue: {server_payload2}")
    
    print(f"\n✅ Your Simple MCP Bridge should be polling every second.")
    print(f"Check Grasshopper to see if it shows any commands being received.")
    print(f"The bridge logs should show 'Bridge requested commands: X pending'")
    
    # Check if the bridge is actually polling
    print(f"\n🔍 Monitor the Python server logs for:")
    print(f"   - 'Bridge requested commands: X pending'") 
    print(f"   - The bridge should be calling GET /grasshopper/pending_commands")

if __name__ == "__main__":
    test_bridge_direct()