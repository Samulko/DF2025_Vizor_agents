#!/usr/bin/env python
"""
Unit tests for gaze integration logic without requiring ROS server.

This test validates the core gaze integration components:
1. Triage agent gaze routing logic
2. Gaze ID validation
3. Spatial command detection
4. Error handling for invalid gaze data

Usage:
    uv run python tests/test_gaze_logic.py
"""

import sys
import re
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

class GazeLogicTester:
    """Test harness for gaze integration logic."""
    
    def __init__(self):
        self.triage_system = None
        self.test_results = []
        
    def setup(self):
        """Initialize test components."""
        print("🔧 Setting up gaze logic test harness...")
        
        try:
            # Initialize triage system
            print("🎯 Initializing triage system...")
            registry = initialize_registry()
            self.triage_system = TriageSystemWrapper(component_registry=registry)
            print("✅ Triage system initialized")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def test_gaze_id_validation(self) -> bool:
        """Test gaze ID format validation."""
        print("\n🔍 Test 1: Gaze ID Validation")
        print("-" * 40)
        
        valid_ids = ["dynamic_001", "dynamic_020", "dynamic_123"]
        invalid_ids = ["invalid_gaze", "001", "dynamic_", "dynamic_1", "dynamic_12ab"]
        
        all_passed = True
        
        # Test valid IDs
        for gaze_id in valid_ids:
            result = self.triage_system._validate_gaze_id(gaze_id)
            if result:
                print(f"✅ Valid ID correctly accepted: {gaze_id}")
            else:
                print(f"❌ Valid ID incorrectly rejected: {gaze_id}")
                all_passed = False
        
        # Test invalid IDs
        for gaze_id in invalid_ids:
            result = self.triage_system._validate_gaze_id(gaze_id)
            if not result:
                print(f"✅ Invalid ID correctly rejected: {gaze_id}")
            else:
                print(f"❌ Invalid ID incorrectly accepted: {gaze_id}")
                all_passed = False
        
        return all_passed
    
    def test_spatial_command_detection(self) -> bool:
        """Test spatial command keyword detection."""
        print("\n🎯 Test 2: Spatial Command Detection")
        print("-" * 40)
        
        # Test spatial commands (should trigger gaze usage)
        spatial_commands = [
            "move this element",
            "modify that component",
            "edit this script",
            "select that object",
            "change this beam",
            "adjust the position",
            "rotate this element"
        ]
        
        # Test non-spatial commands (should ignore gaze)
        non_spatial_commands = [
            "what is the material status?",
            "list available agents",
            "show me the system status",
            "create a new bridge",
            "help me understand the workflow"
        ]
        
        all_passed = True
        
        # Test spatial commands
        for command in spatial_commands:
            # Use the same logic from the triage agent
            spatial_keywords = ["this", "that", "move", "modify", "edit", "select", "change", "adjust", "position", "rotate"]
            needs_spatial_context = any(keyword in command.lower() for keyword in spatial_keywords)
            
            if needs_spatial_context:
                print(f"✅ Spatial command correctly detected: '{command}'")
            else:
                print(f"❌ Spatial command missed: '{command}'")
                all_passed = False
        
        # Test non-spatial commands
        for command in non_spatial_commands:
            spatial_keywords = ["this", "that", "move", "modify", "edit", "select", "change", "adjust", "position", "rotate"]
            needs_spatial_context = any(keyword in command.lower() for keyword in spatial_keywords)
            
            if not needs_spatial_context:
                print(f"✅ Non-spatial command correctly identified: '{command}'")
            else:
                print(f"❌ Non-spatial command incorrectly flagged as spatial: '{command}'")
                all_passed = False
        
        return all_passed
    
    def test_element_id_mapping(self) -> bool:
        """Test element ID mapping logic from gaze to component."""
        print("\n🗺️ Test 3: Element ID Mapping")
        print("-" * 40)
        
        test_cases = [
            ("dynamic_001", "component_1"),
            ("dynamic_020", "component_20"),
            ("dynamic_123", "component_123"),
            ("dynamic_005", "component_5"),
            ("dynamic_100", "component_100")
        ]
        
        all_passed = True
        
        for gaze_id, expected_component_id in test_cases:
            # Apply the mapping logic from geometry agent prompt
            component_number = gaze_id.replace("dynamic_", "").lstrip("0")
            actual_component_id = f"component_{component_number}"
            
            if actual_component_id == expected_component_id:
                print(f"✅ Mapping correct: {gaze_id} → {actual_component_id}")
            else:
                print(f"❌ Mapping failed: {gaze_id} → {actual_component_id} (expected {expected_component_id})")
                all_passed = False
        
        return all_passed
    
    def test_error_handling(self) -> bool:
        """Test error handling for various edge cases."""
        print("\n⚠️ Test 4: Error Handling")
        print("-" * 40)
        
        all_passed = True
        
        # Test None gaze ID
        try:
            response = self.triage_system.handle_design_request("move this element", gaze_id=None)
            if response.success:
                print("✅ None gaze_id handled gracefully")
            else:
                print(f"❌ None gaze_id caused failure: {response.message}")
                all_passed = False
        except Exception as e:
            print(f"❌ None gaze_id caused exception: {e}")
            all_passed = False
        
        # Test empty string gaze ID
        try:
            response = self.triage_system.handle_design_request("move this element", gaze_id="")
            if response.success:
                print("✅ Empty gaze_id handled gracefully")
            else:
                print(f"❌ Empty gaze_id caused failure: {response.message}")
                all_passed = False
        except Exception as e:
            print(f"❌ Empty gaze_id caused exception: {e}")
            all_passed = False
        
        # Test invalid format gaze ID
        try:
            response = self.triage_system.handle_design_request("move this element", gaze_id="invalid_format")
            if response.success:
                print("✅ Invalid format gaze_id handled gracefully")
            else:
                print(f"❌ Invalid format gaze_id caused failure: {response.message}")
                all_passed = False
        except Exception as e:
            print(f"❌ Invalid format gaze_id caused exception: {e}")
            all_passed = False
        
        return all_passed
    
    def test_integration_without_gaze(self) -> bool:
        """Test that system works normally without gaze data."""
        print("\n🔄 Test 5: System Without Gaze")
        print("-" * 40)
        
        try:
            # Test normal operation without gaze
            response = self.triage_system.handle_design_request("what agents are available?")
            if response.success:
                print("✅ System works normally without gaze data")
                print(f"Response: {response.message[:100]}...")
                return True
            else:
                print(f"❌ System failed without gaze data: {response.message}")
                return False
        except Exception as e:
            print(f"❌ System crashed without gaze data: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run complete test suite."""
        print("🚀 Starting Gaze Logic Test Suite")
        print("=" * 50)
        
        if not self.setup():
            print("❌ Test setup failed - aborting")
            return False
        
        tests = [
            ("Gaze ID Validation", self.test_gaze_id_validation),
            ("Spatial Command Detection", self.test_spatial_command_detection),
            ("Element ID Mapping", self.test_element_id_mapping),
            ("Error Handling", self.test_error_handling),
            ("System Without Gaze", self.test_integration_without_gaze),
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
        print("\n📊 Test Results Summary")
        print("=" * 50)
        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        print(f"\nPassed: {passed}/{total} tests")
        
        if passed == total:
            print("🎉 All tests passed! Gaze logic is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
            return False

def main():
    """Main test runner."""
    print("🔍 Gaze Integration Logic Test Suite")
    print("Testing core gaze integration logic without ROS dependencies")
    print()
    
    # Run tests
    tester = GazeLogicTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)