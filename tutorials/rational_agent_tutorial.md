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

## Further Reading

- [Smolagents Documentation](https://github.com/huggingface/smolagents)
- [MCP Integration Guide](../src/bridge_design_system/mcp/)
- [System Prompt Design](../system_prompts/rational_agent.md)
- [Model Configuration](../src/bridge_design_system/config/model_config.py)