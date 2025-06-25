#!/usr/bin/env python3
"""
Live gaze monitoring test script for VizorListener
"""

from src.bridge_design_system.agents.VizorListener import VizorListener
import time

def main():
    print('🔍 Starting gaze monitoring...')
    print('👁️ Look at different elements in AR - I will detect your gaze!')
    print('📡 Listening to /HOLO1_GazePoint and /HOLO1_Model topics...')
    print()

    listener = VizorListener([])

    # Monitor for 30 seconds
    start_time = time.time()
    last_element = None
    last_transforms = None

    print('Status: Ready - start gazing at elements!')
    
    while time.time() - start_time < 30:
        # Check current gaze
        current_element = listener.get_current_element()
        if current_element != last_element:
            if current_element:
                print(f'👁️ GAZE DETECTED: {current_element}')
            else:
                print('👁️ No gaze target')
            last_element = current_element
        
        # Check transforms
        transforms = listener.get_transforms()
        if transforms != last_transforms and transforms:
            print(f'🔄 TRANSFORMS: {list(transforms.keys())}')
            for name, transform in transforms.items():
                if isinstance(transform, dict):
                    pos = transform.get('position', {})
                    print(f'   {name}: pos({pos.get("x",0):.3f}, {pos.get("y",0):.3f}, {pos.get("z",0):.3f})')
            last_transforms = transforms
        
        time.sleep(0.1)

    print()
    print('✅ Monitoring complete!')
    print(f'Final gaze target: {listener.get_current_element()}')
    transforms = listener.get_transforms()
    print(f'Active transforms: {list(transforms.keys()) if transforms else "None"}')

if __name__ == "__main__":
    main()