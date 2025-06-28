#!/usr/bin/env python3
"""
Correct transform listener using geometry_msgs/Pose message type.
Based on the ROS bridge error, HOLO1_Transform uses geometry_msgs/Pose, not std_msgs/String.
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
    """Handle incoming transform messages with geometry_msgs/Pose format"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    print(f"\n🎯 TRANSFORM DATA RECEIVED at {timestamp}")
    print("=" * 60)
    
    print(f"📝 Raw Message: {message}")
    print(f"📊 Message Type: {type(message)}")
    
    # geometry_msgs/Pose structure:
    # position:
    #   x: float64
    #   y: float64  
    #   z: float64
    # orientation:
    #   x: float64
    #   y: float64
    #   z: float64
    #   w: float64
    
    if isinstance(message, dict):
        print("\n🔍 GEOMETRY_MSGS/POSE STRUCTURE:")
        
        # Extract position
        if 'position' in message:
            pos = message['position']
            print(f"📍 Position:")
            print(f"   x: {pos.get('x', 'N/A')}")
            print(f"   y: {pos.get('y', 'N/A')}")
            print(f"   z: {pos.get('z', 'N/A')}")
        
        # Extract orientation (quaternion)
        if 'orientation' in message:
            quat = message['orientation']
            print(f"🔄 Orientation (Quaternion):")
            print(f"   x: {quat.get('x', 'N/A')}")
            print(f"   y: {quat.get('y', 'N/A')}")
            print(f"   z: {quat.get('z', 'N/A')}")
            print(f"   w: {quat.get('w', 'N/A')}")
        
        print(f"\n🔬 FULL JSON STRUCTURE:")
        print(json.dumps(message, indent=2))
        
        # Convert to the format expected by main.py
        print(f"\n🎯 FORMAT FOR MAIN.PY:")
        if 'position' in message and 'orientation' in message:
            pos = message['position']
            quat = message['orientation']
            
            # main.py expects: pose['position'] and pose['quaternion'] 
            # where quaternion is [w, x, y, z] format
            main_py_format = {
                'position': [pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)],
                'quaternion': [quat.get('w', 0), quat.get('x', 0), quat.get('y', 0), quat.get('z', 0)]
            }
            print(json.dumps(main_py_format, indent=2))
    
    print("=" * 60)

def main():
    print("🎯 Correct HOLO1_Transform Listener")
    print("=" * 40)
    print("Using geometry_msgs/Pose message type")
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
        
        # Setup transform listener with CORRECT message type
        transform_topic = roslibpy.Topic(
            client, 
            "/HOLO1_Transform", 
            "geometry_msgs/Pose"  # ← This was the issue!
        )
        
        transform_topic.subscribe(handle_transform_message)
        print("✅ Subscribed to /HOLO1_Transform (geometry_msgs/Pose)")
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()