#!/usr/bin/env python3
"""
Check what message type is actually being published to /HOLO1_Model
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
    print('🔍 Testing different message types for /HOLO1_Model...')
    
    # Test different message types that might be used
    message_types = [
        'std_msgs/String',
        'geometry_msgs/Pose',
        'geometry_msgs/PoseArray', 
        'geometry_msgs/Transform',
        'sensor_msgs/JointState',
        'vizor_package/Model',  # Original assumption
        'std_msgs/Float64MultiArray',
    ]
    
    found_working_type = None
    
    for msg_type in message_types:
        print(f'\n📡 Testing /HOLO1_Model with {msg_type}...')
        
        try:
            def test_callback(message):
                print(f'✅ SUCCESS with {msg_type}!')
                print(f'   Message: {message}')
                nonlocal found_working_type
                found_working_type = msg_type
            
            # Try to subscribe
            listener = roslibpy.Topic(ros, '/HOLO1_Model', msg_type)
            listener.subscribe(test_callback)
            
            print(f'   Subscribed to /HOLO1_Model as {msg_type}')
            print('   👁️ Move/transform AR elements now...')
            
            # Wait 3 seconds for messages
            time.sleep(3)
            
            listener.unsubscribe()
            
            if found_working_type:
                break
                
        except Exception as e:
            print(f'   ❌ Failed with {msg_type}: {e}')
    
    if found_working_type:
        print(f'\n🎯 FOUND CORRECT MESSAGE TYPE: {found_working_type}')
    else:
        print(f'\n⚠️ No working message type found for /HOLO1_Model')
        print('   Either:')
        print('   1. No messages being published to /HOLO1_Model')
        print('   2. Message type not in our test list')
        print('   3. Topic name is different')
    
    ros.close()

if __name__ == "__main__":
    main()