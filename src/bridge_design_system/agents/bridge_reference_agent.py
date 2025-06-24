"""
Bridge Reference Agent for searching real-world bridge information.

This agent specializes in finding information about existing bridges,
their specifications, and engineering details. It serves as a knowledge
base for the bridge design system.

This is an educational example showing how specialized agents can be
created and integrated into the larger system.
"""


from smolagents import ToolCallingAgent, WebSearchTool, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider

logger = get_logger(__name__)


@tool
def search_bridge_info(bridge_name: str) -> str:
    """
    Search for detailed information about a specific bridge.
    
    Args:
        bridge_name: The name of the bridge to search for
    """
    search = WebSearchTool()
    query = f"{bridge_name} bridge specifications history engineering length height type material"
    return search(query)


@tool
def find_bridges_by_type(bridge_type: str, region: str = "worldwide") -> str:
    """
    Find examples of bridges of a specific type in a given region.
    
    Args:
        bridge_type: Type of bridge (e.g., suspension, arch, beam, cable-stayed, truss)
        region: Geographic region to search in (default: worldwide)
    """
    search = WebSearchTool()
    query = f"famous {bridge_type} bridges {region} examples list"
    return search(query)


@tool
def compare_bridge_spans(bridge1: str, bridge2: str) -> str:
    """
    Compare the main span lengths of two bridges.
    
    Args:
        bridge1: Name of the first bridge
        bridge2: Name of the second bridge
    """
    search = WebSearchTool()
    info1 = search(f"{bridge1} bridge main span length meters")
    info2 = search(f"{bridge2} bridge main span length meters")
    
    return f"Information about {bridge1}:\n{info1[:300]}\n\nInformation about {bridge2}:\n{info2[:300]}"


@tool
def search_bridge_materials(bridge_type: str, material_focus: str = "") -> str:
    """
    Search for information about materials used in specific bridge types.
    
    Args:
        bridge_type: Type of bridge (suspension, arch, beam, etc.)
        material_focus: Optional specific material to focus on (steel, concrete, etc.)
    """
    search = WebSearchTool()
    
    if material_focus:
        query = f"{bridge_type} bridge {material_focus} material properties usage"
    else:
        query = f"{bridge_type} bridge construction materials steel concrete composite"
    
    return search(query)


def create_bridge_reference_agent(model_name: str = "reference") -> ToolCallingAgent:
    """
    Create a bridge reference agent for searching real-world bridge information.
    
    This agent can be used standalone or integrated into the triage system
    as a managed agent.
    
    Args:
        model_name: Model configuration name from settings
        
    Returns:
        ToolCallingAgent configured for bridge reference tasks
    """
    # Get model
    model = ModelProvider.get_model(model_name)
    
    # Collect all bridge reference tools
    bridge_tools = [
        search_bridge_info,
        find_bridges_by_type,
        compare_bridge_spans,
        search_bridge_materials,
        WebSearchTool()  # General search as fallback
    ]
    
    # Create the agent
    agent = ToolCallingAgent(
        tools=bridge_tools,
        model=model,
        name="bridge_reference_agent",
        description="Searches for information about existing bridges, their types, "
                   "specifications, and engineering details. Use this when you need "
                   "reference information about real bridges.",
        max_steps=5
    )
    
    logger.info("Created bridge reference agent")
    return agent


# Example of how to integrate with triage system
def create_reference_agent_for_triage() -> ToolCallingAgent:
    """
    Create a bridge reference agent configured for use in the triage system.
    
    This is a convenience function that creates the agent with settings
    optimized for integration with the managed agents pattern.
    
    Returns:
        ToolCallingAgent ready for use as a managed agent
    """
    return create_bridge_reference_agent(model_name="reference")