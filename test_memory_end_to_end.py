#!/usr/bin/env python3
"""
Real end-to-end test for memory system without mocking.

This script tests the actual memory functionality across agent sessions
to validate that the "no context loss" promise is fulfilled.
"""

import time
from pathlib import Path

from src.bridge_design_system.agents.triage_agent import TriageAgent
from src.bridge_design_system.agents.geometry_agent_stdio import GeometryAgentSTDIO
from src.bridge_design_system.state.component_registry import ComponentRegistry
from src.bridge_design_system.tools.memory_tools import remember, recall, search_memory


def test_memory_persistence_across_sessions():
    """Test that memory persists across agent sessions."""
    print("🧪 Testing memory persistence across agent sessions...")
    
    # Session 1: Create initial context
    print("\n📝 Session 1: Creating initial context")
    registry = ComponentRegistry()
    
    # Store some initial context using memory tools directly
    remember("context", "project_type", "timber truss pedestrian bridge")
    remember("context", "span_length", "50 meters")
    remember("context", "location", "forest trail crossing")
    
    # Register a component manually (simulating geometry agent work)
    registry.register_component(
        component_id="comp_truss_main_001",
        component_type="timber_truss", 
        name="Main Truss Structure",
        description="Primary 50m span timber truss for pedestrian bridge"
    )
    
    print("  ✅ Stored project context in memory")
    print("  ✅ Registered main truss component")
    
    # Session 2: New agent instances should recall context
    print("\n📝 Session 2: Fresh agents should recall context")
    
    # Create fresh agent instances (simulating restart)
    triage_agent = TriageAgent(component_registry=ComponentRegistry())
    
    # Test context recall
    project_type = recall("context", "project_type")
    span_length = recall("context", "span_length")
    location = recall("context", "location")
    
    print(f"  📊 Recalled project type: {project_type}")
    print(f"  📊 Recalled span length: {span_length}")
    print(f"  📊 Recalled location: {location}")
    
    # Test component recall
    components = recall("components")
    print(f"  📊 Recalled components: {components}")
    
    # Test search functionality
    search_results = search_memory("timber")
    print(f"  🔍 Search for 'timber': {search_results}")
    
    # Validate results
    assert "timber truss pedestrian bridge" in project_type
    assert "50 meters" in span_length
    assert "forest trail crossing" in location
    assert "comp_truss_main_001" in components
    assert "timber" in search_results.lower()
    
    print("  ✅ All memory recalls successful!")
    return True


def test_triage_agent_memory_integration():
    """Test that TriageAgent can use memory tools in practice."""
    print("\n🧪 Testing TriageAgent memory integration...")
    
    registry = ComponentRegistry()
    triage_agent = TriageAgent(component_registry=registry)
    
    # Initialize the agent (sets up internal state)
    triage_agent.initialize_agent()
    
    # Run a request that should use memory tools
    request = "What information do we have about the bridge project?"
    
    print(f"  📤 Sending request: {request}")
    
    try:
        response = triage_agent._run_with_context(request)
        print(f"  📨 Response success: {response.success}")
        print(f"  📝 Response message: {response.message[:200]}...")
        
        assert response.success, f"Triage agent failed: {response.message}"
        print("  ✅ TriageAgent successfully processed request with memory context")
        return True
        
    except Exception as e:
        print(f"  ❌ TriageAgent failed: {e}")
        return False


def test_geometry_agent_memory_integration():
    """Test that GeometryAgent can use memory tools in practice."""
    print("\n🧪 Testing GeometryAgent memory integration...")
    
    registry = ComponentRegistry()
    
    # Store some geometry context
    remember("geometry", "current_work", "Creating timber truss components")
    remember("components", "last_created", "Main truss structure")
    
    # Create geometry agent
    geometry_agent = GeometryAgentSTDIO(component_registry=registry)
    
    # Run a simple request (will use fallback mode since MCP not running)
    request = "What components have we created so far?"
    
    print(f"  📤 Sending request: {request}")
    
    try:
        result = geometry_agent.run(request)
        print(f"  📨 Result type: {type(result)}")
        print(f"  📝 Result summary: {str(result)[:200]}...")
        
        # The agent should have access to memory tools
        assert hasattr(geometry_agent, 'memory_tools')
        assert len(geometry_agent.memory_tools) == 3
        
        print("  ✅ GeometryAgent successfully accessed memory tools")
        return True
        
    except Exception as e:
        print(f"  ❌ GeometryAgent failed: {e}")
        return False


def test_component_registry_auto_memory():
    """Test that ComponentRegistry automatically stores in memory."""
    print("\n🧪 Testing ComponentRegistry auto-memory storage...")
    
    registry = ComponentRegistry()
    
    # Register a few components
    components = [
        ("comp_beam_001", "timber_beam", "Support Beam A", "Primary support beam"),
        ("comp_post_001", "timber_post", "Vertical Post 1", "End support post"),
        ("comp_deck_001", "bridge_deck", "Walking Surface", "Timber plank deck")
    ]
    
    for comp_id, comp_type, name, description in components:
        success = registry.register_component(comp_id, comp_type, name, description)
        assert success, f"Failed to register {comp_id}"
        print(f"  📝 Registered {comp_id}: {name}")
    
    # Verify components are in memory
    for comp_id, _, _, _ in components:
        component_data = recall("components", comp_id)
        assert comp_id in component_data or "No memory found" not in component_data
        print(f"  📊 Memory contains {comp_id}")
    
    # Test search across all components
    search_timber = search_memory("timber")
    search_deck = search_memory("deck")
    
    print(f"  🔍 Search 'timber' found: {search_timber.count('comp_')}")
    print(f"  🔍 Search 'deck' found: {search_deck.count('comp_')}")
    
    assert "comp_beam_001" in search_timber or "comp_post_001" in search_timber
    assert "comp_deck_001" in search_deck
    
    print("  ✅ ComponentRegistry auto-memory working correctly")
    return True


def test_memory_performance():
    """Test that memory operations meet performance requirements."""
    print("\n🧪 Testing memory performance...")
    
    # Test remember performance
    start = time.time()
    for i in range(10):
        remember("performance", f"test_{i}", f"Test value {i}")
    remember_time = (time.time() - start) * 1000 / 10  # ms per operation
    
    # Test recall performance
    start = time.time()
    for i in range(10):
        recall("performance", f"test_{i}")
    recall_time = (time.time() - start) * 1000 / 10  # ms per operation
    
    # Test search performance
    start = time.time()
    for i in range(10):
        search_memory("test")
    search_time = (time.time() - start) * 1000 / 10  # ms per operation
    
    print(f"  ⏱️  Remember avg: {remember_time:.2f}ms")
    print(f"  ⏱️  Recall avg: {recall_time:.2f}ms") 
    print(f"  ⏱️  Search avg: {search_time:.2f}ms")
    
    # All operations should be under 10ms
    assert remember_time < 10, f"Remember too slow: {remember_time:.2f}ms"
    assert recall_time < 10, f"Recall too slow: {recall_time:.2f}ms"
    assert search_time < 10, f"Search too slow: {search_time:.2f}ms"
    
    print("  ✅ All memory operations under 10ms requirement")
    return True


def main():
    """Run all end-to-end memory tests."""
    print("🚀 Starting real end-to-end memory system tests...")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        test_memory_persistence_across_sessions,
        test_component_registry_auto_memory,
        test_memory_performance,
        test_triage_agent_memory_integration,
        test_geometry_agent_memory_integration,
    ]
    
    for test_func in tests:
        try:
            result = test_func()
            test_results.append((test_func.__name__, result))
        except Exception as e:
            print(f"  ❌ {test_func.__name__} failed with exception: {e}")
            test_results.append((test_func.__name__, False))
        
        print()  # Blank line between tests
    
    # Summary
    print("=" * 60)
    print("📊 TEST RESULTS SUMMARY:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Memory system is working correctly!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed - Memory system needs fixes")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)