#!/usr/bin/env python3
"""Test script to verify the memory synchronization fix."""

import sys
import time

# Add project root to path
sys.path.insert(0, "/home/samko/github/vizor_agents/src")

from bridge_design_system.agents.triage_agent_smolagents import create_triage_system
from bridge_design_system.config.logging_config import get_logger

logger = get_logger(__name__)


def test_component_tracking():
    """Test the improved component tracking system."""
    print("\n=== Testing Component Tracking Fix ===\n")
    
    # Create triage system
    print("1. Creating triage system...")
    triage = create_triage_system()
    print("✅ Triage system created\n")
    
    # Test 1: Create some points
    print("2. Testing point creation...")
    result1 = triage.run("Create two bridge points for testing")
    print(f"Result: {result1}\n")
    
    # Give it a moment to process
    time.sleep(1)
    
    # Test 2: Check component tracking
    print("3. Testing component tracking...")
    result2 = triage.run("Use the debug_component_tracking tool to show current tracked components")
    print(f"Debug info: {result2}\n")
    
    # Test 3: Try to reference recent work
    print("4. Testing follow-up reference...")
    result3 = triage.run("Connect the two points you just created with a curve")
    print(f"Result: {result3}\n")
    
    # Test 4: Check tracking again
    print("5. Checking component tracking after curve creation...")
    result4 = triage.run("Use debug_component_tracking to show tracked components again")
    print(f"Debug info: {result4}\n")
    
    # Test 5: Try modification request
    print("6. Testing modification request...")
    result5 = triage.run("Modify the curve you just drew to be an arch")
    print(f"Result: {result5}\n")
    
    print("\n=== Test Complete ===\n")
    

def test_memory_tools():
    """Test the new memory tools."""
    print("\n=== Testing Memory Tools ===\n")
    
    # Create triage system
    triage = create_triage_system()
    
    # Test get_current_valid_components
    print("1. Testing get_current_valid_components...")
    result1 = triage.run("Use get_current_valid_components to show tracked components")
    print(f"Result: {result1}\n")
    
    # Test get_most_recent_component
    print("2. Testing get_most_recent_component...")
    result2 = triage.run("Use get_most_recent_component to find the most recent bridge_curve")
    print(f"Result: {result2}\n")
    
    print("\n=== Memory Tools Test Complete ===\n")


if __name__ == "__main__":
    print("Starting component tracking and memory synchronization tests...")
    
    try:
        test_component_tracking()
        # test_memory_tools()  # Uncomment to test memory tools separately
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
    
    print("✅ All tests completed!")