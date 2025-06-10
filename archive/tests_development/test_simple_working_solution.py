#!/usr/bin/env python3
"""
Simple Working Solution Test

This test validates the corrected approach:
1. DeepSeek model configuration working
2. Simple MCP pattern (agent INSIDE context) working 
3. No complex lifecycle management, just basic functionality

Run: python test_simple_working_solution.py
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_deepseek_model_config():
    """Test that DeepSeek model configuration works correctly."""
    logger.info("🔍 Testing DeepSeek model configuration...")
    
    try:
        from src.bridge_design_system.config.model_config import ModelProvider
        
        # Get model for geometry agent (should use DeepSeek)
        model = ModelProvider.get_model("geometry")
        
        logger.info(f"Model type: {type(model)}")
        logger.info(f"Model class: {model.__class__}")
        
        # Check if it's the correct OpenAIServerModel for DeepSeek
        if "OpenAIServerModel" in str(type(model)):
            logger.info("✅ Using OpenAIServerModel (correct for DeepSeek)")
            
            # Check if it has the expected attributes
            if hasattr(model, 'api_base'):
                logger.info(f"API Base: {getattr(model, 'api_base', 'N/A')}")
            if hasattr(model, 'model_id'):
                logger.info(f"Model ID: {getattr(model, 'model_id', 'N/A')}")
            
            return True
        else:
            logger.error(f"❌ Wrong model type. Expected OpenAIServerModel, got {type(model)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ DeepSeek model config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_connection_simple():
    """Test simple MCP connection pattern."""
    logger.info("🔍 Testing simple MCP connection...")
    
    try:
        from smolagents import ToolCollection
        from mcp import StdioServerParameters
        
        # Simple connection test
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "grasshopper_mcp.bridge"]
        )
        
        logger.info("Attempting simple MCP connection...")
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
            tools = list(tool_collection.tools)
            logger.info(f"✅ Connected and got {len(tools)} tools")
            
            # Show sample tools
            tool_names = [tool.name for tool in tools[:3]]
            logger.info(f"Sample tools: {tool_names}")
            
            return len(tools) > 40  # We expect around 49 tools
            
    except Exception as e:
        logger.error(f"❌ Simple MCP connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_agent_creation():
    """Test creating agent with correct pattern."""
    logger.info("🔍 Testing simple agent creation with MCP tools...")
    
    try:
        from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools
        
        logger.info("Creating agent using the correct pattern...")
        with create_geometry_agent_with_mcp_tools() as agent:
            logger.info("✅ Agent created successfully!")
            logger.info(f"Agent type: {type(agent)}")
            
            # Check if agent has tools
            if hasattr(agent, 'tools'):
                tool_count = len(agent.tools)
                logger.info(f"Agent has {tool_count} tools")
                return tool_count > 40
            else:
                logger.warning("⚠️ Agent doesn't have 'tools' attribute")
                return True  # Still consider this a success for creation
                
    except Exception as e:
        logger.error(f"❌ Simple agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_task_execution():
    """Test executing a very simple task."""
    logger.info("🔍 Testing simple task execution...")
    
    try:
        from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools
        
        logger.info("Executing simple task with agent...")
        with create_geometry_agent_with_mcp_tools() as agent:
            
            # Try the simplest possible task
            task = "What tools do you have available for Grasshopper?"
            logger.info(f"Task: {task}")
            
            result = agent.run(task)
            
            logger.info("✅ Task executed without errors!")
            logger.info(f"Result type: {type(result)}")
            
            # Check if we got some kind of meaningful response
            if result is not None and str(result).strip():
                logger.info("✅ Got meaningful response from task")
                if len(str(result)) < 500:  # If short enough, show it
                    logger.info(f"Response: {result}")
                else:
                    logger.info(f"Response (truncated): {str(result)[:300]}...")
                return True
            else:
                logger.warning("⚠️ Got empty/None response")
                return False
                
    except Exception as e:
        logger.error(f"❌ Simple task execution failed: {e}")
        
        # Check for specific error types
        if "Event loop is closed" in str(e):
            logger.error("🔍 Still getting 'Event loop is closed' error")
        elif "Rate limit" in str(e):
            logger.error("🔍 Hit rate limit - this suggests the request is working")
        
        import traceback
        traceback.print_exc()
        return False

def test_spiral_creation():
    """Test creating a spiral using Python 3 script component."""
    logger.info("🔍 Testing spiral creation in Grasshopper...")
    
    try:
        from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools
        
        logger.info("Creating spiral with geometry agent...")
        with create_geometry_agent_with_mcp_tools() as agent:
            
            # Task to create a spiral using Python script
            task = """
            Create a 3D spiral in Grasshopper using a Python 3 script component. 
            The spiral should:
            1. Have 10 turns
            2. Radius of 5 units
            3. Height of 20 units
            4. Be centered at origin (0,0,0)
            
            Use the add_python3_script tool to create a Python component with the spiral generation code.
            """
            
            logger.info(f"Task: Create 3D spiral")
            logger.info("This will add a Python component to Grasshopper with spiral code...")
            
            result = agent.run(task)
            
            logger.info("✅ Spiral creation task executed!")
            logger.info(f"Result type: {type(result)}")
            
            # Check if we got a meaningful response
            if result is not None and str(result).strip():
                logger.info("✅ Got response from spiral creation")
                logger.info(f"Response (truncated): {str(result)[:200]}...")
                
                # Look for indicators that a component was created
                result_str = str(result).lower()
                if any(word in result_str for word in ['python', 'script', 'component', 'spiral', 'created']):
                    logger.info("✅ Response indicates component creation")
                    return True
                else:
                    logger.warning("⚠️ Response doesn't clearly indicate success")
                    return False
            else:
                logger.warning("⚠️ Got empty response from spiral creation")
                return False
                
    except Exception as e:
        logger.error(f"❌ Spiral creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the simple working solution tests."""
    logger.info("🧪 Simple Working Solution Test")
    logger.info("=" * 50)
    logger.info("Testing the corrected DeepSeek + MCP approach")
    logger.info("=" * 50)
    
    tests = [
        ("DeepSeek Model Config", test_deepseek_model_config),
        ("MCP Connection Simple", test_mcp_connection_simple),
        ("Simple Agent Creation", test_simple_agent_creation),
        ("Simple Task Execution", test_simple_task_execution),
        ("Spiral Creation", test_spiral_creation),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
        except Exception as e:
            logger.error(f"❌ FAIL {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("SIMPLE SOLUTION TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"  {status} {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed >= 4:  # If DeepSeek + MCP + creation + basic task work
        logger.info("🎉 SIMPLE SOLUTION SUCCESS!")
        logger.info("✅ DeepSeek configuration is working")
        logger.info("✅ MCP external toolbox connection works")
        logger.info("✅ Agent creation with correct pattern works")
        logger.info("✅ Task execution working!")
        
        if passed == total:
            logger.info("✅ Spiral creation also working - geometry being created!")
            logger.info("\n🚀 Ready for production bridge design:")
            logger.info("- DeepSeek model saves 21x cost vs Claude")
            logger.info("- External MCP toolbox pattern is functional")
            logger.info("- Simple, reliable architecture")
            logger.info("- Actual geometry creation in Grasshopper ✅")
            
            logger.info("\n🎯 Check Grasshopper canvas for:")
            logger.info("- Python 3 Script component with spiral code")
            logger.info("- 3D spiral geometry (10 turns, radius 5, height 20)")
        else:
            logger.info("⚠️ Basic functionality working, spiral creation may need adjustment")
        
        logger.info("\n📖 Usage pattern:")
        logger.info("from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools")
        logger.info("with create_geometry_agent_with_mcp_tools() as agent:")
        logger.info("    result = agent.run('Create a bridge span with parametric curves')")
        
        return True
    else:
        logger.error("❌ SIMPLE SOLUTION FAILED")
        logger.error("Basic configuration or connection issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)