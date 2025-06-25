#!/usr/bin/env python3
"""
Diagnose ROS polling rate and message latency issues
"""

import roslibpy
import time
from collections import deque

def main():
    print('📊 ROS Polling Rate and Latency Diagnostics')
    print('=' * 60)
    
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    if not ros.is_connected:
        print('❌ Failed to connect to ROS')
        return

    print('✅ Connected to ROS bridge')
    print('🔍 Starting gaze polling diagnostics...')
    print('👁️ Look at different AR elements rapidly to test responsiveness')
    print()
    
    # Track message timing
    message_times = deque(maxlen=100)  # Keep last 100 messages
    last_element = None
    element_changes = []
    
    def gaze_callback(message):
        nonlocal last_element
        timestamp = time.time()
        element = message["data"]
        
        message_times.append(timestamp)
        
        # Track element changes for responsiveness
        if element != last_element:
            change_time = timestamp
            element_changes.append((change_time, element, last_element))
            print(f'🎯 [{time.strftime("%H:%M:%S.%f", time.localtime(timestamp))[:-3]}] '
                  f'{last_element or "None"} → {element}')
            last_element = element
    
    # Subscribe to gaze topic
    gaze_topic = roslibpy.Topic(ros, '/HOLO1_GazePoint', 'std_msgs/String')
    gaze_topic.subscribe(gaze_callback)
    
    print('📡 Monitoring gaze messages for 20 seconds...')
    start_time = time.time()
    
    # Monitor for 20 seconds with periodic analysis
    while time.time() - start_time < 20:
        current_time = time.time()
        
        # Show real-time stats every 5 seconds
        if len(message_times) >= 2 and int(current_time - start_time) % 5 == 0:
            recent_messages = [t for t in message_times if current_time - t <= 5.0]
            if len(recent_messages) >= 2:
                intervals = []
                for i in range(1, len(recent_messages)):
                    interval = recent_messages[i] - recent_messages[i-1]
                    intervals.append(interval)
                
                avg_interval = sum(intervals) / len(intervals)
                estimated_rate = 1.0 / avg_interval if avg_interval > 0 else 0
                
                print(f'📈 [{int(current_time - start_time):2d}s] '
                      f'Rate: {estimated_rate:.1f} Hz, '
                      f'Avg interval: {avg_interval*1000:.1f}ms, '
                      f'Messages: {len(recent_messages)}')
        
        time.sleep(0.1)
    
    # Final analysis
    print('\n' + '='*60)
    print('📊 FINAL DIAGNOSTICS')
    print('='*60)
    
    if len(message_times) >= 2:
        # Calculate overall message rate
        total_time = message_times[-1] - message_times[0]
        total_messages = len(message_times)
        overall_rate = (total_messages - 1) / total_time if total_time > 0 else 0
        
        # Calculate intervals for latency analysis
        intervals = []
        for i in range(1, len(message_times)):
            interval = message_times[i] - message_times[i-1]
            intervals.append(interval * 1000)  # Convert to milliseconds
        
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        
        print(f'📡 Message Reception Analysis:')
        print(f'   Total messages received: {total_messages}')
        print(f'   Overall rate: {overall_rate:.2f} Hz')
        print(f'   Average interval: {avg_interval:.1f}ms')
        print(f'   Min interval: {min_interval:.1f}ms')
        print(f'   Max interval: {max_interval:.1f}ms')
        
        # Analyze responsiveness (element changes)
        if element_changes:
            print(f'\n🎯 Gaze Change Analysis:')
            print(f'   Element changes detected: {len(element_changes)}')
            print(f'   Change responsiveness:')
            
            for i, (change_time, new_elem, old_elem) in enumerate(element_changes[-5:]):
                relative_time = change_time - start_time
                print(f'     {i+1}. {relative_time:.2f}s: {old_elem} → {new_elem}')
        
        # Latency classification
        print(f'\n⚡ Performance Classification:')
        if avg_interval < 50:
            print(f'   ✅ EXCELLENT: Very responsive (<50ms average)')
        elif avg_interval < 100:
            print(f'   ✅ GOOD: Responsive (<100ms average)')
        elif avg_interval < 200:
            print(f'   ⚠️ ACCEPTABLE: Moderate latency (<200ms average)')
        elif avg_interval < 500:
            print(f'   ⚠️ SLOW: Noticeable latency (<500ms average)')
        else:
            print(f'   ❌ VERY SLOW: High latency (>{avg_interval:.0f}ms average)')
        
        # Recommendations
        print(f'\n💡 Recommendations:')
        if avg_interval > 200:
            print(f'   • Consider optimizing ROS bridge configuration')
            print(f'   • Check network latency between Docker and host')
            print(f'   • Verify AR system publishing rate')
        if max_interval > 1000:
            print(f'   • Large interval spikes detected - check for message buffering')
        if len(element_changes) < 3:
            print(f'   • Try moving gaze between elements more rapidly during test')
    
    else:
        print('❌ Insufficient messages received for analysis')
        print('   Possible issues:')
        print('   • AR system not publishing gaze data')
        print('   • Topic name mismatch')
        print('   • ROS bridge configuration problem')
    
    gaze_topic.unsubscribe()
    ros.close()
    
    print('\n🏁 Diagnostics complete!')

if __name__ == "__main__":
    main()