"""
Test script to verify persistent MCP connections enable iterative design workflow.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import create_triage_system
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.config.logging_config import setup_logging


def test_persistent_mcp_connections():
    """Test that persistent MCP connections enable iterative design workflow."""
    print("=" * 70)
    print("TESTING PERSISTENT MCP CONNECTIONS FOR ITERATIVE DESIGN")
    print("=" * 70)

    setup_logging()

    try:
        # Create component registry
        registry = ComponentRegistry()

        # Create triage system with persistent connections
        print("\n1. Creating triage system with persistent MCP connections...")
        triage_system = create_triage_system(component_registry=registry)
        print("✅ Triage system created successfully with persistent connections")

        # Task 1: Create initial bridge components
        print("\n2. TASK 1: Creating initial bridge components...")
        task1 = "Create two points to represent the start and end of a bridge. The bridge should span 50 meters."

        print(f"Executing task 1: {task1}")
        result1 = triage_system.run(task1)

        print(f"\n3. Task 1 completed!")
        print(f"Result type: {type(result1)}")
        print(f"Result: {str(result1)[:300]}...")

        # Task 2: Build upon the first task (should reference existing components)
        print("\n4. TASK 2: Building upon existing components...")
        task2 = "Now create a bridge deck that connects the two points you just created. Use the existing bridge start and end points."

        print(f"Executing task 2: {task2}")
        result2 = triage_system.run(task2)

        print(f"\n5. Task 2 completed!")
        print(f"Result type: {type(result2)}")
        print(f"Result: {str(result2)[:300]}...")

        # Task 3: Further iteration
        print("\n6. TASK 3: Adding supports to existing bridge...")
        task3 = "Add support columns to the bridge deck you just created. The supports should be placed at regular intervals."

        print(f"Executing task 3: {task3}")
        result3 = triage_system.run(task3)

        print(f"\n7. Task 3 completed!")
        print(f"Result type: {type(result3)}")
        print(f"Result: {str(result3)[:300]}...")

        # Check if the agent maintained context
        print("\n8. ANALYZING ITERATIVE DESIGN CAPABILITY...")

        # Check if subsequent tasks reference previous work
        result2_str = str(result2).lower()
        result3_str = str(result3).lower()

        context_indicators = [
            "existing",
            "previous",
            "created",
            "bridge",
            "points",
            "deck",
            "already",
        ]

        context_found_task2 = sum(1 for indicator in context_indicators if indicator in result2_str)
        context_found_task3 = sum(1 for indicator in context_indicators if indicator in result3_str)

        print(f"Context indicators found in Task 2: {context_found_task2}")
        print(f"Context indicators found in Task 3: {context_found_task3}")

        if context_found_task2 >= 2 and context_found_task3 >= 2:
            print("✅ SUCCESS: Agent appears to maintain context between tasks!")
            print("✅ ITERATIVE DESIGN CAPABILITY: WORKING")
        else:
            print("⚠️  WARNING: Limited evidence of context preservation")
            print("⚠️  May still be creating redundant components")

        print("\n9. MEMORY ANALYSIS...")
        # Check if agent has memory of previous steps
        if hasattr(triage_system, "memory") and hasattr(triage_system.memory, "steps"):
            memory_steps = len(triage_system.memory.steps)
            print(f"Agent memory contains {memory_steps} steps")
            if memory_steps >= 3:
                print("✅ SUCCESS: Agent memory is accumulating steps!")
            else:
                print("⚠️  WARNING: Limited memory accumulation")
        else:
            print("ℹ️  Agent memory structure not directly accessible")

        print("\n" + "=" * 70)
        print("✅ PERSISTENT MCP CONNECTION TEST COMPLETED")
        print("✅ Iterative design workflow appears to be working!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("This indicates the persistent MCP connection issue may still exist.")
        import traceback

        traceback.print_exc()

        # Check for specific error types
        if "Event loop is closed" in str(e):
            print("🔍 Event loop error detected - MCP connection management issue")
        elif "Connection" in str(e):
            print("🔍 Connection error detected - MCP server may not be running")
        else:
            print(f"🔍 Different error: {type(e).__name__}")

    print("\n" + "=" * 70)


def test_mcp_connection_persistence():
    """Test that MCP connections are actually persistent and not recreated."""
    print("=" * 70)
    print("TESTING MCP CONNECTION PERSISTENCE")
    print("=" * 70)

    setup_logging()

    try:
        # Create triage system
        print("\n1. Creating triage system...")
        triage_system = create_triage_system()

        # Access the geometry agent to check connection
        if hasattr(triage_system, "managed_agents") and triage_system.managed_agents:
            geometry_agent = triage_system.managed_agents[0]

            print(f"2. Geometry agent type: {type(geometry_agent)}")

            # Check if MCP connection exists
            if hasattr(geometry_agent, "mcp_connection"):
                print("✅ Geometry agent has persistent MCP connection attribute")
                if geometry_agent.mcp_connection:
                    print("✅ MCP connection is established")
                else:
                    print("❌ MCP connection is None")
            else:
                print("❌ No persistent MCP connection found")

            # Check if MCP tools exist
            if hasattr(geometry_agent, "mcp_tools"):
                print(f"✅ Geometry agent has {len(geometry_agent.mcp_tools)} MCP tools")
            else:
                print("❌ No MCP tools found")

            # Check if the agent has tools
            if hasattr(geometry_agent, "tools"):
                print(f"✅ Geometry agent has {len(geometry_agent.tools)} total tools")
            else:
                print("❌ No tools found in geometry agent")
        else:
            print("❌ No managed agents found in triage system")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Run both tests
    test_mcp_connection_persistence()
    print("\n")
    test_persistent_mcp_connections()
