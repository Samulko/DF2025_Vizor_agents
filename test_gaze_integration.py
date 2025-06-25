#!/usr/bin/env python3
"""
Test gaze integration in the main.py context
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bridge_design_system.agents.VizorListener import VizorListener
import time

def main():
    print('🔍 Testing gaze integration as main.py does...')
    
    # Initialize exactly like main.py does
    TRANSFORM_UPDATE_QUEUE = []
    vizor_listener = VizorListener(update_queue=TRANSFORM_UPDATE_QUEUE)
    
    if vizor_listener.is_ros_connected():
        print("✅ Gaze-assisted spatial grounding enabled (ROS connected)")
        
        # Test the exact code path from main.py lines 600-602
        print('\n👁️ Testing gaze capture (look at AR elements now)...')
        
        for i in range(30):  # Test for 30 iterations
            try:
                gazed_element_id = vizor_listener.get_current_element()
                if gazed_element_id:
                    print(f"🎯 [Debug] Gaze detected on: {gazed_element_id}")
                    
                    # Test the clearing mechanism from main.py line 629
                    print(f"   Current element before clear: {vizor_listener.current_element}")
                    vizor_listener.current_element = None
                    print(f"   Current element after clear: {vizor_listener.current_element}")
                    
            except Exception as e:
                print(f"⚠️ Failed to get gaze data: {e}")
                
            # Check transform queue
            if TRANSFORM_UPDATE_QUEUE:
                print(f"🔄 Transform queue has {len(TRANSFORM_UPDATE_QUEUE)} items")
                
            time.sleep(0.5)
    else:
        print("❌ ROS not connected")
        status = vizor_listener.get_connection_status()
        print(f"Status: {status}")

if __name__ == "__main__":
    main()