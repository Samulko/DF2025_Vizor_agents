# AR-Assisted Bridge Design System

A multi-agent AI system for AR-assisted bridge design in Rhino Grasshopper using the smolagents framework. The system enables a human designer wearing an AR headset to interactively design bridges with AI assistance through natural language and gesture-based interactions.

## Overview

The system implements a **hub-and-spoke multi-agent architecture** with **MCP integration**:
- **🔵 Triage Agent**: Main orchestrator that interprets human requests and coordinates specialized agents
- **🟢 Geometry Agent**: Creates and manipulates 3D geometry in Rhino/Grasshopper via MCP bridge
- **🔴 Material Agent**: Manages construction material inventory and constraints
- **🟠 Structural Agent**: Performs structural analysis and validation

### MCP Integration Architecture
```
Geometry Agent → Sync MCP Tools → HTTP MCP Server → Simple MCP Bridge → Grasshopper
```

**Key Innovation**: Custom sync wrapper tools solve async/sync conflicts while preserving bridge architecture for real-time visual monitoring in Grasshopper.

## Features

### Core System
- ✨ **Enhanced CLI Interface**: Color-coded agent interactions with real-time status updates
- 🤖 **Multi-Agent Coordination**: Intelligent task delegation between specialized agents
- 🎨 **Visual Agent Communication**: Clear visual feedback showing which agents are active
- ⚙️ **Flexible Model Configuration**: Support for multiple LLM providers (OpenAI, Anthropic, DeepSeek, etc.)
- 🔧 **Terminal Compatibility**: Works in Git Bash, PowerShell, Windows Terminal, and more

### MCP Integration (Phase 2 - Complete)
- 🚀 **FastMCP Framework**: Uses [FastMCP v2](https://github.com/jlowin/fastmcp) - the standard framework for MCP with automatic session management
- 🌉 **Bridge Architecture**: Agent → FastMCP Server → SimpleMCPBridge → Grasshopper
- 🔄 **Real-time Polling**: C# bridge component polls server and executes commands in real-time  
- 🔗 **Session Management**: Automatic session handling via FastMCP framework (eliminates timeout issues)
- ⚡ **Sync Tools**: Custom wrappers solve smolagents async/sync conflicts
- 📡 **Production Ready**: Streamable HTTP transport with graceful fallback to manual server
- 🎯 **Complete Tool Set**: Full Grasshopper integration including Python script tools
- 🔧 **Multiple Transports**: Supports Streamable HTTP, SSE, STDIO, and In-Memory protocols

## Quick Start

### Prerequisites

- Python 3.10+
- UV package manager
- API keys for LLM providers (OpenAI, Anthropic, DeepSeek, etc.)
- **For MCP Integration (Phase 2)**: Rhino 8 + Grasshopper (Windows)

### Installation

1. Clone the repository:
```bash
cd bridge-design-system
```

2. Install dependencies with UV:
```bash
uv venv
.venv\Scripts\activate  # Windows - or source .venv/bin/activate on Linux/Mac
uv pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Running the System

**Enhanced CLI (default)** - Color-coded agent interactions:
```bash
python -m bridge_design_system.main
```

**System test** - Validate configuration:
```bash
python -m bridge_design_system.main --test
```

**MCP Integration (Phase 2)** - Start MCP server for Grasshopper:
```bash
# Start MCP server
python -m bridge_design_system.main --start-streamable-http --mcp-port 8001

# In Grasshopper: Add "Simple MCP Bridge" component and connect to True
# The bridge will poll for commands and execute them in real-time
```

**Test MCP Integration**:
```bash
# Test sync tools (requires MCP server running)
python test_sync_tools.py

# Debug connection issues
python debug_session_id.py
```

**Basic interactive mode** - Simple fallback:
```bash
python -m bridge_design_system.main --interactive
```

### Usage Example

```
Designer> I want to create a bridge with two support points

16:45:23 🤔 [T] TRIAGE [THINKING]: Analyzing: I want to create a bridge with two support points
16:45:24 🔵 Triage Agent: I'll help you create a bridge with two support points. Let me coordinate with our specialized agents.
16:45:24 📤 [T] TRIAGE [DELEGATING]: Delegating to geometry agent
16:45:25 *** [G] Geometry thinking: I need to create 3D geometry for this bridge design
16:45:26 🔄 [G] GEOMETRY [ACTIVE]: Creating bridge geometry

Designer> Make the span 50 meters

16:45:30 🔵 Triage Agent: I'll ask the Geometry Agent to position the support points 50 meters apart...
```

### CLI Features

- **🎨 Color-coded agents**: Each agent has its own color for easy identification
- **💭 Agent thoughts**: See what agents are thinking in real-time
- **⚡ Quick commands**: `help`, `status`, `reset`, `clear`, `exit`
- **🔧 Terminal compatibility**: Auto-detects Git Bash, PowerShell, etc.

## Project Structure

```
bridge-design-system/
├── src/bridge_design_system/
│   ├── agents/              # Agent implementations
│   ├── config/              # Configuration and settings
│   ├── tools/               # Agent tools (geometry, material, structural)
│   ├── mcp/                 # MCP integration (Phase 2)
│   └── main.py              # Entry point
├── tests/                   # Test suites
├── system_prompts/          # Agent system prompts
└── .env.example             # Environment configuration template
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

## Configuration

The system supports multiple LLM providers configurable via environment variables:

- **Triage Agent**: Defaults to DeepSeek (cost-efficient)
- **Specialized Agents**: Default to Claude 3.5 Sonnet (high capability)

See `.env.example` for all configuration options.

## Current Status

✅ **Phase 1: Core Agent Setup** - COMPLETED
- Multi-agent architecture implemented with smolagents framework
- 4 agents: Triage (orchestrator), Geometry, Material, Structural
- Enhanced CLI interface with color-coded agent interactions
- Configuration system with multi-LLM provider support
- Comprehensive logging and error handling

🎯 **Phase 2: MCP Integration** - **COMPLETED**
- ✅ **Phase 2.1**: FastMCP server implementation with official MCP protocol
- ✅ **Phase 2.2**: C# SimpleMCPBridge component for Grasshopper (polling client)
- ✅ **Phase 2.3**: End-to-end integration with FastMCP framework

**Major Breakthrough Achieved:**
- ✅ **FastMCP Integration**: Uses the standard MCP framework - eliminates timeout and session issues
- ✅ **Sync Tools**: Custom wrappers solve async/sync framework conflicts  
- ✅ **Bridge Architecture**: Preserved visual monitoring in Grasshopper
- ✅ **Protocol Implementation**: Full MCP streamable HTTP with automatic session management
- ✅ **Production Ready**: Graceful fallback system (FastMCP → Manual → Legacy)

**Remaining Phases:**
- **Phase 3**: Specialized Agent Tools & Full Functionality (Next)
- **Phase 4**: AR Integration & Advanced Features

### Known Issues
- **Resolved**: `RuntimeError: Task group is not initialized` - Fixed by switching to FastMCP framework
- **Current Status**: Phase 2 MCP Integration complete with FastMCP 
- **Next**: Phase 3 specialized agent tools and enhanced functionality

## License

[License information to be added]