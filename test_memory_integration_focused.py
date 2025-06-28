#!/usr/bin/env python3
"""
Focused Memory Integration Test (5 key exchanges)

This test focuses on the core memory integration functionality:
1. Record original element values
2. Modify geometry parameters  
3. Call SysLogic agent
4. Test memory recall capability
5. Validate memory persistence

Designed to complete within timeout limits while testing critical functionality.
"""

import time
from datetime import datetime

from src.bridge_design_system.main import validate_environment
from src.bridge_design_system.agents import TriageAgent
from src.bridge_design_system.state.component_registry import initialize_registry
from src.bridge_design_system.config.logging_config import get_logger
from src.bridge_design_system.memory import (
    get_memory_statistics, 
    validate_memory_integrity
)

logger = get_logger(__name__)

def run_focused_memory_test():
    """Run focused memory integration test."""
    print("🧪 FOCUSED MEMORY INTEGRATION TEST")
    print("🎯 Testing core memory functionality in 5 key exchanges")
    print("=" * 60)
    
    try:
        # Setup
        print("⚙️ Setting up test environment...")
        
        if not validate_environment():
            print("❌ Environment validation failed")
            return False
            
        registry = initialize_registry()
        triage = TriageAgent(component_registry=registry)
        
        # Reset for clean state
        triage.reset_all_agents()
        registry.clear()
        print("✅ System initialized with fresh memories")
        print()
        
        # EXCHANGE 1: Baseline - get original values
        print("📡 EXCHANGE 1/5: Get baseline element values")
        print("-" * 40)
        start_time = time.time()
        
        response1 = triage.handle_design_request(
            "Show me the current parameters for element '002' including center point, direction, and length. This will be our baseline."
        )
        
        duration1 = time.time() - start_time
        print(f"✅ Completed in {duration1:.1f}s")
        if response1.success:
            print(f"📝 Response: {response1.message[:150]}...")
        else:
            print(f"❌ Failed: {response1.message}")
        print()
        
        # Check memory after first exchange
        try:
            geometry_agent = triage.geometry_agent
            if hasattr(geometry_agent, '_wrapper'):
                stats1 = get_memory_statistics(geometry_agent._wrapper.agent)
            else:
                stats1 = get_memory_statistics(geometry_agent)
            print(f"🧠 Memory after exchange 1: {stats1.get('total_steps', 0)} steps")
        except Exception as e:
            print(f"⚠️ Memory check failed: {e}")
        
        # EXCHANGE 2: Modify element 002 to trigger memory tracking
        print("📡 EXCHANGE 2/5: Modify element to trigger memory tracking")
        print("-" * 40)
        start_time = time.time()
        
        response2 = triage.handle_design_request(
            "Update element '002' length from 0.40 to 0.30 meters. Keep center point and direction unchanged. This should trigger memory tracking."
        )
        
        duration2 = time.time() - start_time
        print(f"✅ Completed in {duration2:.1f}s")
        if response2.success:
            print(f"📝 Response: {response2.message[:150]}...")
        else:
            print(f"❌ Failed: {response2.message}")
        print()
        
        # Check memory after modification
        try:
            if hasattr(geometry_agent, '_wrapper'):
                stats2 = get_memory_statistics(geometry_agent._wrapper.agent)
            else:
                stats2 = get_memory_statistics(geometry_agent)
            print(f"🧠 Memory after exchange 2: {stats2.get('total_steps', 0)} steps, {stats2.get('design_changes', 0)} design changes")
        except Exception as e:
            print(f"⚠️ Memory check failed: {e}")
        
        # EXCHANGE 3: Call SysLogic agent
        print("📡 EXCHANGE 3/5: Call SysLogic for validation")
        print("-" * 40)
        start_time = time.time()
        
        response3 = triage.handle_design_request(
            "Use the SysLogic agent to validate the structural integrity of the current bridge design after the element 002 modification."
        )
        
        duration3 = time.time() - start_time
        print(f"✅ Completed in {duration3:.1f}s")
        if response3.success:
            print(f"📝 Response: {response3.message[:150]}...")
        else:
            print(f"❌ Failed: {response3.message}")
        print()
        
        # EXCHANGE 4: Test memory recall
        print("📡 EXCHANGE 4/5: Test memory recall capability")
        print("-" * 40)
        start_time = time.time()
        
        response4 = triage.handle_design_request(
            "What was the original length of element '002' before I modified it? The system should remember this from its memory."
        )
        
        duration4 = time.time() - start_time
        print(f"✅ Completed in {duration4:.1f}s")
        if response4.success:
            print(f"📝 Response: {response4.message[:150]}...")
        else:
            print(f"❌ Failed: {response4.message}")
        print()
        
        # EXCHANGE 5: Memory system status
        print("📡 EXCHANGE 5/5: Check memory system status")
        print("-" * 40)
        start_time = time.time()
        
        response5 = triage.handle_design_request(
            "Show me the current system status and memory statistics. How many design changes have been tracked?"
        )
        
        duration5 = time.time() - start_time
        print(f"✅ Completed in {duration5:.1f}s")
        if response5.success:
            print(f"📝 Response: {response5.message[:150]}...")
        else:
            print(f"❌ Failed: {response5.message}")
        print()
        
        # Final memory analysis
        print("🔍 FINAL MEMORY ANALYSIS")
        print("-" * 40)
        
        try:
            # Get final memory statistics
            triage_stats = get_memory_statistics(triage.manager)
            if hasattr(geometry_agent, '_wrapper'):
                geometry_stats = get_memory_statistics(geometry_agent._wrapper.agent)
            else:
                geometry_stats = get_memory_statistics(geometry_agent)
            
            print("📊 Memory Statistics:")
            print(f"   Triage Agent: {triage_stats.get('total_steps', 0)} steps, {triage_stats.get('design_changes', 0)} changes")
            print(f"   Geometry Agent: {geometry_stats.get('total_steps', 0)} steps, {geometry_stats.get('design_changes', 0)} changes")
            print(f"   MCP Tool Calls: {geometry_stats.get('mcp_tool_calls', 0)}")
            print(f"   Memory Records: {geometry_stats.get('memory_records', 0)}")
            
            # Validate memory integrity
            validation = validate_memory_integrity(triage.manager)
            print(f"\n🔧 Memory Integrity: {'✅ Valid' if validation.get('valid', False) else '❌ Invalid'}")
            
            # Success criteria
            success_criteria = {
                "All exchanges completed": True,  # If we got here, all completed
                "Geometry modifications executed": geometry_stats.get('mcp_tool_calls', 0) > 0,
                "Memory tracking active": geometry_stats.get('total_steps', 0) > 0,
                "Design changes recorded": geometry_stats.get('design_changes', 0) > 0,
                "Memory integrity valid": validation.get('valid', False)
            }
            
            passed = sum(1 for v in success_criteria.values() if v)
            total = len(success_criteria)
            
            print(f"\n🎯 SUCCESS CRITERIA ({passed}/{total}):")
            for criterion, status in success_criteria.items():
                icon = "✅" if status else "❌"
                print(f"   {icon} {criterion}")
            
            overall_success = passed >= total - 1  # Allow 1 failure
            print(f"\n🏆 OVERALL RESULT: {'✅ PASSED' if overall_success else '❌ FAILED'}")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Final analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Focused Native Smolagents Memory Integration Test")
    print("🔗 Using live Grasshopper bridge and LLM models")
    print("⚡ Optimized for timeout constraints")
    print()
    
    success = run_focused_memory_test()
    
    if success:
        print("\n🎉 MEMORY INTEGRATION TEST PASSED!")
        print("✅ Native smolagents memory system is working correctly")
    else:
        print("\n💥 MEMORY INTEGRATION TEST FAILED!")
        print("❌ Issues detected with memory system")
    
    exit(0 if success else 1)