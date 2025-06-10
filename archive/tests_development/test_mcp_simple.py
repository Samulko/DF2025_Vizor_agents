"""Simple test for MCP streamable-http connection."""
from bridge_design_system.mcp.smolagents_integration import GrasshopperMCPIntegration

def test_mcp_connection():
    """Test basic MCP connection without agents."""
    print("Testing MCP streamable-http connection...")
    print("-" * 50)
    
    # Create integration instance
    integration = GrasshopperMCPIntegration("http://localhost:8001/mcp")
    
    # Try to connect
    if integration.connect():
        print("✅ Successfully connected to MCP server!")
        print(f"Found {len(integration.get_tools())} tools:")
        
        for tool in integration.get_tools():
            print(f"  - {tool.name}: {tool.description}")
        
        # Disconnect
        integration.disconnect()
        print("\n✅ Test completed successfully!")
    else:
        print("❌ Failed to connect to MCP server")
        print("\nMake sure the MCP server is running:")
        print("uv run python -m bridge_design_system.main --start-streamable-http")

if __name__ == "__main__":
    test_mcp_connection()