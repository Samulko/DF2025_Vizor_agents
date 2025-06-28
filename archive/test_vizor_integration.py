#!/usr/bin/env python3
"""
Test VizorListener integration with the corrected transform system.
"""

import time
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bridge_design_system.agents.VizorListener import VizorListener

def test_vizor_listener():
    print("🧪 Testing VizorListener Integration")
    print("=" * 40)
    
    # Create a test queue for transforms
    test_queue = []
    
    # Initialize VizorListener
    listener = VizorListener(update_queue=test_queue)
    
    if not listener.is_ros_connected():
        print("❌ VizorListener not connected to ROS")
        status = listener.get_connection_status()
        print(f"Status: {status}")
        return False
    
    print("✅ VizorListener connected to ROS")
    print("📡 Listening for transform data...")
    print("🎯 Run the test script in another terminal:")
    print("   cd tests/vizor_connection && uv run python send_transform.py t1")
    print("\nWaiting 15 seconds for transform data...")
    
    # Monitor for 15 seconds
    start_time = time.time()
    initial_queue_size = len(test_queue)
    
    while time.time() - start_time < 15:
        current_queue_size = len(test_queue)
        transforms = listener.get_transforms()
        
        elapsed = time.time() - start_time
        print(f"\r⏳ {elapsed:.1f}s | Queue: {current_queue_size} | Transforms: {len(transforms)}", end='', flush=True)
        
        if current_queue_size > initial_queue_size:
            print(f"\n🎯 NEW TRANSFORM DATA RECEIVED!")
            print(f"📊 Queue size: {current_queue_size}")
            print(f"🔍 Latest transform batch: {test_queue[-1]}")
            
            # Show format expected by main.py
            if test_queue:
                latest_batch = test_queue[-1]
                print(f"\n✅ Format for main.py processing:")
                for element_name, pose in latest_batch.items():
                    print(f"  Element: {element_name}")
                    print(f"  Position: {pose['position']}")
                    print(f"  Quaternion: {pose['quaternion']}")
            
            return True
        
        time.sleep(0.5)
    
    print(f"\n⚠️  No transform data received in 15 seconds")
    return False

if __name__ == "__main__":
    success = test_vizor_listener()
    if success:
        print("\n✅ VizorListener integration test PASSED")
    else:
        print("\n❌ VizorListener integration test FAILED")