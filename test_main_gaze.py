#!/usr/bin/env python3
"""
Test the main.py gaze integration specifically.
"""

import sys
sys.path.append('/home/samko/github/vizor_agents/src')

from bridge_design_system.agents.VizorListener import VizorListener

def test_main_gaze_integration():
    print("🔍 Testing main.py gaze integration...")
    
    # Initialize the same way main.py does it
    TRANSFORM_UPDATE_QUEUE = []
    vizor_listener = VizorListener(update_queue=TRANSFORM_UPDATE_QUEUE)
    
    print(f"✅ VizorListener initialized")
    print(f"📡 ROS Connected: {vizor_listener.is_ros_connected()}")
    
    # Test the same logic as main.py lines 648-661
    print("\n👁️ Testing gaze detection logic from main.py...")
    print("Look at an element now...")
    
    import time
    time.sleep(2)  # Give you time to look at something
    
    # This is the exact logic from main.py lines 648-661
    gazed_element_id = None
    if vizor_listener:
        try:
            # Try to get recent gaze within 3-second window
            gazed_element_id = vizor_listener.get_recent_gaze(window_seconds=3.0)
            if gazed_element_id:
                print(f"[Debug] Gaze detected on: {gazed_element_id} (within 3 seconds)")
            else:
                # Also try current element as fallback
                current_gaze = vizor_listener.get_current_element()
                if current_gaze:
                    gazed_element_id = current_gaze
                    print(f"[Debug] Current gaze detected on: {gazed_element_id}")
        except Exception as e:
            print(f"⚠️ Failed to get gaze data: {e}")
    
    if gazed_element_id:
        print(f"✅ SUCCESS: Would pass gaze_id='{gazed_element_id}' to triage agent")
    else:
        print("❌ FAILED: No gaze detected - would pass gaze_id=None")
    
    return gazed_element_id

if __name__ == "__main__":
    test_main_gaze_integration()