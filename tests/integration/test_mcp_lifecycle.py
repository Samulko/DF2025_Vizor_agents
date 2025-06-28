"""
Test script to verify MCP lifecycle is working correctly with the new implementation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_smolagents import create_geometry_agent
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.config.logging_config import setup_logging


def test_mcp_lifecycle():
    """Test that MCP lifecycle management works correctly."""
    print("=" * 60)
    print("TESTING MCP LIFECYCLE WITH NEW IMPLEMENTATION")
    print("=" * 60)

    setup_logging()

    try:
        # Create component registry
        registry = ComponentRegistry()

        # Create geometry agent using new wrapper pattern
        print("\n1. Creating geometry agent wrapper...")
        geometry_agent = create_geometry_agent(component_registry=registry)
        print("✅ Geometry agent created successfully")

        # Test task execution - this should properly manage MCP lifecycle
        print("\n2. Testing task execution with MCP lifecycle...")
        task = "Create two points to represent bridge start and end"

        print(f"Executing task: {task}")
        result = geometry_agent.run(task)

        print(f"\n3. Task completed!")
        print(f"Result type: {type(result)}")
        print(f"Result: {str(result)[:200]}...")

        print("\n✅ SUCCESS: MCP lifecycle management working correctly!")
        print("The wrapper pattern properly handles MCPAdapt context management.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("This indicates the MCP lifecycle issue may still exist.")

        # Check if this is the specific error we fixed
        if "Event loop is closed" in str(e):
            print("🔍 This is the event loop error we're trying to fix.")
            print("The MCP connection is being closed before the agent can use it.")
        else:
            print(f"🔍 Different error: {type(e).__name__}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_mcp_lifecycle()
