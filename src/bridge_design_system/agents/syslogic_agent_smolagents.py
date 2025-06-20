"""
Simplified SysLogic Agent using native smolagents patterns.

This module provides a factory function that creates a structural validation agent
following smolagents best practices, focusing on truss system validation and
Grasshopper fix generation.
"""

import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from smolagents import CodeAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider

logger = get_logger(__name__)


@tool
def check_element_connectivity(elements: list) -> dict:
    """
    Validates beam endpoint connections accounting for 5x5mm cross-sections.
    
    Calculates actual beam endpoints from center/direction/length and checks
    if they connect properly with required gaps for physical beam dimensions.
    Different Z-levels are allowed (beams can be at different heights).
    
    Args:
        elements: List of AssemblyElement objects with center_point, direction, length
        
    Returns:
        Dict with valid (bool), gaps (dict of element pairs to gap size), 
        overlaps (dict), and issues (list of connectivity problems)
    """
    logger.info(f"🔍 Checking connectivity for {len(elements)} elements with 5x5mm cross-sections")
    
    result = {
        "valid": True,
        "gaps": {},
        "overlaps": {},
        "issues": []
    }
    
    min_gap = 2.5  # Minimum 2.5mm gap for 5x5mm cross-sections (half the width)
    max_gap = 5.0  # Maximum acceptable gap for connection
    
    try:
        # Calculate actual endpoints for all elements
        element_endpoints = []
        for elem in elements:
            endpoints = _calculate_beam_endpoints(elem)
            element_endpoints.append((elem, endpoints['start'], endpoints['end']))
        
        # Check all pairs of elements for connection
        for i, (elem1, start1, end1) in enumerate(element_endpoints):
            for j, (elem2, start2, end2) in enumerate(element_endpoints[i+1:], i+1):
                elem1_id = elem1.get('id', i)
                elem2_id = elem2.get('id', j)
                
                # Check all endpoint combinations (ignore Z differences)
                connections = [
                    (start1, start2, f"{elem1_id}-{elem2_id}_ss"),
                    (start1, end2, f"{elem1_id}-{elem2_id}_se"),
                    (end1, start2, f"{elem1_id}-{elem2_id}_es"),
                    (end1, end2, f"{elem1_id}-{elem2_id}_ee")
                ]
                
                for pt1, pt2, connection_id in connections:
                    # Calculate XY distance only (ignore Z differences)
                    xy_distance = _calculate_xy_distance(pt1, pt2)
                    
                    if min_gap <= xy_distance <= max_gap:
                        # Valid connection with proper gap
                        continue
                    elif xy_distance < min_gap:
                        # Too close - physical overlap
                        result["overlaps"][connection_id] = round(xy_distance, 3)
                        result["valid"] = False
                        result["issues"].append(
                            f"Physical overlap: {xy_distance:.3f}mm gap (need ≥{min_gap}mm)"
                        )
                    elif xy_distance > max_gap and xy_distance < 15.0:  # Potential intended connection
                        result["gaps"][connection_id] = round(xy_distance, 3)
                        result["valid"] = False
                        result["issues"].append(
                            f"Connection gap: {xy_distance:.3f}mm (should be {min_gap}-{max_gap}mm)"
                        )
        
        logger.info(f"✅ Connectivity check complete: {'VALID' if result['valid'] else 'ISSUES_FOUND'}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Connectivity check failed: {e}")
        return {
            "valid": False,
            "gaps": {},
            "overlaps": {},
            "issues": [f"Connectivity check error: {str(e)}"]
        }


@tool
def generate_geometry_agent_instructions(issue_type: str, element_data: dict, correction_data: dict) -> dict:
    """
    Creates instructions for the Geometry Agent to fix structural issues.
    
    Generates clear, actionable instructions that the Geometry Agent can execute
    via its MCP connection to modify the Grasshopper script.
    
    Args:
        issue_type: "connectivity_gap", "orientation_error", "overlap", or "missing_closure"
        element_data: Current element parameters and IDs
        correction_data: Required corrections (new values, adjustments)
        
    Returns:
        Dict with instructions for the Geometry Agent, reason, and expected outcome
    """
    logger.info(f"🔧 Generating Geometry Agent instructions for {issue_type}")
    
    try:
        instruction_templates = {
            "connectivity_gap": _generate_gap_instructions,
            "orientation_error": _generate_orientation_instructions,
            "overlap": _generate_overlap_instructions,
            "missing_closure": _generate_closure_instructions
        }
        
        if issue_type not in instruction_templates:
            raise ValueError(f"Unknown issue type: {issue_type}")
        
        instruction_generator = instruction_templates[issue_type]
        instructions = instruction_generator(element_data, correction_data)
        
        # Add metadata
        instructions.update({
            "issue_type": issue_type,
            "timestamp": datetime.now().isoformat(),
            "requires_validation": True,
            "target_agent": "geometry_agent"
        })
        
        logger.info(f"✅ Generated instructions for element {element_data.get('element_id', 'unknown')}")
        return instructions
        
    except Exception as e:
        logger.error(f"❌ Instruction generation failed: {e}")
        return {
            "error": str(e),
            "issue_type": issue_type,
            "success": False
        }


@tool
def calculate_closure_correction(elements: list, module_type: str) -> dict:
    """
    Calculates exact corrections for triangular truss module closure.
    
    Primarily handles 3-element triangular modules (A*, B*) by analyzing
    triangle geometry and determining adjustments for proper closure.
    
    Args:
        elements: List of AssemblyElements forming the module
        module_type: "A*", "B*" for triangular modules, "A", "B" for other configurations
        
    Returns:
        Dict with gap_location, required_adjustment, affected_elements
    """
    logger.info(f"📐 Calculating closure correction for {module_type} module with {len(elements)} elements")
    
    try:
        # Focus on triangular modules (well-defined geometry)
        if module_type in ["A*", "B*"]:
            if len(elements) != 3:
                raise ValueError(f"Triangular module {module_type} requires exactly 3 elements, got {len(elements)}")
            return _calculate_triangle_closure(elements, module_type)
        
        # Handle other module types (A, B) - needs clarification
        elif module_type in ["A", "B"]:
            # TODO: Clarify geometry of A/B modules - are they quadrilateral, linear, or other?
            logger.warning(f"Module type {module_type} handling needs clarification - what geometry do these form?")
            return {
                "gap_location": "clarification_needed",
                "required_adjustment": 0,
                "affected_elements": [elem.get("id", f"elem_{i}") for i, elem in enumerate(elements)],
                "note": f"Module type {module_type} geometry needs clarification for proper validation"
            }
        else:
            raise ValueError(f"Unknown module type: {module_type}")
            
    except Exception as e:
        logger.error(f"❌ Closure calculation failed: {e}")
        return {
            "error": str(e),
            "gap_location": "unknown",
            "required_adjustment": 0,
            "affected_elements": []
        }


@tool
def validate_planar_orientation(elements: list) -> dict:
    """
    Checks for non-horizontal beams in truss modules.
    
    Validates that all beam direction vectors have Z=0 component,
    ensuring horizontal orientation as required by system specifications.
    
    Args:
        elements: List of AssemblyElement objects to validate
        
    Returns:
        Dict with valid (bool), errors (list of elements with Z components)
    """
    logger.info(f"📏 Validating planar orientation for {len(elements)} elements")
    
    result = {
        "valid": True,
        "errors": [],
        "non_horizontal_elements": []
    }
    
    try:
        z_tolerance = 0.001  # 1mm tolerance for Z component
        
        for i, element in enumerate(elements):
            start_point = element.get("start_point", [0, 0, 0])
            end_point = element.get("end_point", [0, 0, 0])
            element_id = element.get("id", f"element_{i}")
            
            # Calculate direction vector
            direction = [
                end_point[0] - start_point[0],
                end_point[1] - start_point[1], 
                end_point[2] - start_point[2]
            ]
            
            # Check Z component
            z_component = abs(direction[2])
            
            if z_component > z_tolerance:
                result["valid"] = False
                error_info = {
                    "element_id": element_id,
                    "z_component": round(z_component, 4),
                    "start_z": start_point[2],
                    "end_z": end_point[2]
                }
                result["errors"].append(f"Element {element_id} has Z component: {z_component:.4f}mm")
                result["non_horizontal_elements"].append(error_info)
        
        logger.info(f"✅ Orientation validation: {'PASSED' if result['valid'] else 'FAILED'}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Orientation validation failed: {e}")
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "non_horizontal_elements": []
        }


# Helper functions for generating Geometry Agent instructions
def _generate_gap_instructions(element_data: dict, correction_data: dict) -> dict:
    """Generate instructions for fixing connectivity gaps."""
    element_id = element_data.get("element_id", "unknown")
    current_length = element_data.get("current_length", 0)
    new_length = correction_data.get("new_length", current_length)
    adjustment = abs(new_length - current_length)
    
    if new_length > current_length:
        action = "increase"
        direction = "extend"
    else:
        action = "decrease"
        direction = "shorten"
    
    return {
        "instructions": [
            f"Locate beam with ID '{element_id}' in the Grasshopper script",
            f"Modify the length parameter for beam '{element_id}'",
            f"{action.capitalize()} the length from {current_length}mm to {new_length}mm",
            f"This will {direction} the beam by {adjustment:.2f}mm to close the connection gap"
        ],
        "target_element": element_id,
        "action_type": "length_adjustment",
        "old_value": current_length,
        "new_value": new_length,
        "reason": f"Close {adjustment:.2f}mm connectivity gap",
        "expected_outcome": "Proper beam connection with appropriate physical gap"
    }


def _generate_orientation_instructions(element_data: dict, correction_data: dict) -> dict:
    """Generate instructions for fixing orientation errors."""
    element_id = element_data.get("element_id", "unknown")
    current_z = element_data.get("current_z", 0)
    target_z = correction_data.get("target_z", 0)
    
    return {
        "instructions": [
            f"Locate beam with ID '{element_id}' in the Grasshopper script",
            f"Check the Z-component of the direction vector or endpoints",
            f"Adjust the Z-coordinate from {current_z} to {target_z}",
            "Ensure the beam direction vector has Z=0 for horizontal orientation"
        ],
        "target_element": element_id,
        "action_type": "orientation_correction",
        "old_z_value": current_z,
        "new_z_value": target_z,
        "reason": f"Correct non-horizontal beam (Z={current_z} → Z={target_z})",
        "expected_outcome": "Beam oriented horizontally as required by system"
    }


def _generate_overlap_instructions(element_data: dict, correction_data: dict) -> dict:
    """Generate instructions for fixing element overlaps."""
    element_id = element_data.get("element_id", "unknown")
    overlap_distance = correction_data.get("overlap_distance", 0)
    required_separation = correction_data.get("required_separation", 2.5)
    
    return {
        "instructions": [
            f"Locate beam with ID '{element_id}' in the Grasshopper script",
            f"Current overlap: {overlap_distance:.2f}mm (too close for 5x5mm cross-sections)",
            f"Adjust beam position to achieve {required_separation:.1f}mm minimum gap",
            "This may require modifying center point or direction vector"
        ],
        "target_element": element_id,
        "action_type": "position_adjustment",
        "current_gap": overlap_distance,
        "required_gap": required_separation,
        "reason": "Prevent physical overlap of beam cross-sections",
        "expected_outcome": "Proper physical spacing between beam structures"
    }


def _generate_closure_instructions(element_data: dict, correction_data: dict) -> dict:
    """Generate instructions for fixing triangle closure."""
    affected_elements = correction_data.get("affected_elements", [])
    gap_size = correction_data.get("gap_size", 0)
    adjustment = correction_data.get("adjustment", gap_size / 2)
    
    return {
        "instructions": [
            f"Triangle closure issue detected with {gap_size:.2f}mm gap",
            f"Adjust lengths of beams: {', '.join(affected_elements)}",
            f"Distribute {adjustment:.2f}mm adjustment across the triangle sides",
            "Verify triangle closes properly after modifications"
        ],
        "target_elements": affected_elements,
        "action_type": "triangle_closure",
        "gap_size": gap_size,
        "adjustment_needed": adjustment,
        "reason": f"Close {gap_size:.2f}mm triangle gap for structural integrity",
        "expected_outcome": "Complete triangular module with proper closure"
    }


# Helper functions for calculations
def _calculate_beam_endpoints(element: dict) -> dict:
    """
    Calculate actual beam endpoints from center point, direction, and length.
    
    For AssemblyElement: center ± (direction.normalized * length/2)
    """
    center = element.get("center_point", [0, 0, 0])
    direction = element.get("direction", [1, 0, 0])  # Should be unit vector
    length = element.get("length", 0)
    
    # Normalize direction vector
    dir_length = math.sqrt(sum(d * d for d in direction))
    if dir_length == 0:
        normalized_dir = [0, 0, 0]
    else:
        normalized_dir = [d / dir_length for d in direction]
    
    # Calculate half-length vector
    half_vector = [d * length / 2 for d in normalized_dir]
    
    # Calculate endpoints
    start_point = [center[i] - half_vector[i] for i in range(3)]
    end_point = [center[i] + half_vector[i] for i in range(3)]
    
    return {
        "start": start_point,
        "end": end_point
    }


def _calculate_xy_distance(pt1: List[float], pt2: List[float]) -> float:
    """Calculate XY distance between two points (ignore Z component)."""
    dx = pt1[0] - pt2[0]
    dy = pt1[1] - pt2[1]
    return math.sqrt(dx * dx + dy * dy)


def _calculate_distance(pt1: List[float], pt2: List[float]) -> float:
    """Calculate 3D distance between two points."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pt1, pt2)))


def _calculate_triangle_closure(elements: List[dict], module_type: str) -> dict:
    """Calculate closure correction for triangular modules using actual beam endpoints."""
    
    # Calculate actual endpoints for all beams
    all_endpoints = []
    for element in elements:
        endpoints = _calculate_beam_endpoints(element)
        all_endpoints.extend([endpoints['start'], endpoints['end']])
    
    # Find unique vertices (triangle corners) with small tolerance
    unique_points = []
    tolerance = 0.5  # 0.5mm tolerance for considering points the same
    
    for pt in all_endpoints:
        is_unique = True
        for existing in unique_points:
            if _calculate_distance(pt, existing) < tolerance:
                is_unique = False
                break
        if is_unique:
            unique_points.append(pt)
    
    if len(unique_points) != 3:
        return {
            "error": f"Expected 3 unique vertices for triangle, found {len(unique_points)}",
            "gap_location": "vertex_detection_failed",
            "required_adjustment": 0,
            "affected_elements": [elem.get("id", f"elem_{i}") for i, elem in enumerate(elements)]
        }
    
    # Calculate side lengths between vertices
    side_lengths = [
        _calculate_distance(unique_points[0], unique_points[1]),
        _calculate_distance(unique_points[1], unique_points[2]),
        _calculate_distance(unique_points[2], unique_points[0])
    ]
    
    # Check for closure - in a perfect triangle, the sum of any two sides should exceed the third
    # Here we look for gaps by checking if the triangle actually closes
    perimeter = sum(side_lengths)
    largest_side = max(side_lengths)
    other_sides_sum = perimeter - largest_side
    
    closure_gap = largest_side - other_sides_sum if largest_side > other_sides_sum else 0
    
    return {
        "gap_location": "triangle_perimeter",
        "required_adjustment": closure_gap / 3,  # Distribute across all three beams
        "affected_elements": [elem.get("id", f"elem_{i}") for i, elem in enumerate(elements)],
        "side_lengths": side_lengths,
        "closure_gap": closure_gap,
        "vertices": unique_points
    }


def create_syslogic_agent(
    model_name: str = "syslogic", 
    component_registry: Optional[Any] = None,
    **kwargs
) -> CodeAgent:
    """
    Create autonomous SysLogic agent using smolagents CodeAgent pattern.
    
    This creates a structural validation agent that manages its own memory
    and state, following smolagents best practices for autonomous operation.
    
    Args:
        model_name: Model configuration name from settings
        component_registry: Optional registry for cross-agent communication
        **kwargs: Additional arguments passed to CodeAgent
        
    Returns:
        CodeAgent configured with structural validation tools
    """
    logger.info("🏗️ Creating autonomous SysLogic agent")
    
    # Get model configuration
    model = ModelProvider.get_model(model_name)
    
    # Define validation tools
    validation_tools = [
        check_element_connectivity,
        generate_geometry_agent_instructions,
        calculate_closure_correction,
        validate_planar_orientation
    ]
    
    # Extract max_steps from kwargs to avoid duplicate parameter error
    max_steps = kwargs.pop("max_steps", 8)  # Allow multiple validation steps
    
    # Create autonomous CodeAgent for complex structural reasoning
    agent = CodeAgent(
        tools=validation_tools,
        model=model,
        name="syslogic_agent",
        description="Validates truss structure integrity and provides Grasshopper fix instructions",
        max_steps=max_steps,
        additional_authorized_imports=["math", "re", "datetime", "typing"],
        **kwargs
    )
    
    # Load and append custom system prompt
    custom_prompt = get_syslogic_system_prompt()
    agent.prompt_templates["system_prompt"] = (
        agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
    )
    
    logger.info("✅ Created autonomous SysLogic agent with structural validation capabilities")
    return agent


def get_syslogic_system_prompt() -> str:
    """Get custom system prompt for SysLogic agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "SysLogic_agent.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")
    
    return prompt_path.read_text(encoding="utf-8")