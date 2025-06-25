#!/usr/bin/env python3
"""
Debug VizorListener to see why it's not receiving messages
"""

from src.bridge_design_system.agents.VizorListener import VizorListener
import time

def main():
    print('🔍 Debugging VizorListener...')
    
    # Create listener
    listener = VizorListener([])
    
    # Check status
    status = listener.get_connection_status()
    print(f'Initial status: {status}')
    
    # Force connection attempt
    if not status['connection_attempted']:
        print('🔄 Forcing connection attempt...')
        result = listener._attempt_ros_connection()
        print(f'Connection result: {result}')
        
    # Check status again
    status = listener.get_connection_status()
    print(f'After connection attempt: {status}')
    
    if status['is_connected']:
        print('✅ Connected! Testing message reception...')
        
        # Add debug prints to callback
        original_handle_gaze = listener._handle_gaze_message
        
        def debug_gaze_callback(message):
            print(f'🎯 GAZE CALLBACK TRIGGERED: {message}')
            original_handle_gaze(message)
            
        listener._handle_gaze_message = debug_gaze_callback
        
        # Monitor for 15 seconds
        print('👁️ Look at AR elements now - monitoring for 15 seconds...')
        start_time = time.time()
        last_element = None
        
        while time.time() - start_time < 15:
            current = listener.get_current_element()
            if current != last_element:
                print(f'📊 Current element changed: {current}')
                last_element = current
            time.sleep(0.1)
            
        print(f'Final element: {listener.get_current_element()}')
    else:
        print('❌ Connection failed')
        print('Details:')
        print(f'  ROS available: {status["ros_available"]}')
        print(f'  Connection attempted: {status["connection_attempted"]}')
        print(f'  Client exists: {status["client_exists"]}')

if __name__ == "__main__":
    main()