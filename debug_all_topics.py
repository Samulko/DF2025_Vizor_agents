#!/usr/bin/env python3
"""
Debug listener for ALL available topics to see what's actually being published.
This will help us identify if the AR update button is publishing to a different topic.
"""

import time
import json
from datetime import datetime

try:
    import roslibpy
except ImportError:
    print("❌ roslibpy not available - install with: pip install roslibpy")
    exit(1)

def create_message_handler(topic_name, msg_type):
    """Create a message handler for a specific topic"""
    def handle_message(message):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"\n🔔 [{timestamp}] MESSAGE on {topic_name} ({msg_type})")
        print("=" * 50)
        print(f"📝 Data: {message}")
        print("=" * 50)
    return handle_message

def main():
    print("🔍 Debug ALL Topics Listener")
    print("=" * 40)
    print("This will listen to ALL known topics to see")
    print("what gets published when you press update")
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
        
        # Subscribe to all the topics we know about
        topics_to_monitor = [
            ('HOLO1_Transform', 'geometry_msgs/Pose'),
            ('HOLO1_Model', 'std_msgs/String'),  # Just in case
            ('HOLO1_Command', 'std_msgs/String'),
            ('HOLO1_GazePoint', 'std_msgs/String'),
            # Add some other potential transform topics
            ('transform', 'geometry_msgs/Pose'),
            ('transforms', 'geometry_msgs/Pose'),
            ('holo_transform', 'geometry_msgs/Pose'),
            ('model_update', 'std_msgs/String'),
            ('ar_update', 'std_msgs/String'),
        ]
        
        subscribers = []
        
        for topic_name, msg_type in topics_to_monitor:
            try:
                print(f"📡 Subscribing to /{topic_name} ({msg_type})")
                
                topic = roslibpy.Topic(client, f"/{topic_name}", msg_type)
                topic.subscribe(create_message_handler(topic_name, msg_type))
                subscribers.append(topic)
                
            except Exception as e:
                print(f"  ⚠️  Failed to subscribe to {topic_name}: {e}")
        
        print(f"\n✅ Monitoring {len(subscribers)} topics")
        print("\n👂 Listening for ANY messages...")
        print("   🎯 Press your AR update button now!")
        print("   🔍 Any published message will show up here")
        print("   Press Ctrl+C to stop")
        
        message_count = 0
        start_time = time.time()
        
        # Keep listening
        try:
            while True:
                time.sleep(0.5)
                elapsed = time.time() - start_time
                print(f"\r⏳ Listening for {elapsed:.1f}s | Messages: {message_count}", end='', flush=True)
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping after {elapsed:.1f}s...")
        
        # Cleanup
        for topic in subscribers:
            try:
                topic.unsubscribe()
            except:
                pass
        
        client.terminate()
        print("✅ Disconnected from ROS")
        
        if message_count == 0:
            print("\n⚠️  NO MESSAGES RECEIVED ON ANY TOPIC!")
            print("Possible issues:")
            print("- AR update button not working")
            print("- Publishing to different topic name")
            print("- Different ROS namespace")
            print("- AR system not connected to ROS bridge")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()