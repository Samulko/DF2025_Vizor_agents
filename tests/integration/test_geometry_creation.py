#!/usr/bin/env python3
"""
Test script to verify geometry creation functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.config.logging_config import setup_logging


def test_geometry_creation():
    """Test geometry creation with specific request."""
    print("=" * 60)
    print("TESTING GEOMETRY CREATION")
    print("=" * 60)

    setup_logging()

    try:
        # Create triage system
        print("\n1. Creating triage system...")
        registry = ComponentRegistry()
        triage = TriageSystemWrapper(component_registry=registry)
        print("✅ Triage system created")

        # Test specific geometry request
        print("\n2. Testing specific geometry creation...")
        test_request = "Create two points to mark the start and end of a bridge. Point 1 at (0,0,0) and Point 2 at (100,0,0)."

        print(f"Request: {test_request}")
        response = triage.handle_design_request(test_request)

        print(f"\nResponse Success: {response.success}")
        print(f"Response Message: {response.message}")

        if response.success:
            print("✅ Geometry request processed successfully")
        else:
            print("❌ Geometry request failed")

        # Check memory
        print("\n3. Testing memory functionality...")
        memory_request = "What was the last geometry task I asked you to perform?"
        memory_response = triage.handle_design_request(memory_request)

        print(f"Memory Response: {memory_response.message[:200]}...")

        return response.success

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_geometry_creation()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
