#!/usr/bin/env python
"""
Script to send a transform message to the /HOLO1_Model ROS topic.
Usage: python send_transform.py <transform_type>
Example: python send_transform.py t1
"""

import sys
import time
import argparse
import roslibpy

# Predefined transform messages


# For Transform T1 - green stays put, red and blue move
TRANSFORM_T1_NAMES = ["dynamic_001", "dynamic_002", "dynamic_003"]
TRANSFORM_T1_POSES = [
    {
        "position": {"x": 0.0, "y": -0.0, "z": 0.0},
        "orientation": {"x": 0.0, "y": -0.0, "z": 0.0, "w": -1.0}
    },
    {
        "position": {"x": -0.06644491851329803, "y": -0.08316001296043396, "z": 0.33045026659965515},
        "orientation": {"x": -0.0, "y": 0.0, "z": -0.0, "w": -1.0}
    },
    {
        "position": {"x": -0.3439379036426544, "y": 0.06487333029508591, "z": -0.025135979056358337},
        "orientation": {"x": -0.0, "y": 0.0, "z": -0.0, "w": -1.0}
    }
]

# For Transform T2 - green stays put, red and blue move but are still touching
TRANSFORM_T2_NAMES = ["dynamic_001", "dynamic_002", "dynamic_003"]
TRANSFORM_T2_POSES = [
    {
        "position": {"x": 0.0, "y": -0.0, "z": 0.0},
        "orientation": {"x": 0.0, "y": -0.0, "z": 0.0, "w": -1.0}
    },
    {
        "position": {"x": -0.2936401963233948, "y": -0.18176478147506714, "z": -0.044508472084999084},
        "orientation": {"x": -0.0, "y": 0.0, "z": -0.0, "w": -1.0}
    },
    {
        "position": {"x": -0.30347174406051636, "y": -0.12241509556770325, "z": -0.15938685834407806},
        "orientation": {"x": -0.0, "y": 0.0, "z": -0.0, "w": -1.0}
    }
]

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Send a transform message to ROS.')
    parser.add_argument('transform_type', type=str, choices=['t1', 't2'],
                        help='Transform type (t1 or t2)')
    parser.add_argument('--host', type=str, default='localhost', 
                        help='ROS bridge server host (default: localhost)')
    parser.add_argument('--port', type=int, default=9090, 
                        help='ROS bridge server port (default: 9090)')
    return parser.parse_args()

def send_transform(transform_type, host='localhost', port=9090):
    """
    Send a transform message to the /HOLO1_Model topic.
    
    Args:
        transform_type: String 't1' or 't2' to determine which transform to send
        host: ROS bridge host
        port: ROS bridge port
    """
    # Select the transform message based on type
    if transform_type == 't1':
        names = TRANSFORM_T1_NAMES
        poses = TRANSFORM_T1_POSES
    else:  # transform_type == 't2'
        names = TRANSFORM_T2_NAMES
        poses = TRANSFORM_T2_POSES
    
    try:
        # Connect to ROS bridge
        client = roslibpy.Ros(host=host, port=port)
        client.run()
        
        # Check if connected
        if not client.is_connected:
            print(f"Failed to connect to ROS bridge at {host}:{port}")
            return False
            
        print(f"Connected to ROS bridge at {host}:{port}")
        
        # Create publisher for the topic
        topic = roslibpy.Topic(client, '/HOLO1_Model', 'vizor_package/Model')
        
        # Create and send the message with proper structure for vizor_package/Model
        message = {
            'names': names,
            'poses': poses
        }
        print(f"Sending {transform_type} transform to /HOLO1_Model")
        topic.publish(roslibpy.Message(message))
        
        # Small delay to ensure the message is sent
        time.sleep(0.5)
        
        # Clean up
        topic.unadvertise()
        client.terminate()
        
        print("Transform message sent successfully")
        return True
        
    except Exception as e:
        print(f"Error sending transform message: {e}")
        return False

if __name__ == "__main__":
    args = parse_arguments()
    success = send_transform(args.transform_type, args.host, args.port)
    sys.exit(0 if success else 1)
