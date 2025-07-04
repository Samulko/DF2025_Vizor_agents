"""
Native Smolagents Step Callbacks for Design State Tracking

This module implements step callbacks following the official smolagents documentation
patterns for automatic memory management during agent execution.

Reference: https://github.com/huggingface/smolagents/blob/main/docs/source/en/tutorials/memory.mdx#_snippet_3-4
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from ..config.logging_config import get_logger

logger = get_logger(__name__)


def track_design_changes(memory_step: "ActionStep", agent: "CodeAgent") -> None:
    """
    Native smolagents step callback to automatically save original element values.

    Called after each agent step to extract and store design state changes.
    Follows smolagents best practices from official documentation for step callbacks.

    This function implements the missing native smolagents memory capability to:
    1. Automatically detect Direct Parameter Update tasks
    2. Extract element IDs and save original values before modifications
    3. Store structured design history in memory_step.observations
    4. Clean up old memory data to prevent memory bloat

    Args:
        memory_step: Current ActionStep from smolagents execution
        agent: The CodeAgent instance with memory.steps access

    Reference:
        Smolagents step callback pattern from memory.mdx#_snippet_3
        Memory cleanup pattern from memory.mdx#_snippet_3 (screenshot removal)
    """
    try:
        # Only process steps that have observations
        if not hasattr(memory_step, "observations") or not memory_step.observations:
            return

        observations = str(memory_step.observations)

        # Detect Direct Parameter Update tasks (from current_task.md workflow)
        if "direct parameter update" in observations.lower():
            logger.debug(f"🔍 Detected Direct Parameter Update in step {memory_step.step_number}")

            # Extract element ID using regex pattern from current_task.md
            element_match = re.search(r"element.*?'(\w+)'", observations)
            if element_match:
                element_id = element_match.group(1)

                # Check if this is the FIRST time we're seeing this element
                original_state = _find_original_element_state(agent, element_id)

                if not original_state:
                    # This is the first modification - save original state
                    logger.info(
                        f"💾 Saving original state for element {element_id} (first modification)"
                    )

                    # Create structured memory record following smolagents patterns
                    memory_record = {
                        "element_id": element_id,
                        "timestamp": datetime.now().isoformat(),
                        "step_number": memory_step.step_number,
                        "action": "first_parameter_update",
                        "step_type": "design_change_original",
                        "observations_snapshot": observations,
                    }

                    # Store in memory step observations with structured format
                    # Following smolagents pattern of adding to observations
                    memory_step.observations += f"\n[MEMORY_ORIGINAL] {json.dumps(memory_record)}"

                else:
                    # Subsequent modification - record the change
                    logger.debug(f"📝 Recording subsequent modification for element {element_id}")

                    change_record = {
                        "element_id": element_id,
                        "timestamp": datetime.now().isoformat(),
                        "step_number": memory_step.step_number,
                        "action": "parameter_update",
                        "step_type": "design_change_update",
                        "original_step": original_state["step_number"] if original_state else None,
                    }

                    memory_step.observations += f"\n[MEMORY_UPDATE] {json.dumps(change_record)}"

        # Also track MCP tool calls that might modify geometry
        elif any(
            mcp_indicator in observations.lower()
            for mcp_indicator in [
                "edit_python3_script",
                "get_python3_script",
                "rg.point3d",
                "rg.vector3d",
            ]
        ):
            logger.debug(f"🔧 Detected MCP geometry modification in step {memory_step.step_number}")

            # Record potential geometry changes
            mcp_record = {
                "timestamp": datetime.now().isoformat(),
                "step_number": memory_step.step_number,
                "action": "mcp_geometry_modification",
                "step_type": "mcp_tool_call",
            }

            memory_step.observations += f"\n[MEMORY_MCP] {json.dumps(mcp_record)}"

        # Memory cleanup - remove old screenshots/data (smolagents best practice)
        # Following exact pattern from smolagents documentation memory.mdx#_snippet_3
        latest_step = memory_step.step_number
        for previous_step in agent.memory.steps:
            # Import ActionStep here to avoid circular imports
            from smolagents import ActionStep

            if (
                isinstance(previous_step, ActionStep)
                and previous_step.step_number <= latest_step - 3
            ):
                # Keep only last 3 steps with full context to save memory
                if hasattr(previous_step, "observations_images"):
                    previous_step.observations_images = None

                # Also clean up very old detailed observations to prevent memory bloat
                if previous_step.step_number <= latest_step - 10:
                    if hasattr(previous_step, "observations") and previous_step.observations:
                        # Keep only memory records, remove verbose observations
                        lines = previous_step.observations.split("\n")
                        memory_lines = [line for line in lines if line.startswith("[MEMORY")]
                        if memory_lines:
                            previous_step.observations = "\n".join(memory_lines)

    except Exception as e:
        logger.error(f"❌ Error in track_design_changes callback: {e}")
        # Don't fail the agent execution, just log the error
        if hasattr(memory_step, "observations"):
            memory_step.observations += f"\n[MEMORY_ERROR] Callback failed: {str(e)}"


def _find_original_element_state(agent: Any, element_id: str) -> Optional[Dict]:
    """
    Helper function to find the original state record for an element.

    Searches through agent.memory.steps to find the first [MEMORY_ORIGINAL] record
    for the specified element_id.

    Args:
        agent: CodeAgent with memory.steps access
        element_id: Element identifier to search for

    Returns:
        Dictionary with original state information, or None if not found
    """
    try:
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
                                    return record
                            except json.JSONDecodeError:
                                continue
        return None

    except Exception as e:
        logger.error(f"❌ Error finding original element state: {e}")
        return None
