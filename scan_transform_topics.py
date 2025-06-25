#!/usr/bin/env python3
"""
Scan for any topics that might contain transform/model data
"""

import roslibpy
import time

def main():
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    if not ros.is_connected:
        print('❌ Failed to connect to ROS')
        return

    print('✅ Connected to ROS bridge')
    print('🔍 Scanning for transform/model topics...')
    
    # Test various topic patterns that might contain transform data
    potential_topics = [
        '/HOLO1_Model', '/HOLO1_Transform', '/HOLO1_Pose',
        '/holo1_model', '/holo1_transform', '/holo1_pose',
        '/HOLO1/Model', '/HOLO1/Transform', '/HOLO1/Pose',
        '/holo1/model', '/holo1/transform', '/holo1/pose',
        '/model', '/transform', '/pose', '/transforms',
        '/unity_model', '/unity_transform', '/unity_pose',
        '/ar_model', '/ar_transform', '/ar_pose',
        '/dynamic_model', '/dynamic_transform', '/dynamic_pose',
        '/element_model', '/element_transform', '/element_pose',
        '/object_model', '/object_transform', '/object_pose',
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
    
    # Subscribe to all potential topics with different message types
    for topic in potential_topics:
        for msg_type in ['std_msgs/String', 'geometry_msgs/Pose', 'geometry_msgs/Transform']:
            try:
                listener = roslibpy.Topic(ros, topic, msg_type)
                listener.subscribe(create_callback(f'{topic} [{msg_type}]'))
                listeners.append(listener)
            except:
                pass
    
    print(f'🔍 Listening on {len(listeners)} potential topic/type combinations...')
    print('👁️ Try moving/transforming AR elements now - scanning for 15 seconds...')
    
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
        print(f'✅ Found {len(found_topics)} active transform topics:')
        for topic in found_topics:
            print(f'   {topic}')
    else:
        print('❌ No transform topics found')
        print('\n💡 This suggests:')
        print('   1. Your AR system only publishes gaze data, not transform data')
        print('   2. Transform data uses a different topic name pattern')
        print('   3. Transform data publishing is not enabled yet')
    
    ros.close()

if __name__ == "__main__":
    main()