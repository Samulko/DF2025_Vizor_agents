"""HTTP Geometry Agent for SimpleMCPBridge.cs integration.

This implements the HTTP transport solution for connecting smolagents
to the SimpleMCPBridge.cs component in Grasshopper.

Architecture:
smolagents → HTTP MCP Server → SimpleMCPBridge.cs → Grasshopper
"""

import logging
from contextlib import contextmanager
from typing import Any, Optional

from smolagents import CodeAgent, ToolCollection

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger

logger = get_logger(__name__)


@contextmanager
def create_http_geometry_agent_with_mcp_tools(agent_name: str = "geometry", mcp_server_url: str = "http://localhost:8001/mcp"):
    """Create a geometry agent with HTTP MCP tools for SimpleMCPBridge.cs integration.
    
    This context manager:
    1. Connects to the HTTP MCP server (streamable-http transport)
    2. Creates agent INSIDE the MCP context (crucial for avoiding async/sync issues)
    3. Yields the working agent that SimpleMCPBridge.cs can poll commands from
    4. Automatically cleans up the connection
    
    Args:
        agent_name: Agent configuration name from settings (e.g., "geometry")
        mcp_server_url: URL of the HTTP MCP server (default: http://localhost:8001/mcp)
        
    Yields:
        CodeAgent: A working agent with MCP tools accessible via HTTP
        
    Example:
        # Start HTTP MCP server first:
        # python -m bridge_design_system.main --start-streamable-http --mcp-port 8001
        
        # Then use the agent:
        with create_http_geometry_agent_with_mcp_tools() as agent:
            result = agent.run("Create a point at coordinates (0, 0, 0)")
            print(result)
    """
    logger.info(f"Creating {agent_name} agent with HTTP MCP toolbox...")
    
    # Get model configuration for the agent
    model = ModelProvider.get_model(agent_name)
    logger.info(f"Using model: {model}")
    
    # Configure connection to HTTP MCP server (streamable-http transport)
    mcp_config = {
        "url": mcp_server_url,
        "transport": "streamable-http"
    }
    
    # Connect to HTTP MCP toolbox and create agent INSIDE the context
    try:
        logger.info(f"Connecting to HTTP MCP server at {mcp_server_url}...")
        with ToolCollection.from_mcp(mcp_config, trust_remote_code=True) as tool_collection:
            
            # Get tools from HTTP MCP server
            mcp_tools = list(tool_collection.tools)
            logger.info(f"✅ Connected to HTTP MCP server with {len(mcp_tools)} tools")
            
            # Show sample tools
            tool_names = [tool.name for tool in mcp_tools[:5]]
            logger.info(f"Sample tools: {tool_names}")
            
            # Create agent INSIDE the MCP context where tools are alive
            agent = CodeAgent(
                tools=mcp_tools,  # Use tools directly from the active collection
                model=model,
                add_base_tools=False  # Don't add base tools (avoids duckduckgo_search dependency)
            )
            
            logger.info(f"✅ HTTP Agent created with {len(mcp_tools)} MCP tools (no base tools to avoid dependencies)")
            logger.info("🎯 HTTP Agent ready for use - SimpleMCPBridge.cs can now poll commands")
            logger.info("🔗 Architecture: Agent → HTTP MCP Server → SimpleMCPBridge.cs → Grasshopper")
            
            # Yield the working agent to the caller
            yield agent
            
            logger.info("✅ HTTP Agent session completed, cleaning up MCP connection")
            
    except Exception as e:
        logger.error(f"❌ Failed to create HTTP agent with MCP toolbox: {e}")
        raise


def test_http_mcp_agent():
    """Simple test function to validate the HTTP MCP agent pattern."""
    logger.info("🧪 Testing HTTP MCP agent pattern...")
    
    try:
        with create_http_geometry_agent_with_mcp_tools() as agent:
            logger.info("🔍 Testing HTTP agent with simple task...")
            
            # Test with a very simple task
            task = "Get information about the current Grasshopper document"
            logger.info(f"Task: {task}")
            
            result = agent.run(task)
            logger.info("✅ HTTP Task completed successfully!")
            logger.info(f"Result: {result}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ HTTP MCP agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Convenience function for direct usage
def run_http_geometry_task(task: str, agent_name: str = "geometry", mcp_server_url: str = "http://localhost:8001/mcp") -> Any:
    """Run a single geometry task using HTTP MCP tools.
    
    Args:
        task: The task description
        agent_name: Agent configuration name
        mcp_server_url: URL of the HTTP MCP server
        
    Returns:
        Task result
        
    Example:
        # Make sure HTTP MCP server is running first:
        # python -m bridge_design_system.main --start-streamable-http --mcp-port 8001
        
        result = run_http_geometry_task("Create a circle with radius 5")
    """
    with create_http_geometry_agent_with_mcp_tools(agent_name, mcp_server_url) as agent:
        return agent.run(task)


def start_http_mcp_server_instructions():
    """Print instructions for starting the HTTP MCP server."""
    print("🚀 HTTP MCP Server Setup Instructions")
    print("=" * 50)
    print()
    print("1. Start the HTTP MCP Server:")
    print("   python -m bridge_design_system.main --start-streamable-http --mcp-port 8001")
    print()
    print("2. In Grasshopper:")
    print("   - Add SimpleMCPBridge component to canvas")
    print("   - Connect Boolean Toggle to 'Connect' input")
    print("   - Set Server URL to 'http://localhost:8001' (default)")
    print("   - Set Connect = True")
    print()
    print("3. Test the connection:")
    print("   python test_http_grasshopper_control.py")
    print()
    print("4. Architecture:")
    print("   smolagents → HTTP MCP Server → SimpleMCPBridge.cs → Grasshopper")
    print("   (Port 8001)    (polling)         (UI thread)")
    print()