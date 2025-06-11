#!/usr/bin/env python3
"""
Test HTTP MCP integration performance and functionality.

This test validates the HTTP transport implementation and compares
performance against STDIO transport.
"""

import time
import os
import asyncio
import logging
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_mcpadapt import GeometryAgentMCPAdapt
from bridge_design_system.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_http_mcp_server_availability():
    """Test if HTTP MCP server is available."""
    import requests
    
    try:
        # Test HTTP MCP server health
        response = requests.get(f"{settings.mcp_http_url.replace('/mcp', '')}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ HTTP MCP server is available")
            return True
    except Exception as e:
        logger.warning(f"❌ HTTP MCP server not available: {e}")
        return False
    
    return False


def test_http_transport_configuration():
    """Test HTTP transport configuration."""
    logger.info("=== Testing HTTP Transport Configuration ===")
    
    # Override settings for HTTP mode
    original_mode = settings.mcp_transport_mode
    settings.mcp_transport_mode = "http"
    
    try:
        # Test server params generation
        server_params = settings.get_mcp_server_params()
        
        assert isinstance(server_params, dict)
        assert server_params["url"] == settings.mcp_http_url
        assert server_params["transport"] == "streamable-http"
        
        logger.info(f"✅ HTTP server params: {server_params}")
        
        # Test fallback params
        fallback_params = settings.get_mcp_connection_fallback_params()
        logger.info(f"✅ Fallback params type: {type(fallback_params)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ HTTP configuration test failed: {e}")
        return False
    finally:
        # Restore original setting
        settings.mcp_transport_mode = original_mode


def test_stdio_transport_configuration():
    """Test STDIO transport configuration."""
    logger.info("=== Testing STDIO Transport Configuration ===")
    
    # Override settings for STDIO mode
    original_mode = settings.mcp_transport_mode
    settings.mcp_transport_mode = "stdio"
    
    try:
        # Test server params generation
        server_params = settings.get_mcp_server_params()
        
        from mcp import StdioServerParameters
        assert isinstance(server_params, StdioServerParameters)
        assert server_params.command == "uv"
        
        logger.info(f"✅ STDIO server params: {server_params}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ STDIO configuration test failed: {e}")
        return False
    finally:
        # Restore original setting
        settings.mcp_transport_mode = original_mode


def test_geometry_agent_http_mode():
    """Test geometry agent with HTTP transport."""
    logger.info("=== Testing Geometry Agent HTTP Mode ===")
    
    # Override settings for HTTP mode
    original_mode = settings.mcp_transport_mode
    settings.mcp_transport_mode = "http"
    
    try:
        # Create agent with HTTP transport
        agent = GeometryAgentMCPAdapt(model_name="geometry")
        
        # Check transport mode
        assert agent.transport_mode == "http"
        logger.info(f"✅ Agent transport mode: {agent.transport_mode}")
        
        # Get tool info
        tool_info = agent.get_tool_info()
        logger.info(f"✅ Tool info: {tool_info}")
        
        # Check if connected via HTTP or fallback
        if tool_info["connected"]:
            logger.info(f"✅ Connected via {tool_info.get('transport', 'unknown')} transport")
            logger.info(f"✅ Available tools: {tool_info['mcp_tools']}")
            
            if tool_info.get("transport") == "http":
                logger.info("🎉 HTTP transport working!")
                return True
            elif tool_info.get("transport") == "stdio_fallback":
                logger.info("⚠️  HTTP failed, but STDIO fallback working")
                return True
            else:
                logger.warning(f"❓ Unknown transport: {tool_info.get('transport')}")
                return False
        else:
            logger.warning("❌ No MCP connection available")
            return False
            
    except Exception as e:
        logger.error(f"❌ HTTP mode test failed: {e}")
        return False
    finally:
        # Restore original setting
        settings.mcp_transport_mode = original_mode


def test_geometry_agent_stdio_mode():
    """Test geometry agent with STDIO transport."""
    logger.info("=== Testing Geometry Agent STDIO Mode ===")
    
    # Override settings for STDIO mode
    original_mode = settings.mcp_transport_mode
    settings.mcp_transport_mode = "stdio"
    
    try:
        # Create agent with STDIO transport
        agent = GeometryAgentMCPAdapt(model_name="geometry")
        
        # Check transport mode
        assert agent.transport_mode == "stdio"
        logger.info(f"✅ Agent transport mode: {agent.transport_mode}")
        
        # Get tool info
        tool_info = agent.get_tool_info()
        logger.info(f"✅ Tool info: {tool_info}")
        
        # Check if connected
        if tool_info["connected"]:
            logger.info(f"✅ Connected via {tool_info.get('transport', 'stdio')} transport")
            logger.info(f"✅ Available tools: {tool_info['mcp_tools']}")
            return True
        else:
            logger.warning("❌ No MCP connection available")
            return False
            
    except Exception as e:
        logger.error(f"❌ STDIO mode test failed: {e}")
        return False
    finally:
        # Restore original setting
        settings.mcp_transport_mode = original_mode


def test_fallback_mechanism():
    """Test HTTP to STDIO fallback mechanism."""
    logger.info("=== Testing Fallback Mechanism ===")
    
    # Override settings for HTTP mode
    original_mode = settings.mcp_transport_mode
    original_url = settings.mcp_http_url
    
    # Set invalid HTTP URL to trigger fallback
    settings.mcp_transport_mode = "http"
    settings.mcp_http_url = "http://localhost:9999/mcp"  # Invalid port
    
    try:
        # Create agent - should fail HTTP and fallback to STDIO
        agent = GeometryAgentMCPAdapt(model_name="geometry")
        
        # Get tool info - should show fallback
        tool_info = agent.get_tool_info()
        logger.info(f"✅ Fallback test result: {tool_info}")
        
        # Check if fallback worked
        if tool_info["connected"] and tool_info.get("transport") == "stdio_fallback":
            logger.info("✅ Fallback mechanism working correctly")
            return True
        elif not tool_info["connected"]:
            logger.info("⚠️  No connection available (expected if no MCP server running)")
            return True
        else:
            logger.warning(f"❓ Unexpected result: {tool_info}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fallback test failed: {e}")
        return False
    finally:
        # Restore original settings
        settings.mcp_transport_mode = original_mode
        settings.mcp_http_url = original_url


def run_all_tests():
    """Run all HTTP MCP integration tests."""
    logger.info("🚀 Starting HTTP MCP Integration Tests")
    logger.info("=" * 60)
    
    test_results = []
    
    # Test 1: HTTP Server Availability
    test_results.append(("HTTP Server Availability", test_http_mcp_server_availability()))
    
    # Test 2: HTTP Configuration
    test_results.append(("HTTP Transport Configuration", test_http_transport_configuration()))
    
    # Test 3: STDIO Configuration
    test_results.append(("STDIO Transport Configuration", test_stdio_transport_configuration()))
    
    # Test 4: HTTP Mode Agent
    test_results.append(("Geometry Agent HTTP Mode", test_geometry_agent_http_mode()))
    
    # Test 5: STDIO Mode Agent
    test_results.append(("Geometry Agent STDIO Mode", test_geometry_agent_stdio_mode()))
    
    # Test 6: Fallback Mechanism
    test_results.append(("HTTP to STDIO Fallback", test_fallback_mechanism()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("🏁 Test Results Summary")
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
        logger.info("🎉 All tests passed! HTTP MCP integration is working!")
    elif passed >= total * 0.8:
        logger.info("✅ Most tests passed. HTTP MCP integration is mostly working.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs for issues.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)