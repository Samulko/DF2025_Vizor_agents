#!/usr/bin/env python3
"""Test the Python script tools with the manual MCP server."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_python_script_tools():
    """Test the Python script tools."""
    
    print("🧪 Testing Python Script Tools")
    print("=" * 60)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import (
            add_python3_script, get_python3_script, edit_python3_script,
            get_python3_script_errors, get_all_components_enhanced, clear_document
        )
        
        print("✅ Successfully imported Python script tools")
        
        # Test 1: Clear document first
        print("\n📍 Test 1: Clear document")
        result = clear_document()
        print(f"Clear result: {result}")
        
        # Test 2: Add a Python script component with a simple script
        print("\n📍 Test 2: Add Python script component")
        script_content = """import Rhino.Geometry as rg

# Create a circle at origin with radius 5
circle = rg.Circle(rg.Point3d(0,0,0), 5)
a = circle"""
        
        result = add_python3_script(100, 100, script_content, "Circle Generator")
        print(f"Add Python script result: {result}")
        
        # Extract component ID if successful
        component_id = None
        if "Successfully added Python script component" in result:
            # Try to extract ID from result
            import re
            match = re.search(r"'component_id':\s*'([^']+)'", result)
            if match:
                component_id = match.group(1)
                print(f"Extracted component ID: {component_id}")
        
        # Test 3: Add another Python script with more complex code
        print("\n📍 Test 3: Add complex Python script")
        complex_script = """import Rhino.Geometry as rg
import math

# Create a spiral of points
points = []
for i in range(100):
    t = i * 0.1
    x = math.cos(t) * t
    y = math.sin(t) * t
    z = t * 0.5
    points.append(rg.Point3d(x, y, z))

# Create interpolated curve
spiral = rg.Curve.CreateInterpolatedCurve(points, 3)
a = spiral"""
        
        result2 = add_python3_script(300, 100, complex_script, "Spiral Generator")
        print(f"Add complex script result: {result2}")
        
        # Test 4: Get all components enhanced
        print("\n📍 Test 4: Get all components enhanced")
        result = get_all_components_enhanced()
        print(f"Enhanced components result: {result}")
        
        # Test 5: If we have a component ID, test reading the script
        if component_id:
            print(f"\n📍 Test 5: Get Python script content for ID: {component_id}")
            result = get_python3_script(component_id)
            print(f"Get script result: {result}")
            
            # Test 6: Edit the script
            print(f"\n📍 Test 6: Edit Python script for ID: {component_id}")
            edited_script = """import Rhino.Geometry as rg

# Create a larger circle at origin with radius 10
circle = rg.Circle(rg.Point3d(0,0,0), 10)
a = circle"""
            
            result = edit_python3_script(component_id, edited_script)
            print(f"Edit script result: {result}")
            
            # Test 7: Check for errors
            print(f"\n📍 Test 7: Get Python script errors for ID: {component_id}")
            result = get_python3_script_errors(component_id)
            print(f"Script errors result: {result}")
        
        # Test 8: Add a script with intentional error
        print("\n📍 Test 8: Add script with error to test error handling")
        error_script = """import Rhino.Geometry as rg

# This will cause an error - undefined variable
circle = rg.Circle(rg.Point3d(0,0,0), undefined_radius)
a = circle"""
        
        result = add_python3_script(500, 100, error_script, "Error Test")
        print(f"Add error script result: {result}")
        
        print("\n✅ All Python script tool tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_parametric_script():
    """Test creating a parametric Python script."""
    
    print("\n🧪 Testing Parametric Python Script")
    print("=" * 60)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import add_python3_script
        
        # Create a parametric script that uses input variables
        parametric_script = """import Rhino.Geometry as rg
import math

# Parametric box spiral
# These would be input parameters in a real parametric component
num_boxes = 50
spiral_turns = 3
radius_growth = 0.2
box_size = 0.5
vertical_spacing = 0.1

boxes = []

for i in range(num_boxes):
    t = (i / float(num_boxes)) * spiral_turns * 2 * math.pi
    radius = radius_growth * t
    
    x = math.cos(t) * radius
    y = math.sin(t) * radius
    z = i * vertical_spacing
    
    center = rg.Point3d(x, y, z)
    interval = rg.Interval(-box_size/2, box_size/2)
    box = rg.Box(rg.Plane(center, rg.Vector3d.ZAxis), interval, interval, interval)
    
    boxes.append(box)

a = boxes"""
        
        result = add_python3_script(200, 300, parametric_script, "Parametric Box Spiral")
        print(f"Parametric script result: {result}")
        
        print("\n💡 Note: To make this truly parametric, you would need to:")
        print("1. Add input parameters to the component in Grasshopper")
        print("2. Connect sliders or other inputs to those parameters")
        print("3. Reference the parameters by name in the script")
        
    except Exception as e:
        print(f"❌ Parametric test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Python Script Tools Tests")
    print("Make sure the manual MCP server is running on port 8001")
    print()
    
    # Test basic Python script tools
    test_python_script_tools()
    
    # Test parametric script creation
    test_parametric_script()
    
    print("\n🎉 Testing complete!")
    print("Check your Grasshopper canvas for the created Python components")