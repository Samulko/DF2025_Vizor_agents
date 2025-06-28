"""
Connection management tools for Grasshopper MCP.

This module provides functions for managing connections between components.
"""

from typing import Any, Dict, Optional

from grasshopper_mcp.utils.communication import send_to_grasshopper


def connect_grasshopper_components(
    source_id: str,
    target_id: str,
    source_param: Optional[str] = None,
    target_param: Optional[str] = None,
    source_param_index: Optional[int] = None,
    target_param_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Connect two components in Grasshopper.

    This function handles the connection between component outputs and inputs.

    Args:
        source_id: ID of the source component (output)
        target_id: ID of the target component (input)
        source_param: Name of the source parameter (optional)
        target_param: Name of the target parameter (optional)
        source_param_index: Index of the source parameter (optional)
        target_param_index: Index of the target parameter (optional)

    Returns:
        Dict[str, Any]: Result of the connection operation
    """
    params = {"sourceId": source_id, "targetId": target_id}

    if source_param is not None:
        params["sourceParam"] = source_param
    elif source_param_index is not None:
        params["sourceParamIndex"] = source_param_index

    if target_param is not None:
        params["targetParam"] = target_param
    elif target_param_index is not None:
        params["targetParamIndex"] = target_param_index

    return send_to_grasshopper("connect_components", params)


def get_all_connections() -> Dict[str, Any]:
    """
    Get all connections in the current Grasshopper document.

    Returns:
        Dict[str, Any]: List of all connections with their details
    """
    return send_to_grasshopper("get_connections", {})


def validate_grasshopper_connection(
    source_id: str,
    target_id: str,
    source_param: Optional[str] = None,
    target_param: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate if a connection between two components is possible.

    Args:
        source_id: ID of the source component
        target_id: ID of the target component
        source_param: Name of the source parameter (optional)
        target_param: Name of the target parameter (optional)

    Returns:
        Dict[str, Any]: Validation result with any potential issues
    """
    params = {"sourceId": source_id, "targetId": target_id}

    if source_param is not None:
        params["sourceParam"] = source_param

    if target_param is not None:
        params["targetParam"] = target_param

    return send_to_grasshopper("validate_connection", params)


def smart_connect(source_id: str, target_id: str) -> Dict[str, Any]:
    """
    Intelligently connect two components by analyzing their types.

    This function attempts to determine the correct parameters to connect
    based on the component types and existing connections.

    Args:
        source_id: ID of the source component
        target_id: ID of the target component

    Returns:
        Dict[str, Any]: Result of the connection operation
    """
    # Get information about both components
    source_info = send_to_grasshopper("get_component_info", {"componentId": source_id})
    target_info = send_to_grasshopper("get_component_info", {"componentId": target_id})

    if not (source_info.get("success") and target_info.get("success")):
        return {"success": False, "error": "Failed to get component information"}

    source_type = source_info.get("result", {}).get("type", "")
    target_type = target_info.get("result", {}).get("type", "")

    # Get existing connections to avoid duplicates
    connections = get_all_connections()
    existing_connections = []

    if connections.get("success") and "result" in connections:
        for conn in connections["result"]:
            if conn.get("targetId") == target_id:
                existing_connections.append(conn)

    # Smart parameter selection based on component types
    source_param = None
    target_param = None

    # Handle common connection patterns
    if source_type == "Number Slider":
        source_param = "N"  # Number output

        if target_type == "Circle":
            target_param = "R"  # Radius
        elif target_type in ["Addition", "Subtraction", "Multiplication", "Division"]:
            # Check if A is already connected
            a_connected = any(conn.get("targetParam") == "A" for conn in existing_connections)
            target_param = "B" if a_connected else "A"
        elif target_type == "Construct Point":
            # Determine which coordinate to connect to
            x_connected = any(conn.get("targetParam") == "X" for conn in existing_connections)
            y_connected = any(conn.get("targetParam") == "Y" for conn in existing_connections)

            if not x_connected:
                target_param = "X"
            elif not y_connected:
                target_param = "Y"
            else:
                target_param = "Z"

    elif source_type == "XY Plane" and target_type == "Circle":
        source_param = "P"  # Plane output
        target_param = "P"  # Plane input

    elif source_type == "Circle" and target_type == "Extrude":
        source_param = "C"  # Circle output
        target_param = "B"  # Base input

    # Perform the connection
    return connect_grasshopper_components(
        source_id=source_id,
        target_id=target_id,
        source_param=source_param,
        target_param=target_param,
    )
