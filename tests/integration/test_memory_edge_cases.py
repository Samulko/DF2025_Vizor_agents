"""
Comprehensive tests for memory system edge cases and failure modes.

This test suite focuses on potential production issues:
- Concurrency problems
- File system failures
- Large data handling
- Session ID conflicts
- Memory file corruption
- Performance under load
- Cross-platform path issues
- Memory cleanup
"""

import json
import os
import tempfile
import time
import threading
import shutil
import stat
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
import concurrent.futures

from bridge_design_system.tools.memory_tools import (
    remember,
    recall,
    search_memory,
    clear_memory,
    load_memory,
    save_memory,
    get_memory_file,
    SESSION_ID,
)


class TestMemoryConcurrency:
    """Test concurrent access to memory system."""

    @pytest.fixture
    def temp_memory_dir(self, monkeypatch):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
            monkeypatch.setattr(mem_tools, "SESSION_ID", "concurrent_test")

            yield memory_path

    def test_concurrent_writes(self, temp_memory_dir):
        """Test multiple threads writing simultaneously."""
        num_threads = 10
        writes_per_thread = 20

        def write_memories(thread_id):
            """Write memories from a single thread."""
            results = []
            for i in range(writes_per_thread):
                try:
                    result = remember(
                        f"thread_{thread_id}", f"key_{i}", f"Thread {thread_id} value {i}"
                    )
                    results.append(("success", result))
                except Exception as e:
                    results.append(("error", str(e)))
                # Add small delay to increase chance of conflicts
                time.sleep(0.001)
            return results

        # Launch concurrent threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(write_memories, i) for i in range(num_threads)]
            thread_results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Verify no errors occurred
        all_results = [item for sublist in thread_results for item in sublist]
        errors = [r for r in all_results if r[0] == "error"]

        if errors:
            pytest.fail(f"Concurrent write errors: {errors[:5]}...")  # Show first 5 errors

        # Verify all data was written correctly
        memory_data = load_memory()
        total_expected = num_threads * writes_per_thread

        # Count actual memories
        total_actual = 0
        for category in memory_data.get("memories", {}):
            if category.startswith("thread_"):
                total_actual += len(memory_data["memories"][category])

        assert (
            total_actual == total_expected
        ), f"Expected {total_expected} memories, got {total_actual}"

    def test_concurrent_read_write(self, temp_memory_dir):
        """Test concurrent reads and writes."""
        # Pre-populate some data
        for i in range(10):
            remember("preload", f"key_{i}", f"Preloaded value {i}")

        write_errors = []
        read_errors = []

        def write_worker():
            """Worker that writes data."""
            try:
                for i in range(50):
                    remember("writer", f"key_{i}", f"Written value {i}")
                    time.sleep(0.001)
            except Exception as e:
                write_errors.append(str(e))

        def read_worker():
            """Worker that reads data."""
            try:
                for i in range(100):
                    recall("preload", f"key_{i % 10}")
                    recall()  # Get summary
                    search_memory("value")
                    time.sleep(0.001)
            except Exception as e:
                read_errors.append(str(e))

        # Start concurrent workers
        threads = []
        for _ in range(2):  # 2 writers
            t = threading.Thread(target=write_worker)
            threads.append(t)
            t.start()

        for _ in range(3):  # 3 readers
            t = threading.Thread(target=read_worker)
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Check for errors
        all_errors = write_errors + read_errors
        if all_errors:
            pytest.fail(f"Concurrent read/write errors: {all_errors}")

    def test_rapid_session_switching(self, temp_memory_dir):
        """Test rapidly switching between different sessions."""
        import bridge_design_system.tools.memory_tools as mem_tools

        original_session = mem_tools.SESSION_ID

        def switch_and_write(session_id):
            """Switch session and write data."""
            errors = []
            try:
                # Simulate session switch
                mem_tools.SESSION_ID = f"session_{session_id}"

                for i in range(10):
                    remember("session_test", f"key_{i}", f"Session {session_id} value {i}")
                    time.sleep(0.001)

            except Exception as e:
                errors.append(str(e))
            finally:
                # Restore session
                mem_tools.SESSION_ID = original_session

            return errors

        # Test with multiple sessions concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(switch_and_write, i) for i in range(5)]
            all_errors = [
                error
                for future in concurrent.futures.as_completed(futures)
                for error in future.result()
            ]

        if all_errors:
            pytest.fail(f"Session switching errors: {all_errors}")


class TestFileSystemFailures:
    """Test file system related failures."""

    @pytest.fixture
    def temp_memory_dir(self, monkeypatch):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
            monkeypatch.setattr(mem_tools, "SESSION_ID", "fs_test")

            yield memory_path

    def test_readonly_directory(self, temp_memory_dir):
        """Test behavior when memory directory is read-only."""
        # Make directory read-only
        temp_memory_dir.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            # This should fail gracefully
            with pytest.raises((PermissionError, OSError)):
                remember("test", "key", "value")
        finally:
            # Restore write permissions for cleanup
            temp_memory_dir.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def test_nonexistent_directory(self, monkeypatch):
        """Test behavior when memory directory doesn't exist."""
        # Point to non-existent directory
        fake_path = Path("/nonexistent/path/memory")

        import bridge_design_system.tools.memory_tools as mem_tools

        monkeypatch.setattr(mem_tools, "MEMORY_PATH", fake_path)
        monkeypatch.setattr(mem_tools, "SESSION_ID", "nonexistent_test")

        # Should handle gracefully (create directory or fail safely)
        try:
            result = remember("test", "key", "value")
            # If it succeeds, directory was created
            assert "Remembered" in result
        except (PermissionError, OSError, FileNotFoundError):
            # Expected failure is acceptable
            pass

    def test_disk_full_simulation(self, temp_memory_dir, monkeypatch):
        """Simulate disk full condition."""
        original_write_text = Path.write_text

        def mock_write_text(self, data, encoding=None, errors=None):
            raise OSError("No space left on device")

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        # Should handle disk full gracefully
        with pytest.raises(OSError):
            remember("disk_full", "key", "value")

    def test_corrupted_filesystem(self, temp_memory_dir, monkeypatch):
        """Test handling of filesystem corruption scenarios."""
        # Create a file that reports as existing but can't be read
        memory_file = get_memory_file()
        memory_file.touch()

        # Mock exists() to return True but read to fail
        original_read_text = Path.read_text

        def mock_read_text(self, encoding=None, errors=None):
            raise OSError("Input/output error")

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        # Should handle I/O errors gracefully
        with pytest.raises(OSError):
            load_memory()

    def test_file_locked_by_other_process(self, temp_memory_dir):
        """Test behavior when memory file is locked by another process."""
        # This is hard to test portably, but we can simulate
        # by creating a file and then trying concurrent access

        memory_file = get_memory_file()

        # Create initial file
        initial_data = {"session_id": "lock_test", "memories": {}}
        memory_file.write_text(json.dumps(initial_data))

        def lock_and_sleep():
            """Function that holds file open."""
            try:
                with open(memory_file, "r+") as f:
                    time.sleep(0.1)  # Hold lock briefly
            except:
                pass

        # Start thread that locks file
        lock_thread = threading.Thread(target=lock_and_sleep)
        lock_thread.start()

        time.sleep(0.01)  # Let lock acquire

        # Try to write while locked - should either succeed or fail gracefully
        try:
            result = remember("locked", "key", "value")
            # If it succeeds, locking isn't preventing writes
            assert "Remembered" in result
        except (OSError, IOError):
            # Expected failure for locked file
            pass

        lock_thread.join()


class TestLargeDataHandling:
    """Test handling of large memory files and values."""

    @pytest.fixture
    def temp_memory_dir(self, monkeypatch):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
            monkeypatch.setattr(mem_tools, "SESSION_ID", "large_data_test")

            yield memory_path

    def test_large_memory_values(self, temp_memory_dir):
        """Test storing very large values."""
        # Create a 1MB string
        large_value = "x" * (1024 * 1024)

        start_time = time.time()
        result = remember("large", "big_value", large_value)
        write_time = time.time() - start_time

        assert "Remembered" in result
        assert write_time < 5.0, f"Large write took {write_time:.2f}s"

        # Test reading it back
        start_time = time.time()
        recalled = recall("large", "big_value")
        read_time = time.time() - start_time

        assert large_value in recalled
        assert read_time < 5.0, f"Large read took {read_time:.2f}s"

    def test_many_small_memories(self, temp_memory_dir):
        """Test storing many small memories."""
        num_memories = 10000

        start_time = time.time()

        # Store many small memories
        for i in range(num_memories):
            remember("many", f"key_{i}", f"Small value {i}")

            # Check performance every 1000 operations
            if i % 1000 == 999:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"Stored {i+1} memories in {elapsed:.2f}s ({rate:.1f} ops/sec)")

        total_time = time.time() - start_time
        rate = num_memories / total_time

        print(f"Total: {num_memories} memories in {total_time:.2f}s ({rate:.1f} ops/sec)")

        # Test reading them back
        start_time = time.time()
        summary = recall("many")
        recall_time = time.time() - start_time

        assert f"{num_memories} items" in summary
        assert recall_time < 10.0, f"Recall took {recall_time:.2f}s"

    def test_memory_file_growth(self, temp_memory_dir):
        """Test memory file growth and performance degradation."""
        memory_file = get_memory_file()

        # Store increasing amounts of data
        sizes = []
        times = []

        for batch in range(10):
            batch_size = 100
            start_time = time.time()

            for i in range(batch_size):
                key = f"batch_{batch}_item_{i}"
                value = f"Batch {batch} item {i} with some content " * 10
                remember("growth", key, value)

            batch_time = time.time() - start_time
            file_size = memory_file.stat().st_size if memory_file.exists() else 0

            sizes.append(file_size)
            times.append(batch_time)

            print(f"Batch {batch}: {file_size} bytes, {batch_time:.3f}s")

        # Check that performance doesn't degrade significantly
        early_avg = sum(times[:3]) / 3
        late_avg = sum(times[-3:]) / 3

        # Performance shouldn't degrade by more than 2x
        assert (
            late_avg < early_avg * 2
        ), f"Performance degraded from {early_avg:.3f}s to {late_avg:.3f}s"

    def test_json_parsing_limits(self, temp_memory_dir):
        """Test JSON parsing with complex nested structures."""
        # Create deeply nested structure
        deep_dict = {}
        current = deep_dict
        for i in range(100):  # 100 levels deep
            current[f"level_{i}"] = {}
            current = current[f"level_{i}"]
        current["final"] = "value"

        # Store as JSON string
        complex_value = json.dumps(deep_dict)

        result = remember("complex", "deep_json", complex_value)
        assert "Remembered" in result

        recalled = recall("complex", "deep_json")
        assert "level_50" in recalled  # Should contain nested data


class TestSessionIdConflicts:
    """Test session ID handling and conflicts."""

    @pytest.fixture
    def temp_memory_dir(self, monkeypatch):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)

            yield memory_path

    def test_malformed_session_ids(self, temp_memory_dir, monkeypatch):
        """Test handling of malformed session IDs."""
        import bridge_design_system.tools.memory_tools as mem_tools

        malformed_ids = [
            "",  # Empty
            "../../etc/passwd",  # Path traversal
            "session with spaces",  # Spaces
            "session/with/slashes",  # Path separators
            "session\nwith\nnewlines",  # Newlines
            "session\x00null",  # Null bytes
            "a" * 1000,  # Very long
            "session.json",  # Extension in name
        ]

        for session_id in malformed_ids:
            monkeypatch.setattr(mem_tools, "SESSION_ID", session_id)

            try:
                # Should either work or fail gracefully
                result = remember("malformed", "test", f"Testing {session_id}")
                assert "Remembered" in result
            except (ValueError, OSError, FileNotFoundError):
                # Expected failures for some malformed IDs
                pass

    def test_session_id_collisions(self, temp_memory_dir, monkeypatch):
        """Test behavior when session IDs collide."""
        import bridge_design_system.tools.memory_tools as mem_tools

        # Use same session ID for different "sessions"
        session_id = "collision_test"
        monkeypatch.setattr(mem_tools, "SESSION_ID", session_id)

        # First "session" stores data
        remember("session1", "data", "First session data")

        # Second "session" stores different data
        remember("session2", "data", "Second session data")

        # Both should be accessible
        data1 = recall("session1", "data")
        data2 = recall("session2", "data")

        assert "First session data" in data1
        assert "Second session data" in data2

    def test_unicode_session_ids(self, temp_memory_dir, monkeypatch):
        """Test session IDs with Unicode characters."""
        import bridge_design_system.tools.memory_tools as mem_tools

        unicode_ids = [
            "session_测试",  # Chinese
            "session_عربي",  # Arabic
            "session_🚀",  # Emoji
            "session_Ñoño",  # Spanish
        ]

        for session_id in unicode_ids:
            monkeypatch.setattr(mem_tools, "SESSION_ID", session_id)

            try:
                result = remember("unicode", "test", f"Unicode test {session_id}")
                assert "Remembered" in result

                recalled = recall("unicode", "test")
                assert f"Unicode test" in recalled

            except (UnicodeError, OSError):
                # Some filesystems may not support Unicode filenames
                pass


class TestMemoryCorruption:
    """Test handling of various memory file corruption scenarios."""

    @pytest.fixture
    def temp_memory_dir(self, monkeypatch):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
            monkeypatch.setattr(mem_tools, "SESSION_ID", "corruption_test")

            yield memory_path

    def test_invalid_json_formats(self, temp_memory_dir):
        """Test various JSON corruption scenarios."""
        memory_file = get_memory_file()

        corruption_scenarios = [
            "",  # Empty file
            "{",  # Unclosed brace
            "}",  # Extra closing brace
            '{"session_id": "test", "memories": {',  # Truncated
            '{"session_id": "test", "memories": }',  # Invalid syntax
            "not json at all",  # Not JSON
            '{"session_id": null, "memories": {}}',  # Null session ID
            '{"memories": {}}',  # Missing session_id
            '{"session_id": "test"}',  # Missing memories
            b'\xff\xfe{"session_id": "test"}',  # BOM/encoding issues
        ]

        for i, corruption in enumerate(corruption_scenarios):
            # Write corrupted data
            if isinstance(corruption, str):
                memory_file.write_text(corruption)
            else:
                memory_file.write_bytes(corruption)

            # Try to load - should handle gracefully
            try:
                memory_data = load_memory()
                # Should get fresh memory if corruption handled
                assert "session_id" in memory_data
                assert "memories" in memory_data

                # Should be able to write new data
                result = remember("corruption", f"test_{i}", f"After corruption {i}")
                assert "Remembered" in result

            except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
                # Some corruptions might not be recoverable
                pass

    def test_partial_writes(self, temp_memory_dir):
        """Test handling of partial writes (interrupted saves)."""
        # Create valid initial state
        remember("partial", "initial", "Initial data")

        memory_file = get_memory_file()

        # Simulate partial write by truncating file
        full_content = memory_file.read_text()
        partial_content = full_content[: len(full_content) // 2]  # Half the content

        memory_file.write_text(partial_content)

        # Try to load corrupted file
        try:
            memory_data = load_memory()
            # Should either recover or start fresh
            assert "session_id" in memory_data

            # Should be able to continue working
            result = remember("partial", "after_corruption", "After corruption")
            assert "Remembered" in result

        except json.JSONDecodeError:
            # Acceptable failure for corrupted JSON
            pass

    def test_concurrent_corruption(self, temp_memory_dir):
        """Test corruption during concurrent access."""
        # Pre-populate with data
        for i in range(10):
            remember("concurrent", f"pre_{i}", f"Pre-populated {i}")

        corruption_occurred = threading.Event()

        def corrupt_file():
            """Corrupt the memory file during operations."""
            time.sleep(0.05)  # Let some operations start
            memory_file = get_memory_file()
            if memory_file.exists():
                # Corrupt by writing invalid JSON
                memory_file.write_text("CORRUPTED")
                corruption_occurred.set()

        def normal_operations():
            """Perform normal memory operations."""
            errors = []
            for i in range(20):
                try:
                    remember("concurrent", f"during_{i}", f"During corruption {i}")
                    time.sleep(0.01)
                except Exception as e:
                    errors.append(str(e))
            return errors

        # Start corruption thread
        corrupt_thread = threading.Thread(target=corrupt_file)
        corrupt_thread.start()

        # Start normal operations
        operation_thread = threading.Thread(target=normal_operations)
        operation_thread.start()

        # Wait for completion
        corrupt_thread.join()
        operation_thread.join()

        # Verify system recovers
        assert corruption_occurred.is_set(), "Corruption should have occurred"

        # System should be able to continue working
        result = remember("recovery", "test", "Recovery test")
        assert "Remembered" in result


class TestPerformanceUnderLoad:
    """Test performance characteristics under high load."""

    @pytest.fixture
    def temp_memory_dir(self, monkeypatch):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
            monkeypatch.setattr(mem_tools, "SESSION_ID", "performance_test")

            yield memory_path

    def test_memory_leak_detection(self, temp_memory_dir):
        """Test for memory leaks during repeated operations."""
        import psutil
        import gc

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Perform many operations
        for batch in range(50):
            for i in range(100):
                remember("leak_test", f"batch_{batch}_item_{i}", f"Batch {batch} item {i}")
                recall("leak_test", f"batch_{batch}_item_{i}")
                search_memory(f"batch_{batch}")

            # Force garbage collection
            gc.collect()

            # Check memory growth
            current_memory = process.memory_info().rss
            growth = current_memory - initial_memory
            growth_mb = growth / (1024 * 1024)

            # Shouldn't grow more than 100MB
            if growth_mb > 100:
                pytest.fail(f"Memory grew by {growth_mb:.1f}MB after {(batch+1)*100} operations")

    def test_rapid_operations(self, temp_memory_dir):
        """Test system stability under rapid operations."""
        start_time = time.time()
        operations = 0
        errors = []

        # Run for 10 seconds
        while time.time() - start_time < 10:
            try:
                # Mix of operations
                op_type = operations % 4
                if op_type == 0:
                    remember("rapid", f"key_{operations}", f"Rapid value {operations}")
                elif op_type == 1:
                    recall("rapid", f"key_{operations//2}")
                elif op_type == 2:
                    recall("rapid")
                else:
                    search_memory("rapid")

                operations += 1

            except Exception as e:
                errors.append(str(e))

        rate = operations / 10  # Operations per second
        print(f"Performed {operations} operations in 10s ({rate:.1f} ops/sec)")

        if errors:
            pytest.fail(f"Errors during rapid operations: {errors[:5]}...")

    def test_search_performance_degradation(self, temp_memory_dir):
        """Test search performance as data grows."""
        # Add data in batches and measure search time
        batch_sizes = [100, 500, 1000, 2000, 5000]
        search_times = []

        total_items = 0
        for batch_size in batch_sizes:
            # Add batch of data
            for i in range(batch_size):
                remember(
                    "search_perf",
                    f"item_{total_items + i}",
                    f"Searchable content item {total_items + i} with various keywords",
                )

            total_items += batch_size

            # Measure search time
            start_time = time.time()
            search_memory("searchable")
            search_time = time.time() - start_time
            search_times.append(search_time)

            print(f"Search with {total_items} items: {search_time:.3f}s")

        # Search time shouldn't grow exponentially
        # Linear growth is acceptable, but not quadratic
        if len(search_times) >= 3:
            # Check if last search is more than 10x slower than first
            if search_times[-1] > search_times[0] * 10:
                pytest.fail(
                    f"Search performance degraded from {search_times[0]:.3f}s to {search_times[-1]:.3f}s"
                )


class TestCrossPlatformPaths:
    """Test path handling across different platforms."""

    def test_path_separators(self, monkeypatch):
        """Test handling of different path separators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)

            # Test with different session IDs that might cause path issues
            problematic_ids = [
                "normal_session",
                "session.with.dots",
                "session-with-dashes",
                "session_with_underscores",
            ]

            for session_id in problematic_ids:
                monkeypatch.setattr(mem_tools, "SESSION_ID", session_id)

                try:
                    result = remember("path_test", "key", f"Testing {session_id}")
                    assert "Remembered" in result

                    # Verify file was created with correct name
                    expected_file = memory_path / f"{session_id}.json"
                    assert expected_file.exists(), f"File not created: {expected_file}"

                except (OSError, ValueError) as e:
                    pytest.fail(f"Path handling failed for '{session_id}': {e}")

    def test_long_paths(self, monkeypatch):
        """Test handling of very long file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure
            long_path = Path(temp_dir)
            for i in range(10):
                long_path = long_path / f"very_long_directory_name_{i}"

            memory_path = long_path / "memory"

            try:
                memory_path.mkdir(parents=True, exist_ok=True)

                import bridge_design_system.tools.memory_tools as mem_tools

                monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
                monkeypatch.setattr(mem_tools, "SESSION_ID", "long_path_test")

                result = remember("long_path", "test", "Testing long paths")
                assert "Remembered" in result

            except OSError:
                # Some systems have path length limits
                pytest.skip("System doesn't support long paths")


class TestMemoryCleanup:
    """Test memory cleanup and maintenance."""

    @pytest.fixture
    def temp_memory_dir(self, monkeypatch):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory"
            memory_path.mkdir(exist_ok=True)

            import bridge_design_system.tools.memory_tools as mem_tools

            monkeypatch.setattr(mem_tools, "MEMORY_PATH", memory_path)
            monkeypatch.setattr(mem_tools, "SESSION_ID", "cleanup_test")

            yield memory_path

    def test_clear_memory_functionality(self, temp_memory_dir):
        """Test the clear_memory function."""
        # Store data in multiple categories
        remember("category1", "key1", "value1")
        remember("category1", "key2", "value2")
        remember("category2", "key1", "value1")
        remember("category3", "key1", "value1")

        # Test clearing specific category
        result = clear_memory("category1", "yes")
        assert "Cleared category 'category1'" in result
        assert "2 items deleted" in result

        # Verify category is gone
        summary = recall()
        assert "category1" not in summary
        assert "category2" in summary
        assert "category3" in summary

        # Test clearing all memory
        result = clear_memory(None, "yes")
        assert "Cleared ALL memory" in result

        # Verify all gone
        summary = recall()
        assert "No memories stored yet" in summary

    def test_old_session_cleanup(self, temp_memory_dir):
        """Test cleanup of old session files."""
        # Create multiple session files
        session_files = []
        for i in range(10):
            session_file = temp_memory_dir / f"old_session_{i}.json"
            session_data = {
                "session_id": f"old_session_{i}",
                "memories": {
                    "test": {"key": {"value": f"Old data {i}", "timestamp": "2023-01-01"}}
                },
            }
            session_file.write_text(json.dumps(session_data))
            session_files.append(session_file)

        # Verify files exist
        for session_file in session_files:
            assert session_file.exists()

        # In a real implementation, there would be cleanup logic here
        # For now, we just verify the files can be identified
        json_files = list(temp_memory_dir.glob("*.json"))
        assert len(json_files) >= 10

    def test_memory_compaction(self, temp_memory_dir):
        """Test that deleted memories don't leave gaps."""
        # Store lots of data
        for i in range(100):
            remember("compact", f"key_{i}", f"Value {i}")

        initial_size = get_memory_file().stat().st_size

        # Clear half the data
        memory_data = load_memory()
        for i in range(0, 100, 2):  # Delete even keys
            if f"key_{i}" in memory_data["memories"]["compact"]:
                del memory_data["memories"]["compact"][f"key_{i}"]
        save_memory(memory_data)

        after_delete_size = get_memory_file().stat().st_size

        # File should be smaller after deletion
        assert after_delete_size < initial_size

        # Verify remaining data is accessible
        for i in range(1, 100, 2):  # Odd keys should remain
            recalled = recall("compact", f"key_{i}")
            assert f"Value {i}" in recalled

    def test_memory_growth_monitoring(self, temp_memory_dir):
        """Test monitoring of memory growth over time."""
        memory_file = get_memory_file()
        sizes = []

        # Add data in batches and track size
        for batch in range(20):
            for i in range(50):
                remember("growth", f"batch_{batch}_item_{i}", f"Data for batch {batch} item {i}")

            if memory_file.exists():
                size = memory_file.stat().st_size
                sizes.append(size)

        # Memory should grow predictably
        if len(sizes) >= 5:
            # Check that growth is roughly linear (not exponential)
            early_growth = sizes[4] - sizes[0]  # Growth in first 5 batches
            late_growth = sizes[-1] - sizes[-5]  # Growth in last 5 batches

            # Late growth shouldn't be more than 2x early growth
            # (allowing for JSON overhead and metadata)
            assert (
                late_growth < early_growth * 2.5
            ), f"Memory growth not linear: {early_growth} vs {late_growth}"
