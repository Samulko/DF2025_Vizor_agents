"""
Test memory system with large data values.
"""

import tempfile
import time
from pathlib import Path

from bridge_design_system.tools.memory_tools import remember, recall


def test_large_values():
    """Test storing very large values."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        memory_path = Path(temp_dir) / "memory"
        memory_path.mkdir(exist_ok=True)
        
        import bridge_design_system.tools.memory_tools as mem_tools
        original_memory_path = mem_tools.MEMORY_PATH
        original_session_id = mem_tools.SESSION_ID
        
        try:
            mem_tools.MEMORY_PATH = memory_path
            mem_tools.SESSION_ID = 'large_test'
            
            # Test different sizes
            sizes = [
                ("1KB", 1024),
                ("10KB", 10 * 1024),
                ("100KB", 100 * 1024),
                ("1MB", 1024 * 1024),
                ("5MB", 5 * 1024 * 1024),
            ]
            
            for size_name, size_bytes in sizes:
                print(f"\n=== Testing {size_name} value ===")
                
                # Create large string
                large_value = "x" * size_bytes
                
                # Test write
                start_time = time.time()
                try:
                    result = remember("large", f"value_{size_name}", large_value)
                    write_time = time.time() - start_time
                    print(f"Write time: {write_time:.3f}s")
                    
                    # Test read
                    start_time = time.time()
                    recalled = recall("large", f"value_{size_name}")
                    read_time = time.time() - start_time
                    print(f"Read time: {read_time:.3f}s")
                    
                    # Verify data integrity
                    if large_value in recalled:
                        print(f"✅ Data integrity verified")
                    else:
                        print(f"❌ Data integrity failed")
                        
                    # Check file size
                    memory_file = mem_tools.get_memory_file()
                    if memory_file.exists():
                        file_size = memory_file.stat().st_size
                        print(f"File size: {file_size / 1024:.1f} KB")
                        
                        # File should be larger than the data (JSON overhead)
                        if file_size < size_bytes:
                            print(f"⚠️  File smaller than data: {file_size} < {size_bytes}")
                    
                    # Performance warnings
                    if write_time > 5.0:
                        print(f"⚠️  Slow write: {write_time:.3f}s")
                    if read_time > 5.0:
                        print(f"⚠️  Slow read: {read_time:.3f}s")
                        
                except Exception as e:
                    print(f"❌ Failed: {e}")
                    
        finally:
            mem_tools.MEMORY_PATH = original_memory_path
            mem_tools.SESSION_ID = original_session_id


def test_special_characters():
    """Test handling of special characters and encoding."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        memory_path = Path(temp_dir) / "memory"
        memory_path.mkdir(exist_ok=True)
        
        import bridge_design_system.tools.memory_tools as mem_tools
        original_memory_path = mem_tools.MEMORY_PATH
        original_session_id = mem_tools.SESSION_ID
        
        try:
            mem_tools.MEMORY_PATH = memory_path
            mem_tools.SESSION_ID = 'special_test'
            
            # Test various special cases
            test_cases = [
                ("unicode", "Unicode: 🚀 测试 عربي Ñoño"),
                ("json_chars", 'JSON chars: {"quotes": "value", \'single\': null}'),
                ("newlines", "Multiple\nlines\nwith\nnewlines"),
                ("tabs", "Tabs\tand\tspaces\t\there"),
                ("nullbytes", "Null\x00bytes\x00here"),
                ("long_unicode", "🚀" * 1000),  # 1000 emoji
                ("mixed", "Mixed: 中文 + English + العربية + 🎉\n\tJSON: {\"test\": true}"),
            ]
            
            for test_name, test_value in test_cases:
                print(f"\n=== Testing {test_name} ===")
                try:
                    result = remember("special", test_name, test_value)
                    print(f"Stored: {len(test_value)} chars")
                    
                    recalled = recall("special", test_name)
                    if test_value in recalled:
                        print(f"✅ Roundtrip successful")
                    else:
                        print(f"❌ Roundtrip failed")
                        print(f"Expected: {repr(test_value[:100])}")
                        print(f"Got: {repr(recalled[:100])}")
                        
                except Exception as e:
                    print(f"❌ Failed: {e}")
                    
        finally:
            mem_tools.MEMORY_PATH = original_memory_path
            mem_tools.SESSION_ID = original_session_id


if __name__ == "__main__":
    print("=== LARGE VALUE TEST ===")
    test_large_values()
    
    print("\n\n=== SPECIAL CHARACTERS TEST ===")
    test_special_characters()