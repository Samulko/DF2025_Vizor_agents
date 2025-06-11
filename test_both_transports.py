#!/usr/bin/env python3
"""
Test both HTTP and STDIO transport with direct smolagents integration.
"""

import sys
sys.path.insert(0, 'src')

import os
import time
from smolagents import CodeAgent  
from smolagents.tools import ToolCollection
from bridge_design_system.config.model_config import ModelProvider
from mcp import StdioServerParameters

def test_http_transport():
    """Test HTTP transport if server is available."""
    print("🌐 Testing HTTP Transport...")
    
    try:
        import requests
        # Quick check if HTTP server is available
        response = requests.get("http://localhost:8001/", timeout=2)
        print("✅ HTTP MCP server detected")
    except:
        print("❌ HTTP MCP server not available, skipping HTTP test")
        return False
    
    try:
        # HTTP parameters
        http_params = {
            "url": "http://localhost:8001/mcp",
            "transport": "streamable-http"
        }
        
        print(f"Connecting to: {http_params['url']}")
        
        # Create model
        model = ModelProvider.get_model("geometry")
        
        with ToolCollection.from_mcp(http_params, trust_remote_code=True) as tool_collection:
            print(f"✅ HTTP: Connected with {len(list(tool_collection.tools))} tools")
            
            # Create simple agent
            agent = CodeAgent(
                tools=[*tool_collection.tools],
                model=model,
                add_base_tools=False,
                max_steps=5
            )
            
            # Simple test task
            task = "Create a simple point at coordinates (0, 0, 0) using add_python3_script"
            
            print("Running simple HTTP test task...")
            start_time = time.time()
            result = agent.run(task)
            http_time = time.time() - start_time
            
            print(f"✅ HTTP test completed in {http_time:.2f}s")
            print(f"Result: {str(result)[:200]}...")
            return True
            
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        return False

def test_stdio_transport():
    """Test STDIO transport."""
    print("\n📡 Testing STDIO Transport...")
    
    try:
        # STDIO parameters
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "grasshopper_mcp.bridge"],
            env=None
        )
        
        # Create model
        model = ModelProvider.get_model("geometry")
        
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
            print(f"✅ STDIO: Connected with {len(list(tool_collection.tools))} tools")
            
            # Create simple agent
            agent = CodeAgent(
                tools=[*tool_collection.tools],
                model=model,
                add_base_tools=False,
                max_steps=5
            )
            
            # Simple test task
            task = "Create a simple point at coordinates (1, 1, 1) using add_python3_script"
            
            print("Running simple STDIO test task...")
            start_time = time.time()
            result = agent.run(task)
            stdio_time = time.time() - start_time
            
            print(f"✅ STDIO test completed in {stdio_time:.2f}s")
            print(f"Result: {str(result)[:200]}...")
            return True
            
    except Exception as e:
        print(f"❌ STDIO test failed: {e}")
        return False

def main():
    print("🚀 Testing Both MCP Transports with Direct Smolagents")
    print("=" * 60)
    
    # Test both transports
    http_success = test_http_transport()
    stdio_success = test_stdio_transport()
    
    print("\n📊 Results Summary:")
    print(f"HTTP Transport: {'✅ SUCCESS' if http_success else '❌ FAILED'}")
    print(f"STDIO Transport: {'✅ SUCCESS' if stdio_success else '❌ FAILED'}")
    
    if http_success and stdio_success:
        print("\n🎉 Both transports working! HTTP provides persistent server benefits.")
    elif stdio_success:
        print("\n⚠️  Only STDIO working. Start HTTP server for better performance.")
    else:
        print("\n❌ No transports working. Check server setup.")

if __name__ == "__main__":
    main()