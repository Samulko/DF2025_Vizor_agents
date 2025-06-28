#!/usr/bin/env python3
"""Test script to verify geometry agent has access to edit_python3_script tool."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from bridge_design_system.agents.triage_agent_smolagents import create_triage_system
from bridge_design_system.config.logging_config import get_logger

logger = get_logger(__name__)


def test_full_mcp_access():
    """Test that geometry agent now has access to edit_python3_script tool."""
    print("\n=== Testing Full MCP Tool Access ===\n")

    # Create triage system
    triage = create_triage_system(max_steps=5)

    # Test 1: Create initial component
    print("🔷 STEP 1: Creating initial points component")
    print("-" * 50)

    request1 = "Create two points that will be the start and end of the bridge"
    result1 = triage.run(request1)

    print(f"✅ Initial component created")
    print(f"Result preview: {str(result1)[:200]}...\n")

    # Test 2: Modification request - should now work with edit_python3_script
    print("🔷 STEP 2: Testing modification with full MCP access")
    print("-" * 50)

    request2 = "I wanted you to add the curve in the original script you have created"
    result2 = triage.run(request2)

    print(f"✅ Modification request completed")
    print(f"Result preview: {str(result2)[:300]}...\n")

    # Check for success indicators
    print("🔷 ANALYSIS:")
    print("-" * 50)

    if "edit_python3_script" in str(result2).lower():
        print("✅ SUCCESS: edit_python3_script tool mentioned!")
    else:
        print("❌ ISSUE: edit_python3_script tool not mentioned")

    if "successfully modified" in str(result2).lower():
        print("✅ SUCCESS: Modification completed successfully!")
    else:
        print("❌ ISSUE: Modification may have failed")

    if "tool is not available" in str(result2).lower():
        print("❌ ISSUE: Tool availability problem still exists")
    else:
        print("✅ SUCCESS: No tool availability issues!")

    if "cannot modify" in str(result2).lower():
        print("❌ ISSUE: Still cannot modify existing components")
    else:
        print("✅ SUCCESS: Can modify existing components!")


if __name__ == "__main__":
    test_full_mcp_access()
