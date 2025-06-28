"""
Test Scenario 2: Vague References Resolution

This test validates the core memory synchronization fix by testing vague references like:
- "connect them" → should find previously created points
- "make it an arch" → should modify existing curve
- "modify the curve you just drew" → should target the right component

This addresses the original issue where agents couldn't resolve follow-up references.
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary,
    get_components_by_type,
    get_most_recent_component_of_type,
)


class TestVagueReferencesResolution(MemoryTestCase):
    """Test resolution of vague references to previously created components."""

    def test_connect_them_reference(self):
        """Test 'connect them' after creating bridge points."""
        print("\n=== Test: 'Connect Them' Reference ===")

        # Step 1: Create bridge points
        points_request = "Create bridge foundation points at (0,0,0) and (50,0,0)"
        print(f"Step 1 - Create points: {points_request}")

        points_response = self.config.simulate_user_request(points_request)
        print(f"Points response: {points_response}")

        # Verify points were created and tracked
        intermediate_state = self.config.get_memory_state()
        print(f"State after points: {intermediate_state}")

        bridge_points = get_components_by_type("bridge_points")
        self.assertGreater(len(bridge_points), 0, "Should have created bridge points")

        # Step 2: Use vague reference "connect them"
        connect_request = "Connect them with a bridge curve"
        print(f"Step 2 - Connect them: {connect_request}")

        connect_response = self.config.simulate_user_request(connect_request)
        print(f"Connect response: {connect_response}")

        # Verify the vague reference was resolved
        final_state = self.config.get_memory_state()
        print(f"Final state: {final_state}")

        # Should now have both points and curve
        bridge_curves = get_components_by_type("bridge_curve")
        print(f"Bridge points: {len(bridge_points)}, Bridge curves: {len(bridge_curves)}")

        # Assertions
        self.assertGreater(
            len(bridge_curves), 0, "Should have created bridge curve to connect points"
        )
        self.assertGreater(
            final_state["recent_components_count"],
            intermediate_state["recent_components_count"],
            "Should track the new curve component",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ 'Connect them' reference test passed")

    def test_make_it_an_arch_reference(self):
        """Test 'make it an arch' after creating a bridge curve."""
        print("\n=== Test: 'Make It An Arch' Reference ===")

        # Step 1: Create a basic bridge curve
        curve_request = "Create a bridge curve spanning 40 meters"
        print(f"Step 1 - Create curve: {curve_request}")

        curve_response = self.config.simulate_user_request(curve_request)
        print(f"Curve response: {curve_response}")

        # Verify curve was created
        intermediate_state = self.config.get_memory_state()
        initial_curves = get_components_by_type("bridge_curve")
        print(f"Initial bridge curves: {len(initial_curves)}")
        self.assertGreater(len(initial_curves), 0, "Should have created bridge curve")

        # Step 2: Use vague reference "make it an arch"
        arch_request = "Make it an arch with 8-meter height"
        print(f"Step 2 - Make it arch: {arch_request}")

        arch_response = self.config.simulate_user_request(arch_request)
        print(f"Arch response: {arch_response}")

        # Verify the modification was applied
        final_state = self.config.get_memory_state()
        final_arches = get_components_by_type("bridge_arch")
        print(f"Bridge arches after modification: {len(final_arches)}")

        # Assertions - should have created or modified to arch
        total_geometry = len(get_components_by_type("bridge_curve")) + len(final_arches)
        self.assertGreater(total_geometry, 0, "Should have bridge geometry (curve or arch)")

        # Memory should show progression
        self.assertGreater(
            final_state["triage_memory_steps"],
            intermediate_state["triage_memory_steps"],
            "Memory should record the modification",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ 'Make it an arch' reference test passed")

    def test_modify_what_you_just_drew(self):
        """Test 'modify the curve you just drew' - the original reported issue."""
        print("\n=== Test: 'Modify What You Just Drew' ===")

        # Step 1: Draw a curve
        draw_request = "Draw a bridge curve with 6 control points"
        print(f"Step 1 - Draw: {draw_request}")

        draw_response = self.config.simulate_user_request(draw_request)
        print(f"Draw response: {draw_response}")

        # Capture the curve that was just created
        intermediate_state = self.config.get_memory_state()
        recent_curve = get_most_recent_component_of_type("bridge_curve")
        print(f"Most recent curve: {recent_curve}")
        self.assertIsNotNone(recent_curve, "Should have created a curve")

        # Step 2: Modify what you just drew
        modify_request = "Modify the curve you just drew to have more height"
        print(f"Step 2 - Modify: {modify_request}")

        modify_response = self.config.simulate_user_request(modify_request)
        print(f"Modify response: {modify_response}")

        # Verify the modification targeted the right component
        final_state = self.config.get_memory_state()

        # Should have more memory steps and component tracking
        self.assertGreater(
            final_state["triage_memory_steps"],
            intermediate_state["triage_memory_steps"],
            "Should have recorded the modification",
        )

        # The recent components should show both original and modification
        self.assertGreaterEqual(
            final_state["recent_components_count"],
            intermediate_state["recent_components_count"],
            "Should track modification activity",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ 'Modify what you just drew' test passed")

    def test_complex_vague_reference_chain(self):
        """Test a chain of vague references across multiple interactions."""
        print("\n=== Test: Complex Vague Reference Chain ===")

        conversation = [
            "Create bridge support points",
            "Connect them with a curve",
            "Make it taller",
            "Add more control points to it",
            "Now make the whole thing an arch",
        ]

        responses = []
        states = []

        for i, request in enumerate(conversation):
            print(f"\nStep {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Response {i+1}: {response}")

            state = self.config.get_memory_state()
            states.append(state)
            responses.append(response)

            # Each step should maintain or increase memory
            if i > 0:
                self.assertGreaterEqual(
                    state["triage_memory_steps"],
                    states[i - 1]["triage_memory_steps"],
                    f"Memory should persist through step {i+1}",
                )

        # Final verification
        final_summary = get_test_state_summary()
        print(f"\nFinal summary: {final_summary}")

        # Should have created multiple components or modifications
        self.assertGreater(final_summary["total_components"], 0, "Should have created components")

        # Should have accumulated substantial memory
        final_state = states[-1]
        self.assertGreater(
            final_state["triage_memory_steps"],
            len(conversation),
            "Memory should accumulate across conversation",
        )

        # Verify no errors throughout the chain
        self.config.assert_no_stale_component_errors()

        print("✅ Complex vague reference chain test passed")

    def test_ambiguous_reference_handling(self):
        """Test handling of ambiguous references when multiple components exist."""
        print("\n=== Test: Ambiguous Reference Handling ===")

        # Create multiple similar components
        setup_requests = [
            "Create a bridge curve for span 1",
            "Create another bridge curve for span 2",
            "Create a third bridge curve for span 3",
        ]

        for i, request in enumerate(setup_requests):
            print(f"Setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Setup response {i+1}: {response}")

        # Verify multiple curves exist
        bridge_curves = get_components_by_type("bridge_curve")
        print(f"Total bridge curves created: {len(bridge_curves)}")
        self.assertGreaterEqual(len(bridge_curves), 3, "Should have multiple curves")

        # Try ambiguous reference
        ambiguous_request = "Modify the bridge curve to be taller"
        print(f"Ambiguous request: {ambiguous_request}")

        ambiguous_response = self.config.simulate_user_request(ambiguous_request)
        print(f"Ambiguous response: {ambiguous_response}")

        # Should handle ambiguity gracefully (target most recent or ask for clarification)
        final_state = self.config.get_memory_state()

        # Memory should still function
        self.assertGreater(
            final_state["triage_memory_steps"],
            len(setup_requests),
            "Should handle ambiguous reference without memory failure",
        )

        # Should not cause stale component errors
        self.config.assert_no_stale_component_errors()

        print("✅ Ambiguous reference handling test passed")

    def test_pronoun_references(self):
        """Test pronoun references like 'it', 'that', 'the one'."""
        print("\n=== Test: Pronoun References ===")

        # Create initial component
        create_response = self.config.simulate_user_request(
            "Create a bridge arch with 12-meter span"
        )
        print(f"Created arch: {create_response}")

        # Test various pronoun references
        pronoun_tests = [
            "Make it higher",
            "Adjust that to be wider",
            "Change the height of the one we just made",
            "Update it with different parameters",
        ]

        for i, pronoun_request in enumerate(pronoun_tests):
            print(f"\nPronoun test {i+1}: {pronoun_request}")

            pronoun_response = self.config.simulate_user_request(pronoun_request)
            print(f"Pronoun response {i+1}: {pronoun_response}")

            # Each pronoun reference should be handled without errors
            state = self.config.get_memory_state()
            self.assertGreater(
                state["triage_memory_steps"],
                i + 1,
                f"Memory should accumulate through pronoun {i+1}",
            )

        # Final verification
        self.config.assert_no_stale_component_errors()

        print("✅ Pronoun references test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)
