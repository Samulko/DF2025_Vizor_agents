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
    params = {
        "path": file_path
    }
    
    return send_to_grasshopper("save_document", params)


def load_grasshopper_document(file_path: str) -> Dict[str, Any]:
    """
    Load a Grasshopper document from file.
    
    Args:
        file_path: Path to the document to load
    
    Returns:
        Dict[str, Any]: Result of the load operation
    """
    params = {
        "path": file_path
    }
    
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