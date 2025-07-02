"""
Material Agent for Shape Analysis

This agent processes the found material catalog and determines the geometric shapes
of objects based on their vertex data. It uses mathematical analysis rather than
external tools to classify shapes.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple

from smolagents import CodeAgent, tool
from ..config.model_config import ModelProvider


# =============================================================================
# STEP 1: CREATE SHAPE ANALYSIS TOOLS
# These tools help the agent analyze geometric properties
# =============================================================================


@tool
def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    Calculate Euclidean distance between two 2D points.

    Args:
        point1: First point as [x, y]
        point2: Second point as [x, y]

    Returns:
        Distance between the points
    """
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)


@tool
def calculate_angles(vertices: List[List[float]]) -> List[float]:
    """
    Calculate angles between consecutive edges in a polygon.

    Args:
        vertices: List of vertex coordinates [[x1, y1], [x2, y2], ...]

    Returns:
        List of angles in degrees
    """
    if len(vertices) < 3:
        return []
    
    angles = []
    n = len(vertices)
    
    for i in range(n):
        # Get three consecutive vertices
        prev = vertices[i]
        curr = vertices[(i + 1) % n]
        next_vert = vertices[(i + 2) % n]
        
        # Calculate vectors
        v1 = [curr[0] - prev[0], curr[1] - prev[1]]
        v2 = [next_vert[0] - curr[0], next_vert[1] - curr[1]]
        
        # Calculate dot product
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        
        # Calculate magnitudes
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        # Calculate angle
        if mag1 > 0 and mag2 > 0:
            cos_angle = dot_product / (mag1 * mag2)
            cos_angle = max(-1, min(1, cos_angle))  # Clamp to valid range
            angle = math.degrees(math.acos(cos_angle))
            angles.append(angle)
        else:
            angles.append(0)
    
    return angles


@tool
def save_categorized_data(categorized_objects: Dict[str, Any], filename: str = "material_categories.json") -> str:
    """
    Save categorized material data to a JSON file.

    Args:
        categorized_objects: Dictionary containing categorized objects
        filename: Name of the output file

    Returns:
        Confirmation message with file path
    """
    try:
        # Get the data directory path
        current_file = Path(__file__)
        data_dir = current_file.parent.parent / "data"
        output_path = data_dir / filename
        
        # Save the data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(categorized_objects, f, indent=2, ensure_ascii=False)
        
        return f"✅ Categorized data saved to: {output_path}"

    except Exception as e:
        return f"❌ Error saving data: {str(e)}"


# =============================================================================
# STEP 2: CREATE THE MATERIAL AGENT
# This agent analyzes geometric shapes from material catalog
# =============================================================================


def create_material_agent(tools: List = None, model_name: str = "default") -> CodeAgent:
    """
    Create a material agent for shape analysis.

    This agent processes material catalog data and determines geometric shapes
    using mathematical analysis rather than external tools.

    Args:
        tools: List of tools for the agent (optional)
        model_name: Name of the model to use

        Returns:
        A configured CodeAgent ready for material analysis
    """
    # Get the AI model
    model = ModelProvider.get_model(model_name)

    # Prepare the tools
    default_tools = [calculate_distance, calculate_angles, save_categorized_data]
    agent_tools = tools or default_tools

    # Create the agent
    agent = CodeAgent(
        tools=agent_tools,
        model=model,
        max_steps=15,  # More steps for complex shape analysis
        additional_authorized_imports=["math", "json", "pathlib", "typing"],
        name="material_agent",
        description="Analyzes geometric shapes from material catalog data using mathematical analysis",
    )

    return agent


# =============================================================================
# STEP 3: SHAPE ANALYSIS FUNCTIONS
# Helper functions for shape classification
# =============================================================================


def load_material_catalog() -> Dict[str, Any]:
    """
    Load the found material catalog from JSON file.

    Returns:
        Dictionary containing the material catalog data
    """
    current_file = Path(__file__)
    data_dir = current_file.parent.parent / "data"
    catalog_path = data_dir / "found_material_catalog.json"
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_triangle_shape(vertices: List[List[float]]) -> str:
    """
    Analyze a triangle and determine its type based on angles and sides.

    Args:
        vertices: List of 3 vertex coordinates

    Returns:
        String describing the triangle type
    """
    if len(vertices) != 3:
        return "invalid_triangle"
    
    # Calculate side lengths
    sides = []
    for i in range(3):
        next_i = (i + 1) % 3
        side = calculate_distance(vertices[i], vertices[next_i])
        sides.append(side)
    
    # Calculate angles
    angles = calculate_angles(vertices)
    
    # Classify triangle
    if any(angle > 90 for angle in angles):
        return "obtuse_triangle"
    elif any(abs(angle - 90) < 1 for angle in angles):
        return "right_triangle"
    elif all(abs(angle - 60) < 1 for angle in angles):
        return "equilateral_triangle"
    elif len(set(round(side, 3) for side in sides)) == 1:
        return "equilateral_triangle"
    elif len(set(round(side, 3) for side in sides)) == 2:
        return "isosceles_triangle"
    else:
        return "scalene_triangle"


def categorize_materials(catalog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorize materials based on their geometric properties.

    Args:
        catalog_data: Material catalog data

    Returns:
        Dictionary with categorized materials
    """
    categorized = {
        "triangles": [],
        "other_shapes": [],
        "statistics": {
            "total_objects": 0,
            "triangle_count": 0,
            "shape_types": {}
        }
    }
    
    for item in catalog_data.get("catalog", []):
        object_id = item["id"]
        vertices = item["vertices"]
        
        categorized["statistics"]["total_objects"] += 1
        
        # Analyze based on vertex count
        if len(vertices) == 3:
            shape_type = analyze_triangle_shape(vertices)
            categorized["triangles"].append({
                "id": object_id,
                "vertices": vertices,
                "shape_type": shape_type,
                "original_tags": item.get("tags", [])
            })
            categorized["statistics"]["triangle_count"] += 1
            
            # Update shape type statistics
            if shape_type not in categorized["statistics"]["shape_types"]:
                categorized["statistics"]["shape_types"][shape_type] = 0
            categorized["statistics"]["shape_types"][shape_type] += 1
        else:
            categorized["other_shapes"].append({
                "id": object_id,
                "vertices": vertices,
                "vertex_count": len(vertices),
                "original_tags": item.get("tags", [])
            })
    
    return categorized


# =============================================================================
# STEP 4: DEMO FUNCTION
# Test the material agent functionality
# =============================================================================


def demo_material_agent():
    """
    Demonstrates the material agent's shape analysis capabilities.

    This function:
    1. Loads the material catalog
    2. Creates the material agent
    3. Analyzes shapes and categorizes materials
    4. Saves the results
    """
    print("🔍 Starting Material Agent Demonstration...")
    print("=" * 50)

    try:
        # Step 1: Load material catalog
        print("📂 Loading material catalog...")
        catalog_data = load_material_catalog()
        print(f"✅ Loaded {len(catalog_data['catalog'])} objects from catalog")

        # Step 2: Create the material agent
        print("\n🤖 Creating material agent...")
        agent = create_material_agent()
        print(f"✅ Agent created: {agent.name}")
        print(f"✅ Available tools: {len(agent.tools)}")

        # Step 3: Analyze and categorize materials
        print("\n🔍 Analyzing geometric shapes...")
        categorized_data = categorize_materials(catalog_data)
        
        print(f"📊 Analysis Results:")
        print(f"   - Total objects: {categorized_data['statistics']['total_objects']}")
        print(f"   - Triangles: {categorized_data['statistics']['triangle_count']}")
        print(f"   - Other shapes: {len(categorized_data['other_shapes'])}")
        
        if categorized_data['statistics']['shape_types']:
            print(f"   - Triangle types found:")
            for shape_type, count in categorized_data['statistics']['shape_types'].items():
                print(f"     * {shape_type}: {count}")

        # Step 4: Use agent to save the categorized data
        print("\n💾 Saving categorized data...")
        result = agent.run(
            f"Save the following categorized material data to a file named 'material_categories.json': {categorized_data}"
        )
        print(f"✅ {result}")

        # Step 5: Demonstrate agent's analytical capabilities
        print("\n🧠 Testing agent's shape analysis capabilities...")
        analysis_task = """
        Analyze the geometric properties of the material catalog objects. 
        For each triangle, determine:
        1. Side lengths
        2. Angles
        3. Shape classification (equilateral, isosceles, scalene, right, obtuse)
        4. Any special geometric properties
        
        Provide a detailed analysis of the first 3 objects in the catalog.
        """
        
        analysis_result = agent.run(analysis_task)
        print("📋 Agent Analysis:")
        print(analysis_result)

        print("\n" + "=" * 50)
        print("✅ Material Agent Demonstration Completed Successfully!")
        print("=" * 50)

        return agent, categorized_data
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        raise


# =============================================================================
# QUICK START FOR STUDENTS
# =============================================================================

if __name__ == "__main__":
    """
    Students can run this file directly to see the material agent working.

    To use in workshop:
    1. Run: python material_agent.py
    2. See the material agent analyze shapes
    3. Check the generated material_categories.json file
    4. Modify the analysis functions for different shape types
    """
    print("=" * 50)
    print("MATERIAL AGENT - SHAPE ANALYSIS")
    print("=" * 50)

    # Run the demonstration
    agent, categorized_data = demo_material_agent()

    print("\n" + "=" * 50)
    print("NEXT STEPS FOR STUDENTS:")
    print("=" * 50)
    print("1. Check the generated material_categories.json file")
    print("2. Add analysis for other geometric shapes (quadrilaterals, polygons)")
    print("3. Implement more sophisticated shape classification algorithms")
    print("4. Add material properties analysis (area, perimeter, etc.)")
    print("5. Create visualization tools for the categorized shapes")
    print("\nHappy analyzing! 🔍")
