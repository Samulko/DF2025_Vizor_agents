#!/usr/bin/env python3
"""
Simple test to understand the correct ToolCollection.from_mcp() usage.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_simple_toolcollection():
    """Test basic ToolCollection.from_mcp() usage."""
    print("🧪 Testing Simple ToolCollection.from_mcp()")
    
    try:
        from smolagents import ToolCollection
        
        mcp_server_url = "http://localhost:8001/mcp"
        print(f"📡 Connecting to: {mcp_server_url}")
        
        # Try the context manager approach
        print("🔧 Using context manager...")
        with ToolCollection.from_mcp({
            "url": mcp_server_url, 
            "transport": "streamable-http"
        }, trust_remote_code=True) as tool_collection:
            
            print(f"✅ Connected! Type: {type(tool_collection)}")
            print(f"🛠️  Tools available: {hasattr(tool_collection, 'tools')}")
            
            if hasattr(tool_collection, 'tools'):
                print(f"📊 Number of tools: {len(tool_collection.tools)}")
                tool_names = [tool.name for tool in tool_collection.tools]
                print(f"📋 Tool names: {tool_names}")
            else:
                print("❌ No 'tools' attribute found")
                print(f"🔍 Available attributes: {dir(tool_collection)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_usage():
    """Test direct usage without context manager."""
    print("\n🧪 Testing Direct Usage")
    
    try:
        from smolagents import ToolCollection
        
        mcp_server_url = "http://localhost:8001/mcp"
        print(f"📡 Connecting to: {mcp_server_url}")
        
        # Try direct usage
        tool_collection = ToolCollection.from_mcp({
            "url": mcp_server_url, 
            "transport": "streamable-http"
        }, trust_remote_code=True)
        
        print(f"✅ Created! Type: {type(tool_collection)}")
        print(f"🔍 Attributes: {dir(tool_collection)}")
        
        # Try to enter the context manually
        if hasattr(tool_collection, '__enter__'):
            print("🔧 Entering context manually...")
            actual_collection = tool_collection.__enter__()
            print(f"📊 Actual collection type: {type(actual_collection)}")
            
            if hasattr(actual_collection, 'tools'):
                print(f"🛠️  Number of tools: {len(actual_collection.tools)}")
                tool_names = [tool.name for tool in actual_collection.tools]
                print(f"📋 Tool names: {tool_names}")
            
            # Clean up
            tool_collection.__exit__(None, None, None)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple tests."""
    print("🎯 Simple ToolCollection Tests")
    print("="*50)
    
    test1 = test_simple_toolcollection()
    test2 = test_direct_usage()
    
    print(f"\n📊 Results:")
    print(f"Context manager: {'✅' if test1 else '❌'}")
    print(f"Direct usage: {'✅' if test2 else '❌'}")

if __name__ == "__main__":
    main()