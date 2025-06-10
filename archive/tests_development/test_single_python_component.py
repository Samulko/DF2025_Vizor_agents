#!/usr/bin/env python3
"""Test creating a single Python component to verify cross-thread fix."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_single_python_component():
    """Test creating just one Python component with script."""
    
    print("🧪 Testing Single Python Component Creation")
    print("=" * 60)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import (
            add_python3_script, clear_document
        )
        
        print("✅ Successfully imported sync tools")
        
        # Test 1: Clear document first
        print("\n📍 Test 1: Clear document")
        result = clear_document()
        print(f"Clear result: {result}")
        
        # Test 2: Add ONE Python script component with proper script
        print("\n📍 Test 2: Add single Python script component")
        script_content = """import Rhino.Geometry as rg

# Create a simple circle
circle = rg.Circle(rg.Point3d(0, 0, 0), 5.0)
print("Circle created with radius:", circle.Radius)

# Output the circle
a = circle"""
        
        print("Creating Python3 script component...")
        result = add_python3_script(150, 150, script_content, "Test Circle")
        print(f"Result: {result}")
        
        print("\n✅ Single component test completed!")
        print("📋 Expected behavior:")
        print("  - NO cross-thread exceptions")
        print("  - NO script editor popups")
        print("  - Component created with script content")
        print("  - Component displays 'Py3' nickname")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Single Python Component Creation")
    print("Make sure the manual MCP server is running on port 8001")
    print("This test creates only ONE component to verify fixes")
    print()
    
    test_single_python_component()
    
    print("\n🎉 Test complete!")
    print("Check Grasshopper for the single Python component")