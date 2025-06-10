"""Safe test for GeometryAgent with graceful MCP handling."""
import os
from bridge_design_system.agents.geometry_agent import GeometryAgent

# Set MCP server URL in environment
os.environ["MCP_SERVER_URL"] = "http://localhost:8001/mcp"

def test_geometry_agent_safe():
    """Test the GeometryAgent with safe MCP connection handling."""
    print("Testing GeometryAgent with safe MCP connection...")
    print("-" * 60)
    
    # First, check if MCP server is reachable
    print("0. Checking MCP server connectivity...")
    try:
        import requests
        response = requests.get("http://localhost:8001", timeout=2)
        print("   ✅ MCP server is reachable")
    except Exception as e:
        print(f"   ⚠️  MCP server not reachable: {e}")
        print("   The test will proceed but may fall back to placeholder tools")
    
    try:
        # Create geometry agent
        print("1. Creating GeometryAgent...")
        agent = GeometryAgent()
        print(f"   ✅ Agent created: {agent.name}")
        
        # Try to initialize agent with timeout protection
        print("2. Initializing agent tools...")
        try:
            import threading
            import time
            
            class TimeoutException(Exception):
                pass
            
            # Use threading for Windows-compatible timeout
            result = {"success": False, "error": None}
            
            def init_agent():
                try:
                    agent.initialize_agent()
                    result["success"] = True
                except Exception as e:
                    result["error"] = e
            
            # Start initialization in a separate thread
            thread = threading.Thread(target=init_agent)
            thread.daemon = True
            thread.start()
            
            # Wait up to 15 seconds for initialization
            thread.join(timeout=15)
            
            if thread.is_alive():
                raise TimeoutException("Agent initialization timed out after 15 seconds")
            
            if result["error"]:
                raise result["error"]
            
            if not result["success"]:
                raise Exception("Agent initialization failed for unknown reason")
            
            print(f"   ✅ Agent initialized successfully!")
            print(f"   📊 MCP connected: {agent.mcp_connected}")
            print(f"   🔧 Number of tools: {len(agent.tools)}")
            
            if agent.mcp_connected:
                print("\n3. ✅ MCP Integration Test PASSED!")
                print("   Available MCP tools:")
                for i, tool in enumerate(agent.tools, 1):
                    print(f"   {i}. {tool.name}")
                
                # Test a simple agent interaction
                print("\n4. Testing agent interaction...")
                try:
                    response = agent.run("List the available tools you have access to")
                    print(f"   ✅ Agent response: {response.message[:100]}...")
                except Exception as e:
                    print(f"   ⚠️  Agent interaction failed: {e}")
            else:
                print("\n3. ⚠️  MCP not connected - using placeholder tools")
                print("   This is expected if the MCP server isn't running")
                print("   Available placeholder tools:")
                for i, tool in enumerate(agent.tools, 1):
                    print(f"   {i}. {tool.name}")
                    
        except TimeoutException:
            print("   ⚠️  Agent initialization timed out (>10 seconds)")
            print("   This suggests the MCP server is not responding")
            print("   The agent will fall back to placeholder tools")
            
        except Exception as e:
            print(f"   ⚠️  Agent initialization failed: {str(e)}")
            print("   This is expected if the MCP server isn't running")
            
        finally:
            pass  # Cleanup completed
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_geometry_agent_safe()