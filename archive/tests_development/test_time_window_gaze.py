#!/usr/bin/env python3
"""
Test the new time-window gaze detection approach
"""

from src.bridge_design_system.agents.VizorListener import VizorListener
import time

def main():
    print('🕐 Testing Time-Window Gaze Detection')
    print('=' * 50)
    
    # Reset singleton for fresh test
    VizorListener._instance = None
    
    listener = VizorListener([])
    
    if not listener.is_ros_connected():
        print('❌ ROS not connected - cannot test')
        return
    
    print('✅ ROS connected - starting time-window test')
    print()
    
    print('👁️ Look at AR elements now - I will monitor for 15 seconds...')
    print('   Then I will test the time-window retrieval functionality')
    print()
    
    # Monitor for 15 seconds
    for i in range(15):
        current = listener.get_current_element()
        if current:
            print(f'   [{15-i:2d}s] Currently gazing at: {current}')
        else:
            print(f'   [{15-i:2d}s] No current gaze detected')
        time.sleep(1)
    
    print('\n📊 Time-Window Test Results:')
    print('-' * 30)
    
    # Test different time windows
    for window in [1.0, 3.0, 5.0, 10.0]:
        recent = listener.get_recent_gaze(window)
        print(f'Recent gaze ({window}s): {recent or "None"}')
    
    # Show detailed history
    summary = listener.get_gaze_history_summary()
    print(f'\n📈 Gaze History Summary:')
    print(f'Total gaze events: {summary["total_gazes"]}')
    print(f'Unique elements: {summary["unique_elements"]}') 
    print(f'Most gazed element: {summary["most_gazed"] or "None"}')
    if summary["most_gazed"]:
        print(f'Times gazed: {summary["most_gazed_count"]}')
    print(f'Time span: {summary["time_span_seconds"]:.1f} seconds')
    
    if summary['recent_elements']:
        print(f'Element sequence: {" → ".join(summary["recent_elements"])}')
    
    # Test the main.py logic
    print(f'\n🎯 Main.py Logic Test:')
    print('-' * 20)
    
    # Simulate what main.py does
    gazed_element_id = listener.get_recent_gaze(window_seconds=3.0)
    if gazed_element_id:
        print(f'✅ Would detect gaze on: {gazed_element_id} (within 3 seconds)')
    else:
        current_gaze = listener.get_current_element()
        if current_gaze:
            gazed_element_id = current_gaze
            print(f'✅ Would detect current gaze on: {gazed_element_id}')
        else:
            print('❌ No gaze would be detected')
    
    print('\n🏁 Test complete!')

if __name__ == "__main__":
    main()