"""
Core tools module for Grasshopper MCP.

This module contains core tools for basic Grasshopper operations including:
- Component management
- Document operations
- Connection handling
- Pattern creation
"""

from .components import (
    add_addition,
    add_circle,
    add_construct_point,
    add_extrude,
    add_line,
    add_number_slider,
    add_panel,
    add_python3_script,
    add_xy_plane,
    analyze_script_parameters,
    disable_component,
    edit_python3_script,
    get_all_components_enhanced,
    get_component_info_enhanced,
    get_component_parameters_info,
    get_python3_script,
    get_python3_script_errors,
    recreate_python3_script_with_parameters,
    search_components_by_type,
    set_component_value,
)
from .connections import (
    connect_grasshopper_components,
    get_all_connections,
    smart_connect,
    validate_grasshopper_connection,
)
from .document import (
    clear_grasshopper_document,
    get_components_in_group,
    get_geometry_agent_components,
    get_design_agent_components,
    get_grasshopper_document_info,
    load_grasshopper_document,
    save_grasshopper_document,
)
from .patterns import create_grasshopper_pattern, get_pattern_list

__all__ = [
    # Component tools
    "add_number_slider",
    "add_panel",
    "add_addition",
    "add_circle",
    "add_xy_plane",
    "add_construct_point",
    "add_line",
    "add_extrude",
    "add_python3_script",
    "get_python3_script",
    "edit_python3_script",
    "get_python3_script_errors",
    "set_component_value",
    "get_component_info_enhanced",
    "get_all_components_enhanced",
    "search_components_by_type",
    "get_component_parameters_info",
    "analyze_script_parameters",
    "recreate_python3_script_with_parameters",
    "disable_component",
    # Document tools
    "clear_grasshopper_document",
    "get_components_in_group",
    "get_geometry_agent_components",
    "get_design_agent_components",
    "save_grasshopper_document",
    "load_grasshopper_document",
    "get_grasshopper_document_info",
    # Connection tools
    "connect_grasshopper_components",
    "get_all_connections",
    "validate_grasshopper_connection",
    "smart_connect",
    # Pattern tools
    "create_grasshopper_pattern",
    "get_pattern_list",
]
