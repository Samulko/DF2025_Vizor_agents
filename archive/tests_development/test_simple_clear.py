#!/usr/bin/env python3
"""Test just the clear document operation to verify threading fix."""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_clear():
    """Test just clearing the document."""
    
    print("🧪 Testing Simple Clear Document")
    print("=" * 60)
    
    try:
        from bridge_design_system.mcp.sync_mcp_tools import clear_document
        
        print("✅ Successfully imported clear_document")
        
        # Test: Clear document
        print("\n📍 Testing clear document (should NOT timeout)")
        print("Starting clear operation...")
        
        result = clear_document()
        print(f"Clear result: {result}")
        
        if "timed out" in result:
            print("❌ Still timing out - threading issue not resolved")
        elif "Failed" in result:
            print(f"⚠️ Operation failed but didn't timeout: {result}")
        else:
            print("✅ Clear operation completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Simple Clear Operation")
    print("Make sure the manual MCP server is running on port 8001")
    print("This test only does a clear operation to verify threading fixes")
    print()
    
    test_simple_clear()
    
    print("\n🎉 Test complete!")