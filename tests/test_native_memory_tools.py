"""
Test script to validate native memory tools implementation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import create_triage_system
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.config.logging_config import setup_logging


def test_native_memory_tools():
    """Test that native memory tools are properly integrated."""
    print("=" * 70)
    print("TESTING NATIVE MEMORY TOOLS INTEGRATION")
    print("=" * 70)
    
    setup_logging()
    
    try:
        # Create component registry
        registry = ComponentRegistry()
        
        # Create triage system with native memory tools
        print("\n1. Creating triage system with native memory tools...")
        triage_system = create_triage_system(component_registry=registry)
        print("✅ Triage system created successfully")
        
        # Check if native memory tools are available
        print("\n2. Checking for native memory tools...")
        tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in triage_system.tools]
        
        expected_tools = [
            'get_geometry_agent_memory',
            'search_geometry_agent_memory', 
            'extract_components_from_geometry_memory'
        ]
        
        found_tools = []
        for expected_tool in expected_tools:
            if any(expected_tool in tool_name for tool_name in tool_names):
                found_tools.append(expected_tool)
                print(f"✅ Found tool: {expected_tool}")
            else:
                print(f"❌ Missing tool: {expected_tool}")
        
        if len(found_tools) == len(expected_tools):
            print(f"\n✅ All {len(expected_tools)} native memory tools successfully integrated!")
        else:
            print(f"\n⚠️  Only {len(found_tools)}/{len(expected_tools)} native memory tools found")
        
        # Test basic geometry agent access
        print("\n3. Testing geometry agent access...")
        if hasattr(triage_system, 'managed_agents'):
            managed_agents = triage_system.managed_agents
            print(f"Managed agents type: {type(managed_agents)}")
            print(f"Managed agents content: {managed_agents}")
            
            if managed_agents:
                if isinstance(managed_agents, list) and len(managed_agents) > 0:
                    geometry_agent = managed_agents[0]
                elif isinstance(managed_agents, dict) and managed_agents:
                    geometry_agent = list(managed_agents.values())[0]
                else:
                    print("❌ Unexpected managed_agents structure")
                    geometry_agent = None
                
                if geometry_agent:
                    print(f"✅ Geometry agent found: {type(geometry_agent).__name__}")
                    
                    # Check if it has memory attribute
                    if hasattr(geometry_agent, 'memory'):
                        print("✅ Geometry agent has memory attribute")
                        if hasattr(geometry_agent.memory, 'steps'):
                            print(f"✅ Memory steps available: {len(geometry_agent.memory.steps)} steps")
                        else:
                            print("⚠️  Memory steps attribute not found")
                    else:
                        print("❌ Geometry agent missing memory attribute")
            else:
                print("❌ No managed agents found")
        else:
            print("❌ managed_agents attribute not found")
        
        print("\n" + "=" * 70)
        print("✅ NATIVE MEMORY TOOLS INTEGRATION TEST COMPLETED")
        print("Ready to test with real conversation!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_native_memory_tools()