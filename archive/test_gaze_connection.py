#!/usr/bin/env python3
"""
Test script to diagnose gaze connection issues.
Run this while you're looking at elements in the HoloLens.
"""

import time
import sys
sys.path.append('/home/samko/github/vizor_agents/src')

from bridge_design_system.agents.VizorListener import VizorListener

def test_gaze_connection():
    print("🔍 Testing ROS connection and gaze functionality...")
    print("=" * 50)
    
    # Initialize VizorListener
    vizor_listener = VizorListener()
    
    # Check connection status
    status = vizor_listener.get_connection_status()
    print(f"ROS Available: {status['ros_available']}")
    print(f"Connection Attempted: {status['connection_attempted']}")
    print(f"Client Exists: {status['client_exists']}")
    print(f"Is Connected: {status['is_connected']}")
    print(f"Gaze Subscriber Active: {status['gaze_subscriber_active']}")
    print(f"Model Subscriber Active: {status['model_subscriber_active']}")
    
    if not vizor_listener.is_ros_connected():
        print("\n❌ ROS connection failed!")
        print("📋 Troubleshooting steps:")
        print("1. Check if ROS Docker container is running: docker ps | grep ros")
        print("2. Check if port 9090 is accessible: curl localhost:9090")
        print("3. Check if rosbridge is running in the container")
        return False
    
    print("\n✅ ROS connection successful!")
    print("\n👁️ Now testing gaze detection...")
    print("Look at different elements in the HoloLens for 30 seconds...")
    print("(The system should detect your gaze and show element names)")
    
    # Monitor gaze for 30 seconds
    start_time = time.time()
    last_current = None
    last_recent = None
    
    while time.time() - start_time < 30:
        current_gaze = vizor_listener.get_current_element()
        recent_gaze = vizor_listener.get_recent_gaze(3.0)
        
        # Only print when something changes
        if current_gaze != last_current or recent_gaze != last_recent:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] Current: {current_gaze or 'None'} | Recent(3s): {recent_gaze or 'None'}")
            last_current = current_gaze
            last_recent = recent_gaze
        
        time.sleep(0.1)  # Check 10 times per second
    
    # Show final summary
    summary = vizor_listener.get_gaze_history_summary(30.0)
    print(f"\n📊 Gaze Summary (30 seconds):")
    print(f"  Total gaze events: {summary['total_gazes']}")
    print(f"  Unique elements: {summary['unique_elements']}")
    print(f"  Most gazed element: {summary['most_gazed'] or 'None'}")
    if summary['recent_elements']:
        print(f"  Element sequence: {' → '.join(summary['recent_elements'])}")
    
    return True

if __name__ == "__main__":
    try:
        test_gaze_connection()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()