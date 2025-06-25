#!/usr/bin/env python3
"""
Deep investigation: Where is /HOLO1_GazePoint actually coming from?
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

    print('🔍 DEEP INVESTIGATION: /HOLO1_GazePoint Source Detection')
    print('=' * 70)
    
    # Phase 1: Try to get topic information via rosapi
    print('\n📋 PHASE 1: ROS API Topic Information')
    print('-' * 50)
    
    def topics_callback(result):
        print('✅ ROS API Response:')
        if 'topics' in result:
            gaze_topics = [t for t in result['topics'] if 'gaze' in t['name'].lower() or 'holo' in t['name'].lower()]
            if gaze_topics:
                print(f'Found {len(gaze_topics)} potential gaze topics:')
                for topic in gaze_topics:
                    print(f'   • {topic["name"]} [{topic["type"]}]')
            else:
                print('❌ No gaze/holo topics found in ROS API')
                print('Available topics:')
                for topic in result['topics'][:10]:  # Show first 10
                    print(f'   • {topic["name"]} [{topic["type"]}]')
                if len(result['topics']) > 10:
                    print(f'   ... and {len(result["topics"]) - 10} more')
        else:
            print('❌ No topics in API response')
    
    try:
        topics_service = roslibpy.Service(ros, '/rosapi/topics', 'rosapi/Topics')
        request = roslibpy.ServiceRequest()
        topics_service.call(request, topics_callback)
        time.sleep(2)
    except Exception as e:
        print(f'❌ ROS API failed: {e}')
    
    # Phase 2: Try to get publishers of /HOLO1_GazePoint
    print('\n📡 PHASE 2: Publisher Detection')
    print('-' * 50)
    
    def publishers_callback(result):
        print('✅ Publishers info:')
        print(json.dumps(result, indent=2))
    
    try:
        publishers_service = roslibpy.Service(ros, '/rosapi/publishers', 'rosapi/Publishers')
        request = roslibpy.ServiceRequest({'topic': '/HOLO1_GazePoint'})
        publishers_service.call(request, publishers_callback)
        time.sleep(1)
    except Exception as e:
        print(f'❌ Publishers service failed: {e}')
    
    # Phase 3: Live monitoring with detailed analysis
    print('\n👁️ PHASE 3: Live Monitoring Analysis')
    print('-' * 50)
    print('🔍 Setting up enhanced monitoring...')
    
    messages_received = []
    subscription_successful = False
    connection_details = {}
    
    def enhanced_gaze_callback(message):
        nonlocal messages_received, subscription_successful
        subscription_successful = True
        timestamp = time.time()
        messages_received.append({
            'timestamp': timestamp,
            'message': message,
            'time_str': time.strftime('%H:%M:%S', time.localtime(timestamp))
        })
        print(f'🎯 [{time.strftime("%H:%M:%S")}] GAZE: {message}')
    
    # Try to subscribe and capture connection details
    try:
        print('📡 Attempting subscription to /HOLO1_GazePoint...')
        gaze_topic = roslibpy.Topic(ros, '/HOLO1_GazePoint', 'std_msgs/String')
        
        # Capture subscription details
        connection_details = {
            'topic_name': gaze_topic.name,
            'message_type': gaze_topic.message_type,
            'ros_connected': ros.is_connected,
            'subscription_time': time.time()
        }
        
        gaze_topic.subscribe(enhanced_gaze_callback)
        print('✅ Subscription created successfully')
        print(f'   Topic: {gaze_topic.name}')
        print(f'   Type: {gaze_topic.message_type}')
        
    except Exception as e:
        print(f'❌ Subscription failed: {e}')
        gaze_topic = None
    
    # Phase 4: Extended monitoring period
    print('\n⏱️ PHASE 4: Extended Monitoring (30 seconds)')
    print('-' * 50)
    print('👁️ LOOK AT AR ELEMENTS NOW - Monitoring for 30 seconds...')
    print('📊 Real-time message counter:')
    
    start_time = time.time()
    last_count = 0
    
    while time.time() - start_time < 30:
        current_count = len(messages_received)
        if current_count != last_count:
            print(f'   📈 Messages received: {current_count}')
            last_count = current_count
        time.sleep(1)
    
    # Phase 5: Analysis and conclusions
    print('\n📊 PHASE 5: Analysis Results')
    print('=' * 70)
    
    print(f'📈 Total messages received: {len(messages_received)}')
    print(f'🔗 Subscription successful: {subscription_successful}')
    print(f'⚡ ROS connection active: {ros.is_connected}')
    
    if messages_received:
        print('\n✅ TOPIC IS REAL AND ACTIVE!')
        print('📝 Message samples:')
        for i, msg_data in enumerate(messages_received[:5]):  # Show first 5
            print(f'   {i+1}. [{msg_data["time_str"]}] {msg_data["message"]}')
        if len(messages_received) > 5:
            print(f'   ... and {len(messages_received) - 5} more messages')
            
        # Analyze message patterns
        unique_elements = set(msg['message']['data'] for msg in messages_received if 'data' in msg['message'])
        print(f'\n🎯 Unique elements detected: {len(unique_elements)}')
        for element in unique_elements:
            print(f'   • {element}')
            
    else:
        print('\n❌ NO MESSAGES RECEIVED')
        print('🤔 Possible explanations:')
        print('   1. Topic exists but no publisher is active')
        print('   2. You weren\'t looking at AR elements during test')
        print('   3. AR system isn\'t publishing gaze data')
        print('   4. Topic name or message type is incorrect')
        print('   5. Previous detections were false positives')
    
    # Cleanup
    if gaze_topic:
        try:
            gaze_topic.unsubscribe()
        except:
            pass
    
    ros.close()
    
    print('\n🏁 Investigation complete!')

if __name__ == "__main__":
    main()