#!/usr/bin/env python3
"""
Quick test to verify category agent works with the TEAM launcher system.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_category_integration():
    """Test category agent integration in the complete system."""
    print("🧪 Testing Category Agent with TEAM System")
    print("=" * 50)
    
    try:
        # Test imports
        from src.bridge_design_system.agents import TriageAgent
        from src.bridge_design_system.state.component_registry import initialize_registry
        from src.bridge_design_system.agents.category_smolagent import (
            calculate_distance, calculate_angles, generate_tags_from_description
        )
        print("✅ All imports successful")
        
        # Test category tools
        print("\n🔧 Testing category tools:")
        distance = calculate_distance([0, 0], [3, 4])
        print(f"  Distance calculation: {distance:.1f}")
        
        angles = calculate_angles([[0, 0], [3, 0], [0, 4]])
        print(f"  Triangle analysis: {len(angles)} angles calculated")
        
        tags = generate_tags_from_description("steel beam structural element")
        print(f"  Tag generation: {len(tags)} tags from description")
        
        # Test triage integration
        print("\n🤖 Testing triage integration:")
        registry = initialize_registry()
        triage = TriageAgent(component_registry=registry)
        status = triage.get_status()
        
        print(f"  Managed agents: {status['triage']['managed_agents']}")
        print(f"  Category agent type: {status['category_agent']['type']}")
        print(f"  Category status: {status['category_agent']['material_analysis']}")
        
        # Verify configuration
        assert status['triage']['managed_agents'] == 1, "Should have 1 managed agent"
        assert status['category_agent']['initialized'] == True, "Category agent should be initialized"
        assert status['category_agent']['material_analysis'] == "enabled", "Material analysis should be enabled"
        assert status['geometry_agent']['initialized'] == False, "Geometry agent should be disabled"
        
        print("\n✅ TEAM Category Integration Test PASSED!")
        print("\n📋 System Ready For:")
        print("  🔹 Material analysis and categorization")
        print("  🔹 Shape and geometry classification")
        print("  🔹 Triangle analysis (equilateral, isosceles, scalene, right, obtuse)")
        print("  🔹 Natural language material descriptions")
        print("  🔹 Material catalog management")
        print("  🔹 Tag generation from descriptions")
        
        print("\n🚀 To test with full TEAM system:")
        print("  python3 start_TEAM.py --interactive")
        print("  Then type: 'Analyze triangle shapes with vertices [[0,0], [3,0], [0,4]]'")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_category_integration()
    sys.exit(0 if success else 1)