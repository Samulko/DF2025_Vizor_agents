"""
Test Scenario 7: Complex References and Parametric Modifications

This test validates complex contextual references with specific instructions:
1. Spatial modifications ("move that up by 10")
2. Parameter additions ("add height parameter to it")
3. Quantitative changes ("increase by 50%", "make it 30% longer")
4. Directional references ("move it to the right", "rotate that clockwise")
5. Complex compound modifications ("move it up and make it wider")

These test the memory fix's ability to handle nuanced contextual references
that require both component identification AND specific parametric changes.
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary, 
    get_components_by_type,
    get_most_recent_component_of_type
)


class TestComplexReferences(MemoryTestCase):
    """Test complex contextual references with parametric modifications."""
    
    def test_spatial_modification_references(self):
        """Test spatial modification references like 'move that up by 10'."""
        print("\n=== Test: Spatial Modification References ===")
        
        # Create component for spatial modification
        create_request = "Create a bridge arch at coordinates (25, 0, 0)"
        print(f"Create: {create_request}")
        create_response = self.config.simulate_user_request(create_request)
        print(f"Create response: {create_response}")
        
        # Test various spatial modifications
        spatial_modifications = [
            "Move that up by 10 meters",
            "Shift it 5 meters to the right", 
            "Lower the arch by 3 meters",
            "Move it back along the Y axis by 8 meters"
        ]
        
        for i, spatial_mod in enumerate(spatial_modifications):
            print(f"\nSpatial modification {i+1}: {spatial_mod}")
            response = self.config.simulate_user_request(spatial_mod)
            print(f"Spatial {i+1} response: {response}")
            
            # Verify spatial modification was processed
            state = self.config.get_memory_state()
            self.assertGreater(state["triage_memory_steps"], i + 1,
                              f"Memory should accumulate through spatial mod {i+1}")
        
        # Test compound spatial modification
        compound_spatial = "Move it up by 5 and to the left by 10"
        print(f"\nCompound spatial: {compound_spatial}")
        compound_response = self.config.simulate_user_request(compound_spatial)
        print(f"Compound response: {compound_response}")
        
        # Verify all spatial modifications
        final_state = self.config.get_memory_state()
        expected_operations = 1 + len(spatial_modifications) + 1  # create + mods + compound
        
        self.assertGreaterEqual(final_state["triage_memory_steps"], expected_operations,
                               "Should handle all spatial modifications")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Spatial modification references test passed")
        
    def test_parametric_addition_references(self):
        """Test parametric addition references like 'add height parameter'."""
        print("\n=== Test: Parametric Addition References ===")
        
        # Create base component
        base_request = "Create a bridge curve with basic parameters"
        print(f"Base creation: {base_request}")
        base_response = self.config.simulate_user_request(base_request)
        print(f"Base response: {base_response}")
        
        # Test parameter additions
        parameter_additions = [
            "Add height parameter to it",
            "Include width control in that curve",
            "Add material properties to the component",
            "Give it dynamic span adjustment capability"
        ]
        
        for i, param_add in enumerate(parameter_additions):
            print(f"\nParameter addition {i+1}: {param_add}")
            response = self.config.simulate_user_request(param_add)
            print(f"Parameter {i+1} response: {response}")
            
            # Verify parameter addition was processed
            state = self.config.get_memory_state()
            self.assertGreater(state["triage_memory_steps"], i + 1,
                              f"Memory should accumulate through param addition {i+1}")
        
        # Test complex parameter addition
        complex_param = "Add both elevation control and curve smoothing parameters to it"
        print(f"\nComplex parameter: {complex_param}")
        complex_response = self.config.simulate_user_request(complex_param)
        print(f"Complex parameter response: {complex_response}")
        
        # Verify parametric additions
        final_state = self.config.get_memory_state()
        expected_operations = 1 + len(parameter_additions) + 1
        
        self.assertGreaterEqual(final_state["triage_memory_steps"], expected_operations,
                               "Should handle all parameter additions")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Parametric addition references test passed")
        
    def test_quantitative_modification_references(self):
        """Test quantitative modifications like 'increase by 50%'."""
        print("\n=== Test: Quantitative Modification References ===")
        
        # Create component for quantitative modification
        quant_request = "Create a bridge span with 40-meter length"
        print(f"Quantitative base: {quant_request}")
        quant_response = self.config.simulate_user_request(quant_request)
        print(f"Quantitative response: {quant_response}")
        
        # Test quantitative modifications
        quantitative_mods = [
            "Increase its length by 50%",
            "Make it 30% wider",
            "Reduce the height by 20%",
            "Scale it up by a factor of 1.5",
            "Decrease the span by 10 meters"
        ]
        
        for i, quant_mod in enumerate(quantitative_mods):
            print(f"\nQuantitative mod {i+1}: {quant_mod}")
            response = self.config.simulate_user_request(quant_mod)
            print(f"Quantitative {i+1} response: {response}")
            
            # Verify quantitative modification was processed
            state = self.config.get_memory_state()
            self.assertGreater(state["triage_memory_steps"], i + 1,
                              f"Memory should accumulate through quantitative mod {i+1}")
        
        # Test complex quantitative modification
        complex_quant = "Make it 25% longer and 15% taller at the same time"
        print(f"\nComplex quantitative: {complex_quant}")
        complex_response = self.config.simulate_user_request(complex_quant)
        print(f"Complex quantitative response: {complex_response}")
        
        # Verify quantitative modifications
        final_state = self.config.get_memory_state()
        expected_operations = 1 + len(quantitative_mods) + 1
        
        self.assertGreaterEqual(final_state["triage_memory_steps"], expected_operations,
                               "Should handle all quantitative modifications")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Quantitative modification references test passed")
        
    def test_directional_modification_references(self):
        """Test directional references like 'rotate that clockwise'."""
        print("\n=== Test: Directional Modification References ===")
        
        # Create component for directional modification
        direction_request = "Create a bridge arch oriented north-south"
        print(f"Directional base: {direction_request}")
        direction_response = self.config.simulate_user_request(direction_request)
        print(f"Directional response: {direction_response}")
        
        # Test directional modifications
        directional_mods = [
            "Rotate that clockwise by 45 degrees",
            "Turn it to face east-west",
            "Tilt it backwards by 10 degrees",
            "Orient it perpendicular to the current direction",
            "Flip it horizontally"
        ]
        
        for i, dir_mod in enumerate(directional_mods):
            print(f"\nDirectional mod {i+1}: {dir_mod}")
            response = self.config.simulate_user_request(dir_mod)
            print(f"Directional {i+1} response: {response}")
            
            # Verify directional modification was processed
            state = self.config.get_memory_state()
            self.assertGreater(state["triage_memory_steps"], i + 1,
                              f"Memory should accumulate through directional mod {i+1}")
        
        # Test complex directional modification
        complex_direction = "Rotate it 30 degrees clockwise and tilt it forward 15 degrees"
        print(f"\nComplex directional: {complex_direction}")
        complex_response = self.config.simulate_user_request(complex_direction)
        print(f"Complex directional response: {complex_response}")
        
        # Verify directional modifications
        final_state = self.config.get_memory_state()
        expected_operations = 1 + len(directional_mods) + 1
        
        self.assertGreaterEqual(final_state["triage_memory_steps"], expected_operations,
                               "Should handle all directional modifications")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Directional modification references test passed")
        
    def test_compound_complex_references(self):
        """Test compound complex references combining multiple modification types."""
        print("\n=== Test: Compound Complex References ===")
        
        # Create base component
        compound_base = "Create a bridge structure with arch and supports"
        print(f"Compound base: {compound_base}")
        base_response = self.config.simulate_user_request(compound_base)
        print(f"Compound base response: {base_response}")
        
        # Test compound complex modifications
        compound_modifications = [
            "Move it up 10 meters and make it 20% wider",
            "Rotate it 45 degrees and add height parameters",
            "Scale it by 1.3 and shift it to the right by 5 meters",
            "Add material properties and increase the span by 30%",
            "Tilt it backwards 10 degrees and add dynamic control parameters"
        ]
        
        for i, compound_mod in enumerate(compound_modifications):
            print(f"\nCompound modification {i+1}: {compound_mod}")
            response = self.config.simulate_user_request(compound_mod)
            print(f"Compound {i+1} response: {response}")
            
            # Verify compound modification was processed
            state = self.config.get_memory_state()
            self.assertGreater(state["triage_memory_steps"], i + 1,
                              f"Memory should accumulate through compound mod {i+1}")
        
        # Test ultra-complex compound modification
        ultra_complex = "Move it up 15m, rotate 30 degrees clockwise, make it 40% longer, add wind load parameters, and tilt it forward 5 degrees"
        print(f"\nUltra-complex: {ultra_complex}")
        ultra_response = self.config.simulate_user_request(ultra_complex)
        print(f"Ultra-complex response: {ultra_response}")
        
        # Verify compound modifications
        final_state = self.config.get_memory_state()
        expected_operations = 1 + len(compound_modifications) + 1
        
        self.assertGreaterEqual(final_state["triage_memory_steps"], expected_operations,
                               "Should handle all compound modifications")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Compound complex references test passed")
        
    def test_contextual_reference_chain(self):
        """Test a chain of contextual references building on each other."""
        print("\n=== Test: Contextual Reference Chain ===")
        
        # Build a chain of contextual modifications
        reference_chain = [
            "Create a basic bridge arch",
            "Make it 20% taller",
            "Move that up by 5 meters", 
            "Add height control parameters to it",
            "Rotate the whole thing 15 degrees",
            "Now make it 10% wider",
            "Tilt that forward by 8 degrees",
            "Add material properties to the modified arch",
            "Scale the entire structure by 1.2",
            "Finally, shift it 3 meters to the left"
        ]
        
        chain_responses = []
        for i, chain_step in enumerate(reference_chain):
            print(f"\nChain step {i+1}: {chain_step}")
            response = self.config.simulate_user_request(chain_step)
            chain_responses.append(response)
            print(f"Chain {i+1} response: {response}")
            
            # Verify each step builds on previous ones
            state = self.config.get_memory_state()
            self.assertGreaterEqual(state["triage_memory_steps"], i + 1,
                                   f"Memory should accumulate through chain step {i+1}")
        
        # Test final complex reference to the whole chain
        final_reference = "Show me what we've built with all those modifications"
        print(f"\nFinal reference: {final_reference}")
        final_response = self.config.simulate_user_request(final_reference)
        print(f"Final response: {final_response}")
        
        # Verify complete reference chain
        final_state = self.config.get_memory_state()
        total_expected = len(reference_chain) + 1
        
        self.assertGreaterEqual(final_state["triage_memory_steps"], total_expected,
                               "Should handle complete contextual reference chain")
        
        # Should still be tracking components correctly
        self.assertGreater(final_state["recent_components_count"], 0,
                          "Should maintain component tracking through complex chain")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Contextual reference chain test passed")
        
    def test_complex_references_with_multiple_components(self):
        """Test complex references when multiple components are involved."""
        print("\n=== Test: Complex References with Multiple Components ===")
        
        # Create multiple components
        multi_setup = [
            "Create bridge arch A at position (0,0)",
            "Create bridge arch B at position (50,0)",
            "Create connecting beam between them"
        ]
        
        for i, setup_step in enumerate(multi_setup):
            print(f"Multi setup {i+1}: {setup_step}")
            response = self.config.simulate_user_request(setup_step)
            print(f"Multi setup {i+1} response: {response}")
        
        # Test complex references targeting specific components
        multi_complex_refs = [
            "Move arch A up by 10 meters and make it 20% wider",
            "Rotate arch B 30 degrees and add height parameters",
            "Make the connecting beam 15% longer and tilt it 5 degrees",
            "Scale all arches by 1.1 but leave the beam unchanged",
            "Add wind load parameters to arch A and material properties to arch B"
        ]
        
        for i, complex_ref in enumerate(multi_complex_refs):
            print(f"\nMulti complex {i+1}: {complex_ref}")
            response = self.config.simulate_user_request(complex_ref)
            print(f"Multi complex {i+1} response: {response}")
            
            # Verify complex multi-component references
            state = self.config.get_memory_state()
            expected_steps = len(multi_setup) + i + 1
            self.assertGreaterEqual(state["triage_memory_steps"], expected_steps,
                                   f"Should handle multi-component complex ref {i+1}")
        
        # Test ultra-complex multi-component reference
        ultra_multi = "Move arch A up 8m and arch B right 5m, scale the beam by 1.3, add parameters to all components"
        print(f"\nUltra multi-component: {ultra_multi}")
        ultra_response = self.config.simulate_user_request(ultra_multi)
        print(f"Ultra multi response: {ultra_response}")
        
        # Verify complex multi-component handling
        final_state = self.config.get_memory_state()
        total_operations = len(multi_setup) + len(multi_complex_refs) + 1
        
        self.assertGreaterEqual(final_state["triage_memory_steps"], total_operations,
                               "Should handle ultra-complex multi-component references")
        
        # Should maintain tracking of multiple components
        self.assertGreater(final_state["recent_components_count"], 2,
                          "Should track multiple components through complex operations")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Complex references with multiple components test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)