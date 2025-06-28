#!/usr/bin/env python3
"""
Simple continuous listener for HOLO1_Transform topic.
Just run it and it will listen forever until you stop it.
"""

import time
import json
from datetime import datetime

try:
    import roslibpy
except ImportError:
    print("❌ roslibpy not available - install with: pip install roslibpy")
    exit(1)

def handle_transform_message(message):
    """Handle incoming transform messages"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    print(f"\n🎯 TRANSFORM DATA RECEIVED at {timestamp}")
    print("=" * 50)
    
    # Extract the data
    data = message.get('data', message)
    print(f"📝 Raw Data: {data}")
    
    # Try to parse as JSON
    if isinstance(data, str) and (data.strip().startswith('{') or data.strip().startswith('[')):
        try:
            parsed = json.loads(data)
            print("\n🔍 PARSED JSON:")
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse failed: {e}")
    
    print("=" * 50)

def main():
    print("🎯 Continuous HOLO1_Transform Listener")
    print("=" * 40)
    print("Listening to /HOLO1_Transform...")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    # Connect to ROS
    try:
        print("🔌 Connecting to ROS bridge...")
        client = roslibpy.Ros(host='localhost', port=9090)
        client.run()
        
        if not client.is_connected:
            print("❌ Failed to connect to ROS bridge")
            return
        
        print("✅ Connected to ROS bridge")
        
        # Setup transform listener
        transform_topic = roslibpy.Topic(
            client, 
            "/HOLO1_Transform", 
            "std_msgs/String"
        )
        
        transform_topic.subscribe(handle_transform_message)
        print("✅ Subscribed to /HOLO1_Transform")
        print("\n👂 Listening for transform data...")
        print("   Press your AR update button now!")
        
        # Keep listening
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping listener...")
        
        # Cleanup
        transform_topic.unsubscribe()
        client.terminate()
        print("✅ Disconnected from ROS")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()