'''
VizorListener Behaviour: 

Listens to topic: HOLO1_GazePoint
The received input is a string message, giving an element name (uniquely identifiable)
The element names are mostly 01red, 01green, 01blue, 02red, 02green, 02blue, etc. 
But it can also be link1, link2, link3 etc. 
When the input is received, store it in variable: current_element

Listens to topic: HOLO1_Model
The received input is a custom message containing: 
string[] names
geometry_msgs/Pose[] poses
It describes the transformed position of element [name] to pose [pose]. 
When the input is received, transform the element based on pose (containing position + orientation)
If the transform is zero (no movement), simply ignore it. 
If the transform is non-zero, return the list of transforms in a dictionary with the name as key

The agents/geometry_agent_stdio.py will hold an instance to this class 

'''

import roslibpy
import numpy as np
from typing import Dict, Optional, List
from geometry_msgs.msg import Pose

class VizorListener:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VizorListener, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.current_element: Optional[str] = None
        self.transforms: Dict[str, Pose] = {}
        
        # Initialize ROS client
        self.client = roslibpy.Ros(host='localhost', port=9090)
        self.client.run()
        
        # Subscribe to HOLO1_GazePoint topic
        self.gaze_subscriber = roslibpy.Topic(
            self.client,
            '/HOLO1_GazePoint',
            'std_msgs/String'
        )
        self.gaze_subscriber.subscribe(self._handle_gaze_message)
        
        # Subscribe to HOLO1_Model topic
        self.model_subscriber = roslibpy.Topic(
            self.client,
            '/HOLO1_Model',
            'vizor_package/Model'
        )
        self.model_subscriber.subscribe(self._handle_model_message)

    def _handle_gaze_message(self, message):
        self.current_element = message['data']

    def _handle_model_message(self, message):
        self.transforms = {}
        names = message['names']
        poses = message['poses']
        
        for name, pose in zip(names, poses):
            # Check if the transform is non-zero
            position = pose['position']
            orientation = pose['orientation']
            
            # Check if position or orientation has changed
            if (abs(position['x']) > 1e-6 or 
                abs(position['y']) > 1e-6 or 
                abs(position['z']) > 1e-6 or
                abs(orientation['x']) > 1e-6 or
                abs(orientation['y']) > 1e-6 or
                abs(orientation['z']) > 1e-6 or
                abs(orientation['w'] - 1.0) > 1e-6):
                
                # ros to rhino transition
                pos = [-position['y'], position['x'], position['z']] 
                rot = [orientation['w'], -orientation['y'], orientation['x'], orientation['z']] 
                transform = {"position": pos, "quaternion": rot}
                self.transforms[name] = transform
        
        #TODO: if transforms is not empty, escalate this into the geometry agent


    def get_transforms(self) -> Dict[str, Pose]:
        """Return the current transforms dictionary"""
        return self.transforms.copy()

    def get_current_element(self) -> Optional[str]:
        """Return the current element being gazed at"""
        return self.current_element

    def __del__(self):
        """Cleanup when the instance is destroyed"""
        if hasattr(self, 'client'):
            self.client.terminate()