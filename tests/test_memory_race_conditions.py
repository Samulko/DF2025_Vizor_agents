"""
Simple test to isolate race conditions in memory system.
"""

import tempfile
import threading
import time
from pathlib import Path
import pytest

from bridge_design_system.tools.memory_tools import remember, load_memory


def test_simple_race_condition():
    """Test the simplest possible race condition."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        memory_path = Path(temp_dir) / "memory"
        memory_path.mkdir(exist_ok=True)
        
        # Patch the memory tools to use our temp directory
        import bridge_design_system.tools.memory_tools as mem_tools
        original_memory_path = mem_tools.MEMORY_PATH
        original_session_id = mem_tools.SESSION_ID
        
        try:
            mem_tools.MEMORY_PATH = memory_path
            mem_tools.SESSION_ID = 'race_test'
            
            errors = []
            
            def write_worker(worker_id):
                """Worker that writes 5 memories."""
                try:
                    for i in range(5):
                        result = remember(f"worker_{worker_id}", f"key_{i}", f"Worker {worker_id} value {i}")
                        print(f"Worker {worker_id}: {result}")
                        time.sleep(0.01)  # Small delay
                except Exception as e:
                    errors.append(f"Worker {worker_id}: {e}")
            
            # Start 3 workers
            threads = []
            for i in range(3):
                t = threading.Thread(target=write_worker, args=(i,))
                threads.append(t)
                t.start()
            
            # Wait for all to complete
            for t in threads:
                t.join()
            
            print(f"Errors: {errors}")
            
            # Check final state
            final_memory = load_memory()
            print(f"Final memory: {final_memory}")
            
            # Count total memories
            total_memories = 0
            for category, items in final_memory.get("memories", {}).items():
                total_memories += len(items)
            
            print(f"Total memories: {total_memories} (expected: 15)")
            
            # This should have 15 memories (3 workers * 5 memories each)
            assert total_memories == 15, f"Expected 15 memories, got {total_memories}"
            assert len(errors) == 0, f"Got errors: {errors}"
            
        finally:
            # Restore original values
            mem_tools.MEMORY_PATH = original_memory_path  
            mem_tools.SESSION_ID = original_session_id


if __name__ == "__main__":
    test_simple_race_condition()