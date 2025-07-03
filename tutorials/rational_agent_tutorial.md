# Rational Agent Tutorial - Level Validation and Correction

This tutorial demonstrates how to build a specialized smolagent for bridge element level validation using the rational agent as an example.

## Overview

The Rational Agent is a focused smolagent that validates and corrects bridge element levels to ensure proper horizontal alignment. It demonstrates key smolagents patterns while solving a specific engineering problem.

## What You'll Learn

- How to create a specialized smolagent with custom tools
- MCP integration for external system access
- System prompt design with chain-of-thought reasoning
- Model configuration and optimization
- Command-line demonstration techniques

## Agent Architecture

### Core Components

```python
# 1. MCP Integration for Grasshopper access
self.mcp_connection = MCPAdapt(self.stdio_params, SmolAgentsAdapter())
self.mcp_tools = self.mcp_connection.__enter__()

# 2. Custom analysis tool
@tool
def analyze_element_level(element_id: str) -> str:
    # Structured analysis logic
    
# 3. ToolCallingAgent with specialized configuration
self.agent = ToolCallingAgent(
    tools=all_tools,
    model=self.model,
    max_steps=8,
    name="rational_agent",
    description="Validates and corrects bridge element levels"
)
```

### Available Tools

**MCP Tools** (from Grasshopper integration):

- `get_geometry_agent_components` - View available components
- `get_python3_script` - Read component parameters
- `edit_python3_script` - Modify component code
- `get_python3_script_errors` - Validate syntax

**Custom Tool**:

- `analyze_element_level` - Structured level analysis reporting

## Level System

Bridge elements must be positioned at specific horizontal levels:

- **Level 1**: Z = 0.025 meters (green/red elements)
- **Level 2**: Z = 0.075 meters (blue elements)
- **Level 3**: Z = 0.125 meters (orange elements)

### Validation Rules

1. **Center Point Z-Value**: Must match exactly one of the three levels
2. **Direction Vector Z-Value**: Must be 0 (horizontal orientation)
3. **Consistency Check**: All parameters must be at the same level

## System Prompt Design

The rational agent uses a sophisticated system prompt with:

### XML Structure
```xml
<role>
You are a Rational Agent specialized in validating and correcting element levels.
</role>

<levels>
- Level 1: Z = 0.025 meters (green/red elements)
- Level 2: Z = 0.075 meters (blue elements)
- Level 3: Z = 0.125 meters (orange elements)
</levels>

<thinking_process>
1. Extract Parameters
2. Check Center Point
3. Check Direction Vector
4. Identify Issues
5. Calculate Corrections
6. Apply Changes
</thinking_process>
```

### Chain of Thought Examples

The prompt includes three detailed examples showing:

- Correct element analysis
- Elements needing correction
- Elements that are already correct

## Model Configuration

### Optimized for Performance
```python
# .env configuration
RATIONAL_AGENT_PROVIDER=gemini
RATIONAL_AGENT_MODEL=gemini-2.5-flash-lite-preview-06-17

# settings.py
rational_agent_provider: str = "gemini"
rational_agent_model: str = "gemini-2.5-flash-lite-preview-06-17"
```

**Why Gemini 2.5 Flash Lite?**

- Fastest and most cost-efficient Gemini model
- Optimized for low-latency validation tasks
- Excellent tool use capabilities for MCP integration
- 1M token context for complex component analysis

## Usage Examples

### Basic Demo
```bash
# Run the built-in demonstration
python -m src.bridge_design_system.agents.rational_smolagents
```

### Interactive Usage
```python
from src.bridge_design_system.agents.rational_smolagents import create_rational_agent

# Create agent instance
agent = create_rational_agent()

# Analyze specific element
result = agent.run("Check element 021 for level issues and correct if needed")
print(result)
```

### Verbose Debugging
```bash
# Enable detailed logging to see agent reasoning
PYTHONPATH=/home/samko/github/vizor_agents python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.bridge_design_system.agents.rational_smolagents import demo_level_checking
demo_level_checking()
"
```

## Workshop Demonstration

### 1. Component Discovery

The agent first discovers available components:
```
╭─ Calling tool: 'get_geometry_agent_components' ╮
│ Found 4 components: component_1, component_2,  │
│ component_3, component_4                        │
╰─────────────────────────────────────────────────╯
```

### 2. Structured Analysis

Uses custom tool for systematic evaluation:
```
╭─ Calling tool: 'analyze_element_level' ╮
│ Element ID: component_1                │
│ Analysis Focus: Direction vector       │
│ Z-component validation                 │
╰────────────────────────────────────────╯
```

### 3. Parameter Extraction

Reads current element parameters from Grasshopper:
```python
# Example extracted parameters
center1 = rg.Point3d(-0.1874, -0.10, 0.025)  # Correct level
direction1 = rg.Vector3d(-34.5, -20, 0)      # Horizontal ✓
```

### 4. Correction Application

If issues found, applies precise corrections:
```python
# Before: direction1 = rg.Vector3d(-34.5, -20, 0.5)  # Not horizontal
# After:  direction1 = rg.Vector3d(-34.5, -20, 0)    # Corrected
```

## Key Design Patterns

### 1. Focused Responsibility

- Single purpose: level validation and correction
- Clear scope boundaries
- Specific domain expertise

### 2. MCP Integration

- Leverages existing infrastructure
- No duplication of functionality
- Clean separation of concerns

### 3. Custom Tool Strategy

- One custom tool for structured analysis
- Builds on MCP foundation rather than replacing it
- Demonstrates @tool decorator usage

### 4. Chain of Thought Prompting

- Structured reasoning process
- Multiple examples for different scenarios
- XML tags for clear formatting

### 5. Model Optimization

- Task-appropriate model selection
- Cost and performance considerations
- Dedicated agent configuration

## Error Handling

The agent includes robust error handling:

```python
try:
    result = self.agent.run(task)
    logger.info("Level checking task completed successfully")
    return result
except Exception as e:
    logger.error(f"Level checking task failed: {e}")
    raise RuntimeError(f"Rational smolagent execution failed: {e}")
```

## Integration with Bridge Design System

### Triage Agent Coordination

The rational agent can be called by the triage agent for level validation:

```python
# Example triage agent usage
rational_result = rational_agent.run(
    "Validate levels for all elements in component_1"
)
```

### Memory and State Management

- Uses smolagents native memory system
- Integrates with design change tracking
- Maintains context across multiple validations

## Best Practices Demonstrated

### 1. Configuration Management

- Centralized model configuration
- Environment-based settings
- Validation and fallback handling

### 2. System Prompt Engineering

- Role-based instructions
- Structured examples
- Chain of thought reasoning
- XML formatting for clarity

### 3. Tool Design

- Single responsibility principle
- Clear docstrings for LLM understanding
- Structured output formats
- Error handling and logging

### 4. Factory Pattern

- Clean agent instantiation
- Proper resource management
- Flexible configuration options

## Extending the Agent

### Adding New Tools
```python
@tool
def validate_structural_integrity(element_id: str) -> str:
    """Custom validation logic for structural requirements."""
    # Implementation here
    
# Add to tools list
all_tools.append(validate_structural_integrity)
```

### Custom System Prompts

- Create new prompt files in `system_prompts/`
- Use XML structure for clarity
- Include multiple examples
- Follow chain of thought patterns

### Model Experimentation
```python
# Try different models
RATIONAL_AGENT_MODEL=gemini-2.0-flash        # Newer alternative
RATIONAL_AGENT_MODEL=gemini-1.5-flash-001    # Maximum compatibility
```

## Troubleshooting

### Common Issues

**1. Model Not Found Error**

```
Error: models/gemini-2.5-flash-lite is not found
```

**Solution**: Use full versioned name: `gemini-2.5-flash-lite-preview-06-17`

**2. MCP Connection Failure**

```
Failed to establish persistent MCP connection
```

**Solution**: Ensure MCP server is running on port 8001

**3. Configuration Not Loading**

```
Initializing rational agent with openai/gpt-4
```

**Solution**: Check both `.env` and `settings.py` have rational agent fields

### Debug Commands
```bash
# Test model configuration
python -c "
from src.bridge_design_system.config.model_config import ModelProvider
info = ModelProvider.get_model_info('rational')
print(info)
"

# Validate all models
python -c "
from src.bridge_design_system.config.model_config import ModelProvider
results = ModelProvider.validate_all_models()
print(results)
"
```

## Conclusion

The Rational Agent demonstrates how to build focused, efficient smolagents that:

- Solve specific engineering problems
- Integrate cleanly with existing systems
- Use appropriate models for the task
- Follow smolagents best practices
- Provide clear demonstration value

This pattern can be adapted for other specialized validation and correction tasks in the bridge design system.

## Making the Rational Agent a Managed Agent

Once you have completed building your rational agent following the patterns above, the next step is integrating it into the triage system as a managed agent. This enables automatic delegation and coordination with other specialized agents.

### Why Managed Agents?

The managed agent pattern in smolagents provides:

- **Automatic Delegation**: Triage agent automatically routes tasks to appropriate specialists
- **Context Sharing**: Agents can coordinate and share information seamlessly  
- **Resource Management**: Centralized memory, monitoring, and cleanup
- **Scalability**: Easy to add new specialized agents without modifying existing code

### Integration Steps

#### Step 1: Ensure Factory Function Pattern

Your rational agent should already follow this pattern:

```python
# File: src/bridge_design_system/agents/rational_smolagents.py

def create_rational_agent(model_name: str = "rational", **kwargs) -> ToolCallingAgent:
    """Factory function returning a ToolCallingAgent ready for managed use."""
    wrapper = RationalSmolagent(model_name=model_name, **kwargs)
    internal_agent = wrapper.agent
    
    # Store wrapper reference for proper cleanup
    internal_agent._wrapper = wrapper
    return internal_agent
```

**Key Requirements:**
- Returns a `ToolCallingAgent` (not wrapper class)
- Stores wrapper reference for resource cleanup
- Accepts `monitoring_callback` parameter

#### Step 2: Add to Triage System

Modify `src/bridge_design_system/agents/triage_agent_smolagents.py` in these specific locations:

**2.1 Agent Creation Block (Lines 73-92)**

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

**2.2 Managed Agents Registration (Lines 140 & 454)**

Update both managed_agents lists:

```python
# In create_triage_system() (line 140)
managed_agents=[geometry_agent, rational_agent],

# In TriageSystemWrapper.__init__() (line 454)  
managed_agents=[self.geometry_agent, self.rational_agent],
```

**2.3 Wrapper Class Integration (Lines 422-429)**

In `TriageSystemWrapper.__init__()`:

```python
# Create agents using the updated factory functions
self.geometry_agent = _create_mcp_enabled_geometry_agent(
    monitoring_callback=geometry_monitor,
)

self.rational_agent = create_rational_agent(monitoring_callback=rational_monitor)
```

**2.4 Status Reporting (Lines 515-544)**

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

#### Step 3: Configuration Updates

**3.1 Settings Configuration** (`src/bridge_design_system/config/settings.py`):

```python
class Settings(BaseSettings):
    # Add rational agent configuration
    rational_agent_provider: str = "gemini"
    rational_agent_model: str = "gemini-2.5-flash-lite-preview-06-17"
```

**3.2 Model Validation** (`src/bridge_design_system/config/model_config.py`):

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

#### Test Direct Delegation

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

#### Test Memory Integration

```python
# Test memory reset includes rational agent
triage.reset_all_agents()
# Should clear rational agent memory along with others
```

### How Delegation Works

Once integrated, the rational agent works seamlessly with the triage system:

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
```
# Check if agent is properly registered
status = triage.get_status()
print("rational_agent" in status)  # Should be True
```

**Issue**: Monitoring not working
```
# Verify monitoring callback is passed
print(hasattr(rational_agent, '_wrapper'))  # Should be True
```

**Issue**: Memory reset not working
```
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

## Further Reading

- [Smolagents Documentation](https://github.com/huggingface/smolagents)
- [MCP Integration Guide](../src/bridge_design_system/mcp/)
- [System Prompt Design](../system_prompts/rational_agent.md)
- [Model Configuration](../src/bridge_design_system/config/model_config.py)