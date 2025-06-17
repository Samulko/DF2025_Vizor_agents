"""
Core component tools for Grasshopper MCP.

This module provides functions for working with basic Grasshopper components.
"""

from typing import Any, Dict, List, Optional, Tuple

from grasshopper_mcp.utils.communication import send_to_grasshopper


def add_number_slider(
    x: float = 100.0,
    y: float = 100.0,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    current_value: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Add a Number Slider component to the Grasshopper canvas.

    The slider can be configured with min/max/current values using the initCode format.

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)
        min_value: Minimum value of the slider (optional)
        max_value: Maximum value of the slider (optional)
        current_value: Current value of the slider (optional)

    Returns:
        Dict[str, Any]: Result containing component ID and details
    """
    import sys

    # Debug logging
    print(
        f"add_number_slider called with: min={min_value}, max={max_value}, current={current_value}",
        file=sys.stderr,
    )

    # First add the component
    params = {"type": "Number Slider", "x": x, "y": y}

    # If we have min/max values, create initCode
    # The GH_NumberSlider.SetInitCode expects format: "min < current < max"
    if min_value is not None and max_value is not None:
        # Determine current value
        if current_value is not None:
            curr = current_value
        else:
            curr = (min_value + max_value) / 2.0

        # Create initCode string
        params["initCode"] = f"{min_value} < {curr} < {max_value}"
        print(f"Generated initCode: {params['initCode']}", file=sys.stderr)
    elif current_value is not None:
        # If only current value is provided, use default range 0 to 1
        params["initCode"] = f"0 < {current_value} < 1"
        print(f"Generated initCode: {params['initCode']}", file=sys.stderr)

    print(f"Sending params to Grasshopper: {params}", file=sys.stderr)
    result = send_to_grasshopper("add_component", params)

    return result


def add_panel(x: float = 200.0, y: float = 100.0) -> Dict[str, Any]:
    """
    Add a Panel component to the Grasshopper canvas.

    Panels are used to display text or numeric data in Grasshopper.

    Args:
        x: X coordinate on the canvas (default: 200.0)
        y: Y coordinate on the canvas (default: 100.0)

    Returns:
        Dict[str, Any]: Result containing component ID
    """
    params = {"type": "Panel", "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


def add_addition(x: float = 150.0, y: float = 150.0) -> Dict[str, Any]:
    """
    Add an Addition component to the Grasshopper canvas.

    Addition components add two or more numeric inputs together.

    Args:
        x: X coordinate on the canvas (default: 150.0)
        y: Y coordinate on the canvas (default: 150.0)

    Returns:
        Dict[str, Any]: Result containing component ID
    """
    params = {"type": "Addition", "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


def add_circle(x: float = 250.0, y: float = 200.0) -> Dict[str, Any]:
    """
    Add a Circle component to the Grasshopper canvas.

    Circle components create circular curves in Grasshopper.

    Args:
        x: X coordinate on the canvas (default: 250.0)
        y: Y coordinate on the canvas (default: 200.0)

    Returns:
        Dict[str, Any]: Result containing component ID
    """
    params = {"type": "Circle", "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


def add_xy_plane(x: float = 150.0, y: float = 200.0) -> Dict[str, Any]:
    """
    Add an XY Plane component to the Grasshopper canvas.

    XY Plane components create a plane at the world origin or specified point.

    Args:
        x: X coordinate on the canvas (default: 150.0)
        y: Y coordinate on the canvas (default: 200.0)

    Returns:
        Dict[str, Any]: Result containing component ID
    """
    params = {"type": "XY Plane", "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


def add_construct_point(x: float = 100.0, y: float = 250.0) -> Dict[str, Any]:
    """
    Add a Construct Point component to the Grasshopper canvas.

    Construct Point components create 3D points from X, Y, Z coordinates.

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 250.0)

    Returns:
        Dict[str, Any]: Result containing component ID
    """
    params = {"type": "Construct Point", "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


def add_line(x: float = 200.0, y: float = 250.0) -> Dict[str, Any]:
    """
    Add a Line component to the Grasshopper canvas.

    Line components create line segments between two points.

    Args:
        x: X coordinate on the canvas (default: 200.0)
        y: Y coordinate on the canvas (default: 250.0)

    Returns:
        Dict[str, Any]: Result containing component ID
    """
    params = {"type": "Line", "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


def add_extrude(x: float = 350.0, y: float = 200.0) -> Dict[str, Any]:
    """
    Add an Extrude component to the Grasshopper canvas.

    Extrude components create surfaces or solids by extruding curves.

    Args:
        x: X coordinate on the canvas (default: 350.0)
        y: Y coordinate on the canvas (default: 200.0)

    Returns:
        Dict[str, Any]: Result containing component ID
    """
    params = {"type": "Extrude", "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


def set_component_value(
    component_id: str, value: Any, param_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set the value of a component parameter.

    Args:
        component_id: ID of the component to modify
        value: Value to set
        param_name: Name of the parameter to set (optional)

    Returns:
        Dict[str, Any]: Result of the operation
    """
    params = {
        "id": component_id,  # Changed from "componentId" to match C# expectation
        "value": str(value),  # Convert to string as C# expects string
    }

    if param_name:
        params["paramName"] = param_name

    return send_to_grasshopper("set_component_value", params)


def get_component_info_enhanced(component_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific component.

    This is an enhanced version that includes additional metadata.

    Args:
        component_id: ID of the component

    Returns:
        Dict[str, Any]: Detailed component information
    """
    params = {"id": component_id}

    return send_to_grasshopper("get_component_info", params)


def get_all_components_enhanced() -> Dict[str, Any]:
    """
    Get a list of all components in the current document.

    Returns:
        Dict[str, Any]: List of all components with their details
    """
    doc_info = send_to_grasshopper("get_document_info", {})

    if doc_info.get("success") and "result" in doc_info:
        result_data = doc_info["result"]
        if "components" in result_data:
            return {"success": True, "result": result_data["components"]}

    return doc_info


def search_components_by_type(component_type: str) -> Dict[str, Any]:
    """
    Search for components by type in the current document.

    Args:
        component_type: Type of component to search for

    Returns:
        Dict[str, Any]: List of matching components
    """
    result = get_all_components_enhanced()

    if result.get("success") and "result" in result:
        components = result["result"]
        matching = [c for c in components if c.get("type") == component_type]

        return {"success": True, "result": matching, "count": len(matching)}

    return result


def get_component_parameters_info(component_type: str) -> Dict[str, Any]:
    """
    Get parameter information for a specific component type.

    Args:
        component_type: Type of component

    Returns:
        Dict[str, Any]: Parameter information
    """
    params = {"componentType": component_type}

    return send_to_grasshopper("get_component_parameters", params)


def add_python3_script(
    x: float = 100.0,
    y: float = 100.0,
    script: str = "",
    name: str = "Python Script",
    input_parameters: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Add a Python 3 Script component with pre-populated code to the Grasshopper canvas.

    This allows the LLM to generate Python code that will execute in Grasshopper,
    enabling dynamic geometry creation, data processing, and custom operations.

    IMPORTANT:
    - The script parameter must contain the actual Python code as a string. The script must be clearly documented with a clear script description at the top of the script.
    - The output variable 'a' is automatically connected to the component's output.
    - ALWAYS provide a descriptive name that can be used as a clear identifier for that component (e.g., "unit 1", "unit 2",
      "module 1"). This helps with organization and debugging.

    Args:
        x: X coordinate on the canvas (default: 100.0)
        y: Y coordinate on the canvas (default: 100.0)
        script: Python script content to populate in the component. Use 'a' as output variable.
        name: REQUIRED - Descriptive name that clearly indicates the component's purpose
              and context within the current task (e.g., "Bridge Deck Generator", "Stress Analysis")
        input_parameters: List of parameter definitions to add to the component (optional)
            Each parameter should be a dict with:
            - "name": Parameter name
            - "type": Parameter type ("Number", "Integer", "Text", "Boolean")
            - "description": Parameter description

    Returns:
        Dict[str, Any]: Result containing component ID and details

    Examples:
        # Example 1: Bridge engineering - Pier foundation layout
        >>> add_python3_script(
        ...     x=100, y=100,
        ...     name="Bridge Pier Foundation Layout",
        ...     script='''import Rhino.Geometry as rg
        ...
        ... # Create circular foundation footprint for bridge pier
        ... foundation_radius = 5.0  # meters
        ... foundation = rg.Circle(rg.Point3d(0,0,0), foundation_radius)
        ... a = foundation'''
        ... )

        # Example 2: Structural analysis - Support point grid
        >>> add_python3_script(
        ...     x=200, y=100,
        ...     name="Bridge Deck Support Points",
        ...     script='''import Rhino.Geometry as rg
        ...
        ... # Generate support points for bridge deck analysis
        ... support_points = []
        ... for span in range(5):
        ...     for width in range(3):
        ...         pt = rg.Point3d(span * 10, width * 4, 0)  # 10m spans, 4m width
        ...         support_points.append(pt)
        ...
        ... a = support_points'''
        ... )

        # Example 3: Cable-stayed bridge - Cable geometry
        >>> add_python3_script(
        ...     x=300, y=100,
        ...     name="Cable-Stayed Bridge Cable Path",
        ...     script='''import Rhino.Geometry as rg
        ... import math
        ...
        ... # Create cable path from tower to deck
        ... cable_points = []
        ... tower_height = 100  # meters
        ... span_length = 200   # meters
        ... for i in range(50):
        ...     t = i / 49.0
        ...     x = t * span_length
        ...     # Catenary curve approximation for cable sag
        ...     y = tower_height * (1 - t) + 5 * math.sin(math.pi * t)
        ...     cable_points.append(rg.Point3d(x, 0, y))
        ...
        ... cable_curve = rg.Curve.CreateInterpolatedCurve(cable_points, 3)
        ... a = cable_curve'''
        ... )
    """
    params = {
        "type": "Py3",  # Use Py3 which is the proper Python 3 component in Rhino 8
        "x": x,
        "y": y,
        "name": name,  # Pass the name parameter to the C# backend
    }

    if script:
        params["script"] = script
    else:
        # Provide a default template
        params[
            "script"
        ] = """# Python 3 Script in Grasshopper
# Access inputs through variable names matching input parameters
# Return outputs as a tuple or single value

import Rhino.Geometry as rg

# Your code here
result = "Hello from Python 3!"

# Return output
result"""

    return send_to_grasshopper("add_component", params)


def get_python3_script(component_id: str) -> Dict[str, Any]:
    """
    Get the script content from an existing Python 3 Script component.

    This allows the LLM to read and understand the current code in a Python
    script component, enabling code inspection and informed editing.

    Args:
        component_id: ID of the Python 3 Script component to read from

    Returns:
        Dict[str, Any]: Result containing component info and script content

    Examples:
        # Read script from an existing component
        >>> result = get_python3_script("d18eee48-60ef-4b2a-bda4-0be546f1586a")
        >>> if result.get("success"):
        ...     script_content = result["data"]["script"]
        ...     print(f"Current script:\n{script_content}")
    """
    params = {"id": component_id}

    return send_to_grasshopper("get_python_script_content", params)


def edit_python3_script(component_id: str, script: str) -> Dict[str, Any]:
    """
    Edit the script content of an existing Python 3 Script component without creating a new one.

    This allows the LLM to modify existing Python scripts in place, enabling iterative
    development and refinement of code without cluttering the canvas with new components.

    IMPORTANT: This modifies the existing component rather than creating a new one.
    The script parameter must contain the complete new Python code as a string.
    The output variable 'a' is automatically connected to the component's output.

    Args:
        component_id: ID of the existing Python 3 Script component to modify
        script: New Python script content to replace the existing code

    Returns:
        Dict[str, Any]: Result containing success status and component details

    Examples:
        # Example 1: Update an existing spiral to change parameters
        >>> edit_python3_script(
        ...     component_id="d18eee48-60ef-4b2a-bda4-0be546f1586a",
        ...     script='''import Rhino.Geometry as rg
        ... import math
        ...
        ... # Updated spiral parameters
        ... num_boxes = 75  # Increased from 50
        ... spiral_turns = 5  # Increased from 3
        ... radius_growth = 0.3  # Increased from 0.2
        ... box_size = 0.7  # Increased from 0.5
        ... vertical_spacing = 0.15  # Increased from 0.1
        ...
        ... boxes = []
        ...
        ... for i in range(num_boxes):
        ...     t = (i / float(num_boxes)) * spiral_turns * 2 * math.pi
        ...     radius = radius_growth * t
        ...
        ...     x = math.cos(t) * radius
        ...     y = math.sin(t) * radius
        ...     z = i * vertical_spacing
        ...
        ...     center = rg.Point3d(x, y, z)
        ...     interval = rg.Interval(-box_size/2, box_size/2)
        ...     box = rg.Box(rg.Plane(center, rg.Vector3d.ZAxis), interval, interval, interval)
        ...
        ...     boxes.append(box)
        ...
        ... a = boxes'''
        ... )

        # Example 2: Change geometry type from boxes to spheres
        >>> edit_python3_script(
        ...     component_id="d18eee48-60ef-4b2a-bda4-0be546f1586a",
        ...     script='''import Rhino.Geometry as rg
        ... import math
        ...
        ... # Spiral parameters
        ... num_spheres = 50
        ... spiral_turns = 3
        ... radius_growth = 0.2
        ... sphere_radius = 0.3
        ... vertical_spacing = 0.1
        ...
        ... spheres = []
        ...
        ... for i in range(num_spheres):
        ...     t = (i / float(num_spheres)) * spiral_turns * 2 * math.pi
        ...     radius = radius_growth * t
        ...
        ...     x = math.cos(t) * radius
        ...     y = math.sin(t) * radius
        ...     z = i * vertical_spacing
        ...
        ...     center = rg.Point3d(x, y, z)
        ...     sphere = rg.Sphere(center, sphere_radius)
        ...
        ...     spheres.append(sphere)
        ...
        ... a = spheres'''
        ... )

        # Example 3: Add conditional logic to existing code
        >>> edit_python3_script(
        ...     component_id="d18eee48-60ef-4b2a-bda4-0be546f1586a",
        ...     script='''import Rhino.Geometry as rg
        ... import math
        ...
        ... # Spiral parameters
        ... num_boxes = 50
        ... spiral_turns = 3
        ... radius_growth = 0.2
        ... box_size = 0.5
        ... vertical_spacing = 0.1
        ...
        ... boxes = []
        ...
        ... for i in range(num_boxes):
        ...     t = (i / float(num_boxes)) * spiral_turns * 2 * math.pi
        ...     radius = radius_growth * t
        ...
        ...     x = math.cos(t) * radius
        ...     y = math.sin(t) * radius
        ...     z = i * vertical_spacing
        ...
        ...     # Special handling for every 10th box - make it larger
        ...     current_box_size = box_size * 1.5 if i % 10 == 0 else box_size
        ...
        ...     center = rg.Point3d(x, y, z)
        ...     interval = rg.Interval(-current_box_size/2, current_box_size/2)
        ...     box = rg.Box(rg.Plane(center, rg.Vector3d.ZAxis), interval, interval, interval)
        ...
        ...     boxes.append(box)
        ...
        ... a = boxes'''
        ... )
    """
    params = {"id": component_id, "script": script}

    return send_to_grasshopper("set_python_script_content", params)


def get_python3_script_errors(component_id: str) -> Dict[str, Any]:
    """
    Get error and warning messages from an existing Python 3 Script component.

    This allows the LLM to check for syntax errors, runtime exceptions, warnings,
    and other issues in Python script components, enabling debugging and error resolution.

    IMPORTANT: This reads runtime messages that are generated when the component executes.
    If the component hasn't run yet or had no errors, the result may be empty.

    Args:
        component_id: ID of the Python 3 Script component to check for errors

    Returns:
        Dict[str, Any]: Result containing error status, messages, and categorized errors/warnings

    Examples:
        # Example 1: Check for errors in a component
        >>> result = get_python3_script_errors("d18eee48-60ef-4b2a-bda4-0be546f1586a")
        >>> if result.get("success"):
        ...     error_info = result["data"]
        ...     if error_info["hasErrors"]:
        ...         print(f"Component has {len(error_info['errors'])} errors:")
        ...         for error in error_info["errors"]:
        ...             print(f"  - {error}")
        ...     elif error_info["hasWarnings"]:
        ...         print(f"Component has {len(error_info['warnings'])} warnings:")
        ...         for warning in error_info["warnings"]:
        ...             print(f"  - {warning}")
        ...     else:
        ...         print("Component status: OK - no errors or warnings")

        # Example 2: Debug a script with syntax errors
        >>> result = get_python3_script_errors("script-component-id")
        >>> if result.get("success"):
        ...     error_info = result["data"]
        ...     print(f"Status: {error_info['status']}")
        ...     print(f"All messages ({error_info['messageCount']}):")
        ...     for message in error_info["allMessages"]:
        ...         print(f"  {message}")

        # Example 3: Use error checking in an iterative development workflow
        >>> # First, read the current script
        >>> script_result = get_python3_script("component-id")
        >>> # Then check for errors
        >>> error_result = get_python3_script_errors("component-id")
        >>> if error_result.get("success") and error_result["data"]["hasErrors"]:
        ...     print("Found errors in script:")
        ...     for error in error_result["data"]["errors"]:
        ...         print(f"  {error}")
        ...     # Now you can edit the script to fix the errors
        ...     # edit_python3_script("component-id", fixed_script)
    """
    params = {"id": component_id}

    return send_to_grasshopper("get_python_script_errors", params)


def analyze_script_parameters(script: str) -> Dict[str, Any]:
    """
    Analyze a Python script to detect variables that should be component input parameters.

    This function parses Python code to identify variables that are used as inputs
    and suggests parameter definitions for creating parametric components.

    Args:
        script: Python script content to analyze

    Returns:
        Dict[str, Any]: Analysis results containing detected parameters and suggestions

    Examples:
        # Example 1: Analyze a simple script
        >>> script = '''
        ... import Rhino.Geometry as rg
        ...
        ... # Create a circle with variable radius
        ... radius = float(r) if 'r' in globals() else 5.0
        ... circle = rg.Circle(rg.Point3d.Origin, radius)
        ... a = circle
        ... '''
        >>> result = analyze_script_parameters(script)
        >>> print(result["suggested_parameters"])
        [{"name": "r", "type": "Number", "description": "Circle radius"}]

        # Example 2: Analyze complex parametric script
        >>> script = '''
        ... num_points = int(x) if 'x' in globals() else 5
        ... outer_radius = float(y) if 'y' in globals() else 10.0
        ... inner_radius = float(z) if 'z' in globals() else 4.0
        ... sphere_radius = float(radius) if 'radius' in globals() else 0.5
        ... '''
        >>> result = analyze_script_parameters(script)
        >>> # Returns 4 suggested parameters: x, y, z, radius
    """
    import re

    # Initialize results
    detected_vars = set()
    suggested_parameters = []
    analysis_notes = []

    try:
        # Pattern 1: Standard conditional variable assignment
        # Matches: var = type(name) if 'name' in globals() else default
        pattern1 = (
            r"(\w+)\s*=\s*(?:int|float|str|bool)\s*\(\s*(\w+)\s*\)\s*if\s*['\"](\w+)['\"].*?else"
        )
        matches1 = re.findall(pattern1, script, re.MULTILINE)

        for local_var, param_var, globals_check in matches1:
            if param_var == globals_check:  # Consistency check
                detected_vars.add(param_var)
                analysis_notes.append(f"Found standard pattern: {local_var} = {param_var}")

        # Pattern 2: Direct variable usage with globals check
        # Matches: if 'name' in globals() and name is not None
        pattern2 = r"if\s*['\"](\w+)['\"].*?in\s*globals\(\)"
        matches2 = re.findall(pattern2, script)
        for var_name in matches2:
            detected_vars.add(var_name)
            analysis_notes.append(f"Found globals check for: {var_name}")

        # Pattern 3: Try to detect direct variable usage (common single-letter params)
        # Look for standalone variable names that are likely inputs
        common_input_vars = {
            "x",
            "y",
            "z",
            "a",
            "b",
            "c",
            "r",
            "radius",
            "height",
            "width",
            "length",
            "count",
            "size",
            "scale",
            "angle",
            "rotation",
        }

        # Find variable usage in the script
        lines = script.split("\n")
        for line in lines:
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Look for variables being used directly (not being assigned to)
            for var in common_input_vars:
                # Check if variable is used but not in an assignment context
                if re.search(rf"\b{var}\b(?!\s*=)", line) and not re.search(
                    rf"^{var}\s*=", line.strip()
                ):
                    if var not in detected_vars:  # Don't duplicate
                        detected_vars.add(var)
                        analysis_notes.append(f"Found potential input usage: {var}")

        # Create parameter suggestions based on detected variables
        for var_name in sorted(detected_vars):
            param_def = {
                "name": var_name,
                "type": _infer_parameter_type(var_name, script),
                "description": _generate_parameter_description(var_name),
                "suggested_default": _suggest_default_value(var_name),
            }
            suggested_parameters.append(param_def)

        # Additional analysis
        has_rhino_geometry = "Rhino.Geometry" in script or "rg." in script
        has_math_operations = "math." in script or "import math" in script
        output_assignment = "a =" in script

        return {
            "success": True,
            "detected_variables": list(detected_vars),
            "suggested_parameters": suggested_parameters,
            "analysis_notes": analysis_notes,
            "script_info": {
                "has_rhino_geometry": has_rhino_geometry,
                "has_math_operations": has_math_operations,
                "has_output_assignment": output_assignment,
                "line_count": len([line for line in script.split("\n") if line.strip()]),
            },
            "recommendations": _generate_recommendations(suggested_parameters, script),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Script analysis failed: {str(e)}",
            "detected_variables": [],
            "suggested_parameters": [],
            "analysis_notes": [f"Error during analysis: {str(e)}"],
        }


def _infer_parameter_type(var_name: str, script: str) -> str:
    """Infer the likely parameter type based on variable name and usage context."""

    # Check for explicit type conversions in script
    if f"int({var_name})" in script:
        return "Integer"
    elif f"float({var_name})" in script:
        return "Number"
    elif f"str({var_name})" in script:
        return "Text"
    elif f"bool({var_name})" in script:
        return "Boolean"

    # Infer from variable name patterns
    integer_patterns = ["count", "num", "number", "index", "step", "points", "sides", "segments"]
    number_patterns = [
        "radius",
        "size",
        "scale",
        "angle",
        "rotation",
        "height",
        "width",
        "length",
        "distance",
        "offset",
    ]

    var_lower = var_name.lower()

    for pattern in integer_patterns:
        if pattern in var_lower:
            return "Integer"

    for pattern in number_patterns:
        if pattern in var_lower:
            return "Number"

    # Default based on common single-letter conventions
    if var_name in ["x", "y", "z", "r", "a", "b", "c"]:
        return "Number"

    # Default fallback
    return "Number"


def _generate_parameter_description(var_name: str) -> str:
    """Generate a descriptive name for a parameter based on its variable name."""

    descriptions = {
        "x": "X coordinate or first numeric input",
        "y": "Y coordinate or second numeric input",
        "z": "Z coordinate or third numeric input",
        "r": "Radius value",
        "radius": "Radius value",
        "height": "Height dimension",
        "width": "Width dimension",
        "length": "Length dimension",
        "size": "Size value",
        "scale": "Scale factor",
        "angle": "Angle in radians",
        "rotation": "Rotation angle",
        "count": "Number of items",
        "num": "Numeric count",
        "points": "Number of points",
        "segments": "Number of segments",
        "density": "Density or resolution value",
        "offset": "Offset distance",
        "distance": "Distance value",
    }

    return descriptions.get(var_name.lower(), f"{var_name.title()} input parameter")


def _suggest_default_value(var_name: str) -> str:
    """Suggest a reasonable default value for a parameter."""

    defaults = {
        "x": "0.0",
        "y": "0.0",
        "z": "0.0",
        "r": "1.0",
        "radius": "1.0",
        "height": "1.0",
        "width": "1.0",
        "length": "1.0",
        "size": "1.0",
        "scale": "1.0",
        "angle": "0.0",
        "rotation": "0.0",
        "count": "10",
        "num": "5",
        "points": "10",
        "segments": "10",
        "density": "10",
        "offset": "0.0",
        "distance": "1.0",
    }

    return defaults.get(var_name.lower(), "1.0")


def _generate_recommendations(parameters: list, script: str) -> list:
    """Generate recommendations for improving the parametric script."""

    recommendations = []

    if not parameters:
        recommendations.append(
            "No input parameters detected. Consider adding variables for user control."
        )

    if len(parameters) > 8:
        recommendations.append(
            "Many parameters detected. Consider grouping related parameters or using fewer inputs."
        )

    if "a =" not in script:
        recommendations.append(
            "No output assignment found. Make sure to assign result to variable 'a'."
        )

    if "import math" not in script and any("angle" in p["name"].lower() for p in parameters):
        recommendations.append(
            "Angle parameters detected but math module not imported. Consider adding 'import math'."
        )

    return recommendations


def recreate_python3_script_with_parameters(
    source_component_id: str,
    additional_params: Optional[List[Dict[str, str]]] = None,
    disable_original: bool = True,
    position_offset: Tuple[float, float] = (50, 0),
    auto_analyze: bool = True,
    new_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new parametric Python component based on an existing one, with proper input parameters.

    This function reads an existing Python component, analyzes its script for parameters,
    creates a new component with the detected/specified parameters, and optionally disables
    the original component. This solves the timing constraint issue where parameters cannot
    be added to components during solution execution.

    Args:
        source_component_id: ID of the existing Python component to recreate
        additional_params: Additional parameter definitions to include (optional)
        disable_original: Whether to disable the original component (default: True)
        position_offset: X,Y offset for positioning new component relative to original
        auto_analyze: Whether to automatically analyze script for parameters (default: True)
        new_name: Name for the new component (optional, defaults to original name + " (Parametric)")

    Returns:
        Dict[str, Any]: Result containing new component details and operation status

    Examples:
        # Example 1: Auto-analyze and recreate with detected parameters
        >>> result = recreate_python3_script_with_parameters(
        ...     source_component_id="a7ea6230-13cf-4bc3-a2b7-ae60c925f6c3",
        ...     auto_analyze=True
        ... )
        >>> if result.get("success"):
        ...     new_id = result["data"]["new_component"]["id"]
        ...     params = result["data"]["detected_parameters"]
        ...     print(f"Created parametric component {new_id} with {len(params)} inputs")

        # Example 2: Recreate with specific parameter definitions
        >>> custom_params = [
        ...     {"name": "sides", "type": "Integer", "description": "Number of polygon sides"},
        ...     {"name": "radius", "type": "Number", "description": "Polygon radius"}
        ... ]
        >>> result = recreate_python3_script_with_parameters(
        ...     source_component_id="component-id",
        ...     additional_params=custom_params,
        ...     auto_analyze=False,
        ...     new_name="Parametric Polygon"
        ... )

        # Example 3: Keep original component enabled for comparison
        >>> result = recreate_python3_script_with_parameters(
        ...     source_component_id="component-id",
        ...     disable_original=False,
        ...     position_offset=(100, 50)
        ... )
    """
    try:
        # Step 1: Read the original component and its script
        original_script_result = get_python3_script(source_component_id)
        if not original_script_result.get("success"):
            return {
                "success": False,
                "error": f"Could not read original component script: {original_script_result.get('error', 'Unknown error')}",
                "data": None,
            }

        # Extract script and component info
        original_data = original_script_result.get("data", {})
        script_content = original_data.get("script", "")
        original_name = original_data.get("name", "Python Script")

        if not script_content:
            return {
                "success": False,
                "error": "Original component has no script content",
                "data": None,
            }

        # Step 2: Get original component info for positioning
        original_info_result = get_component_info_enhanced(source_component_id)
        original_x = 100.0
        original_y = 100.0

        if original_info_result.get("success"):
            original_pos = original_info_result.get("result", {})
            original_x = float(original_pos.get("x", 100.0))
            original_y = float(original_pos.get("y", 100.0))

        # Step 3: Analyze script for parameters (if requested)
        detected_parameters = []
        analysis_result = None

        if auto_analyze:
            analysis_result = analyze_script_parameters(script_content)
            if analysis_result.get("success"):
                detected_parameters = analysis_result.get("suggested_parameters", [])
            else:
                # Continue even if analysis fails, but note the issue
                detected_parameters = []

        # Step 4: Combine detected and additional parameters
        all_parameters = detected_parameters.copy()
        if additional_params:
            # Merge additional params, avoiding duplicates
            existing_names = {p["name"] for p in detected_parameters}
            for param in additional_params:
                if param.get("name") not in existing_names:
                    all_parameters.append(param)

        # Step 5: Calculate new component position
        new_x = original_x + position_offset[0]
        new_y = original_y + position_offset[1]

        # Step 6: Determine new component name
        if new_name is None:
            new_name = f"{original_name} (Parametric)"

        # Step 7: Create new component with parameters
        # For now, we'll create with the enhanced add_python3_script
        # TODO: This will need C# backend support for custom parameters
        new_component_result = add_python3_script(
            x=new_x, y=new_y, script=script_content, name=new_name
        )

        if not new_component_result.get("success"):
            return {
                "success": False,
                "error": f"Failed to create new component: {new_component_result.get('error', 'Unknown error')}",
                "data": None,
            }

        new_component_data = new_component_result.get("data", {})

        # Step 8: Disable original component (if requested)
        disable_result = None
        if disable_original:
            # TODO: Implement component disable functionality
            # For now, we'll note this in the response
            disable_result = {
                "note": "Component disabling not yet implemented - please manually disable the original component",
                "original_component_id": source_component_id,
            }

        # Step 9: Return comprehensive result
        return {
            "success": True,
            "data": {
                "new_component": new_component_data,
                "original_component_id": source_component_id,
                "detected_parameters": detected_parameters,
                "all_parameters": all_parameters,
                "script_analysis": analysis_result,
                "position": {"x": new_x, "y": new_y},
                "disable_result": disable_result,
            },
            "message": f"Created parametric component '{new_name}' with {len(all_parameters)} suggested parameters",
            "next_steps": [
                "Manually add the detected input parameters to the new component:",
                *[
                    f"  - Add input '{p['name']}' ({p['type']}): {p['description']}"
                    for p in all_parameters
                ],
                "Connect sliders or other inputs to the new parameters",
                (
                    "Disable the original component if desired"
                    if not disable_original
                    else "Original component marked for disabling"
                ),
            ],
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to recreate component: {str(e)}", "data": None}


def disable_component(component_id: str, disable: bool = True) -> Dict[str, Any]:
    """
    Enable or disable a component on the Grasshopper canvas.

    Args:
        component_id: ID of the component to disable/enable
        disable: True to disable, False to enable (default: True)

    Returns:
        Dict[str, Any]: Result of the operation
    """
    # TODO: Implement component enable/disable functionality in C# backend
    # For now, return a placeholder response
    return {
        "success": False,
        "error": "Component disable/enable functionality not yet implemented in C# backend",
        "data": {
            "component_id": component_id,
            "requested_state": "disabled" if disable else "enabled",
            "note": "Please manually disable/enable the component in Grasshopper",
        },
    }
