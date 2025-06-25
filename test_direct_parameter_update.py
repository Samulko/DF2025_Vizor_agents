#!/usr/bin/env python3
"""
Test script for Direct Parameter Update workflow without requiring ROS.

This script simulates the HoloLens transform data by directly injecting 
transform messages into the VizorListener's queue, then running the 
main.py interactive loop to process them.

Usage: python test_direct_parameter_update.py [t1|t2]
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bridge_design_system.main import (
    quaternion_to_direction_vector, 
    format_direct_update_task,
    validate_environment,
    get_monitoring_callback
)
from src.bridge_design_system.agents import TriageAgent
from src.bridge_design_system.agents.VizorListener import VizorListener
from src.bridge_design_system.state.component_registry import initialize_registry
from src.bridge_design_system.config.logging_config import get_logger

logger = get_logger(__name__)

# Transform data from the original send_transform.py
TRANSFORM_T1_DATA = {
    "dynamic_001": {
        "position": [0.0, -0.0, 0.0],  # Already converted to ROS→Rhino format
        "quaternion": [-1.0, 0.0, -0.0, 0.0]  # WXYZ format
    },
    "dynamic_002": {
        "position": [0.08316001296043396, -0.06644491851329803, 0.33045026659965515],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    },
    "dynamic_003": {
        "position": [-0.06487333029508591, -0.3439379036426544, -0.025135979056358337],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    }
}

TRANSFORM_T2_DATA = {
    "dynamic_001": {
        "position": [0.0, -0.0, 0.0],
        "quaternion": [-1.0, 0.0, -0.0, 0.0]
    },
    "dynamic_002": {
        "position": [0.18176478147506714, -0.2936401963233948, -0.044508472084999084],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    },
    "dynamic_003": {
        "position": [0.12241509556770325, -0.30347174406051636, -0.15938685834407806],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    }
}

def simulate_transform_message(transform_type="t1"):
    """
    Simulate the complete Direct Parameter Update workflow by directly calling VizorListener 
    message handler and processing the queue.
    
    Args:
        transform_type: "t1" or "t2" for different transform configurations
    """
    print(f"🧪 Starting Direct Parameter Update Test - Transform {transform_type.upper()}")
    print("=" * 60)
    
    # Validate environment
    if not validate_environment():
        print("❌ Environment validation failed")
        return False
    
    try:
        # Initialize system components
        print("🔧 Initializing system components...")
        registry = initialize_registry()
        monitoring_callback = get_monitoring_callback(enable_embedded_monitoring=False)
        
        # Create transform queue
        TRANSFORM_UPDATE_QUEUE = []
        
        # Initialize VizorListener with our queue (without ROS)
        vizor_listener = VizorListener(update_queue=TRANSFORM_UPDATE_QUEUE)
        
        # Ensure the queue reference is properly set
        vizor_listener.update_queue = TRANSFORM_UPDATE_QUEUE
        
        # Initialize triage agent
        triage = TriageAgent(component_registry=registry, monitoring_callback=monitoring_callback)
        
        print("✅ System components initialized successfully")
        
        # Select transform data
        transform_data = TRANSFORM_T1_DATA if transform_type == "t1" else TRANSFORM_T2_DATA
        
        print(f"\n📡 Simulating {transform_type.upper()} transform message...")
        print(f"Elements to update: {list(transform_data.keys())}")
        
        # Create a mock ROS message in the format that _handle_model_message expects
        mock_message = {
            "names": list(transform_data.keys()),
            "poses": []
        }
        
        # Convert our transform data to ROS message format
        for element_name in transform_data:
            pose_data = transform_data[element_name]
            # Convert back from Rhino to ROS format for the message handler
            ros_pos = pose_data['position']  # Already in Rhino format, need to convert back
            ros_quat = pose_data['quaternion']  # Already in WXYZ format
            
            # Convert Rhino back to ROS format for message handling
            ros_pose = {
                "position": {
                    "x": ros_pos[1],  # Rhino Y -> ROS X
                    "y": -ros_pos[0], # Rhino -X -> ROS Y  
                    "z": ros_pos[2]   # Rhino Z -> ROS Z
                },
                "orientation": {
                    "w": ros_quat[0],  # W stays W
                    "x": ros_quat[2],  # Rhino Y -> ROS X
                    "y": -ros_quat[1], # Rhino -X -> ROS Y
                    "z": ros_quat[3]   # Rhino Z -> ROS Z
                }
            }
            mock_message["poses"].append(ros_pose)
        
        # Directly call the VizorListener message handler to simulate ROS message
        print("🔄 Simulating ROS message processing...")
        vizor_listener._handle_model_message(mock_message)
        
        print(f"✅ Message processed, queue size: {len(TRANSFORM_UPDATE_QUEUE)}")
        
        # Process the queue (simulating the interactive_mode logic)
        if TRANSFORM_UPDATE_QUEUE:
            print(f"\n🔄 Processing {len(TRANSFORM_UPDATE_QUEUE)} queued transform batch(es)...")
            
            for transform_batch in TRANSFORM_UPDATE_QUEUE:
                for element_name, pose in transform_batch.items():
                    # Extract element ID (this matches main.py logic)
                    element_id = element_name.split('_')[-1]  # Keep full element ID: 001, 002, 003
                    
                    # Convert quaternion to direction vector
                    new_pos = pose['position']
                    new_dir = quaternion_to_direction_vector(pose['quaternion'])
                    
                    # Format the task for GeometryAgent
                    task = format_direct_update_task(element_id, new_pos, new_dir)
                    
                    print(f"\n🎯 Processing element {element_id}:")
                    print(f"   Position: {new_pos}")
                    print(f"   Direction: {new_dir}")
                    print(f"   Task: {task[:80]}...")
                    
                    try:
                        # Send the task to the triage agent
                        print(f"   📤 Sending to GeometryAgent...")
                        response = triage.handle_design_request(request=task, gaze_id=None)
                        
                        if response.success:
                            print(f"   ✅ Element {element_id} updated successfully")
                            # Show a preview of the response
                            preview = response.message[:200] + "..." if len(response.message) > 200 else response.message
                            print(f"   Response: {preview}")
                        else:
                            print(f"   ❌ Element {element_id} update failed")
                            print(f"   Error: {response.message}")
                            
                    except Exception as e:
                        print(f"   ❌ Element {element_id} update error: {e}")
                        
                    # Small delay between elements
                    time.sleep(0.5)
            
            # Clear the queue
            TRANSFORM_UPDATE_QUEUE.clear()
            print(f"\n✅ Transform queue processed successfully")
        else:
            print("❌ No transforms were queued - message processing failed")
            return False
        
        print(f"\n🎉 Direct Parameter Update test completed!")
        print("💡 Check Rhino Grasshopper to see if elements have moved")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main entry point for the test."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Direct Parameter Update workflow')
    parser.add_argument('transform_type', nargs='?', default='t1', choices=['t1', 't2'],
                        help='Transform type to test (t1 or t2, default: t1)')
    
    args = parser.parse_args()
    
    print("🧪 Direct Parameter Update Test")
    print("This test simulates HoloLens transform data without requiring ROS")
    print("Make sure Rhino Grasshopper is open with the bridge components loaded")
    print()
    
    success = simulate_transform_message(args.transform_type)
    
    if success:
        print("\n🎯 Test completed successfully!")
        print("👀 Check Rhino Grasshopper to verify elements have moved")
    else:
        print("\n❌ Test failed!")
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()