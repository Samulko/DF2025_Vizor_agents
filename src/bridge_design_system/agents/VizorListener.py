"""
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

"""

from typing import Dict, Optional, Union

# Optional ROS imports with graceful fallback
try:
    import roslibpy
    # Note: geometry_msgs.msg.Pose is not available in roslibpy
    # We'll use dict representation for pose data instead
    ROS_AVAILABLE = True
except ImportError:
    roslibpy = None
    ROS_AVAILABLE = False

# Define a simple Pose type for type hints when ROS is not available
Pose = dict if ROS_AVAILABLE else None


class VizorListener:
    _instance = None

    def __new__(cls, update_queue=None):
        if cls._instance is None:
            cls._instance = super(VizorListener, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, update_queue=None):
        if self._initialized:
            # Update the queue if a new one is provided
            if update_queue is not None:
                self.update_queue = update_queue
            return

        self._initialized = True
        self.current_element: Optional[str] = None
        self.gaze_history: list = []  # Store (timestamp, element) tuples
        self.gaze_window_seconds = 3.0  # Time window for gaze retrieval
        self.transforms: Dict[str, Union[dict, "Pose"]] = {}
        self.update_queue = update_queue or []  # Queue for Direct Parameter Updates
        self.ros_available = ROS_AVAILABLE
        self.client = None
        self.gaze_subscriber = None
        self.model_subscriber = None
        self._connection_attempted = False

        # Defer ROS connection until first use (lazy loading)
        if self.ros_available:
            self._attempt_ros_connection()

    def _attempt_ros_connection(self):
        """Attempt to establish ROS connection with graceful failure handling."""
        if self._connection_attempted or not self.ros_available:
            return False

        self._connection_attempted = True
        try:
            # Initialize ROS client
            self.client = roslibpy.Ros(host="localhost", port=9090)
            self.client.run()

            # Check if connection is successful
            if not self.client.is_connected:
                print("⚠️ ROS connection failed - gaze features will be limited")
                return False

            # Subscribe to HOLO1_GazePoint topic
            self.gaze_subscriber = roslibpy.Topic(
                self.client, "/HOLO1_GazePoint", "std_msgs/String"
            )
            self.gaze_subscriber.subscribe(self._handle_gaze_message)

            # Subscribe to HOLO1_Model topic (optional - may not be available)
            try:
                self.model_subscriber = roslibpy.Topic(
                    self.client, "/HOLO1_Model", "std_msgs/String"  # Try std_msgs/String first
                )
                self.model_subscriber.subscribe(self._handle_model_message)
                print("📡 Subscribed to /HOLO1_Model for transform data")
            except Exception as e:
                print(f"⚠️ /HOLO1_Model subscription failed (transform features disabled): {e}")
                self.model_subscriber = None

            print("✅ ROS connection established - gaze features enabled")
            return True

        except Exception as e:
            print(f"⚠️ ROS connection failed: {e}")
            self.client = None
            return False

    def _handle_gaze_message(self, message):
        import time
        timestamp = time.time()
        element = message["data"]
        
        self.current_element = element
        
        # Add to gaze history with timestamp
        self.gaze_history.append((timestamp, element))
        
        # Clean old entries (keep only last 10 seconds of history)
        cutoff_time = timestamp - 10.0
        self.gaze_history = [(ts, elem) for ts, elem in self.gaze_history if ts > cutoff_time]

    def _handle_model_message(self, message):
        """Handle incoming model transform messages from ROS."""
        self.transforms = {}
        names = message["names"]
        poses = message["poses"]

        for name, pose in zip(names, poses):
            # Check if the transform is non-zero
            position = pose["position"]
            orientation = pose["orientation"]

            # Check if position or orientation has changed
            if (
                abs(position["x"]) > 1e-6
                or abs(position["y"]) > 1e-6
                or abs(position["z"]) > 1e-6
                or abs(orientation["x"]) > 1e-6
                or abs(orientation["y"]) > 1e-6
                or abs(orientation["z"]) > 1e-6
                or abs(orientation["w"] - 1.0) > 1e-6
            ):

                # ROS to Rhino coordinate system transition
                pos = [-position["y"], position["x"], position["z"]]
                rot = [orientation["w"], -orientation["y"], orientation["x"], orientation["z"]]

                # Store as dictionary for compatibility with both ROS and non-ROS modes
                transform = {"position": pos, "quaternion": rot}
                self.transforms[name] = transform

        # Queue raw transform data for Direct Parameter Update processing
        if self.transforms and hasattr(self, 'update_queue'):
            self.update_queue.append(self.transforms.copy())
            print(f"\n[SYSTEM] Transform data for {len(self.transforms)} element(s) queued for update.")

    def get_transforms(self) -> Dict[str, Union[dict, "Pose"]]:
        """Return the current transforms dictionary."""
        return self.transforms.copy()

    def get_current_element(self) -> Optional[str]:
        """Return the current element being gazed at."""
        return self.current_element
    
    def get_recent_gaze(self, window_seconds: Optional[float] = None) -> Optional[str]:
        """Get the most recent gaze within a time window.
        
        Args:
            window_seconds: Time window in seconds (default: 3.0 seconds)
            
        Returns:
            Most recent element gazed at within the time window, or None
        """
        import time
        
        if window_seconds is None:
            window_seconds = self.gaze_window_seconds
            
        if not self.gaze_history:
            return None
            
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Find the most recent gaze within the time window
        recent_gazes = [(ts, elem) for ts, elem in self.gaze_history if ts > cutoff_time]
        
        if recent_gazes:
            # Return the most recent element
            return recent_gazes[-1][1]
        
        return None
    
    def get_gaze_history_summary(self, window_seconds: float = 10.0) -> dict:
        """Get a summary of recent gaze activity.
        
        Args:
            window_seconds: Time window to analyze
            
        Returns:
            Dictionary with gaze activity summary
        """
        import time
        from collections import Counter
        
        if not self.gaze_history:
            return {"total_gazes": 0, "unique_elements": 0, "most_gazed": None, "recent_elements": []}
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        recent_gazes = [(ts, elem) for ts, elem in self.gaze_history if ts > cutoff_time]
        
        if not recent_gazes:
            return {"total_gazes": 0, "unique_elements": 0, "most_gazed": None, "recent_elements": []}
        
        elements = [elem for ts, elem in recent_gazes]
        element_counts = Counter(elements)
        most_gazed = element_counts.most_common(1)[0] if element_counts else None
        
        return {
            "total_gazes": len(recent_gazes),
            "unique_elements": len(set(elements)),
            "most_gazed": most_gazed[0] if most_gazed else None,
            "most_gazed_count": most_gazed[1] if most_gazed else 0,
            "recent_elements": list(dict.fromkeys(elements)),  # Preserve order, remove duplicates
            "time_span_seconds": recent_gazes[-1][0] - recent_gazes[0][0] if len(recent_gazes) > 1 else 0
        }

    def is_ros_connected(self) -> bool:
        """Check if ROS connection is active."""
        return (
            self.client is not None
            and hasattr(self.client, "is_connected")
            and self.client.is_connected
        )

    def get_connection_status(self) -> dict:
        """Get detailed connection status for debugging."""
        return {
            "ros_available": self.ros_available,
            "connection_attempted": self._connection_attempted,
            "client_exists": self.client is not None,
            "is_connected": self.is_ros_connected(),
            "gaze_subscriber_active": self.gaze_subscriber is not None,
            "model_subscriber_active": self.model_subscriber is not None,
        }

    def __del__(self):
        """Cleanup when the instance is destroyed."""
        if hasattr(self, "client") and self.client is not None:
            try:
                self.client.terminate()
            except Exception:
                pass  # Ignore cleanup errors
