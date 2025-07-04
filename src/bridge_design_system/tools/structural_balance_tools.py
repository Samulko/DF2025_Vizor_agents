"""
Structural Balance Tools for Geometry Agent

This module provides specialized tools for parsing beam parameters from Python code,
calculating structural moments, and solving for optimal beam placement to achieve
structural equilibrium.
"""

import re
from typing import Dict, List, Any, Tuple
from smolagents import tool

# Physics constants
DEFAULT_DENSITY = 600.0  # kg/m³ for wood
DEFAULT_WIDTH = 0.05     # m
DEFAULT_HEIGHT = 0.05    # m
DEFAULT_PIVOT = [0.0, 0.0, 0.0]  # origin


@tool
def parse_beam_parameters_from_code(python_code: str) -> str:
    """
    Parse beam parameters from Python component code to extract structured data for analysis.
    
    This tool extracts beam definitions from raw Python scripts, making it easier to
    perform structural calculations without manual parsing.
    
    Args:
        python_code: Raw Python script containing beam definitions with AssemblyElement objects
        
    Returns:
        JSON string with structured beam data including id, center, direction, length, and type
    """
    import json
    
    # Pattern to match beam definitions
    # Matches patterns like: center1 = rg.Point3d(-0, -0.0, 0.00)
    center_pattern = r'center(\d+)\s*=\s*rg\.Point3d\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)'
    
    # Matches patterns like: direction1 = rg.Vector3d(-1, -0, 0)
    direction_pattern = r'direction(\d+)\s*=\s*rg\.Vector3d\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)'
    
    # Matches patterns like: length1 = 0.30
    length_pattern = r'length(\d+)\s*=\s*([\d.]+)'
    
    # Matches patterns like: beam1 = AssemblyElement(id="001", type="green_a", ...)
    beam_pattern = r'beam(\d+)\s*=\s*AssemblyElement\([^)]*id\s*=\s*"(\d+)"[^)]*type\s*=\s*"([^"]+)"'
    
    # Find all matches
    centers = {match[0]: [float(match[1]), float(match[2]), float(match[3])] 
              for match in re.findall(center_pattern, python_code)}
    
    directions = {match[0]: [float(match[1]), float(match[2]), float(match[3])] 
                 for match in re.findall(direction_pattern, python_code)}
    
    lengths = {match[0]: float(match[1]) 
              for match in re.findall(length_pattern, python_code)}
    
    beam_info = {match[0]: {"id": match[1], "type": match[2]} 
                for match in re.findall(beam_pattern, python_code)}
    
    # Combine into structured data
    beams = []
    for beam_num in centers.keys():
        if beam_num in directions and beam_num in lengths and beam_num in beam_info:
            beam_data = {
                "id": beam_info[beam_num]["id"],
                "beam_number": int(beam_num),
                "center": centers[beam_num],
                "direction": directions[beam_num],
                "length": lengths[beam_num],
                "width": DEFAULT_WIDTH,
                "height": DEFAULT_HEIGHT,
                "type": beam_info[beam_num]["type"]
            }
            beams.append(beam_data)
    
    result = {
        "beams": sorted(beams, key=lambda x: x["beam_number"]),
        "total_beams": len(beams),
        "parsing_status": "success" if beams else "no beams found"
    }
    
    return json.dumps(result, indent=2)


@tool
def calculate_structural_moments(beam_data_json: str, density: float = 600.0, pivot_point_str: str = "0,0,0") -> str:
    """
    Calculate structural moments for a beam configuration to analyze structural balance.
    
    This tool performs physics calculations to determine the current imbalance in a structure
    and identifies the counter-moments needed for equilibrium.
    
    Args:
        beam_data_json: JSON string from parse_beam_parameters_from_code containing beam data
        density: Material density in kg/m³ (default: 600 for wood)
        pivot_point_str: Pivot point as comma-separated string "x,y,z" (default: "0,0,0")
        
    Returns:
        JSON string with detailed moment calculations, current imbalance, and required counter-moments
    """
    import json
    
    # Parse inputs
    try:
        beam_data = json.loads(beam_data_json)
        if not isinstance(beam_data, dict) or "beams" not in beam_data:
            return json.dumps({"error": "Invalid beam data format. Expected JSON with 'beams' array."})
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Failed to parse beam data JSON: {str(e)}"})
    
    # Parse pivot point
    try:
        pivot_parts = pivot_point_str.split(",")
        pivot_point = [float(p.strip()) for p in pivot_parts]
        if len(pivot_point) != 3:
            pivot_point = DEFAULT_PIVOT
    except:
        pivot_point = DEFAULT_PIVOT
    
    beams = beam_data.get("beams", [])
    if not beams:
        return json.dumps({"error": "No beams found in the provided data"})
    
    # Calculate moments for each beam
    individual_beams = []
    total_mx = 0.0
    total_my = 0.0
    
    for beam in beams:
        # Extract beam properties
        center = beam.get("center", [0, 0, 0])
        length = beam.get("length", 0)
        width = beam.get("width", DEFAULT_WIDTH)
        height = beam.get("height", DEFAULT_HEIGHT)
        
        # Calculate mass
        volume = length * width * height
        mass = density * volume
        
        # Calculate moment arms (distance from pivot)
        center_offset = [
            center[0] - pivot_point[0],
            center[1] - pivot_point[1],
            center[2] - pivot_point[2]
        ]
        
        # Calculate moments about pivot
        # Moment_x = mass * y_offset (rotation about x-axis)
        # Moment_y = mass * x_offset (rotation about y-axis)
        moment_x = mass * center_offset[1]
        moment_y = mass * center_offset[0]
        
        total_mx += moment_x
        total_my += moment_y
        
        individual_beams.append({
            "id": beam.get("id", "unknown"),
            "mass": round(mass, 3),
            "moment_x": round(moment_x, 3),
            "moment_y": round(moment_y, 3),
            "center": center,
            "center_offset": [round(x, 3) for x in center_offset]
        })
    
    # Determine balance status
    tolerance = 0.001  # kg⋅m
    is_balanced = abs(total_mx) < tolerance and abs(total_my) < tolerance
    
    result = {
        "individual_beams": individual_beams,
        "total_moments": {
            "moment_x": round(total_mx, 3),
            "moment_y": round(total_my, 3)
        },
        "required_counter_moments": {
            "moment_x": round(-total_mx, 3),
            "moment_y": round(-total_my, 3)
        },
        "is_balanced": is_balanced,
        "balance_status": "balanced" if is_balanced else "unbalanced",
        "pivot_point": pivot_point,
        "density_used": density
    }
    
    return json.dumps(result, indent=2)


@tool
def solve_balancing_beam_placement(
    required_moments_json: str, 
    constraints_json: str,
    beam_properties_str: str = "width:0.05,height:0.05"
) -> str:
    """
    Calculate optimal beam placement to achieve structural balance given moment requirements.
    
    This tool solves the engineering problem of where to place a beam to create specific
    counter-moments and achieve structural equilibrium.
    
    Args:
        required_moments_json: JSON string with required counter-moments {"moment_x": float, "moment_y": float}
        constraints_json: JSON string with placement constraints {"z_level": float, "direction": "X/Y/custom", "max_length": float}
        beam_properties_str: Beam dimensions as "width:W,height:H" (default: "width:0.05,height:0.05")
        
    Returns:
        JSON string with optimal beam parameters, verification calculations, and Python code
    """
    import json
    import math
    
    # Parse inputs
    try:
        required_moments = json.loads(required_moments_json)
        if not isinstance(required_moments, dict):
            return json.dumps({"error": "Invalid required_moments format"})
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Failed to parse required_moments JSON: {str(e)}"})
    
    try:
        constraints = json.loads(constraints_json)
        if not isinstance(constraints, dict):
            return json.dumps({"error": "Invalid constraints format"})
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Failed to parse constraints JSON: {str(e)}"})
    
    # Parse beam properties
    try:
        props = dict(item.split(":") for item in beam_properties_str.split(","))
        width = float(props.get("width", DEFAULT_WIDTH))
        height = float(props.get("height", DEFAULT_HEIGHT))
    except:
        width = DEFAULT_WIDTH
        height = DEFAULT_HEIGHT
    
    # Extract values
    req_mx = required_moments.get("moment_x", 0)
    req_my = required_moments.get("moment_y", 0)
    z_level = constraints.get("z_level", 0.1)
    direction = constraints.get("direction", "X").upper()
    max_length = constraints.get("max_length", 2.0)
    
    # Determine beam direction vector
    if direction == "X":
        direction_vec = [1, 0, 0]
    elif direction == "Y":
        direction_vec = [0, 1, 0]
    else:
        # Custom direction from constraints
        direction_vec = constraints.get("custom_direction", [1, 0, 0])
    
    # Normalize direction vector
    dir_magnitude = math.sqrt(sum(d*d for d in direction_vec))
    if dir_magnitude > 0:
        direction_vec = [d/dir_magnitude for d in direction_vec]
    
    # Calculate required beam properties
    # We need to solve: mass * y_center = req_mx and mass * x_center = req_my
    # This gives us constraints on position and mass
    
    # Strategy: Place beam at a position that satisfies moment requirements
    # If req_mx ≈ 0, place beam at y = 0
    # If req_my ≈ 0, place beam at x = 0
    # Otherwise, choose a reasonable position and solve for mass/length
    
    # Choose initial position based on moment requirements
    if abs(req_mx) < 0.001:
        y_pos = 0.0
    else:
        # Place at a reasonable y position
        y_pos = 0.15 if req_mx > 0 else -0.15
    
    if abs(req_my) < 0.001:
        x_pos = 0.0
    else:
        # Place at a reasonable x position  
        x_pos = -0.15 if req_my > 0 else 0.15
    
    center = [x_pos, y_pos, z_level]
    
    # Calculate required mass
    # req_mx = mass * y_pos, so mass = req_mx / y_pos (if y_pos != 0)
    # req_my = mass * x_pos, so mass = req_my / x_pos (if x_pos != 0)
    
    if abs(y_pos) > 0.001:
        mass_from_mx = req_mx / y_pos
    else:
        mass_from_mx = float('inf')
    
    if abs(x_pos) > 0.001:
        mass_from_my = req_my / x_pos
    else:
        mass_from_my = float('inf')
    
    # Choose the valid mass constraint
    if mass_from_mx != float('inf') and mass_from_my != float('inf'):
        # Both constraints exist - need to satisfy both
        # Adjust position to make them compatible
        if abs(mass_from_mx - mass_from_my) > 0.01:
            # Adjust positions to make mass constraints compatible
            if abs(req_mx) > abs(req_my):
                mass = mass_from_mx
                x_pos = req_my / mass if abs(mass) > 0.001 else 0
            else:
                mass = mass_from_my
                y_pos = req_mx / mass if abs(mass) > 0.001 else 0
            center = [x_pos, y_pos, z_level]
        else:
            mass = (mass_from_mx + mass_from_my) / 2
    elif mass_from_mx != float('inf'):
        mass = mass_from_mx
    elif mass_from_my != float('inf'):
        mass = mass_from_my
    else:
        # Both positions are zero - can't create required moments
        return json.dumps({
            "error": "Cannot create required moments with beam at origin",
            "suggestion": "Adjust constraints to allow non-zero x or y position"
        })
    
    # Calculate required length from mass
    volume_needed = abs(mass) / DEFAULT_DENSITY
    length = volume_needed / (width * height)
    
    # Check length constraint
    if length > max_length:
        # Scale down to max length and adjust position
        length = max_length
        actual_mass = DEFAULT_DENSITY * length * width * height
        scale_factor = actual_mass / abs(mass)
        
        # Adjust position to compensate
        if abs(y_pos) > 0.001:
            y_pos = y_pos / scale_factor
        if abs(x_pos) > 0.001:
            x_pos = x_pos / scale_factor
        center = [x_pos, y_pos, z_level]
        mass = actual_mass
    
    # Round values for clean output
    center = [round(c, 3) for c in center]
    direction_vec = [round(d, 3) for d in direction_vec]
    length = round(length, 3)
    mass = round(mass, 3)
    
    # Verify the solution
    actual_mx = mass * center[1]
    actual_my = mass * center[0]
    
    # Generate Python code
    beam_id = "XXX"  # Placeholder - should be determined by context
    beam_type = "yellow_a"  # Default balancing beam color
    
    python_code = f"""# --- BALANCING BEAM ---
center = rg.Point3d({center[0]}, {center[1]}, {center[2]})
direction = rg.Vector3d({direction_vec[0]}, {direction_vec[1]}, {direction_vec[2]})
length = {length}
beam = AssemblyElement(id="{beam_id}", type="{beam_type}", center_point=center,
                      direction=direction, length=length, width={width}, height={height})
assembly_elements.append(beam)"""
    
    result = {
        "optimal_beam": {
            "center": center,
            "direction": direction_vec,
            "length": length,
            "width": width,
            "height": height,
            "mass": mass
        },
        "verification": {
            "moments_created": {
                "moment_x": round(actual_mx, 3),
                "moment_y": round(actual_my, 3)
            },
            "required_moments": {
                "moment_x": round(req_mx, 3),
                "moment_y": round(req_my, 3)
            },
            "error": {
                "moment_x": round(abs(actual_mx - req_mx), 3),
                "moment_y": round(abs(actual_my - req_my), 3)
            },
            "is_balanced": abs(actual_mx - req_mx) < 0.001 and abs(actual_my - req_my) < 0.001
        },
        "python_code": python_code,
        "note": "Replace 'XXX' with appropriate beam ID and adjust beam type as needed"
    }
    
    return json.dumps(result, indent=2)


@tool 
def generate_beam_code(beam_parameters_json: str, beam_id: str, beam_type: str = "yellow_a") -> str:
    """
    Generate properly formatted Python code for a beam given its parameters.
    
    This tool creates the exact Python code needed to add a beam to a Grasshopper component,
    following the standard format used in the codebase.
    
    Args:
        beam_parameters_json: JSON string with beam parameters (center, direction, length, etc.)
        beam_id: Element ID for the beam (e.g., "004", "005")
        beam_type: Beam type/color (default: "yellow_a" for balancing beams)
        
    Returns:
        Formatted Python code string ready to be inserted into a component script
    """
    import json
    
    try:
        params = json.loads(beam_parameters_json)
        if not isinstance(params, dict):
            return "# ERROR: Invalid beam parameters format"
    except json.JSONDecodeError as e:
        return f"# ERROR: Failed to parse beam parameters: {str(e)}"
    
    # Extract parameters
    center = params.get("center", [0, 0, 0])
    direction = params.get("direction", [1, 0, 0])
    length = params.get("length", 1.0)
    width = params.get("width", DEFAULT_WIDTH)
    height = params.get("height", DEFAULT_HEIGHT)
    
    # Determine beam number from ID
    try:
        beam_num = int(beam_id)
    except:
        beam_num = 4  # Default if ID parsing fails
    
    # Generate description based on beam position
    if center[2] < 0.05:
        level_desc = "Level 1"
    elif center[2] < 0.10:
        level_desc = "Level 2"
    else:
        level_desc = "Level 3"
    
    code = f"""
# --- BEAM {beam_num}: Balancing beam on {level_desc} ---
center{beam_num} = rg.Point3d({center[0]}, {center[1]}, {center[2]})
direction{beam_num} = rg.Vector3d({direction[0]}, {direction[1]}, {direction[2]})
length{beam_num} = {length}
beam{beam_num} = AssemblyElement(id="{beam_id}", type="{beam_type}", center_point=center{beam_num},
                        direction=direction{beam_num}, length=length{beam_num}, width={width}, height={height})
assembly_elements.append(beam{beam_num})"""
    
    return code