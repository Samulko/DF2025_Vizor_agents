"""
Simplified SysLogic Agent using native smolagents patterns.

This module provides a factory function that creates a structural validation agent
following smolagents best practices, focusing on truss system validation and
Grasshopper fix generation.
"""

import math
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from smolagents import CodeAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..tools.material_tools import (
    CuttingOptimizer,
    MaterialInventoryManager,
    create_session_record,
    extract_element_lengths,
)

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

    result = {"valid": True, "gaps": {}, "overlaps": {}, "issues": []}

    min_gap = 2.5  # Minimum 2.5mm gap for 5x5mm cross-sections (half the width)
    max_gap = 5.0  # Maximum acceptable gap for connection

    try:
        # Calculate actual endpoints for all elements
        element_endpoints = []
        for elem in elements:
            endpoints = _calculate_beam_endpoints(elem)
            element_endpoints.append((elem, endpoints["start"], endpoints["end"]))

        # Check all pairs of elements for connection
        for i, (elem1, start1, end1) in enumerate(element_endpoints):
            for j, (elem2, start2, end2) in enumerate(element_endpoints[i + 1 :], i + 1):
                elem1_id = elem1.get("id", i)
                elem2_id = elem2.get("id", j)

                # Check all endpoint combinations (ignore Z differences)
                connections = [
                    (start1, start2, f"{elem1_id}-{elem2_id}_ss"),
                    (start1, end2, f"{elem1_id}-{elem2_id}_se"),
                    (end1, start2, f"{elem1_id}-{elem2_id}_es"),
                    (end1, end2, f"{elem1_id}-{elem2_id}_ee"),
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
                    elif (
                        xy_distance > max_gap and xy_distance < 15.0
                    ):  # Potential intended connection
                        result["gaps"][connection_id] = round(xy_distance, 3)
                        result["valid"] = False
                        result["issues"].append(
                            f"Connection gap: {xy_distance:.3f}mm (should be {min_gap}-{max_gap}mm)"
                        )

        logger.info(
            f"✅ Connectivity check complete: {'VALID' if result['valid'] else 'ISSUES_FOUND'}"
        )
        return result

    except Exception as e:
        logger.error(f"❌ Connectivity check failed: {e}")
        return {
            "valid": False,
            "gaps": {},
            "overlaps": {},
            "issues": [f"Connectivity check error: {str(e)}"],
        }


@tool
def generate_geometry_agent_instructions(
    issue_type: str, element_data: dict, correction_data: dict
) -> dict:
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
            "missing_closure": _generate_closure_instructions,
        }

        if issue_type not in instruction_templates:
            raise ValueError(f"Unknown issue type: {issue_type}")

        instruction_generator = instruction_templates[issue_type]
        instructions = instruction_generator(element_data, correction_data)

        # Add metadata
        instructions.update(
            {
                "issue_type": issue_type,
                "timestamp": datetime.now().isoformat(),
                "requires_validation": True,
                "target_agent": "geometry_agent",
            }
        )

        logger.info(
            f"✅ Generated instructions for element {element_data.get('element_id', 'unknown')}"
        )
        return instructions

    except Exception as e:
        logger.error(f"❌ Instruction generation failed: {e}")
        return {"error": str(e), "issue_type": issue_type, "success": False}


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
    logger.info(
        f"📐 Calculating closure correction for {module_type} module with {len(elements)} elements"
    )

    try:
        # Focus on triangular modules (well-defined geometry)
        if module_type in ["A*", "B*"]:
            if len(elements) != 3:
                raise ValueError(
                    f"Triangular module {module_type} requires exactly 3 elements, "
                    f"got {len(elements)}"
                )
            return _calculate_triangle_closure(elements, module_type)

        # Handle other module types (A, B) - needs clarification
        elif module_type in ["A", "B"]:
            # TODO: Clarify geometry of A/B modules - are they quadrilateral, linear, or other?
            logger.warning(
                f"Module type {module_type} handling needs clarification - "
                f"what geometry do these form?"
            )
            return {
                "gap_location": "clarification_needed",
                "required_adjustment": 0,
                "affected_elements": [
                    elem.get("id", f"elem_{i}") for i, elem in enumerate(elements)
                ],
                "note": (
                    f"Module type {module_type} geometry needs clarification "
                    f"for proper validation"
                ),
            }
        else:
            raise ValueError(f"Unknown module type: {module_type}")

    except Exception as e:
        logger.error(f"❌ Closure calculation failed: {e}")
        return {
            "error": str(e),
            "gap_location": "unknown",
            "required_adjustment": 0,
            "affected_elements": [],
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

    result = {"valid": True, "errors": [], "non_horizontal_elements": []}

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
                end_point[2] - start_point[2],
            ]

            # Check Z component
            z_component = abs(direction[2])

            if z_component > z_tolerance:
                result["valid"] = False
                error_info = {
                    "element_id": element_id,
                    "z_component": round(z_component, 4),
                    "start_z": start_point[2],
                    "end_z": end_point[2],
                }
                result["errors"].append(
                    f"Element {element_id} has Z component: {z_component:.4f}mm"
                )
                result["non_horizontal_elements"].append(error_info)

        logger.info(f"✅ Orientation validation: {'PASSED' if result['valid'] else 'FAILED'}")
        return result

    except Exception as e:
        logger.error(f"❌ Orientation validation failed: {e}")
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "non_horizontal_elements": [],
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
            f"This will {direction} the beam by {adjustment:.2f}mm to close the connection gap",
        ],
        "target_element": element_id,
        "action_type": "length_adjustment",
        "old_value": current_length,
        "new_value": new_length,
        "reason": f"Close {adjustment:.2f}mm connectivity gap",
        "expected_outcome": "Proper beam connection with appropriate physical gap",
    }


def _generate_orientation_instructions(element_data: dict, correction_data: dict) -> dict:
    """Generate instructions for fixing orientation errors."""
    element_id = element_data.get("element_id", "unknown")
    current_z = element_data.get("current_z", 0)
    target_z = correction_data.get("target_z", 0)

    return {
        "instructions": [
            f"Locate beam with ID '{element_id}' in the Grasshopper script",
            "Check the Z-component of the direction vector or endpoints",
            f"Adjust the Z-coordinate from {current_z} to {target_z}",
            "Ensure the beam direction vector has Z=0 for horizontal orientation",
        ],
        "target_element": element_id,
        "action_type": "orientation_correction",
        "old_z_value": current_z,
        "new_z_value": target_z,
        "reason": f"Correct non-horizontal beam (Z={current_z} → Z={target_z})",
        "expected_outcome": "Beam oriented horizontally as required by system",
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
            "This may require modifying center point or direction vector",
        ],
        "target_element": element_id,
        "action_type": "position_adjustment",
        "current_gap": overlap_distance,
        "required_gap": required_separation,
        "reason": "Prevent physical overlap of beam cross-sections",
        "expected_outcome": "Proper physical spacing between beam structures",
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
            "Verify triangle closes properly after modifications",
        ],
        "target_elements": affected_elements,
        "action_type": "triangle_closure",
        "gap_size": gap_size,
        "adjustment_needed": adjustment,
        "reason": f"Close {gap_size:.2f}mm triangle gap for structural integrity",
        "expected_outcome": "Complete triangular module with proper closure",
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

    return {"start": start_point, "end": end_point}


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
        all_endpoints.extend([endpoints["start"], endpoints["end"]])

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
            "affected_elements": [elem.get("id", f"elem_{i}") for i, elem in enumerate(elements)],
        }

    # Calculate side lengths between vertices
    side_lengths = [
        _calculate_distance(unique_points[0], unique_points[1]),
        _calculate_distance(unique_points[1], unique_points[2]),
        _calculate_distance(unique_points[2], unique_points[0]),
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
        "vertices": unique_points,
    }


# ==================== MATERIAL TRACKING TOOLS ====================


@tool
def analyze_cutting_plan(required_lengths: list) -> dict:
    """
    Analyzes and validates a cutting plan against the current material inventory.

    This tool checks if a list of required element lengths is feasible with the
    available material. It uses an optimizer to find the most efficient cutting
    sequence and returns a detailed analysis including feasibility, projected waste,
    material efficiency, and a visual plan.

    This is a READ-ONLY tool for planning and does NOT modify the inventory. Use
    'commit_material_usage' to apply the cuts after analysis.

    Args:
        required_lengths: List of required element lengths in mm.

    Returns:
        Dict with feasibility status, optimization analysis, and potential alternatives.
    """
    logger.info(f"📊 Analyzing cutting plan for {len(required_lengths)} elements")

    try:
        # Initialize managers
        inventory_manager = MaterialInventoryManager()
        optimizer = CuttingOptimizer()

        # Convert to proper lengths if needed
        element_lengths = []
        if isinstance(required_lengths[0], (int, float)) and all(
            isinstance(x, (int, float)) for x in required_lengths
        ):
            # Direct length values - convert to mm if needed
            for length in required_lengths:
                if length < 100:  # Assume cm, convert to mm
                    element_lengths.append(int(length * 10))
                else:  # Already mm
                    element_lengths.append(int(length))
        else:
            # Extract from element objects
            element_lengths = extract_element_lengths(required_lengths)

        if not element_lengths:
            return {
                "feasible": False,
                "error": "No valid element lengths found",
                "analysis": None,
            }

        # Get current beams
        beams = inventory_manager.get_beams()

        # Perform comprehensive feasibility analysis
        feasibility_result = optimizer.validate_feasibility(element_lengths, beams)

        # Get optimized cutting plan
        cutting_result = optimizer.first_fit_decreasing(element_lengths, beams)

        # Generate alternatives if not feasible
        alternatives = []
        if not feasibility_result["feasible"]:
            alternatives = _generate_design_alternatives(element_lengths, beams, optimizer)

        # Calculate design metrics
        total_required = sum(element_lengths)
        total_available = sum(beam.remaining_length_mm for beam in beams)

        return {
            "feasible": cutting_result["summary"]["feasible"],
            "analysis": {
                "total_elements": len(element_lengths),
                "total_length_required_mm": total_required,
                "total_length_available_mm": total_available,
                "capacity_utilization_percent": (
                    (total_required / total_available * 100) if total_available > 0 else 0
                ),
                "largest_element_mm": max(element_lengths) if element_lengths else 0,
                "smallest_element_mm": min(element_lengths) if element_lengths else 0,
            },
            "optimization_results": {
                "efficiency_percent": cutting_result["summary"]["material_efficiency_percent"],
                "waste_mm": cutting_result["summary"]["total_waste_mm"],
                "unassigned_elements": cutting_result["summary"]["unassigned_elements"],
                "cutting_plan": cutting_result["cutting_plan"],
                "beam_assignments": cutting_result["beam_assignments"],
            },
            "feasibility_details": feasibility_result,
            "alternatives": alternatives,
            "recommendations": _generate_feasibility_recommendations(
                feasibility_result, element_lengths, beams
            ),
            "visual_plan": _format_cutting_plan_visual(cutting_result),
            "constraints": {
                "max_beam_length_available_mm": max(
                    (beam.remaining_length_mm for beam in beams), default=0
                ),
                "min_cut_length_recommended_mm": 50,
                "kerf_loss_per_cut_mm": 3,
            },
        }

    except Exception as e:
        logger.error(f"❌ Cutting plan analysis failed: {e}")
        return {
            "feasible": False,
            "error": f"Analysis error: {str(e)}",
            "analysis": None,
        }


@tool
def commit_material_usage(elements: list, session_id: str = None) -> dict:
    """
    Optimizes cutting and commits material usage to the inventory.

    This tool first calculates the most efficient cutting plan for the given
    elements. If the plan is feasible, it applies the cuts to the material inventory,
    updates the remaining material, tracks waste, and saves a session record.

    CRITICAL: This tool permanently modifies the inventory. It is best practice
    to use 'analyze_cutting_plan' first to validate feasibility.

    Args:
        elements: List of AssemblyElement objects with a 'length' property.
        session_id: Optional session identifier for tracking.

    Returns:
        A dictionary summarizing the material used, waste generated, and updated inventory status.
    """
    logger.info(f"💾 Committing material usage for {len(elements)} elements")

    try:
        # Initialize material manager
        inventory_manager = MaterialInventoryManager()
        optimizer = CuttingOptimizer()

        # Extract element lengths
        element_lengths = extract_element_lengths(elements)

        if not element_lengths:
            return {
                "success": False,
                "error": "No valid element lengths found",
                "elements_processed": 0,
            }

        # Generate session ID if not provided
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Get current beams and plan cutting
        beams = inventory_manager.get_beams()
        cutting_result = optimizer.first_fit_decreasing(element_lengths, beams)

        # Check if cutting is feasible
        if not cutting_result["summary"]["feasible"]:
            return {
                "success": False,
                "feasible": False,
                "error": "Insufficient material for requested elements",
                "required_elements": len(element_lengths),
                "unassigned_elements": cutting_result["summary"]["unassigned_elements"],
                "suggestions": optimizer._generate_optimization_suggestions(cutting_result),
                "available_material_mm": sum(beam.remaining_length_mm for beam in beams),
                "recommendation": (
                    "Use 'analyze_cutting_plan' first to validate feasibility "
                    "and explore alternatives"
                ),
            }

        # Apply cuts to inventory
        updated_beams = []
        for beam_assignment in cutting_result["beam_assignments"]:
            # Find the corresponding beam
            beam = next((b for b in beams if b.beam_id == beam_assignment["beam_id"]), None)
            if beam:
                # Update beam with new cuts from the optimization result
                beam.remaining_length_mm = beam_assignment["remaining_length_mm"]
                beam.utilization_percent = beam_assignment["utilization_percent"]
                beam.waste_mm = beam_assignment["waste_mm"]
                # Add new cuts
                for cut_data in beam_assignment["cuts"]:
                    if cut_data["element_id"] not in [cut.element_id for cut in beam.cuts]:
                        beam.add_cut(
                            cut_data["element_id"],
                            cut_data["length_mm"],
                            cut_data.get("kerf_loss_mm", 3),
                        )
                updated_beams.append(beam)

        # Update inventory
        inventory_manager.update_beams(updated_beams)

        # Create session record
        session_record = create_session_record(session_id, elements, cutting_result)

        # Add session to inventory data
        inventory_manager.inventory_data.setdefault("cutting_sessions", []).append(session_record)
        inventory_manager._save_inventory()

        # Get updated status
        status = inventory_manager.get_status(detailed=False)

        return {
            "success": True,
            "session_id": session_id,
            "elements_processed": len(element_lengths),
            "cutting_plan": cutting_result["cutting_plan"],
            "material_summary": {
                "total_length_used_mm": sum(element_lengths),
                "total_kerf_loss_mm": len(element_lengths) * 3,
                "waste_generated_mm": cutting_result["summary"]["total_waste_mm"],
                "efficiency_percent": cutting_result["summary"]["material_efficiency_percent"],
            },
            "inventory_status": status,
            "optimization_applied": {
                "algorithm": "first_fit_decreasing",
                "beam_assignments": len(cutting_result["beam_assignments"]),
                "total_cuts_applied": sum(
                    len(ba["cuts"]) for ba in cutting_result["beam_assignments"]
                ),
            },
            "recommendations": optimizer._generate_optimization_suggestions(cutting_result),
        }

    except Exception as e:
        logger.error(f"❌ Material usage commit failed: {e}")
        return {
            "success": False,
            "error": f"Commit error: {str(e)}",
            "elements_processed": 0,
        }


@tool
def get_material_status(
    detailed: bool = False,
    project_context: str = None,
    design_complexity: str = None,
    user_intent: str = None,
) -> dict:
    """
    Get current material inventory status and availability with context.

    Provides real-time view of material inventory including remaining
    capacity, utilization statistics, and beam-by-beam breakdown.
    Returns raw data for agent to reason about contextually.

    Args:
        detailed: Whether to include detailed beam-by-beam breakdown
        project_context: Context about project phase (e.g., "prototyping", "production", "testing")
        design_complexity: Complexity level (e.g., "simple", "complex", "experimental")
        user_intent: User's current goal (e.g., "optimization", "validation", "exploration")

    Returns:
        Dict with raw inventory data, context info, and deterministic calculations only
    """
    logger.info(f"📊 Getting material status (detailed={detailed})")

    try:
        # Initialize material manager
        inventory_manager = MaterialInventoryManager()

        # Get comprehensive status
        status = inventory_manager.get_status(detailed=detailed)

        # Add additional analysis
        beams = inventory_manager.get_beams()

        # Calculate beam utilization distribution
        utilization_ranges = {
            "unused": len([b for b in beams if b.utilization_percent == 0]),
            "low_use_0_25": len([b for b in beams if 0 < b.utilization_percent <= 25]),
            "medium_use_25_75": len([b for b in beams if 25 < b.utilization_percent <= 75]),
            "high_use_75_100": len([b for b in beams if 75 < b.utilization_percent <= 100]),
        }

        # Calculate remaining capacity by beam size
        capacity_analysis = {
            "beams_with_500mm_plus": len([b for b in beams if b.remaining_length_mm >= 500]),
            "beams_with_200_500mm": len([b for b in beams if 200 <= b.remaining_length_mm < 500]),
            "beams_with_50_200mm": len([b for b in beams if 50 <= b.remaining_length_mm < 200]),
            "beams_unusable": len([b for b in beams if b.remaining_length_mm < 50]),
        }

        # Recent usage analysis
        total_cuts = sum(len(beam.cuts) for beam in beams)
        recent_sessions = inventory_manager.inventory_data.get("cutting_sessions", [])

        return {
            "success": True,
            "inventory_status": status,
            "utilization_distribution": utilization_ranges,
            "capacity_analysis": capacity_analysis,
            "usage_summary": {
                "total_cuts_made": total_cuts,
                "cutting_sessions": len(recent_sessions),
                "last_updated": inventory_manager.inventory_data.get("last_updated", "Unknown"),
            },
            "context_info": {
                "project_context": project_context,
                "design_complexity": design_complexity,
                "user_intent": user_intent,
            },
            # Note: No hardcoded recommendations or alerts - agent will reason about
            # this data contextually
        }

    except Exception as e:
        logger.error(f"❌ Failed to get material status: {e}")
        return {
            "success": False,
            "error": f"Status retrieval error: {str(e)}",
            "inventory_status": None,
        }


# Note: validate_material_feasibility functionality has been consolidated into analyze_cutting_plan


@tool
def reset_material_inventory(reset_type: str = "full", backup_name: str = None) -> dict:
    """
    Reset material inventory to original or specified state.

    Provides flexible reset options for development, testing, and design iteration.
    Automatically creates backup before reset operations for safety.

    Args:
        reset_type: Type of reset - "full" (all beams pristine), "session" (to specific session),
                   "backup" (restore from backup), "confirm_full" (confirmed full reset)
        backup_name: Name of backup to restore from (if reset_type="backup") or
                     session ID (if reset_type="session")

    Returns:
        Dict with reset status, operation details, and new inventory state
    """
    logger.info(f"🔄 Material inventory reset requested: {reset_type}")

    try:
        # Initialize material manager
        inventory_manager = MaterialInventoryManager()

        # Safety check for full reset
        if reset_type == "full":
            current_status = inventory_manager.get_status(detailed=False)
            if current_status["total_utilization_percent"] > 0:
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "warning": (
                        f"Current inventory has "
                        f"{current_status['total_utilization_percent']:.1f}% utilization"
                    ),
                    "current_usage": {
                        "total_cuts": sum(len(beam.cuts) for beam in inventory_manager.get_beams()),
                        "sessions": len(
                            inventory_manager.inventory_data.get("cutting_sessions", [])
                        ),
                        "waste_mm": current_status["total_waste_mm"],
                    },
                    "message": "Use reset_type='confirm_full' to proceed with full reset",
                    "alternative": (
                        "Consider using reset_type='session' to reset to a specific "
                        "session instead"
                    ),
                }

        # Create automatic backup before reset
        backup_created = None
        if reset_type in ["full", "confirm_full"]:
            try:
                backup_name_auto = (
                    f"auto_backup_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                inventory_manager._create_backup(backup_name_auto)
                backup_created = backup_name_auto
                logger.info(f"📋 Automatic backup created: {backup_name_auto}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create automatic backup: {e}")

        # Perform reset based on type
        reset_result = None

        if reset_type in ["full", "confirm_full"]:
            # Full reset - restore all 13 beams to pristine state
            reset_result = _perform_full_reset(inventory_manager)

        elif reset_type == "session":
            # Session reset - restore to specific cutting session
            if not backup_name:
                return {
                    "success": False,
                    "error": "session_id required for session reset",
                    "available_sessions": [
                        session["session_id"]
                        for session in inventory_manager.inventory_data.get("cutting_sessions", [])
                    ],
                }
            reset_result = _perform_session_reset(inventory_manager, backup_name)

        elif reset_type == "backup":
            # Backup restore - restore from named backup
            if not backup_name:
                return {
                    "success": False,
                    "error": "backup_name required for backup restore",
                    "available_backups": inventory_manager._list_backups(),
                }
            reset_result = _perform_backup_restore(inventory_manager, backup_name)

        else:
            return {
                "success": False,
                "error": f"Unknown reset_type: {reset_type}",
                "valid_types": ["full", "confirm_full", "session", "backup"],
            }

        # Get new status after reset
        new_status = inventory_manager.get_status(detailed=False)

        return {
            "success": True,
            "reset_type": reset_type,
            "backup_created": backup_created,
            "reset_details": reset_result,
            "new_inventory_status": {
                "total_beams": new_status["total_beams"],
                "beams_available": new_status["beams_available"],
                "total_remaining_mm": new_status["total_remaining_mm"],
                "total_utilization_percent": new_status["total_utilization_percent"],
            },
            "message": f"Material inventory reset completed successfully using {reset_type} method",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Material inventory reset failed: {e}")
        return {
            "success": False,
            "error": f"Reset operation failed: {str(e)}",
            "reset_type": reset_type,
        }


# ==================== RESET HELPER FUNCTIONS ====================


def _perform_full_reset(inventory_manager) -> dict:
    """Perform full reset of all beams to pristine state."""
    try:
        # Create fresh inventory data with all 13 beams at 1980mm
        fresh_inventory = {
            "total_stock_mm": 25740,  # 13 * 1980
            "beam_length_mm": 1980,
            "kerf_loss_mm": 3,
            "available_beams": [],
            "used_elements": [],
            "total_waste_mm": 0,
            "total_utilization_percent": 0.0,
            "cutting_sessions": [],
            "last_updated": datetime.now().isoformat(),
            "metadata": {
                "cross_section": "5x5cm",
                "material_type": "timber",
                "project": "bridge_design",
                "version": "1.0",
                "units": "millimeters",
            },
            "statistics": {
                "total_beams": 13,
                "full_beams": 13,
                "partial_beams": 0,
                "average_beam_length_mm": 1980.0,
                "material_efficiency_target": 95.0,
                "waste_tolerance_mm": 100,
            },
        }

        # Create 13 pristine beams
        for i in range(1, 14):
            beam_data = {
                "id": f"beam_{i:03d}",
                "original_length_mm": 1980,
                "remaining_length_mm": 1980,
                "cuts": [],
                "waste_mm": 0,
                "utilization_percent": 0.0,
            }
            fresh_inventory["available_beams"].append(beam_data)

        # Save the fresh inventory
        inventory_manager.inventory_data = fresh_inventory
        inventory_manager._save_inventory()

        logger.info("✅ Full reset completed - all 13 beams restored to 1980mm")
        return {
            "operation": "full_reset",
            "beams_reset": 13,
            "total_material_restored_mm": 25740,
            "sessions_cleared": "all",
            "cuts_cleared": "all",
        }

    except Exception as e:
        logger.error(f"❌ Full reset failed: {e}")
        raise


def _perform_session_reset(inventory_manager, session_id: str) -> dict:
    """Reset inventory to state before a specific cutting session."""
    try:
        sessions = inventory_manager.inventory_data.get("cutting_sessions", [])

        # Find the target session
        target_session_index = None
        for i, session in enumerate(sessions):
            if session["session_id"] == session_id:
                target_session_index = i
                break

        if target_session_index is None:
            raise ValueError(f"Session '{session_id}' not found")

        # Create inventory state as it was before this session
        # We need to reverse all sessions from the target onwards
        sessions_to_reverse = sessions[target_session_index:]

        logger.info(f"🔄 Reversing {len(sessions_to_reverse)} sessions from '{session_id}' onwards")

        # Start with current beams and reverse the operations
        beams = inventory_manager.get_beams()
        cuts_removed = 0

        for session in reversed(sessions_to_reverse):
            cutting_plan = session.get("cutting_plan", {}).get("cutting_plan", [])
            for cut in cutting_plan:
                # Find the beam and remove this cut
                for beam in beams:
                    if beam.beam_id == cut["beam_id"]:
                        # Remove the cut if it exists
                        beam.cuts = [c for c in beam.cuts if c.element_id != cut["element_id"]]
                        # Recalculate remaining length
                        total_cuts_length = sum(c.length_mm + c.kerf_loss_mm for c in beam.cuts)
                        beam.remaining_length_mm = beam.original_length_mm - total_cuts_length
                        beam.utilization_percent = (
                            (beam.original_length_mm - beam.remaining_length_mm)
                            / beam.original_length_mm
                        ) * 100
                        cuts_removed += 1
                        break

        # Update inventory with reversed state
        inventory_manager.update_beams(beams)

        # Remove the reversed sessions from history
        inventory_manager.inventory_data["cutting_sessions"] = sessions[:target_session_index]
        inventory_manager._save_inventory()

        logger.info(f"✅ Session reset completed - removed {cuts_removed} cuts")
        return {
            "operation": "session_reset",
            "target_session": session_id,
            "sessions_removed": len(sessions_to_reverse),
            "cuts_removed": cuts_removed,
            "remaining_sessions": len(inventory_manager.inventory_data["cutting_sessions"]),
        }

    except Exception as e:
        logger.error(f"❌ Session reset failed: {e}")
        raise


def _perform_backup_restore(inventory_manager, backup_name: str) -> dict:
    """Restore inventory from a named backup file."""
    try:
        restored_data = inventory_manager._restore_backup(backup_name)

        logger.info(f"✅ Backup restore completed from '{backup_name}'")
        return {
            "operation": "backup_restore",
            "backup_name": backup_name,
            "restored_beams": len(restored_data.get("available_beams", [])),
            "restored_sessions": len(restored_data.get("cutting_sessions", [])),
            "restore_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Backup restore failed: {e}")
        raise


# ==================== HELPER FUNCTIONS ====================


def _format_cutting_plan_visual(cutting_result: dict) -> str:
    """Create enhanced ASCII visual representation of cutting plan with cut line indicators."""
    try:
        visual_lines = ["CUTTING PLAN VISUALIZATION:", "=" * 40]

        # Calculate summary metrics
        total_efficiency = cutting_result.get("summary", {}).get("material_efficiency_percent", 0)
        total_waste = cutting_result.get("summary", {}).get("total_waste_mm", 0)
        total_cuts = sum(
            len(ba.get("cuts", [])) for ba in cutting_result.get("beam_assignments", [])
        )
        kerf_loss = total_cuts * 3  # 3mm per cut

        for beam_assignment in cutting_result["beam_assignments"]:
            beam_id = beam_assignment["beam_id"]
            original_length = beam_assignment["original_length_mm"]
            remaining_length = beam_assignment["remaining_length_mm"]
            cuts = beam_assignment["cuts"]

            # Create visual bar (scaled to 40 chars max)
            scale = 40 / original_length if original_length > 0 else 0
            used_length = original_length - remaining_length
            used_chars = int(used_length * scale)
            remaining_chars = 40 - used_chars

            bar = "█" * used_chars + "░" * remaining_chars

            # Add unused beam indicator
            unused_indicator = " (unused)" if used_length == 0 else ""
            visual_lines.append(
                f"{beam_id}: [{bar}] {used_length}/{original_length}mm{unused_indicator}"
            )

            # Show cuts with cut line indicators
            if cuts:
                cut_info = " | ".join(
                    [f"{cut['element_id']}({cut['length_mm']}mm)" for cut in cuts]
                )
                visual_lines.append(f"   Cuts: {cut_info}")

            visual_lines.append("")

        # Add summary metrics
        visual_lines.append(
            f"Material Efficiency: {total_efficiency:.1f}% | Total Waste: {total_waste:.0f}mm | Kerf Loss: {kerf_loss}mm ({total_cuts} cuts)"
        )

        return "\n".join(visual_lines)
    except Exception:
        return "Visual representation unavailable"


# Note: Removed hardcoded recommendation and alert functions.
# Material analysis is now handled contextually by the agent using
# the raw data from get_material_status() with project context.


def _generate_design_alternatives(element_lengths: list, beams: list, optimizer) -> list:
    """Generate alternative design suggestions for infeasible designs."""
    alternatives = []

    # Try reducing largest elements
    if element_lengths:
        max_length = max(element_lengths)
        max_available = max((beam.remaining_length_mm for beam in beams), default=0)

        if max_length > max_available:
            reduced_length = max_available - 10  # Account for kerf
            alternatives.append(
                {
                    "type": "reduce_largest_element",
                    "description": (
                        f"Reduce largest element from {max_length}mm to {reduced_length}mm"
                    ),
                    "impact": "Allows design to fit within available material",
                }
            )

    # Try splitting large elements
    large_elements = [length for length in element_lengths if length > 800]
    if large_elements:
        alternatives.append(
            {
                "type": "split_large_elements",
                "description": f"Split {len(large_elements)} large elements into smaller segments",
                "impact": "Better material utilization but may require joining",
            }
        )

    return alternatives


def _generate_feasibility_recommendations(
    feasibility_result: dict, element_lengths: list, beams: list
) -> list:
    """Generate specific recommendations based on feasibility analysis."""
    recommendations = []

    if not feasibility_result["feasible"]:
        if "reason" in feasibility_result:
            if "Insufficient total material" in feasibility_result["reason"]:
                shortage = feasibility_result.get("shortage_mm", 0)
                recommendations.append(f"Need additional {shortage}mm of material")
            elif "Largest element exceeds" in feasibility_result["reason"]:
                max_space = feasibility_result.get("max_beam_space_mm", 0)
                recommendations.append(f"Reduce largest element to max {max_space-3}mm")

    # Efficiency recommendations
    efficiency = feasibility_result.get("efficiency_percent", 0)
    if efficiency < 70:
        recommendations.append("Design has low material efficiency - consider optimization")
    elif efficiency > 95:
        recommendations.append("Excellent material efficiency!")

    return recommendations if recommendations else ["Design appears feasible with current approach"]


def create_syslogic_agent(
    model_name: str = "syslogic",
    monitoring_callback: Optional[Any] = None,
    **kwargs,
) -> CodeAgent:
    """
    Create autonomous SysLogic agent using smolagents managed_agents pattern.

    This creates a structural validation agent that manages its own memory
    and state, following smolagents best practices for autonomous operation.

    Args:
        model_name: Model configuration name from settings
        monitoring_callback: Optional callback for real-time monitoring
        **kwargs: Additional arguments passed to CodeAgent

    Returns:
        CodeAgent configured for managed_agents pattern
    """
    logger.info("🏗️ Creating autonomous SysLogic agent")

    # Get model configuration
    model = ModelProvider.get_model(model_name)

    # Define validation and material tracking tools
    validation_tools = [
        # Structural validation tools
        check_element_connectivity,
        generate_geometry_agent_instructions,
        calculate_closure_correction,
        validate_planar_orientation,
        # NEW Material tracking tools (refactored for clear separation)
        analyze_cutting_plan,  # Planning tool - does NOT modify inventory
        commit_material_usage,  # Execution tool - commits to inventory
        get_material_status,
        reset_material_inventory,
    ]

    # Extract max_steps from kwargs to avoid duplicate parameter error
    max_steps = kwargs.pop("max_steps", 8)  # Allow multiple validation steps

    # Prepare step_callbacks for monitoring
    step_callbacks = kwargs.pop("step_callbacks", [])
    if monitoring_callback:
        step_callbacks.append(monitoring_callback)

    # Remove component_registry from kwargs if present (not supported by CodeAgent)
    kwargs.pop("component_registry", None)

    # Create autonomous CodeAgent for complex structural reasoning
    agent = CodeAgent(
        tools=validation_tools,
        model=model,
        name="syslogic_agent",
        description=(
            "Validates truss structure integrity, checks connectivity, analyzes material usage and inventory, "
            "optimizes cutting plans, tracks material consumption, and provides fix instructions for geometric issues."
        ),
        max_steps=max_steps,
        step_callbacks=step_callbacks,
        additional_authorized_imports=["math", "re", "datetime", "typing"],
        **kwargs,
    )

    # Load and append custom system prompt
    custom_prompt = get_syslogic_system_prompt()
    agent.prompt_templates["system_prompt"] = (
        agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
    )

    # Agent configured for managed_agents pattern with proper name/description in constructor

    logger.info("✅ Created autonomous SysLogic agent configured for managed_agents pattern")
    return agent


def get_syslogic_system_prompt() -> str:
    """Get custom system prompt for SysLogic agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "SysLogic_agent.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")
