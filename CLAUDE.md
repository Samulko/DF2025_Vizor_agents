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

## MCP Integration Architecture (Phase 2)

The system uses **Model Context Protocol (MCP)** for seamless integration with Rhino/Grasshopper:

### Bridge Architecture (Recommended)
```
Geometry Agent → Sync MCP Tools → HTTP MCP Server → Simple MCP Bridge → Grasshopper
```

**Key Components:**
- **Sync MCP Tools**: Custom synchronous wrappers around MCP protocol (solves async/sync conflicts)
- **HTTP MCP Server**: Official MCP streamable HTTP server with bridge mode support  
- **Simple MCP Bridge**: C# Grasshopper component that polls for commands every second
- **Session Management**: Proper 'mcp-session-id' header handling for authentication

### Architecture Decision: Bridge vs Direct
**Chosen: Bridge Architecture** because:
- ✅ Works with any MCP client (not just smolagents)
- ✅ Visual monitoring component in Grasshopper
- ✅ Decoupled - server and Grasshopper can run independently  
- ✅ Real-time polling with status feedback
- ✅ Avoids smolagents async/sync conflicts

**Alternative: STDIO MCP** (not chosen):
- ❌ Would bypass bridge infrastructure
- ❌ Tightly coupled to smolagents framework
- ❌ No visual monitoring in Grasshopper

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

# Start MCP server for Grasshopper integration (Phase 2)
python -m bridge_design_system.main --start-streamable-http --mcp-port 8001

# Run tests
pytest tests/

# Test MCP integration (requires server running)
python test_sync_tools.py

# Debug MCP connection issues
python debug_mcp_connection.py
python debug_session_id.py

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

## Current Status - Phase 2.3 Nearly Complete 🎯

**Phase 1: Core Agent Setup** - ✅ COMPLETED
- Multi-agent architecture implemented with smolagents framework
- 4 agents: Triage (orchestrator), Geometry, Material, Structural
- Configuration system with multi-LLM provider support
- Comprehensive logging and error handling
- Enhanced CLI interface with color-coded agent interactions
- Test framework and system validation

**Phase 2: MCP Integration** - 🎯 **95% COMPLETE** 
- ✅ **Phase 2.1**: HTTP MCP Server implementation
- ✅ **Phase 2.2**: Grasshopper SimpleMCPBridge component (C# polling client)
- 🎯 **Phase 2.3**: End-to-end integration with sync tools (nearly complete)

**Major Breakthrough Achieved:**
- ✅ Bridge architecture working: Agent → Sync Tools → HTTP MCP Server → Bridge → Grasshopper
- ✅ Session management solved: proper 'mcp-session-id' header handling
- ✅ Async/sync conflicts resolved: custom sync wrapper tools implemented
- ✅ Authentication working: MCP streamable HTTP protocol implemented
- 🔧 **Final fix needed**: Server task group initialization

**Phase Status:**
1. ✅ **Phase 1: Core Agent Setup** (COMPLETE)
2. 🎯 **Phase 2: MCP Integration** (95% - one server fix remaining)
3. ⏳ **Phase 3: Specialized Agent Tools** (Next)
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
- HuggingFace Inference API
- Together AI

## Known Issues & Troubleshooting

### MCP Integration (Phase 2.3)
**Latest Status (RESOLVED):**
- ✅ Fixed local dependency installation issue for grasshopper-mcp
- ✅ Added grasshopper-mcp as local dependency in main pyproject.toml  
- ✅ Updated STDIO command to use installed module: `uv run python -m grasshopper_mcp.bridge`
- ✅ Ready for testing with proper package installation

**Working Components:**
- ✅ Session ID capture: `mcp-session-id` header handling
- ✅ Sync tool authentication: Proper SSE response parsing  
- ✅ Bridge polling: SimpleMCPBridge successfully connects and polls
- ✅ Command queuing: Bridge mode architecture functional

**Debugging Commands:**
```bash
# Test connection and session
python debug_session_id.py

# Test sync tools (will show server error)
python test_sync_tools.py

# Check bridge status
curl http://localhost:8001/grasshopper/status
```

### async/sync Conflicts (SOLVED)
- **Problem**: smolagents CodeAgent vs async MCP tools incompatibility
- **Solution**: Custom sync wrapper tools in `src/bridge_design_system/mcp/sync_mcp_tools.py`
- **Result**: Preserves bridge architecture while solving framework conflicts

## Project Structure

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

## Memory: @MCP_IMPLEMENTATION_GUIDE.md
- Detailed technical documentation for implementing the Model Context Protocol (MCP)
- Covers synchronous and asynchronous integration strategies
- Explains bridge architecture, session management, and authentication mechanisms
- Provides reference implementations for different programming environments

## Memories: Tools for MCP and Smolagents

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