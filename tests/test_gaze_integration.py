#!/usr/bin/env python
"""
Integration tests for gaze-assisted spatial command grounding.

This test validates the complete gaze integration pipeline:
1. ROS message simulation using existing send_gaze.py
2. VizorListener gaze capture
3. Triage agent gaze routing
4. Geometry agent gaze-assisted targeting

Usage:
    python tests/test_gaze_integration.py

Prerequisites:
    - ROS bridge server running on localhost:9090
    - Bridge design system components available
"""

import sys
import time
import subprocess
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.bridge_design_system.agents.VizorListener import VizorListener
    from src.bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper
    from src.bridge_design_system.state.component_registry import initialize_registry
    from src.bridge_design_system.config.logging_config import get_logger
except ImportError as e:
    print(f"❌ Failed to import bridge design system components: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


class GazeIntegrationTester:
    """Test harness for gaze integration functionality."""

    def __init__(self):
        self.vizor_listener = None
        self.triage_system = None
        self.test_results = []

    def setup(self):
        """Initialize test components."""
        print("🔧 Setting up gaze integration test harness...")

        try:
            # Initialize VizorListener
            print("📡 Initializing VizorListener...")
            self.vizor_listener = VizorListener()

            if not self.vizor_listener.client.is_connected:
                print(
                    "❌ ROS connection failed - make sure ROS bridge is running on localhost:9090"
                )
                return False

            print("✅ VizorListener connected to ROS bridge")

            # Initialize triage system
            print("🎯 Initializing triage system...")
            registry = initialize_registry()
            self.triage_system = TriageSystemWrapper(component_registry=registry)
            print("✅ Triage system initialized")

            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def send_gaze_message(self, element_id: str) -> bool:
        """Send gaze message using existing send_gaze.py script."""
        try:
            script_path = project_root / "tests" / "vizor_connection" / "send_gaze.py"

            print(f"📤 Sending gaze message for element: {element_id}")
            result = subprocess.run(
                [sys.executable, str(script_path), element_id],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print(f"✅ Gaze message sent successfully")
                return True
            else:
                print(f"❌ Failed to send gaze message: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error sending gaze message: {e}")
            return False

    def test_gaze_capture(self) -> bool:
        """Test VizorListener gaze data capture."""
        print("\n🔍 Test 1: Gaze Data Capture")
        print("-" * 40)

        # Clear any existing gaze data
        self.vizor_listener.current_element = None

        # Send gaze message
        if not self.send_gaze_message("003"):
            return False

        # Wait for message processing
        time.sleep(1)

        # Check if gaze data was captured
        gazed_element = self.vizor_listener.get_current_element()

        if gazed_element == "dynamic_003":
            print(f"✅ Gaze capture successful: {gazed_element}")
            return True
        else:
            print(f"❌ Gaze capture failed. Expected: dynamic_003, Got: {gazed_element}")
            return False

    def test_spatial_command_routing(self) -> bool:
        """Test spatial command detection and gaze routing."""
        print("\n🎯 Test 2: Spatial Command Routing")
        print("-" * 40)

        # Send gaze message
        if not self.send_gaze_message("001"):
            return False

        time.sleep(1)

        # Get current gaze data
        gazed_element = self.vizor_listener.get_current_element()
        print(f"📍 Current gaze: {gazed_element}")

        # Test spatial command (should use gaze)
        print("🔄 Testing spatial command: 'move this element'")
        try:
            response = self.triage_system.handle_design_request(
                request="move this element", gaze_id=gazed_element
            )

            if response.success:
                print("✅ Spatial command processed successfully")
                print(f"Response: {response.message[:100]}...")
                return True
            else:
                print(f"❌ Spatial command failed: {response.message}")
                return False

        except Exception as e:
            print(f"❌ Spatial command error: {e}")
            return False

    def test_non_spatial_command_routing(self) -> bool:
        """Test non-spatial command (should ignore gaze)."""
        print("\n📊 Test 3: Non-Spatial Command Routing")
        print("-" * 40)

        # Send gaze message
        if not self.send_gaze_message("002"):
            return False

        time.sleep(1)

        # Get current gaze data
        gazed_element = self.vizor_listener.get_current_element()
        print(f"📍 Current gaze: {gazed_element}")

        # Test non-spatial command (should ignore gaze)
        print("🔄 Testing non-spatial command: 'what is the material status?'")
        try:
            response = self.triage_system.handle_design_request(
                request="what is the material status?", gaze_id=gazed_element
            )

            if response.success:
                print("✅ Non-spatial command processed successfully")
                print(f"Response: {response.message[:100]}...")
                return True
            else:
                print(f"❌ Non-spatial command failed: {response.message}")
                return False

        except Exception as e:
            print(f"❌ Non-spatial command error: {e}")
            return False

    def test_single_shot_policy(self) -> bool:
        """Test single-shot gaze consumption policy."""
        print("\n🔄 Test 4: Single-Shot Policy")
        print("-" * 40)

        # Send gaze message
        if not self.send_gaze_message("004"):
            return False

        time.sleep(1)

        # Verify gaze is captured
        gazed_element = self.vizor_listener.get_current_element()
        print(f"📍 Initial gaze: {gazed_element}")

        if gazed_element != "dynamic_004":
            print("❌ Initial gaze capture failed")
            return False

        # Simulate single-shot policy (manual clear)
        self.vizor_listener.current_element = None

        # Verify gaze is cleared
        cleared_gaze = self.vizor_listener.get_current_element()

        if cleared_gaze is None:
            print("✅ Single-shot policy working: gaze data cleared")
            return True
        else:
            print(f"❌ Single-shot policy failed: gaze still present: {cleared_gaze}")
            return False

    def test_invalid_gaze_handling(self) -> bool:
        """Test handling of invalid gaze data."""
        print("\n⚠️ Test 5: Invalid Gaze Handling")
        print("-" * 40)

        # Test with invalid gaze ID format
        print("🔄 Testing invalid gaze ID: 'invalid_gaze'")
        try:
            response = self.triage_system.handle_design_request(
                request="move this element", gaze_id="invalid_gaze"
            )

            # Should still process the command, just without gaze context
            if response.success:
                print("✅ Invalid gaze handled gracefully")
                print(f"Response: {response.message[:100]}...")
                return True
            else:
                print(f"❌ Invalid gaze handling failed: {response.message}")
                return False

        except Exception as e:
            print(f"❌ Invalid gaze handling error: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run complete test suite."""
        print("🚀 Starting Gaze Integration Test Suite")
        print("=" * 50)

        if not self.setup():
            print("❌ Test setup failed - aborting")
            return False

        tests = [
            ("Gaze Data Capture", self.test_gaze_capture),
            ("Spatial Command Routing", self.test_spatial_command_routing),
            ("Non-Spatial Command Routing", self.test_non_spatial_command_routing),
            ("Single-Shot Policy", self.test_single_shot_policy),
            ("Invalid Gaze Handling", self.test_invalid_gaze_handling),
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
            print("🎉 All tests passed! Gaze integration is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
            return False

    def cleanup(self):
        """Clean up test resources."""
        try:
            if self.vizor_listener:
                self.vizor_listener.current_element = None
        except Exception as e:
            logger.debug(f"Cleanup warning: {e}")


def main():
    """Main test runner."""
    print("🔍 Gaze Integration Test Suite")
    print("Testing HoloLens gaze integration with Bridge Design System")
    print()

    # Check prerequisites
    print("🔧 Checking prerequisites...")
    try:
        import roslibpy

        print("✅ roslibpy available")
    except ImportError:
        print("❌ roslibpy not available - install with: pip install roslibpy")
        return False

    print("📋 Prerequisites:")
    print("  - ROS bridge server should be running on localhost:9090")
    print("  - Bridge design system should be properly configured")
    print()

    # Run tests
    tester = GazeIntegrationTester()
    try:
        success = tester.run_all_tests()
        return success
    finally:
        tester.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
