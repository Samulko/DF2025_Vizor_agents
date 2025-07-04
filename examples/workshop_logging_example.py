#!/usr/bin/env python3
"""
Example: How to add workshop logging to any agent in 3 lines of code.

This shows students how to easily add comprehensive logging to their agents
that will automatically save traces to workshop_logs/ for analysis.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from smolagents import CodeAgent, tool
from bridge_design_system.config.model_config import ModelProvider
from bridge_design_system.monitoring.workshop_logging import add_workshop_logging


# Example: Create a simple custom agent
@tool
def simple_calculator(operation: str, a: float, b: float) -> float:
    """Simple calculator tool."""
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b if b != 0 else 0
    else:
        return 0


def create_my_custom_agent():
    """Example: Student creates their own agent."""
    model = ModelProvider.get_model("category")  # Use any available model
    
    agent = CodeAgent(
        tools=[simple_calculator],
        model=model,
        name="my_custom_agent",
        description="A simple calculator agent for demonstration",
        max_steps=5
    )
    
    return agent


def main():
    """Demonstrate workshop logging in action."""
    print("🎓 Workshop Logging Example")
    print("=" * 50)
    
    # Step 1: Create your agent normally
    print("1️⃣ Creating custom agent...")
    agent = create_my_custom_agent()
    
    # Step 2: Add workshop logging (JUST 1 LINE!)
    print("2️⃣ Adding workshop logging...")
    add_workshop_logging(agent, "my_custom_agent")
    
    # Step 3: Use your agent normally - logging happens automatically!
    print("3️⃣ Running agent tasks...")
    
    try:
        # Task 1
        result1 = agent.run("Calculate 15 + 27")
        print(f"Result 1: {result1}")
        
        # Task 2  
        result2 = agent.run("What is 8 multiplied by 6?")
        print(f"Result 2: {result2}")
        
        # Task 3
        result3 = agent.run("Divide 100 by 4")
        print(f"Result 3: {result3}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✅ Done! Check workshop_logs/ directory:")
    print("  📁 workshop_logs/agents/my_custom_agent_traces.jsonl")
    print("  📁 workshop_logs/daily/YYYY-MM-DD_traces.jsonl") 
    print("  📁 workshop_logs/daily/YYYY-MM-DD_summary.txt")
    
    print("\n💡 For students: Add logging to ANY agent with just:")
    print("    from bridge_design_system.monitoring.workshop_logging import add_workshop_logging")
    print("    agent = create_your_agent()  # Your existing code")
    print("    add_workshop_logging(agent, 'your_agent_name')  # Add this line!")


if __name__ == "__main__":
    main()