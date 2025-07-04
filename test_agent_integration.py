#!/usr/bin/env python3
"""
Test script to verify surface_agent and category_agent integration into the triage system.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_agent_imports():
    """Test that the agents can be imported correctly."""
    try:
        from bridge_design_system.agents.surface_agent import create_surface_agent
        from bridge_design_system.agents.category_smolagent import create_category_agent
        from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
        print("✅ All agents imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_triage_system_creation():
    """Test that the triage system can be created with the new agents."""
    try:
        from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
        
        # Test wrapper
        triage_wrapper = TriageSystemWrapper()
        print("✅ Triage system wrapper created successfully")
        
        # Check status
        status = triage_wrapper.get_status()
        print(f"✅ Status retrieved: {status['triage']['managed_agents']} managed agents")
        
        # Verify all agents are present
        expected_agents = ["surface_agent", "category_agent", "design_agent"]
        for agent_name in expected_agents:
            if agent_name in status:
                print(f"✅ {agent_name} is properly initialized")
            else:
                print(f"❌ {agent_name} is missing from status")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error creating triage system: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing surface_agent and category_agent integration...")
    print("=" * 60)
    
    # Test imports
    if not test_agent_imports():
        sys.exit(1)
    
    # Test triage system creation
    if not test_triage_system_creation():
        sys.exit(1)
    
    print("=" * 60)
    print("✅ All tests passed! Integration is working correctly.")

if __name__ == "__main__":
    main()