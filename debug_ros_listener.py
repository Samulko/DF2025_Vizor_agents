#!/usr/bin/env python3
"""
Debug ROS listener to capture transform messages when AR update button is pressed.
Run this for 30 seconds while pressing the update button to see the actual message format.
"""

import time
import json
from datetime import datetime

try:
    import roslibpy
    ROS_AVAILABLE = True
except ImportError:
    print("❌ roslibpy not available - install with: pip install roslibpy")
    ROS_AVAILABLE = False
    exit(1)

class DebugROSListener:
    def __init__(self):
        self.client = None
        self.subscribers = {}
        self.message_count = 0
        self.start_time = time.time()
        
    def connect(self):
        """Connect to ROS bridge"""
        try:
            print("🔌 Connecting to ROS bridge at ws://localhost:9090...")
            self.client = roslibpy.Ros(host='localhost', port=9090)
            self.client.run()
            
            if self.client.is_connected:
                print("✅ Connected to ROS bridge successfully")
                return True
            else:
                print("❌ Failed to connect to ROS bridge")
                return False
                
        except Exception as e:
            print(f"❌ ROS connection error: {e}")
            return False
    
    def setup_listeners(self):
        """Setup listeners for all relevant topics"""
        # Topics to monitor based on your error log
        topics_to_monitor = [
            ('HOLO1_Transform', 'std_msgs/String'),
            ('HOLO1_Model', 'std_msgs/String'), 
            ('HOLO1_Command', 'std_msgs/String'),
            ('HOLO1_GazePoint', 'std_msgs/String'),
        ]
        
        print("\n📡 Setting up topic listeners...")
        
        for topic_name, msg_type in topics_to_monitor:
            try:
                print(f"  🎯 Subscribing to /{topic_name} ({msg_type})")
                
                subscriber = roslibpy.Topic(
                    self.client, 
                    f"/{topic_name}", 
                    msg_type
                )
                
                # Create callback with topic name captured
                def make_callback(topic):
                    def callback(message):
                        self.handle_message(topic, message)
                    return callback
                
                subscriber.subscribe(make_callback(topic_name))
                self.subscribers[topic_name] = subscriber
                
            except Exception as e:
                print(f"  ❌ Failed to subscribe to {topic_name}: {e}")
        
        print(f"✅ Setup complete - monitoring {len(self.subscribers)} topics")
    
    def handle_message(self, topic_name, message):
        """Handle incoming ROS messages"""
        self.message_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        elapsed = time.time() - self.start_time
        
        print(f"\n🔔 [{timestamp}] Message #{self.message_count} on /{topic_name} (t+{elapsed:.1f}s)")
        print("=" * 60)
        
        # Pretty print the message
        if hasattr(message, 'data'):
            # std_msgs/String format
            data = message['data']
            print(f"📝 Message Data: {data}")
            
            # Try to parse as JSON if it looks like JSON
            if data.strip().startswith('{') or data.strip().startswith('['):
                try:
                    parsed = json.loads(data)
                    print("📋 Parsed JSON:")
                    print(json.dumps(parsed, indent=2))
                    
                    # If this looks like transform data, analyze it
                    if topic_name in ['HOLO1_Transform', 'HOLO1_Model']:
                        self.analyze_transform_data(parsed)
                        
                except json.JSONDecodeError:
                    print("⚠️  Data looks like JSON but couldn't parse")
        else:
            # Other message formats
            print(f"📝 Raw Message: {message}")
        
        print("=" * 60)
    
    def analyze_transform_data(self, data):
        """Analyze potential transform data structure"""
        print("\n🔍 Transform Data Analysis:")
        
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  🔑 {key}: {type(value).__name__}")
                if isinstance(value, (list, dict)):
                    print(f"     → {value}")
                else:
                    print(f"     → {value}")
        elif isinstance(data, list):
            print(f"  📊 List with {len(data)} items")
            for i, item in enumerate(data[:3]):  # Show first 3 items
                print(f"  [{i}] {type(item).__name__}: {item}")
            if len(data) > 3:
                print(f"  ... and {len(data) - 3} more items")
    
    def monitor(self, duration=30):
        """Monitor for specified duration"""
        print(f"\n⏱️  Monitoring for {duration} seconds...")
        print("🎯 Press your AR update button now!")
        print("Press Ctrl+C to stop early")
        
        try:
            end_time = time.time() + duration
            while time.time() < end_time:
                remaining = int(end_time - time.time())
                print(f"\r⏳ {remaining:2d}s remaining | Messages received: {self.message_count}", end='', flush=True)
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        
        print(f"\n📊 Monitoring complete!")
        print(f"   Total messages: {self.message_count}")
        print(f"   Duration: {time.time() - self.start_time:.1f}s")
    
    def cleanup(self):
        """Clean up connections"""
        print("\n🧹 Cleaning up...")
        
        for topic_name, subscriber in self.subscribers.items():
            try:
                subscriber.unsubscribe()
                print(f"  ✅ Unsubscribed from {topic_name}")
            except Exception as e:
                print(f"  ⚠️  Error unsubscribing from {topic_name}: {e}")
        
        if self.client and self.client.is_connected:
            self.client.terminate()
            print("  ✅ ROS connection terminated")

def main():
    print("🔍 ROS Transform Debug Listener")
    print("=" * 50)
    
    listener = DebugROSListener()
    
    try:
        # Connect to ROS
        if not listener.connect():
            print("💥 Cannot proceed without ROS connection")
            return
        
        # Setup topic listeners
        listener.setup_listeners()
        
        # Monitor for messages
        listener.monitor(duration=30)
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        listener.cleanup()
        print("\n👋 Debug session complete")

if __name__ == "__main__":
    main()