"""
Test Scenario 4: Error Handling and Target Resolution

This test validates error handling with vague references:
1. Create components with errors
2. Use "fix that error" references
3. Ensure correct component targeting
4. Test error resolution workflows
5. Validate no stale component ID issues during error fixing

This addresses the critical use case where agents couldn't identify which
component had errors when users said "fix that error".
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary,
    get_components_by_type,
    get_most_recent_component_of_type,
    simulate_error_type,
    verify_no_components_have_errors,
    get_mock_state,
)


class TestErrorHandlingAndTargeting(MemoryTestCase):
    """Test error handling and correct component targeting for fixes."""

    def test_fix_that_error_single_component(self):
        """Test 'fix that error' with single component having error."""
        print("\n=== Test: 'Fix That Error' Single Component ===")

        # Create component with error
        print("Creating component with syntax error...")
        simulate_error_type("syntax")

        create_response = self.config.simulate_user_request(
            "Create a bridge script that contains syntax_error"
        )
        print(f"Create response: {create_response}")

        # Verify error was created
        after_create = get_test_state_summary()
        print(f"Components with errors: {after_create['components_with_errors']}")
        self.assertGreater(
            after_create["components_with_errors"], 0, "Should have created component with error"
        )

        # Use vague reference to fix error
        fix_request = "Fix that error"
        print(f"Fix request: {fix_request}")

        fix_response = self.config.simulate_user_request(fix_request)
        print(f"Fix response: {fix_response}")

        # Verify error was resolved
        after_fix = get_test_state_summary()
        print(f"Components with errors after fix: {after_fix['components_with_errors']}")

        # Should have resolved the error
        self.assertEqual(after_fix["components_with_errors"], 0, "Error should be fixed")

        # Memory should show the fix operation
        final_state = self.config.get_memory_state()
        self.assertGreaterEqual(
            final_state["triage_memory_steps"], 2, "Should have memory from create and fix"
        )

        # Verify no stale component errors
        self.config.assert_no_stale_component_errors()

        print("✅ 'Fix that error' single component test passed")

    def test_fix_specific_error_multiple_components(self):
        """Test error fixing when multiple components have errors."""
        print("\n=== Test: Fix Specific Error Multiple Components ===")

        # Create multiple components, some with errors
        components_setup = [
            ("Create bridge points script", None),
            ("Create bridge curve script with syntax_error", "syntax"),
            ("Create bridge arch script", None),
            ("Create analysis script with undefined_variable", "name"),
        ]

        error_components = []
        for i, (request, error_type) in enumerate(components_setup):
            if error_type:
                print(f"Setting up {error_type} error for component {i+1}")
                simulate_error_type(error_type)
                error_components.append(i + 1)

            print(f"Creating component {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Component {i+1} response: {response}")

        # Verify multiple errors exist
        after_setup = get_test_state_summary()
        print(f"Components with errors after setup: {after_setup['components_with_errors']}")
        self.assertGreaterEqual(
            after_setup["components_with_errors"], 2, "Should have multiple components with errors"
        )

        # Fix syntax error specifically
        fix_syntax = "Fix the syntax error in the bridge curve script"
        print(f"Fix syntax: {fix_syntax}")

        syntax_response = self.config.simulate_user_request(fix_syntax)
        print(f"Syntax fix response: {syntax_response}")

        # Check that syntax error was targeted
        after_syntax_fix = get_test_state_summary()
        print(f"Errors after syntax fix: {after_syntax_fix['components_with_errors']}")

        # Should have reduced error count
        self.assertLess(
            after_syntax_fix["components_with_errors"],
            after_setup["components_with_errors"],
            "Should have fixed at least one error",
        )

        # Fix remaining error with vague reference
        fix_remaining = "Fix the other error"
        print(f"Fix remaining: {fix_remaining}")

        remaining_response = self.config.simulate_user_request(fix_remaining)
        print(f"Remaining fix response: {remaining_response}")

        # Verify all errors fixed
        final_summary = get_test_state_summary()
        print(f"Final errors: {final_summary['components_with_errors']}")

        # Memory should reflect all operations
        final_state = self.config.get_memory_state()
        expected_min_steps = len(components_setup) + 2  # setup + 2 fixes
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            expected_min_steps,
            "Should have memory from all operations",
        )

        # Verify no stale component errors
        self.config.assert_no_stale_component_errors()

        print("✅ Fix specific error multiple components test passed")

    def test_error_detection_and_immediate_fix(self):
        """Test immediate error detection and fixing workflow."""
        print("\n=== Test: Error Detection and Immediate Fix ===")

        # Create script that will have error
        create_request = "Create a bridge calculation script"
        print(f"Creating script: {create_request}")

        create_response = self.config.simulate_user_request(create_request)
        print(f"Create response: {create_response}")

        # Edit script to introduce error
        print("Introducing error through edit...")
        simulate_error_type("runtime")

        edit_request = "Edit the script to add undefined_variable usage"
        print(f"Edit request: {edit_request}")

        edit_response = self.config.simulate_user_request(edit_request)
        print(f"Edit response: {edit_response}")

        # Immediately fix the error
        immediate_fix = "Fix that error right away"
        print(f"Immediate fix: {immediate_fix}")

        fix_response = self.config.simulate_user_request(immediate_fix)
        print(f"Fix response: {fix_response}")

        # Verify error cycle
        final_summary = get_test_state_summary()
        final_state = self.config.get_memory_state()

        print(f"Final summary: {final_summary}")
        print(f"Final memory steps: {final_state['triage_memory_steps']}")

        # Should have no errors after fix
        self.assertEqual(
            final_summary["components_with_errors"], 0, "Should have no errors after immediate fix"
        )

        # Should have memory of the rapid error/fix cycle
        self.assertGreaterEqual(
            final_state["triage_memory_steps"], 3, "Should have memory from create, edit, fix"
        )

        # Verify no stale component errors
        self.config.assert_no_stale_component_errors()

        print("✅ Error detection and immediate fix test passed")

    def test_fix_errors_with_pronoun_references(self):
        """Test fixing errors using pronoun references."""
        print("\n=== Test: Fix Errors with Pronoun References ===")

        # Create component with error
        simulate_error_type("import")
        create_response = self.config.simulate_user_request(
            "Create a bridge script that tries to import os"
        )
        print(f"Created script with import error: {create_response}")

        # Test various pronoun references for fixing
        pronoun_fixes = [
            "Fix it",
            "Correct that",
            "Resolve the issue with it",
            "Update that to work properly",
        ]

        for i, pronoun_fix in enumerate(pronoun_fixes):
            print(f"\nPronoun fix {i+1}: {pronoun_fix}")

            # If this isn't the first fix, introduce new error
            if i > 0:
                simulate_error_type("syntax")
                self.config.simulate_user_request("Edit the script to add syntax issues")

            fix_response = self.config.simulate_user_request(pronoun_fix)
            print(f"Pronoun fix {i+1} response: {fix_response}")

            # Verify each pronoun reference was handled
            state = self.config.get_memory_state()
            self.assertGreater(
                state["triage_memory_steps"],
                i + 1,
                f"Memory should accumulate through pronoun fix {i+1}",
            )

        # Final verification
        final_summary = get_test_state_summary()
        print(f"Final components with errors: {final_summary['components_with_errors']}")

        # Verify no stale component errors
        self.config.assert_no_stale_component_errors()

        print("✅ Fix errors with pronoun references test passed")

    def test_error_propagation_and_cascade_fixing(self):
        """Test fixing cascading errors across related components."""
        print("\n=== Test: Error Propagation and Cascade Fixing ===")

        # Create dependent components with cascading errors
        cascade_setup = [
            "Create bridge foundation points",
            "Create curve connecting the points (with syntax_error)",
            "Create arch based on the curve (with undefined_variable)",
        ]

        # Introduce errors in the dependent components
        responses = []
        for i, request in enumerate(cascade_setup):
            if i == 1:  # Second component gets syntax error
                simulate_error_type("syntax")
            elif i == 2:  # Third component gets name error
                simulate_error_type("name")

            print(f"Cascade setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            responses.append(response)
            print(f"Setup {i+1} response: {response}")

        # Verify cascade errors exist
        after_cascade = get_test_state_summary()
        print(f"Errors after cascade setup: {after_cascade['components_with_errors']}")
        self.assertGreaterEqual(
            after_cascade["components_with_errors"], 2, "Should have cascading errors"
        )

        # Fix the base error first
        fix_base = "Fix the syntax error in the curve component"
        print(f"Fix base: {fix_base}")

        base_fix_response = self.config.simulate_user_request(fix_base)
        print(f"Base fix response: {base_fix_response}")

        # Fix the dependent error
        fix_dependent = "Now fix the error in the arch component"
        print(f"Fix dependent: {fix_dependent}")

        dependent_fix_response = self.config.simulate_user_request(fix_dependent)
        print(f"Dependent fix response: {dependent_fix_response}")

        # Verify cascade fixing worked
        final_summary = get_test_state_summary()
        final_state = self.config.get_memory_state()

        print(f"Final errors: {final_summary['components_with_errors']}")
        print(f"Total memory steps: {final_state['triage_memory_steps']}")

        # Should have resolved cascade
        self.assertEqual(
            final_summary["components_with_errors"], 0, "Should have fixed cascading errors"
        )

        # Should have substantial memory
        expected_min_steps = len(cascade_setup) + 2  # setup + 2 fixes
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            expected_min_steps,
            "Should have memory from cascade operations",
        )

        # Verify no stale component errors
        self.config.assert_no_stale_component_errors()

        print("✅ Error propagation and cascade fixing test passed")

    def test_ambiguous_error_reference_handling(self):
        """Test handling when error references are ambiguous."""
        print("\n=== Test: Ambiguous Error Reference Handling ===")

        # Create multiple components with similar errors
        similar_errors = [
            "Create bridge script 1 with syntax_error",
            "Create bridge script 2 with syntax_error",
            "Create bridge script 3 with syntax_error",
        ]

        for i, request in enumerate(similar_errors):
            simulate_error_type("syntax")
            print(f"Creating error {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Error {i+1} response: {response}")

        # Verify multiple similar errors
        after_errors = get_test_state_summary()
        print(f"Multiple similar errors: {after_errors['components_with_errors']}")
        self.assertGreaterEqual(
            after_errors["components_with_errors"], 3, "Should have multiple similar errors"
        )

        # Use ambiguous reference
        ambiguous_fix = "Fix the syntax error"
        print(f"Ambiguous fix: {ambiguous_fix}")

        ambiguous_response = self.config.simulate_user_request(ambiguous_fix)
        print(f"Ambiguous response: {ambiguous_response}")

        # Should handle ambiguity gracefully (fix one or ask for clarification)
        after_ambiguous = get_test_state_summary()
        print(f"Errors after ambiguous fix: {after_ambiguous['components_with_errors']}")

        # Use more specific reference
        specific_fix = "Fix the syntax error in script 2"
        print(f"Specific fix: {specific_fix}")

        specific_response = self.config.simulate_user_request(specific_fix)
        print(f"Specific response: {specific_response}")

        # Final verification
        final_state = self.config.get_memory_state()

        # Should have handled ambiguous references without failure
        self.assertGreater(
            final_state["triage_memory_steps"],
            len(similar_errors) + 1,
            "Should handle ambiguous references without memory failure",
        )

        # Verify no stale component errors
        self.config.assert_no_stale_component_errors()

        print("✅ Ambiguous error reference handling test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)
