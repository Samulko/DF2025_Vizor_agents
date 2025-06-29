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

## Adding New Agents to the Triage System

The rational agent integration demonstrates the standard pattern for adding new specialized agents. Here are the **specific locations** you need to modify:

### 1. Agent Creation Block
**Location**: `triage_agent_smolagents.py` lines 73-92

Add your agent creation after the rational agent:
```python
# Create [your_agent_name] for [purpose]
from .[your_agent_file] import create_[your_agent_name]

[your_agent_name]_monitor = None
if monitoring_callback:
    if (callable(monitoring_callback) and hasattr(monitoring_callback, "__name__") 
        and "create" in monitoring_callback.__name__):
        [your_agent_name]_monitor = monitoring_callback("[your_agent_name]")
    else:
        from ..monitoring.agent_monitor import create_monitor_callback
        [your_agent_name]_monitor = create_monitor_callback("[your_agent_name]", monitoring_callback)

[your_agent_name] = create_[your_agent_name](monitoring_callback=[your_agent_name]_monitor)
```

### 2. Managed Agents List
**Locations**: Lines 140 & 454

Update both managed_agents lists:
```python
managed_agents=[geometry_agent, rational_agent, [your_agent_name]],
```

### 3. TriageSystemWrapper Monitoring
**Location**: Lines 405-420

Add monitoring variables:
```python
geometry_monitor = None
rational_monitor = None
[your_agent_name]_monitor = None  # ADD HERE

# Add to both monitoring callback sections
[your_agent_name]_monitor = monitoring_callback("[your_agent_name]")
[your_agent_name]_monitor = create_monitor_callback("[your_agent_name]", monitoring_callback)
```

### 4. TriageSystemWrapper Agent Instantiation
**Location**: After line 429

Add agent creation:
```python
from .[your_agent_file] import create_[your_agent_name]
self.[your_agent_name] = create_[your_agent_name](monitoring_callback=[your_agent_name]_monitor)
```

### 5. Status Reporting Updates
**Locations**: Line 521 (count) & after line 543 (status block)

Update agent count and add status block:
```python
"managed_agents": 3,  # Update count

"[your_agent_name]": {
    "initialized": hasattr(self, "[your_agent_name]") and self.[your_agent_name] is not None,
    "type": type(self.[your_agent_name]).__name__ if hasattr(self, "[your_agent_name]") else "Unknown",
    "name": "[your_agent_name]",
    "[your_capability]": "enabled",
},
```

### 6. Configuration Requirements

**Settings Configuration** (`settings.py`):
```python
[your_agent_name]_provider: str = "gemini"
[your_agent_name]_model: str = "gemini-2.5-flash-preview-05-20"
```

**Model Validation** (`model_config.py`):
```python
agents = ["triage", "geometry", "material", "structural", "syslogic", "rational", "[your_agent_name]"]
```

**System Prompt** (`system_prompts/triage_agent.md`):
Add agent description following the rational agent pattern.

### 7. Integration Checklist

When adding a new agent, ensure you:

- [ ] Create the agent implementation file
- [ ] Add factory function (`create_[your_agent_name]`)
- [ ] Update all 7 locations in `triage_agent_smolagents.py`
- [ ] Add configuration to `settings.py`
- [ ] Update validation list in `model_config.py`
- [ ] Document in system prompt
- [ ] Test with triage delegation

### 8. Example: Material Agent Integration

```python
# 1. Agent creation (lines 73-92)
from .material_smolagents import create_material_agent
material_monitor = monitoring_callback("material_agent") if monitoring_callback else None
material_agent = create_material_agent(monitoring_callback=material_monitor)

# 2. Managed agents (lines 140 & 454)
managed_agents=[geometry_agent, rational_agent, material_agent],

# 3. Status updates
"managed_agents": 3,
"material_agent": {
    "initialized": hasattr(self, "material_agent") and self.material_agent is not None,
    "name": "material_agent",
    "material_tracking": "enabled",
},
```

This systematic approach ensures consistent integration patterns and maintainable agent architecture.

## Further Reading

- [Smolagents Documentation](https://github.com/huggingface/smolagents)
- [MCP Integration Guide](../src/bridge_design_system/mcp/)
- [System Prompt Design](../system_prompts/rational_agent.md)
- [Model Configuration](../src/bridge_design_system/config/model_config.py)