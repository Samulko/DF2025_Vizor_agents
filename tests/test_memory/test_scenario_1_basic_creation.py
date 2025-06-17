"""
Test Scenario 1: Basic Creation and Component ID Tracking Validation

This test validates that:
1. Components are created successfully
2. Component IDs are tracked in memory
3. Component tracking persists across agent interactions
4. No stale component ID errors occur
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import get_test_state_summary, get_components_by_type


class TestBasicCreationAndTracking(MemoryTestCase):
    """Test basic component creation and ID tracking."""
    
    def test_create_single_bridge_curve(self):
        """Test creating a single bridge curve and verifying tracking."""
        print("\n=== Test: Create Single Bridge Curve ===")
        
        # Initial state - should be empty
        initial_state = self.config.get_memory_state()
        print(f"Initial memory state: {initial_state}")
        self.assertEqual(initial_state["recent_components_count"], 0)
        
        # Create a bridge curve
        user_request = "Create a bridge curve with 5 control points spanning 50 meters"
        print(f"User request: {user_request}")
        
        response = self.config.simulate_user_request(user_request)
        print(f"Agent response: {response}")
        
        # Verify memory state after creation
        final_state = self.config.get_memory_state()
        print(f"Final memory state: {final_state}")
        
        # Assertions
        self.assertGreater(final_state["recent_components_count"], 0, 
                          "Component should be tracked in recent_components")
        self.assertGreater(final_state["triage_memory_steps"], 0,
                          "Triage agent should have memory steps")
        
        # Verify component exists in mock state
        mock_summary = final_state["mock_state_summary"]
        print(f"Mock state summary: {mock_summary}")
        self.assertGreater(mock_summary["total_components"], 0,
                          "Should have created at least one component")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        # Verify bridge curve was detected
        bridge_curves = get_components_by_type("bridge_curve")
        print(f"Bridge curves found: {len(bridge_curves)}")
        self.assertGreater(len(bridge_curves), 0, "Should have created a bridge curve")
        
        print("✅ Single bridge curve creation test passed")
        
    def test_create_multiple_components_sequential(self):
        """Test creating multiple components sequentially and tracking all."""
        print("\n=== Test: Create Multiple Components Sequential ===")
        
        # Create bridge points first
        response1 = self.config.simulate_user_request(
            "Create bridge foundation points for a 40-meter span"
        )
        print(f"Response 1 (points): {response1}")
        
        # Check intermediate state
        intermediate_state = self.config.get_memory_state()
        print(f"Intermediate state: {intermediate_state}")
        
        # Create bridge curve
        response2 = self.config.simulate_user_request(
            "Create a bridge curve connecting the foundation points"
        )
        print(f"Response 2 (curve): {response2}")
        
        # Verify final state
        final_state = self.config.get_memory_state()
        print(f"Final memory state: {final_state}")
        
        # Assertions
        self.assertGreaterEqual(final_state["recent_components_count"], 2,
                               "Should track multiple components")
        
        # Verify different component types were created
        mock_summary = final_state["mock_state_summary"]
        print(f"Components by type: {mock_summary['components_by_type']}")
        
        # Should have both bridge_points and bridge_curve
        bridge_points = get_components_by_type("bridge_points")
        bridge_curves = get_components_by_type("bridge_curve")
        
        print(f"Bridge points: {len(bridge_points)}, Bridge curves: {len(bridge_curves)}")
        self.assertGreater(len(bridge_points), 0, "Should have bridge points")
        self.assertGreater(len(bridge_curves), 0, "Should have bridge curve")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Multiple components sequential test passed")
        
    def test_component_id_persistence(self):
        """Test that component IDs persist across multiple requests."""
        print("\n=== Test: Component ID Persistence ===")
        
        # Create initial component
        response1 = self.config.simulate_user_request(
            "Create a bridge arch with 8-meter height"
        )
        print(f"Initial creation: {response1}")
        
        # Get initial component info
        initial_state = self.config.get_memory_state()
        initial_components = initial_state["recent_components"]
        print(f"Initial tracked components: {initial_components}")
        
        # Make another request that should reference existing components
        response2 = self.config.simulate_user_request(
            "Show me the current component status"
        )
        print(f"Status check: {response2}")
        
        # Verify persistence
        final_state = self.config.get_memory_state()
        final_components = final_state["recent_components"]
        print(f"Final tracked components: {final_components}")
        
        # Component tracking should persist
        self.assertGreaterEqual(len(final_components), len(initial_components),
                               "Component tracking should persist")
        
        # Memory steps should increase
        self.assertGreater(final_state["triage_memory_steps"], 
                          initial_state["triage_memory_steps"],
                          "Memory should accumulate across requests")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Component ID persistence test passed")
        
    def test_memory_tools_functionality(self):
        """Test that memory tools work correctly."""
        print("\n=== Test: Memory Tools Functionality ===")
        
        # Create a component
        response1 = self.config.simulate_user_request(
            "Create a bridge curve for testing memory tools"
        )
        print(f"Created component: {response1}")
        
        # Test get_most_recent_component tool
        response2 = self.config.simulate_user_request(
            "What was the most recent bridge component I created?"
        )
        print(f"Most recent query: {response2}")
        
        # Test debug_component_tracking tool
        response3 = self.config.simulate_user_request(
            "Debug the current component tracking state"
        )
        print(f"Debug output: {response3}")
        
        # Verify memory state
        final_state = self.config.get_memory_state()
        print(f"Final memory state: {final_state}")
        
        # Should have tracked interactions
        self.assertGreater(final_state["triage_memory_steps"], 2,
                          "Should have multiple memory steps")
        self.assertGreater(final_state["recent_components_count"], 0,
                          "Should have tracked components")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Memory tools functionality test passed")
        
    def test_component_creation_with_validation(self):
        """Test component creation with comprehensive validation."""
        print("\n=== Test: Component Creation with Validation ===")
        
        # Test different component types
        test_requests = [
            "Create bridge foundation points at coordinates (0,0) and (50,0)",
            "Generate a bridge curve with parametric control",
            "Design an arch structure with 10-meter height"
        ]
        
        responses = []
        for i, request in enumerate(test_requests):
            print(f"\nRequest {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            responses.append(response)
            print(f"Response {i+1}: {response}")
            
            # Verify state after each request
            state = self.config.get_memory_state()
            print(f"State after request {i+1}: recent_components={state['recent_components_count']}")
            
        # Final validation
        final_state = self.config.get_memory_state()
        mock_summary = final_state["mock_state_summary"]
        
        print(f"\nFinal validation:")
        print(f"Total components: {mock_summary['total_components']}")
        print(f"Components by type: {mock_summary['components_by_type']}")
        print(f"Recent components tracked: {final_state['recent_components_count']}")
        
        # Assertions
        self.assertGreaterEqual(mock_summary["total_components"], 3,
                               "Should have created at least 3 components")
        self.assertGreater(final_state["recent_components_count"], 0,
                          "Should track recent components")
        self.assertEqual(mock_summary["components_with_errors"], 0,
                        "No components should have errors")
        
        # Verify no stale component errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Component creation with validation test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)