"""Bridge Design System Agents."""

from .geometry_agent_smolagents import create_geometry_agent
from .triage_agent_smolagents import TriageSystemWrapper as TriageAgent

from .category_smolagent import create_category_material_agent, demo_level_checking  # 或者对应函数名


__all__ = [
    "TriageAgent",
    "create_geometry_agent",
    "create_material_agent",
    "demo_material_agent",
]
