# Building a Rational Smolagent: Step-by-Step Tutorial

This tutorial guides you through implementing a specialized AI agent for bridge element level validation and correction. The agent will connect to Grasshopper via MCP (Model Context Protocol) and perform engineering validation tasks.

## Learning Objectives

By the end of this tutorial, you will:
- Understand how to create a smolagent with MCP integration
- Learn to implement custom tools for specialized tasks
- Build an agent that validates and corrects bridge element alignment
- Understand the connection between AI agents and CAD software

## Prerequisites

- Basic Python knowledge
- Understanding of object-oriented programming
- Familiarity with the project structure
- MCP server running (see CLAUDE.md for setup)

---

## Step 1: Understanding the Architecture

The Rational Smolagent consists of several key components:

```
RationalSmolagent
├── MCP Connection (communicates with Grasshopper)
├── Custom Analysis Tool (analyzes element levels)
├── ToolCallingAgent (handles AI reasoning and tool execution)
└── System Prompt (provides specialized instructions)
```

**What we're building**: An agent that can read bridge element parameters from Grasshopper, check if elements are horizontal (Z-component = 0), and correct them if needed.

---

## Step 2: Add Required Imports

First, let's add all the necessary imports to `rational_smolagents.py`:

```python
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter
from smolagents import ToolCallingAgent, tool

from ..config.logging_config import get_logger
from ..config.model_config import ModelProvider
from ..config.settings import settings

logger = get_logger(__name__)
```

**Explanation**:
- `mcp` and `mcpadapt`: Handle connection to Grasshopper
- `smolagents`: Core AI agent framework
- `tool`: Decorator for creating custom agent tools
- Local imports: Project configuration and logging

---

## Step 3: Initialize the Agent Class

Replace the `__init__` method with this implementation:

```python
def __init__(self, model_name: str = "rational", **kwargs):
    """
    Initialize the rational smolagent with MCP connection and custom tools.

    Args:
        model_name: Model configuration name from settings
        **kwargs: Additional arguments for extensibility
    """
    self.model_name = model_name
    
    # Agent identification
    self.name = "rational_agent"
    self.description = "Validates and corrects bridge element levels for proper horizontal alignment"
    
    # Initialize model
    self.model = ModelProvider.get_model(model_name, temperature=0.1)
    
    # MCP server configuration
    self.stdio_params = StdioServerParameters(
        command=settings.mcp_stdio_command,
        args=settings.mcp_stdio_args.split(","),
        env=None
    )
    
    # Establish MCP connection
    logger.info("Establishing MCP connection for rational agent...")
    try:
        self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
        self.mcp_tools = self.mcp_connection.__enter__()
        logger.info(f"MCP connection established with {len(self.mcp_tools)} tools")
        
        # Use MCP tools plus one custom analysis tool
        all_tools = list(self.mcp_tools)
        all_tools.append(self._create_analysis_tool())
        
        # Create the ToolCallingAgent
        self.agent = ToolCallingAgent(
            tools=all_tools,
            model=self.model,
            max_steps=8,
            name="rational_agent",
            description=self.description,
        )
        
        # Add specialized system prompt from file
        custom_prompt = get_rational_system_prompt()
        self.agent.prompt_templates["system_prompt"] = (
            self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
        )
        
        logger.info("Rational smolagent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize rational smolagent: {e}")
        raise RuntimeError(f"Rational smolagent initialization failed: {e}")
```

**Key concepts**:
- **MCP Connection**: Establishes communication with Grasshopper
- **Tool Collection**: Combines MCP tools with our custom analysis tool
- **ToolCallingAgent**: The core AI agent that reasons and executes tools
- **System Prompt**: Specialized instructions for engineering tasks

---

## Step 4: Implement Task Execution

Replace the `run` method:

```python
def run(self, task: str) -> Any:
    """
    Execute level checking and correction task.

    Args:
        task: Task description for level validation or correction

    Returns:
        Result of the agent execution
    """
    logger.info(f"Executing level checking task: {task[:100]}...")
    
    try:
        result = self.agent.run(task)
        logger.info("Level checking task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Level checking task failed: {e}")
        raise RuntimeError(f"Rational smolagent execution failed: {e}")
```

**What this does**: 
- Logs the task for debugging
- Delegates execution to the ToolCallingAgent
- Handles errors gracefully with informative messages

---

## Step 5: Create the Custom Analysis Tool

This is the most important part - our specialized tool for analyzing bridge elements:

```python
def _create_analysis_tool(self):
    """
    Create custom analysis tool for structured element level assessment.

    Returns:
        Custom tool function for level analysis
    """
    
    @tool
    def analyze_element_level(element_id: str) -> str:
        """
        Analyze the level status of a bridge element to determine if it's horizontal.

        This tool provides structured analysis of element orientation and generates
        a report on whether the element needs level correction.

        Args:
            element_id: Element identifier to analyze (e.g., "021", "022")

        Returns:
            Analysis report of element's horizontal alignment status
        """
        try:
            logger.info(f"Analyzing level status for element {element_id}")
            
            return f"""
LEVEL ANALYSIS REPORT - Element {element_id}:
============================================
Element ID: {element_id}
Analysis Focus: Direction vector Z-component validation
Required State: Z-component = 0 for horizontal alignment

Next Steps:
1. Use get_python3_script to read current element parameters
2. Extract direction vector values from the code
3. Check if Z-component is zero (horizontal)
4. If not zero, use edit_python3_script to correct the direction vector
5. Verify correction with get_python3_script_errors

Status: Ready for parameter extraction and validation
            """.strip()
            
        except Exception as e:
            return f"Error analyzing element {element_id}: {str(e)}"
    
    return analyze_element_level
```

**Engineering Logic**:
- **Direction Vector**: Bridge elements have direction vectors (X, Y, Z)
- **Horizontal Requirement**: For level elements, Z-component must be 0
- **Workflow**: Read → Analyze → Correct → Verify

---

## Step 6: Implement Cleanup

Replace the `__del__` method:

```python
def __del__(self):
    """Clean up MCP connection when agent is destroyed."""
    try:
        if hasattr(self, "mcp_connection") and self.mcp_connection:
            self.mcp_connection.__exit__(None, None, None)
            logger.info("MCP connection closed for rational smolagent")
    except Exception as e:
        logger.warning(f"Error closing MCP connection: {e}")
```

**Important**: Always clean up connections to prevent resource leaks.

---

## Step 7: Load System Prompt

Replace the `get_rational_system_prompt` function:

```python
def get_rational_system_prompt() -> str:
    """Get custom system prompt for rational agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "rational_agent.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")
    
    return prompt_path.read_text(encoding="utf-8")
```

**Purpose**: Loads specialized instructions that teach the agent about bridge engineering principles.

---

## Step 8: Create Factory Function

Replace the `create_rational_agent` function:

```python
def create_rational_agent(model_name: str = "rational", **kwargs) -> ToolCallingAgent:
    """
    Factory function for creating rational smolagent instances.

    Args:
        model_name: Model configuration name from settings
        **kwargs: Additional arguments for agent configuration

    Returns:
        Configured ToolCallingAgent for level checking operations
    """
    logger.info("Creating rational smolagent...")
    
    wrapper = RationalSmolagent(model_name=model_name, **kwargs)
    
    # Extract the internal ToolCallingAgent
    internal_agent = wrapper.agent
    
    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper
    
    logger.info("Rational smolagent created successfully")
    return internal_agent
```

**Design Pattern**: Factory pattern for clean object creation and dependency injection.

---

## Step 9: Add Demonstration Function

Replace the `demo_level_checking` function:

```python
def demo_level_checking():
    """
    Demonstration function showing basic level checking operations.

    This function creates an agent instance and runs a simple validation task
    to demonstrate the level checking capabilities.
    """
    print("Starting rational smolagent demonstration...")
    
    try:
        agent = create_rational_agent()
        
        demo_task = "Analyze the current bridge elements and identify any that need level correction"
        result = agent.run(demo_task)
        
        print("Demonstration completed successfully")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Demonstration failed: {e}")
        raise
```

---

## Step 10: Testing Your Implementation

1. **Test the agent**:
```bash
uv run python -m bridge_design_system.agents.rational_smolagents
```

2. **Expected output**:
- MCP connection established
- Agent created successfully
- Demo task executed
- Analysis report generated

---

## Understanding the Workflow

When you run a task like "Check element 021 for horizontal alignment":

1. **Agent receives task** → Understands it needs to check element levels
2. **Calls analyze_element_level("021")** → Gets structured analysis plan
3. **Uses get_python3_script** → Reads current element parameters from Grasshopper
4. **Analyzes direction vector** → Checks if Z-component equals 0
5. **If not level**: Uses edit_python3_script to correct it
6. **Verifies correction** → Ensures changes were applied correctly

---

## Advanced Topics

### Custom Tool Development
You can extend the agent with additional tools:

```python
@tool
def validate_structural_integrity(element_id: str) -> str:
    """Check if element meets structural requirements."""
    # Implementation here
    pass
```

### Error Handling Strategies
- Always wrap MCP calls in try-catch blocks
- Provide meaningful error messages for debugging
- Log important steps for troubleshooting

### Performance Optimization
- Use appropriate temperature settings (0.1 for precise engineering tasks)
- Limit max_steps to prevent infinite loops
- Cache frequently accessed data

---

## Common Issues and Solutions

**Problem**: "MCP connection failed"
**Solution**: Ensure MCP server is running on port 8001

**Problem**: "System prompt file not found"
**Solution**: Create `system_prompts/rational_agent.md` with engineering instructions

**Problem**: "Tool not found"
**Solution**: Verify all required tools are available in MCP server

---

## Next Steps

1. **Extend functionality**: Add more engineering validation tools
2. **Improve prompts**: Refine system prompts for better performance
3. **Add visualization**: Create tools that generate reports or diagrams
4. **Integration**: Connect with other agents in the system

---

## Complete Implementation

Here's the complete working code for reference:

```python
"""
Rational Smolagent - Level Checking and Correction Agent

This agent validates and corrects bridge element levels to ensure proper horizontal alignment.
It integrates with the MCP-connected Grasshopper environment to access and modify component parameters.

The agent focuses on a specific engineering task: ensuring all bridge elements have correct
horizontal orientation by checking and adjusting their direction vectors.
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

logger = get_logger(__name__)


class RationalSmolagent:
    """
    Specialized smolagent for bridge element level validation and correction.

    This agent connects to the MCP server to access Grasshopper components and
    performs level checking operations to ensure elements are properly horizontal.
    """

    def __init__(self, model_name: str = "rational", **kwargs):
        """
        Initialize the rational smolagent with MCP connection and custom tools.

        Args:
            model_name: Model configuration name from settings
            **kwargs: Additional arguments for extensibility
        """
        self.model_name = model_name
        
        # Agent identification
        self.name = "rational_agent"
        self.description = "Validates and corrects bridge element levels for proper horizontal alignment"
        
        # Initialize model
        self.model = ModelProvider.get_model(model_name, temperature=0.1)
        
        # MCP server configuration
        self.stdio_params = StdioServerParameters(
            command=settings.mcp_stdio_command,
            args=settings.mcp_stdio_args.split(","),
            env=None
        )
        
        # Establish MCP connection
        logger.info("Establishing MCP connection for rational agent...")
        try:
            self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
            self.mcp_tools = self.mcp_connection.__enter__()
            logger.info(f"MCP connection established with {len(self.mcp_tools)} tools")
            
            # Use MCP tools plus one custom analysis tool
            all_tools = list(self.mcp_tools)
            all_tools.append(self._create_analysis_tool())
            
            # Create the ToolCallingAgent
            self.agent = ToolCallingAgent(
                tools=all_tools,
                model=self.model,
                max_steps=8,
                name="rational_agent",
                description=self.description,
            )
            
            # Add specialized system prompt from file
            custom_prompt = get_rational_system_prompt()
            self.agent.prompt_templates["system_prompt"] = (
                self.agent.prompt_templates["system_prompt"] + "\n\n" + custom_prompt
            )
            
            logger.info("Rational smolagent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize rational smolagent: {e}")
            raise RuntimeError(f"Rational smolagent initialization failed: {e}")

    def run(self, task: str) -> Any:
        """
        Execute level checking and correction task.

        Args:
            task: Task description for level validation or correction

        Returns:
            Result of the agent execution
        """
        logger.info(f"Executing level checking task: {task[:100]}...")
        
        try:
            result = self.agent.run(task)
            logger.info("Level checking task completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Level checking task failed: {e}")
            raise RuntimeError(f"Rational smolagent execution failed: {e}")

    def _create_analysis_tool(self):
        """
        Create custom analysis tool for structured element level assessment.

        Returns:
            Custom tool function for level analysis
        """
        
        @tool
        def analyze_element_level(element_id: str) -> str:
            """
            Analyze the level status of a bridge element to determine if it's horizontal.

            This tool provides structured analysis of element orientation and generates
            a report on whether the element needs level correction.

            Args:
                element_id: Element identifier to analyze (e.g., "021", "022")

            Returns:
                Analysis report of element's horizontal alignment status
            """
            try:
                logger.info(f"Analyzing level status for element {element_id}")
                
                return f"""
LEVEL ANALYSIS REPORT - Element {element_id}:
============================================
Element ID: {element_id}
Analysis Focus: Direction vector Z-component validation
Required State: Z-component = 0 for horizontal alignment

Next Steps:
1. Use get_python3_script to read current element parameters
2. Extract direction vector values from the code
3. Check if Z-component is zero (horizontal)
4. If not zero, use edit_python3_script to correct the direction vector
5. Verify correction with get_python3_script_errors

Status: Ready for parameter extraction and validation
                """.strip()
                
            except Exception as e:
                return f"Error analyzing element {element_id}: {str(e)}"
        
        return analyze_element_level

    def __del__(self):
        """Clean up MCP connection when agent is destroyed."""
        try:
            if hasattr(self, "mcp_connection") and self.mcp_connection:
                self.mcp_connection.__exit__(None, None, None)
                logger.info("MCP connection closed for rational smolagent")
        except Exception as e:
            logger.warning(f"Error closing MCP connection: {e}")


def get_rational_system_prompt() -> str:
    """Get custom system prompt for rational agent from file."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    prompt_path = project_root / "system_prompts" / "rational_agent.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file not found: {prompt_path}")
    
    return prompt_path.read_text(encoding="utf-8")


def create_rational_agent(model_name: str = "rational", **kwargs) -> ToolCallingAgent:
    """
    Factory function for creating rational smolagent instances.

    Args:
        model_name: Model configuration name from settings
        **kwargs: Additional arguments for agent configuration

    Returns:
        Configured ToolCallingAgent for level checking operations
    """
    logger.info("Creating rational smolagent...")
    
    wrapper = RationalSmolagent(model_name=model_name, **kwargs)
    
    # Extract the internal ToolCallingAgent
    internal_agent = wrapper.agent
    
    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper
    
    logger.info("Rational smolagent created successfully")
    return internal_agent


def demo_level_checking():
    """
    Demonstration function showing basic level checking operations.

    This function creates an agent instance and runs a simple validation task
    to demonstrate the level checking capabilities.
    """
    print("Starting rational smolagent demonstration...")
    
    try:
        agent = create_rational_agent()
        
        demo_task = "Analyze the current bridge elements and identify any that need level correction"
        result = agent.run(demo_task)
        
        print("Demonstration completed successfully")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    demo_level_checking()
```

This tutorial provides a comprehensive guide to building a specialized AI agent that can validate and correct bridge element alignment through integration with CAD software. The step-by-step approach ensures understanding of both the technical implementation and the engineering principles involved.

---

## Step 11: Making the Rational Agent a Managed Agent

Once you've completed building your rational agent, the next step is integrating it into the triage system as a managed agent. This enables automatic delegation and coordination with other specialized agents.

### Understanding Managed Agents

The smolagents framework uses a **managed_agents** pattern where:

1. **Manager Agent** (triage): Coordinates tasks and delegates to specialists
2. **Managed Agents** (geometry, rational, etc.): Execute specialized tasks
3. **Native Delegation**: Smolagents handles task routing automatically
4. **Memory Sharing**: Agents can transfer context via memory.steps

### Integration Steps

#### Step 11.1: Verify Factory Function Pattern

Your rational agent should already follow this pattern:

```python
def create_rational_agent(model_name: str = "rational", **kwargs) -> ToolCallingAgent:
    """Factory function creating a ToolCallingAgent suitable for managed_agents."""
    wrapper = RationalSmolagent(model_name=model_name, **kwargs)
    internal_agent = wrapper.agent
    
    # Store wrapper reference for resource cleanup
    internal_agent._wrapper = wrapper
    
    return internal_agent  # Return ToolCallingAgent directly
```

**Key Requirements:**
- Returns `ToolCallingAgent` (not wrapper class)
- Stores wrapper reference for cleanup
- Accepts `monitoring_callback` parameter

#### Step 11.2: Integrate into Triage System

Modify `src/bridge_design_system/agents/triage_agent_smolagents.py` in these locations:

**Location 1: Agent Creation Block (Lines 73-92)**

Add after the geometry agent creation:

```python
# Create rational agent for level validation
from .rational_smolagents import create_rational_agent

rational_monitor = None
if monitoring_callback:
    # Check if it's a remote callback factory or local callback
    if (
        callable(monitoring_callback)
        and hasattr(monitoring_callback, "__name__")
        and "create" in monitoring_callback.__name__
    ):
        # Remote monitoring factory - create callback for this agent
        rational_monitor = monitoring_callback("rational_agent")
    else:
        # Local monitoring - use existing pattern
        from ..monitoring.agent_monitor import create_monitor_callback
        rational_monitor = create_monitor_callback("rational_agent", monitoring_callback)

rational_agent = create_rational_agent(monitoring_callback=rational_monitor)
```

**Location 2: Managed Agents Registration (Lines 140 & 454)**

Update both managed_agents lists:

```python
# In create_triage_system() (line 140)
managed_agents=[geometry_agent, rational_agent],

# In TriageSystemWrapper.__init__() (line 454)  
managed_agents=[self.geometry_agent, self.rational_agent],
```

**Location 3: Wrapper Class Integration (Lines 422-429)**

In `TriageSystemWrapper.__init__()`:

```python
# Create agents using the updated factory functions
self.geometry_agent = _create_mcp_enabled_geometry_agent(
    monitoring_callback=geometry_monitor,
)

self.rational_agent = create_rational_agent(monitoring_callback=rational_monitor)
```

**Location 4: Status Reporting (Lines 515-544)**

Add rational agent status block:

```python
def get_status(self) -> Dict[str, Any]:
    return {
        "triage": {
            "initialized": True,
            "type": "smolagents_managed_agents", 
            "managed_agents": 2,  # Update count
            "max_steps": self.manager.max_steps,
        },
        "geometry_agent": {
            # existing geometry status...
        },
        "rational_agent": {  # ADD THIS BLOCK
            "initialized": hasattr(self, "rational_agent") and self.rational_agent is not None,
            "type": (
                type(self.rational_agent).__name__
                if hasattr(self, "rational_agent")
                else "Unknown"
            ),
            "name": "rational_agent",
            "level_validation": "enabled",
        },
    }
```

#### Step 11.3: Configuration Updates

**Settings Configuration** (`src/bridge_design_system/config/settings.py`):

```python
class Settings(BaseSettings):
    # Add rational agent configuration
    rational_agent_provider: str = "gemini"
    rational_agent_model: str = "gemini-2.5-flash-lite-preview-06-17"
```

**Model Validation** (`src/bridge_design_system/config/model_config.py`):

```python
def validate_all_models() -> Dict[str, bool]:
    """Validate all configured agent models."""
    agents = ["triage", "geometry", "material", "structural", "syslogic", "rational"]
    # Add "rational" to the validation list
```

### Testing the Integration

#### Verify Agent Status

```python
from src.bridge_design_system.agents import TriageAgent

triage = TriageAgent()
status = triage.get_status()
print(status["rational_agent"])
# Expected: {"initialized": True, "name": "rational_agent", "level_validation": "enabled"}
```

#### Test Automatic Delegation

```python
# Test through triage system - rational agent called automatically
response = triage.handle_design_request(
    "Check all bridge elements for proper horizontal alignment and fix any issues"
)
print(response.message)
```

The triage agent will automatically:
1. Recognize "horizontal alignment" as rational agent capability
2. Delegate the task to the rational agent
3. Coordinate the results back to the user

### How Delegation Works

Once integrated, your rational agent works seamlessly with the triage system:

**Example User Request**: *"Validate that element 021 is properly horizontal and correct if needed"*

**Automatic Delegation Flow**:
1. **Triage Agent** receives the request
2. **Analysis**: Identifies "horizontal validation" keywords → rational agent capability  
3. **Delegation**: Routes task to rational agent with full context
4. **Execution**: Rational agent uses MCP tools + custom analysis tools
5. **Coordination**: Results integrated back through triage agent
6. **Response**: User gets coordinated response from the system

### Key Benefits of Managed Integration

**1. Automatic Task Routing**
- No manual agent selection required
- Intelligent delegation based on request content
- Multiple agents can collaborate on complex tasks

**2. Context Preservation**
- Shared memory across agents
- Design history accessible to all agents
- Coordinated decision making

**3. Resource Management**
- Centralized monitoring and logging
- Unified memory reset and cleanup
- Consistent error handling

**4. Scalability**
- Easy to add new specialized agents
- No changes needed to existing agents
- Consistent integration pattern

### Troubleshooting Integration

**Issue**: Rational agent not being delegated to
```python
# Check if agent is properly registered
status = triage.get_status()
print("rational_agent" in status)  # Should be True
```

**Issue**: Monitoring not working
```python
# Verify monitoring callback is passed
print(hasattr(rational_agent, '_wrapper'))  # Should be True
```

**Issue**: Memory reset not working
```python
# Check if agent has proper memory structure
print(hasattr(rational_agent, 'memory'))  # Should be True
print(hasattr(rational_agent.memory, 'steps'))  # Should be True
```

### Extending to Other Agents

This same integration pattern can be applied to any specialized agent:

1. **Follow Factory Pattern**: Return `ToolCallingAgent` from factory function
2. **Add to Triage System**: Update all 4 locations in triage file
3. **Configure Models**: Add to settings and validation
4. **Test Integration**: Verify delegation and status reporting

The rational agent integration serves as a template for adding any new specialized capability to the bridge design system while maintaining clean architecture and automatic coordination.

---

This completes the full implementation of a rational smolagent from development to integration as a managed agent in the smolagents triage system.

Now that you have built your rational agent, the next step is integrating it into the triage system as a managed agent. This enables automatic delegation and coordination with other specialized agents in the bridge design system.

### Why Managed Agents?

The managed agent pattern in smolagents provides several key benefits:

- **Automatic Delegation**: The triage agent automatically routes tasks to appropriate specialists
- **Context Sharing**: Agents can coordinate and share information seamlessly  
- **Resource Management**: Centralized memory, monitoring, and cleanup
- **Scalability**: Easy to add new specialized agents without modifying existing code

### Integration Process

#### Step 11.1: Verify Factory Function Pattern

Your rational agent should already follow the correct pattern from Step 8. Ensure your `create_rational_agent` function:

```python
def create_rational_agent(model_name: str = "rational", **kwargs) -> ToolCallingAgent:
    """Factory function returning a ToolCallingAgent ready for managed use."""
    wrapper = RationalSmolagent(model_name=model_name, **kwargs)
    internal_agent = wrapper.agent
    
    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper
    return internal_agent
```

**Key Requirements:**
- Returns a `ToolCallingAgent` (not the wrapper class)
- Stores wrapper reference for resource cleanup
- Accepts `monitoring_callback` parameter

#### Step 11.2: Add to Triage System

Open `src/bridge_design_system/agents/triage_agent_smolagents.py` and make these modifications:

**11.2.1 Agent Creation Block (Lines 73-92)**

Add after the geometry agent creation:

```python
# Create rational agent for level validation
from .rational_smolagents import create_rational_agent

rational_monitor = None
if monitoring_callback:
    # Check if it's a remote callback factory or local callback
    if (
        callable(monitoring_callback)
        and hasattr(monitoring_callback, "__name__")
        and "create" in monitoring_callback.__name__
    ):
        # Remote monitoring factory - create callback for this agent
        rational_monitor = monitoring_callback("rational_agent")
    else:
        # Local monitoring - use existing pattern
        from ..monitoring.agent_monitor import create_monitor_callback
        rational_monitor = create_monitor_callback("rational_agent", monitoring_callback)

rational_agent = create_rational_agent(monitoring_callback=rational_monitor)
```

**11.2.2 Managed Agents Registration (Lines 140 & 454)**

Update both managed_agents lists:

```python
# In create_triage_system() (line 140)
managed_agents=[geometry_agent, rational_agent],

# In TriageSystemWrapper.__init__() (line 454)  
managed_agents=[self.geometry_agent, self.rational_agent],
```

**11.2.3 Wrapper Class Integration (Lines 422-429)**

In `TriageSystemWrapper.__init__()`:

```python
# Create agents using the updated factory functions
self.geometry_agent = _create_mcp_enabled_geometry_agent(
    monitoring_callback=geometry_monitor,
)

self.rational_agent = create_rational_agent(monitoring_callback=rational_monitor)
```

**11.2.4 Status Reporting (Lines 515-544)**

Add rational agent status block:

```python
def get_status(self) -> Dict[str, Any]:
    return {
        "triage": {
            "initialized": True,
            "type": "smolagents_managed_agents", 
            "managed_agents": 2,  # Update count
            "max_steps": self.manager.max_steps,
        },
        "geometry_agent": {
            # existing geometry status...
        },
        "rational_agent": {  # ADD THIS BLOCK
            "initialized": hasattr(self, "rational_agent") and self.rational_agent is not None,
            "type": (
                type(self.rational_agent).__name__
                if hasattr(self, "rational_agent")
                else "Unknown"
            ),
            "name": "rational_agent",
            "level_validation": "enabled",
        },
    }
```

#### Step 11.3: Configuration Updates

**11.3.1 Settings Configuration** (`src/bridge_design_system/config/settings.py`):

```python
class Settings(BaseSettings):
    # Add rational agent configuration
    rational_agent_provider: str = "gemini"
    rational_agent_model: str = "gemini-2.5-flash-lite-preview-06-17"
```

**11.3.2 Model Validation** (`src/bridge_design_system/config/model_config.py`):

```python
def validate_all_models() -> Dict[str, bool]:
    """Validate all configured agent models."""
    agents = ["triage", "geometry", "material", "structural", "syslogic", "rational"]
    # Add "rational" to the validation list
```

### Testing the Managed Agent Integration

#### Step 11.4: Verify Integration

**Test Agent Status:**

```python
from src.bridge_design_system.agents import TriageAgent

triage = TriageAgent()
status = triage.get_status()
print(status["rational_agent"])
# Expected: {"initialized": True, "name": "rational_agent", "level_validation": "enabled"}
```

**Test Automatic Delegation:**

```python
# Test through triage system
response = triage.handle_design_request(
    "Check all bridge elements for proper horizontal alignment and fix any issues"
)
print(response.message)
```

The triage agent will automatically:
1. Recognize "horizontal alignment" as rational agent capability
2. Delegate the task to the rational agent
3. Coordinate the results back to the user

**Test Memory Integration:**

```python
# Test memory reset includes rational agent
triage.reset_all_agents()
# Should clear rational agent memory along with others
```

### How Delegation Works

Once integrated, your rational agent works seamlessly with the triage system:

**Example User Request**: *"Validate that element 021 is properly horizontal and correct if needed"*

**Automatic Delegation Flow**:
1. **Triage Agent** receives the request
2. **Analysis**: Identifies "horizontal validation" keywords → rational agent capability  
3. **Delegation**: Routes task to rational agent with full context
4. **Execution**: Rational agent uses MCP tools + custom analysis tools
5. **Coordination**: Results integrated back through triage agent
6. **Response**: User gets coordinated response from the system

### Integration Benefits

**Automatic Task Routing**: No manual agent selection required - the system intelligently delegates based on request content.

**Context Preservation**: Shared memory across agents means design history is accessible to all agents for coordinated decision making.

**Resource Management**: Centralized monitoring, logging, unified memory reset and cleanup, plus consistent error handling.

**Scalability**: Easy to add new specialized agents without changes to existing agents, following consistent integration patterns.

### Troubleshooting Integration

**Issue**: Rational agent not being delegated to
```python
# Check if agent is properly registered
status = triage.get_status()
print("rational_agent" in status)  # Should be True
```

**Issue**: Monitoring not working
```python
# Verify monitoring callback is passed
print(hasattr(rational_agent, '_wrapper'))  # Should be True
```

**Issue**: Memory reset not working
```python
# Check if agent has proper memory structure
print(hasattr(rational_agent, 'memory'))  # Should be True
print(hasattr(rational_agent.memory, 'steps'))  # Should be True
```

### Extending to Other Agents

This same integration pattern can be applied to any specialized agent:

1. **Follow Factory Pattern**: Return `ToolCallingAgent` from factory function
2. **Add to Triage System**: Update all 4 locations in triage file (lines 73-92, 140, 422-429, 454, 515-544)
3. **Configure Models**: Add to settings and validation
4. **Test Integration**: Verify delegation and status reporting

The rational agent integration serves as a template for adding any new specialized capability to the bridge design system while maintaining clean architecture and automatic coordination.

---

## Conclusion

Congratulations! You have successfully:

1. **Built a specialized rational agent** that validates bridge element levels
2. **Integrated MCP connectivity** for real-time CAD software interaction  
3. **Created custom analysis tools** for engineering-specific tasks
4. **Implemented proper resource management** and error handling
5. **Integrated the agent into the triage system** for automatic delegation and coordination

Your rational agent can now work both independently and as part of the larger bridge design system, automatically receiving delegated tasks and coordinating with other specialized agents to provide comprehensive engineering analysis and validation.

This foundational pattern can be extended to create other specialized agents for different aspects of bridge design, structural analysis, material optimization, and more.