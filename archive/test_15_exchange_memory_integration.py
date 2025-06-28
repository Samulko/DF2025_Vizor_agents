#!/usr/bin/env python3
"""
15-Exchange Memory Integration Test

This test runs a comprehensive scenario across 15 exchanges that:
1. Manipulates geometry through multiple parameter updates
2. Calls SysLogic agent for structural validation
3. Tests memory persistence and original value recall
4. Validates the native smolagents memory integration

The test simulates a realistic design workflow where:
- Original element values are modified multiple times
- Memory system tracks all changes
- Agents can recall original states
- SysLogic validates structural integrity
"""

import time
from datetime import datetime
from typing import Dict, Any

from src.bridge_design_system.main import validate_environment
from src.bridge_design_system.agents import TriageAgent
from src.bridge_design_system.state.component_registry import initialize_registry
from src.bridge_design_system.config.logging_config import get_logger
from src.bridge_design_system.memory import (
    get_memory_statistics, 
    validate_memory_integrity,
    get_original_element_state
)

logger = get_logger(__name__)

class MemoryIntegrationTest:
    """
    Comprehensive test of native smolagents memory integration.
    
    Tests the core use case: agents remembering original element values
    even after multiple modifications, and ability to query design history.
    """
    
    def __init__(self):
        """Initialize the test system."""
        self.triage = None
        self.registry = None
        self.test_results = []
        self.exchange_count = 0
        self.start_time = None
        
    def setup(self) -> bool:
        """Set up the test environment."""
        try:
            print("🧪 Setting up 15-Exchange Memory Integration Test")
            print("=" * 60)
            
            # Validate environment
            if not validate_environment():
                print("❌ Environment validation failed")
                return False
                
            # Initialize registry
            self.registry = initialize_registry()
            print("✅ Component registry initialized")
            
            # Create triage system with memory tracking
            self.triage = TriageAgent(component_registry=self.registry)
            print("✅ Triage system initialized with memory tracking")
            
            # Reset to ensure clean state
            self.triage.reset_all_agents()
            self.registry.clear()
            print("✅ Starting with fresh agent memories")
            
            self.start_time = datetime.now()
            print(f"🚀 Test started at {self.start_time.strftime('%H:%M:%S')}")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_exchange(self, exchange_num: int, request: str, expected_memory_changes: bool = False) -> Dict[str, Any]:
        """Execute a single exchange and track results."""
        self.exchange_count += 1
        
        print(f"📡 EXCHANGE {exchange_num}/15: {request[:80]}{'...' if len(request) > 80 else ''}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Execute the request
            response = self.triage.handle_design_request(request)
            
            duration = time.time() - start_time
            
            # Gather memory statistics from triage and geometry agents
            triage_stats = self._get_agent_memory_stats("triage")
            geometry_stats = self._get_agent_memory_stats("geometry")
            
            result = {
                "exchange": exchange_num,
                "request": request,
                "success": response.success,
                "response": response.message[:200] + "..." if len(response.message) > 200 else response.message,
                "duration": duration,
                "triage_memory": triage_stats,
                "geometry_memory": geometry_stats,
                "expected_memory_changes": expected_memory_changes,
                "timestamp": datetime.now().isoformat()
            }
            
            if response.success:
                print(f"✅ SUCCESS ({duration:.1f}s)")
                print(f"📝 Response: {result['response']}")
            else:
                print(f"❌ FAILED ({duration:.1f}s)")
                print(f"💥 Error: {response.message}")
                
            # Show memory activity
            total_memory_steps = triage_stats.get("total_steps", 0) + geometry_stats.get("total_steps", 0)
            total_design_changes = triage_stats.get("design_changes", 0) + geometry_stats.get("design_changes", 0)
            
            print(f"🧠 Memory: {total_memory_steps} steps, {total_design_changes} design changes")
            
            if expected_memory_changes and total_design_changes == 0:
                print("⚠️  Expected memory changes but none detected")
                
            self.test_results.append(result)
            print()
            
            return result
            
        except Exception as e:
            print(f"❌ EXCHANGE FAILED: {e}")
            import traceback
            traceback.print_exc()
            
            result = {
                "exchange": exchange_num,
                "request": request,
                "success": False,
                "response": f"Exception: {str(e)}",
                "duration": time.time() - start_time,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            self.test_results.append(result)
            print()
            return result
    
    def _get_agent_memory_stats(self, agent_type: str) -> Dict[str, Any]:
        """Get memory statistics for a specific agent."""
        try:
            if agent_type == "triage":
                return get_memory_statistics(self.triage.manager)
            elif agent_type == "geometry":
                # Get geometry agent from triage system
                if hasattr(self.triage, 'geometry_agent'):
                    geometry_agent = self.triage.geometry_agent
                    if hasattr(geometry_agent, '_wrapper'):
                        return get_memory_statistics(geometry_agent._wrapper.agent)
                    else:
                        return get_memory_statistics(geometry_agent)
                else:
                    return {"error": "Geometry agent not found"}
            else:
                return {"error": f"Unknown agent type: {agent_type}"}
        except Exception as e:
            return {"error": str(e)}
    
    def test_original_value_recall(self, element_id: str) -> Dict[str, Any]:
        """Test ability to recall original element values."""
        print(f"🔍 Testing original value recall for element {element_id}")
        
        try:
            # Try to get original state from both agents
            triage_original = None
            geometry_original = None
            
            # Check triage agent memory
            try:
                triage_original = get_original_element_state(self.triage.manager, element_id)
            except Exception as e:
                print(f"⚠️  Triage memory query failed: {e}")
            
            # Check geometry agent memory
            try:
                if hasattr(self.triage, 'geometry_agent'):
                    geometry_agent = self.triage.geometry_agent
                    if hasattr(geometry_agent, '_wrapper'):
                        geometry_original = get_original_element_state(geometry_agent._wrapper.agent, element_id)
                    else:
                        geometry_original = get_original_element_state(geometry_agent, element_id)
            except Exception as e:
                print(f"⚠️  Geometry memory query failed: {e}")
                
            result = {
                "element_id": element_id,
                "triage_original": triage_original,
                "geometry_original": geometry_original,
                "found_original": bool(triage_original or geometry_original)
            }
            
            if result["found_original"]:
                print(f"✅ Found original state for element {element_id}")
                if triage_original:
                    print(f"   Triage memory: {triage_original}")
                if geometry_original:
                    print(f"   Geometry memory: {geometry_original}")
            else:
                print(f"❌ No original state found for element {element_id}")
                
            return result
            
        except Exception as e:
            print(f"❌ Original value recall test failed: {e}")
            return {"error": str(e)}
    
    def run_15_exchange_test(self) -> bool:
        """Run the complete 15-exchange test scenario."""
        try:
            print("🎬 Starting 15-Exchange Memory Integration Test")
            print("🎯 Goal: Test memory persistence across geometry manipulation and SysLogic validation")
            print()
            
            # EXCHANGE 1: Initial system check
            self.execute_exchange(1, 
                "Check the current bridge model status and list all element IDs. This is our baseline.")
            
            # EXCHANGE 2: Get original values for element 002 (should be length 0.40)
            self.execute_exchange(2, 
                "What are the current parameter values for element '002'? Please show the center point, direction, and length.")
            
            # EXCHANGE 3: First modification of element 002
            self.execute_exchange(3, 
                "Update element '002' length from 0.40 to 0.35 meters. Keep all other parameters the same.", 
                expected_memory_changes=True)
            
            # EXCHANGE 4: Verify the change
            self.execute_exchange(4, 
                "Confirm element '002' now has length 0.35. Show me the current parameters.")
            
            # EXCHANGE 5: Modify element 001 center point
            self.execute_exchange(5, 
                "Move element '001' center point to position (-0.15, -0.12, 0.025). Keep direction and length unchanged.", 
                expected_memory_changes=True)
            
            # EXCHANGE 6: Call SysLogic for structural validation
            self.execute_exchange(6, 
                "Use the SysLogic agent to validate the structural integrity of the current bridge design. Check for any issues.")
            
            # EXCHANGE 7: Second modification of element 002
            self.execute_exchange(7, 
                "Change element '002' length again from 0.35 to 0.25 meters. This is the second change to this element.", 
                expected_memory_changes=True)
            
            # EXCHANGE 8: Test memory recall - what was original length of 002?
            self.execute_exchange(8, 
                "What was the original length of element '002' before any modifications? The system should remember this from memory.")
            
            # EXCHANGE 9: Modify element 003 direction
            self.execute_exchange(9, 
                "Rotate element '003' direction vector by 5 degrees. Update the direction while keeping center and length unchanged.", 
                expected_memory_changes=True)
            
            # EXCHANGE 10: SysLogic validation after multiple changes
            self.execute_exchange(10, 
                "Run another SysLogic structural analysis. How do the recent changes affect structural performance?")
            
            # EXCHANGE 11: Batch modification - multiple elements
            self.execute_exchange(11, 
                "Update multiple elements: change element '001' length to 0.45, and element '003' length to 0.75. Process both changes.", 
                expected_memory_changes=True)
            
            # EXCHANGE 12: Memory recall test for element 001
            self.execute_exchange(12, 
                "What was the original center point and length of element '001'? Show the design history for this element.")
            
            # EXCHANGE 13: Final SysLogic comprehensive check
            self.execute_exchange(13, 
                "Perform a comprehensive SysLogic analysis of the final bridge design. Compare structural performance to original.")
            
            # EXCHANGE 14: Memory system validation
            self.execute_exchange(14, 
                "Generate a summary of all design changes made during this session. What elements were modified and what were their original values?")
            
            # EXCHANGE 15: System status and memory health check
            self.execute_exchange(15, 
                "Show the current system status, agent memory statistics, and confirm all elements are properly tracked.")
            
            return True
            
        except Exception as e:
            print(f"❌ 15-exchange test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_memory_recall_capabilities(self):
        """Test memory recall for modified elements."""
        print("\n🔍 MEMORY RECALL CAPABILITY TESTS")
        print("=" * 50)
        
        # Test recall for elements that should have been modified
        test_elements = ["001", "002", "003"]
        
        for element_id in test_elements:
            self.test_original_value_recall(element_id)
            print()
    
    def generate_final_report(self):
        """Generate comprehensive test report."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n📊 15-EXCHANGE MEMORY INTEGRATION TEST REPORT")
        print("=" * 60)
        
        successful_exchanges = sum(1 for r in self.test_results if r.get("success", False))
        total_exchanges = len(self.test_results)
        
        print(f"🕒 Test Duration: {duration}")
        print(f"✅ Successful Exchanges: {successful_exchanges}/{total_exchanges}")
        print(f"❌ Failed Exchanges: {total_exchanges - successful_exchanges}")
        print()
        
        # Memory statistics summary
        print("🧠 MEMORY SYSTEM PERFORMANCE:")
        
        final_triage_stats = self._get_agent_memory_stats("triage")
        final_geometry_stats = self._get_agent_memory_stats("geometry")
        
        print(f"   Triage Agent Memory:")
        print(f"     Total steps: {final_triage_stats.get('total_steps', 0)}")
        print(f"     Design changes: {final_triage_stats.get('design_changes', 0)}")
        print(f"     Memory records: {final_triage_stats.get('memory_records', 0)}")
        
        print(f"   Geometry Agent Memory:")
        print(f"     Total steps: {final_geometry_stats.get('total_steps', 0)}")
        print(f"     Design changes: {final_geometry_stats.get('design_changes', 0)}")
        print(f"     Memory records: {final_geometry_stats.get('memory_records', 0)}")
        print(f"     MCP tool calls: {final_geometry_stats.get('mcp_tool_calls', 0)}")
        
        # Validate memory integrity
        print("\n🔧 MEMORY INTEGRITY VALIDATION:")
        try:
            triage_validation = validate_memory_integrity(self.triage.manager)
            print(f"   Triage memory valid: {triage_validation.get('valid', False)}")
            print(f"   Issues found: {len(triage_validation.get('issues', []))}")
            print(f"   Warnings: {len(triage_validation.get('warnings', []))}")
        except Exception as e:
            print(f"   Triage validation failed: {e}")
        
        # Exchange performance breakdown
        print("\n⚡ EXCHANGE PERFORMANCE:")
        for result in self.test_results:
            status = "✅" if result.get("success", False) else "❌"
            duration = result.get("duration", 0)
            exchange = result.get("exchange", "?")
            print(f"   {status} Exchange {exchange}: {duration:.1f}s")
        
        # Success criteria evaluation
        print("\n🎯 SUCCESS CRITERIA EVALUATION:")
        
        criteria = {
            "All exchanges completed": total_exchanges == 15,
            "Majority exchanges successful": successful_exchanges >= 12,
            "Memory tracking active": (
                final_triage_stats.get('total_steps', 0) > 0 or 
                final_geometry_stats.get('total_steps', 0) > 0
            ),
            "Design changes recorded": (
                final_triage_stats.get('design_changes', 0) > 0 or 
                final_geometry_stats.get('design_changes', 0) > 0
            ),
            "MCP integration working": final_geometry_stats.get('mcp_tool_calls', 0) > 0,
            "Memory integrity maintained": triage_validation.get('valid', False) if 'triage_validation' in locals() else False
        }
        
        passed_criteria = sum(1 for passed in criteria.values() if passed)
        total_criteria = len(criteria)
        
        for criterion, passed in criteria.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {criterion}")
            
        print(f"\n🏆 OVERALL SUCCESS: {passed_criteria}/{total_criteria} criteria met")
        
        if passed_criteria >= total_criteria - 1:  # Allow 1 failure
            print("🎉 MEMORY INTEGRATION TEST PASSED!")
            return True
        else:
            print("💥 MEMORY INTEGRATION TEST FAILED!")
            return False


def main():
    """Run the 15-exchange memory integration test."""
    test = MemoryIntegrationTest()
    
    try:
        # Setup
        if not test.setup():
            print("❌ Test setup failed")
            return False
        
        # Run 15 exchanges
        if not test.run_15_exchange_test():
            print("❌ 15-exchange test failed")
            return False
        
        # Test memory recall
        test.test_memory_recall_capabilities()
        
        # Generate report
        success = test.generate_final_report()
        
        return success
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 15-Exchange Native Smolagents Memory Integration Test")
    print("🎯 Testing memory persistence across geometry manipulation and SysLogic validation")
    print("🔗 Using live Grasshopper bridge and LLM models")
    print()
    
    success = main()
    exit(0 if success else 1)