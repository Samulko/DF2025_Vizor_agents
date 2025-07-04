"""Geometry Agent Template

Provides tools and a factory to:
 1. Load evaluation criteria from `evaluation_criteria.json`
 2. Convert percentage values to Grasshopper slider integers
 3. Apply slider updates via MCP and bake models in three stages

Follows smolagents patterns with a persistent MCP connection for Grasshopper integration.
"""

from typing import List

from smolagents import CodeAgent, tool
from ..config.model_config import ModelProvider
from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from ..config.settings import settings


# =============================================================================
# STEP 1: CREATE DATA & CONVERSION TOOLS
# Tools to load JSON and convert percentages to slider values
# =============================================================================

@tool
def load_evaluation_criteria(path: str = "evaluation_criteria.json") -> dict:
    """
    Load evaluation criteria JSON mapping criteria names to percentage values.
    Args:
        path: Path to evaluation_criteria.json file.
    Returns:
        A dict mapping criteria names to percentage integers.
    """
    from pathlib import Path
    import json

    file_path = Path(path)
    if not file_path.exists():
        # Attempt to load from project root
        file_path = Path(__file__).parent.parent.parent.parent / path
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found in cwd or project root: {path}")
    content = file_path.read_text(encoding="utf-8")
    data = json.loads(content)
    return data


# @tool
def convert_criteria_to_parameters(criteria: dict) -> dict:
    """
    Convert raw percentage values from JSON into design parameters:
      - X_size (1–10 int)
      - number_of_layers (1–50 int)
      - model_rotation (0.08–0.80 float, 2 decimals)
      - timber_units_per_layer (1–5 int)
    """
    from decimal import Decimal, ROUND_HALF_UP

    mapping = {
        "X_size": (Decimal(1), Decimal(10), "int"),
        "number_of_layers": (Decimal(1), Decimal(50), "int"),
        "model_rotation": (Decimal("0.08"), Decimal("0.80"), "float"),
        "timber_units_per_layer": (Decimal(1), Decimal(5), "int"),
    }

    results = {}
    for key, pct in criteria.items():
        if key not in mapping:
            continue
        min_v, max_v, typ = mapping[key]
        ratio = Decimal(pct) / Decimal(100)
        raw = min_v + ratio * (max_v - min_v)
        if typ == "int":
            val = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            val = max(int(min_v), min(int(max_v), val))
        else:
            # float rotation, two decimal places
            val_dec = raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            val = float(val_dec)
            val = max(float(min_v), min(float(max_v), val))
        results[key] = val
    return results


# =============================================================================
# STEP 2: CREATE THE AGENT TEMPLATE
# This is the MVP agent that students will expand
# =============================================================================


def create_geometry_agent(tools: List = None, model_name: str = "geometry") -> CodeAgent:
    """
    Create a Geometry Agent configured for slider updates and multi-stage bakes.

    This agent provides:
    1. JSON loading of evaluation criteria
    2. Conversion of percentages to slider values
    3. MCP-based updates of Grasshopper slider components and three bake sequences.

    Args:
        tools: Optional initial tools (defaults to load + convert)
        model_name: Model name for LLM configuration (default 'geometry')

    Returns:
        A configured CodeAgent ready for geometry tasks.
    """
    # ESSENTIAL ELEMENT 1: Get the AI model
    # This connects to the language model that powers the agent
    model = ModelProvider.get_model(model_name)

    # ESSENTIAL ELEMENT 2: Prepare the tools
    # Tools are functions the agent can call to perform actions
    agent_tools = tools or []  # Use provided tools or default empty list

    # Add JSON-loading and conversion tools
    agent_tools = [load_evaluation_criteria, convert_criteria_to_parameters] + agent_tools

    # Set up persistent MCP connection and include GH_MCP commands as tools
    stdio_params = StdioServerParameters(
        settings.mcp_stdio_command,
        settings.mcp_stdio_args.split(","),
        env=None
    )
    mcp_connection = MCPAdapt(stdio_params, SmolAgentsAdapter())
    mcp_tools = mcp_connection.__enter__()
    agent_tools += list(mcp_tools)

    # ESSENTIAL ELEMENT 3: Create the agent
    # This is the core smolagents pattern
    agent = CodeAgent(
        tools=agent_tools,  # What the agent can do
        model=model,  # How the agent thinks
        max_steps=20,  # Increased steps for full workflow
        additional_authorized_imports=["math", "json", "decimal", "pathlib"],  # Include needed modules
        name="geometry_agent",  # Agent identifier
        description="Geometry agent for parameter updates and bakes via MCP",  # What this agent does
    )

    # Inject geometry agent system prompt
    from pathlib import Path
    prompt_path = Path(__file__).parent.parent.parent.parent / "system_prompts" / "geometry_agent.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Geometry system prompt not found: {prompt_path}")
    geometry_prompt = prompt_path.read_text(encoding="utf-8")
    agent.prompt_templates["system_prompt"] += "\n\n" + geometry_prompt

    # Persist MCP connection for cleanup
    agent._mcp_connection = mcp_connection

    return agent


# =============================================================================
# STEP 3: EXAMPLE USAGE
# Shows students how to use their agent
# =============================================================================


def demo_geometry_agent():
    """
    Demonstrates how to create and use the geometry agent with a test workflow.
    """
    print("🤖 Creating geometry agent...")
    # Create the agent
    agent = create_geometry_agent()
    print(f"Agent created: {agent.name}")
    print(f"Available tools: {len(agent.tools)}")
    print(f"Max steps: {agent.max_steps}")

    # Test workflow: load JSON, convert, and bake three models
    test_task = (
        "Load the JSON, convert each criterion to slider values, "
        "bake Model 1; then scale×1.2 & bake Model 2; "
        "then scale×0.8 & bake Model 3."
    )
    print(f"\n📝 Running test task: {test_task}")
    result = agent.run(test_task)
    print(f"Result: {result}")

    return agent


# =============================================================================
# HELPER FUNCTIONS
# Additional factories for custom tool sets (optional)
# =============================================================================


def create_agent_with_custom_tools(custom_tools: List) -> CodeAgent:
    """
    Creates an agent with student's custom tools.

    This shows students how to use their own tools with the basic template.

    Example:
        my_tools = [my_custom_tool, another_tool]
        agent = create_agent_with_custom_tools(my_tools)
    """
    return create_geometry_agent(tools=custom_tools)


# =============================================================================
# QUICK START FOR STUDENTS
# =============================================================================

if __name__ == "__main__":
    """
    Students can run this file directly to see the agent working.

    To use in workshop:
    1. Run: python agent_templates.py
    2. See the basic agent in action
    3. Copy the create_geometry_agent() function to start building
    4. Add your own tools and modify as needed
    """
    print("=" * 50)
    print("GEOMETRY AGENT TEMPLATE")
    print("=" * 50)

    # Run the geometry demo
    agent = demo_geometry_agent()
    print("\nModel runs complete.")

    # For custom workflows:
    #  - use `create_geometry_agent()` to instantiate your agent
    #  - call `agent.run(<task_string>)` with a high-level instruction
