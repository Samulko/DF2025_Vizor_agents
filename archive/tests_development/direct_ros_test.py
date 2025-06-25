#!/usr/bin/env python3
"""
Direct ROS connection test bypassing VizorListener to isolate the issue
"""

import roslibpy
import time

def main():
    print('🔍 Direct ROS connection test...')
    
    # Create fresh ROS connection
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()
    
    if not ros.is_connected:
        print('❌ Failed to connect to ROS')
        return
        
    print('✅ Connected to ROS')
    
    # Direct subscription to gaze topic
    def gaze_callback(message):
        print(f'👁️ DIRECT CALLBACK: {message}')
    
    gaze_topic = roslibpy.Topic(ros, '/HOLO1_GazePoint', 'std_msgs/String')
    gaze_topic.subscribe(gaze_callback)
    
    print('📡 Subscribed to /HOLO1_GazePoint')
    print('👁️ Look at AR elements now - monitoring for 15 seconds...')
    
    # Listen for 15 seconds
    time.sleep(15)
    
    gaze_topic.unsubscribe()
    ros.close()
    
    print('✅ Test complete')

if __name__ == "__main__":
    main()