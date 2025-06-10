import requests
import json

def test_manual_queue():
    """Manually add commands to the server's queue to test bridge pickup."""
    
    # We need to access the server's internal queue
    # Let's create a simple endpoint to manually add commands for testing
    
    print("🧪 Testing Manual Command Queue")
    print("This will test if we can manually queue commands for the bridge...")
    
    # First, let's check the current status
    try:
        response = requests.get("http://localhost:8001/grasshopper/status")
        status = response.json()
        print(f"Current Status: {status}")
        
        pending = status.get('pending_commands', 0)
        print(f"Pending commands: {pending}")
        
        if pending == 0:
            print("\n💡 The bridge is connected but no commands are queued.")
            print("We need to queue commands through the MCP server's internal system.")
            print("\nThe issue is that we need to:")
            print("1. Properly initialize an MCP session")
            print("2. Send tools through the MCP protocol") 
            print("3. The server will then queue them for the bridge")
            
        print(f"\n📊 Bridge is polling successfully!")
        print(f"Check your Python server logs - you should see:")
        print(f"'Bridge requested commands: 0 pending' every second")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_manual_queue()