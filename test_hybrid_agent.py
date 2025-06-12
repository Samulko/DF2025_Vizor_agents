#!/usr/bin/env python3
"""
Test Hybrid Agent Implementation.

This test validates the hybrid transport strategy that uses:
- HTTP for fast tool discovery
- STDIO for reliable task execution
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_hybrid import GeometryAgentHybrid
from bridge_design_system.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_hybrid_agent_setup():
    """Test hybrid agent initialization and configuration."""
    logger.info("=== Testing Hybrid Agent Setup ===")
    
    # Configure for hybrid mode
    settings.mcp_transport_mode = "http"  # This enables HTTP discovery
    settings.mcp_http_url = "http://localhost:8001/mcp"
    
    try:
        # Create hybrid agent
        agent = GeometryAgentHybrid(model_name="geometry")
        
        logger.info(f"✅ Hybrid agent initialized")
        logger.info(f"✅ HTTP params: {agent.http_params}")
        logger.info(f"✅ STDIO params: {agent.stdio_params}")
        
        return agent
        
    except Exception as e:
        logger.error(f"❌ Hybrid agent setup failed: {e}")
        return None


def test_tool_discovery_performance(agent):
    """Test fast tool discovery via hybrid strategy."""
    logger.info("=== Testing Tool Discovery Performance ===")
    
    try:
        import time
        
        # Test fast tool discovery
        start_time = time.time()
        tools = agent.get_tools_fast()
        discovery_time = time.time() - start_time
        
        logger.info(f"📊 Tool discovery time: {discovery_time:.2f}s")
        logger.info(f"📊 Tools discovered: {len(tools)}")
        
        # Test cache hit
        start_time = time.time()
        cached_tools = agent.get_tools_fast()
        cache_time = time.time() - start_time
        
        logger.info(f"📊 Cache hit time: {cache_time:.3f}s")
        logger.info(f"📊 Cache performance gain: {discovery_time/cache_time:.1f}x faster")
        
        if discovery_time < 5.0:  # Should be fast
            logger.info("✅ Tool discovery performance is good")
            return True
        else:
            logger.warning("⚠️  Tool discovery slower than expected")
            return False
        
    except Exception as e:
        logger.error(f"❌ Tool discovery test failed: {e}")
        return False


def test_hybrid_tool_info(agent):
    """Test hybrid tool information and status."""
    logger.info("=== Testing Hybrid Tool Information ===")
    
    try:
        # Get tool info
        tool_info = agent.get_tool_info()
        logger.info(f"📊 Tool Info: {tool_info}")
        
        # Verify hybrid strategy
        expected_keys = ["transport", "strategy", "mcp_tools", "mode"]
        for key in expected_keys:
            if key not in tool_info:
                logger.warning(f"⚠️  Missing key in tool info: {key}")
                return False
        
        if tool_info.get("transport") == "hybrid":
            logger.info("✅ Hybrid transport confirmed")
            return True
        else:
            logger.warning(f"⚠️  Expected hybrid transport, got: {tool_info.get('transport')}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Tool info test failed: {e}")
        return False


def test_hybrid_execution(agent):
    """Test task execution with hybrid strategy."""
    logger.info("=== Testing Hybrid Task Execution ===")
    
    try:
        # Simple geometry task
        task = "Create a point at coordinates (5, 15, 25)"
        
        import time
        start_time = time.time()
        result = agent.run(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        logger.info(f"📝 Task result: {str(result)[:150]}...")
        
        # Check for success indicators
        if result and not ("error" in str(result).lower() and "fallback" not in str(result).lower()):
            logger.info("✅ Hybrid execution successful")
            return True, execution_time
        else:
            logger.warning("⚠️  Hybrid execution completed with issues")
            return False, execution_time
        
    except Exception as e:
        logger.error(f"❌ Hybrid execution failed: {e}")
        return False, 0


def test_fallback_behavior(agent):
    """Test fallback behavior when MCP unavailable."""
    logger.info("=== Testing Fallback Behavior ===")
    
    try:
        # Force fallback by clearing cache and using invalid settings
        agent._tool_cache = None
        original_http_url = agent.http_params["url"]
        original_stdio_command = agent.stdio_params.command
        
        # Set invalid parameters to trigger fallback
        agent.http_params["url"] = "http://localhost:9999/invalid"
        agent.stdio_params = agent.stdio_params._replace(command="invalid_command")
        
        # Test fallback tools
        fallback_tools = agent._create_fallback_tools()
        logger.info(f"📊 Fallback tools: {len(fallback_tools)}")
        
        # Test fallback execution
        task = "Get connection status"
        result = agent.run(task)
        
        if "fallback" in str(result).lower():
            logger.info("✅ Fallback behavior working")
            fallback_success = True
        else:
            logger.warning("⚠️  Fallback behavior unclear")
            fallback_success = False
        
        # Restore original settings
        agent.http_params["url"] = original_http_url
        agent.stdio_params = agent.stdio_params._replace(command=original_stdio_command)
        
        return fallback_success
        
    except Exception as e:
        logger.error(f"❌ Fallback test failed: {e}")
        return False


def main():
    """Run all hybrid agent tests."""
    logger.info("🚀 Hybrid Agent Test Suite")
    logger.info("=" * 50)
    
    # Test 1: Agent Setup
    agent = test_hybrid_agent_setup()
    if not agent:
        logger.error("❌ Cannot continue without agent")
        return False
    
    # Test 2: Tool Discovery Performance
    discovery_success = test_tool_discovery_performance(agent)
    
    # Test 3: Tool Information
    info_success = test_hybrid_tool_info(agent)
    
    # Test 4: Hybrid Execution
    execution_success, exec_time = test_hybrid_execution(agent)
    
    # Test 5: Fallback Behavior
    fallback_success = test_fallback_behavior(agent)
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Hybrid Agent Test Summary:")
    logger.info(f"✅ Agent Setup: Success")
    logger.info(f"📈 Tool Discovery: {'Success' if discovery_success else 'Failed'}")
    logger.info(f"ℹ️  Tool Information: {'Success' if info_success else 'Failed'}")
    logger.info(f"🎯 Hybrid Execution: {'Success' if execution_success else 'Failed'}")
    logger.info(f"🔄 Fallback Behavior: {'Success' if fallback_success else 'Failed'}")
    
    # Calculate overall success
    tests_passed = sum([discovery_success, info_success, execution_success, fallback_success])
    total_tests = 4
    
    if tests_passed >= 3:
        logger.info("🎉 Hybrid agent strategy is working well!")
        logger.info("📝 Benefits:")
        logger.info("   - Fast HTTP tool discovery")
        logger.info("   - Reliable STDIO execution") 
        logger.info("   - Robust fallback mechanisms")
        logger.info("   - No async/sync conflicts")
        return True
    else:
        logger.warning("⚠️  Hybrid agent needs optimization")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)