"""
Document management tools for Grasshopper MCP.

This module provides functions for managing Grasshopper documents.
"""

from typing import Any, Dict

from grasshopper_mcp.utils.communication import send_to_grasshopper


def clear_grasshopper_document() -> Dict[str, Any]:
    """
    Clear the current Grasshopper document.

    This removes all components except the MCP component itself.

    Returns:
        Dict[str, Any]: Result of the clear operation
    """
    return send_to_grasshopper("clear_document", {})


def save_grasshopper_document(file_path: str) -> Dict[str, Any]:
    """
    Save the current Grasshopper document.

    Args:
        file_path: Path where the document should be saved

    Returns:
        Dict[str, Any]: Result of the save operation
    """
    params = {"path": file_path}

    return send_to_grasshopper("save_document", params)


def load_grasshopper_document(file_path: str) -> Dict[str, Any]:
    """
    Load a Grasshopper document from file.

    Args:
        file_path: Path to the document to load

    Returns:
        Dict[str, Any]: Result of the load operation
    """
    params = {"path": file_path}

    return send_to_grasshopper("load_document", params)


def get_grasshopper_document_info() -> Dict[str, Any]:
    """
    Get information about the current Grasshopper document.

    Returns:
        Dict[str, Any]: Document information including:
            - Document name
            - Component count
            - File path (if saved)
            - Modified status
    """
    return send_to_grasshopper("get_document_info", {})


def get_components_in_group(group_name: str) -> Dict[str, Any]:
    """
    Get all component UUIDs from a group with a specific name.

    This function finds all groups matching the specified name and returns
    the UUIDs and details of all components contained within those groups.

    Args:
        group_name: Name of the group to search for (case-insensitive)

    Returns:
        Dict[str, Any]: Result containing:
            - success: Boolean indicating if operation succeeded
            - groupName: The searched group name
            - found: Whether the group was found
            - componentCount: Number of components in the group
            - components: List of component details (id, type, name)
    """
    params = {"groupName": group_name}
    return send_to_grasshopper("get_components_in_group", params)


def get_geometry_agent_components() -> Dict[str, Any]:
    """
    Get all component UUIDs from the geometry_agent group.

    This is a specialized function that automatically retrieves components
    from the "geometry_agent" group without requiring the group name to be specified.
    This is intended for use by the geometry agent to discover its assigned components.

    Returns:
        Dict[str, Any]: Result containing:
            - success: Boolean indicating if operation succeeded
            - groupName: Always "geometry_agent"
            - found: Whether the geometry_agent group was found
            - componentCount: Number of components in the group
            - components: List of component details (id, type, name)
    """
    return get_components_in_group("geometry_agent")

def get_design_agent_components() -> Dict[str, Any]:
    """
    Get all component UUIDs from the design_agent group.

    This is a specialized function that automatically retrieves components
    from the "design_agent" group without requiring the group name to be specified.
    This is intended for use by the geometry agent to discover its assigned components.

    Returns:
        Dict[str, Any]: Result containing:
            - success: Boolean indicating if operation succeeded
            - groupName: Always "design_agent"
            - found: Whether the design_agent group was found
            - componentCount: Number of components in the group
            - components: List of component details (id, type, name)
    """
    return get_components_in_group("design_agent")