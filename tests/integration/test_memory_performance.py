"""
Test memory system performance characteristics.
"""

import tempfile
import time
from pathlib import Path
import psutil
import os

from bridge_design_system.tools.memory_tools import remember, recall, search_memory


def test_memory_performance():
    """Test performance degradation with large datasets."""

    with tempfile.TemporaryDirectory() as temp_dir:
        memory_path = Path(temp_dir) / "memory"
        memory_path.mkdir(exist_ok=True)

        # Patch the memory tools
        import bridge_design_system.tools.memory_tools as mem_tools

        original_memory_path = mem_tools.MEMORY_PATH
        original_session_id = mem_tools.SESSION_ID

        try:
            mem_tools.MEMORY_PATH = memory_path
            mem_tools.SESSION_ID = "perf_test"

            # Test performance at different scales
            scales = [100, 500, 1000, 2000]
            times = []
            file_sizes = []

            for scale in scales:
                print(f"\n=== Testing scale: {scale} memories ===")

                # Add memories
                start_time = time.time()
                for i in range(scale):
                    remember("perf", f"key_{i}", f"Performance test value {i} with some content")
                write_time = time.time() - start_time

                # Measure file size
                memory_file = mem_tools.get_memory_file()
                file_size = memory_file.stat().st_size if memory_file.exists() else 0

                # Test search performance
                start_time = time.time()
                search_memory("performance")
                search_time = time.time() - start_time

                # Test recall performance
                start_time = time.time()
                recall("perf")
                recall_time = time.time() - start_time

                times.append(
                    {
                        "scale": scale,
                        "write_time": write_time,
                        "search_time": search_time,
                        "recall_time": recall_time,
                    }
                )
                file_sizes.append(file_size)

                print(f"Write time: {write_time:.3f}s ({scale/write_time:.1f} ops/sec)")
                print(f"Search time: {search_time:.3f}s")
                print(f"Recall time: {recall_time:.3f}s")
                print(f"File size: {file_size/1024:.1f} KB")

                # Check for exponential degradation
                if len(times) >= 2:
                    prev = times[-2]
                    curr = times[-1]
                    write_ratio = curr["write_time"] / prev["write_time"]
                    search_ratio = curr["search_time"] / prev["search_time"]
                    scale_ratio = curr["scale"] / prev["scale"]

                    print(f"Performance ratios vs scale ratio {scale_ratio:.1f}:")
                    print(f"  Write: {write_ratio:.2f}x")
                    print(f"  Search: {search_ratio:.2f}x")

                    # Warn if performance degrades quadratically
                    if write_ratio > scale_ratio * 1.5:
                        print(
                            f"⚠️  Write performance degrading: {write_ratio:.2f}x vs {scale_ratio:.1f}x scale"
                        )
                    if search_ratio > scale_ratio * 2:
                        print(
                            f"⚠️  Search performance degrading: {search_ratio:.2f}x vs {scale_ratio:.1f}x scale"
                        )

            return times, file_sizes

        finally:
            mem_tools.MEMORY_PATH = original_memory_path
            mem_tools.SESSION_ID = original_session_id


def test_memory_leak():
    """Test for memory leaks during repeated operations."""

    with tempfile.TemporaryDirectory() as temp_dir:
        memory_path = Path(temp_dir) / "memory"
        memory_path.mkdir(exist_ok=True)

        import bridge_design_system.tools.memory_tools as mem_tools

        original_memory_path = mem_tools.MEMORY_PATH
        original_session_id = mem_tools.SESSION_ID

        try:
            mem_tools.MEMORY_PATH = memory_path
            mem_tools.SESSION_ID = "leak_test"

            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            print(f"Initial memory usage: {initial_memory:.1f} MB")

            # Perform many operations
            for batch in range(20):
                for i in range(100):
                    remember("leak", f"batch_{batch}_item_{i}", f"Batch {batch} item {i}")
                    recall("leak", f"batch_{batch}_item_{i}")
                    search_memory(f"batch_{batch}")

                # Check memory every 5 batches
                if batch % 5 == 4:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    growth = current_memory - initial_memory
                    operations = (batch + 1) * 100 * 3  # 3 ops per iteration

                    print(
                        f"After {operations} operations: {current_memory:.1f} MB (+{growth:.1f} MB)"
                    )

                    if growth > 50:  # More than 50MB growth
                        print(f"⚠️  Potential memory leak: {growth:.1f} MB growth")
                        return False

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_growth = final_memory - initial_memory
            print(f"Final memory usage: {final_memory:.1f} MB (+{total_growth:.1f} MB)")

            return total_growth < 30  # Should not grow more than 30MB

        finally:
            mem_tools.MEMORY_PATH = original_memory_path
            mem_tools.SESSION_ID = original_session_id


if __name__ == "__main__":
    print("=== MEMORY PERFORMANCE TEST ===")
    times, sizes = test_memory_performance()

    print("\n=== MEMORY LEAK TEST ===")
    no_leak = test_memory_leak()
    print(f"Memory leak test passed: {no_leak}")

    print("\n=== SUMMARY ===")
    print(f"Tested scales: {[t['scale'] for t in times]}")
    print(f"File sizes: {[s/1024 for s in sizes]} KB")
    print(f"No memory leaks detected: {no_leak}")
