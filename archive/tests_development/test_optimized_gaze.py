#!/usr/bin/env python3
"""
Test the optimized gaze detection for responsiveness
"""

from src.bridge_design_system.agents.VizorListener import VizorListener
import time

def main():
    print('⚡ Testing Optimized Gaze Detection')
    print('=' * 50)
    
    # Reset singleton for fresh test
    VizorListener._instance = None
    
    print('🔄 Initializing VizorListener...')
    start_init = time.time()
    listener = VizorListener([])
    init_time = time.time() - start_init
    print(f'   Initialization took: {init_time*1000:.1f}ms')
    
    if not listener.is_ros_connected():
        print('❌ ROS not connected - cannot test')
        return
    
    print('✅ ROS connected - testing responsiveness')
    print()
    print('🎯 Quick responsiveness test:')
    print('   Look at AR elements and change your gaze rapidly')
    print('   I will measure response time for gaze changes')
    print()
    
    last_element = None
    last_change_time = None
    change_count = 0
    response_times = []
    
    # Monitor for 10 seconds with high-frequency checking
    start_time = time.time()
    check_interval = 0.05  # Check every 50ms
    
    while time.time() - start_time < 10:
        check_start = time.time()
        
        # Check both current and recent gaze
        current = listener.get_current_element()
        recent = listener.get_recent_gaze(0.5)  # Very short window
        
        # Use the most immediate available gaze
        detected_element = current or recent
        
        if detected_element != last_element:
            change_time = time.time()
            
            if last_element is not None:
                change_count += 1
                # Estimate response time (this is approximate)
                if last_change_time:
                    response_time = change_time - last_change_time
                    response_times.append(response_time)
                    print(f'   🔄 [{change_time-start_time:.2f}s] {last_element} → {detected_element} '
                          f'(~{response_time*1000:.0f}ms since last)')
                else:
                    print(f'   🎯 [{change_time-start_time:.2f}s] First detection: {detected_element}')
            else:
                print(f'   🎯 [{change_time-start_time:.2f}s] Initial gaze: {detected_element}')
            
            last_element = detected_element
            last_change_time = change_time
        
        # Measure our own polling overhead
        check_time = time.time() - check_start
        
        # Sleep for the remainder of our check interval
        sleep_time = max(0, check_interval - check_time)
        time.sleep(sleep_time)
    
    print('\n📊 Responsiveness Analysis:')
    print('-' * 30)
    
    if change_count > 0:
        print(f'Gaze changes detected: {change_count}')
        
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            min_response = min(response_times)
            max_response = max(response_times)
            
            print(f'Average change interval: {avg_response*1000:.0f}ms')
            print(f'Fastest change: {min_response*1000:.0f}ms')
            print(f'Slowest change: {max_response*1000:.0f}ms')
            
            if avg_response < 0.2:
                print('✅ EXCELLENT: Very responsive gaze tracking')
            elif avg_response < 0.5:
                print('✅ GOOD: Responsive gaze tracking')
            elif avg_response < 1.0:
                print('⚠️ ACCEPTABLE: Moderate responsiveness')
            else:
                print('❌ SLOW: Consider optimizing further')
    else:
        print('❌ No gaze changes detected')
        print('   Try moving your gaze between different AR elements')
    
    # Test time-window effectiveness
    print(f'\n🕐 Time-Window Test:')
    print('   Look at an element, then look away and wait...')
    
    for countdown in range(5, 0, -1):
        recent_1s = listener.get_recent_gaze(1.0)
        recent_3s = listener.get_recent_gaze(3.0)
        current = listener.get_current_element()
        
        print(f'   [{countdown}s] Current: {current or "None"}, '
              f'Recent(1s): {recent_1s or "None"}, '
              f'Recent(3s): {recent_3s or "None"}')
        time.sleep(1)
    
    print('\n🏁 Optimization test complete!')

if __name__ == "__main__":
    main()