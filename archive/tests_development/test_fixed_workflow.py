#!/usr/bin/env python3
"""
Test script for the fixed three-step orchestrator workflow.
"""

import logging
from pathlib import Path
import sys

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
from bridge_design_system.state.component_registry import GlobalComponentRegistry

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_workflow():
    """Test the fixed three-step workflow with the same request that was failing."""
    
    print("🧪 Testing Fixed Three-Step Orchestrator Workflow")
    print("=" * 60)
    
    # Initialize component registry
    registry = GlobalComponentRegistry.get_instance()
    
    # Create triage system wrapper
    print("🔧 Creating TriageSystemWrapper...")
    triage_system = TriageSystemWrapper(
        component_registry=registry
    )
    
    # Test request - same one that was failing before
    test_request = "check the @current_task.md and check out this issue I am having"
    
    print(f"📝 Test Request: {test_request}")
    print("\n🚀 Starting workflow...")
    
    try:
        # Execute the three-step workflow
        result = triage_system.handle_design_request(test_request)
        
        print("\n📊 Workflow Results:")
        print("=" * 40)
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        
        if hasattr(result, 'data') and isinstance(result.data, dict):
            print("\nDetailed Results:")
            for key, value in result.data.items():
                print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        
        # Check if we fixed the JSON parsing issue
        if result.success and "parsed_elements" in str(result.data):
            print("\n✅ SUCCESS: Three-step workflow completed!")
            print("✅ The JSON parsing issue has been resolved")
        else:
            print("\n❌ ISSUE: Workflow did not complete as expected")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow()