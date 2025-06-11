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

## MCP Integration Architecture (Phase 2) - ✅ COMPLETED

The system uses **Model Context Protocol (MCP)** for seamless integration with Rhino/Grasshopper via **proven TCP bridge architecture**:

### TCP Bridge Architecture (Production Solution) ✅
```
smolagents → STDIO MCP Server → TCP Client → TCP Bridge → Grasshopper
          (grasshopper_mcp.bridge)  (communication.py)  (GH_MCPComponent.cs)
           49 tools via STDIO      JSON over TCP       C# TCP server
```

**Key Components:**
- **STDIO Transport**: smolagents uses STDIO MCP for 49 working tools
- **grasshopper_mcp.bridge**: FastMCP server with complete Grasshopper toolset
- **TCP Client**: communication.py sends JSON commands over TCP socket
- **TCP Bridge**: GH_MCPComponent.cs proven C# bridge from Claude Desktop integration
- **Gemini 2.5 Flash**: Cost-efficient LLM with optimal price-performance ratio

### Architecture Decision: TCP Bridge (Proven)
**Why TCP Bridge** (vs HTTP polling):
- ✅ **Proven**: Same architecture that worked with Claude Desktop
- ✅ **Simple**: Direct JSON over TCP socket, no HTTP complexity
- ✅ **Fast**: No polling delays, immediate request-response pattern
- ✅ **Stable**: No HTTP bugs, TCP bridge is battle-tested
- ✅ **Visual Monitoring**: TCP bridge component shows status in Grasshopper
- ✅ **Reliable**: TCP socket connection more stable than HTTP polling

**Key Benefits:**
- ✅ **No Polling**: Direct TCP communication eliminates 1-second delays
- ✅ **No HTTP Overhead**: Simple protocol, faster execution
- ✅ **Proven Protocol**: Same TCP bridge used by Claude Desktop
- ✅ **Visual Feedback**: Bridge component shows commands in real-time

## Development Commands

This project uses UV package manager:

### Windows (Recommended for Claude Code)
```powershell
# Setup project - Run in PowerShell or Command Prompt (NOT WSL2)
uv venv
.venv\Scripts\activate
uv pip install -e .

# Run system test
uv run python -m bridge_design_system.main --test

# Run interactive mode
uv run python -m bridge_design_system.main --interactive

# Test STDIO MCP server integration (49 tools)
uv run python test_simple_working_solution.py

# Test TCP bridge connection and communication
uv run python test_tcp_bridge_connection.py

# Deploy TCP bridge to Grasshopper (one-time setup)
cd src/bridge_design_system/mcp/GH_MCP/GH_MCP/ && dotnet build --configuration Release

# Run comprehensive tests
uv run pytest tests/

# Debug MCP connection issues  
uv run python debug_mcp_connection.py
uv run python debug_session_id.py

# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/
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

**🚨 CRITICAL: Always check official documentation before implementing!**
- **smolagents**: https://huggingface.co/docs/smolagents/
- **FastMCP**: https://gofastmcp.com/
- **MCP Protocol**: https://modelcontextprotocol.io/

### Tool Creation

**Standard smolagents tools:**
```python
from smolagents import tool

@tool
def tool_name(param: type) -> return_type:
    """Tool description for the agent."""
    # Implementation
```

**MCP Integration (CORRECT Approach):**
```python
from smolagents import ToolCollection, CodeAgent

# Use smolagents' built-in MCP support - handles async/sync automatically
tool_collection = ToolCollection.from_mcp({
    "url": "http://localhost:8001/mcp", 
    "transport": "streamable-http"
}, trust_remote_code=True)

# Tools are now available as proper smolagents tools
agent = CodeAgent(tools=[*tool_collection.tools])
```

**❌ AVOID: Custom sync wrappers, manual async/sync conversion, custom HTTP endpoints**

### Agent Implementation
- Extend base agent class for common functionality
- Use model provider abstraction for LLM flexibility
- Define behavior via system prompts in `system_prompts/`
- Pass tools to agents at initialization

**MCP-Enabled Agents (Phase 2):**
```python
from ..mcp.sync_mcp_tools import get_sync_grasshopper_tools

class GeometryAgent(BaseAgent):
    def _initialize_tools(self) -> List[Tool]:
        if self.use_official_mcp:
            # Use sync MCP tools for Grasshopper integration
            sync_tools = get_sync_grasshopper_tools()
            return sync_tools
        else:
            # Fallback to placeholder tools
            return self._create_placeholder_tools()
```

## Git Workflow - Trunk-based Development

This project uses **Trunk-based Development** for collaborative development:

### Branch Strategy
- **`master`**: The trunk branch - always deployable, represents production-ready code
- **Feature branches**: Short-lived branches for new features (max 2-3 days)
- **Branch naming**: `feature/description-of-change` (e.g., `feature/http-mcp-integration`)

### Workflow Rules
1. **Small, frequent commits**: Keep changes atomic and focused
2. **Feature branches**: Create from `master`, merge back to `master` via PR
3. **Continuous integration**: All commits on `master` must pass tests
4. **No long-lived branches**: Feature branches should be merged within 2-3 days
5. **Merge strategy**: Use squash merges to keep linear history

### Commands
```bash
# Create feature branch from master
git checkout master
git pull origin master
git checkout -b feature/your-feature-name

# Work on feature, make atomic commits
git add .
git commit -m "feat: add specific functionality"

# Before merging, rebase on latest master
git checkout master
git pull origin master
git checkout feature/your-feature-name
git rebase master

# Merge back to master (or via PR)
git checkout master
git merge --squash feature/your-feature-name
git commit -m "feat: complete feature description"
git branch -d feature/your-feature-name
```

## Coding Standards

- Type hints required for all functions
- Google-style docstrings
- Comprehensive error handling with custom error enums
- Logging decorators for all agent actions
- Maximum step limits to prevent runaway agents

## Current Status - Phase 2 COMPLETE! 🎉

**Phase 1: Core Agent Setup** - ✅ COMPLETED
- Multi-agent architecture implemented with smolagents framework
- 4 agents: Triage (orchestrator), Geometry, Material, Structural
- Configuration system with multi-LLM provider support
- Comprehensive logging and error handling
- Enhanced CLI interface with color-coded agent interactions
- Test framework and system validation

**Phase 2: MCP Integration** - ✅ **COMPLETED**
- ✅ STDIO MCP server with 49 working Grasshopper tools
- ✅ TCP bridge architecture proven and functional  
- ✅ Gemini 2.5 Flash integration for optimal cost-performance
- ✅ Enhanced JSON handling with proper smolagents imports
- ✅ Successful test validation (5/5 tests passing)

**Phase Status:**
1. ✅ **Phase 1: Core Agent Setup** (COMPLETE)
2. ✅ **Phase 2: MCP Integration** (COMPLETE - TCP bridge working with 49 tools)
3. 🎯 **Phase 3: Specialized Agent Tools** (Next - Ready to start)
4. ⏳ **Phase 4: AR Integration** (Future)

## Environment Configuration

Copy `.env.example` to `.env` and configure:
- **API Keys**: Set ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.
- **Model Selection**: Configure provider/model for each agent
- **Paths**: Set GRASSHOPPER_MCP_PATH for Phase 2

Current implementation supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet)
- DeepSeek (deepseek-chat)
- Gemini (Gemini 2.5 Flash) - ✅ **Default for optimal price-performance**
- HuggingFace Inference API
- Together AI

## Known Issues & Troubleshooting

### MCP Integration (Phase 2.3)
**Latest Status (COMPLETED):**
- ✅ Fixed local dependency installation issue for grasshopper-mcp
- ✅ Added grasshopper-mcp as local dependency in main pyproject.toml  
- ✅ Updated STDIO command to use installed module: `uv run python -m grasshopper_mcp.bridge`
- ✅ Enhanced JSON handling with proper smolagents imports (json, re, collections, etc.)
- ✅ Gemini 2.5 Flash integration for all agents
- ✅ All tests passing (5/5) with improved performance
- ✅ Ready for production with proven TCP bridge architecture


**Debugging Commands:**
```bash
# Test connection and session
uv run python debug_session_id.py

# Test sync tools (will show server error)
uv run python test_sync_tools.py

system structure

```
bridge-design-system/
├── src/bridge_design_system/
│   ├── agents/           # Agent implementations (4 agents)
│   ├── config/           # Settings and model configuration
│   ├── tools/            # Agent tools (geometry, material, structural)
│   ├── mcp/              # MCP integration (Phase 2) - NEW
│   │   ├── GH_MCP/       # C# Grasshopper bridge component
│   │   ├── grasshopper_mcp/      # MCP server utilities
│   │   ├── streamable_http_server.py  # Main MCP server
│   │   ├── sync_mcp_tools.py     # Sync wrapper tools (breakthrough)
│   │   └── smolagents_integration.py  # smolagents integration
│   └── main.py           # CLI entry point
├── tests/                # Unit and integration tests
├── test_*.py             # MCP integration tests (NEW)
├── debug_*.py            # MCP debugging utilities (NEW)
├── system_prompts/       # Agent behavior definitions
└── .env.example          # Environment configuration template
```

## Memory: @pyproject.toml
- Critical configuration file for project metadata and build system settings
- Uses `uv` (Rye) package manager
- Defines project dependencies, build requirements, and packaging information

#Memories: Tools for MCP and Smolagents

### Smolagents Tools Overview
Smolagents provides a robust framework for creating and managing AI tools with key features:

1. **Tool Creation**
```python
@tool
def web_search(query: str, max_results: int = 10) -> List[str]:
    """Search the web and return top results."""
    # Implementation
```

2. **Tool Loading from Hub**
```python
# Load a tool directly from Hugging Face Hub
image_generator = Tool.from_space(
    space_id="stability-ai/stable-diffusion",
    name="image-generator",
    description="Generate images from text prompts"
)
```

3. **MCP Tool Collection**
```python
# Load tools from an MCP server
tool_collection = ToolCollection.from_mcp({
    "url": "http://localhost:8001/mcp", 
    "transport": "streamable-http"
}, trust_remote_code=True)
```

4. **Tool Collection Management**
```python
# Combine tools from multiple sources
all_tools = [
    *weather_tool_collection.tools, 
    *pubmed_tool_collection.tools
]
```

### MCP Tool Integration Patterns

1. **Stdio MCP Server**
```python
server_parameters = StdioServerParameters(
    command="uv",
    args=["--quiet", "pubmedmcp@0.1.3"],
    env={"UV_PYTHON": "3.12", **os.environ},
)

with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
    agent = CodeAgent(tools=[*tool_collection.tools])
```

2. **HTTP Streamable MCP**
```python
tool_collection = ToolCollection.from_mcp({
    "url": "http://localhost:8000/mcp", 
    "transport": "streamable-http"
}, trust_remote_code=True)
```

### Best Practices
- Always use `trust_remote_code=False` by default
- Inspect tools before loading from external sources
- Use tool collections for modular tool management
- Leverage built-in MCP transport methods

## Tools Memory for Smolagents and MCP

**Key Tools Categories:**
1. **Web Interaction**
   - WebSearchTool
   - VisitWebpageTool
   - DuckDuckGoSearchTool
   - GoogleSearchTool

2. **Code & Computation**
   - PythonInterpreterTool
   - MathTool
   - CodeExecutionTool

3. **Text Processing**
   - TextClassificationTool
   - TranslationTool
   - SummarizationTool

4. **Multimedia**
   - SpeechToTextTool
   - ImageGenerationTool
   - ImageClassificationTool

5. **Specialized Domain Tools**
   - MedicalResearchTool (PubMed)
   - WeatherForecastTool
   - FinancialDataTool

### Adding New Memories

Do not build the environment yourself, rather give me instructions how to do it. I will then give you informations if there were any issues.
