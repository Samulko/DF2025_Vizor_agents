"""
Minimal Agent Template for Workshop Students

This is a simple, working agent template that demonstrates the essential elements
of creating agents with smolagents. Students can use this as their starting point
and expand from here.

This template shows the absolute minimum needed to create a functional agent:
1. Import the necessary smolagents components
2. Create a simple tool using the @tool decorator
3. Initialize the agent with model, tools, and basic configuration
4. Run the agent with a task

All examples follow official smolagents documentation patterns.
"""

from typing import List

from smolagents import CodeAgent, tool
from ..config.model_config import ModelProvider


# =============================================================================
# STEP 1: CREATE A SIMPLE TOOL
# This shows students how to create their own agent tools
# =============================================================================


@tool
def simple_calculator(x: float, y: float, operation: str) -> float:
    """
    A basic calculator tool that demonstrates tool creation for students.

    This shows the essential pattern:
    - Use @tool decorator
    - Clear docstring explaining what the tool does
    - Typed parameters with descriptions
    - Return the result

    Args:
        x: First number
        y: Second number
        operation: "add", "subtract", "multiply", or "divide"

    Returns:
        The calculation result
    """
    if operation == "add":
        return x + y
    elif operation == "subtract":
        return x - y
    elif operation == "multiply":
        return x * y
    elif operation == "divide":
        if y == 0:
            raise ValueError("Cannot divide by zero")
        return x / y
    else:
        raise ValueError(f"Unknown operation: {operation}")


# =============================================================================
# STEP 2: CREATE THE AGENT TEMPLATE
# This is the MVP agent that students will expand
# =============================================================================


def create_basic_agent(tools: List = None, model_name: str = "default") -> CodeAgent:
    """
    Create a basic agent - the minimal viable agent for students.

    This demonstrates the essential smolagents pattern:
    1. Get a model from the model provider
    2. Create a CodeAgent with model and tools
    3. Configure basic settings (max_steps, imports)
    4. Return the ready-to-use agent

    Students can copy this function and modify it for their needs.

    Args:
        tools: List of tools for the agent (optional)
        model_name: Name of the model to use

    Returns:
        A configured CodeAgent ready to use
    """
    # ESSENTIAL ELEMENT 1: Get the AI model
    # This connects to the language model that powers the agent
    model = ModelProvider.get_model(model_name)

    # ESSENTIAL ELEMENT 2: Prepare the tools
    # Tools are functions the agent can call to perform actions
    agent_tools = tools or [simple_calculator]  # Use provided tools or default

    # ESSENTIAL ELEMENT 3: Create the agent
    # This is the core smolagents pattern
    agent = CodeAgent(
        tools=agent_tools,  # What the agent can do
        model=model,  # How the agent thinks
        max_steps=10,  # How many reasoning steps
        additional_authorized_imports=["math", "json"],  # What Python modules it can use
        name="basic_agent",  # Agent identifier
        description="A simple agent for learning purposes",  # What this agent does
    )

    return agent


# =============================================================================
# STEP 3: EXAMPLE USAGE
# Shows students how to use their agent
# =============================================================================


def demo_basic_agent():
    """
    Demonstrates how to create and use the basic agent.

    Students can run this function to see the agent in action,
    then modify it for their own tasks.
    """
    print("🤖 Creating basic agent...")

    # Create the agent
    agent = create_basic_agent()

    # Show agent info
    print(f"Agent created: {agent.name}")
    print(f"Available tools: {len(agent.tools)}")
    print(f"Max steps: {agent.max_steps}")

    # Example task - students can change this
    print("\n📝 Running example task...")

    # This is how you use an agent - just call agent.run() with your task
    result = agent.run("Calculate 15 + 27, then multiply the result by 2")

    print(f"Result: {result}")

    return agent


# =============================================================================
# STEP 4: CUSTOMIZATION HELPERS
# Simple functions to help students modify the template
# =============================================================================


def create_agent_with_custom_tools(custom_tools: List) -> CodeAgent:
    """
    Creates an agent with student's custom tools.

    This shows students how to use their own tools with the basic template.

    Example:
        my_tools = [my_custom_tool, another_tool]
        agent = create_agent_with_custom_tools(my_tools)
    """
    return create_basic_agent(tools=custom_tools)


def create_agent_with_more_steps(max_steps: int = 20) -> CodeAgent:
    """
    Creates an agent with more reasoning steps for complex tasks.

    Students can use this when their tasks need more thinking time.
    """
    model = ModelProvider.get_model("default")

    agent = CodeAgent(
        tools=[simple_calculator],
        model=model,
        max_steps=max_steps,  # More steps for complex reasoning
        additional_authorized_imports=["math", "json", "datetime"],
        name="extended_agent",
        description="Agent with more reasoning steps",
    )

    return agent


# =============================================================================
# QUICK START FOR STUDENTS
# =============================================================================

if __name__ == "__main__":
    """
    Students can run this file directly to see the agent working.

    To use in workshop:
    1. Run: python agent_templates.py
    2. See the basic agent in action
    3. Copy the create_basic_agent() function to start building
    4. Add your own tools and modify as needed
    """
    print("=" * 50)
    print("SMOLAGENTS BASIC AGENT TEMPLATE")
    print("=" * 50)

    # Run the demonstration
    agent = demo_basic_agent()

    print("\n" + "=" * 50)
    print("NEXT STEPS FOR STUDENTS:")
    print("=" * 50)
    print("1. Copy the create_basic_agent() function")
    print("2. Create your own tools using @tool decorator")
    print("3. Modify the agent configuration for your needs")
    print("4. Test with agent.run('your task here')")
    print("5. Expand with more tools and capabilities")
    print("\nHappy coding! 🚀")
