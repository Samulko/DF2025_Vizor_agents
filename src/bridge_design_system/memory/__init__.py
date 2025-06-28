"""
Native Smolagents Memory Integration Module

This module implements the missing native smolagents memory methods to automatically
track and remember original element values, solving the core issue where agents
forget design history.

Following smolagents official documentation patterns for:
- Step callbacks for automatic memory tracking
- Memory queries using agent.memory.steps
- Manual step execution with memory control
- Memory transfer between agents

Key Functions:
- track_design_changes: Step callback for automatic design state tracking
- get_original_element_state: Query agent memory for original element values
- query_design_history: Get complete design history for an element
- Memory transfer utilities for cross-agent communication

References:
- Smolagents Documentation: /huggingface/smolagents memory tutorial
- Step callbacks: memory.mdx#_snippet_3-4
- Manual execution: memory.mdx#_snippet_5
- Memory access: memory.mdx#_snippet_2
"""

from .memory_callbacks import track_design_changes
from .memory_queries import (
    get_original_element_state,
    query_design_history,
    get_element_changes_count,
    transfer_agent_memory,
    find_element_original_values,
)
from .memory_utils import (
    extract_element_id_from_observations,
    format_memory_record,
    cleanup_old_memory_steps,
    get_memory_statistics,
    validate_memory_integrity,
)

__all__ = [
    "track_design_changes",
    "get_original_element_state",
    "query_design_history",
    "get_element_changes_count",
    "transfer_agent_memory",
    "find_element_original_values",
    "extract_element_id_from_observations",
    "format_memory_record",
    "cleanup_old_memory_steps",
    "get_memory_statistics",
    "validate_memory_integrity",
]
