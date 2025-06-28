#!/usr/bin/env python3
"""
Test script to verify real MCP geometry creation works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.config.logging_config import setup_logging


def test_real_mcp_geometry():
    """Test real MCP geometry creation."""
    print("=" * 60)
    print("TESTING REAL MCP GEOMETRY CREATION")
    print("=" * 60)

    setup_logging()

    try:
        # Create triage system
        print("\n1. Creating triage system with MCP wrapper tools...")
        registry = ComponentRegistry()
        triage = TriageSystemWrapper(component_registry=registry)
        print("✅ Triage system created")

        # Check available tools
        print("\n2. Checking available tools in geometry agent...")
        geometry_agent = (
            triage.manager.managed_agents[0]
            if hasattr(triage.manager, "managed_agents") and triage.manager.managed_agents
            else None
        )

        if geometry_agent:
            tool_names = [tool.name for tool in geometry_agent.tools if hasattr(tool, "name")]
            print(f"Geometry agent tools: {tool_names}")

            if "create_geometry" in tool_names:
                print("✅ MCP wrapper tools found")
            else:
                print("❌ MCP wrapper tools missing")

        # Test real geometry creation
        print("\n3. Testing real geometry creation...")
        test_request = "Create two points for bridge start and end: Point 1 at (0,0,0) and Point 2 at (100,0,0). Make sure they appear on the Grasshopper canvas."

        print(f"Request: {test_request}")
        response = triage.handle_design_request(test_request)

        print(f"\nResponse Success: {response.success}")
        print(f"Response Message: {response.message[:500]}...")

        # Look for signs of real geometry creation
        if "fallback" in response.message.lower():
            print("❌ Still in fallback mode")
            return False
        elif "created" in response.message.lower() or "generated" in response.message.lower():
            print("✅ Geometry creation attempted")
            return True
        else:
            print("⚠️ Unclear if geometry was created")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_real_mcp_geometry()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
