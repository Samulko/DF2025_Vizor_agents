#!/usr/bin/env python3
"""
Phase 3 Test: MCPClient Approach for Geometry Agent

This test validates the new MCPClient approach where the external MCP server
is treated as a toolbox that the agent can draw from with proper connection lifecycle.

Run: python test_phase3_mcp_client.py
"""

import sys
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mcp_client_connection() -> bool:
    """Test MCPClient connection to external MCP toolbox."""
    logger.info("🔍 Testing MCPClient connection to external MCP toolbox...")
    
    try:
        from src.bridge_design_system.mcp.mcp_tools_utils import create_mcp_client_for_grasshopper
        from smolagents import MCPClient
        
        # Create MCPClient for Grasshopper toolbox
        mcp_client = create_mcp_client_for_grasshopper()
        
        logger.info("Attempting to connect to external MCP toolbox...")
        mcp_client.connect()
        
        # Get tools from external toolbox
        tools = mcp_client.get_tools()
        logger.info(f"✅ Retrieved {len(tools)} tools from external MCP toolbox")
        
        # Show available tools
        tool_names = [tool.name for tool in tools[:10]]  # First 10
        logger.info(f"Available tools (sample): {tool_names}")
        
        # Clean disconnect
        mcp_client.disconnect()
        logger.info("✅ Disconnected cleanly from MCP toolbox")
        
        return len(tools) > 0
        
    except Exception as e:
        logger.error(f"❌ MCPClient connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_geometry_agent_with_mcp_creation() -> bool:
    """Test creating Geometry Agent with MCP toolbox."""
    logger.info("🔍 Testing Geometry Agent with MCP toolbox creation...")
    
    try:
        from src.bridge_design_system.agents.geometry_agent_with_mcp import GeometryAgentWithMCP
        
        # Create agent (without auto-connect)
        agent = GeometryAgentWithMCP()
        logger.info("✅ GeometryAgentWithMCP created successfully")
        
        # Test connection
        logger.info("Testing MCP toolbox connection...")
        connected = agent.connect_to_mcp()
        
        if connected:
            logger.info("✅ Successfully connected to MCP toolbox")
            
            # Get tool info
            tool_info = agent.get_tool_info()
            logger.info(f"Tool info: {tool_info}")
            
            # Check if we have expected tools
            expected_tools = tool_info.get('mcp_tools', 0)
            if expected_tools >= 40:  # We expect around 49 tools
                logger.info(f"✅ Found expected number of tools: {expected_tools}")
                
                # Test disconnect
                agent.disconnect()
                logger.info("✅ Disconnected successfully")
                return True
            else:
                logger.warning(f"⚠️ Expected more tools, got {expected_tools}")
                agent.disconnect()
                return False
        else:
            logger.error("❌ Failed to connect to MCP toolbox")
            return False
            
    except Exception as e:
        logger.error(f"❌ Geometry Agent with MCP creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_manager_pattern() -> bool:
    """Test the context manager pattern for clean resource management."""
    logger.info("🔍 Testing context manager pattern...")
    
    try:
        from src.bridge_design_system.agents.geometry_agent_with_mcp import create_geometry_agent_with_mcp
        
        # Test context manager usage
        with create_geometry_agent_with_mcp() as agent:
            logger.info("✅ Agent created inside context manager")
            
            # Check agent is connected
            if not agent.is_connected():
                logger.error("❌ Agent should be connected inside context manager")
                return False
            
            # Get tool info
            tool_info = agent.get_tool_info()
            logger.info(f"Tool info: {tool_info}")
            
            expected_tools = tool_info.get('mcp_tools', 0)
            if expected_tools >= 40:
                logger.info(f"✅ Context manager working: {expected_tools} tools available")
                return True
            else:
                logger.warning(f"⚠️ Expected more tools in context manager: {expected_tools}")
                return False
        
        # Context should be cleaned up automatically
        logger.info("✅ Context manager exited cleanly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Context manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_task_execution() -> bool:
    """Test executing a simple task through the MCP toolbox."""
    logger.info("🔍 Testing simple task execution...")
    
    try:
        from src.bridge_design_system.agents.geometry_agent_with_mcp import GeometryAgentWithMCP
        
        # Create and connect agent
        agent = GeometryAgentWithMCP()
        
        if not agent.connect_to_mcp():
            logger.error("❌ Failed to connect to MCP toolbox for task execution")
            return False
        
        logger.info("Attempting to execute simple task...")
        
        # Try a very simple task that should work
        simple_task = "Get information about the current Grasshopper document"
        
        try:
            result = agent.run(simple_task)
            logger.info("✅ Task executed successfully!")
            logger.info(f"Result type: {type(result)}")
            
            # Check if we got a reasonable response
            if result is not None:
                logger.info("✅ Got non-None result from task execution")
                agent.disconnect()
                return True
            else:
                logger.warning("⚠️ Got None result from task execution")
                agent.disconnect()
                return False
                
        except Exception as task_error:
            logger.error(f"❌ Task execution failed: {task_error}")
            # Check if it's still the async/sync error
            if "Event loop is closed" in str(task_error):
                logger.error("🔍 Still getting async/sync error - need to investigate further")
            agent.disconnect()
            return False
        
    except Exception as e:
        logger.error(f"❌ Simple task execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run MCPClient approach tests."""
    logger.info("🧪 Phase 3 Test - MCPClient Approach for External MCP Toolbox")
    logger.info("=" * 70)
    
    tests = [
        ("MCPClient Connection", test_mcp_client_connection),
        ("Geometry Agent Creation", test_geometry_agent_with_mcp_creation),
        ("Context Manager Pattern", test_context_manager_pattern),
        ("Simple Task Execution", test_simple_task_execution),
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
    logger.info("\n" + "=" * 70)
    logger.info("MCPCLIENT APPROACH TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"  {status} {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed >= 3:  # If connection and creation work
        logger.info("🎉 MCPCLIENT APPROACH SUCCESS!")
        logger.info("✅ External MCP toolbox pattern is working")
        logger.info("✅ Connection lifecycle management is working")
        logger.info("✅ Agent can access external MCP tools")
        
        if passed == total:
            logger.info("✅ Task execution also working - fully functional!")
            logger.info("\n🚀 Ready for production use:")
            logger.info("- Use GeometryAgentWithMCP for MCP toolbox integration")
            logger.info("- Use context manager for automatic cleanup")
            logger.info("- External MCP server works as intended toolbox")
        else:
            logger.info("⚠️ Task execution needs refinement")
            logger.info("🔧 Next: Debug any remaining async/sync issues in task execution")
        
        return True
    else:
        logger.error("❌ MCPCLIENT APPROACH FAILED")
        logger.error("Foundation issues with MCPClient or agent creation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)