import sys
import traceback

# Add the project root to the Python path when running as a script
if __name__ == "__main__":
    import pathlib

    # Get the absolute path of the current file
    current_file = pathlib.Path(__file__).resolve()
    # Get the correct project root for our setup
    # File is at: vizor_agents/reference/grasshopper_mcp/bridge.py
    # Project root should be: vizor_agents/reference
    project_root = current_file.parent.parent  # This gets us to 'reference'
    # Add the project root to the Python path
    sys.path.insert(0, str(project_root))

# Import MCP server
# Import utility functions
from grasshopper_mcp.utils.communication import send_to_grasshopper
from mcp.server.fastmcp import FastMCP

# Create MCP server
server = FastMCP("Grasshopper Bridge")

# 註冊 MCP 工具 - TEMPORARILY DISABLED
# @server.tool("add_component")
# def add_component(component_type: str, x: float, y: float):
# """
# Add a component to the Grasshopper canvas

# Args:
#     component_type: Component type (point, curve, circle, line, panel, slider)
#     x: X coordinate on the canvas
#     y: Y coordinate on the canvas

# Returns:
#     Result of adding the component
# """
# pass

# Document operations are now provided by core.document module

# @server.tool("connect_components") - TEMPORARILY DISABLED
# def connect_components(source_id: str, target_id: str, source_param: str = None, target_param: str = None, source_param_index: int = None, target_param_index: int = None):
#     """
#     Connect two components in the Grasshopper canvas
#
#     Args:
#         source_id: ID of the source component (output)
#         target_id: ID of the target component (input)
#         source_param: Name of the source parameter (optional)
#         target_param: Name of the target parameter (optional)
#         source_param_index: Index of the source parameter (optional, used if source_param is not provided)
#         target_param_index: Index of the target parameter (optional, used if target_param is not provided)
#
#     Returns:
#         Result of connecting the components
#     """
#     pass

# Pattern operations are now provided by core.patterns module

# @server.tool("get_component_info") - TEMPORARILY DISABLED
# def get_component_info(component_id: str):
#     """
#     Get detailed information about a specific component
#
#     Args:
#         component_id: ID of the component to get information about
#
#     Returns:
#         Detailed information about the component, including inputs, outputs, and current values
#     """
#     pass

# @server.tool("get_all_components") - TEMPORARILY DISABLED
# def get_all_components():
#     """
#     Get a list of all components in the current document
#
#     Returns:
#         List of all components in the document with their IDs, types, and positions
#     """
#     pass

# Connection query is now provided by core.connections module as get_all_connections

# @server.tool("search_components") - TEMPORARILY DISABLED
# def search_components(query: str):
#     """
#     Search for components by name or category
#
#     Args:
#         query: Search query
#
#     Returns:
#         List of components matching the search query
#     """
#     pass

# @server.tool("get_component_parameters") - TEMPORARILY DISABLED
# def get_component_parameters(component_type: str):
#     """
#     Get a list of parameters for a specific component type
#
#     Args:
#         component_type: Type of component to get parameters for
#
#     Returns:
#         List of input and output parameters for the component type
#     """
#     pass

# Connection validation is now provided by core.connections module as validate_grasshopper_connection


# 註冊 MCP 資源
@server.resource("grasshopper://status")
def get_grasshopper_status():
    """Get Grasshopper status"""
    try:
        # 獲取文檔信息
        doc_info = send_to_grasshopper("get_document_info")

        # 獲取所有組件（使用增強版的 get_all_components）
        # components_result = get_all_components()  # Temporarily disabled
        # components = components_result.get("result", []) if components_result else []
        components = []  # Placeholder until function is re-enabled

        # 獲取所有連接 (temporarily disabled until C# backend is updated)
        connections = {"result": []}

        # 添加常用組件的提示信息
        component_hints = {
            "Number Slider": {
                "description": "Single numeric value slider with adjustable range",
                "common_usage": "Use for single numeric inputs like radius, height, count, etc.",
                "parameters": ["min", "max", "value", "rounding", "type"],
                "NOT_TO_BE_CONFUSED_WITH": "MD Slider (which is for multi-dimensional values)",
            },
            "MD Slider": {
                "description": "Multi-dimensional slider for vector input",
                "common_usage": "Use for vector inputs, NOT for simple numeric values",
                "NOT_TO_BE_CONFUSED_WITH": "Number Slider (which is for single numeric values)",
            },
            "Panel": {
                "description": "Displays text or numeric data",
                "common_usage": "Use for displaying outputs and debugging",
            },
            "Addition": {
                "description": "Adds two or more numbers",
                "common_usage": "Connect two Number Sliders to inputs A and B",
                "parameters": ["A", "B"],
                "connection_tip": "First slider should connect to input A, second to input B",
            },
        }

        # 為每個組件添加當前參數值的摘要
        component_summaries = []
        for component in components:
            summary = {
                "id": component.get("id", ""),
                "type": component.get("type", ""),
                "position": {"x": component.get("x", 0), "y": component.get("y", 0)},
            }

            # 添加組件特定的參數信息
            if "currentSettings" in component:
                summary["settings"] = component["currentSettings"]
            elif component.get("type") == "Number Slider":
                # 嘗試從組件信息中提取滑桿設置
                summary["settings"] = {
                    "min": component.get("min", 0),
                    "max": component.get("max", 10),
                    "value": component.get("value", 5),
                    "rounding": component.get("rounding", 0.1),
                }

            # 添加連接信息摘要
            if "connections" in component:
                conn_summary = []
                for conn in component["connections"]:
                    if conn.get("sourceId") == component.get("id"):
                        conn_summary.append(
                            {
                                "type": "output",
                                "to": conn.get("targetId", ""),
                                "sourceParam": conn.get("sourceParam", ""),
                                "targetParam": conn.get("targetParam", ""),
                            }
                        )
                    else:
                        conn_summary.append(
                            {
                                "type": "input",
                                "from": conn.get("sourceId", ""),
                                "sourceParam": conn.get("sourceParam", ""),
                                "targetParam": conn.get("targetParam", ""),
                            }
                        )

                if conn_summary:
                    summary["connections"] = conn_summary

            component_summaries.append(summary)

        return {
            "status": "Connected to Grasshopper",
            "document": doc_info.get("result", {}),
            "components": component_summaries,
            "connections": connections.get("result", []),
            "component_hints": component_hints,
            "recommendations": [
                "When needing a simple numeric input control, ALWAYS use 'Number Slider', not MD Slider",
                "For vector inputs (like 3D points), use 'MD Slider' or 'Construct Point' with multiple Number Sliders",
                "Use 'Panel' to display outputs and debug values",
                "When connecting multiple sliders to Addition, first slider goes to input A, second to input B",
            ],
            "canvas_summary": f"Current canvas has {len(component_summaries)} components and {len(connections.get('result', []))} connections",
        }
    except Exception as e:
        print(f"Error getting Grasshopper status: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"status": f"Error: {str(e)}", "document": {}, "components": [], "connections": []}


@server.resource("grasshopper://component_guide")
def get_component_guide():
    """Get guide for Grasshopper components and connections"""
    return {
        "title": "Grasshopper Component Guide",
        "description": "Guide for creating and connecting Grasshopper components",
        "components": [
            {
                "name": "Point",
                "category": "Params",
                "description": "Creates a point at specific coordinates",
                "inputs": [
                    {"name": "X", "type": "Number"},
                    {"name": "Y", "type": "Number"},
                    {"name": "Z", "type": "Number"},
                ],
                "outputs": [{"name": "Pt", "type": "Point"}],
            },
            {
                "name": "Circle",
                "category": "Curve",
                "description": "Creates a circle",
                "inputs": [
                    {"name": "Plane", "type": "Plane", "description": "Base plane for the circle"},
                    {"name": "Radius", "type": "Number", "description": "Circle radius"},
                ],
                "outputs": [{"name": "C", "type": "Circle"}],
            },
            {
                "name": "XY Plane",
                "category": "Vector",
                "description": "Creates an XY plane at the world origin or at a specified point",
                "inputs": [
                    {
                        "name": "Origin",
                        "type": "Point",
                        "description": "Origin point",
                        "optional": True,
                    }
                ],
                "outputs": [{"name": "Plane", "type": "Plane", "description": "XY plane"}],
            },
            {
                "name": "Addition",
                "fullName": "Addition",
                "description": "Adds two or more numbers",
                "inputs": [
                    {"name": "A", "type": "Number", "description": "First input value"},
                    {"name": "B", "type": "Number", "description": "Second input value"},
                ],
                "outputs": [{"name": "Result", "type": "Number", "description": "Sum of inputs"}],
                "usage_examples": [
                    "Connect two Number Sliders to inputs A and B to add their values",
                    "Connect multiple values to add them all together",
                ],
                "common_issues": [
                    "When connecting multiple sliders, ensure they connect to different inputs (A and B)",
                    "The first slider should connect to input A, the second to input B",
                ],
            },
            {
                "name": "Number Slider",
                "fullName": "Number Slider",
                "description": "Creates a slider for numeric input with adjustable range and precision",
                "inputs": [],
                "outputs": [{"name": "N", "type": "Number", "description": "Number output"}],
                "settings": {
                    "min": {"description": "Minimum value of the slider", "default": 0},
                    "max": {"description": "Maximum value of the slider", "default": 10},
                    "value": {"description": "Current value of the slider", "default": 5},
                    "rounding": {
                        "description": "Rounding precision (0.01, 0.1, 1, etc.)",
                        "default": 0.1,
                    },
                    "type": {
                        "description": "Slider type (integer, floating point)",
                        "default": "float",
                    },
                    "name": {"description": "Custom name for the slider", "default": ""},
                },
                "usage_examples": [
                    "Create a Number Slider with min=0, max=100, value=50",
                    "Create a Number Slider for radius with min=0.1, max=10, value=2.5, rounding=0.1",
                ],
                "common_issues": [
                    "Confusing with other slider types",
                    "Not setting appropriate min/max values for the intended use",
                ],
                "disambiguation": {
                    "similar_components": [
                        {
                            "name": "MD Slider",
                            "description": "Multi-dimensional slider for vector input, NOT for simple numeric values",
                            "how_to_distinguish": "Use Number Slider for single numeric values; use MD Slider only when you need multi-dimensional control",
                        },
                        {
                            "name": "Graph Mapper",
                            "description": "Maps values through a graph function, NOT a simple slider",
                            "how_to_distinguish": "Use Number Slider for direct numeric input; use Graph Mapper only for function-based mapping",
                        },
                    ],
                    "correct_usage": "When needing a simple numeric input control, ALWAYS use 'Number Slider', not MD Slider or other variants",
                },
            },
            {
                "name": "Panel",
                "fullName": "Panel",
                "description": "Displays text or numeric data",
                "inputs": [{"name": "Input", "type": "Any"}],
                "outputs": [],
            },
            {
                "name": "Math",
                "fullName": "Mathematics",
                "description": "Performs mathematical operations",
                "inputs": [{"name": "A", "type": "Number"}, {"name": "B", "type": "Number"}],
                "outputs": [{"name": "Result", "type": "Number"}],
                "operations": [
                    "Addition",
                    "Subtraction",
                    "Multiplication",
                    "Division",
                    "Power",
                    "Modulo",
                ],
            },
            {
                "name": "Construct Point",
                "fullName": "Construct Point",
                "description": "Constructs a point from X, Y, Z coordinates",
                "inputs": [
                    {"name": "X", "type": "Number"},
                    {"name": "Y", "type": "Number"},
                    {"name": "Z", "type": "Number"},
                ],
                "outputs": [{"name": "Pt", "type": "Point"}],
            },
            {
                "name": "Line",
                "fullName": "Line",
                "description": "Creates a line between two points",
                "inputs": [{"name": "Start", "type": "Point"}, {"name": "End", "type": "Point"}],
                "outputs": [{"name": "L", "type": "Line"}],
            },
            {
                "name": "Extrude",
                "fullName": "Extrude",
                "description": "Extrudes a curve to create a surface or a solid",
                "inputs": [
                    {"name": "Base", "type": "Curve"},
                    {"name": "Direction", "type": "Vector"},
                    {"name": "Height", "type": "Number"},
                ],
                "outputs": [{"name": "Brep", "type": "Brep"}],
            },
        ],
        "connectionRules": [
            {
                "from": "Number",
                "to": "Circle.Radius",
                "description": "Connect a number to the radius input of a circle",
            },
            {
                "from": "Point",
                "to": "Circle.Plane",
                "description": "Connect a point to the plane input of a circle (not recommended, use XY Plane instead)",
            },
            {
                "from": "XY Plane",
                "to": "Circle.Plane",
                "description": "Connect an XY Plane to the plane input of a circle (recommended)",
            },
            {
                "from": "Number",
                "to": "Math.A",
                "description": "Connect a number to the first input of a Math component",
            },
            {
                "from": "Number",
                "to": "Math.B",
                "description": "Connect a number to the second input of a Math component",
            },
            {
                "from": "Number",
                "to": "Construct Point.X",
                "description": "Connect a number to the X input of a Construct Point component",
            },
            {
                "from": "Number",
                "to": "Construct Point.Y",
                "description": "Connect a number to the Y input of a Construct Point component",
            },
            {
                "from": "Number",
                "to": "Construct Point.Z",
                "description": "Connect a number to the Z input of a Construct Point component",
            },
            {
                "from": "Point",
                "to": "Line.Start",
                "description": "Connect a point to the start input of a Line component",
            },
            {
                "from": "Point",
                "to": "Line.End",
                "description": "Connect a point to the end input of a Line component",
            },
            {
                "from": "Circle",
                "to": "Extrude.Base",
                "description": "Connect a circle to the base input of an Extrude component",
            },
            {
                "from": "Number",
                "to": "Extrude.Height",
                "description": "Connect a number to the height input of an Extrude component",
            },
        ],
        "commonIssues": [
            "Using Point component instead of XY Plane for inputs that require planes",
            "Not specifying parameter names when connecting components",
            "Using incorrect component names (e.g., 'addition' instead of 'Math' with Addition operation)",
            "Trying to connect incompatible data types",
            "Not providing all required inputs for a component",
            "Using incorrect parameter names (e.g., 'A' and 'B' for Math component instead of the actual parameter names)",
            "Not checking if a connection was successful before proceeding",
        ],
        "tips": [
            "Always use XY Plane component for plane inputs",
            "Specify parameter names when connecting components",
            "For Circle components, make sure to use the correct inputs (Plane and Radius)",
            "Test simple connections before creating complex geometry",
            "Avoid using components that require selection from Rhino",
            "Use get_component_info to check the actual parameter names of a component",
            "Use get_connections to verify if connections were established correctly",
            "Use search_components to find the correct component name before adding it",
            "Use validate_connection to check if a connection is possible before attempting it",
        ],
    }


# Import Vizor components - TEMPORARILY DISABLED
# from grasshopper_mcp.tools.vizor.components import (
#     add_vizor_component,
#     vizor_tracked_object,
#     vizor_ar_worker,
#     vizor_robot,
#     vizor_ws_connection,
#     vizor_construct_content,
#     vizor_make_mesh,
#     vizor_device_tracker,
#     vizor_make_text,
#     vizor_make_trajectory,
#     vizor_scene_model,
#     vizor_construct_task,
#     vizor_task_controller,
#     vizor_robot_execution
# )

# Register Vizor tools with the server - TEMPORARILY DISABLED
# server.tool("add_vizor_component")(add_vizor_component)
# server.tool("vizor_tracked_object")(vizor_tracked_object)
# server.tool("vizor_ar_worker")(vizor_ar_worker)
# server.tool("vizor_robot")(vizor_robot)
# server.tool("vizor_ws_connection")(vizor_ws_connection)
# server.tool("vizor_construct_content")(vizor_construct_content)
# server.tool("vizor_make_mesh")(vizor_make_mesh)
# server.tool("vizor_device_tracker")(vizor_device_tracker)
# server.tool("vizor_make_text")(vizor_make_text)
# server.tool("vizor_make_trajectory")(vizor_make_trajectory)
# server.tool("vizor_scene_model")(vizor_scene_model)
# server.tool("vizor_construct_task")(vizor_construct_task)
# server.tool("vizor_task_controller")(vizor_task_controller)
# server.tool("vizor_robot_execution")(vizor_robot_execution)

# Import Core tools - ONLY KEEP REQUIRED TOOLS
from grasshopper_mcp.tools.core import (
    edit_python3_script,
    get_all_components_enhanced,
    get_components_in_group,
    get_geometry_agent_components,
    # TEMPORARILY DISABLED
    # add_number_slider,
    # add_panel,
    # add_addition,
    # add_circle,
    # add_xy_plane,
    # add_construct_point,
    # add_line,
    # add_extrude,
    # set_component_value,
    # search_components_by_type,
    # get_component_parameters_info,
    # analyze_script_parameters,
    # recreate_python3_script_with_parameters,
    # Document tools - DISABLED
    # clear_grasshopper_document,
    # save_grasshopper_document,
    # load_grasshopper_document,
    # get_grasshopper_document_info,
    # Connection tools - DISABLED
    # connect_grasshopper_components,
    # get_all_connections,
    # validate_grasshopper_connection,
    # smart_connect,
    # Pattern tools - DISABLED
    # create_grasshopper_pattern,
    # get_pattern_list
    get_component_info_enhanced,
    # Component tools - KEEP ONLY THESE 6
    # add_python3_script,  # DISABLED
    get_python3_script,
    get_python3_script_errors,
)

# Register Core tools with the server - ONLY KEEP 6 REQUIRED TOOLS
# Component tools - KEEP ONLY THESE 6
# server.tool("add_python3_script")(add_python3_script)  # DISABLED
server.tool("get_python3_script")(get_python3_script)
server.tool("edit_python3_script")(edit_python3_script)
server.tool("get_python3_script_errors")(get_python3_script_errors)
server.tool("get_component_info_enhanced")(get_component_info_enhanced)
# server.tool("get_all_components_enhanced")(get_all_components_enhanced)  # Replaced by get_geometry_agent_components for precision
# server.tool("get_components_in_group")(get_components_in_group)  # Commented out - use get_geometry_agent_components instead
server.tool("get_geometry_agent_components")(get_geometry_agent_components)

# TEMPORARILY DISABLED TOOLS
# server.tool("add_number_slider")(add_number_slider)
# server.tool("add_panel")(add_panel)
# server.tool("add_addition")(add_addition)
# server.tool("add_circle")(add_circle)
# server.tool("add_xy_plane")(add_xy_plane)
# server.tool("add_construct_point")(add_construct_point)
# server.tool("add_line")(add_line)
# server.tool("add_extrude")(add_extrude)
# server.tool("set_component_value")(set_component_value)
# server.tool("search_components_by_type")(search_components_by_type)
# server.tool("get_component_parameters_info")(get_component_parameters_info)
# server.tool("analyze_script_parameters")(analyze_script_parameters)
# server.tool("recreate_python3_script_with_parameters")(recreate_python3_script_with_parameters)

# Document tools - TEMPORARILY DISABLED
# server.tool("clear_grasshopper_document")(clear_grasshopper_document)
# server.tool("save_grasshopper_document")(save_grasshopper_document)
# server.tool("load_grasshopper_document")(load_grasshopper_document)
# server.tool("get_grasshopper_document_info")(get_grasshopper_document_info)

# Connection tools - TEMPORARILY DISABLED
# server.tool("connect_grasshopper_components")(connect_grasshopper_components)
# server.tool("get_all_connections")(get_all_connections)
# server.tool("validate_grasshopper_connection")(validate_grasshopper_connection)
# server.tool("smart_connect")(smart_connect)

# Pattern tools - TEMPORARILY DISABLED
# server.tool("create_grasshopper_pattern")(create_grasshopper_pattern)
# server.tool("get_pattern_list")(get_pattern_list)


@server.resource("grasshopper://component_library")
def get_component_library():
    """Get a comprehensive library of Grasshopper components"""
    # 這個資源提供了一個更全面的組件庫，包括常用組件的詳細信息
    return {
        "categories": [
            {
                "name": "Params",
                "components": [
                    {
                        "name": "Point",
                        "fullName": "Point Parameter",
                        "description": "Creates a point parameter",
                        "inputs": [
                            {"name": "X", "type": "Number", "description": "X coordinate"},
                            {"name": "Y", "type": "Number", "description": "Y coordinate"},
                            {"name": "Z", "type": "Number", "description": "Z coordinate"},
                        ],
                        "outputs": [{"name": "Pt", "type": "Point", "description": "Point output"}],
                    },
                    {
                        "name": "Number Slider",
                        "fullName": "Number Slider",
                        "description": "Creates a slider for numeric input with adjustable range and precision",
                        "inputs": [],
                        "outputs": [
                            {"name": "N", "type": "Number", "description": "Number output"}
                        ],
                        "settings": {
                            "min": {"description": "Minimum value of the slider", "default": 0},
                            "max": {"description": "Maximum value of the slider", "default": 10},
                            "value": {"description": "Current value of the slider", "default": 5},
                            "rounding": {
                                "description": "Rounding precision (0.01, 0.1, 1, etc.)",
                                "default": 0.1,
                            },
                            "type": {
                                "description": "Slider type (integer, floating point)",
                                "default": "float",
                            },
                            "name": {"description": "Custom name for the slider", "default": ""},
                        },
                        "usage_examples": [
                            "Create a Number Slider with min=0, max=100, value=50",
                            "Create a Number Slider for radius with min=0.1, max=10, value=2.5, rounding=0.1",
                        ],
                        "common_issues": [
                            "Confusing with other slider types",
                            "Not setting appropriate min/max values for the intended use",
                        ],
                        "disambiguation": {
                            "similar_components": [
                                {
                                    "name": "MD Slider",
                                    "description": "Multi-dimensional slider for vector input, NOT for simple numeric values",
                                    "how_to_distinguish": "Use Number Slider for single numeric values; use MD Slider only when you need multi-dimensional control",
                                },
                                {
                                    "name": "Graph Mapper",
                                    "description": "Maps values through a graph function, NOT a simple slider",
                                    "how_to_distinguish": "Use Number Slider for direct numeric input; use Graph Mapper only for function-based mapping",
                                },
                            ],
                            "correct_usage": "When needing a simple numeric input control, ALWAYS use 'Number Slider', not MD Slider or other variants",
                        },
                    },
                    {
                        "name": "Panel",
                        "fullName": "Panel",
                        "description": "Displays text or numeric data",
                        "inputs": [
                            {"name": "Input", "type": "Any", "description": "Any input data"}
                        ],
                        "outputs": [],
                    },
                ],
            },
            {
                "name": "Maths",
                "components": [
                    {
                        "name": "Math",
                        "fullName": "Mathematics",
                        "description": "Performs mathematical operations",
                        "inputs": [
                            {"name": "A", "type": "Number", "description": "First number"},
                            {"name": "B", "type": "Number", "description": "Second number"},
                        ],
                        "outputs": [
                            {
                                "name": "Result",
                                "type": "Number",
                                "description": "Result of the operation",
                            }
                        ],
                        "operations": [
                            "Addition",
                            "Subtraction",
                            "Multiplication",
                            "Division",
                            "Power",
                            "Modulo",
                        ],
                    }
                ],
            },
            {
                "name": "Vector",
                "components": [
                    {
                        "name": "XY Plane",
                        "fullName": "XY Plane",
                        "description": "Creates an XY plane at the world origin or at a specified point",
                        "inputs": [
                            {
                                "name": "Origin",
                                "type": "Point",
                                "description": "Origin point",
                                "optional": True,
                            }
                        ],
                        "outputs": [{"name": "Plane", "type": "Plane", "description": "XY plane"}],
                    },
                    {
                        "name": "Construct Point",
                        "fullName": "Construct Point",
                        "description": "Constructs a point from X, Y, Z coordinates",
                        "inputs": [
                            {"name": "X", "type": "Number", "description": "X coordinate"},
                            {"name": "Y", "type": "Number", "description": "Y coordinate"},
                            {"name": "Z", "type": "Number", "description": "Z coordinate"},
                        ],
                        "outputs": [
                            {"name": "Pt", "type": "Point", "description": "Constructed point"}
                        ],
                    },
                ],
            },
            {
                "name": "Curve",
                "components": [
                    {
                        "name": "Circle",
                        "fullName": "Circle",
                        "description": "Creates a circle",
                        "inputs": [
                            {
                                "name": "Plane",
                                "type": "Plane",
                                "description": "Base plane for the circle",
                            },
                            {"name": "Radius", "type": "Number", "description": "Circle radius"},
                        ],
                        "outputs": [
                            {"name": "C", "type": "Circle", "description": "Circle output"}
                        ],
                    },
                    {
                        "name": "Line",
                        "fullName": "Line",
                        "description": "Creates a line between two points",
                        "inputs": [
                            {"name": "Start", "type": "Point", "description": "Start point"},
                            {"name": "End", "type": "Point", "description": "End point"},
                        ],
                        "outputs": [{"name": "L", "type": "Line", "description": "Line output"}],
                    },
                ],
            },
            {
                "name": "Surface",
                "components": [
                    {
                        "name": "Extrude",
                        "fullName": "Extrude",
                        "description": "Extrudes a curve to create a surface or a solid",
                        "inputs": [
                            {
                                "name": "Base",
                                "type": "Curve",
                                "description": "Base curve to extrude",
                            },
                            {
                                "name": "Direction",
                                "type": "Vector",
                                "description": "Direction of extrusion",
                                "optional": True,
                            },
                            {
                                "name": "Height",
                                "type": "Number",
                                "description": "Height of extrusion",
                            },
                        ],
                        "outputs": [
                            {"name": "Brep", "type": "Brep", "description": "Extruded brep"}
                        ],
                    }
                ],
            },
        ],
        "dataTypes": [
            {
                "name": "Number",
                "description": "A numeric value",
                "compatibleWith": ["Number", "Integer", "Double"],
            },
            {
                "name": "Point",
                "description": "A 3D point in space",
                "compatibleWith": ["Point3d", "Point"],
            },
            {
                "name": "Vector",
                "description": "A 3D vector",
                "compatibleWith": ["Vector3d", "Vector"],
            },
            {"name": "Plane", "description": "A plane in 3D space", "compatibleWith": ["Plane"]},
            {
                "name": "Circle",
                "description": "A circle curve",
                "compatibleWith": ["Circle", "Curve"],
            },
            {"name": "Line", "description": "A line segment", "compatibleWith": ["Line", "Curve"]},
            {
                "name": "Curve",
                "description": "A curve object",
                "compatibleWith": ["Curve", "Circle", "Line", "Arc", "Polyline"],
            },
            {
                "name": "Brep",
                "description": "A boundary representation object",
                "compatibleWith": ["Brep", "Surface", "Solid"],
            },
        ],
    }


def main():
    """Main entry point for the Grasshopper MCP Bridge Server"""
    try:
        # 啟動 MCP 服務器
        print("Starting Grasshopper MCP Bridge Server...", file=sys.stderr)
        print("Please add this MCP server to Claude Desktop", file=sys.stderr)
        server.run(transport="stdio")
    except Exception as e:
        print(f"Error starting MCP server: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
