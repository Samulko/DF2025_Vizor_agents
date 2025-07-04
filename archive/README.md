# Smolagents Educational Tutorials

This directory contains educational Jupyter notebooks and tutorials for learning the smolagents framework in the context of bridge design.

## Introduction to Smolagents

**File**: `introduction_to_smolagents.ipynb`

A comprehensive introduction to the smolagents framework, designed for students with little to medium programming knowledge. This notebook teaches:

- Understanding AI agents and the smolagents framework
- The difference between CodeAgent and ToolCallingAgent
- Using built-in tools like WebSearchTool
- Creating custom tools with the @tool decorator
- Building a Bridge Reference Agent
- Integrating agents into multi-agent systems

### Prerequisites

1. **Python Environment**:
   ```bash
   # Windows (PowerShell/Command Prompt)
   uv venv
   .venv\Scripts\activate
   uv pip install -e .
   ```

2. **Hugging Face Token**:
   - Get a token from https://huggingface.co/settings/tokens
   - Set it as an environment variable: `HF_TOKEN=your_token_here`
   - Or provide it directly in the notebook

3. **Jupyter**:
   ```bash
   uv pip install jupyter notebook
   ```

### Running the Notebook

1. **Start Jupyter**:
   ```bash
   jupyter notebook
   ```

2. **Navigate** to the `tutorials/` directory

3. **Open** `introduction_to_smolagents.ipynb`

4. **Run cells** sequentially (Shift+Enter)

### What You'll Build

By the end of the notebook, you'll have created a **Bridge Reference Agent** that can:
- Search for information about real bridges
- Find bridges by type (suspension, arch, etc.)
- Compare bridge specifications
- Provide engineering details and history

### Learning Objectives

**Part 1**: Introduction to Smolagents
- Understand AI agents and their capabilities
- Learn about the smolagents framework
- Compare CodeAgent vs ToolCallingAgent

**Part 2**: Using Built-in Tools
- Work with WebSearchTool directly
- Understand tool integration with agents
- See how different agent types use tools

**Part 3**: Creating Custom Tools
- Learn tool anatomy and structure
- Create bridge-specific search tools
- Test tools independently

**Part 4**: Building Agents
- Combine tools into capable agents
- Compare agent behaviors on the same task
- Understand when to use each agent type

**Part 5**: System Integration
- Learn the managed agents pattern
- See how agents work together
- Understand the triage system architecture

**Part 6**: Hands-on Exercises
- Practice creating new tools
- Build more complex agents
- Extend the system with your ideas

### Integration with Bridge Design System

The Bridge Reference Agent you'll build can be integrated into the main bridge design system:

```python
# Example integration (shown in the notebook)
from src.bridge_design_system.agents.bridge_reference_agent import create_reference_agent_for_triage

# Add to triage system
reference_agent = create_reference_agent_for_triage()
triage.managed_agents.append(reference_agent)
```

### Troubleshooting

**Common Issues**:

1. **Import Errors**: Make sure you're in the activated virtual environment
2. **Token Issues**: Verify your HF_TOKEN is set correctly
3. **Model Access**: Some models require approval - use default models first
4. **Network Issues**: WebSearchTool requires internet access

**Getting Help**:
- Check the smolagents documentation: https://huggingface.co/docs/smolagents
- Review the existing agents in `src/bridge_design_system/agents/`
- Use the integration example in `examples/bridge_reference_integration.py`

### Next Steps

After completing this notebook:

1. **Explore** the geometry agent code to see MCP integration
2. **Design** your own specialized agent for the workshop
3. **Experiment** with different agent architectures
4. **Build** tools specific to your bridge design needs

### Workshop Context

This notebook prepares you for the workshop where you'll:
- Work on a real bridge design challenge
- Create agents that solve specific problems
- Integrate with CAD tools via MCP
- Build a complete multi-agent system

Happy learning! 🌉