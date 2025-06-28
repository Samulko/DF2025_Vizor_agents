#!/usr/bin/env python3
"""
Complete integration test with better timing control
"""

import time
import sys
import os
import threading

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bridge_design_system.agents.VizorListener import VizorListener

def test_complete_integration():
    print("🧪 Complete VizorListener Integration Test")
    print("=" * 50)
    
    # Create a test queue for transforms
    test_queue = []
    
    # Initialize VizorListener
    print("📡 Initializing VizorListener...")
    listener = VizorListener(update_queue=test_queue)
    
    if not listener.is_ros_connected():
        print("❌ VizorListener not connected to ROS")
        status = listener.get_connection_status()
        print(f"Status: {status}")
        return False
    
    print("✅ VizorListener connected and ready")
    
    # Function to send test data after delay
    def send_test_data():
        time.sleep(3)  # Wait for listener to be ready
        print("📤 Sending test transform data...")
        
        try:
            import roslibpy
            
            client = roslibpy.Ros(host='localhost', port=9090)
            client.run()
            
            if not client.is_connected:
                print("❌ Failed to connect sender")
                return
            
            topic = roslibpy.Topic(client, '/HOLO1_Model', 'vizor_package/Model')
            
            # Send test transform data
            message = {
                'names': ['dynamic_001', 'dynamic_002'],
                'poses': [
                    {
                        'position': {'x': 1.0, 'y': 0.5, 'z': 0.0},
                        'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
                    },
                    {
                        'position': {'x': 2.0, 'y': 1.0, 'z': 0.0},
                        'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
                    }
                ]
            }
            
            topic.publish(roslibpy.Message(message))
            print("📤 Test transform message sent")
            
            time.sleep(1)
            topic.unadvertise()
            client.terminate()
            
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    # Start sender in background
    sender_thread = threading.Thread(target=send_test_data)
    sender_thread.start()
    
    # Monitor for results
    print("👂 Listening for transform data for 10 seconds...")
    start_time = time.time()
    received_data = False
    
    while time.time() - start_time < 10:
        current_queue_size = len(test_queue)
        transforms = listener.get_transforms()
        
        elapsed = time.time() - start_time
        print(f"\r⏳ {elapsed:.1f}s | Queue: {current_queue_size} | Transforms: {len(transforms)}", end='', flush=True)
        
        if current_queue_size > 0:
            print(f"\n🎯 SUCCESS! Transform data received!")
            print(f"📊 Queue contents: {test_queue}")
            
            # Verify the data format
            if test_queue:
                latest_batch = test_queue[-1]
                print(f"\n✅ Received transform batch:")
                for element_name, pose in latest_batch.items():
                    print(f"  Element: {element_name}")
                    print(f"  Position: {pose['position']}")
                    print(f"  Quaternion: {pose['quaternion']}")
                    
                    # Verify coordinate conversion
                    if element_name == 'dynamic_001':
                        expected_pos = [-0.5, 1.0, 0.0]  # ROS->Rhino: [-y, x, z]
                        expected_quat = [1.0, -0.0, 0.0, 0.0]  # ROS->Rhino: [w, -y, x, z]
                        
                        if pose['position'] == expected_pos and pose['quaternion'] == expected_quat:
                            print("  ✅ Coordinate conversion correct")
                        else:
                            print(f"  ⚠️ Coordinate conversion mismatch")
                            print(f"     Expected pos: {expected_pos}, got: {pose['position']}")
                            print(f"     Expected quat: {expected_quat}, got: {pose['quaternion']}")
            
            received_data = True
            break
        
        time.sleep(0.2)
    
    # Wait for sender thread to complete
    sender_thread.join()
    
    if received_data:
        print(f"\n\n✅ INTEGRATION TEST PASSED!")
        print("🎯 VizorListener successfully received and processed transform data")
        print("🔧 System is ready for AR update button integration")
        return True
    else:
        print(f"\n\n❌ INTEGRATION TEST FAILED!")
        print("⚠️  No transform data received - check ROS bridge configuration")
        return False

if __name__ == "__main__":
    success = test_complete_integration()
    sys.exit(0 if success else 1)