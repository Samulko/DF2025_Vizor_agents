"""
Test Scenario 6: Memory Tools Validation

This test validates the specific memory tools that are part of our memory fix:
1. get_most_recent_component() - Finding recently created components
2. debug_component_tracking() - Debugging memory state
3. track_geometry_result() - Tracking components from geometry operations
4. Memory tool integration with vague reference resolution
5. Memory persistence across agent interactions

These tools are central to the memory synchronization fix and enable
proper resolution of vague references like "modify the curve you just drew".
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary, 
    get_components_by_type,
    get_most_recent_component_of_type,
    get_mock_state
)


class TestMemoryToolsValidation(MemoryTestCase):
    """Test the specific memory tools added for the memory synchronization fix."""
    
    def test_get_most_recent_component_basic(self):
        """Test get_most_recent_component tool functionality."""
        print("\n=== Test: Get Most Recent Component Basic ===")
        
        # Create components of different types
        creation_sequence = [
            "Create bridge foundation points",
            "Create bridge curve",
            "Create bridge arch"
        ]
        
        for i, request in enumerate(creation_sequence):
            print(f"Creating {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Creation {i+1} response: {response}")
            
        # Test get_most_recent_component without filter
        recent_request = "What was the most recent component I created?"
        print(f"Recent query: {recent_request}")
        
        recent_response = self.config.simulate_user_request(recent_request)
        print(f"Recent response: {recent_response}")
        
        # Should reference the arch (last created)
        self.assertIn("arch", recent_response.lower(), 
                     "Should reference the most recent component (arch)")
        
        # Test get_most_recent_component with type filter
        recent_curve_request = "What was the most recent bridge curve I created?"
        print(f"Recent curve query: {recent_curve_request}")
        
        recent_curve_response = self.config.simulate_user_request(recent_curve_request)
        print(f"Recent curve response: {recent_curve_response}")
        
        # Should reference the curve specifically
        self.assertIn("curve", recent_curve_response.lower(),
                     "Should reference the most recent curve component")
        
        # Verify memory state
        final_state = self.config.get_memory_state()
        expected_min_steps = len(creation_sequence) + 2  # creation + 2 queries
        self.assertGreaterEqual(final_state["triage_memory_steps"], expected_min_steps,
                               "Should have memory from all operations")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Get most recent component basic test passed")
        
    def test_debug_component_tracking_tool(self):
        """Test debug_component_tracking tool functionality."""
        print("\n=== Test: Debug Component Tracking Tool ===")
        
        # Create some components to debug
        setup_requests = [
            "Create bridge points at (0,0) and (50,0)",
            "Create curve connecting the points"
        ]
        
        for i, request in enumerate(setup_requests):
            print(f"Setup {i+1}: {request}")
            response = self.config.simulate_user_request(request)
            print(f"Setup {i+1} response: {response}")
            
        # Use debug tool
        debug_request = "Debug the current component tracking state"
        print(f"Debug request: {debug_request}")
        
        debug_response = self.config.simulate_user_request(debug_request)
        print(f"Debug response: {debug_response}")
        
        # Debug response should contain tracking information
        self.assertIn("component", debug_response.lower(),
                     "Debug should show component tracking info")
        
        # Create another component and debug again
        additional_request = "Create bridge arch with 8m height"
        print(f"Additional creation: {additional_request}")
        
        additional_response = self.config.simulate_user_request(additional_request)
        print(f"Additional response: {additional_response}")
        
        # Debug again to see updated state
        debug2_request = "Show me the current tracking state again"
        print(f"Debug 2 request: {debug2_request}")
        
        debug2_response = self.config.simulate_user_request(debug2_request)
        print(f"Debug 2 response: {debug2_response}")
        
        # Should show updated tracking state
        final_state = self.config.get_memory_state()
        print(f"Final memory state: {final_state}")
        
        # Should have progressed through all operations
        self.assertGreater(final_state["triage_memory_steps"], len(setup_requests) + 3,
                          "Should have memory from setup + debug operations")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Debug component tracking tool test passed")
        
    def test_track_geometry_result_tool(self):
        """Test track_geometry_result tool functionality."""
        print("\n=== Test: Track Geometry Result Tool ===")
        
        # Create geometry that should be tracked
        geometry_request = "Create a complex bridge structure with multiple components"
        print(f"Geometry request: {geometry_request}")
        
        geometry_response = self.config.simulate_user_request(geometry_request)
        print(f"Geometry response: {geometry_response}")
        
        # The track_geometry_result should be called automatically by our memory fix
        # Verify it's working by checking memory state
        after_geometry = self.config.get_memory_state()
        print(f"After geometry memory: {after_geometry}")
        
        # Should have tracked components
        self.assertGreater(after_geometry["recent_components_count"], 0,
                          "Should have tracked geometry components")
        
        # Test explicit tracking request
        explicit_track = "Track the results from that geometry operation"
        print(f"Explicit tracking: {explicit_track}")
        
        track_response = self.config.simulate_user_request(explicit_track)
        print(f"Track response: {track_response}")
        
        # Should show tracking confirmation
        self.assertIn("track", track_response.lower(),
                     "Should confirm component tracking")
        
        # Verify tracking persistence
        final_state = self.config.get_memory_state()
        self.assertGreaterEqual(final_state["recent_components_count"],
                               after_geometry["recent_components_count"],
                               "Tracking should persist")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Track geometry result tool test passed")
        
    def test_memory_tools_integration_workflow(self):
        """Test integration of all memory tools in a realistic workflow."""
        print("\n=== Test: Memory Tools Integration Workflow ===")
        
        # Step 1: Create initial component
        step1 = "Create a bridge curve for main span"
        print(f"Step 1: {step1}")
        response1 = self.config.simulate_user_request(step1)
        print(f"Step 1 response: {response1}")
        
        # Step 2: Debug to see what was tracked
        step2 = "Debug what components are currently tracked"
        print(f"Step 2: {step2}")
        response2 = self.config.simulate_user_request(step2)
        print(f"Step 2 response: {response2}")
        
        # Step 3: Create another component
        step3 = "Create bridge foundation points"
        print(f"Step 3: {step3}")
        response3 = self.config.simulate_user_request(step3)
        print(f"Step 3 response: {response3}")
        
        # Step 4: Use most recent component query
        step4 = "What was the most recent thing I created?"
        print(f"Step 4: {step4}")
        response4 = self.config.simulate_user_request(step4)
        print(f"Step 4 response: {response4}")
        
        # Should reference the foundation points (most recent)
        self.assertIn("point", response4.lower(),
                     "Should reference most recent component (points)")
        
        # Step 5: Modify using vague reference (testing memory tool integration)
        step5 = "Modify the curve I created earlier"
        print(f"Step 5: {step5}")
        response5 = self.config.simulate_user_request(step5)
        print(f"Step 5 response: {response5}")
        
        # Step 6: Debug final state
        step6 = "Show me the final tracking state"
        print(f"Step 6: {step6}")
        response6 = self.config.simulate_user_request(step6)
        print(f"Step 6 response: {response6}")
        
        # Verify complete workflow
        final_state = self.config.get_memory_state()
        print(f"Integration workflow final state: {final_state}")
        
        # Should have substantial memory accumulation
        self.assertGreaterEqual(final_state["triage_memory_steps"], 6,
                               "Should have memory from complete workflow")
        
        # Should have tracked multiple components
        self.assertGreater(final_state["recent_components_count"], 0,
                          "Should have tracked components throughout workflow")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Memory tools integration workflow test passed")
        
    def test_memory_tools_with_errors(self):
        """Test memory tools functionality when components have errors."""
        print("\n=== Test: Memory Tools with Errors ===")
        
        # Create component with error
        from .mock_mcp_tools import simulate_error_type
        simulate_error_type("syntax")
        
        error_request = "Create bridge script with syntax_error"
        print(f"Error creation: {error_request}")
        error_response = self.config.simulate_user_request(error_request)
        print(f"Error response: {error_response}")
        
        # Debug should show error state
        debug_error = "Debug the component tracking including any errors"
        print(f"Debug errors: {debug_error}")
        debug_response = self.config.simulate_user_request(debug_error)
        print(f"Debug error response: {debug_response}")
        
        # Should show error information
        error_summary = get_test_state_summary()
        print(f"Error summary: {error_summary}")
        self.assertGreater(error_summary["components_with_errors"], 0,
                          "Should track components with errors")
        
        # Test most recent with error
        recent_error = "What was the most recent component, even if it has errors?"
        print(f"Recent with error: {recent_error}")
        recent_response = self.config.simulate_user_request(recent_error)
        print(f"Recent error response: {recent_response}")
        
        # Should still reference the component despite error
        self.assertIn("script", recent_response.lower(),
                     "Should reference recent component even with errors")
        
        # Fix the error and test tracking
        fix_request = "Fix that syntax error"
        print(f"Fix request: {fix_request}")
        fix_response = self.config.simulate_user_request(fix_request)
        print(f"Fix response: {fix_response}")
        
        # Debug after fix
        debug_fixed = "Debug the state after error fix"
        print(f"Debug after fix: {debug_fixed}")
        debug_fixed_response = self.config.simulate_user_request(debug_fixed)
        print(f"Debug fixed response: {debug_fixed_response}")
        
        # Should show resolved state
        final_error_summary = get_test_state_summary()
        print(f"Final error summary: {final_error_summary}")
        
        # Verify error handling in memory tools
        final_state = self.config.get_memory_state()
        self.assertGreaterEqual(final_state["triage_memory_steps"], 5,
                               "Should handle error workflow with memory tools")
        
        print("✅ Memory tools with errors test passed")
        
    def test_memory_tool_performance_multiple_components(self):
        """Test memory tool performance with many components."""
        print("\n=== Test: Memory Tool Performance Multiple Components ===")
        
        # Create many components
        many_components = []
        for i in range(10):
            request = f"Create bridge element {i+1}"
            print(f"Creating element {i+1}")
            response = self.config.simulate_user_request(request)
            many_components.append(response)
            
        print(f"Created {len(many_components)} components")
        
        # Test memory tools with many components
        performance_tests = [
            "What was the most recent component?",
            "Debug the tracking state with all components",
            "What was the most recent bridge curve?",
            "Show me the tracking performance"
        ]
        
        for i, perf_test in enumerate(performance_tests):
            print(f"Performance test {i+1}: {perf_test}")
            start_time = time.time()
            response = self.config.simulate_user_request(perf_test)
            end_time = time.time()
            
            print(f"Performance {i+1} response time: {end_time - start_time:.3f}s")
            print(f"Performance {i+1} response: {response}")
            
            # Should handle multiple components efficiently
            self.assertLess(end_time - start_time, 5.0,
                           f"Memory tool {i+1} should perform reasonably with many components")
        
        # Final performance check
        final_state = self.config.get_memory_state()
        total_operations = len(many_components) + len(performance_tests)
        
        print(f"Final state with many components: {final_state}")
        self.assertGreaterEqual(final_state["triage_memory_steps"], total_operations,
                               "Should handle many components with memory tools")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Memory tool performance test passed")
        
    def test_memory_tools_cross_agent_consistency(self):
        """Test memory tools consistency across triage and geometry agents."""
        print("\n=== Test: Memory Tools Cross-Agent Consistency ===")
        
        # Create component via geometry agent delegation
        geometry_request = "Create complex bridge geometry with curves and arches"
        print(f"Geometry delegation: {geometry_request}")
        geometry_response = self.config.simulate_user_request(geometry_request)
        print(f"Geometry response: {geometry_response}")
        
        # Check memory consistency
        consistency_check = "Debug the component tracking to verify consistency"
        print(f"Consistency check: {consistency_check}")
        consistency_response = self.config.simulate_user_request(consistency_check)
        print(f"Consistency response: {consistency_response}")
        
        # Test cross-agent recent component query
        cross_agent_recent = "What geometry did we just create together?"
        print(f"Cross-agent recent: {cross_agent_recent}")
        cross_response = self.config.simulate_user_request(cross_agent_recent)
        print(f"Cross-agent response: {cross_response}")
        
        # Should show consistent tracking across agents
        memory_state = self.config.get_memory_state()
        print(f"Cross-agent memory state: {memory_state}")
        
        # Both triage and geometry agents should have memory
        self.assertGreater(memory_state["triage_memory_steps"], 0,
                          "Triage agent should have memory")
        self.assertGreater(memory_state["geometry_memory_steps"], 0,
                          "Geometry agent should have memory")
        
        # Test memory tool with cross-agent modification
        cross_modify = "Modify the geometry we just created together"
        print(f"Cross-agent modify: {cross_modify}")
        modify_response = self.config.simulate_user_request(cross_modify)
        print(f"Cross-modify response: {modify_response}")
        
        # Final consistency verification
        final_state = self.config.get_memory_state()
        self.assertGreaterEqual(final_state["triage_memory_steps"], 4,
                               "Should maintain cross-agent memory consistency")
        
        # Verify no errors
        self.config.assert_no_stale_component_errors()
        
        print("✅ Memory tools cross-agent consistency test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)