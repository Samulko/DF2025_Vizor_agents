#!/usr/bin/env python3
"""
Test VizorListener with fresh instance to bypass singleton issues
"""

import roslibpy
import time

def main():
    print('🔍 Testing fresh ROS connection (bypassing VizorListener singleton)...')
    
    # Create completely fresh ROS connection
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()
    
    if not ros.is_connected:
        print('❌ Failed to connect')
        return
        
    print('✅ Fresh ROS connection established')
    
    # Direct subscription like VizorListener does
    current_element = None
    
    def handle_gaze_message(message):
        global current_element
        current_element = message["data"]
        print(f"🎯 [Fresh] Gaze detected: {message['data']}")
    
    gaze_subscriber = roslibpy.Topic(ros, "/HOLO1_GazePoint", "std_msgs/String")
    gaze_subscriber.subscribe(handle_gaze_message)
    
    print('📡 Subscribed to /HOLO1_GazePoint')
    print('👁️ Look at AR elements now - testing for 15 seconds...')
    
    # Monitor for 15 seconds
    start_time = time.time()
    while time.time() - start_time < 15:
        time.sleep(0.1)
    
    print(f'Final detected element: {current_element}')
    
    gaze_subscriber.unsubscribe()
    ros.close()

if __name__ == "__main__":
    main()