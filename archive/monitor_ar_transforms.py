#!/usr/bin/env python3
"""
Live monitor for AR transform updates when you press the update button.
This will show you exactly what data your AR system sends to ROS.
"""

import time
import json
from datetime import datetime

try:
    import roslibpy
except ImportError:
    print("❌ roslibpy not available - install with: pip install roslibpy")
    exit(1)

class ARTransformMonitor:
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
    
    def setup_transform_monitor(self):
        """Setup monitor for HOLO1_Model transforms"""
        print("\n📡 Setting up transform monitor...")
        
        try:
            # Subscribe to the corrected topic/message type
            self.transform_subscriber = roslibpy.Topic(
                self.client, 
                "/HOLO1_Model", 
                "vizor_package/Model"
            )
            
            self.transform_subscriber.subscribe(self.handle_transform_message)
            print("✅ Subscribed to /HOLO1_Model (vizor_package/Model)")
            
        except Exception as e:
            print(f"❌ Failed to subscribe to /HOLO1_Model: {e}")
            return False
        
        return True
    
    def handle_transform_message(self, message):
        """Handle incoming AR transform messages"""
        self.message_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        elapsed = time.time() - self.start_time
        
        print(f"\n🎯 AR UPDATE BUTTON PRESSED! (Message #{self.message_count})")
        print(f"⏰ Time: {timestamp} (t+{elapsed:.1f}s)")
        print("=" * 70)
        
        # Extract message data
        names = message.get('names', [])
        poses = message.get('poses', [])
        
        print(f"📊 Transform Data Summary:")
        print(f"   Elements: {len(names)}")
        print(f"   Poses: {len(poses)}")
        
        if names:
            print(f"\n🏷️  Element Names:")
            for i, name in enumerate(names):
                print(f"   [{i}] {name}")
        
        if poses:
            print(f"\n📍 Transform Details:")
            for i, (name, pose) in enumerate(zip(names, poses)):
                position = pose.get('position', {})
                orientation = pose.get('orientation', {})
                
                print(f"\n   Element {i+1}: {name}")
                print(f"   Position:")
                print(f"     x: {position.get('x', 'N/A')}")
                print(f"     y: {position.get('y', 'N/A')}")
                print(f"     z: {position.get('z', 'N/A')}")
                print(f"   Orientation (Quaternion):")
                print(f"     x: {orientation.get('x', 'N/A')}")
                print(f"     y: {orientation.get('y', 'N/A')}")
                print(f"     z: {orientation.get('z', 'N/A')}")
                print(f"     w: {orientation.get('w', 'N/A')}")
                
                # Show what main.py will receive after coordinate conversion
                if all(k in position for k in ['x', 'y', 'z']) and all(k in orientation for k in ['x', 'y', 'z', 'w']):
                    # Apply VizorListener coordinate conversion (ROS -> Rhino)
                    converted_pos = [-position['y'], position['x'], position['z']]
                    converted_quat = [orientation['w'], -orientation['y'], orientation['x'], orientation['z']]
                    
                    print(f"   🔄 After coordinate conversion (for main.py):")
                    print(f"     Position: {converted_pos}")
                    print(f"     Quaternion: {converted_quat}")
        
        print("\n📋 Raw Message Structure:")
        print(json.dumps(message, indent=2))
        print("=" * 70)
        print("✅ Transform data captured! Ready for main.py processing.")
    
    def monitor(self):
        """Start monitoring for transform messages"""
        print(f"\n👁️  MONITORING AR TRANSFORMS")
        print("=" * 50)
        print("🎯 Press your AR UPDATE BUTTON to see transform data!")
        print("📱 This will show exactly what your AR system sends to ROS")
        print("⚡ Each button press will display detailed transform information")
        print("🛑 Press Ctrl+C to stop monitoring")
        print()
        
        try:
            while True:
                elapsed = time.time() - self.start_time
                print(f"\r⏳ Monitoring for {elapsed:.0f}s | Messages received: {self.message_count}", end='', flush=True)
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        
        print(f"\n📊 Monitor Summary:")
        print(f"   Total AR button presses: {self.message_count}")
        print(f"   Monitoring duration: {time.time() - self.start_time:.1f}s")
        
        if self.message_count == 0:
            print("\n⚠️  NO TRANSFORM DATA RECEIVED!")
            print("   Possible issues:")
            print("   - AR update button not connected to ROS")
            print("   - Wrong topic name (should be /HOLO1_Model)")
            print("   - Wrong message type (should be vizor_package/Model)")
            print("   - ROS bridge configuration issue")
        else:
            print(f"\n✅ Successfully captured {self.message_count} transform updates!")
            print("   Your AR system is working correctly with ROS")
    
    def cleanup(self):
        """Clean up connections"""
        print("\n🧹 Cleaning up...")
        
        if self.transform_subscriber:
            try:
                self.transform_subscriber.unsubscribe()
                print("  ✅ Unsubscribed from /HOLO1_Model")
            except Exception as e:
                print(f"  ⚠️  Error unsubscribing: {e}")
        
        if self.client and self.client.is_connected:
            self.client.terminate()
            print("  ✅ ROS connection terminated")

def main():
    print("🎯 AR Transform Monitor")
    print("=" * 30)
    print("Monitor live transform data from your AR update button")
    print("Shows exactly what data flows from AR → ROS → VizorListener")
    print()
    
    monitor = ARTransformMonitor()
    
    try:
        # Connect to ROS
        if not monitor.connect():
            print("💥 Cannot proceed without ROS connection")
            return
        
        # Setup transform monitoring
        if not monitor.setup_transform_monitor():
            print("💥 Cannot setup transform monitoring")
            return
        
        # Start monitoring
        monitor.monitor()
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        monitor.cleanup()
        print("\n👋 AR Transform monitoring session complete")

if __name__ == "__main__":
    main()