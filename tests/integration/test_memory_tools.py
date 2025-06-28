"""Tests for memory tools functionality."""

import json
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime
import pytest

from bridge_design_system.tools.memory_tools import (
    remember,
    recall,
    search_memory,
    remember_component,
    load_memory,
    save_memory,
    get_memory_file,
)


@pytest.fixture
def temp_memory_dir(monkeypatch):
    """Create a temporary directory for memory storage during tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override the MEMORY_PATH
        memory_path = Path(temp_dir) / "memory"
        memory_path.mkdir(exist_ok=True)

        # Patch the module-level variables
        import bridge_design_system.tools.memory_tools as mem_tools

        monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
        monkeypatch.setattr(mem_tools, "SESSION_ID", "test_session")

        yield memory_path


class TestMemoryTools:
    """Test suite for memory tools."""

    def test_remember_and_recall(self, temp_memory_dir):
        """Test basic remember and recall functionality."""
        # Remember something
        result = remember("components", "test_comp", "A test component")
        assert "Remembered" in result
        assert "components" in result
        assert "test_comp" in result

        # Recall it
        recalled = recall("components", "test_comp")
        assert "A test component" in recalled
        assert "Stored at:" in recalled

    def test_recall_all_categories(self, temp_memory_dir):
        """Test recalling all categories."""
        # Store memories in different categories
        remember("components", "comp1", "Component 1")
        remember("context", "goal", "Build a bridge")
        remember("errors", "err1", "Connection failed")

        # Recall all
        summary = recall()
        assert "Memory categories available" in summary
        assert "components: 1 items" in summary
        assert "context: 1 items" in summary
        assert "errors: 1 items" in summary

    def test_recall_category(self, temp_memory_dir):
        """Test recalling all items in a category."""
        # Store multiple components
        remember("components", "comp1", "First component")
        remember("components", "comp2", "Second component")

        # Recall category
        result = recall("components")
        assert "Memories in category 'components'" in result
        assert "comp1" in result
        assert "First component" in result
        assert "comp2" in result
        assert "Second component" in result

    def test_recall_nonexistent(self, temp_memory_dir):
        """Test recalling non-existent memories."""
        # Empty memory
        result = recall()
        assert "No memories stored yet" in result

        # Non-existent category
        result = recall("nonexistent")
        assert "No memories found in category 'nonexistent'" in result

        # Non-existent key
        remember("components", "comp1", "Component 1")
        result = recall("components", "nonexistent_key")
        assert "No memory found for key 'nonexistent_key'" in result

    def test_search_memory(self, temp_memory_dir):
        """Test memory search functionality."""
        # Store various memories
        remember("components", "timber_truss", "Main timber truss component")
        remember("components", "steel_beam", "Support steel beam")
        remember("context", "material", "Using timber for sustainability")
        remember("decisions", "choice", "Chose timber over steel")

        # Search for "timber"
        results = search_memory("timber")
        assert "Found" in results
        assert "timber_truss" in results
        assert "Main timber truss component" in results
        assert "Using timber for sustainability" in results

        # Search with limit
        results = search_memory("timber", limit=1)
        lines = results.split("\n")
        # Should only have 1 result
        assert "1." in results
        assert "2." not in results

    def test_search_case_insensitive(self, temp_memory_dir):
        """Test that search is case-insensitive."""
        remember("components", "test", "UPPERCASE content")

        # Search with lowercase
        results = search_memory("uppercase")
        assert "UPPERCASE content" in results

        # Search with mixed case
        results = search_memory("UpPeRcAsE")
        assert "UPPERCASE content" in results

    def test_search_no_results(self, temp_memory_dir):
        """Test search with no matching results."""
        remember("components", "comp1", "Component 1")

        results = search_memory("nonexistent")
        assert "No memories found matching 'nonexistent'" in results

    def test_performance(self, temp_memory_dir):
        """Test that operations complete within 10ms."""
        # Store some data first
        for i in range(10):
            remember("components", f"comp_{i}", f"Component {i}")

        # Test remember performance
        start = time.time()
        remember("test", "perf", "Performance test")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 10, f"remember took {elapsed:.2f}ms"

        # Test recall performance
        start = time.time()
        recall("components", "comp_5")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 10, f"recall took {elapsed:.2f}ms"

        # Test search performance
        start = time.time()
        search_memory("Component")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 10, f"search took {elapsed:.2f}ms"

    def test_remember_component_helper(self, temp_memory_dir):
        """Test the component registry helper function."""
        # Use the helper
        remember_component("comp_123", "timber_truss", "Main bridge truss")

        # Verify it was stored correctly
        recalled = recall("components", "comp_123")
        assert "Type: timber_truss" in recalled
        assert "Description: Main bridge truss" in recalled
        assert "Created:" in recalled

    def test_corrupted_memory_file(self, temp_memory_dir):
        """Test handling of corrupted memory files."""
        # Write corrupted JSON
        memory_file = get_memory_file()
        memory_file.write_text("{ corrupted json file")

        # Should handle gracefully
        result = remember("test", "key", "value")
        assert "Remembered" in result

        # Should be able to recall
        recalled = recall("test", "key")
        assert "value" in recalled

    def test_memory_persistence(self, temp_memory_dir):
        """Test that memories persist across function calls."""
        # Store memory
        remember("persist", "test1", "First value")

        # Clear any in-memory cache by loading again
        memory1 = load_memory()

        # Store another
        remember("persist", "test2", "Second value")

        # Load and verify both exist
        memory2 = load_memory()
        assert "test1" in memory2["memories"]["persist"]
        assert "test2" in memory2["memories"]["persist"]

    def test_session_id_handling(self, temp_memory_dir):
        """Test session ID management."""
        # Current session ID should be 'test_session' (from fixture)
        memory_data = load_memory()
        assert memory_data["session_id"] == "test_session"

        # Save something to create the file
        remember("test", "key", "value")

        # File should be named correctly
        expected_file = temp_memory_dir / "test_session.json"
        assert expected_file.exists()

    def test_empty_values(self, temp_memory_dir):
        """Test handling of empty values."""
        # Empty value should still work
        result = remember("test", "empty", "")
        assert "Remembered" in result

        recalled = recall("test", "empty")
        assert recalled.strip().endswith("ms)")  # Just has metadata

    def test_special_characters(self, temp_memory_dir):
        """Test handling of special characters in keys and values."""
        # Special characters in key and value
        special_key = "comp/2024-12-14@15:30"
        special_value = "Component with \"quotes\" and 'apostrophes' and \n newlines"

        remember("special", special_key, special_value)
        recalled = recall("special", special_key)

        assert special_value in recalled
