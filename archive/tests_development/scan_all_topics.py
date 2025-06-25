#!/usr/bin/env python3
"""
Scan for any ROS topics that might contain gaze data
"""

import roslibpy
import time
import threading

def main():
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    if not ros.is_connected:
        print('❌ Failed to connect to ROS')
        return

    print('✅ Connected to ROS bridge')
    print('🔍 Scanning for topics with gaze data...')
    print('👁️ Keep looking at elements in AR - scanning for 15 seconds...')
    
    # List of potential topic names and patterns
    potential_topics = [
        # Expected topics
        '/HOLO1_GazePoint', '/HOLO1_Model',
        
        # Variations
        '/holo1_gaze_point', '/holo1_model',
        '/HOLO1/GazePoint', '/HOLO1/Model',
        '/holo1/gaze_point', '/holo1/model',
        
        # Generic patterns
        '/gaze', '/gaze_point', '/gaze_data', '/gaze_target',
        '/element_gaze', '/dynamic_gaze', '/ar_gaze',
        '/hololens_gaze', '/hololens/gaze',
        '/unity_gaze', '/unity/gaze',
        
        # Dynamic patterns
        '/dynamic', '/dynamic_data', '/element_data',
        '/ar_data', '/holo_data', '/unity_data'
    ]
    
    found_topics = []
    
    def create_callback(topic_name):
        def callback(message):
            print(f'🎯 FOUND ACTIVE TOPIC: {topic_name}')
            print(f'   Message: {message}')
            if topic_name not in found_topics:
                found_topics.append(topic_name)
        return callback
    
    listeners = []
    
    # Subscribe to all potential topics
    for topic in potential_topics:
        try:
            # Try different message types
            for msg_type in ['std_msgs/String', 'geometry_msgs/Pose', 'sensor_msgs/JointState']:
                try:
                    listener = roslibpy.Topic(ros, topic, msg_type)
                    listener.subscribe(create_callback(f'{topic} [{msg_type}]'))
                    listeners.append(listener)
                except:
                    pass
        except:
            pass
    
    print(f'🔍 Listening on {len(listeners)} potential topic/type combinations...')
    
    # Listen for 15 seconds
    time.sleep(15)
    
    # Clean up
    for listener in listeners:
        try:
            listener.unsubscribe()
        except:
            pass
    
    print(f'\n📊 Results:')
    if found_topics:
        print(f'✅ Found {len(found_topics)} active topics:')
        for topic in found_topics:
            print(f'   {topic}')
    else:
        print('❌ No gaze topics found')
        print('\n🔧 Troubleshooting suggestions:')
        print('   1. Check if your AR app is publishing to ROS')
        print('   2. Verify the correct topic names in your AR app')
        print('   3. Check if topic names use different capitalization')
        print('   4. Verify your AR app connects to the same ROS bridge')
    
    ros.close()

if __name__ == "__main__":
    main()