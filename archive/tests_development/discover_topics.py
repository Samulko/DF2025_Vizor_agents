#!/usr/bin/env python3
"""
Discover what ROS topics are actually being published
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
    print('🔍 Discovering active topics...')
    
    # Try to get topic list via rosapi
    try:
        def topics_callback(result):
            if 'topics' in result:
                print(f'\n📡 Found {len(result["topics"])} topics:')
                for topic_info in result['topics']:
                    topic_name = topic_info['name']
                    topic_type = topic_info['type']
                    print(f'   {topic_name} [{topic_type}]')
                    
                    # Check if this might be our gaze topic
                    if 'gaze' in topic_name.lower() or 'holo' in topic_name.lower() or 'dynamic' in topic_name.lower():
                        print(f'   ⭐ POTENTIAL GAZE TOPIC: {topic_name}')
            else:
                print('No topics found in response')
            ros.close()
        
        topics_service = roslibpy.Service(ros, '/rosapi/topics', 'rosapi/Topics')
        request = roslibpy.ServiceRequest()
        topics_service.call(request, topics_callback)
        
        # Wait for response
        time.sleep(3)
        
    except Exception as e:
        print(f'Service call failed: {e}')
        
        # Alternative: try listening to common topic patterns
        print('\n🔍 Trying alternative discovery method...')
        potential_topics = [
            '/gaze', '/gaze_point', '/gaze_data',
            '/hololens/gaze', '/hololens/gaze_point', 
            '/ar/gaze', '/ar/gaze_point',
            '/dynamic_gaze', '/element_gaze',
            '/HOLO1_GazePoint', '/HOLO1_Model',  # Expected topics
            '/holo1_gaze_point', '/holo1_model',  # Lowercase variants
        ]
        
        print('Testing potential topic names...')
        for topic in potential_topics:
            try:
                def test_callback(message):
                    print(f'✅ FOUND ACTIVE TOPIC: {topic} - Message: {message}')
                
                listener = roslibpy.Topic(ros, topic, 'std_msgs/String')
                listener.subscribe(test_callback)
                time.sleep(0.5)  # Brief listen
                listener.unsubscribe()
                
            except Exception as e:
                pass  # Topic doesn't exist or wrong type
        
        ros.close()

if __name__ == "__main__":
    main()