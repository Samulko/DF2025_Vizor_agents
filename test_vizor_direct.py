#!/usr/bin/env python3
"""
Direct test of VizorListener without full system dependencies
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only the VizorListener file directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/bridge_design_system/agents'))

from VizorListener import VizorListener

def test_vizor_queue():
    print("🧪 Testing VizorListener Queue References")
    print("=" * 50)
    
    # Test 1: Create with queue
    main_queue = []
    print(f"📋 Created main_queue: {id(main_queue)}")
    
    listener = VizorListener(update_queue=main_queue)
    print(f"📋 VizorListener queue: {id(listener.update_queue)}")
    print(f"🔗 Same object? {main_queue is listener.update_queue}")
    
    # Test 2: Simulate singleton behavior
    print("\n🔄 Testing singleton behavior...")
    listener2 = VizorListener(update_queue=main_queue)
    print(f"📋 Second listener queue: {id(listener2.update_queue)}")
    print(f"🔗 Same object? {main_queue is listener2.update_queue}")
    print(f"🔗 Same listener instance? {listener is listener2}")
    
    # Test 3: Add data and check synchronization
    print("\n📤 Testing data synchronization...")
    test_data = {'test': 'data'}
    listener.update_queue.append(test_data)
    
    print(f"   main_queue: {main_queue}")
    print(f"   listener.update_queue: {listener.update_queue}")
    
    if main_queue == listener.update_queue and len(main_queue) > 0:
        print("✅ Queue synchronization working!")
        return True
    else:
        print("❌ Queue synchronization failed!")
        return False

if __name__ == "__main__":
    success = test_vizor_queue()
    sys.exit(0 if success else 1)