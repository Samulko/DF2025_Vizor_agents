#!/usr/bin/env python3
"""
Test HTTP MCP transport with simple geometry creation - no fallback.
"""

import sys
sys.path.insert(0, 'src')

import time
from smolagents import CodeAgent  
from smolagents.tools import ToolCollection
from bridge_design_system.config.model_config import ModelProvider

def test_http_only():
    """Test HTTP transport only."""
    print("⚡ HTTP-Only Transport Test")
    print("=" * 40)
    
    http_params = {
        "url": "http://localhost:8001/mcp",
        "transport": "streamable-http"
    }
    
    try:
        # Check server
        import requests
        requests.get("http://localhost:8001/", timeout=2)
        print("✅ HTTP server available")
    except:
        print("❌ HTTP server not available")
        return False
        
    try:
        model = ModelProvider.get_model("geometry")
        
        start_time = time.time()
        with ToolCollection.from_mcp(http_params, trust_remote_code=True) as tools:
            connect_time = time.time() - start_time
            print(f"✅ Connected in {connect_time:.2f}s")
            print(f"✅ Tools: {len(list(tools.tools))}")
            
            agent = CodeAgent(
                tools=[*tools.tools],
                model=model,
                add_base_tools=False,
                max_steps=3
            )
            
            task = "Create a circle in Grasshopper using add_python3_script with radius 5"
            
            task_start = time.time()
            result = agent.run(task)
            task_time = time.time() - task_start
            
            total_time = connect_time + task_time
            
            print(f"\n📊 Results:")
            print(f"   Connection: {connect_time:.2f}s")
            print(f"   Task: {task_time:.2f}s") 
            print(f"   Total: {total_time:.2f}s")
            print(f"   Status: HTTP-only (no fallback)")
            
            success = "success" in str(result).lower() or len(str(result)) > 50
            return total_time if success else False
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 HTTP MCP Transport Test (No Fallback)")
    print("=" * 50)
    
    result = test_http_only()
    
    if result:
        print(f"\n✅ SUCCESS: {result:.2f}s total")
        if result < 2.9:
            print(f"🚀 Faster than STDIO (~2.9s)!")
        else:
            print(f"⚠️ Slower than STDIO (~2.9s)")
    else:
        print(f"\n❌ HTTP test failed")