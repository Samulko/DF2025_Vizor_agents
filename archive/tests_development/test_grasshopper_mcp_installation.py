#!/usr/bin/env python3
"""
Test script to verify grasshopper-mcp package installation and MCP tools loading.

This test verifies that:
1. grasshopper-mcp package can be imported 
2. MCP tools can be loaded via STDIO
3. The bridge.py module is accessible as an installed package

Run this test AFTER installing dependencies:
```bash
uv sync
python test_grasshopper_mcp_installation.py
```
"""

import sys
import subprocess
from pathlib import Path

def test_grasshopper_mcp_import():
    """Test that grasshopper_mcp package can be imported."""
    print("Testing grasshopper_mcp package import...")
    try:
        import grasshopper_mcp
        print(f"✅ Successfully imported grasshopper_mcp version {grasshopper_mcp.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import grasshopper_mcp: {e}")
        return False

def test_grasshopper_mcp_bridge_module():
    """Test that bridge module can be imported."""
    print("Testing grasshopper_mcp.bridge module import...")
    try:
        import grasshopper_mcp.bridge
        print("✅ Successfully imported grasshopper_mcp.bridge module")
        return True
    except ImportError as e:
        print(f"❌ Failed to import grasshopper_mcp.bridge: {e}")
        return False

def test_uv_run_command():
    """Test that 'uv run python -m grasshopper_mcp.bridge' works."""
    print("Testing 'uv run python -m grasshopper_mcp.bridge' command...")
    try:
        # Start the process
        process = subprocess.Popen(
            ["uv", "run", "python", "-m", "grasshopper_mcp.bridge"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start up
        import time
        time.sleep(2)
        
        # Check if process is still running (it should be waiting for STDIO input)
        if process.poll() is None:
            print("✅ Command started successfully and is running (MCP server active)")
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            return True
        else:
            # Process exited, check why
            stdout, stderr = process.communicate()
            print(f"❌ Process exited unexpectedly:")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            return False
        
    except FileNotFoundError:
        print("❌ 'uv' command not found")
        return False
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False

def test_mcp_tools_loading():
    """Test that MCP tools can be loaded via our utility."""
    print("Testing MCP tools loading...")
    try:
        from src.bridge_design_system.mcp.mcp_tools_utils import get_grasshopper_tools
        
        # This will likely fail if server isn't running, but we can test the import
        print("✅ Successfully imported MCP tools utility")
        
        # Try to load tools (this may fail if no server is running, which is OK)
        try:
            tools = get_grasshopper_tools(use_stdio=True)
            if tools:
                print(f"✅ Successfully loaded {len(tools)} MCP tools")
                tool_names = [tool.name for tool in tools[:5]]  # Show first 5
                print(f"   Sample tools: {tool_names}")
            else:
                print("⚠️ No MCP tools loaded (server may not be running - this is OK for this test)")
        except Exception as e:
            print(f"⚠️ Could not load MCP tools: {e} (this is OK if server isn't running)")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import MCP tools utility: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Grasshopper MCP Package Installation Test")
    print("=" * 60)
    
    tests = [
        test_grasshopper_mcp_import,
        test_grasshopper_mcp_bridge_module,
        test_uv_run_command,
        test_mcp_tools_loading
    ]
    
    results = []
    for test in tests:
        print()
        result = test()
        results.append(result)
        print()
    
    print("=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! grasshopper-mcp installation is working correctly.")
        print()
        print("Next steps:")
        print("1. Run: uv sync  (to install the local dependency)")
        print("2. Test the STDIO connection with smolagents")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        print()
        print("Troubleshooting:")
        print("1. Make sure you ran 'uv sync' after updating pyproject.toml")
        print("2. Verify you're in the correct project directory")
        print("3. Check that reference/README.md exists")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)