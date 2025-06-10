"""Simple Geometry Agent with proper MCP integration.

This implements the correct pattern: keeping the agent INSIDE the MCP connection context
to avoid the "Event loop is closed" errors.
"""

import logging
from contextlib import contextmanager
from typing import Any, Optional

from smolagents import CodeAgent, ToolCollection
from mcp import StdioServerParameters

from ..config.model_config import ModelProvider
from ..config.logging_config import get_logger

logger = get_logger(__name__)


@contextmanager
def create_geometry_agent_with_mcp_tools(agent_name: str = "geometry"):
    """Create a geometry agent with MCP tools using the correct pattern.
    
    This context manager:
    1. Connects to the external MCP toolbox 
    2. Creates agent INSIDE the MCP context (crucial for avoiding async/sync issues)
    3. Yields the working agent
    4. Automatically cleans up the connection
    
    Args:
        agent_name: Agent configuration name from settings (e.g., "geometry")
        
    Yields:
        CodeAgent: A working agent with MCP tools from external toolbox
        
    Example:
        with create_geometry_agent_with_mcp_tools() as agent:
            result = agent.run("Create a point at coordinates (0, 0, 0)")
            print(result)
    """
    logger.info(f"Creating {agent_name} agent with external MCP toolbox...")
    
    # Get model configuration for the agent
    model = ModelProvider.get_model(agent_name)
    logger.info(f"Using model: {model}")
    
    # Configure connection to external grasshopper_mcp.bridge
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "grasshopper_mcp.bridge"],
        env=None  # Use current environment
    )
    
    # Connect to external MCP toolbox and create agent INSIDE the context
    try:
        logger.info("Connecting to external MCP toolbox...")
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
            
            # Get tools from external toolbox
            mcp_tools = list(tool_collection.tools)
            logger.info(f"✅ Connected to external MCP toolbox with {len(mcp_tools)} tools")
            
            # Show sample tools
            tool_names = [tool.name for tool in mcp_tools[:5]]
            logger.info(f"Sample tools: {tool_names}")
            
            # Create agent INSIDE the MCP context where tools are alive
            agent = CodeAgent(
                tools=mcp_tools,  # Use tools directly from the active collection
                model=model,
                add_base_tools=False  # Don't add base tools (avoids duckduckgo_search dependency)
            )
            
            logger.info(f"✅ Agent created with {len(mcp_tools)} MCP tools (no base tools to avoid dependencies)")
            logger.info("🎯 Agent ready for use - tools are connected and active")
            
            # Yield the working agent to the caller
            yield agent
            
            logger.info("✅ Agent session completed, cleaning up MCP connection")
            
    except Exception as e:
        logger.error(f"❌ Failed to create agent with MCP toolbox: {e}")
        raise


def test_simple_mcp_agent():
    """Simple test function to validate the MCP agent pattern."""
    logger.info("🧪 Testing simple MCP agent pattern...")
    
    try:
        with create_geometry_agent_with_mcp_tools() as agent:
            logger.info("🔍 Testing agent with simple task...")
            
            # Test with a very simple task
            task = "Get information about the current Grasshopper document"
            logger.info(f"Task: {task}")
            
            result = agent.run(task)
            logger.info("✅ Task completed successfully!")
            logger.info(f"Result: {result}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Simple MCP agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Convenience function for direct usage
def run_geometry_task(task: str, agent_name: str = "geometry") -> Any:
    """Run a single geometry task using MCP tools.
    
    Args:
        task: The task description
        agent_name: Agent configuration name
        
    Returns:
        Task result
        
    Example:
        result = run_geometry_task("Create a circle with radius 5")
    """
    with create_geometry_agent_with_mcp_tools(agent_name) as agent:
        return agent.run(task)