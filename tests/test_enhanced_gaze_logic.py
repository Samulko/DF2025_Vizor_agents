#!/usr/bin/env python
"""
Test enhanced gaze logic with sophisticated LLM reasoning.

This test validates that the enhanced gaze integration correctly handles:
1. Spatial commands that should use gaze context
2. Abstract commands that should ignore gaze context
3. Ambiguous commands that should ask for clarification

Usage:
    uv run python tests/test_enhanced_gaze_logic.py
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
    from src.bridge_design_system.state.component_registry import initialize_registry
    from src.bridge_design_system.config.logging_config import get_logger
except ImportError as e:
    print(f"❌ Failed to import bridge design system components: {e}")
    sys.exit(1)

logger = get_logger(__name__)

class EnhancedGazeLogicTester:
    """Test harness for enhanced gaze integration logic."""
    
    def __init__(self):
        self.triage_system = None
        self.test_results = []
        
    def setup(self):
        """Initialize test components."""
        print("🔧 Setting up enhanced gaze logic test harness...")
        
        try:
            print("🎯 Initializing triage system...")
            registry = initialize_registry()
            self.triage_system = TriageSystemWrapper(component_registry=registry)
            print("✅ Triage system initialized")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def test_spatial_command_with_gaze(self) -> bool:
        """Test spatial command that should use gaze context."""
        print("\\n🎯 Test 1: Spatial Command WITH Gaze Context")
        print("-" * 50)
        
        try:
            # This should delegate to geometry agent WITH gaze context
            response = self.triage_system.handle_design_request(
                "rotate this element a bit",
                gaze_id="dynamic_007"
            )
            
            if response.success:
                print("✅ Spatial command processed successfully")
                response_text = response.message.lower()
                
                # Check if the response indicates it's working with geometry/spatial context
                spatial_indicators = ["geometry", "rotate", "element", "component", "move"]
                has_spatial_context = any(indicator in response_text for indicator in spatial_indicators)
                
                if has_spatial_context:
                    print("✅ Response contains spatial/geometric context")
                    return True
                else:
                    print("❌ Response lacks expected spatial context")
                    print(f"Response: {response.message[:200]}...")
                    return False
                    
            else:
                print(f"❌ Spatial command failed: {response.message}")
                return False
                
        except Exception as e:
            print(f"❌ Exception in spatial command test: {e}")
            return False
    
    def test_abstract_command_with_gaze(self) -> bool:
        """Test abstract command that should ignore gaze context."""
        print("\\n📊 Test 2: Abstract Command WITH Gaze Context (Should Ignore Gaze)")
        print("-" * 50)
        
        try:
            # This should ignore gaze and route to appropriate agent (not geometry)
            response = self.triage_system.handle_design_request(
                "what is the status of this material inventory?",
                gaze_id="dynamic_004"
            )
            
            if response.success:
                print("✅ Abstract command processed successfully")
                response_text = response.message.lower()
                
                # Check if response is about materials/inventory, not about the gazed object
                material_indicators = ["material", "inventory", "status", "syslogic"]
                has_material_context = any(indicator in response_text for indicator in material_indicators)
                
                # Should NOT contain references to the specific gazed object
                gaze_object_references = ["dynamic_004", "component_4", "object you're looking at"]
                has_gaze_reference = any(ref in response_text for ref in gaze_object_references)
                
                if has_material_context and not has_gaze_reference:
                    print("✅ Response correctly focuses on material inventory, ignores gaze")
                    return True
                elif has_gaze_reference:
                    print("❌ Response incorrectly references gazed object")
                    print(f"Response: {response.message[:200]}...")
                    return False
                else:
                    print("❌ Response doesn't address material inventory properly")
                    print(f"Response: {response.message[:200]}...")
                    return False
                    
            else:
                print(f"❌ Abstract command failed: {response.message}")
                return False
                
        except Exception as e:
            print(f"❌ Exception in abstract command test: {e}")
            return False
    
    def test_ambiguous_command_with_gaze(self) -> bool:
        """Test ambiguous command that should ask for clarification."""
        print("\\n❓ Test 3: Ambiguous Command WITH Gaze Context (Should Ask for Clarification)")
        print("-" * 50)
        
        try:
            # This should ask for clarification rather than assume intent
            response = self.triage_system.handle_design_request(
                "let's review this",
                gaze_id="dynamic_002"
            )
            
            if response.success:
                print("✅ Ambiguous command processed successfully")
                response_text = response.message.lower()
                
                # Check if response asks for clarification
                clarification_indicators = [
                    "clarify", "clarification", "what do you mean", "could you specify",
                    "are you interested in", "which", "what kind", "what aspect"
                ]
                asks_clarification = any(indicator in response_text for indicator in clarification_indicators)
                
                if asks_clarification:
                    print("✅ Response correctly asks for clarification")
                    return True
                else:
                    print("❌ Response should ask for clarification but doesn't")
                    print(f"Response: {response.message[:200]}...")
                    return False
                    
            else:
                print(f"❌ Ambiguous command failed: {response.message}")
                return False
                
        except Exception as e:
            print(f"❌ Exception in ambiguous command test: {e}")
            return False
    
    def test_approach_question_with_gaze(self) -> bool:
        """Test abstract approach question that should ignore gaze."""
        print("\\n💭 Test 4: Abstract Approach Question (Should Ignore Gaze)")
        print("-" * 50)
        
        try:
            # This should ignore gaze and respond about methodology/approach
            response = self.triage_system.handle_design_request(
                "what do you think about this approach?",
                gaze_id="dynamic_001"
            )
            
            if response.success:
                print("✅ Approach question processed successfully")
                response_text = response.message.lower()
                
                # Should NOT reference the specific gazed object
                gaze_object_references = ["dynamic_001", "component_1", "object you're looking at"]
                has_gaze_reference = any(ref in response_text for ref in gaze_object_references)
                
                # Should ask for clarification about approach or respond about methodology
                approach_indicators = ["approach", "methodology", "strategy", "clarify", "which approach"]
                handles_approach = any(indicator in response_text for indicator in approach_indicators)
                
                if not has_gaze_reference and handles_approach:
                    print("✅ Response correctly ignores gaze and addresses approach question")
                    return True
                elif has_gaze_reference:
                    print("❌ Response incorrectly references gazed object")
                    print(f"Response: {response.message[:200]}...")
                    return False
                else:
                    print("❌ Response doesn't properly handle approach question")
                    print(f"Response: {response.message[:200]}...")
                    return False
                    
            else:
                print(f"❌ Approach question failed: {response.message}")
                return False
                
        except Exception as e:
            print(f"❌ Exception in approach question test: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run complete enhanced gaze logic test suite."""
        print("🚀 Starting Enhanced Gaze Logic Test Suite")
        print("=" * 60)
        
        if not self.setup():
            print("❌ Test setup failed - aborting")
            return False
        
        tests = [
            ("Spatial Command with Gaze", self.test_spatial_command_with_gaze),
            ("Abstract Command Ignoring Gaze", self.test_abstract_command_with_gaze),
            ("Ambiguous Command Clarification", self.test_ambiguous_command_with_gaze),
            ("Abstract Approach Question", self.test_approach_question_with_gaze),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    self.test_results.append((test_name, "PASS"))
                else:
                    self.test_results.append((test_name, "FAIL"))
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {e}")
                self.test_results.append((test_name, f"ERROR: {e}"))
        
        # Print summary
        print("\\n📊 Enhanced Gaze Logic Test Results")
        print("=" * 60)
        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        print(f"\\nPassed: {passed}/{total} tests")
        
        if passed == total:
            print("🎉 All tests passed! Enhanced gaze logic is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. The LLM-based reasoning may need refinement.")
            return False

def main():
    """Main test runner."""
    print("🧠 Enhanced Gaze Integration Logic Test Suite")
    print("Testing sophisticated LLM reasoning for gaze relevance detection")
    print()
    
    # Run tests
    tester = EnhancedGazeLogicTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)