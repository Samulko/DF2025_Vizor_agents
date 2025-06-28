#!/usr/bin/env python3
"""
Simple test to verify queue synchronization between main.py and VizorListener
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Direct import to avoid config dependencies
from bridge_design_system.agents.VizorListener import VizorListener

def test_queue_sync():
    print("🧪 Testing VizorListener Queue Synchronization")
    print("=" * 50)
    
    # Create a test queue (simulating main.py TRANSFORM_UPDATE_QUEUE)
    main_queue = []
    print(f"📋 Created main_queue with ID: {id(main_queue)}")
    
    # Create VizorListener with the queue
    print("🔍 Creating VizorListener...")
    listener = VizorListener(update_queue=main_queue)
    
    print(f"📋 VizorListener queue ID: {id(listener.update_queue)}")
    print(f"🔗 Queue references same object: {main_queue is listener.update_queue}")
    
    # Simulate adding transform data directly (bypass ROS)
    print("\n📤 Simulating transform data...")
    test_transforms = {
        'dynamic_001': {
            'position': [1.0, 2.0, 3.0],
            'quaternion': [1.0, 0.0, 0.0, 0.0]
        }
    }
    
    # Add to VizorListener queue directly
    listener.update_queue.append(test_transforms.copy())
    print(f"✅ Added transform data to VizorListener queue")
    
    # Check if main_queue received the data
    print(f"\n📊 Results:")
    print(f"   main_queue length: {len(main_queue)}")
    print(f"   listener.update_queue length: {len(listener.update_queue)}")
    print(f"   main_queue contents: {main_queue}")
    print(f"   listener queue contents: {listener.update_queue}")
    
    if len(main_queue) > 0 and len(listener.update_queue) > 0:
        print("\n✅ SUCCESS: Queue synchronization working!")
        print("   Transform data properly shared between main.py and VizorListener")
        return True
    else:
        print("\n❌ FAILED: Queue synchronization not working!")
        print("   Transform data not properly shared")
        return False

if __name__ == "__main__":
    success = test_queue_sync()
    sys.exit(0 if success else 1)