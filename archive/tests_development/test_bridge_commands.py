#!/usr/bin/env python3
"""Test what commands the Grasshopper bridge actually supports."""
import sys
import os
import httpx

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_bridge_status():
    """Check what the bridge knows about."""
    
    print("🔍 Checking Grasshopper Bridge Status")
    print("=" * 50)
    
    try:
        # Check bridge status
        response = httpx.get("http://localhost:8001/grasshopper/status", timeout=5.0)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bridge status:")
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Bridge status check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Bridge status error: {e}")

def test_basic_commands():
    """Test basic commands that we know work."""
    
    print("\n🧪 Testing Basic Commands")
    print("=" * 50)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import (
            clear_document, add_component, get_all_components
        )
        
        # Test 1: Clear document (we know this works)
        print("📍 Test 1: Clear document")
        result = clear_document()
        print(f"Clear result: {'✅ SUCCESS' if 'Successfully' in result else '❌ FAILED'}")
        
        # Test 2: Add basic component (we know this works)
        print("\n📍 Test 2: Add basic point component")
        result = add_component("point", 100, 100)
        print(f"Add point result: {'✅ SUCCESS' if 'Successfully' in result else '❌ FAILED'}")
        
        # Test 3: Get all components (we know this works)
        print("\n📍 Test 3: Get basic components list")
        result = get_all_components()
        print(f"Get components result: {'✅ SUCCESS' if 'Successfully' in result else '❌ FAILED'}")
        
        # Test 4: Try adding a Python component WITHOUT script parameter
        print("\n📍 Test 4: Add Python component (type 'Py3' without script)")
        result = add_component("Py3", 200, 100)
        print(f"Add Py3 result: {'✅ SUCCESS' if 'Successfully' in result else '❌ FAILED'}")
        print(f"Full result: {result}")
        
    except Exception as e:
        print(f"❌ Basic commands test failed: {e}")
        import traceback
        traceback.print_exc()

def test_python_component_creation():
    """Test different ways to create Python components."""
    
    print("\n🐍 Testing Python Component Creation Methods")
    print("=" * 60)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import SyncMCPClient
        
        client = SyncMCPClient("http://localhost:8001/mcp/")
        client.connect()
        
        # Method 1: Try standard component creation with Py3 type
        print("📍 Method 1: Standard component creation")
        result = client.call_tool("add_component", {
            "component_type": "Py3",
            "x": 300,
            "y": 100
        })
        print(f"Method 1 result: {result}")
        
        # Method 2: Try with script parameter
        print("\n📍 Method 2: With script parameter")
        result = client.call_tool("add_component", {
            "component_type": "Py3",
            "x": 400,
            "y": 100,
            "script": "# Test script\na = 'Hello World'"
        })
        print(f"Method 2 result: {result}")
        
        # Method 3: Try other Python component names
        print("\n📍 Method 3: Try 'Python Script' as type")
        result = client.call_tool("add_component", {
            "component_type": "Python Script",
            "x": 500,
            "y": 100
        })
        print(f"Method 3 result: {result}")
        
    except Exception as e:
        print(f"❌ Python component test failed: {e}")
        import traceback
        traceback.print_exc()

def analyze_timeout_issue():
    """Analyze why commands are timing out."""
    
    print("\n🔍 Analyzing Timeout Issue")
    print("=" * 50)
    
    print("Based on the timeout behavior, the likely issues are:")
    print()
    print("1. **Missing C# Implementations in SimpleMCPBridge:**")
    print("   The following commands are NOT implemented in the Grasshopper bridge:")
    print("   ❌ get_python_script_content")
    print("   ❌ set_python_script_content")
    print("   ❌ get_python_script_errors")
    print("   ❌ get_document_info")
    print()
    print("2. **Script Parameter Not Supported:**")
    print("   The 'script' parameter in add_component might not be handled")
    print("   for Py3 components in the current bridge implementation.")
    print()
    print("3. **Bridge Mode Limitations:**")
    print("   The SimpleMCPBridge polls for commands but may only support")
    print("   basic operations like add_component, connect_components, etc.")
    print()
    print("📋 TO FIX THIS, YOU NEED TO:")
    print("1. Update the C# SimpleMCPBridge component to handle:")
    print("   - get_python_script_content command")
    print("   - set_python_script_content command") 
    print("   - get_python_script_errors command")
    print("   - get_document_info command")
    print("   - 'script' parameter in add_component for Py3 type")
    print()
    print("2. Or use the reference MCP implementation that already has these features")

if __name__ == "__main__":
    print("🚀 Grasshopper Bridge Command Analysis")
    print("Make sure the manual MCP server is running on port 8001")
    print()
    
    # Check bridge status
    test_bridge_status()
    
    # Test basic commands
    test_basic_commands()
    
    # Test Python component creation
    test_python_component_creation()
    
    # Analyze the issue
    analyze_timeout_issue()
    
    print("\n📋 SUMMARY:")
    print("The Python script tools are timing out because the SimpleMCPBridge")
    print("component doesn't implement the required C# methods. You need to either:")
    print("1. Extend the SimpleMCPBridge with these Python script methods, OR")
    print("2. Use the full reference MCP implementation that already supports them")