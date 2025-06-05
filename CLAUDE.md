# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

vizor_agents is an AR-assisted bridge design system that uses AI agents to help human designers create bridges in Rhino Grasshopper. The system implements a multi-agent architecture using the smolagents framework (v1.4.1+).

## Architecture

The system follows a hub-and-spoke pattern:
- **Triage Agent** (hub): Orchestrates workflow, delegates to specialized agents
- **Geometry Agent**: Creates/manipulates 3D geometry via Rhino/Grasshopper MCP
- **Material Management Agent**: Tracks construction materials from database
- **Structural Agent**: Performs structural analysis and validation

Communication flow:
```
Human (AR) ←→ Triage Agent ←→ Specialized Agents ←→ External Tools
```

## Development Commands

This project uses UV package manager:

### Windows (Recommended for Claude Code)
```powershell
# Setup project - Run in PowerShell or Command Prompt (NOT WSL2)
uv venv
.venv\Scripts\activate
uv pip install -e .

# Run system test
python -m bridge_design_system.main --test

# Run interactive mode
python -m bridge_design_system.main --interactive

# Run tests
pytest tests/

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

> **Note for Claude Code**: This project should be run on native Windows (PowerShell/Command Prompt), NOT through WSL2, for optimal compatibility with Rhino/Grasshopper MCP integration in Phase 2.

### Linux/macOS
```bash
# Setup project
uv venv
source .venv/bin/activate
uv pip install -e .

# Commands same as above
```

## Key Implementation Patterns

### Tool Creation
```python
from smolagents import tool

@tool
def tool_name(param: type) -> return_type:
    """Tool description for the agent."""
    # Implementation
```

### Agent Implementation
- Extend base agent class for common functionality
- Use model provider abstraction for LLM flexibility
- Define behavior via system prompts in `system_prompts/`
- Pass tools to agents at initialization

## Coding Standards

- Type hints required for all functions
- Google-style docstrings
- Comprehensive error handling with custom error enums
- Logging decorators for all agent actions
- Maximum step limits to prevent runaway agents

## Current Status - Phase 1 Complete ✅

**Phase 1: Core Agent Setup** - ✅ COMPLETED
- Multi-agent architecture implemented with smolagents framework
- 4 agents: Triage (orchestrator), Geometry, Material, Structural
- Configuration system with multi-LLM provider support
- Comprehensive logging and error handling
- Enhanced CLI interface with color-coded agent interactions
- Test framework and system validation

**Next Phases:**
1. ✅ **Phase 1: Core Agent Setup** (DONE)
2. 🔄 **Phase 2: MCP Integration** (Next)
3. ⏳ **Phase 3: Specialized Agent Tools**
4. ⏳ **Phase 4: AR Integration**

## Environment Configuration

Copy `.env.example` to `.env` and configure:
- **API Keys**: Set ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.
- **Model Selection**: Configure provider/model for each agent
- **Paths**: Set GRASSHOPPER_MCP_PATH for Phase 2

Current implementation supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet)
- DeepSeek (deepseek-chat)
- HuggingFace Inference API
- Together AI

## Project Structure

```
bridge-design-system/
├── src/bridge_design_system/
│   ├── agents/           # Agent implementations (5 agents)
│   ├── config/           # Settings and model configuration
│   ├── tools/            # Agent tools (geometry, material, structural)
│   ├── mcp/              # MCP integration (Phase 2)
│   └── main.py           # CLI entry point
├── tests/                # Unit and integration tests
├── system_prompts/       # Agent behavior definitions
└── .env.example          # Environment configuration template
```