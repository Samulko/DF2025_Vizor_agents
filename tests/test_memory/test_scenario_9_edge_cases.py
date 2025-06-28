"""
Test Scenario 9: Edge Cases and Boundary Conditions

This test validates edge cases and boundary conditions for memory synchronization:
1. Empty or nonsensical references
2. Components with identical types and properties
3. Session boundary scenarios and memory limits
4. Error recovery edge cases
5. Malformed input handling
6. Stress testing with extreme conditions
7. Memory cleanup and garbage collection scenarios

These edge cases ensure the memory fix is robust and handles
unusual conditions without breaking or losing component tracking.
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary,
    get_components_by_type,
    get_most_recent_component_of_type,
    simulate_error_type,
    reset_mock_state,
)


class TestEdgeCasesAndBoundaries(MemoryTestCase):
    """Test edge cases and boundary conditions for memory synchronization."""

    def test_empty_and_nonsensical_references(self):
        """Test handling of empty or nonsensical references."""
        print("\n=== Test: Empty and Nonsensical References ===")

        # Create a component first
        setup_response = self.config.simulate_user_request("Create a bridge arch")
        print(f"Setup: {setup_response}")

        # Test empty and nonsensical references
        edge_references = [
            "",  # Empty input
            "   ",  # Whitespace only
            "modify",  # Incomplete reference
            "fix",  # Incomplete reference
            "that thing over there",  # Vague nonsense
            "the purple elephant",  # Nonsensical reference
            "update the quantum flux capacitor",  # Sci-fi nonsense
            "change it to be more better",  # Grammatically poor
            "do something with the stuff",  # Extremely vague
            "make that thing do the thing",  # Circular reference
        ]

        for i, edge_ref in enumerate(edge_references):
            print(f"\nEdge reference {i+1}: '{edge_ref}'")
            try:
                response = self.config.simulate_user_request(edge_ref)
                print(f"Edge response {i+1}: {response}")

                # Should handle gracefully without crashing
                state = self.config.get_memory_state()
                self.assertIsInstance(
                    state["triage_memory_steps"],
                    int,
                    f"Should maintain valid memory state for edge case {i+1}",
                )

            except Exception as e:
                print(f"Edge case {i+1} exception: {e}")
                # Should not crash the system
                self.fail(f"Edge case {i+1} should not crash the system: {e}")

        # System should still be functional after edge cases
        recovery_response = self.config.simulate_user_request("Show me the bridge arch")
        print(f"Recovery test: {recovery_response}")

        final_state = self.config.get_memory_state()
        self.assertGreater(
            final_state["triage_memory_steps"],
            1,
            "System should remain functional after edge cases",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Empty and nonsensical references test passed")

    def test_identical_components_disambiguation(self):
        """Test handling of multiple identical components."""
        print("\n=== Test: Identical Components Disambiguation ===")

        # Create multiple identical components
        identical_requests = [
            "Create bridge arch with default parameters",
            "Create bridge arch with default parameters",
            "Create bridge arch with default parameters",
            "Create bridge arch with default parameters",
            "Create bridge arch with default parameters",
        ]

        for i, identical_request in enumerate(identical_requests):
            print(f"Creating identical {i+1}: {identical_request}")
            response = self.config.simulate_user_request(identical_request)
            print(f"Identical {i+1} response: {response}")

        # Verify multiple identical components exist
        summary = get_test_state_summary()
        arch_components = get_components_by_type("bridge_arch")
        print(f"Identical components created: {len(arch_components)}")
        self.assertGreaterEqual(
            len(arch_components), 5, "Should create multiple identical components"
        )

        # Test disambiguation with vague references
        disambiguation_tests = [
            "Modify the bridge arch",  # Ambiguous
            "Update that arch",  # Ambiguous
            "Change the first one",  # Ordinal
            "Modify the most recent arch",  # Temporal
            "Update the last bridge arch we created",  # Temporal specific
        ]

        for i, disambig_test in enumerate(disambiguation_tests):
            print(f"\nDisambiguation {i+1}: {disambig_test}")
            response = self.config.simulate_user_request(disambig_test)
            print(f"Disambiguation {i+1} response: {response}")

            # Should handle ambiguity gracefully
            state = self.config.get_memory_state()
            self.assertIsInstance(
                state["triage_memory_steps"], int, f"Should handle disambiguation {i+1} gracefully"
            )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Identical components disambiguation test passed")

    def test_session_boundary_scenarios(self):
        """Test session boundary and memory limit scenarios."""
        print("\n=== Test: Session Boundary Scenarios ===")

        # Test memory state across "session reset"
        print("Creating components before reset...")
        pre_reset_requests = [
            "Create bridge foundation",
            "Create bridge deck",
            "Create bridge supports",
        ]

        for request in pre_reset_requests:
            response = self.config.simulate_user_request(request)
            print(f"Pre-reset: {response}")

        pre_reset_state = self.config.get_memory_state()
        print(f"Pre-reset memory: {pre_reset_state}")

        # Simulate session boundary (reset mock state but keep agent memory)
        print("\nSimulating session boundary...")
        reset_mock_state()  # Reset mock grasshopper state

        # Test post-reset behavior
        post_reset_requests = [
            "What components do we have?",
            "Show me the recent components",
            "Create a new bridge arch",
        ]

        for i, request in enumerate(post_reset_requests):
            print(f"Post-reset {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Post-reset {i+1} response: {response}")

        post_reset_state = self.config.get_memory_state()
        print(f"Post-reset memory: {post_reset_state}")

        # Agent memory should persist across session boundary
        self.assertGreaterEqual(
            post_reset_state["triage_memory_steps"],
            pre_reset_state["triage_memory_steps"],
            "Agent memory should persist across session boundary",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Session boundary scenarios test passed")

    def test_error_recovery_edge_cases(self):
        """Test error recovery in edge case scenarios."""
        print("\n=== Test: Error Recovery Edge Cases ===")

        # Create component that will have cascading errors
        base_request = "Create bridge analysis script"
        print(f"Base creation: {base_request}")
        base_response = self.config.simulate_user_request(base_request)
        print(f"Base response: {base_response}")

        # Introduce multiple error types in sequence
        error_cascade = [
            ("syntax", "Edit the script to include syntax_error"),
            ("runtime", "Add undefined_variable to the script"),
            ("import", "Try to import os in the script"),
            ("name", "Use nonexistent_function in the script"),
        ]

        for i, (error_type, error_request) in enumerate(error_cascade):
            print(f"\nError cascade {i+1} ({error_type}): {error_request}")
            simulate_error_type(error_type)

            error_response = self.config.simulate_user_request(error_request)
            print(f"Error {i+1} response: {error_response}")

            # Try to recover from each error
            recovery_request = f"Fix the {error_type} error"
            print(f"Recovery {i+1}: {recovery_request}")
            recovery_response = self.config.simulate_user_request(recovery_request)
            print(f"Recovery {i+1} response: {recovery_response}")

        # Test system stability after error cascade
        stability_test = "Show me the current state of the script"
        print(f"\nStability test: {stability_test}")
        stability_response = self.config.simulate_user_request(stability_test)
        print(f"Stability response: {stability_response}")

        # Verify system recovered
        final_state = self.config.get_memory_state()
        expected_operations = (
            1 + (len(error_cascade) * 2) + 1
        )  # base + errors + recoveries + stability
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            expected_operations,
            "Should recover from error cascade",
        )

        print("✅ Error recovery edge cases test passed")

    def test_malformed_input_handling(self):
        """Test handling of malformed and unusual inputs."""
        print("\n=== Test: Malformed Input Handling ===")

        # Create base component
        base_response = self.config.simulate_user_request("Create a bridge structure")
        print(f"Base: {base_response}")

        # Test various malformed inputs
        malformed_inputs = [
            "modify the bridge\n\n\nwith extra newlines",
            "update   the   structure   with   extra   spaces",
            "Change THE BRIDGE TO BE LOUDER",  # All caps
            "modify the bridge... with... ellipses...",
            "update the bridge!!!???",  # Multiple punctuation
            "change\tthe\tbridge\twith\ttabs",
            "🌉 modify the bridge with emoji 🔧",
            "modify the bridge; drop table components;",  # SQL injection attempt
            "<script>alert('xss')</script> modify bridge",  # XSS attempt
            "modify the bridge AND 1=1",  # SQL-like injection
        ]

        for i, malformed_input in enumerate(malformed_inputs):
            print(f"\nMalformed {i+1}: '{malformed_input}'")
            try:
                response = self.config.simulate_user_request(malformed_input)
                print(f"Malformed {i+1} response: {response}")

                # Should handle without crashing
                state = self.config.get_memory_state()
                self.assertIsInstance(
                    state, dict, f"Should maintain valid state for malformed input {i+1}"
                )

            except Exception as e:
                print(f"Malformed {i+1} exception: {e}")
                # Should not crash the system
                self.fail(f"Malformed input {i+1} should not crash system: {e}")

        # Verify system still works normally
        normal_test = "Show me the bridge structure"
        print(f"\nNormal test after malformed: {normal_test}")
        normal_response = self.config.simulate_user_request(normal_test)
        print(f"Normal response: {normal_response}")

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Malformed input handling test passed")

    def test_stress_testing_extreme_conditions(self):
        """Test stress conditions with many rapid operations."""
        print("\n=== Test: Stress Testing Extreme Conditions ===")

        # Rapid component creation
        print("Rapid component creation stress test...")
        rapid_creation_count = 20
        start_time = time.time()

        for i in range(rapid_creation_count):
            request = f"Create bridge element {i+1}"
            if i % 5 == 0:  # Log every 5th
                print(f"Rapid creation {i+1}/{rapid_creation_count}")
            response = self.config.simulate_user_request(request)

        rapid_creation_time = time.time() - start_time
        print(f"Rapid creation completed in {rapid_creation_time:.2f} seconds")

        # Rapid modification stress test
        print("\nRapid modification stress test...")
        rapid_modification_count = 15
        start_time = time.time()

        for i in range(rapid_modification_count):
            request = f"Modify element {(i % 5) + 1} to be taller"
            if i % 5 == 0:  # Log every 5th
                print(f"Rapid modification {i+1}/{rapid_modification_count}")
            response = self.config.simulate_user_request(request)

        rapid_modification_time = time.time() - start_time
        print(f"Rapid modification completed in {rapid_modification_time:.2f} seconds")

        # Verify system stability after stress
        stress_state = self.config.get_memory_state()
        stress_summary = get_test_state_summary()

        print(f"Stress test final state: {stress_state}")
        print(f"Stress test summary: {stress_summary}")

        # Should have handled stress without errors
        expected_min_operations = rapid_creation_count + rapid_modification_count
        self.assertGreaterEqual(
            stress_state["triage_memory_steps"],
            expected_min_operations,
            "Should handle stress testing",
        )

        # Should have created many components
        self.assertGreaterEqual(
            stress_summary["total_components"],
            rapid_creation_count,
            "Should have created components during stress test",
        )

        # Performance should be reasonable
        self.assertLess(rapid_creation_time, 30.0, "Rapid creation should complete reasonably fast")
        self.assertLess(
            rapid_modification_time, 30.0, "Rapid modification should complete reasonably fast"
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Stress testing extreme conditions test passed")

    def test_memory_cleanup_scenarios(self):
        """Test memory cleanup and garbage collection scenarios."""
        print("\n=== Test: Memory Cleanup Scenarios ===")

        # Create many components to test memory management
        print("Creating many components for cleanup testing...")
        cleanup_requests = []
        for i in range(15):
            request = f"Create temporary bridge element {i+1}"
            cleanup_requests.append(request)
            response = self.config.simulate_user_request(request)
            if i % 5 == 0:
                print(f"Created temporary element {i+1}")

        # Check memory state with many components
        pre_cleanup_state = self.config.get_memory_state()
        pre_cleanup_summary = get_test_state_summary()

        print(f"Pre-cleanup state: {pre_cleanup_state}")
        print(f"Pre-cleanup components: {pre_cleanup_summary['total_components']}")

        # Test cleanup operations
        cleanup_operations = [
            "Clean up the temporary elements",
            "Remove unused components",
            "Optimize the memory state",
            "Clear old tracking data",
        ]

        for i, cleanup_op in enumerate(cleanup_operations):
            print(f"\nCleanup {i+1}: {cleanup_op}")
            response = self.config.simulate_user_request(cleanup_op)
            print(f"Cleanup {i+1} response: {response}")

        # Check post-cleanup state
        post_cleanup_state = self.config.get_memory_state()
        post_cleanup_summary = get_test_state_summary()

        print(f"Post-cleanup state: {post_cleanup_state}")
        print(f"Post-cleanup components: {post_cleanup_summary['total_components']}")

        # Memory should still be functional after cleanup attempts
        self.assertGreater(
            post_cleanup_state["triage_memory_steps"],
            pre_cleanup_state["triage_memory_steps"],
            "Memory should remain functional after cleanup",
        )

        # Test that system still works normally
        post_cleanup_test = "Create a final bridge arch"
        print(f"\nPost-cleanup test: {post_cleanup_test}")
        final_response = self.config.simulate_user_request(post_cleanup_test)
        print(f"Final response: {final_response}")

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Memory cleanup scenarios test passed")

    def test_concurrent_operation_simulation(self):
        """Test simulation of concurrent-like operations."""
        print("\n=== Test: Concurrent Operation Simulation ===")

        # Simulate concurrent-like operations by rapid switching
        concurrent_simulation = [
            "Start creating bridge A",
            "Start creating bridge B",
            "Continue bridge A with arch",
            "Continue bridge B with beam",
            "Add details to bridge A",
            "Add details to bridge B",
            "Modify bridge A height",
            "Modify bridge B width",
            "Finalize bridge A",
            "Finalize bridge B",
            "Compare both bridges",
            "Choose the better design",
        ]

        concurrent_responses = []
        for i, concurrent_op in enumerate(concurrent_simulation):
            print(f"\nConcurrent-like {i+1}: {concurrent_op}")
            response = self.config.simulate_user_request(concurrent_op)
            concurrent_responses.append(response)
            print(f"Concurrent {i+1} response: {response}")

            # Verify state remains consistent
            state = self.config.get_memory_state()
            self.assertIsInstance(
                state["triage_memory_steps"],
                int,
                f"State should remain consistent in concurrent-like op {i+1}",
            )

        # Verify concurrent-like operations handled correctly
        final_concurrent_state = self.config.get_memory_state()

        self.assertGreaterEqual(
            final_concurrent_state["triage_memory_steps"],
            len(concurrent_simulation),
            "Should handle concurrent-like operations",
        )

        # Should have components from both "concurrent" operations
        final_summary = get_test_state_summary()
        self.assertGreater(
            final_summary["total_components"],
            1,
            "Should have components from concurrent-like operations",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Concurrent operation simulation test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)
