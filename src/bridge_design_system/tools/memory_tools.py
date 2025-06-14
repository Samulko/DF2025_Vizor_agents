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

from smolagents import tool


# Session management
SESSION_ID = os.environ.get('BRIDGE_SESSION_ID', f'session_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
MEMORY_PATH = Path(__file__).parent.parent / 'data' / 'memory'
MEMORY_PATH.mkdir(parents=True, exist_ok=True)


def get_memory_file() -> Path:
    """Get the path to the current session's memory file."""
    return MEMORY_PATH / f'{SESSION_ID}.json'


def load_memory() -> Dict[str, Any]:
    """Load memory from JSON file."""
    memory_file = get_memory_file()
    if memory_file.exists():
        try:
            return json.loads(memory_file.read_text())
        except json.JSONDecodeError:
            print(f"Warning: Corrupted memory file {memory_file}, starting fresh")
            return {"session_id": SESSION_ID, "memories": {}}
    return {"session_id": SESSION_ID, "memories": {}}


def save_memory(memory_data: Dict[str, Any]) -> None:
    """Save memory to JSON file."""
    memory_file = get_memory_file()
    memory_file.write_text(json.dumps(memory_data, indent=2))


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
    save_memory(memory_data)
    
    elapsed_ms = (time.time() - start_time) * 1000
    return f"Remembered in category '{category}' with key '{key}' (took {elapsed_ms:.1f}ms)"


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
    save_memory(memory_data)