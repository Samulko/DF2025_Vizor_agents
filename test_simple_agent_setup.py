#!/usr/bin/env python3
"""
Simple Agent Setup Test for HTTP MCP Integration.

This test performs quick validation of agent setup and HTTP MCP connectivity.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_mcpadapt import GeometryAgentMCPAdapt
from bridge_design_system.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_agent_setup():
    """Test basic agent setup and configuration."""
    logger.info("=== Testing Basic Agent Setup ===")
    
    # Configure HTTP mode
    settings.mcp_transport_mode = "http"
    settings.mcp_http_url = "http://localhost:8001/mcp"
    
    try:
        # Create geometry agent
        agent = GeometryAgentMCPAdapt(model_name="geometry")
        
        logger.info(f"✅ Agent transport mode: {agent.transport_mode}")
        logger.info(f"✅ Server params: {agent.server_params}")
        
        return agent
        
    except Exception as e:
        logger.error(f"❌ Agent setup failed: {e}")
        return None


def test_tool_info(agent):
    """Test tool information retrieval."""
    logger.info("=== Testing Tool Information ===")
    
    try:
        # Get tool info (this test MCP connectivity)
        tool_info = agent.get_tool_info()
        
        logger.info(f"📊 Connected: {tool_info['connected']}")
        logger.info(f"📊 Transport: {tool_info.get('transport', 'unknown')}")
        logger.info(f"📊 Mode: {tool_info.get('mode', 'unknown')}")
        logger.info(f"📊 Total tools: {tool_info.get('total_tools', 0)}")
        logger.info(f"📊 MCP tools: {tool_info.get('mcp_tools', 0)}")
        
        if tool_info['connected']:
            logger.info("✅ MCP connection successful")
            
            if tool_info.get('transport') == 'http':
                logger.info("🎉 HTTP transport working!")
                return "http"
            elif tool_info.get('transport') == 'stdio_fallback':
                logger.info("⚠️  Using STDIO fallback")
                return "stdio_fallback"
            else:
                logger.info(f"📝 Transport: {tool_info.get('transport')}")
                return "other"
        else:
            logger.warning("❌ No MCP connection")
            return "none"
        
    except Exception as e:
        logger.error(f"❌ Tool info test failed: {e}")
        return "error"


def test_simple_task(agent):
    """Test a very simple task execution."""
    logger.info("=== Testing Simple Task Execution ===")
    
    try:
        # Very simple task
        task = "Get the current connection status"
        result = agent.run(task)
        
        logger.info(f"📝 Task result type: {type(result)}")
        logger.info(f"📝 Task result: {str(result)[:100]}...")
        
        if result:
            logger.info("✅ Simple task executed")
            return True
        else:
            logger.warning("⚠️  Task returned no result")
            return False
        
    except Exception as e:
        logger.error(f"❌ Simple task failed: {e}")
        return False


def main():
    """Run simple agent setup tests."""
    logger.info("🚀 Simple Agent Setup Test")
    logger.info("=" * 50)
    
    # Test 1: Agent Setup
    agent = test_agent_setup()
    if not agent:
        logger.error("❌ Cannot continue without agent")
        return False
    
    # Test 2: Tool Info
    transport_status = test_tool_info(agent)
    
    # Test 3: Simple Task (only if connected)
    if transport_status in ["http", "stdio_fallback", "other"]:
        task_success = test_simple_task(agent)
    else:
        task_success = False
        logger.info("⏭️  Skipping task test (no connection)")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Test Summary:")
    logger.info(f"✅ Agent Setup: Success")
    logger.info(f"📡 Transport: {transport_status}")
    logger.info(f"🎯 Task Execution: {'Success' if task_success else 'Failed/Skipped'}")
    
    if transport_status == "http":
        logger.info("🎉 HTTP MCP integration is working!")
        return True
    elif transport_status == "stdio_fallback":
        logger.info("✅ STDIO fallback is working (HTTP may need server)")
        return True
    else:
        logger.warning("⚠️  MCP integration needs attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)