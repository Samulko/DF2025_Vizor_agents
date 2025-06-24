"""
Pattern creation tools for Grasshopper MCP.

This module provides functions for creating complex component patterns.
"""

from typing import Any, Dict

from grasshopper_mcp.utils.communication import send_to_grasshopper


def create_grasshopper_pattern(pattern_description: str) -> Dict[str, Any]:
    """
    Create a pattern of components based on a high-level description.
    
    This function uses the intent recognition system in Grasshopper to
    create complex component networks from natural language descriptions.
    
    Args:
        pattern_description: High-level description of the pattern
            Examples:
            - "3D voronoi cube"
            - "parametric spiral"
            - "grid of circles"
            - "random point cloud"
    
    Returns:
        Dict[str, Any]: Result containing created component IDs
    """
    params = {
        "description": pattern_description
    }
    
    return send_to_grasshopper("create_pattern", params)


def get_pattern_list(search_query: str = "") -> Dict[str, Any]:
    """
    Get a list of available patterns that can be created.
    
    Args:
        search_query: Optional search query to filter patterns
    
    Returns:
        Dict[str, Any]: List of available patterns with descriptions
    """
    params = {
        "query": search_query
    }
    
    return send_to_grasshopper("get_available_patterns", params)