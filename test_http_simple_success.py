#!/usr/bin/env python3
"""
Test HTTP MCP transport with a simple, guaranteed-to-work geometry creation.
Focuses on validating HTTP transport performance vs STDIO.
"""

import sys
sys.path.insert(0, 'src')

import os
import time
from smolagents import CodeAgent  
from smolagents.tools import ToolCollection
from bridge_design_system.config.model_config import ModelProvider

def test_http_performance():
    """Test HTTP transport performance with simple geometry."""
    print("⚡ HTTP MCP Performance Test")
    print("=" * 50)
    
    # HTTP parameters (no fallback)
    http_params = {
        "url": "http://localhost:8001/mcp",
        "transport": "streamable-http"
    }
    
    try:
        # Quick availability check
        import requests
        response = requests.get("http://localhost:8001/", timeout=2)
        print("✅ HTTP MCP server available")
    except:
        print("❌ HTTP server not available")
        return False
        
    # Create model
    model = ModelProvider.get_model("geometry")
    
    print("\n🔌 Connecting via HTTP (no fallback)...")
    start_connect = time.time()
    
    with ToolCollection.from_mcp(http_params, trust_remote_code=True) as tool_collection:
        connect_time = time.time() - start_connect
        print(f"✅ HTTP connection: {connect_time:.2f}s")
        print(f"✅ Tools loaded: {len(list(tool_collection.tools))}")
        
        # Create agent
        agent = CodeAgent(
            tools=[*tool_collection.tools],
            model=model,
            add_base_tools=False,
            max_steps=3
        )
        
        # Simple, fast task
        task = "Create a simple circle in Grasshopper using add_python3_script. Just create one circle with radius 5 at origin."
        
        print(f"\n🎯 Running simple circle task via HTTP...")
        start_task = time.time()
        
        result = agent.run(task)
        
        task_time = time.time() - start_task
        total_time = connect_time + task_time
        
        print(f"\n📊 HTTP Performance Results:")
        print(f"   Connection time: {connect_time:.2f}s")
        print(f"   Task time: {task_time:.2f}s")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Transport: HTTP (streamable-http)")
        print(f"   Fallback used: NO")
        
        # Check if successful
        if "success" in str(result).lower() or "circle" in str(result).lower():
            print(f"✅ HTTP test SUCCESSFUL")
            return total_time
        else:
            print(f"⚠️  HTTP test completed but check result")
            print(f"Result: {str(result)[:200]}...")
            return total_time
            
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        return False

def main():
    print("🚀 HTTP MCP Simple Performance Test")
    print("=" * 50)
    print("🎯 Goal: Measure pure HTTP transport performance")
    print("📈 Expected: Sub-second geometry creation")
    
    http_time = test_http_performance()
    
    print(f"\n📊 Final Results:")
    if http_time:
        print(f"✅ HTTP Transport Time: {http_time:.2f}s")
        if http_time < 2.0:
            print("🚀 EXCELLENT: HTTP transport is performing well!")
        elif http_time < 5.0:
            print("✅ GOOD: HTTP transport is working adequately")
        else:
            print("⚠️  SLOW: HTTP transport needs optimization")
        
        print(f"\n🎯 Compare to STDIO (~2.9s):")
        if http_time < 2.9:
            improvement = (2.9 - http_time) / 2.9 * 100
            print(f"🚀 {improvement:.0f}% FASTER than STDIO!")
        else:
            slowdown = (http_time - 2.9) / 2.9 * 100
            print(f"⚠️  {slowdown:.0f}% slower than STDIO")
    else:
        print("❌ HTTP transport test failed")

if __name__ == "__main__":
    main()