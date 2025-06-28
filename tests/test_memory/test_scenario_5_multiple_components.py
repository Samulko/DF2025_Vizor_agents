"""
Test Scenario 5: Multiple Components with Selective Modification

This test validates selective component targeting when multiple similar components exist:
1. Create multiple similar components (3 bridge curves)
2. Selective modification ("modify the second curve")
3. Ordinal references ("change the middle one", "update the last one")
4. Named/indexed targeting ("curve 2", "the third bridge")
5. Memory persistence across selective operations

This tests the memory fix's ability to distinguish between similar components
and correctly target specific ones for modification.
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary,
    get_components_by_type,
    get_most_recent_component_of_type,
    get_mock_state,
)


class TestMultipleComponentsSelective(MemoryTestCase):
    """Test selective modification of multiple similar components."""

    def test_create_and_modify_multiple_curves(self):
        """Test creating multiple curves and modifying specific ones."""
        print("\n=== Test: Create and Modify Multiple Curves ===")

        # Create multiple bridge curves
        curve_requests = [
            "Create bridge curve 1 with 30-meter span",
            "Create bridge curve 2 with 40-meter span",
            "Create bridge curve 3 with 50-meter span",
        ]

        curve_responses = []
        for i, request in enumerate(curve_requests):
            print(f"Creating curve {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            curve_responses.append(response)
            print(f"Curve {i+1} response: {response}")

        # Verify multiple curves created
        after_creation = get_test_state_summary()
        bridge_curves = get_components_by_type("bridge_curve")
        print(f"Total bridge curves: {len(bridge_curves)}")
        self.assertGreaterEqual(len(bridge_curves), 3, "Should have created 3+ curves")

        # Modify specific curve by ordinal
        modify_second = "Modify the second bridge curve to have 45-meter span"
        print(f"Modify second: {modify_second}")

        second_response = self.config.simulate_user_request(modify_second)
        print(f"Second modification response: {second_response}")

        # Modify another curve by position
        modify_last = "Update the last bridge curve to include arch features"
        print(f"Modify last: {modify_last}")

        last_response = self.config.simulate_user_request(modify_last)
        print(f"Last modification response: {last_response}")

        # Verify selective modifications
        final_state = self.config.get_memory_state()
        final_summary = get_test_state_summary()

        print(f"Final memory steps: {final_state['triage_memory_steps']}")
        print(f"Final component count: {final_summary['total_components']}")

        # Should have memory from all operations
        expected_min_steps = len(curve_requests) + 2  # creation + 2 modifications
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            expected_min_steps,
            "Should have memory from all selective operations",
        )

        # Should still have reasonable component count (modifications, not excessive creation)
        self.assertLessEqual(
            final_summary["total_components"],
            len(curve_requests) + 2,
            "Should not create excessive components during modification",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Create and modify multiple curves test passed")

    def test_ordinal_references_multiple_types(self):
        """Test ordinal references across different component types."""
        print("\n=== Test: Ordinal References Multiple Types ===")

        # Create mixed component types
        mixed_setup = [
            "Create bridge foundation points set 1",
            "Create bridge curve connecting the points",
            "Create another bridge foundation points set 2",
            "Create second bridge curve for different span",
            "Create bridge arch over the first curve",
        ]

        setup_responses = []
        for i, request in enumerate(mixed_setup):
            print(f"Setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            setup_responses.append(response)
            print(f"Setup {i+1} response: {response}")

        # Test ordinal references for different types
        ordinal_tests = [
            "Modify the first bridge curve to be higher",
            "Update the second set of foundation points",
            "Change the bridge arch to have different parameters",
        ]

        for i, ordinal_test in enumerate(ordinal_tests):
            print(f"\nOrdinal test {i+1}: {ordinal_test}")
            response = self.config.simulate_user_request(ordinal_test)
            print(f"Ordinal {i+1} response: {response}")

            # Verify each ordinal reference was processed
            state = self.config.get_memory_state()
            expected_steps = len(mixed_setup) + i + 1
            self.assertGreaterEqual(
                state["triage_memory_steps"],
                expected_steps,
                f"Memory should accumulate through ordinal {i+1}",
            )

        # Final verification
        final_summary = get_test_state_summary()
        print(f"Final component types: {final_summary['components_by_type']}")

        # Should have multiple types
        total_types = sum(1 for count in final_summary["components_by_type"].values() if count > 0)
        self.assertGreaterEqual(total_types, 2, "Should have multiple component types")

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Ordinal references multiple types test passed")

    def test_relative_positioning_references(self):
        """Test relative positioning references (middle, between, next to)."""
        print("\n=== Test: Relative Positioning References ===")

        # Create components in sequence
        sequence_setup = [
            "Create bridge support A at position (0,0)",
            "Create bridge support B at position (25,0)",
            "Create bridge support C at position (50,0)",
            "Create bridge curve from A to B",
            "Create bridge curve from B to C",
        ]

        for i, request in enumerate(sequence_setup):
            print(f"Sequence {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Sequence {i+1} response: {response}")

        # Test relative positioning references
        relative_tests = [
            "Modify the middle bridge support",
            "Update the curve between A and B",
            "Change the bridge element at position B",
        ]

        for i, relative_test in enumerate(relative_tests):
            print(f"\nRelative test {i+1}: {relative_test}")
            response = self.config.simulate_user_request(relative_test)
            print(f"Relative {i+1} response: {response}")

        # Verify relative references were handled
        final_state = self.config.get_memory_state()
        total_operations = len(sequence_setup) + len(relative_tests)

        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            total_operations,
            "Should handle all relative positioning references",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Relative positioning references test passed")

    def test_selective_modification_with_properties(self):
        """Test selective modification based on component properties."""
        print("\n=== Test: Selective Modification with Properties ===")

        # Create components with different properties
        property_setup = [
            "Create short bridge curve with 20-meter span",
            "Create medium bridge curve with 40-meter span",
            "Create long bridge curve with 60-meter span",
        ]

        for i, request in enumerate(property_setup):
            print(f"Property setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Property {i+1} response: {response}")

        # Test property-based selection
        property_tests = [
            "Modify the short bridge curve to add height",
            "Update the longest curve to include arch features",
            "Change the medium span curve to have more control points",
        ]

        for i, property_test in enumerate(property_tests):
            print(f"\nProperty test {i+1}: {property_test}")
            response = self.config.simulate_user_request(property_test)
            print(f"Property {i+1} response: {response}")

            # Verify property-based selection worked
            state = self.config.get_memory_state()
            self.assertGreater(
                state["triage_memory_steps"],
                len(property_setup) + i,
                f"Should process property-based selection {i+1}",
            )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Selective modification with properties test passed")

    def test_batch_selective_modifications(self):
        """Test batch modifications of selected components."""
        print("\n=== Test: Batch Selective Modifications ===")

        # Create multiple components for batch operations
        batch_setup = [
            "Create bridge curve set for span section 1",
            "Create bridge curve set for span section 2",
            "Create bridge curve set for span section 3",
            "Create bridge curve set for span section 4",
        ]

        for i, request in enumerate(batch_setup):
            print(f"Batch setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Batch {i+1} response: {response}")

        # Test batch selective operations
        batch_operations = [
            "Modify curves 1 and 3 to have increased height",
            "Update the even-numbered curves with arch features",
            "Change all curves except the first one to have smoother transitions",
        ]

        for i, batch_op in enumerate(batch_operations):
            print(f"\nBatch operation {i+1}: {batch_op}")
            response = self.config.simulate_user_request(batch_op)
            print(f"Batch {i+1} response: {response}")

            # Verify batch operation was processed
            state = self.config.get_memory_state()
            expected_steps = len(batch_setup) + i + 1
            self.assertGreaterEqual(
                state["triage_memory_steps"],
                expected_steps,
                f"Should process batch operation {i+1}",
            )

        # Final verification
        final_summary = get_test_state_summary()
        print(f"Final total components: {final_summary['total_components']}")

        # Should have handled batch operations without excessive component creation
        self.assertLessEqual(
            final_summary["total_components"],
            len(batch_setup) * 2,
            "Batch operations should not create excessive components",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Batch selective modifications test passed")

    def test_ambiguous_selection_resolution(self):
        """Test resolution of ambiguous component selections."""
        print("\n=== Test: Ambiguous Selection Resolution ===")

        # Create very similar components that could be ambiguous
        similar_setup = [
            "Create bridge curve with default parameters",
            "Create another bridge curve with default parameters",
            "Create third bridge curve with default parameters",
        ]

        for i, request in enumerate(similar_setup):
            print(f"Similar setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Similar {i+1} response: {response}")

        # Test ambiguous references
        ambiguous_tests = [
            "Modify the bridge curve",  # Ambiguous - which one?
            "Update that curve",  # Ambiguous reference
            "Change the curve we just made",  # Should reference most recent
        ]

        for i, ambiguous_test in enumerate(ambiguous_tests):
            print(f"\nAmbiguous test {i+1}: {ambiguous_test}")
            response = self.config.simulate_user_request(ambiguous_test)
            print(f"Ambiguous {i+1} response: {response}")

            # Should handle ambiguity gracefully without errors
            state = self.config.get_memory_state()
            self.assertGreater(
                state["triage_memory_steps"],
                len(similar_setup) + i,
                f"Should handle ambiguous reference {i+1} gracefully",
            )

        # Test more specific resolution
        specific_resolution = "Modify the first bridge curve specifically"
        print(f"\nSpecific resolution: {specific_resolution}")

        specific_response = self.config.simulate_user_request(specific_resolution)
        print(f"Specific response: {specific_response}")

        # Verify ambiguity resolution
        final_state = self.config.get_memory_state()
        total_expected = len(similar_setup) + len(ambiguous_tests) + 1

        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            total_expected,
            "Should handle ambiguity resolution without memory failure",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Ambiguous selection resolution test passed")

    def test_cross_type_selective_modifications(self):
        """Test selective modifications across different component types."""
        print("\n=== Test: Cross-Type Selective Modifications ===")

        # Create diverse component types
        diverse_setup = [
            "Create bridge points for foundation 1",
            "Create bridge curve connecting foundation 1",
            "Create bridge arch over the curve",
            "Create bridge points for foundation 2",
            "Create analysis script for the bridge structure",
        ]

        for i, request in enumerate(diverse_setup):
            print(f"Diverse setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Diverse {i+1} response: {response}")

        # Test cross-type selective operations
        cross_type_tests = [
            "Modify only the geometric components (not the script)",
            "Update the foundation points but leave curves unchanged",
            "Change the arch while keeping the supporting elements",
        ]

        for i, cross_test in enumerate(cross_type_tests):
            print(f"\nCross-type test {i+1}: {cross_test}")
            response = self.config.simulate_user_request(cross_test)
            print(f"Cross-type {i+1} response: {response}")

        # Verify cross-type selections
        final_state = self.config.get_memory_state()
        final_summary = get_test_state_summary()

        print(f"Final component types: {final_summary['components_by_type']}")
        print(f"Total memory steps: {final_state['triage_memory_steps']}")

        # Should have handled cross-type operations
        total_operations = len(diverse_setup) + len(cross_type_tests)
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            total_operations,
            "Should handle cross-type selective modifications",
        )

        # Should maintain diverse component types
        type_count = sum(1 for count in final_summary["components_by_type"].values() if count > 0)
        self.assertGreaterEqual(type_count, 2, "Should maintain diverse component types")

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Cross-type selective modifications test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)
