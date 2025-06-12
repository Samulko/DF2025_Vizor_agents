#!/usr/bin/env python3
"""
Test HTTP MCP for Simple Query Commands vs Complex Execution Tasks.

This test specifically checks if HTTP transport works for:
1. Simple queries: "What's on the canvas?"
2. Info retrieval: "Get component info"
3. Status checks: "Get document status"

vs complex execution tasks that we know timeout.
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.config.settings import settings
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_http_simple_queries():
    """Test HTTP MCP for simple query operations."""
    logger.info("=== Testing HTTP MCP for Simple Query Commands ===")
    
    # Configure HTTP parameters
    http_params = {
        "url": "http://localhost:8001/mcp",
        "transport": "streamable-http"
    }
    
    try:
        # Test HTTP for query operations
        with MCPAdapt(http_params, SmolAgentsAdapter()) as tools:
            logger.info(f"✅ Connected via HTTP with {len(tools)} tools")
            
            # Find query-type tools
            query_tools = []
            for tool in tools:
                tool_name = getattr(tool, 'name', str(tool))
                if any(keyword in tool_name.lower() for keyword in ['get', 'status', 'info', 'document', 'component']):
                    query_tools.append((tool_name, tool))
            
            logger.info(f"📊 Found {len(query_tools)} query-type tools")
            
            results = {}
            
            # Test each query tool
            for tool_name, tool in query_tools[:3]:  # Test first 3 to avoid too many calls
                try:
                    logger.info(f"🔍 Testing HTTP query: {tool_name}")
                    start_time = time.time()
                    
                    # Call the tool (most query tools don't need parameters)
                    if 'get_all_components' in tool_name:
                        result = tool()
                    elif 'get_component_info' in tool_name:
                        # Skip this one as it needs parameters
                        continue
                    elif 'get_document' in tool_name or 'document' in tool_name:
                        result = tool()
                    else:
                        result = tool()
                    
                    execution_time = time.time() - start_time
                    
                    logger.info(f"✅ {tool_name}: {execution_time:.2f}s")
                    logger.info(f"📝 Result: {str(result)[:100]}...")
                    
                    results[tool_name] = {
                        "success": True,
                        "time": execution_time,
                        "result_preview": str(result)[:100]
                    }
                    
                except Exception as e:
                    logger.error(f"❌ {tool_name} failed: {e}")
                    results[tool_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            return results
            
    except Exception as e:
        logger.error(f"❌ HTTP connection failed: {e}")
        return {"connection_error": str(e)}


def test_http_complex_execution():
    """Test HTTP MCP for complex execution tasks (known to fail)."""
    logger.info("=== Testing HTTP MCP for Complex Execution Tasks ===")
    
    # Configure HTTP parameters
    http_params = {
        "url": "http://localhost:8001/mcp",
        "transport": "streamable-http"
    }
    
    try:
        with MCPAdapt(http_params, SmolAgentsAdapter()) as tools:
            logger.info(f"✅ Connected via HTTP with {len(tools)} tools")
            
            # Find execution tools
            execution_tools = []
            for tool in tools:
                tool_name = getattr(tool, 'name', str(tool))
                if any(keyword in tool_name.lower() for keyword in ['add', 'create', 'edit', 'script']):
                    execution_tools.append((tool_name, tool))
            
            logger.info(f"🔧 Found {len(execution_tools)} execution-type tools")
            
            # Test a simple execution task
            for tool_name, tool in execution_tools[:1]:  # Test just the first one
                try:
                    logger.info(f"⚡ Testing HTTP execution: {tool_name}")
                    start_time = time.time()
                    
                    # Simple script execution
                    if 'add_python3_script' in tool_name:
                        result = tool(
                            x=100, 
                            y=100, 
                            name="HTTP Test Component",
                            script="# Simple HTTP test\na = 'HTTP works for execution!'"
                        )
                    else:
                        # Skip if not the tool we expect
                        continue
                    
                    execution_time = time.time() - start_time
                    
                    logger.info(f"✅ {tool_name}: {execution_time:.2f}s")
                    logger.info(f"📝 Result: {str(result)[:100]}...")
                    
                    return {
                        "success": True,
                        "time": execution_time,
                        "tool": tool_name,
                        "result": str(result)[:200]
                    }
                    
                except Exception as e:
                    logger.error(f"❌ {tool_name} failed: {e}")
                    return {
                        "success": False,
                        "tool": tool_name,
                        "error": str(e)
                    }
            
            return {"no_suitable_tools": True}
            
    except Exception as e:
        logger.error(f"❌ HTTP execution test failed: {e}")
        return {"connection_error": str(e)}


def compare_with_stdio():
    """Compare the same operations with STDIO transport."""
    logger.info("=== Comparing with STDIO Transport ===")
    
    from mcp import StdioServerParameters
    
    stdio_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "grasshopper_mcp.bridge"],
        env=None
    )
    
    try:
        with MCPAdapt(stdio_params, SmolAgentsAdapter()) as tools:
            logger.info(f"✅ STDIO connected with {len(tools)} tools")
            
            # Test the same query operation
            for tool in tools:
                tool_name = getattr(tool, 'name', str(tool))
                if 'get_all_components' in tool_name:
                    try:
                        start_time = time.time()
                        result = tool()
                        execution_time = time.time() - start_time
                        
                        logger.info(f"✅ STDIO {tool_name}: {execution_time:.2f}s")
                        logger.info(f"📝 Result: {str(result)[:100]}...")
                        
                        return {
                            "success": True,
                            "time": execution_time,
                            "transport": "STDIO"
                        }
                    except Exception as e:
                        logger.error(f"❌ STDIO {tool_name} failed: {e}")
                        return {"success": False, "error": str(e)}
            
            return {"no_suitable_tools": True}
            
    except Exception as e:
        logger.error(f"❌ STDIO test failed: {e}")
        return {"connection_error": str(e)}


def main():
    """Run HTTP query vs execution comparison tests."""
    logger.info("🔍 HTTP MCP: Query Commands vs Execution Tasks Analysis")
    logger.info("=" * 70)
    
    # Configure settings
    settings.mcp_transport_mode = "http"
    settings.mcp_http_url = "http://localhost:8001/mcp"
    
    # Test 1: HTTP Simple Queries
    logger.info("\n" + "=" * 50)
    http_query_results = test_http_simple_queries()
    
    # Test 2: HTTP Complex Execution  
    logger.info("\n" + "=" * 50)
    http_execution_results = test_http_complex_execution()
    
    # Test 3: STDIO Comparison
    logger.info("\n" + "=" * 50)
    stdio_results = compare_with_stdio()
    
    # Analysis
    logger.info("\n" + "=" * 70)
    logger.info("📊 ANALYSIS: HTTP Query vs Execution Capabilities")
    logger.info("=" * 70)
    
    # Analyze query results
    if isinstance(http_query_results, dict) and not http_query_results.get("connection_error"):
        successful_queries = sum(1 for r in http_query_results.values() if isinstance(r, dict) and r.get("success"))
        total_queries = len([r for r in http_query_results.values() if isinstance(r, dict)])
        
        logger.info(f"🔍 HTTP Query Commands:")
        logger.info(f"   ✅ Successful: {successful_queries}/{total_queries}")
        
        # Show timing for successful queries
        for tool_name, result in http_query_results.items():
            if isinstance(result, dict) and result.get("success"):
                logger.info(f"   ⏱️  {tool_name}: {result['time']:.2f}s")
    else:
        logger.info(f"🔍 HTTP Query Commands: ❌ Connection failed")
    
    # Analyze execution results
    if isinstance(http_execution_results, dict):
        if http_execution_results.get("success"):
            logger.info(f"⚡ HTTP Execution Tasks:")
            logger.info(f"   ✅ Success: {http_execution_results['time']:.2f}s")
        else:
            logger.info(f"⚡ HTTP Execution Tasks:")
            logger.info(f"   ❌ Failed: {http_execution_results.get('error', 'Unknown error')}")
    
    # Compare with STDIO
    if isinstance(stdio_results, dict) and stdio_results.get("success"):
        logger.info(f"📊 STDIO Comparison:")
        logger.info(f"   ✅ Success: {stdio_results['time']:.2f}s")
    
    # Conclusion
    logger.info("\n" + "🎯 CONCLUSION:")
    
    query_success = (isinstance(http_query_results, dict) and 
                    not http_query_results.get("connection_error") and
                    any(r.get("success") for r in http_query_results.values() if isinstance(r, dict)))
    
    execution_success = (isinstance(http_execution_results, dict) and 
                        http_execution_results.get("success"))
    
    if query_success and execution_success:
        logger.info("✅ HTTP works for BOTH queries AND execution")
    elif query_success and not execution_success:
        logger.info("⚡ HTTP works for QUERIES but fails for EXECUTION")
        logger.info("💡 This suggests the timeout issue is execution-context specific")
    elif not query_success and not execution_success:
        logger.info("❌ HTTP fails for both (likely server not running)")
    else:
        logger.info("❓ Unexpected result pattern")
    
    return query_success, execution_success


if __name__ == "__main__":
    query_ok, execution_ok = main()
    
    # Exit with appropriate code
    if query_ok and execution_ok:
        sys.exit(0)  # All good
    elif query_ok:
        sys.exit(1)  # Queries work, execution doesn't
    else:
        sys.exit(2)  # Nothing works