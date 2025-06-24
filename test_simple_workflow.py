#!/usr/bin/env python3
"""
Simple test script for the fixed three-step orchestrator workflow.
"""

import logging
from pathlib import Path
import sys

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_workflow():
    """Test the fixed three-step workflow with a simple geometry request."""
    
    print("🧪 Testing Fixed Three-Step Orchestrator Workflow")
    print("=" * 60)
    
    # Create triage system wrapper without registry for simple test
    print("🔧 Creating TriageSystemWrapper...")
    triage_system = TriageSystemWrapper()
    
    # Simple test request that should trigger geometry parsing
    test_request = "tell me about material usage from the current components"
    
    print(f"📝 Test Request: {test_request}")
    print("\n🚀 Starting workflow...")
    
    try:
        # Execute the three-step workflow
        result = triage_system.handle_design_request(test_request)
        
        print("\n📊 Workflow Results:")
        print("=" * 40)
        print(f"Success: {result.success}")
        
        if result.success:
            print("✅ Workflow completed successfully!")
            
            # Check the data structure
            if hasattr(result, 'data') and isinstance(result.data, dict):
                print("\nWorkflow Steps:")
                for key, value in result.data.items():
                    if key == "geometry_outcome":
                        print(f"  Step 1 - Geometry Result: {str(value)[:100]}...")
                    elif key == "parsed_elements":
                        print(f"  Step 2 - Parsed Elements: {value}")
                        if value and "elements" in value:
                            element_count = len(value["elements"])
                            print(f"    -> Found {element_count} elements")
                    elif key == "syslogic_analysis":
                        print(f"  Step 3 - SysLogic: {str(value)[:100]}...")
                    elif key == "workflow_status":
                        print(f"  Status: {value}")
                        
            # Specific check for the JSON parsing fix
            if hasattr(result, 'data') and result.data.get("workflow_status") == "completed_successfully":
                print("\n🎉 SUCCESS: The JSON parsing issue has been FIXED!")
                print("🎉 All three workflow steps completed successfully")
            else:
                print("\n⚠️  Workflow completed but may have issues")
        else:
            print(f"❌ Workflow failed: {result.message}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow()