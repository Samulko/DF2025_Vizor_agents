"""
Native Smolagents Memory Utilities

Helper functions for memory management, formatting, and extraction tasks
that support the native smolagents memory integration.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config.logging_config import get_logger

logger = get_logger(__name__)


def extract_element_id_from_observations(observations: str) -> Optional[str]:
    """
    Extract element ID from step observations using multiple patterns.

    Supports various formats from Direct Parameter Update workflow:
    - element 'XXX' (from formatted tasks)
    - dynamic_XXX (from HoloLens data)
    - Element XXX (from MCP responses)

    Args:
        observations: Step observations text to parse

    Returns:
        Element ID string, or None if not found

    Example:
        >>> extract_element_id_from_observations("Update element '002' center")
        '002'
        >>> extract_element_id_from_observations("Processing dynamic_021")
        '021'
    """
    if not observations:
        return None

    try:
        # Pattern 1: element 'XXX' (from Direct Parameter Update tasks)
        match = re.search(r"element.*?'(\w+)'", observations)
        if match:
            return match.group(1)

        # Pattern 2: dynamic_XXX (from HoloLens VizorListener data)
        match = re.search(r"dynamic_(\d+)", observations)
        if match:
            return match.group(1)

        # Pattern 3: Element XXX (from MCP responses)
        match = re.search(r"element\s+(\w+)", observations, re.IGNORECASE)
        if match:
            return match.group(1)

        # Pattern 4: component_X/beam_Y references
        match = re.search(r"component_\d+/beam_(\d+)", observations)
        if match:
            return match.group(1)

        return None

    except Exception as e:
        logger.error(f"❌ Error extracting element ID: {e}")
        return None


def format_memory_record(
    element_id: str, action: str, step_number: int, additional_data: Optional[Dict] = None
) -> str:
    """
    Format a structured memory record for storage in step observations.

    Creates consistent JSON format for memory records that can be easily
    parsed by memory query functions.

    Args:
        element_id: Element identifier
        action: Action type (e.g., "parameter_update", "first_modification")
        step_number: Current step number
        additional_data: Optional additional data to include

    Returns:
        Formatted JSON string ready for storage in observations

    Example:
        >>> record = format_memory_record("002", "parameter_update", 5)
        >>> # Returns: '{"element_id": "002", "action": "parameter_update", ...}'
    """
    try:
        record = {
            "element_id": element_id,
            "action": action,
            "step_number": step_number,
            "timestamp": datetime.now().isoformat(),
        }

        if additional_data:
            record.update(additional_data)

        return json.dumps(record)

    except Exception as e:
        logger.error(f"❌ Error formatting memory record: {e}")
        return (
            f'{{"element_id": "{element_id}", "action": "{action}", "error": "formatting_failed"}}'
        )


def cleanup_old_memory_steps(agent: Any, keep_last_n: int = 3) -> int:
    """
    Clean up old memory steps to prevent memory bloat.

    Implements the smolagents memory cleanup pattern from documentation,
    removing old observations_images and compressing old detailed observations
    while preserving memory records.

    Args:
        agent: Agent with memory.steps to clean up
        keep_last_n: Number of recent steps to keep with full detail

    Returns:
        Number of steps cleaned up

    Reference:
        Smolagents memory cleanup pattern from memory.mdx#_snippet_3
    """
    try:
        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            return 0

        cleaned_steps = 0
        total_steps = len(agent.memory.steps)

        if total_steps <= keep_last_n:
            return 0  # Not enough steps to clean

        # Get the latest step number for reference
        latest_step_num = max(
            step.step_number for step in agent.memory.steps if hasattr(step, "step_number")
        )

        from smolagents import ActionStep

        for step in agent.memory.steps:
            if isinstance(step, ActionStep):
                step_age = latest_step_num - getattr(step, "step_number", 0)

                # Clean up observations_images for steps older than keep_last_n
                if step_age > keep_last_n and hasattr(step, "observations_images"):
                    if step.observations_images is not None:
                        step.observations_images = None
                        cleaned_steps += 1

                # Compress very old detailed observations (keep only memory records)
                if step_age > keep_last_n * 2 and hasattr(step, "observations"):
                    if step.observations:
                        lines = step.observations.split("\n")
                        memory_lines = [line for line in lines if line.startswith("[MEMORY")]

                        if memory_lines and len(memory_lines) < len(lines):
                            # Compress to memory records only
                            step.observations = "\n".join(memory_lines)
                            cleaned_steps += 1

        logger.debug(f"🧹 Cleaned up {cleaned_steps} old memory steps")
        return cleaned_steps

    except Exception as e:
        logger.error(f"❌ Error cleaning up memory steps: {e}")
        return 0


def get_memory_statistics(agent: Any) -> Dict[str, Any]:
    """
    Get statistics about agent memory usage and content.

    Provides overview of memory health, design activity, and storage usage
    for monitoring and debugging purposes.

    Args:
        agent: Agent with memory.steps to analyze

    Returns:
        Dictionary with memory statistics

    Example:
        >>> stats = get_memory_statistics(geometry_agent)
        >>> print(f"Total steps: {stats['total_steps']}")
        >>> print(f"Design changes: {stats['design_changes']}")
    """
    try:
        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            return {"error": "Agent has no memory.steps"}

        from smolagents import ActionStep, TaskStep

        stats = {
            "total_steps": len(agent.memory.steps),
            "action_steps": 0,
            "task_steps": 0,
            "design_changes": 0,
            "memory_records": 0,
            "elements_modified": set(),
            "mcp_tool_calls": 0,
            "steps_with_images": 0,
            "memory_size_estimate": 0,
        }

        for step in agent.memory.steps:
            # Count step types
            if isinstance(step, ActionStep):
                stats["action_steps"] += 1

                # Count image storage
                if hasattr(step, "observations_images") and step.observations_images:
                    stats["steps_with_images"] += 1

            elif isinstance(step, TaskStep):
                stats["task_steps"] += 1

            # Analyze observations for design activity
            if hasattr(step, "observations") and step.observations:
                observations = step.observations

                # Count design changes
                if "parameter update" in observations.lower():
                    stats["design_changes"] += 1

                # Count memory records
                memory_lines = [
                    line for line in observations.split("\n") if line.startswith("[MEMORY")
                ]
                stats["memory_records"] += len(memory_lines)

                # Extract modified elements
                element_id = extract_element_id_from_observations(observations)
                if element_id:
                    stats["elements_modified"].add(element_id)

                # Count MCP tool calls
                if any(
                    mcp_indicator in observations.lower()
                    for mcp_indicator in [
                        "edit_python3_script",
                        "get_python3_script",
                        "rg.point3d",
                        "rg.vector3d",
                    ]
                ):
                    stats["mcp_tool_calls"] += 1

                # Estimate memory size
                stats["memory_size_estimate"] += len(observations)

        # Convert set to count
        stats["unique_elements_modified"] = len(stats["elements_modified"])
        stats["elements_modified"] = list(stats["elements_modified"])

        # Add memory health indicators
        stats["memory_health"] = {
            "has_design_activity": stats["design_changes"] > 0,
            "has_memory_records": stats["memory_records"] > 0,
            "memory_size_mb": stats["memory_size_estimate"] / (1024 * 1024),
            "avg_records_per_change": (
                stats["memory_records"] / stats["design_changes"]
                if stats["design_changes"] > 0
                else 0
            ),
        }

        return stats

    except Exception as e:
        logger.error(f"❌ Error getting memory statistics: {e}")
        return {"error": str(e)}


def validate_memory_integrity(agent: Any) -> Dict[str, Any]:
    """
    Validate memory integrity and consistency.

    Checks for common memory issues like:
    - Missing memory records for design changes
    - Corrupted JSON in memory records
    - Inconsistent element tracking

    Args:
        agent: Agent to validate memory for

    Returns:
        Dictionary with validation results and issues found
    """
    try:
        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            return {"valid": False, "error": "Agent has no memory.steps"}

        validation = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "stats": {
                "total_steps": len(agent.memory.steps),
                "corrupted_records": 0,
                "design_changes_without_memory": 0,
                "orphaned_memory_records": 0,
            },
        }

        from smolagents import ActionStep

        for step in agent.memory.steps:
            if isinstance(step, ActionStep) and hasattr(step, "observations"):
                if step.observations:
                    # Check for design changes without memory records
                    has_design_change = "parameter update" in step.observations.lower()
                    has_memory_record = "[MEMORY" in step.observations

                    if has_design_change and not has_memory_record:
                        validation["stats"]["design_changes_without_memory"] += 1
                        validation["warnings"].append(
                            f"Step {getattr(step, 'step_number', '?')} has design change but no memory record"
                        )

                    # Validate JSON in memory records
                    for line in step.observations.split("\n"):
                        if line.startswith("[MEMORY"):
                            try:
                                # Extract and parse JSON
                                for prefix in [
                                    "[MEMORY_ORIGINAL] ",
                                    "[MEMORY_UPDATE] ",
                                    "[MEMORY_MCP] ",
                                ]:
                                    if line.startswith(prefix):
                                        record_json = line.replace(prefix, "")
                                        json.loads(record_json)  # Validate JSON
                                        break
                            except json.JSONDecodeError:
                                validation["stats"]["corrupted_records"] += 1
                                validation["issues"].append(
                                    f"Corrupted memory record in step {getattr(step, 'step_number', '?')}"
                                )
                                validation["valid"] = False

        # Overall validation
        if validation["stats"]["corrupted_records"] > 0:
            validation["valid"] = False

        if validation["stats"]["design_changes_without_memory"] > 3:
            validation["warnings"].append(
                "High number of design changes without memory tracking - "
                "step callbacks may not be properly configured"
            )

        return validation

    except Exception as e:
        logger.error(f"❌ Error validating memory integrity: {e}")
        return {"valid": False, "error": str(e)}
