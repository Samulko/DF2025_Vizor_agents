"""
Core Memory Logic Tests - Realistic Validation Approach

Tests memory tools and component tracking with deterministic data.
This tests the 40% we can actually validate - system logic, not full use case.

Based on current_task.md honest assessment.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os
import time

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from bridge_design_system.tools.memory_tools import (
    remember,
    recall,
    search_memory,
    clear_memory,
    load_memory,
)
from bridge_design_system.state.component_registry import ComponentRegistry, ComponentInfo


class TestMemoryToolFunctionality:
    """Test memory tools work correctly with known data."""

    def setup_method(self):
        """Setup for each test - clean memory state."""
        # Clear any existing memory for clean test state
        clear_memory(None, "yes")  # Clear all memory
        time.sleep(0.1)  # Brief pause for file operations

    def test_memory_tools_basic_functionality(self):
        """Test that memory tools function correctly with known data."""

        # Simulate a known component being created
        mock_component = {
            "id": "test_curve_001",
            "type": "curve",
            "description": "bridge arch curve",
            "timestamp": "2024-12-16T10:00:00",
        }

        # Test memory storage
        result = remember(
            "components",
            "test_curve_001",
            f"Type: {mock_component['type']}, Description: {mock_component['description']}",
        )
        assert "Remembered" in result
        assert "components" in result
        assert "test_curve_001" in result

        # Test memory retrieval
        retrieved = recall("components", "test_curve_001")
        assert "curve" in retrieved
        assert "bridge arch curve" in retrieved

        # Test component is findable
        search_result = search_memory("curve")
        assert "test_curve_001" in search_result
        assert "bridge arch curve" in search_result

    def test_memory_persistence_across_operations(self):
        """Test memory persists across multiple operations."""

        # Store multiple components
        components = [
            {"id": "beam_001", "type": "beam", "desc": "main support beam"},
            {"id": "post_001", "type": "post", "desc": "vertical support post"},
            {"id": "truss_001", "type": "truss", "desc": "triangular truss structure"},
        ]

        # Store all components
        for comp in components:
            result = remember(
                "components", comp["id"], f"Type: {comp['type']}, Description: {comp['desc']}"
            )
            assert "Remembered" in result

        # Verify all components are retrievable
        for comp in components:
            retrieved = recall("components", comp["id"])
            assert comp["type"] in retrieved
            assert comp["desc"] in retrieved

        # Test category recall shows all components
        all_components = recall("components")
        for comp in components:
            assert comp["id"] in all_components

    def test_vague_reference_context_storage(self):
        """Test storing context that enables vague reference resolution."""

        # Store recent action context
        remember("context", "last_action", "created bridge curve with ID curve_123")
        remember("context", "current_project", "pedestrian bridge design")
        remember("context", "user_intent", "modify the curve you just drew")

        # Store component details for resolution
        remember(
            "components",
            "curve_123",
            "Type: curve, Description: bridge arch curve, Status: recently_created",
        )

        # Test context is retrievable
        last_action = recall("context", "last_action")
        assert "curve_123" in last_action
        assert "created" in last_action

        # Test search can find related context
        curve_context = search_memory("curve")
        assert "curve_123" in curve_context
        assert "bridge arch" in curve_context

        user_intent = recall("context", "user_intent")
        assert "modify" in user_intent
        assert "just drew" in user_intent

    def test_memory_categories_work_correctly(self):
        """Test different memory categories function correctly."""

        categories_test_data = {
            "components": {"main_beam": "Type: beam, Length: 20m, Material: timber"},
            "context": {"project_goal": "Design pedestrian bridge with 30m span"},
            "decisions": {"material_choice": "Selected timber for sustainability"},
            "errors": {"last_error": "Component connection failed - joint too weak"},
            "tools": {"active_tool": "Grasshopper Python3 script component"},
        }

        # Store data in different categories
        for category, data in categories_test_data.items():
            for key, value in data.items():
                result = remember(category, key, value)
                assert "Remembered" in result
                assert category in result

        # Verify each category works independently
        for category, data in categories_test_data.items():
            for key, expected_value in data.items():
                retrieved = recall(category, key)
                # Check that key content appears in retrieved value
                assert any(
                    word in retrieved for word in expected_value.split()[:3]
                )  # Check first 3 words

        # Test category listing
        summary = recall()
        for category in categories_test_data.keys():
            assert category in summary

    def test_memory_search_functionality(self):
        """Test memory search works with known patterns."""

        # Create searchable memory entries
        test_memories = [
            ("components", "beam_main", "Primary timber beam for bridge span"),
            ("components", "beam_secondary", "Secondary support beam"),
            ("context", "bridge_type", "Timber truss bridge design"),
            ("decisions", "beam_sizing", "Beam depth: 400mm for adequate strength"),
            ("tools", "beam_generator", "Python script to generate beam geometry"),
        ]

        # Store all memories
        for category, key, value in test_memories:
            remember(category, key, value)

        # Test search finds relevant items
        beam_results = search_memory("beam")
        assert "beam_main" in beam_results
        assert "beam_secondary" in beam_results
        assert "beam_sizing" in beam_results
        assert "beam_generator" in beam_results

        # Test search with different terms
        timber_results = search_memory("timber")
        assert "beam_main" in timber_results or "bridge_type" in timber_results

        # Test search limits work
        limited_results = search_memory("beam", limit=2)
        # Should contain beam references but be limited
        assert "beam" in limited_results.lower()
        lines = limited_results.split("\n")
        result_lines = [
            line
            for line in lines
            if line.strip() and not line.startswith("Found") and not line.startswith("(Search")
        ]
        assert len(result_lines) <= 6  # Max 2 results * ~3 lines each


class TestComponentRegistryLogic:
    """Test component registry works with deterministic data."""

    def setup_method(self):
        """Setup clean registry for each test."""
        self.registry = ComponentRegistry()

    def test_component_registration_and_retrieval(self):
        """Test component registration and retrieval logic."""

        # Register a known component
        success = self.registry.register_component(
            component_id="test_curve_001",
            component_type="curve",
            name="Bridge Arch Curve",
            description="Main arch curve for pedestrian bridge",
            properties={"material": "virtual", "span": "10m"},
        )

        assert success == True

        # Retrieve the component
        component = self.registry.get_component("test_curve_001")
        assert component is not None
        assert component.id == "test_curve_001"
        assert component.type == "curve"
        assert component.name == "Bridge Arch Curve"
        assert component.description == "Main arch curve for pedestrian bridge"
        assert component.properties["span"] == "10m"

    def test_vague_reference_resolution_logic(self):
        """Test vague reference resolution with known components."""

        # Set up known conversation state with registered components
        components = [
            {
                "id": "curve_001",
                "type": "curve",
                "name": "Bridge Arch",
                "description": "main bridge arch",
            },
            {
                "id": "support_001",
                "type": "support",
                "name": "Steel Beam",
                "description": "vertical support beam",
            },
            {
                "id": "bridge_001",
                "type": "bridge_structure",
                "name": "Main Bridge",
                "description": "complete bridge structure",
            },
        ]

        # Register all components
        for comp in components:
            self.registry.register_component(
                comp["id"], comp["type"], comp["name"], comp["description"]
            )

        # Test vague reference resolution
        test_references = [
            ("the curve", ["curve_001"]),  # Should resolve to curve
            ("it", ["bridge_001"]),  # Should resolve to most recent (bridge)
            ("that", ["bridge_001"]),  # Should resolve to most recent
            ("the bridge", ["bridge_001"]),  # Should find bridge component
            ("all", 3),  # Should return multiple components
        ]

        for vague_ref, expected in test_references:
            resolved = self.registry.resolve_reference(vague_ref)

            if isinstance(expected, list):
                # Check specific resolution
                assert len(resolved) > 0, f"No resolution for '{vague_ref}'"
                if expected:  # If we expect specific IDs
                    assert any(
                        exp_id in resolved for exp_id in expected
                    ), f"Expected {expected} in resolution for '{vague_ref}', got {resolved}"
            else:
                # Check count (for "all")
                assert (
                    len(resolved) == expected
                ), f"Expected {expected} components for '{vague_ref}', got {len(resolved)}"

    def test_component_type_search(self):
        """Test finding components by type."""

        # Register components of different types
        test_components = [
            ("beam_001", "beam", "Main Beam"),
            ("beam_002", "beam", "Support Beam"),
            ("post_001", "post", "Corner Post"),
            ("curve_001", "curve", "Arch Curve"),
            ("curve_002", "curve", "Guide Curve"),
        ]

        for comp_id, comp_type, name in test_components:
            self.registry.register_component(comp_id, comp_type, name, f"Test {name}")

        # Test type-based search
        beams = self.registry.find_by_type("beam")
        assert len(beams) == 2
        assert "beam_001" in beams
        assert "beam_002" in beams

        curves = self.registry.find_by_type("curve")
        assert len(curves) == 2
        assert "curve_001" in curves
        assert "curve_002" in curves

        posts = self.registry.find_by_type("post")
        assert len(posts) == 1
        assert "post_001" in posts

    def test_recent_component_tracking(self):
        """Test recent component tracking logic."""

        # Register components in sequence
        components = [
            ("comp_001", "beam", "First Component"),
            ("comp_002", "post", "Second Component"),
            ("comp_003", "curve", "Third Component"),
        ]

        for comp_id, comp_type, name in components:
            self.registry.register_component(comp_id, comp_type, name, f"Test {name}")
            time.sleep(0.01)  # Small delay to ensure ordering

        # Test recent tracking
        recent = self.registry.find_recent(limit=3)
        assert len(recent) == 3
        assert recent[0] == "comp_003"  # Most recent first
        assert recent[1] == "comp_002"
        assert recent[2] == "comp_001"

        # Test "it" resolution to most recent
        it_resolved = self.registry.resolve_reference("it")
        assert len(it_resolved) > 0
        assert it_resolved[0] == "comp_003"  # Should be most recent


class TestCrossAgentMemorySync:
    """Test memory synchronization logic between components."""

    def test_memory_and_registry_coordination(self):
        """Test that memory tools and component registry work together."""

        # Create registry and add component
        registry = ComponentRegistry()

        # Register component (this should also store in memory via remember_component)
        success = registry.register_component(
            "bridge_001", "bridge", "Main Bridge", "Primary bridge structure"
        )
        assert success

        # Component should be findable in registry
        component = registry.get_component("bridge_001")
        assert component is not None

        # Should also be searchable in memory (due to remember_component integration)
        memory_search = search_memory("bridge_001")
        assert "bridge_001" in memory_search or "bridge" in memory_search

        # Test that context can reference the component
        remember("context", "current_focus", "Working on bridge_001 - the main bridge structure")

        context = recall("context", "current_focus")
        assert "bridge_001" in context

        # Test that both systems see the component
        registry_result = registry.resolve_reference("the bridge")
        assert len(registry_result) > 0
        assert "bridge_001" in registry_result

    def test_conversation_state_persistence(self):
        """Test conversation state persists correctly."""

        # Simulate conversation state across operations
        conversation_steps = [
            ("user_request", "Create a bridge arch"),
            ("system_action", "Created curve component curve_123"),
            ("user_request", "Modify the curve you just drew"),
            ("system_context", "Resolving 'the curve' to curve_123"),
            ("system_action", "Modified curve_123 - increased arch height"),
        ]

        # Store conversation steps
        for i, (step_type, content) in enumerate(conversation_steps):
            remember("conversation", f"step_{i:02d}_{step_type}", content)

        # Verify conversation state is complete
        for i, (step_type, expected_content) in enumerate(conversation_steps):
            retrieved = recall("conversation", f"step_{i:02d}_{step_type}")
            # Check that key words from expected content are present
            key_words = expected_content.split()[:3]  # First 3 words
            assert any(word in retrieved for word in key_words)

        # Test conversation search
        curve_conversation = search_memory("curve")
        assert "curve_123" in curve_conversation
        assert "arch" in curve_conversation.lower()

        modify_conversation = search_memory("modify")
        assert "curve" in modify_conversation.lower()


class TestErrorHandling:
    """Test system behavior under error conditions."""

    def test_memory_tool_error_handling(self):
        """Test memory tools handle errors gracefully."""

        # Test recall of non-existent category
        result = recall("nonexistent_category")
        assert "No memories found" in result

        # Test recall of non-existent key
        result = recall("components", "nonexistent_key")
        assert "No memory found" in result

        # Test search with no results
        result = search_memory("completely_unique_term_12345")
        assert "No memories found" in result

    def test_component_registry_error_handling(self):
        """Test registry handles errors gracefully."""

        registry = ComponentRegistry()

        # Test get non-existent component
        component = registry.get_component("nonexistent_id")
        assert component is None

        # Test resolve invalid reference
        resolved = registry.resolve_reference("nonexistent reference pattern")
        assert isinstance(resolved, list)  # Should return empty list, not crash

        # Test find by non-existent type
        found = registry.find_by_type("nonexistent_type")
        assert isinstance(found, list)
        assert len(found) == 0

    def test_duplicate_component_handling(self):
        """Test handling of duplicate component registration."""

        registry = ComponentRegistry()

        # Register component
        success1 = registry.register_component(
            "test_001", "beam", "Test Beam", "First registration"
        )
        assert success1 == True

        # Try to register same ID again
        success2 = registry.register_component(
            "test_001", "post", "Test Post", "Second registration"
        )
        assert success2 == False  # Should fail

        # Original component should be unchanged
        component = registry.get_component("test_001")
        assert component.type == "beam"  # Should still be beam, not post
        assert component.name == "Test Beam"


if __name__ == "__main__":
    """Run the realistic core memory logic tests."""
    print("🧪 REALISTIC VALIDATION: Core Memory Logic Tests")
    print("Testing the 40% we can actually validate with deterministic data")
    print("=" * 70)

    # Run tests manually for immediate feedback
    test_classes = [
        TestMemoryToolFunctionality,
        TestComponentRegistryLogic,
        TestCrossAgentMemorySync,
        TestErrorHandling,
    ]

    total_tests = 0
    passed_tests = 0

    for test_class in test_classes:
        print(f"\n📋 Testing: {test_class.__name__}")
        print("-" * 50)

        test_instance = test_class()

        # Get test methods
        test_methods = [method for method in dir(test_instance) if method.startswith("test_")]

        for test_method_name in test_methods:
            total_tests += 1
            try:
                # Setup if exists
                if hasattr(test_instance, "setup_method"):
                    test_instance.setup_method()

                # Run test
                test_method = getattr(test_instance, test_method_name)
                test_method()

                print(f"  ✅ {test_method_name}")
                passed_tests += 1

            except Exception as e:
                print(f"  ❌ {test_method_name}: {e}")

    print("\n" + "=" * 70)
    print(f"🎯 REALISTIC MEMORY VALIDATION RESULTS:")
    print(f"  Tests passed: {passed_tests}/{total_tests}")
    print(
        f"  Success rate: {passed_tests/total_tests*100:.1f}%"
        if total_tests > 0
        else "  No tests run"
    )
    print(f"  Coverage: Memory tools, Component registry, Cross-system sync, Error handling")
    print("=" * 70)

    if passed_tests == total_tests:
        print("✅ CORE MEMORY LOGIC: All tests passed")
        print("✅ Memory tools work correctly with deterministic data")
        print("✅ Component tracking and retrieval functional")
        print("✅ Vague reference resolution logic works")
        print("✅ Cross-agent memory synchronization functional")
    else:
        print("❌ CORE MEMORY LOGIC: Some tests failed")
        print("❌ Memory synchronization has logical issues")

    print("\n💡 What this validates:")
    print("  - Memory tool functionality (store/retrieve/search)")
    print("  - Component registry logic (register/resolve/track)")
    print("  - Vague reference resolution algorithms")
    print("  - System coordination between memory components")
    print("  - Error handling and edge cases")
    print("\n💡 What this does NOT validate:")
    print("  - Real AI understanding of vague references")
    print("  - Real geometry creation in Grasshopper")
    print("  - Real user experience and workflows")
    print("  - Production performance and reliability")
    print("\n🎯 This is honest testing - 40% validation of testable components")
