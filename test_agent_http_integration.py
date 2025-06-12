#!/usr/bin/env python3
"""
Test Agent HTTP MCP Integration.

This test focuses on validating the agent workflow with HTTP MCP transport,
testing the complete flow from agent initialization through task execution.
"""

import time
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_mcpadapt import GeometryAgentMCPAdapt
from bridge_design_system.agents.triage_agent import TriageAgent
from bridge_design_system.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_http_mode():
    """Configure settings for HTTP mode testing."""
    logger.info("🔧 Configuring HTTP transport mode")
    settings.mcp_transport_mode = "http"
    settings.mcp_http_url = "http://localhost:8001/mcp"
    logger.info(f"✅ HTTP mode configured: {settings.mcp_http_url}")


def test_agent_initialization():
    """Test geometry agent initialization with HTTP transport."""
    logger.info("=== Testing Agent Initialization ===")
    
    try:
        # Create geometry agent
        agent = GeometryAgentMCPAdapt(model_name="geometry")
        
        # Verify configuration
        assert agent.transport_mode == "http"
        assert agent.server_params["url"] == settings.mcp_http_url
        assert agent.server_params["transport"] == "streamable-http"
        
        logger.info(f"✅ Agent initialized with HTTP transport")
        logger.info(f"✅ Server URL: {agent.server_params['url']}")
        
        return True, agent
        
    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {e}")
        return False, None


def test_tool_availability(agent):
    """Test tool loading from HTTP MCP server."""
    logger.info("=== Testing Tool Availability ===")
    
    try:
        # Get tool information
        tool_info = agent.get_tool_info()
        logger.info(f"📊 Tool Info: {tool_info}")
        
        # Check connection status
        if not tool_info["connected"]:
            logger.warning("⚠️  MCP server not connected - may need to start server")
            return False
        
        # Verify HTTP transport
        if tool_info.get("transport") != "http":
            logger.warning(f"⚠️  Expected HTTP transport, got: {tool_info.get('transport')}")
            if tool_info.get("transport") == "stdio_fallback":
                logger.info("📝 Using STDIO fallback - HTTP server may not be running")
            return False
        
        # Check tool count
        tool_count = tool_info.get("mcp_tools", 0)
        if tool_count < 6:
            logger.warning(f"⚠️  Expected at least 6 tools, got: {tool_count}")
            return False
        
        logger.info(f"✅ HTTP MCP connected with {tool_count} tools")
        logger.info(f"✅ Transport: {tool_info.get('transport')}")
        logger.info(f"✅ Mode: {tool_info.get('mode')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Tool availability test failed: {e}")
        return False


def test_simple_geometry_task(agent):
    """Test simple geometry task execution."""
    logger.info("=== Testing Simple Geometry Task ===")
    
    task = "Create a point at coordinates (5, 10, 15)"
    
    try:
        start_time = time.time()
        result = agent.run(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        logger.info(f"📝 Task result: {str(result)[:200]}...")
        
        # Check for success indicators
        if result and not ("error" in str(result).lower() and "fallback" not in str(result).lower()):
            logger.info("✅ Simple geometry task completed successfully")
            return True, execution_time
        else:
            logger.warning("⚠️  Task completed with issues")
            return False, execution_time
        
    except Exception as e:
        logger.error(f"❌ Simple geometry task failed: {e}")
        return False, 0


def test_complex_geometry_task(agent):
    """Test complex geometry task execution."""
    logger.info("=== Testing Complex Geometry Task ===")
    
    task = """Create a simple bridge structure:
1. Create two support points at (0, 0, 0) and (20, 0, 0)
2. Create a bridge deck line connecting these points
3. Add vertical support pillars at each end (height 5 units)
Please use Python scripts to create this geometry."""
    
    try:
        start_time = time.time()
        result = agent.run(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        logger.info(f"📝 Task result: {str(result)[:300]}...")
        
        # Check for success indicators
        if result and not ("error" in str(result).lower() and "fallback" not in str(result).lower()):
            logger.info("✅ Complex geometry task completed successfully")
            return True, execution_time
        else:
            logger.warning("⚠️  Task completed with issues")
            return False, execution_time
        
    except Exception as e:
        logger.error(f"❌ Complex geometry task failed: {e}")
        return False, 0


def test_triage_agent_delegation():
    """Test full workflow through triage agent delegation."""
    logger.info("=== Testing Triage Agent Delegation ===")
    
    try:
        # Initialize triage agent
        triage = TriageAgent()
        triage.initialize_agent()
        
        # Check agent status
        status = triage.get_agent_status()
        logger.info(f"📊 Agent Status: {status}")
        
        # Test delegation
        task = "Create a point at coordinates (1, 2, 3) for a bridge anchor"
        
        start_time = time.time()
        response = triage.handle_design_request(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Delegation time: {execution_time:.2f}s")
        logger.info(f"📝 Response: {response}")
        
        if response.success:
            logger.info("✅ Triage delegation successful")
            return True, execution_time
        else:
            logger.warning("⚠️  Triage delegation had issues")
            return False, execution_time
        
    except Exception as e:
        logger.error(f"❌ Triage delegation failed: {e}")
        return False, 0


def test_performance_metrics(execution_times):
    """Analyze performance metrics."""
    logger.info("=== Performance Analysis ===")
    
    if not execution_times:
        logger.warning("⚠️  No execution times to analyze")
        return False
    
    avg_time = sum(execution_times) / len(execution_times)
    fastest = min(execution_times)
    slowest = max(execution_times)
    
    logger.info(f"📊 Average execution time: {avg_time:.2f}s")
    logger.info(f"📊 Fastest execution: {fastest:.2f}s")
    logger.info(f"📊 Slowest execution: {slowest:.2f}s")
    
    # Check if performance is reasonable (< 10s average)
    if avg_time < 10.0:
        logger.info("✅ Performance looks good (< 10s average)")
        return True
    else:
        logger.warning(f"⚠️  Performance may be slow (average {avg_time:.2f}s)")
        return False


def run_agent_tests():
    """Run all agent HTTP integration tests."""
    logger.info("🚀 Starting Agent HTTP Integration Tests")
    logger.info("=" * 60)
    
    # Setup
    setup_http_mode()
    
    test_results = []
    execution_times = []
    
    # Test 1: Agent Initialization
    logger.info("\n" + "=" * 40)
    success, agent = test_agent_initialization()
    test_results.append(("Agent Initialization", success))
    
    if not success:
        logger.error("❌ Cannot continue without agent initialization")
        return False
    
    # Test 2: Tool Availability
    logger.info("\n" + "=" * 40)
    success = test_tool_availability(agent)
    test_results.append(("Tool Availability", success))
    
    # Test 3: Simple Task
    logger.info("\n" + "=" * 40)
    success, exec_time = test_simple_geometry_task(agent)
    test_results.append(("Simple Geometry Task", success))
    if success:
        execution_times.append(exec_time)
    
    # Test 4: Complex Task
    logger.info("\n" + "=" * 40)
    success, exec_time = test_complex_geometry_task(agent)
    test_results.append(("Complex Geometry Task", success))
    if success:
        execution_times.append(exec_time)
    
    # Test 5: Triage Delegation
    logger.info("\n" + "=" * 40)
    success, exec_time = test_triage_agent_delegation()
    test_results.append(("Triage Agent Delegation", success))
    if success:
        execution_times.append(exec_time)
    
    # Test 6: Performance Analysis
    logger.info("\n" + "=" * 40)
    success = test_performance_metrics(execution_times)
    test_results.append(("Performance Analysis", success))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Agent Test Results Summary")
    logger.info("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
    
    logger.info("=" * 60)
    logger.info(f"📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All agent tests passed! HTTP MCP integration is working!")
    elif passed >= total * 0.8:
        logger.info("✅ Most tests passed. Agent HTTP integration is mostly working.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs for issues.")
    
    return passed >= total * 0.8  # Success if 80% or more pass


if __name__ == "__main__":
    success = run_agent_tests()
    sys.exit(0 if success else 1)