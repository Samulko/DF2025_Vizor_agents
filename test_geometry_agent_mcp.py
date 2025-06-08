"""Test GeometryAgent with MCP integration."""
import os
from bridge_design_system.agents.geometry_agent import GeometryAgent
from bridge_design_system.config.model_config import ModelProvider

# Set MCP server URL in environment
os.environ["MCP_SERVER_URL"] = "http://localhost:8001/mcp"

def test_geometry_agent_with_mcp():
    """Test the GeometryAgent with MCP tools."""
    print("Testing GeometryAgent with MCP streamable-http integration...")
    
    try:
        # Create geometry agent - it auto-initializes the model and should auto-detect MCP
        agent = GeometryAgent()
        
        # Initialize the agent to trigger tool loading
        agent.initialize_agent()
        
        print(f"Agent initialized: {agent.name}")
        print(f"MCP connected: {agent.mcp_connected}")
        print(f"Number of tools: {len(agent.tools)}")
        
        if agent.mcp_connected:
            print("\n✅ MCP tools loaded successfully!")
            print("Available tools:")
            for tool in agent.tools:
                print(f"  - {tool.name}")
            
            # Test a simple operation
            print("\nTesting agent with a simple request...")
            response = agent.run("List all components in the current document")
            print(f"Response: {response}")
        else:
            print("\n⚠️  Agent is using placeholder tools (MCP not connected)")
            print("Make sure the MCP server is running!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_geometry_agent_with_mcp()