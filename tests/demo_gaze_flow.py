#!/usr/bin/env python
"""
Demonstration of complete gaze integration flow.

This shows how the gaze integration works end-to-end:
1. User issues spatial command: "move this element"
2. System detects spatial intent and passes gaze context
3. Geometry agent receives gazed_object_id and processes accordingly

Usage:
    uv run python tests/demo_gaze_flow.py
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
from src.bridge_design_system.state.component_registry import initialize_registry

def demo_complete_gaze_flow():
    """Demonstrate the complete gaze integration flow."""
    print("🎯 HoloLens Gaze Integration - Complete Flow Demo")
    print("=" * 60)
    
    # Initialize system
    print("🔧 Initializing system...")
    registry = initialize_registry()
    triage_system = TriageSystemWrapper(component_registry=registry)
    print("✅ System ready")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Spatial Command WITH Gaze Context",
            "command": "move this element", 
            "gaze_id": "dynamic_003",
            "expected": "Should receive gaze context and ask for movement details"
        },
        {
            "name": "Spatial Command WITHOUT Gaze Context", 
            "command": "move this element",
            "gaze_id": None,
            "expected": "Should ask which element to move"
        },
        {
            "name": "Non-Spatial Command WITH Gaze Context",
            "command": "what is the material status?",
            "gaze_id": "dynamic_003", 
            "expected": "Should ignore gaze and process material query"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Test {i}: {scenario['name']}")
        print("-" * 50)
        print(f"Command: '{scenario['command']}'")
        print(f"Gaze ID: {scenario['gaze_id']}")
        print(f"Expected: {scenario['expected']}")
        print()
        
        try:
            # Process the request
            response = triage_system.handle_design_request(
                request=scenario['command'],
                gaze_id=scenario['gaze_id']
            )
            
            if response.success:
                print("✅ Request processed successfully")
                # Show key parts of response
                response_text = response.message
                if len(response_text) > 300:
                    print(f"Response: {response_text[:300]}...")
                else:
                    print(f"Response: {response_text}")
            else:
                print(f"❌ Request failed: {response.message}")
                
        except Exception as e:
            print(f"🔥 Exception: {e}")
    
    print("\n🎉 Demo Complete!")
    print("\n💡 Key Observations:")
    print("   • Spatial commands with gaze context get gazed_object_id")
    print("   • Spatial commands without gaze ask for clarification") 
    print("   • Non-spatial commands ignore gaze context")
    print("   • Element ID mapping: dynamic_003 → component_3")

if __name__ == "__main__":
    demo_complete_gaze_flow()