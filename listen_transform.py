#!/usr/bin/env python3
"""
Simple listener focused on HOLO1_Transform topic only.
Will show exactly what data comes through when you press the update button.
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

class TransformListener:
    def __init__(self):
        self.client = None
        self.transform_subscriber = None
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
    
    def setup_transform_listener(self):
        """Setup listener specifically for HOLO1_Transform"""
        print("\n📡 Setting up HOLO1_Transform listener...")
        
        try:
            # Try std_msgs/String first
            self.transform_subscriber = roslibpy.Topic(
                self.client, 
                "/HOLO1_Transform", 
                "std_msgs/String"
            )
            
            self.transform_subscriber.subscribe(self.handle_transform_message)
            print("✅ Subscribed to /HOLO1_Transform (std_msgs/String)")
            
        except Exception as e:
            print(f"❌ Failed to subscribe to HOLO1_Transform: {e}")
            return False
        
        return True
    
    def handle_transform_message(self, message):
        """Handle incoming transform messages"""
        self.message_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        elapsed = time.time() - self.start_time
        
        print(f"\n🎯 TRANSFORM MESSAGE #{self.message_count} at {timestamp} (t+{elapsed:.1f}s)")
        print("=" * 70)
        
        # Extract the data
        if hasattr(message, 'data'):
            data = message['data']
        else:
            data = message
            
        print(f"📝 Raw Data: {data}")
        print(f"📊 Data Type: {type(data)}")
        print(f"📏 Data Length: {len(str(data))}")
        
        # Try to parse as JSON
        if isinstance(data, str) and (data.strip().startswith('{') or data.strip().startswith('[')):
            try:
                parsed = json.loads(data)
                print("\n🔍 PARSED JSON STRUCTURE:")
                print(json.dumps(parsed, indent=2))
                
                # Analyze the structure for transform data
                self.analyze_transform_structure(parsed)
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse failed: {e}")
        else:
            print("ℹ️  Data is not JSON format")
        
        print("=" * 70)
        print("🎯 This is the transform data your AR system is sending!")
    
    def analyze_transform_structure(self, data):
        """Analyze the transform data structure"""
        print("\n🔬 TRANSFORM DATA ANALYSIS:")
        
        if isinstance(data, dict):
            print("📋 Dictionary structure:")
            for key, value in data.items():
                print(f"  🔑 '{key}': {type(value).__name__}")
                
                if key.lower() in ['position', 'pos', 'translation', 'location']:
                    print(f"     🎯 POSITION DATA: {value}")
                elif key.lower() in ['rotation', 'quaternion', 'quat', 'orientation']:
                    print(f"     🔄 ROTATION DATA: {value}")
                elif key.lower() in ['name', 'id', 'element', 'object']:
                    print(f"     🏷️  IDENTIFIER: {value}")
                else:
                    if isinstance(value, (list, dict)):
                        print(f"     📦 Complex data: {value}")
                    else:
                        print(f"     📄 Simple data: {value}")
                        
        elif isinstance(data, list):
            print(f"📊 List with {len(data)} items:")
            for i, item in enumerate(data):
                print(f"  [{i}] {type(item).__name__}: {item}")
                if i >= 2:  # Show first 3 items
                    print(f"  ... and {len(data) - 3} more items")
                    break
    
    def monitor(self, duration=60):
        """Monitor for transform messages"""
        print(f"\n⏱️  Monitoring HOLO1_Transform for {duration} seconds...")
        print("🎯 NOW PRESS YOUR AR UPDATE BUTTON!")
        print("📱 I'm listening specifically for transform data...")
        print("Press Ctrl+C to stop early")
        
        try:
            end_time = time.time() + duration
            while time.time() < end_time:
                remaining = int(end_time - time.time())
                if self.message_count == 0:
                    print(f"\r⏳ {remaining:2d}s remaining | 🔍 Waiting for transform data...", end='', flush=True)
                else:
                    print(f"\r⏳ {remaining:2d}s remaining | ✅ {self.message_count} transform messages received", end='', flush=True)
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        
        print(f"\n📊 Monitoring complete!")
        print(f"   Transform messages: {self.message_count}")
        print(f"   Duration: {time.time() - self.start_time:.1f}s")
        
        if self.message_count == 0:
            print("\n⚠️  NO TRANSFORM DATA RECEIVED!")
            print("   Possible issues:")
            print("   - AR update button not publishing to HOLO1_Transform")
            print("   - Wrong message type (not std_msgs/String)")
            print("   - Topic name mismatch")
            print("   - ROS bridge not configured properly")
    
    def cleanup(self):
        """Clean up connections"""
        print("\n🧹 Cleaning up...")
        
        if self.transform_subscriber:
            try:
                self.transform_subscriber.unsubscribe()
                print("  ✅ Unsubscribed from HOLO1_Transform")
            except Exception as e:
                print(f"  ⚠️  Error unsubscribing: {e}")
        
        if self.client and self.client.is_connected:
            self.client.terminate()
            print("  ✅ ROS connection terminated")

def main():
    print("🎯 HOLO1_Transform Listener")
    print("=" * 40)
    print("This script will show you EXACTLY what data")
    print("your AR update button sends to ROS")
    print("=" * 40)
    
    listener = TransformListener()
    
    try:
        # Connect to ROS
        if not listener.connect():
            print("💥 Cannot proceed without ROS connection")
            return
        
        # Setup transform listener
        if not listener.setup_transform_listener():
            print("💥 Cannot setup transform listener")
            return
        
        # Monitor for messages
        listener.monitor(duration=60)
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        listener.cleanup()
        print("\n👋 Transform listening session complete")

if __name__ == "__main__":
    main()