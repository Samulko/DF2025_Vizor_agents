"""
Simple Balance Tools - Two Point Load System

This module provides simple tools for parsing beam code into loads and solving
the classic two-point balance problem: given existing loads, find the weight
and position for a new load to achieve balance.
"""

import re
import json
import math
from typing import Dict, List, Any
from smolagents import tool

# Physics constants
DEFAULT_DENSITY = 600.0  # kg/m³ for wood
DEFAULT_WIDTH = 0.05     # m
DEFAULT_HEIGHT = 0.05    # m


@tool
def parse_code_to_loads(python_code: str, density: float = 600.0) -> str:
    """
    Parse beam Python code into simple loads (weight at position).
    
    Converts complex beam geometry to simple: Load1(weight, x, y) + Load2(weight, x, y) = ?
    This is the classic beam balance problem where you know existing loads and need to find a new one.
    
    Args:
        python_code: Raw Python script containing beam definitions
        density: Material density in kg/m³ (default: 600 for wood)
        
    Returns:
        JSON string with existing loads and what's needed to balance
    """
    # Pattern to match beam definitions
    center_pattern = r'center(\d+)\s*=\s*rg\.Point3d\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)'
    length_pattern = r'length(\d+)\s*=\s*([\d.]+)'
    beam_pattern = r'beam(\d+)\s*=\s*AssemblyElement\([^)]*id\s*=\s*"(\d+)"[^)]*type\s*=\s*"([^"]+)"'
    
    # Extract beam data
    centers = {match[0]: [float(match[1]), float(match[2]), float(match[3])] 
              for match in re.findall(center_pattern, python_code)}
    lengths = {match[0]: float(match[1]) 
              for match in re.findall(length_pattern, python_code)}
    beam_info = {match[0]: {"id": match[1], "type": match[2]} 
                for match in re.findall(beam_pattern, python_code)}
    
    # Convert to loads
    loads = []
    total_moment_x = 0.0
    total_moment_y = 0.0
    
    for beam_num in centers.keys():
        if beam_num in lengths and beam_num in beam_info:
            # Calculate weight from volume
            volume = lengths[beam_num] * DEFAULT_WIDTH * DEFAULT_HEIGHT
            weight = density * volume
            
            # Position (distance from origin/pivot)
            x_pos = centers[beam_num][0]
            y_pos = centers[beam_num][1]
            
            # Moments (weight × distance)
            moment_x = weight * y_pos
            moment_y = weight * x_pos
            
            total_moment_x += moment_x
            total_moment_y += moment_y
            
            loads.append({
                "beam_id": beam_info[beam_num]["id"],
                "weight": round(weight, 3),
                "x_position": round(x_pos, 3),
                "y_position": round(y_pos, 3),
                "moments": {
                    "x": round(moment_x, 3),
                    "y": round(moment_y, 3)
                }
            })
    
    result = {
        "existing_loads": loads,
        "current_state": {
            "total_loads": len(loads),
            "net_moments": {
                "x": round(total_moment_x, 3),
                "y": round(total_moment_y, 3)
            },
            "is_balanced": abs(total_moment_x) < 0.001 and abs(total_moment_y) < 0.001
        },
        "to_balance": {
            "need_moment_x": round(-total_moment_x, 3),
            "need_moment_y": round(-total_moment_y, 3),
            "explanation": "New load must create these moments to achieve balance"
        }
    }
    
    return json.dumps(result, indent=2)


@tool
def solve_balance_load(existing_loads_json: str, max_distance: float = 0.3, beam_length_constraint: float = 0.4) -> str:
    """
    Solve for new load placement given existing loads and constraints.
    
    Classic scenario: existing beams create imbalance, need to place new beam to balance.
    The new beam must sit within constraints (distance from center, beam length).
    
    Args:
        existing_loads_json: JSON from parse_code_to_loads
        max_distance: Maximum distance new load can be from center (default: 0.3m)  
        beam_length_constraint: Length of beam new load sits on (default: 0.4m)
        
    Returns:
        JSON with new load weight and position for balance
    """
    try:
        data = json.loads(existing_loads_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})
    
    # Get required moments to balance
    to_balance = data.get("to_balance", {})
    req_moment_x = to_balance.get("need_moment_x", 0)
    req_moment_y = to_balance.get("need_moment_y", 0)
    
    # If already balanced
    if abs(req_moment_x) < 0.001 and abs(req_moment_y) < 0.001:
        return json.dumps({
            "result": "System is already balanced",
            "action": "No new load needed"
        })
    
    # Try different weights and find feasible positions
    feasible_solutions = []
    test_weights = [0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]
    
    for weight in test_weights:
        # Calculate required position: moment = weight × distance
        # So: distance = moment / weight
        
        if abs(weight) < 0.001:
            continue
            
        # Required positions
        y_pos = req_moment_x / weight if abs(req_moment_x) > 0.001 else 0.0
        x_pos = req_moment_y / weight if abs(req_moment_y) > 0.001 else 0.0
        
        # Check constraints
        distance_from_center = math.sqrt(x_pos**2 + y_pos**2)
        fits_on_beam = abs(x_pos) <= beam_length_constraint/2 and abs(y_pos) <= beam_length_constraint/2
        within_max_distance = distance_from_center <= max_distance
        
        if fits_on_beam and within_max_distance:
            # Calculate beam length needed for this weight
            volume_needed = weight / DEFAULT_DENSITY
            beam_length_needed = volume_needed / (DEFAULT_WIDTH * DEFAULT_HEIGHT)
            
            feasible_solutions.append({
                "weight": round(weight, 3),
                "position": {
                    "x": round(x_pos, 3),
                    "y": round(y_pos, 3)
                },
                "distance_from_center": round(distance_from_center, 3),
                "beam_length_needed": round(beam_length_needed, 3),
                "verification": {
                    "moment_x_created": round(weight * y_pos, 3),
                    "moment_y_created": round(weight * x_pos, 3),
                    "balances_required": {
                        "x": abs(weight * y_pos - req_moment_x) < 0.001,
                        "y": abs(weight * x_pos - req_moment_y) < 0.001
                    }
                }
            })
    
    if feasible_solutions:
        # Choose lightest solution
        best = min(feasible_solutions, key=lambda s: s["weight"])
        
        result = {
            "solution_found": True,
            "recommended_load": best,
            "explanation": f"Place {best['weight']} kg load at position ({best['position']['x']}, {best['position']['y']})",
            "constraints_met": {
                "within_max_distance": best["distance_from_center"] <= max_distance,
                "fits_on_beam": True,
                "beam_length_needed": f"{best['beam_length_needed']}m"
            },
            "alternatives": feasible_solutions[:3]  # Show top 3
        }
    else:
        # No feasible solution
        result = {
            "solution_found": False,
            "problem": "No solution within constraints",
            "suggestions": {
                "try_larger_max_distance": max_distance * 1.5,
                "or_longer_support_beam": beam_length_constraint * 1.5,
                "required_moments": {
                    "x": req_moment_x,
                    "y": req_moment_y
                }
            }
        }
    
    return json.dumps(result, indent=2)


@tool
def check_balance_feasibility(weight: float, distance: float, required_moment: float) -> str:
    """
    Simple check: can this weight at this distance create the required moment?
    
    Basic equation: weight × distance = moment
    
    Args:
        weight: Weight of the load in kg
        distance: Distance from pivot in meters  
        required_moment: Required moment in kg⋅m
        
    Returns:
        JSON with feasibility check and recommendations
    """
    created_moment = weight * distance
    error = abs(created_moment - required_moment)
    is_feasible = error < 0.001
    
    result = {
        "equation": f"{weight} kg × {distance} m = {round(created_moment, 3)} kg⋅m",
        "required_moment": required_moment,
        "created_moment": round(created_moment, 3),
        "error": round(error, 3),
        "is_feasible": is_feasible
    }
    
    if not is_feasible:
        if abs(required_moment) > 0.001:
            correct_weight = required_moment / distance if abs(distance) > 0.001 else float('inf')
            correct_distance = required_moment / weight if abs(weight) > 0.001 else float('inf')
            
            result["corrections"] = {
                "keep_distance_change_weight_to": round(correct_weight, 3) if correct_weight != float('inf') else "impossible",
                "keep_weight_change_distance_to": round(correct_distance, 3) if correct_distance != float('inf') else "impossible"
            }
    
    return json.dumps(result, indent=2)