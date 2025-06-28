#!/usr/bin/env python3
"""
Simple listener to debug HOLO1_Model messages
"""

import time
import roslibpy

def handle_model_message(message):
    print(f"\n🔔 RECEIVED MESSAGE ON /HOLO1_Model:")
    print(f"📝 Raw message: {message}")
    print(f"📊 Message type: {type(message)}")
    
    if 'data' in message:
        print(f"📄 Data field: {message['data']}")
        
        # Try to parse as JSON
        try:
            import json
            parsed = json.loads(message['data'])
            print(f"✅ Parsed JSON: {parsed}")
        except Exception as e:
            print(f"❌ JSON parse failed: {e}")

def main():
    print("🎯 Simple HOLO1_Model Listener")
    print("Subscribing to /HOLO1_Model with std_msgs/String")
    
    client = roslibpy.Ros(host='localhost', port=9090)
    client.run()
    
    if not client.is_connected:
        print("❌ Failed to connect")
        return
    
    print("✅ Connected to ROS")
    
    topic = roslibpy.Topic(client, '/HOLO1_Model', 'std_msgs/String')
    topic.subscribe(handle_model_message)
    
    print("📡 Subscribed to /HOLO1_Model")
    print("Waiting for messages... (Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    
    topic.unsubscribe()
    client.terminate()

if __name__ == "__main__":
    main()