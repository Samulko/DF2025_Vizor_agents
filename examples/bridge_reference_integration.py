"""
Example: Integrating Bridge Reference Agent with Triage System

This example shows how to add the bridge reference agent to the
existing triage system, demonstrating the extensibility of the
multi-agent architecture.

Run this example to see how agents work together to answer
bridge design questions.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bridge_design_system.agents.triage_agent_smolagents import create_triage_system
from src.bridge_design_system.agents.bridge_reference_agent import create_reference_agent_for_triage
from src.bridge_design_system.config.logging_config import setup_logging


def main():
    """Demonstrate bridge reference agent integration."""
    # Setup logging
    setup_logging()
    
    print("=== Bridge Reference Agent Integration Example ===\n")
    
    # Create the triage system
    print("1. Creating triage system...")
    triage = create_triage_system()
    
    # Create the bridge reference agent
    print("2. Creating bridge reference agent...")
    reference_agent = create_reference_agent_for_triage()
    
    # Add the reference agent to the triage system's managed agents
    print("3. Adding reference agent to triage system...")
    if hasattr(triage, 'managed_agents'):
        # For the current implementation, we need to modify the managed_agents list
        triage.managed_agents.append(reference_agent)
        print("   ✓ Bridge reference agent added successfully!\n")
    else:
        print("   ⚠ Note: In production, you would modify create_triage_system() to include the reference agent\n")
    
    # Test queries that use the reference agent
    test_queries = [
        "What are the main specifications of the Golden Gate Bridge?",
        "Find examples of cable-stayed bridges in Europe",
        "Compare the spans of the Brooklyn Bridge and the Manhattan Bridge",
        "I'm designing a suspension bridge for a 600m span. What existing bridges should I study for reference?"
    ]
    
    print("4. Testing bridge reference capabilities:\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 50)
        
        try:
            result = triage.run(query)
            print(f"Response: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
        
        if i < len(test_queries):
            input("Press Enter to continue to the next query...")
            print()
    
    print("\n=== Integration Example Complete ===")
    print("\nKey Takeaways:")
    print("- The bridge reference agent provides real-world bridge data")
    print("- It integrates seamlessly with the existing triage system")
    print("- The triage agent automatically delegates reference queries")
    print("- This pattern can be used to add more specialized agents")


def demonstrate_standalone_usage():
    """Show how to use the bridge reference agent standalone."""
    print("\n=== Standalone Bridge Reference Agent ===\n")
    
    from src.bridge_design_system.agents.bridge_reference_agent import create_bridge_reference_agent
    
    # Create standalone agent
    agent = create_bridge_reference_agent()
    
    # Direct usage
    result = agent.run("What materials are commonly used in arch bridges?")
    print(f"Result: {result}")


if __name__ == "__main__":
    # Check if we have the necessary environment setup
    try:
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your Python environment with: uv venv && .venv\\Scripts\\activate")
        print("2. Installed dependencies with: uv pip install -e .")
        print("3. Set your HF_TOKEN environment variable")
    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying standalone demonstration instead...")
        demonstrate_standalone_usage()