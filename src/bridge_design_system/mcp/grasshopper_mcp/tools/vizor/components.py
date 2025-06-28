"""
Vizor components module for Grasshopper MCP.

This module contains functions for working with Vizor components in Grasshopper.
Vizor is a library for augmented reality in Grasshopper.
"""

import sys
from typing import Any, Dict

# Add the project root to the Python path when running as a script
if __name__ == "__main__":
    import pathlib
    import sys

    # Get the absolute path of the current file
    current_file = pathlib.Path(__file__).resolve()
    # Get the project root (three directories up from this file)
    project_root = current_file.parent.parent.parent
    # Add the project root to the Python path
    sys.path.insert(0, str(project_root))

# Import the send_to_grasshopper function
from grasshopper_mcp.utils.communication import send_to_grasshopper


def add_vizor_component(component_name: str, x: float, y: float) -> Dict[str, Any]:
    """
    Add a Vizor component to the Grasshopper canvas.

    The Vizor library provides components for working with augmented reality in Grasshopper.
    These components are organized into several categories:

    1. Object Components - Components for working with AR devices and objects
    2. Content Components - Components for creating and managing AR content
    3. Task Components - Components for defining and managing tasks
    4. Utility Components - Components for various utility functions

    Args:
        component_name: Name of the Vizor component (e.g., "TrackedObject", "ARWorker", "MakeMesh")
        x: X coordinate on the canvas
        y: Y coordinate on the canvas

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    # Map of Vizor component names to their GUIDs
    # These GUIDs are extracted from the Vizor component classes
    vizor_component_mapping = {
        # 1_Object category
        "trackedobject": "bc1f4be7-bcf1-4d24-bcf8-d3c97a2262d5",
        "tracked object": "bc1f4be7-bcf1-4d24-bcf8-d3c97a2262d5",
        "arworker": "3a1af2b6-e0fa-4fe3-a08e-e41a596cb496",
        "ar worker": "3a1af2b6-e0fa-4fe3-a08e-e41a596cb496",
        "arworkerteam": "593c1864-a7a6-481a-916f-5ec75855e540",
        "ar worker team": "593c1864-a7a6-481a-916f-5ec75855e540",
        "robot": "afb86c19-713d-45b6-873c-27b22aab4f95",
        "wsconnection": "4dd685c6-885c-4d9f-a807-c25d526811a9",
        "ws connection": "4dd685c6-885c-4d9f-a807-c25d526811a9",
        # 2_Content category
        "constructcontent": "bd2ab8e4-9622-4ce4-bead-1570878b4532",
        "construct content": "bd2ab8e4-9622-4ce4-bead-1570878b4532",
        "makemesh": "6bcc3c7e-4f62-4369-82f0-4fd02e28ce4c",
        "make mesh": "6bcc3c7e-4f62-4369-82f0-4fd02e28ce4c",
        "maketext": "daffdd63-8fc0-4b92-a56a-c31ae4eadaf4",
        "make text": "daffdd63-8fc0-4b92-a56a-c31ae4eadaf4",
        "maketrajectory": "9a03197b-3b8b-492e-93f1-32baf9fd7a12",
        "make trajectory": "9a03197b-3b8b-492e-93f1-32baf9fd7a12",
        "makewireframe": "7b6e87d9-0187-4cce-bca1-d7393fd01070",
        "make wireframe": "7b6e87d9-0187-4cce-bca1-d7393fd01070",
        "makeworkarea": "3ec4d7c4-933a-49c2-aa15-dc3a23452db6",
        "make work area": "3ec4d7c4-933a-49c2-aa15-dc3a23452db6",
        "scenemodel": "028cda0a-93ed-4954-90aa-de13be27da43",
        "scene model": "028cda0a-93ed-4954-90aa-de13be27da43",
        # 3_Task category
        "constructtask": "97128de9-5dbb-4b95-a3e7-e293506f6791",
        "construct task": "97128de9-5dbb-4b95-a3e7-e293506f6791",
        "deconstructtask": "efec098a-72cb-44a6-a113-8bff140f6baa",
        "deconstruct task": "efec098a-72cb-44a6-a113-8bff140f6baa",
        "maketaskseries": "d66d05ad-6746-4510-9032-ca0abce8db58",
        "make task series": "d66d05ad-6746-4510-9032-ca0abce8db58",
        "safetyzoneconfiguration": "85baf117-c74a-4cbb-9d8a-723572eec403",
        "safety zone config": "85baf117-c74a-4cbb-9d8a-723572eec403",
        "safetyzone": "85baf117-c74a-4cbb-9d8a-723572eec403",
        "safety zone": "85baf117-c74a-4cbb-9d8a-723572eec403",
        "taskcontroller": "64507e61-dceb-41af-b34e-fdf823d4a111",
        "task controller": "64507e61-dceb-41af-b34e-fdf823d4a111",
        # 4_Utilities category
        "devicetracker": "d4d5cd1d-a9f7-438a-bce6-c83ebce3f3a2",
        "device tracker": "d4d5cd1d-a9f7-438a-bce6-c83ebce3f3a2",
        "monitorworkarea": "1083875e-9e6e-4574-88e0-36f75a629db2",
        "monitor work area": "1083875e-9e6e-4574-88e0-36f75a629db2",
        "motionsimulation": "1d5fcb9f-8af4-4cdc-b166-c15f958f4bde",  # Using SimulateDevice's GUID as placeholder
        "motion simulation": "1d5fcb9f-8af4-4cdc-b166-c15f958f4bde",  # Using SimulateDevice's GUID as placeholder
        "planningscenemodel": "431b9c35-d484-4846-aa12-520d3fe64ae0",
        "planning scene model": "431b9c35-d484-4846-aa12-520d3fe64ae0",
        "plantrajectory": "54a527c3-8a74-4c1b-aed0-00427a87adbd",
        "plan trajectory": "54a527c3-8a74-4c1b-aed0-00427a87adbd",
        "robotexecution": "fbc5cfd7-580b-44eb-96af-12bb8f3ae636",
        "robot execution": "fbc5cfd7-580b-44eb-96af-12bb8f3ae636",
        "sensortracker": "58118ff7-fa58-4cc1-b080-ca617fb73ece",
        "sensor tracker": "58118ff7-fa58-4cc1-b080-ca617fb73ece",
        "simulatedevice": "1d5fcb9f-8af4-4cdc-b166-c15f958f4bde",
        "simulate device": "1d5fcb9f-8af4-4cdc-b166-c15f958f4bde",
    }

    # Normalize the component name
    normalized_name = component_name.lower().replace(" ", "")

    # Check if the component exists in our mapping
    if normalized_name in vizor_component_mapping:
        component_guid = vizor_component_mapping[normalized_name]
        print(
            f"Adding Vizor component with GUID: {component_guid} at position ({x}, {y})",
            file=sys.stderr,
        )

        # Prepare parameters for the add_component command using the GUID
        params = {"type": component_guid, "x": x, "y": y}

        # Send the command to Grasshopper
        return send_to_grasshopper("add_component", params)
    else:
        # If not found in our mapping, try searching for the component by name
        # First, try with VizorGH category
        vizor_name = f"VizorGH {component_name}"
        print(f"Component not found in mapping, trying: {vizor_name}", file=sys.stderr)

        # Prepare parameters for the add_component command
        params = {"type": vizor_name, "x": x, "y": y}

        # Try to send the command to Grasshopper
        result = send_to_grasshopper("add_component", params)

        # If that fails, try with just the component name
        if not result.get("success", False):
            print(
                f"Failed to add component as '{vizor_name}', trying with just '{component_name}'",
                file=sys.stderr,
            )
            params["type"] = component_name
            result = send_to_grasshopper("add_component", params)

        return result


def vizor_tracked_object(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a TrackedObject component to the Grasshopper canvas.

    The TrackedObject component registers a physical object in the AR system that can be tracked in space.

    Purpose:
    - Register a physical object that will be tracked in the AR environment
    - Provide a reference point for other AR content
    - Enable spatial tracking of real-world objects

    Inputs:
    - Websocket Object: Connection to the AR system
    - Disable: Toggle to enable/disable the tracking
    - Device Name: Identifier for the tracked object (default: "assembly")

    Outputs:
    - Output: Status message about the tracked object
    - Tracked Device: The registered tracked object that can be used by other components

    Usage:
    - Connect a WsConnection component to the Websocket Object input
    - Set a unique name for the tracked object
    - Use the output Tracked Device as input for other components that need to reference this object

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("TrackedObject", x, y)


def vizor_ar_worker(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add an ARWorker component to the Grasshopper canvas.

    The ARWorker component registers an AR device (like HoloLens) in the system.

    Purpose:
    - Register an AR headset or device in the system
    - Define skills and capabilities of the AR user
    - Establish communication with AR devices

    Inputs:
    - Websocket Object: Connection to the AR system
    - Disable: Toggle to enable/disable the AR device
    - Device Name: Identifier for the AR device (default: "HOLO1")
    - Skill Configuration: JSON dictionary defining the skills of this AR worker

    Outputs:
    - Output: Status message about the AR device
    - AR Device: The registered AR device that can be used by other components

    Usage:
    - Connect a WsConnection component to the Websocket Object input
    - Set a unique name for the AR device
    - Define skills in the Skill Configuration input (e.g., '{"robot-control": 1, "screw": 1, "pick-and-place": 1}')
    - Use the output AR Device as input for components that need to send content to this device

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("ARWorker", x, y)


def vizor_robot(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a Robot component to the Grasshopper canvas.

    The Robot component registers a robot in the AR system.

    Purpose:
    - Register a robot in the AR system
    - Define robot properties and capabilities
    - Enable robot control and visualization in AR

    Inputs:
    - Websocket Object: Connection to the AR system
    - Disable: Toggle to enable/disable the robot
    - Device Name: Identifier for the robot (default: "robot1")
    - Robot Type: Type of robot (e.g., "UR10", "KUKA")

    Outputs:
    - Output: Status message about the robot
    - Robot Device: The registered robot device that can be used by other components

    Usage:
    - Connect a WsConnection component to the Websocket Object input
    - Set a unique name for the robot
    - Specify the robot type
    - Use the output Robot Device as input for components that need to control or reference this robot

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("Robot", x, y)


def vizor_ws_connection(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a WsConnection component to the Grasshopper canvas.

    The WsConnection component establishes a WebSocket connection to the AR system.

    Purpose:
    - Create a connection to the AR system
    - Enable communication between Grasshopper and AR devices
    - Serve as the foundation for all AR interactions

    Inputs:
    - Address: WebSocket server address (default: "ws://127.0.0.1:9090")
    - Reset: Toggle to restart the connection

    Outputs:
    - Websocket Object: The connection object that can be used by other components

    Usage:
    - Set the WebSocket server address
    - Connect the Websocket Object output to other Vizor components that require a connection
    - This component must be used before any other Vizor components

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("WsConnection", x, y)


def vizor_construct_content(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a ConstructContent component to the Grasshopper canvas.

    The ConstructContent component combines different types of AR content (meshes, wireframes, text) into a single content object.

    Purpose:
    - Combine different AR content types into a single object
    - Create composite AR content for visualization
    - Organize and manage AR content

    Inputs:
    - Name: Name for the content object (default: "content object")
    - Meshes: Mesh objects for AR visualization
    - Wireframes: Wireframe objects for AR visualization
    - Texts: Text objects for AR visualization
    - Level of Detail: Integer specifying the level of detail (default: 0)

    Outputs:
    - Content Object: The combined AR content object that can be used by other components

    Usage:
    - Connect MakeMesh, MakeWireframe, and MakeText components to the respective inputs
    - Set a descriptive name for the content
    - Use the Content Object output in a SceneModel or TaskController component

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("ConstructContent", x, y)


def vizor_make_mesh(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a MakeMesh component to the Grasshopper canvas.

    The MakeMesh component creates mesh objects for AR visualization.

    Purpose:
    - Create 3D mesh objects for AR visualization
    - Define appearance properties of 3D objects in AR
    - Prepare geometry for AR display

    Inputs:
    - Target Anchor: Device to anchor the mesh to
    - Meshes: Rhino mesh objects to visualize in AR
    - Names: Names for each mesh (optional)
    - Colors: Colors for each mesh (optional)
    - Materials: Material definitions for each mesh (optional)
    - Rules: Visualization rules for each mesh (optional)

    Outputs:
    - Output: Status message
    - Mesh Objects: The created AR mesh objects

    Usage:
    - Connect a TrackedObject or Robot component to the Target Anchor input
    - Provide Rhino mesh geometry to visualize
    - Optionally set names, colors, and materials
    - Use the Mesh Objects output in a ConstructContent component

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("MakeMesh", x, y)


def vizor_device_tracker(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a DeviceTracker component to the Grasshopper canvas.

    The DeviceTracker component tracks the position and orientation of an AR device.

    Purpose:
    - Track the position and orientation of an AR device in real-time
    - Get spatial information from AR devices
    - Enable spatial awareness in AR applications

    Inputs:
    - AR Device: The AR device to track
    - Disable: Toggle to enable/disable tracking

    Outputs:
    - Output: Status message
    - Position: Current position of the device
    - Orientation Plane: Current orientation of the device

    Usage:
    - Connect an ARWorker component to the AR Device input
    - Use the Position and Orientation outputs to get real-time spatial data
    - This component is useful for creating spatially-aware AR applications

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("DeviceTracker", x, y)


def vizor_make_text(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a MakeText component to the Grasshopper canvas.

    The MakeText component creates text objects for AR visualization.

    Purpose:
    - Create text labels and annotations in AR
    - Display information in the AR environment
    - Add textual context to AR scenes

    Inputs:
    - Target Anchor: Device to anchor the text to
    - Text Strings: Text content to display in AR
    - Positions: 3D positions for each text string
    - Names: Names for each text object (optional)
    - Colors: Colors for each text object (optional)
    - Font Sizes: Font sizes for each text object (optional)
    - Rules: Visualization rules for each text object (optional)

    Outputs:
    - Output: Status message
    - Text Objects: The created AR text objects

    Usage:
    - Connect a TrackedObject or Robot component to the Target Anchor input
    - Provide text strings and their 3D positions
    - Optionally set names, colors, and font sizes
    - Use the Text Objects output in a ConstructContent component

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("MakeText", x, y)


def vizor_make_trajectory(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a MakeTrajectory component to the Grasshopper canvas.

    The MakeTrajectory component creates trajectory paths for AR visualization and robot motion.

    Purpose:
    - Create motion paths for robots in AR
    - Visualize planned trajectories
    - Define motion sequences for AR animation

    Inputs:
    - Target Anchor: Device to anchor the trajectory to
    - Planes: List of planes defining the trajectory path
    - Names: Names for each trajectory (optional)
    - Colors: Colors for each trajectory (optional)
    - Rules: Visualization rules for each trajectory (optional)

    Outputs:
    - Output: Status message
    - Trajectory Objects: The created AR trajectory objects

    Usage:
    - Connect a Robot component to the Target Anchor input
    - Provide a list of planes defining the trajectory path
    - Optionally set names and colors
    - Use the Trajectory Objects output in a ConstructContent component

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("MakeTrajectory", x, y)


def vizor_scene_model(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a SceneModel component to the Grasshopper canvas.

    The SceneModel component manages AR content and sends it to AR devices.

    Purpose:
    - Manage and organize AR content
    - Send content to AR devices
    - Control the AR scene

    Inputs:
    - GH Control: Toggle for using Grasshopper as the scene controller
    - AR Devices: List of AR devices to send content to
    - Content Objects: List of content objects to include in the scene
    - Trigger Send: Toggle to manually trigger sending the content

    Outputs:
    - Output: Status message

    Usage:
    - Connect ARWorker components to the AR Devices input
    - Connect ConstructContent components to the Content Objects input
    - Set GH Control to true for Grasshopper to control the scene
    - Toggle Trigger Send to update the AR scene

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("SceneModel", x, y)


def vizor_construct_task(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a ConstructTask component to the Grasshopper canvas.

    The ConstructTask component creates task definitions for AR-guided operations.

    Purpose:
    - Define tasks for AR-guided operations
    - Create step-by-step instructions for AR users
    - Organize work procedures in AR

    Inputs:
    - Task Name: Name of the task
    - Task ID: Unique identifier for the task
    - Target Device: Device that will perform the task
    - Content Object: AR content associated with the task
    - Task Type: Type of task (e.g., "assembly", "inspection")
    - Skill Required: Skill level required for the task
    - Deadline: Time limit for the task (optional)
    - Safety Zone: Safety zone configuration for the task (optional)

    Outputs:
    - Task Object: The created task object

    Usage:
    - Connect an ARWorker or Robot component to the Target Device input
    - Connect a ConstructContent component to the Content Object input
    - Define task parameters like name, ID, type, and skill required
    - Use the Task Object output in a TaskController component

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("ConstructTask", x, y)


def vizor_task_controller(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a TaskController component to the Grasshopper canvas.

    The TaskController component manages and executes AR tasks.

    Purpose:
    - Control and manage AR tasks
    - Coordinate task execution
    - Monitor task progress

    Inputs:
    - GH Control: Toggle for using Grasshopper as the task controller
    - Start: Toggle to initiate the task sequence
    - HRC Tasks: List of tasks to execute
    - Disable: Toggle to enable/disable the controller

    Outputs:
    - Current Task: The task currently being executed
    - Process Log: Log of task execution
    - Current Geometry: Current position of task geometry

    Usage:
    - Connect ConstructTask components to the HRC Tasks input
    - Set GH Control to true for Grasshopper to control the tasks
    - Toggle Start to begin task execution
    - Monitor the Process Log for task status

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("TaskController", x, y)


def vizor_robot_execution(x: float = 100.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a RobotExecution component to the Grasshopper canvas.

    The RobotExecution component executes robot tasks.

    Purpose:
    - Execute robot tasks
    - Control robot motion
    - Integrate robots with AR workflows

    Inputs:
    - Robot: The robot to control
    - Robot Task: The task for the robot to execute
    - Start: Toggle to start execution
    - Physical: Toggle for physical execution vs. simulation

    Outputs:
    - Output: Status message
    - Process Log: Log of execution

    Usage:
    - Connect a Robot component to the Robot input
    - Connect a ConstructTask component to the Robot Task input
    - Toggle Start to begin execution
    - Set Physical to true for actual robot movement, false for simulation

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result of adding the component
    """
    return add_vizor_component("RobotExecution", x, y)
