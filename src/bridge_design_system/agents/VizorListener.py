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
import time

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
            # Always update the queue reference if a new one is provided
            if update_queue is not None:
                self.update_queue = update_queue
                print(f"[DEBUG] VizorListener singleton: Updated queue reference to {id(update_queue)}")
                print(f"[DEBUG] VizorListener queue object: {self.update_queue}")
            else:
                print(f"[DEBUG] VizorListener singleton: Keeping existing queue reference {id(self.update_queue)}")
            return

        self._initialized = True
        self.current_element: Optional[str] = None
        self.gaze_history: list = []  # Store (timestamp, element) tuples
        self.gaze_window_seconds = 3.0  # Time window for gaze retrieval
        self.transforms: Dict[str, Union[dict, "Pose"]] = {}
        self.update_queue = update_queue if update_queue is not None else []  # Queue for Direct Parameter Updates
        print(f"[DEBUG] VizorListener __init__: Queue reference set to ID {id(self.update_queue)}")
        self.ros_available = ROS_AVAILABLE
        self.client = None
        self.gaze_subscriber = None
        self.model_subscriber = None
        self._connection_attempted = False

        # Defer ROS connection until first use (lazy loading)
        if self.ros_available:
            self._attempt_ros_connection()

    def _attempt_ros_connection(self, max_retries=3):
        """Attempt to establish ROS connection with retry logic and graceful failure handling."""
        if not self.ros_available:
            return False

        retry_count = 0
        while retry_count < max_retries:
            try:
                print(f"🔄 Attempting ROS connection (attempt {retry_count + 1}/{max_retries})...")
                
                # Initialize ROS client with optimized settings
                self.client = roslibpy.Ros(host="localhost", port=9090)
                self.client.run()
                
                # Wait a moment for connection to stabilize
                time.sleep(0.2)

                # Check if connection is successful
                if not self.client.is_connected:
                    raise ConnectionError("ROS client failed to connect")
                
                print("✅ ROS connection established successfully")
                break
                
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = (2 ** retry_count) * 0.5  # Exponential backoff: 0.5s, 1s, 2s
                    print(f"⚠️ Connection attempt {retry_count} failed: {e}")
                    print(f"🕐 Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    
                    # Cleanup failed connection attempt
                    if self.client is not None:
                        try:
                            self.client.terminate()
                        except:
                            pass
                        self.client = None
                else:
                    print(f"❌ All {max_retries} connection attempts failed: {e}")
                    print("⚠️ ROS connection failed - gaze features will be limited")
                    self._connection_attempted = True
                    return False

        if not self.client or not self.client.is_connected:
            self._connection_attempted = True
            return False

        # Subscribe to HOLO1_GazePoint topic
        try:
            self.gaze_subscriber = roslibpy.Topic(
                self.client, "/HOLO1_GazePoint", "std_msgs/String"
            )
            self.gaze_subscriber.subscribe(self._handle_gaze_message)
            print("📡 Subscribed to /HOLO1_GazePoint for gaze data")

            # Subscribe to HOLO1_Model topic (original implementation)
            try:
                self.model_subscriber = roslibpy.Topic(
                    self.client, "/HOLO1_Model", "vizor_package/Model"
                )
                self.model_subscriber.subscribe(self._handle_model_message)
                print("📡 Subscribed to /HOLO1_Model for transform data")
            except Exception as e:
                print(f"⚠️ /HOLO1_Model subscription failed (transform features disabled): {e}")
                self.model_subscriber = None

            print("✅ ROS connection established - gaze features enabled")
            self._connection_attempted = True
            return True

        except Exception as e:
            print(f"⚠️ ROS subscription failed: {e}")
            self._connection_attempted = True
            return False

    def reconnect(self):
        """Attempt to reconnect to ROS if connection was lost."""
        if self.client is not None:
            try:
                self.cleanup()
            except Exception:
                pass
        
        # Reset connection state
        self._connection_attempted = False
        self.client = None
        self.gaze_subscriber = None
        self.model_subscriber = None
        
        # Attempt new connection
        return self._attempt_ros_connection()

    def _handle_gaze_message(self, message):
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
            position = pose["position"]
            orientation = pose["orientation"]

            is_identity_quat = (
                (abs(orientation["w"] - 1.0) < 1e-6 or abs(orientation["w"] + 1.0) < 1e-6) and
                abs(orientation["x"]) < 1e-6 and
                abs(orientation["y"]) < 1e-6 and
                abs(orientation["z"]) < 1e-6
            )
            
            print(f"[DEBUG] Checking {name}: pos=({position['x']}, {position['y']}, {position['z']}), quat=({orientation['w']}, {orientation['x']}, {orientation['y']}, {orientation['z']})")
            print(f"[DEBUG] is_identity_quat={is_identity_quat}")
            
            if (
                abs(position["x"]) > 1e-6
                or abs(position["y"]) > 1e-6
                or abs(position["z"]) > 1e-6
                or not is_identity_quat
            ):

                # STEP 1: Transform the POSITION vector from ROS (y-right) to Rhino.
                pos = [position["y"], position["x"], position["z"]]

                # STEP 2: Use the quaternion AS-IS. DO NOT transform its components.
                rot = orientation

                # Store the transformed position and the RAW quaternion.
                transform = {"position": pos, "quaternion": rot}
                self.transforms[name] = transform
                print(f"[DEBUG] Including element {name} with non-zero transform")
            else:
                print(f"[DEBUG] Skipping element {name} - zero transform detected")

        if self.transforms and hasattr(self, "update_queue"):
            self.update_queue.append(self.transforms.copy())
            print(
                f"\n[SYSTEM] Transform data for {len(self.transforms)} element(s) queued for update."
            )
            print(f"[DEBUG] Queue reference ID in VizorListener: {id(self.update_queue)}")
            print(f"[DEBUG] Queue length after append: {len(self.update_queue)}")
            print(f"[DEBUG] Queue contents: {self.update_queue}")

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
        from collections import Counter

        if not self.gaze_history:
            return {
                "total_gazes": 0,
                "unique_elements": 0,
                "most_gazed": None,
                "recent_elements": [],
            }

        current_time = time.time()
        cutoff_time = current_time - window_seconds

        recent_gazes = [(ts, elem) for ts, elem in self.gaze_history if ts > cutoff_time]

        if not recent_gazes:
            return {
                "total_gazes": 0,
                "unique_elements": 0,
                "most_gazed": None,
                "recent_elements": [],
            }

        elements = [elem for ts, elem in recent_gazes]
        element_counts = Counter(elements)
        most_gazed = element_counts.most_common(1)[0] if element_counts else None

        return {
            "total_gazes": len(recent_gazes),
            "unique_elements": len(set(elements)),
            "most_gazed": most_gazed[0] if most_gazed else None,
            "most_gazed_count": most_gazed[1] if most_gazed else 0,
            "recent_elements": list(dict.fromkeys(elements)),  # Preserve order, remove duplicates
            "time_span_seconds": (
                recent_gazes[-1][0] - recent_gazes[0][0] if len(recent_gazes) > 1 else 0
            ),
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

    def cleanup(self):
        """Properly cleanup ROS connections and subscribers."""
        try:
            # Unsubscribe from topics first
            if hasattr(self, 'gaze_subscriber') and self.gaze_subscriber is not None:
                try:
                    self.gaze_subscriber.unsubscribe()
                    print("🧹 Unsubscribed from gaze topic")
                except Exception as e:
                    print(f"⚠️ Warning: Failed to unsubscribe from gaze topic: {e}")
                finally:
                    self.gaze_subscriber = None
            
            if hasattr(self, 'model_subscriber') and self.model_subscriber is not None:
                try:
                    self.model_subscriber.unsubscribe()
                    print("🧹 Unsubscribed from model topic")
                except Exception as e:
                    print(f"⚠️ Warning: Failed to unsubscribe from model topic: {e}")
                finally:
                    self.model_subscriber = None
            
            # Close ROS client connection
            if hasattr(self, 'client') and self.client is not None:
                try:
                    if self.client.is_connected:
                        self.client.close()
                        print("🧹 Closed ROS client connection")
                    self.client.terminate()
                except Exception as e:
                    print(f"⚠️ Warning: Failed to close ROS client: {e}")
                finally:
                    self.client = None
            
            # Clear internal state
            self.current_element = None
            if hasattr(self, 'gaze_history'):
                self.gaze_history.clear()
            if hasattr(self, 'transforms'):
                self.transforms.clear()
            
            # Reset connection flags
            self._connection_attempted = False
            
            print("✅ VizorListener cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during VizorListener cleanup: {e}")

    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance to force fresh initialization."""
        if cls._instance is not None:
            try:
                # Cleanup the existing instance
                cls._instance.cleanup()
            except Exception as e:
                print(f"⚠️ Warning: Error cleaning up existing VizorListener: {e}")
            
            # Reset the singleton
            cls._instance = None
            print("🔄 VizorListener singleton reset")

    def __del__(self):
        """Cleanup when the instance is destroyed."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors in destructor
