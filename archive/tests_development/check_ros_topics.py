#!/usr/bin/env python3
"""
Check what ROS topics are available
"""

import roslibpy
import time

def main():
    # Connect to ROS
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    if not ros.is_connected:
        print('❌ Failed to connect to ROS')
        return

    print('✅ Connected to ROS bridge')
    print('🔍 Checking for expected topics...')
    
    # Check if our expected topics exist by trying to subscribe
    expected_topics = ['/HOLO1_GazePoint', '/HOLO1_Model']
    
    for topic_name in expected_topics:
        print(f'\n📡 Testing topic: {topic_name}')
        
        # Try to subscribe to see if topic exists
        def message_callback(message):
            print(f'✅ {topic_name} - Message received: {message}')
        
        def error_callback(error):
            print(f'❌ {topic_name} - Error: {error}')
        
        # Subscribe with different message types to test
        try:
            listener = roslibpy.Topic(ros, topic_name, 'std_msgs/String')
            listener.subscribe(message_callback)
            print(f'   Subscribed to {topic_name} as std_msgs/String')
            
            # Wait a moment for messages
            time.sleep(2)
            
            listener.unsubscribe()
            
        except Exception as e:
            print(f'   Failed to subscribe to {topic_name}: {e}')
    
    print('\n🔍 Listening for any messages on expected topics for 10 seconds...')
    print('   (Look at elements in AR now!)')
    
    # Set up listeners
    gaze_received = False
    model_received = False
    
    def gaze_callback(message):
        nonlocal gaze_received
        gaze_received = True
        print(f'👁️ GAZE MESSAGE: {message}')
    
    def model_callback(message):
        nonlocal model_received  
        model_received = True
        print(f'🔄 MODEL MESSAGE: {message}')
    
    gaze_listener = roslibpy.Topic(ros, '/HOLO1_GazePoint', 'std_msgs/String')
    model_listener = roslibpy.Topic(ros, '/HOLO1_Model', 'vizor_package/Model') 
    
    gaze_listener.subscribe(gaze_callback)
    model_listener.subscribe(model_callback)
    
    # Wait for messages
    start_time = time.time()
    while time.time() - start_time < 10:
        time.sleep(0.1)
    
    print(f'\n📊 Results after 10 seconds:')
    print(f'   Gaze messages received: {gaze_received}')
    print(f'   Model messages received: {model_received}')
    
    if not gaze_received and not model_received:
        print('\n⚠️ No messages received. Possible issues:')
        print('   1. AR system not publishing to these topics')
        print('   2. Topic names are different')
        print('   3. Message types are different')
        print('   4. AR system not running')
    
    gaze_listener.unsubscribe()
    model_listener.unsubscribe()
    ros.close()

if __name__ == "__main__":
    main()