#!/usr/bin/env python3
"""
Reverse engineer what's running inside the Docker ROS setup
"""

import roslibpy
import time
import json

def main():
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    if not ros.is_connected:
        print('❌ Failed to connect to ROS')
        return

    print('✅ Connected to ROS Docker instance')
    print('🔍 Reverse engineering ROS Docker setup...\n')
    
    # 1. Try to get ROS info
    print('=' * 60)
    print('📋 ATTEMPTING TO GET ROS SYSTEM INFO')
    print('=' * 60)
    
    # Try rosapi services to get system information
    services_to_try = [
        '/rosapi/topics',
        '/rosapi/services', 
        '/rosapi/nodes',
        '/rosapi/topics_for_type',
        '/rosapi/service_type',
        '/rosapi/get_param',
    ]
    
    for service_name in services_to_try:
        try:
            print(f'\n🔧 Trying service: {service_name}')
            
            def service_callback(result):
                print(f'✅ {service_name} result:')
                if isinstance(result, dict):
                    for key, value in result.items():
                        if isinstance(value, list) and len(value) > 0:
                            print(f'   {key}: {len(value)} items')
                            for item in value[:5]:  # Show first 5 items
                                print(f'     - {item}')
                            if len(value) > 5:
                                print(f'     ... and {len(value) - 5} more')
                        else:
                            print(f'   {key}: {value}')
                else:
                    print(f'   {result}')
            
            service = roslibpy.Service(ros, service_name, 'rosapi/Topics')
            request = roslibpy.ServiceRequest()
            service.call(request, service_callback)
            
            # Wait a bit for callback
            time.sleep(1)
            
        except Exception as e:
            print(f'❌ {service_name} failed: {e}')
    
    print('\n' + '=' * 60)
    print('📡 MONITORING ALL TOPIC ACTIVITY')
    print('=' * 60)
    
    # Monitor for any topic activity
    print('🔍 Listening for any ROS messages for 10 seconds...')
    print('👁️ Try interacting with your AR system now!')
    
    # Common ROS topics to monitor
    common_topics = [
        '/rosout',
        '/rosout_agg', 
        '/tf',
        '/tf_static',
        '/clock',
        '/diagnostics',
        '/parameter_events',
        # Our known topics
        '/HOLO1_GazePoint',
        '/HOLO1_Model',
    ]
    
    detected_activity = []
    
    def create_monitor_callback(topic_name):
        def callback(message):
            activity_info = f'{topic_name}: {str(message)[:100]}...'
            if activity_info not in detected_activity:
                detected_activity.append(activity_info)
                print(f'📨 ACTIVITY: {activity_info}')
        return callback
    
    listeners = []
    
    # Subscribe to common topics with different message types
    for topic in common_topics:
        for msg_type in ['std_msgs/String', 'rosgraph_msgs/Log', 'tf2_msgs/TFMessage']:
            try:
                listener = roslibpy.Topic(ros, topic, msg_type)
                listener.subscribe(create_monitor_callback(f'{topic}[{msg_type}]'))
                listeners.append(listener)
            except:
                pass
    
    # Monitor for 10 seconds
    time.sleep(10)
    
    print('\n' + '=' * 60)
    print('📊 ACTIVITY SUMMARY')
    print('=' * 60)
    
    if detected_activity:
        print(f'✅ Detected {len(detected_activity)} types of activity:')
        for activity in detected_activity:
            print(f'   • {activity}')
    else:
        print('❌ No ROS topic activity detected')
        print('   This suggests:')
        print('   • ROS is running but mostly idle')
        print('   • Topics use different names than expected')
        print('   • Publishers are not active')
    
    # Clean up
    for listener in listeners:
        try:
            listener.unsubscribe()
        except:
            pass
    
    print('\n' + '=' * 60)
    print('🐳 DOCKER ROS ANALYSIS COMPLETE')
    print('=' * 60)
    
    ros.close()

if __name__ == "__main__":
    main()