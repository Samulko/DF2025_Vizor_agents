"""
Test Scenario 3: Script Editing Workflow

This test validates script editing operations and memory persistence:
1. Create→Edit→Verify workflow
2. Component ID persistence through edits
3. Script error detection and handling  
4. Edit history tracking
5. Memory synchronization during script modifications
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary, 
    get_components_by_type,
    get_most_recent_component_of_type,
    simulate_error_type,
    verify_no_components_have_errors
)


class TestScriptEditingWorkflow(MemoryTestCase):
    """Test script creation, editing, and verification workflows."""
    
    def test_create_edit_verify_workflow(self):
        """Test complete create→edit→verify workflow."""
        print("\n=== Test: Create→Edit→Verify Workflow ===")
        
        # Step 1: Create initial script
        create_request = "Create a Python script to generate bridge points"
        print(f"Step 1 - Create: {create_request}")
        
        create_response = self.config.simulate_user_request(create_request)
        print(f"Create response: {create_response}")
        
        # Verify creation
        after_create = self.config.get_memory_state()
        components_after_create = get_test_state_summary()["total_components"]
        print(f"Components after create: {components_after_create}")
        self.assertGreater(components_after_create, 0, "Should have created component")
        
        # Step 2: Edit the script
        edit_request = "Edit the script to add height parameters to the bridge points"
        print(f"Step 2 - Edit: {edit_request}")
        
        edit_response = self.config.simulate_user_request(edit_request)
        print(f"Edit response: {edit_response}")
        
        # Verify edit was processed
        after_edit = self.config.get_memory_state()
        print(f"Memory after edit: {after_edit}")
        
        # Memory should have progressed
        self.assertGreater(after_edit["triage_memory_steps"],
                          after_create["triage_memory_steps"],
                          "Memory should record edit operation")
        
        # Step 3: Verify the edit
        verify_request = "Show me the updated script content"
        print(f"Step 3 - Verify: {verify_request}")
        
        verify_response = self.config.simulate_user_request(verify_request)
        print(f"Verify response: {verify_response}")
        
        # Final verification
        final_state = self.config.get_memory_state()
        final_components = get_test_state_summary()["total_components"]
        
        # Should have same number of components (edit, not create new)
        self.assertEqual(final_components, components_after_create,
                        "Edit should modify existing, not create new component")
        
        # Should have accumulated memory
        self.assertGreaterEqual(final_state["triage_memory_steps"], 3,
                               "Should have memory from all three steps")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Create→Edit→Verify workflow test passed")
        
    def test_component_id_persistence_through_edits(self):
        """Test that component IDs persist through multiple edits."""
        print("\n=== Test: Component ID Persistence Through Edits ===")
        
        # Create initial component
        create_response = self.config.simulate_user_request(
            "Create a bridge curve generation script"
        )
        print(f"Initial creation: {create_response}")
        
        # Get initial component tracking
        initial_state = self.config.get_memory_state()
        initial_recent = initial_state["recent_components_count"]
        
        # Perform multiple edits
        edits = [
            "Edit the script to change the curve span to 60 meters",
            "Modify the script to add curve smoothing",
            "Update the script to include elevation parameters"
        ]
        
        for i, edit_request in enumerate(edits):
            print(f"\nEdit {i+1}: {edit_request}")
            edit_response = self.config.simulate_user_request(edit_request)
            print(f"Edit {i+1} response: {edit_response}")
            
            # Verify state after each edit
            current_state = self.config.get_memory_state()
            current_components = get_test_state_summary()["total_components"]
            
            # Should not create new components, just edit existing
            self.assertLessEqual(current_components, initial_recent + 1,
                                f"Edit {i+1} should not create excess components")
            
            # Memory should continue accumulating
            self.assertGreater(current_state["triage_memory_steps"],
                              initial_state["triage_memory_steps"],
                              f"Memory should accumulate through edit {i+1}")
        
        # Final verification
        final_state = self.config.get_memory_state()
        
        # Should have substantial memory accumulation
        self.assertGreater(final_state["triage_memory_steps"], len(edits) + 1,
                          "Memory should accumulate across all edits")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Component ID persistence through edits test passed")
        
    def test_script_error_introduction_and_fixing(self):
        """Test error detection and fixing workflow."""
        print("\n=== Test: Script Error Introduction and Fixing ===")
        
        # Create clean script
        create_response = self.config.simulate_user_request(
            "Create a bridge arch script with proper syntax"
        )
        print(f"Created clean script: {create_response}")
        
        # Verify initially no errors
        initial_summary = get_test_state_summary()
        self.assertEqual(initial_summary["components_with_errors"], 0,
                        "Should start with no errors")
        
        # Introduce syntax error through edit
        print("\nIntroducing syntax error...")
        simulate_error_type("syntax")  # Set up next operation to have error
        
        error_response = self.config.simulate_user_request(
            "Edit the script to add syntax_error to the code"
        )
        print(f"Error introduction response: {error_response}")
        
        # Verify error was detected
        after_error = get_test_state_summary()
        print(f"Components with errors after introduction: {after_error['components_with_errors']}")
        
        # Now fix the error
        fix_request = "Fix the syntax error in the script"
        print(f"\nFixing error: {fix_request}")
        
        fix_response = self.config.simulate_user_request(fix_request)
        print(f"Fix response: {fix_response}")
        
        # Verify error was resolved
        after_fix = get_test_state_summary()
        print(f"Components with errors after fix: {after_fix['components_with_errors']}")
        
        # Final memory state
        final_state = self.config.get_memory_state()
        
        # Memory should reflect the error/fix cycle
        self.assertGreater(final_state["triage_memory_steps"], 2,
                          "Should have memory from error introduction and fix")
        
        # Should end with no errors
        self.assertEqual(after_fix["components_with_errors"], 0,
                        "Should have no errors after fix")
        
        print("✅ Script error introduction and fixing test passed")
        
    def test_multiple_script_edits_different_components(self):
        """Test editing multiple different script components."""
        print("\n=== Test: Multiple Script Edits Different Components ===")
        
        # Create multiple script components
        scripts = [
            "Create a script for bridge foundation points",
            "Create a script for bridge curve generation", 
            "Create a script for bridge arch calculations"
        ]
        
        component_counts = []
        for i, script_request in enumerate(scripts):
            print(f"\nCreating script {i+1}: {script_request}")
            response = self.config.simulate_user_request(script_request)
            print(f"Script {i+1} response: {response}")
            
            summary = get_test_state_summary()
            component_counts.append(summary["total_components"])
            
        print(f"Component progression: {component_counts}")
        
        # Edit each script differently
        edits = [
            "Edit the foundation points script to include Z coordinates",
            "Modify the curve script to add control point parameters",
            "Update the arch script to include material properties"
        ]
        
        for i, edit_request in enumerate(edits):
            print(f"\nEdit {i+1}: {edit_request}")
            edit_response = self.config.simulate_user_request(edit_request)
            print(f"Edit {i+1} response: {edit_response}")
            
            # Verify component count stays same (editing, not creating)
            current_summary = get_test_state_summary()
            self.assertEqual(current_summary["total_components"], component_counts[-1],
                            f"Edit {i+1} should not create new components")
        
        # Verify memory accumulated correctly
        final_state = self.config.get_memory_state()
        expected_min_steps = len(scripts) + len(edits)
        self.assertGreaterEqual(final_state["triage_memory_steps"], expected_min_steps,
                               "Should have memory from all operations")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Multiple script edits different components test passed")
        
    def test_script_edit_with_vague_reference(self):
        """Test editing scripts using vague references."""
        print("\n=== Test: Script Edit with Vague Reference ===")
        
        # Create script
        create_response = self.config.simulate_user_request(
            "Create a bridge design script with basic parameters"
        )
        print(f"Created script: {create_response}")
        
        # Edit using vague reference
        vague_edit = "Edit that script to add more detail"
        print(f"Vague edit: {vague_edit}")
        
        vague_response = self.config.simulate_user_request(vague_edit)
        print(f"Vague edit response: {vague_response}")
        
        # Follow up with another vague reference
        followup_edit = "Now modify it to include error checking"
        print(f"Followup edit: {followup_edit}")
        
        followup_response = self.config.simulate_user_request(followup_edit)
        print(f"Followup response: {followup_response}")
        
        # Verify vague references were resolved
        final_state = self.config.get_memory_state()
        final_summary = get_test_state_summary()
        
        # Should have processed edits without creating new components
        self.assertGreaterEqual(final_summary["total_components"], 1,
                               "Should have at least the original script")
        self.assertLessEqual(final_summary["total_components"], 2,
                            "Should not have created many new components")
        
        # Memory should show progression
        self.assertGreaterEqual(final_state["triage_memory_steps"], 3,
                               "Should have memory from create + 2 edits")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Script edit with vague reference test passed")
        
    def test_edit_history_and_rollback_simulation(self):
        """Test simulation of edit history and rollback scenarios."""
        print("\n=== Test: Edit History and Rollback Simulation ===")
        
        # Create base script
        base_response = self.config.simulate_user_request(
            "Create a bridge analysis script with version control"
        )
        print(f"Base script: {base_response}")
        
        # Track memory after each edit
        memory_states = []
        edit_history = [
            "Edit to add wind load calculations",
            "Modify to include seismic analysis", 
            "Update with traffic load modeling",
            "Add safety factor calculations"
        ]
        
        for i, edit in enumerate(edit_history):
            print(f"\nEdit {i+1}: {edit}")
            response = self.config.simulate_user_request(edit)
            print(f"Edit {i+1} response: {response}")
            
            state = self.config.get_memory_state()
            memory_states.append(state)
            
            # Each edit should increase memory
            if i > 0:
                self.assertGreater(state["triage_memory_steps"],
                                  memory_states[i-1]["triage_memory_steps"],
                                  f"Memory should grow through edit {i+1}")
        
        # Simulate rollback request
        rollback_request = "Rollback the script to before the traffic load changes"
        print(f"\nRollback request: {rollback_request}")
        
        rollback_response = self.config.simulate_user_request(rollback_request)
        print(f"Rollback response: {rollback_response}")
        
        # Final verification
        final_state = self.config.get_memory_state()
        
        # Should have substantial memory from all operations
        total_operations = len(edit_history) + 2  # base + rollback
        self.assertGreaterEqual(final_state["triage_memory_steps"], total_operations,
                               "Should have memory from all operations")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Edit history and rollback simulation test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)