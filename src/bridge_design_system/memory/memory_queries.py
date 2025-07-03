"""
Native Smolagents Memory Query System

This module implements memory query functions using native smolagents agent.memory.steps
to retrieve design history and original element values.

Solves the core issue: "What was element 002's original length?" by querying agent memory
instead of relying on external storage.

Reference: https://github.com/huggingface/smolagents/blob/main/docs/source/en/tutorials/memory.mdx#_snippet_2
"""

import json
import re
from typing import Any, Dict, List, Optional

from ..config.logging_config import get_logger

logger = get_logger(__name__)


def get_original_element_state(agent: Any, element_id: str) -> Optional[Dict]:
    """
    Query agent's native memory for original element state.

    Uses smolagents agent.memory.steps to find the earliest record of element
    before any modifications. This solves the core issue where agents forget
    original values like element 002's original length.

    Args:
        agent: CodeAgent or ToolCallingAgent with memory.steps access
        element_id: Element identifier (e.g., "002", "021")

    Returns:
        Dictionary with original element state information, or None if not found

    Example:
        >>> original = get_original_element_state(geometry_agent, "002")
        >>> if original:
        >>>     print(f"Element 002 original length: {original['original_observations']}")

    Reference:
        Based on smolagents memory access pattern from memory.mdx#_snippet_2
    """
    try:
        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            logger.warning(f"⚠️ Agent does not have memory.steps attribute")
            return None

        logger.debug(
            f"🔍 Searching for original state of element {element_id} in {len(agent.memory.steps)} memory steps"
        )

        # Search through memory steps chronologically for first occurrence
        for step in agent.memory.steps:
            # Import ActionStep here to avoid circular imports
            from smolagents import ActionStep

            if isinstance(step, ActionStep) and hasattr(step, "observations"):
                if step.observations and f"[MEMORY_ORIGINAL]" in step.observations:
                    # Parse memory records from observations
                    for line in step.observations.split("\n"):
                        if line.startswith("[MEMORY_ORIGINAL]"):
                            try:
                                record_json = line.replace("[MEMORY_ORIGINAL] ", "")
                                record = json.loads(record_json)

                                if record.get("element_id") == element_id:
                                    logger.info(
                                        f"✅ Found original state for element {element_id} from step {step.step_number}"
                                    )
                                    return {
                                        "element_id": element_id,
                                        "step_number": step.step_number,
                                        "original_observations": record.get(
                                            "observations_snapshot", ""
                                        ),
                                        "timestamp": record.get("timestamp"),
                                        "memory_record": record,
                                    }
                            except json.JSONDecodeError as e:
                                logger.warning(f"⚠️ Failed to parse memory record: {e}")
                                continue

        logger.debug(f"🔍 No original state found for element {element_id}")
        return None

    except Exception as e:
        logger.error(f"❌ Error querying original element state: {e}")
        return None


def query_design_history(agent: Any, element_id: str) -> List[Dict]:
    """
    Get complete design history for an element from agent memory.

    Returns chronological list of all changes to the element using native
    smolagents memory.steps access pattern.

    Args:
        agent: CodeAgent or ToolCallingAgent with memory.steps
        element_id: Element identifier to get history for

    Returns:
        List of dictionaries with chronological design history

    Example:
        >>> history = query_design_history(geometry_agent, "002")
        >>> for change in history:
        >>>     print(f"Step {change['step_number']}: {change['action']}")

    Reference:
        Smolagents memory iteration pattern from memory.mdx#_snippet_2
    """
    try:
        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            logger.warning(f"⚠️ Agent does not have memory.steps attribute")
            return []

        history = []

        logger.debug(f"🔍 Querying design history for element {element_id}")

        # Iterate through all memory steps chronologically
        for step in agent.memory.steps:
            from smolagents import ActionStep

            if isinstance(step, ActionStep) and hasattr(step, "observations"):
                if step.observations and element_id in step.observations:
                    # Extract all memory records for this element
                    step_records = []

                    for line in step.observations.split("\n"):
                        if any(
                            line.startswith(prefix)
                            for prefix in ["[MEMORY_ORIGINAL]", "[MEMORY_UPDATE]", "[MEMORY_MCP]"]
                        ):
                            try:
                                # Extract JSON from memory line
                                for prefix in [
                                    "[MEMORY_ORIGINAL] ",
                                    "[MEMORY_UPDATE] ",
                                    "[MEMORY_MCP] ",
                                ]:
                                    if line.startswith(prefix):
                                        record_json = line.replace(prefix, "")
                                        record = json.loads(record_json)
                                        if record.get("element_id") == element_id:
                                            step_records.append(record)
                                        break
                            except json.JSONDecodeError:
                                continue

                    # Add step to history if it contains relevant records
                    if step_records or element_id in step.observations:
                        history_entry = {
                            "step_number": step.step_number,
                            "observations": step.observations,
                            "error": getattr(step, "error", None),
                            "memory_records": step_records,
                            "has_element_reference": element_id in step.observations,
                        }
                        history.append(history_entry)

        logger.info(f"📊 Found {len(history)} history entries for element {element_id}")
        return history

    except Exception as e:
        logger.error(f"❌ Error querying design history: {e}")
        return []


def get_element_changes_count(agent: Any) -> Dict[str, int]:
    """
    Count how many times each element has been modified using agent memory.

    Provides overview of design activity by analyzing native smolagents memory
    for parameter update patterns.

    Args:
        agent: CodeAgent or ToolCallingAgent with memory.steps

    Returns:
        Dictionary mapping element_id to modification count

    Example:
        >>> changes = get_element_changes_count(geometry_agent)
        >>> print(f"Element 002 modified {changes.get('002', 0)} times")
    """
    try:
        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            return {}

        changes = {}

        for step in agent.memory.steps:
            from smolagents import ActionStep

            if isinstance(step, ActionStep) and hasattr(step, "observations"):
                if step.observations:
                    # Look for parameter update patterns
                    if "parameter update" in step.observations.lower():
                        # Extract element ID from observations using multiple patterns
                        element_matches = []

                        # Pattern 1: element 'XXX' (from Direct Parameter Update)
                        matches = re.findall(r"element.*?'(\w+)'", step.observations)
                        element_matches.extend(matches)

                        # Pattern 2: dynamic_XXX (from HoloLens data)
                        matches = re.findall(r"dynamic_(\d+)", step.observations)
                        element_matches.extend(matches)

                        # Pattern 3: Memory records
                        for line in step.observations.split("\n"):
                            if "[MEMORY_" in line:
                                try:
                                    for prefix in [
                                        "[MEMORY_ORIGINAL] ",
                                        "[MEMORY_UPDATE] ",
                                        "[MEMORY_MCP] ",
                                    ]:
                                        if line.startswith(prefix):
                                            record_json = line.replace(prefix, "")
                                            record = json.loads(record_json)
                                            if "element_id" in record:
                                                element_matches.append(record["element_id"])
                                            break
                                except json.JSONDecodeError:
                                    continue

                        # Count unique elements in this step
                        for element_id in set(element_matches):
                            changes[element_id] = changes.get(element_id, 0) + 1

        logger.debug(f"📊 Element modification counts: {changes}")
        return changes

    except Exception as e:
        logger.error(f"❌ Error counting element changes: {e}")
        return {}


def transfer_agent_memory(
    source_agent: Any, target_agent: Any, element_filter: Optional[str] = None
) -> bool:
    """
    Transfer design memory from source agent to target agent.

    Uses smolagents native memory.steps transfer pattern from documentation
    to share design history between geometry and triage agents.

    Args:
        source_agent: Agent to copy memory from
        target_agent: Agent to copy memory to
        element_filter: Optional element ID to filter transfer

    Returns:
        True if transfer successful, False otherwise

    Example:
        >>> # Transfer all geometry memory to triage agent
        >>> transfer_agent_memory(geometry_agent, triage_agent)
        >>>
        >>> # Transfer only element 002 history
        >>> transfer_agent_memory(geometry_agent, triage_agent, element_filter="002")

    Reference:
        Smolagents memory transfer pattern: agent.memory.steps = other_agent.memory.steps
        From memory.mdx#_snippet_5 documentation
    """
    try:
        if not all(
            hasattr(agent, "memory") and hasattr(agent.memory, "steps")
            for agent in [source_agent, target_agent]
        ):
            logger.error("❌ Both agents must have memory.steps attribute")
            return False

        # Selective transfer of design-related steps only
        design_steps = []

        for step in source_agent.memory.steps:
            from smolagents import ActionStep

            if isinstance(step, ActionStep) and hasattr(step, "observations"):
                if step.observations:
                    # Check if step contains design-related content
                    is_design_step = any(
                        indicator in step.observations.lower()
                        for indicator in [
                            "parameter update",
                            "element",
                            "[memory_",
                            "direct parameter",
                            "rg.point3d",
                            "rg.vector3d",
                            "mcp",
                        ]
                    )

                    # Apply element filter if specified
                    if element_filter and is_design_step:
                        is_design_step = element_filter in step.observations

                    if is_design_step:
                        design_steps.append(step)

        # Add to target agent memory (native smolagents pattern)
        if design_steps:
            target_agent.memory.steps.extend(design_steps)
            logger.info(f"🔄 Transferred {len(design_steps)} design memory steps to target agent")

            if element_filter:
                logger.info(f"   📎 Filter applied: element {element_filter}")

            return True
        else:
            logger.info("ℹ️ No design-related memory steps found to transfer")
            return False

    except Exception as e:
        logger.error(f"❌ Error transferring agent memory: {e}")
        return False


def find_element_original_values(agent: Any, element_id: str) -> Optional[Dict[str, Any]]:
    """
    Extract original parameter values from memory for specific element.

    Solves the specific use case: "What was element 002's original length of 0.40?"
    by parsing the original observations for actual parameter values.

    Args:
        agent: Agent with memory to search
        element_id: Element to find original values for

    Returns:
        Dictionary with extracted original values (length, center, direction)

    Example:
        >>> values = find_element_original_values(geometry_agent, "002")
        >>> if values:
        >>>     print(f"Original length: {values.get('length')}")
        >>>     print(f"Original center: {values.get('center')}")
    """
    try:
        original_state = get_original_element_state(agent, element_id)
        if not original_state:
            return None

        observations = original_state.get("original_observations", "")
        values = {}

        # Extract parameter values from observations using regex patterns
        # Pattern for Point3d values: rg.Point3d(x, y, z)
        point_match = re.search(r"rg\.Point3d\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)", observations)
        if point_match:
            values["center"] = [
                float(point_match.group(1)),
                float(point_match.group(2)),
                float(point_match.group(3)),
            ]

        # Pattern for Vector3d values: rg.Vector3d(x, y, z)
        vector_match = re.search(
            r"rg\.Vector3d\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)", observations
        )
        if vector_match:
            values["direction"] = [
                float(vector_match.group(1)),
                float(vector_match.group(2)),
                float(vector_match.group(3)),
            ]

        # Pattern for length values (more generic)
        length_patterns = [
            r'length["\']?\s*[:=]\s*([-\d.]+)',
            r"([0-9.]+)\s*(?:mm|meter|m)\s*(?:long|length)",
            r"length.*?([-\d.]+)",
        ]

        for pattern in length_patterns:
            length_match = re.search(pattern, observations, re.IGNORECASE)
            if length_match:
                values["length"] = float(length_match.group(1))
                break

        logger.debug(f"📏 Extracted original values for element {element_id}: {values}")
        return values if values else None

    except Exception as e:
        logger.error(f"❌ Error extracting original values: {e}")
        return None
