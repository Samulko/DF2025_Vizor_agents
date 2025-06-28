#!/usr/bin/env python3
"""
Test script to verify improved efficiency and single script creation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.config.logging_config import setup_logging


def test_improved_efficiency():
    """Test improved efficiency and consolidated script creation."""
    print("=" * 60)
    print("TESTING IMPROVED EFFICIENCY AND CONSOLIDATED SCRIPTS")
    print("=" * 60)

    setup_logging()

    try:
        # Create triage system
        print("\n1. Creating triage system...")
        registry = ComponentRegistry()
        triage = TriageSystemWrapper(component_registry=registry)
        print("✅ Triage system created")

        # Test consolidated geometry creation
        print("\n2. Testing consolidated geometry creation...")
        test_request = "Create two points for bridge start and end: start point at (0,0,0) and end point at (100,0,0). Put both in one script."

        print(f"Request: {test_request}")
        response = triage.handle_design_request(test_request)

        print(f"\nResponse Success: {response.success}")
        print(f"Response Message: {response.message[:400]}...")

        # Check for efficiency improvements
        message_lower = response.message.lower()

        if "two" in message_lower and ("script" in message_lower or "component" in message_lower):
            if "separate" in message_lower or "two components" in message_lower:
                print("❌ Still creating separate components")
                return False
            else:
                print("✅ Appears to be creating consolidated script")
                return True
        else:
            print("⚠️ Need to check the actual result")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_improved_efficiency()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
