#!/usr/bin/env python3
"""
Definitive test: Does /HOLO1_GazePoint actually exist?
"""

import roslibpy
import time

def main():
    print('🔍 DEFINITIVE TOPIC EXISTENCE TEST')
    print('=' * 50)
    
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    if not ros.is_connected:
        print('❌ Failed to connect to ROS')
        return

    print('✅ Connected to ROS')
    
    # Test 1: Simple subscription attempt
    print('\n📡 TEST 1: Simple Subscription Test')
    print('-' * 30)
    
    message_received = False
    error_occurred = False
    error_message = ""
    
    def test_callback(message):
        nonlocal message_received
        message_received = True
        print(f'✅ MESSAGE RECEIVED: {message}')
    
    def error_callback(error):
        nonlocal error_occurred, error_message
        error_occurred = True
        error_message = str(error)
        print(f'❌ ERROR: {error}')
    
    try:
        # Try to subscribe with error handling
        topic = roslibpy.Topic(ros, '/HOLO1_GazePoint', 'std_msgs/String')
        topic.subscribe(test_callback)
        
        print('📡 Subscription created, waiting 10 seconds...')
        print('👁️ Look at AR elements NOW if possible!')
        
        # Wait 10 seconds
        for i in range(10):
            print(f'   Waiting... {10-i} seconds remaining')
            time.sleep(1)
            
        topic.unsubscribe()
        
    except Exception as e:
        print(f'❌ Subscription failed: {e}')
        error_occurred = True
        error_message = str(e)
    
    # Test 2: Check if topic appears in any listings
    print('\n📋 TEST 2: Topic Listing Verification')
    print('-' * 30)
    
    try:
        def list_callback(result):
            if 'topics' in result:
                all_topics = [topic['name'] for topic in result['topics']]
                holo_topics = [t for t in all_topics if 'HOLO' in t or 'holo' in t]
                gaze_topics = [t for t in all_topics if 'gaze' in t.lower()]
                
                print(f'📊 Total topics: {len(all_topics)}')
                print(f'🤖 HOLO topics: {holo_topics if holo_topics else "None"}')
                print(f'👁️ Gaze topics: {gaze_topics if gaze_topics else "None"}')
                
                if '/HOLO1_GazePoint' in all_topics:
                    print('✅ /HOLO1_GazePoint FOUND in topic list!')
                else:
                    print('❌ /HOLO1_GazePoint NOT in topic list')
                    
                # Show some example topics for context
                print(f'📝 Sample topics:')
                for topic in all_topics[:10]:
                    print(f'   • {topic}')
            else:
                print('❌ No topics returned from API')
        
        service = roslibpy.Service(ros, '/rosapi/topics', 'rosapi/Topics')
        request = roslibpy.ServiceRequest()
        service.call(request, list_callback)
        time.sleep(2)
        
    except Exception as e:
        print(f'❌ Topic listing failed: {e}')
    
    # Test 3: Publishers check
    print('\n🖨️ TEST 3: Publishers Check')
    print('-' * 30)
    
    try:
        def publishers_callback(result):
            print(f'📡 Publishers result: {result}')
        
        pub_service = roslibpy.Service(ros, '/rosapi/publishers', 'rosapi/Publishers')
        pub_request = roslibpy.ServiceRequest({'topic': '/HOLO1_GazePoint'})
        pub_service.call(pub_request, publishers_callback)
        time.sleep(1)
        
    except Exception as e:
        print(f'❌ Publishers check failed: {e}')
    
    # Final verdict
    print('\n🏁 FINAL VERDICT')
    print('=' * 50)
    
    if message_received:
        print('✅ TOPIC IS REAL - Messages were received!')
    elif error_occurred:
        print(f'⚠️ TOPIC STATUS UNCLEAR - Error: {error_message}')
    else:
        print('❌ TOPIC APPEARS TO BE NON-EXISTENT OR INACTIVE')
        print('   • Subscription succeeded but no messages received')
        print('   • This suggests either:')
        print('     1. Topic exists but no publisher is active')
        print('     2. Topic doesn\'t actually exist')
        print('     3. Our previous detections were false positives')
    
    ros.close()

if __name__ == "__main__":
    main()