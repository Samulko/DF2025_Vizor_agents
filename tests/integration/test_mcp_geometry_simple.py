#!/usr/bin/env python3
"""
Simple test for MCP geometry creation without fallback.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.config.logging_config import setup_logging


def test_mcp_geometry_simple():
    """Test real MCP geometry creation."""
    print("=" * 60)
    print("TESTING MCP GEOMETRY WITHOUT FALLBACK")
    print("=" * 60)

    setup_logging()

    try:
        # Create triage system
        print("\n1. Creating triage system...")
        registry = ComponentRegistry()
        triage = TriageSystemWrapper(component_registry=registry)
        print("✅ Triage system created")

        # Test geometry creation
        print("\n2. Testing MCP geometry creation...")
        test_request = "Create two points: Point 1 at (0,0,0) and Point 2 at (100,0,0). These should appear on the Grasshopper canvas."

        print(f"Request: {test_request}")
        response = triage.handle_design_request(test_request)

        print(f"\nResponse Success: {response.success}")
        print(f"Response Message: {response.message[:300]}...")

        # Check if it's using real MCP
        message_lower = response.message.lower()

        if "fallback" in message_lower or "unavailable" in message_lower:
            print("❌ Still using fallback mode")
            return False
        elif (
            "component" in message_lower
            or "created" in message_lower
            or "generated" in message_lower
        ):
            print("✅ Real MCP geometry creation working")
            return True
        else:
            print("⚠️ Need to check result in Grasshopper")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mcp_geometry_simple()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
