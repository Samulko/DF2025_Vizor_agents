"""Memory tools for persistent context across agent sessions.

This module provides three SmolaGents tools for memory management:
- remember: Store information in persistent memory
- recall: Retrieve stored information
- search_memory: Search across all memories
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import time
# Platform-specific imports for file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
import tempfile
import shutil

from smolagents import tool


# Session management
SESSION_ID = os.environ.get('BRIDGE_SESSION_ID', f'session_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
MEMORY_PATH = Path(__file__).parent.parent / 'data' / 'memory'
MEMORY_PATH.mkdir(parents=True, exist_ok=True)


def get_memory_file() -> Path:
    """Get the path to the current session's memory file."""
    return MEMORY_PATH / f'{SESSION_ID}.json'


def get_lock_file() -> Path:
    """Get the path to the lock file for the current session."""
    return MEMORY_PATH / f'.{SESSION_ID}.lock'


def acquire_lock(timeout: float = 5.0) -> Optional[Any]:
    """Acquire a file lock for memory operations.
    
    Returns:
        Lock object if successful, None if failed
    """
    lock_file = get_lock_file()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Try to create lock file exclusively
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            # Write PID to help with debugging
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lock_file  # Return the lock file path as our "lock object"
        except FileExistsError:
            # Lock is held by another process
            # Check if lock is stale (older than 30 seconds)
            try:
                if lock_file.exists():
                    lock_age = time.time() - lock_file.stat().st_mtime
                    if lock_age > 30:  # Stale lock
                        lock_file.unlink()  # Remove stale lock
                        continue
            except:
                pass
            time.sleep(0.05)  # Brief wait before retry
        except Exception:
            return None
    
    return None


def release_lock(lock: Any) -> None:
    """Release a file lock."""
    if lock and isinstance(lock, Path):
        try:
            lock.unlink()
        except:
            pass


def load_memory() -> Dict[str, Any]:
    """Load memory from JSON file with error handling."""
    memory_file = get_memory_file()
    default_memory = {"session_id": SESSION_ID, "memories": {}}
    
    if not memory_file.exists():
        return default_memory
    
    # Try to read with retries for transient failures
    for attempt in range(3):
        try:
            with open(memory_file, 'r') as f:
                # Non-blocking read attempt
                content = f.read()
                if content:
                    return json.loads(content)
                else:
                    return default_memory
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Corrupted memory file {memory_file}, starting fresh. Error: {e}")
            return default_memory
        except (IOError, OSError) as e:
            if attempt < 2:
                time.sleep(0.1)  # Brief retry delay
                continue
            print(f"Warning: Could not read memory file after 3 attempts. Error: {e}")
            return default_memory
        except Exception as e:
            print(f"Warning: Unexpected error reading memory. Using defaults. Error: {e}")
            return default_memory
    
    return default_memory


def save_memory(memory_data: Dict[str, Any]) -> bool:
    """Save memory to JSON file with atomic writes and error handling.
    
    Returns:
        bool: True if save succeeded, False otherwise
    """
    memory_file = get_memory_file()
    
    # Ensure directory exists
    try:
        memory_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create memory directory. Error: {e}")
        return False
    
    # Acquire lock for exclusive write access
    lock = acquire_lock(timeout=2.0)  # Shorter timeout for workshop responsiveness
    if not lock:
        print(f"Warning: Could not acquire lock for memory write. Another operation in progress.")
        # In workshop setting, we'll continue without lock rather than fail
    
    try:
        # Use atomic write with temp file to prevent corruption
        temp_fd = None
        temp_path = None
        
        for attempt in range(3):
            try:
                # Create temp file in same directory for atomic rename
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=memory_file.parent,
                    prefix='.tmp_memory_',
                    suffix='.json'
                )
                
                # Write to temp file
                with os.fdopen(temp_fd, 'w') as f:
                    json.dump(memory_data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                
                # Atomic rename (works on same filesystem)
                if os.name == 'nt':  # Windows
                    # Windows doesn't support atomic rename if target exists
                    if memory_file.exists():
                        memory_file.unlink()
                os.rename(temp_path, memory_file)
                
                return True
                
            except Exception as e:
                # Clean up temp file if it exists
                if temp_fd is not None:
                    try:
                        os.close(temp_fd)
                    except:
                        pass
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                
                if attempt < 2:
                    time.sleep(0.1)  # Brief retry delay
                    continue
                    
                print(f"Warning: Could not save memory after 3 attempts. Error: {e}")
                return False
        
        return False
    
    finally:
        # Always release lock
        release_lock(lock)


@tool
def remember(category: str, key: str, value: str) -> str:
    """Store information in persistent memory.
    
    Args:
        category: Type of memory (components, context, errors, tools, decisions, etc)
        key: Unique identifier for this memory within the category
        value: Information to store
    
    Returns:
        Confirmation message
    
    Example:
        remember("components", "main_truss", "ID: comp_123, 50m span timber truss")
        remember("context", "project_goal", "Design a pedestrian bridge with timber trusses")
        remember("decisions", "material_choice", "Selected timber for sustainability")
    """
    start_time = time.time()
    
    # Load current memory
    memory_data = load_memory()
    
    # Ensure category exists
    if "memories" not in memory_data:
        memory_data["memories"] = {}
    if category not in memory_data["memories"]:
        memory_data["memories"][category] = {}
    
    # Store the memory with metadata
    memory_data["memories"][category][key] = {
        "value": value,
        "timestamp": datetime.now().isoformat(),
        "category": category
    }
    
    # Save to file
    success = save_memory(memory_data)
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    if success:
        return f"Remembered in category '{category}' with key '{key}' (took {elapsed_ms:.1f}ms)"
    else:
        # Memory save failed but we can continue - workshop must go on!
        return f"⚠️ Memory save had issues but continuing. Item: '{category}/{key}' (took {elapsed_ms:.1f}ms)"


@tool  
def recall(category: Optional[str] = None, key: Optional[str] = None) -> str:
    """Retrieve information from memory.
    
    Args:
        category: Optional - filter by category (if None, shows all categories)
        key: Optional - get specific memory (if None, shows all in category)
        
    Returns:
        Retrieved memory or summary of available memories
        
    Example:
        recall() -> Summary of all memory categories
        recall("components") -> All component memories
        recall("components", "main_truss") -> Specific component memory
    """
    start_time = time.time()
    
    memory_data = load_memory()
    memories = memory_data.get("memories", {})
    
    # No parameters - show summary
    if category is None:
        if not memories:
            return "No memories stored yet"
        
        summary = f"Memory categories available (session: {memory_data.get('session_id', 'unknown')}):\n"
        for cat, items in memories.items():
            summary += f"- {cat}: {len(items)} items\n"
        
        elapsed_ms = (time.time() - start_time) * 1000
        summary += f"\n(Query took {elapsed_ms:.1f}ms)"
        return summary
    
    # Category specified but not found
    if category not in memories:
        return f"No memories found in category '{category}'"
    
    # Specific key requested
    if key is not None:
        if key in memories[category]:
            item = memories[category][key]
            elapsed_ms = (time.time() - start_time) * 1000
            return f"{item['value']}\n(Stored at: {item['timestamp']}, retrieved in {elapsed_ms:.1f}ms)"
        else:
            return f"No memory found for key '{key}' in category '{category}'"
    
    # All items in category
    result = f"Memories in category '{category}':\n"
    for key, item in memories[category].items():
        result += f"\n[{key}]: {item['value']}\n  (Stored: {item['timestamp']})\n"
    
    elapsed_ms = (time.time() - start_time) * 1000
    result += f"\n(Query took {elapsed_ms:.1f}ms)"
    return result


@tool
def search_memory(query: str, limit: int = 10) -> str:
    """Search across all memories for matching content.
    
    Args:
        query: Text to search for (case-insensitive)
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        Matching memories with their categories and keys
        
    Example:
        search_memory("timber") -> Find all memories mentioning timber
        search_memory("comp_") -> Find all component IDs
        search_memory("error", limit=5) -> Find up to 5 error-related memories
    """
    start_time = time.time()
    
    memory_data = load_memory()
    memories = memory_data.get("memories", {})
    
    if not memories:
        return "No memories to search"
    
    # Case-insensitive search
    query_lower = query.lower()
    results = []
    
    # Search through all memories
    for category, items in memories.items():
        for key, item in items.items():
            value_lower = item["value"].lower()
            key_lower = key.lower()
            
            # Check if query matches in key or value
            if query_lower in value_lower or query_lower in key_lower:
                score = 0
                # Higher score for exact matches
                if query_lower == key_lower:
                    score = 100
                elif query_lower in key_lower:
                    score = 50
                elif query_lower in value_lower:
                    # Score based on position (earlier = better)
                    score = 25 - (value_lower.index(query_lower) / len(value_lower) * 20)
                
                results.append({
                    "category": category,
                    "key": key,
                    "value": item["value"],
                    "timestamp": item["timestamp"],
                    "score": score
                })
    
    if not results:
        return f"No memories found matching '{query}'"
    
    # Sort by score (highest first) and limit
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]
    
    # Format results
    output = f"Found {len(results)} memories matching '{query}':\n"
    for i, result in enumerate(results, 1):
        output += f"\n{i}. [{result['category']}/{result['key']}]:\n"
        output += f"   {result['value']}\n"
        output += f"   (Stored: {result['timestamp']})\n"
    
    elapsed_ms = (time.time() - start_time) * 1000
    output += f"\n(Search took {elapsed_ms:.1f}ms)"
    return output


@tool
def clear_memory(category: Optional[str] = None, confirm: str = "no") -> str:
    """Clear memory data. USE WITH CAUTION - this deletes stored memories.
    
    Args:
        category: Specific category to clear (e.g., "components", "context"). 
                 If None, clears ALL memory.
        confirm: Must be "yes" to actually perform the deletion
        
    Returns:
        Status message about what was cleared
        
    Examples:
        clear_memory("components", "yes") -> Clear only component memories
        clear_memory(None, "yes") -> Clear ALL memories (full reset)
        clear_memory("errors", "yes") -> Clear error logs
    """
    if confirm != "yes":
        return f"Memory clear aborted. To confirm deletion, use confirm='yes'"
    
    memory_data = load_memory()
    
    if category is None:
        # Clear all memory
        old_count = sum(len(items) for items in memory_data.get("memories", {}).values())
        memory_data["memories"] = {}
        if save_memory(memory_data):
            return f"🗑️ Cleared ALL memory ({old_count} items deleted). Fresh start!"
        else:
            return f"⚠️ Had issues clearing memory but will continue"
    
    elif category in memory_data.get("memories", {}):
        # Clear specific category
        old_count = len(memory_data["memories"][category])
        del memory_data["memories"][category]
        if save_memory(memory_data):
            return f"🗑️ Cleared category '{category}' ({old_count} items deleted)"
        else:
            return f"⚠️ Had issues clearing category '{category}' but will continue"
    
    else:
        return f"Category '{category}' not found. Available: {list(memory_data.get('memories', {}).keys())}"


# Helper function for Component Registry integration
def remember_component(component_id: str, component_type: str, description: str) -> None:
    """Helper function to remember a component (used by Component Registry).
    
    This is not a tool, but a helper function for internal use.
    """
    value = f"Type: {component_type}, Description: {description}, Created: {datetime.now().isoformat()}"
    # Direct memory manipulation for efficiency
    memory_data = load_memory()
    if "memories" not in memory_data:
        memory_data["memories"] = {}
    if "components" not in memory_data["memories"]:
        memory_data["memories"]["components"] = {}
    
    memory_data["memories"]["components"][component_id] = {
        "value": value,
        "timestamp": datetime.now().isoformat(),
        "category": "components",
        "metadata": {
            "type": component_type,
            "description": description
        }
    }
    # Best effort save - don't crash component creation if memory fails
    try:
        save_memory(memory_data)
    except Exception as e:
        print(f"Warning: Could not save component to memory: {e}")