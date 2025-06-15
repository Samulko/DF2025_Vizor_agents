# Vizor Agents - AR Bridge Design System

An AI-assisted bridge design system that uses intelligent agents to control Rhino Grasshopper for parametric design generation. This system features multi-provider AI model support and integrates with the Model Context Protocol (MCP) via STDIO for collaborative, iterative geometry creation.

## Key Features

* **Multi-Provider AI Support**: Works with Gemini, OpenAI, Anthropic, DeepSeek, and HuggingFace.
* **Collaborative Design**: Supports iterative, conversational design workflows.
* **AI-Generated Geometry**: Capable of creating spirals, bridges, and other complex structures.
* **Stable Core Tools**: Optimized with 6 core MCP tools for reliable operation.
* **Cross-Platform Support**: Compatible with both native Windows and WSL2.
* **Conversation Memory**: Agents remember context between interactions for seamless sessions.
* **Natural Language Modifications**: Understands commands like "make it wider."
* **Dynamic Tool Discovery**: Can list available MCP tools upon request.
* **Interactive CLI**: User-friendly command-line interface with real-time status updates.

## Quick Start

### Prerequisites

* Windows 10/11 (WSL2 optional)
* Rhino 8 with Grasshopper
* Python 3.10+
* [UV package manager](https://docs.astral.sh/uv/install/)

### 1. Installation

Clone the repository and set up the environment.

**PowerShell (Windows):**
```powershell
# Install UV if needed
powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"

# Clone and set up the project
git clone <repository-url>
cd vizor_agents
uv venv
.venv\Scripts\activate
uv pip install -e .
```

**Bash (WSL2/Linux):**
```bash
git clone <repository-url>
cd vizor_agents
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. API Configuration

Copy the example environment file and add your API keys.

```bash
# For Windows
copy .env.example .env
notepad .env

# For WSL2/Linux
cp .env.example .env
nano .env
```

### 3. Grasshopper Setup

* **Pre-built**: Copy `GH_MCP.gha` to `%APPDATA%\Grasshopper\Libraries\`.
* **For Developers**: Open the solution in Visual Studio 2022 and run in debug mode with the `.stp` file.

After setup, restart Grasshopper, add the "Grasshopper MCP" component to the canvas, and configure it with **Enabled=True**, **Port=8081**, and **Address=0.0.0.0**.

### 4. Usage

To start a design session, run:
```bash
uv run python -m bridge_design_system.main
```
You can then use natural language to create designs (e.g., "create a spiral staircase").

## Architecture Overview

The system operates through the following flow:

```
WSL/Windows Environment -> MCP via STDIO -> STDIO MCP Server -> TCP Bridge (Port 8081) -> Grasshopper MCP Component -> Real-time Geometry Creation
```

### Multi-Agent System
* **Triage Agent**: Orchestrates design workflows.
* **Geometry Agent**: Controls Grasshopper for 3D modeling.
* **Material Agent**: Manages construction material data.
* **Structural Agent**: Performs engineering analyses.

## Available Tools

The system is optimized with 6 core MCP tools for stability:

* `add_python3_script`
* `get_python3_script`
* `edit_python3_script`
* `get_python3_script_errors`
* `get_component_info_enhanced`
* `get_all_components_enhanced`

The limited toolset ensures reliable operation, with the Python script tool offering extensive flexibility for geometry creation.

## Development

### Project Structure
```
vizor_agents/
├── src/bridge_design_system/
│   ├── agents/
│   ├── config/
│   ├── tools/
│   └── mcp/
│       └── GH_MCP/
├── tests/
└── main.py
```

### Contributing

To format and test your code, run:
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Run tests
pytest tests/
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
