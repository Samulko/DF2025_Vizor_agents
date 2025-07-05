"""Geometry Agent Template

Provides tools and a factory to:
 1. Load evaluation criteria from `evaluation_criteria.json`
 2. Convert percentage values to Grasshopper slider integers
 3. Apply slider updates via MCP and bake models in three stages

Follows smolagents patterns with a persistent MCP connection for Grasshopper integration.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings
from ..memory import track_design_changes

logger = get_logger(__name__)


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


@tool
def load_design_profile(path: str = "src/bridge_design_system/agents/design_profile.json") -> dict:
    """
    Load design profile JSON containing user preferences and design constraints.
    
    Args:
        path: Path to design_profile.json file (defaults to agents directory)
    
    Returns:
        A dict containing design profile preferences including ratings for:
        - self_weight: Weight preference rating (0-100)
        - complexity: Complexity preference rating (0-100) 
        - storage: Storage preference rating (0-100)
    """
    from pathlib import Path
    import json

    file_path = Path(path)
    if not file_path.exists():
        # Try relative to current file location
        file_path = Path(__file__).parent / "design_profile.json"
        if not file_path.exists():
            # Try project root
            file_path = Path(__file__).parent.parent.parent.parent / path
            if not file_path.exists():
                raise FileNotFoundError(f"Design profile JSON file not found: {path}")
    
    content = file_path.read_text(encoding="utf-8")
    data = json.loads(content)
    return data



# =============================================================================
# STEP 2: CREATE THE DESIGN AGENT CLASS
# Following the rational_smolagents_complete.py pattern
# =============================================================================


class DesignSmolagent:
    """
    Specialized smolagent for bridge design parameter updates and geometry creation.

    This agent connects to the MCP server to access Grasshopper components and
    performs design operations including parameter conversion and model baking.
    """

    def __init__(self, model_name: str = "design", **kwargs):
        """
        Initialize the design smolagent with MCP connection and custom tools.

        Args:
            model_name: Model configuration name from settings
            **kwargs: Additional arguments for extensibility
        """
        self.model_name = model_name
        
        # Agent identification
        self.name = "design_agent"
        self.description = "Handles bridge design parameters and geometry creation via MCP connection"
        
        # Initialize model
        self.model = ModelProvider.get_model(model_name, temperature=0.1)
        
        # MCP server configuration
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command,
            args=settings.mcp_stdio_args.split(","),
            env=None
        )
        
        # Establish MCP connection
        logger.info("Establishing MCP connection for design agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(f"MCP connection established with {len(self.mcp_tools)} tools")
            
            # Use MCP tools plus our custom design tools
            all_tools = list(self.mcp_tools)
            all_tools.extend([load_evaluation_criteria, load_design_profile])
            
            # Add native smolagents memory tracking callback
            step_callbacks = [track_design_changes]
            
            # Create the ToolCallingAgent
            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=20,
                name="design_agent",
                description=self.description,
                step_callbacks=step_callbacks,
            )
            
            # Add specialized system prompt
            custom_prompt = get_design_system_prompt()
            self.agent.prompt_templates["system_prompt"] = (
                self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            )
            
            logger.info("Design smolagent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize design smolagent: {e}")
            raise RuntimeError(f"Design smolagent initialization failed: {e}")

    def run(self, task: str) -> Any:
        """
        Execute design task including parameter conversion and geometry creation.

        Args:
            task: Task description for design operations

        Returns:
            Result of the agent execution
        """
        logger.info(f"Executing design task: {task[:100]}...")
        
        try:
            result = self.agent.run(task)
            logger.info("Design task completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Design task failed: {e}")
            raise RuntimeError(f"Design smolagent execution failed: {e}")

    def __del__(self):
        """Clean up MCP connection when agent is destroyed."""
        try:
            if hasattr(self, "mcp_connection") and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("MCP connection closed for design smolagent")
        except Exception as e:
            logger.warning(f"Error closing MCP connection: {e}")


def get_design_system_prompt() -> str:
    """Get custom system prompt for design agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "geometry_agent.md"
    
    if not prompt_path.exists():
        # Return a default prompt if file doesn't exist
        return """
You are a specialized bridge design agent focused on parameter conversion and geometry creation with design profile integration.

Your primary tasks:
1. Load evaluation criteria from JSON files using load_evaluation_criteria
2. Load design profile preferences using load_design_profile 
3. Use MCP tools to update Grasshopper sliders and bake 3D models
4. Handle multi-stage design workflows with parameter scaling
5. Ensure all designs comply with design_profile.json preferences

When working with design tasks:
1. Always start by loading the design profile with load_design_profile to understand user preferences
2. Load evaluation criteria with load_evaluation_criteria when needed
3. Consider design profile ratings (self_weight, complexity, storage) in all design decisions
4. Use MCP tools to update Grasshopper and create geometry that aligns with user preferences
5. Verify results meet both technical requirements and design profile constraints

Design Profile Integration:
- self_weight rating: Consider weight implications in design choices
- complexity rating: Balance design sophistication with user preference
- storage rating: Consider storage and transportation requirements

Be systematic, precise, and thorough in your design operations while always respecting the user's design profile preferences.
        """.strip()
    
    return prompt_path.read_text(encoding="utf-8")


def create_geometry_agent(tools: List = None, model_name: str = "design", **kwargs) -> ToolCallingAgent:
    """
    Factory function for creating design smolagent instances.

    Args:
        tools: Optional additional tools (ignored, MCP tools are auto-added)
        model_name: Model configuration name from settings
        **kwargs: Additional arguments for agent configuration

    Returns:
        Configured ToolCallingAgent for design operations
    """
    logger.info("Creating design smolagent...")
    
    wrapper = DesignSmolagent(model_name=model_name, **kwargs)
    
    # Extract the internal ToolCallingAgent
    internal_agent = wrapper.agent
    
    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper
    
    # Add workshop logging
    from ..monitoring.workshop_logging import add_workshop_logging
    add_workshop_logging(internal_agent, "design_agent")
    
    logger.info("Design smolagent created successfully")
    return internal_agent


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


def create_agent_with_custom_tools(custom_tools: List) -> ToolCallingAgent:
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
