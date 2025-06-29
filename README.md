# Vizor Agents - AR Bridge Design System

An AI-assisted bridge design system that uses intelligent agents to control Rhino Grasshopper for parametric design generation. This system features multi-provider AI model support and integrates with the Model Context Protocol (MCP) via STDIO for collaborative, iterative geometry creation.

## Key Features

* **Multi-Provider AI Support**: Works with Gemini, OpenAI, Anthropic, DeepSeek, and HuggingFace.
* **Voice Input**: Hands-free design with wake word detection and speech recognition.
* **AR Integration**: Gaze tracking and spatial interaction with HoloLens.
* **Collaborative Design**: Supports iterative, conversational design workflows.
* **AI-Generated Geometry**: Capable of creating spirals, bridges, and other complex structures.
* **Stable Core Tools**: Optimized with 6 core MCP tools for reliable operation.
* **Cross-Platform Support**: Compatible with both native Windows and WSL2.
* **Conversation Memory**: Agents remember context between interactions for seamless sessions.
* **Natural Language Modifications**: Understands commands like "make it wider."
* **Dynamic Tool Discovery**: Can list available MCP tools upon request.
* **Interactive CLI**: User-friendly command-line interface with real-time status updates.

## Complete Workshop Setup Guide

This guide will walk you through setting up the complete development environment for the DF2025 Vizor Agents workshop on Windows.

### 1. Prerequisites Check

Before we begin, let's check what you already have:
- **API Keys**: How many of you already have OpenAI, Anthropic, or Google (Gemini) API keys?
- **Development Tools**: Do you have Git, VS Code, or similar installed?

### 2. Core System Installation

#### Step 1: Install Winget (if not present)
```powershell
# Check if winget is available
winget --version

# If not available, install from Microsoft Store:
# Search for "App Installer" and install it
```

#### Step 2: Install WSL2 (Linux Subsystem)
```powershell
# Run as Administrator
wsl --install

# Restart your computer when prompted
# After restart, set up Ubuntu username and password
```

#### Step 3: Install Git
```powershell
# Install Git via winget
winget install Git.Git

# Restart terminal after installation
```

#### Step 4: Install VS Code or Cursor
```powershell
# Option A: VS Code (recommended)
winget install Microsoft.VisualStudioCode

# Option B: Cursor (AI-powered alternative)
winget install Cursor.Cursor

# Install WSL extension for VS Code
code --install-extension ms-vscode-remote.remote-wsl
```

#### Step 5: Install UV Package Manager
```powershell
# Install UV for Python package management
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Restart terminal to use UV
```

### 3. GitHub Setup

#### Create GitHub Account
1. Go to [github.com](https://github.com) and create an account
2. Configure Git with your credentials:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 4. Project Installation

#### Step 1: Clone the Repository
```bash
# In WSL2 or PowerShell
git clone https://github.com/Samulko/DF2025_Vizor_agents.git
cd DF2025_Vizor_agents
```

#### Step 2: Set Up Python Environment
```bash
# Create virtual environment
uv venv

# Activate environment (WSL2/Linux)
source .venv/bin/activate

# OR for PowerShell/Windows
.venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### 5. API Keys Setup

You'll need at least one of these API keys for the workshop:

#### Required APIs (choose at least one):
- **Google Gemini** (Recommended - free tier available): [Get API Key](https://makersuite.google.com/app/apikey)
- **OpenAI**: [Get API Key](https://platform.openai.com/api-keys)
- **Anthropic Claude**: [Get API Key](https://console.anthropic.com/)

#### Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys (use VS Code or nano)
code .env  # or nano .env
```

Add your API keys:
```env
# Add your actual API keys here
GEMINI_API_KEY=your_actual_gemini_key_here
OPENAI_API_KEY=your_actual_openai_key_here
ANTHROPIC_API_KEY=your_actual_anthropic_key_here
```

### 6. Optional: Voice Input Setup

For advanced features, you can set up voice input:

#### Step 1: Get Picovoice Access Key
1. Go to [Picovoice Console](https://console.picovoice.ai/)
2. Create free account and get access key

#### Step 2: Install Voice Dependencies
```bash
uv sync --extra voice
```

#### Step 3: Configure Voice Settings
Add to your `.env` file:
```env
ACCESS_KEY=your_picovoice_access_key_here
USE_OPENAI_API=true
```

### 7. Rhino + Grasshopper Setup

#### Install Rhino 8
1. Download from [rhino3d.com](https://www.rhino3d.com/)
2. Use trial or educational license

#### Install MCP Component
```bash
# Copy the Grasshopper component
cp src/bridge_design_system/mcp/GH_MCP/gha/GH_MCP.gha "%APPDATA%\Grasshopper\Libraries\"
```

### 8. Test Installation

#### Test Basic System
```bash
uv run python -m bridge_design_system.main --test
```

#### Test with Rhino (if available)
1. Open Rhino 8 + Grasshopper
2. Add "Grasshopper MCP" component to canvas
3. Set: Enabled=True, Port=8081, Address=0.0.0.0
4. Run the main system:
```bash
uv run python -m bridge_design_system.main
```

### 9. Workshop Verification Checklist

✅ **System Requirements:**
- [ ] Windows 10/11 with WSL2 installed
- [ ] Git installed and configured
- [ ] VS Code/Cursor with WSL extension
- [ ] UV package manager installed

✅ **Project Setup:**
- [ ] Repository cloned successfully
- [ ] Python virtual environment created
- [ ] Dependencies installed without errors
- [ ] At least one API key configured

✅ **Optional Components:**
- [ ] Rhino 8 installed (if available)
- [ ] Voice input configured (advanced users)
- [ ] Grasshopper MCP component installed

### 10. Quick Start Commands

Once everything is installed:

#### Standard Mode (Keyboard Input)
```bash
uv run python -m bridge_design_system.main
```

#### Voice Input Mode
```bash
uv run --extra voice python -m bridge_design_system.main --voice-input
```

#### Test Mode
```bash
uv run python -m bridge_design_system.main --test
```

### Troubleshooting

**Common Issues:**
- **UV not found**: Restart terminal after installation
- **WSL issues**: Run `wsl --update` and restart
- **API errors**: Check your `.env` file has valid API keys
- **Import errors**: Make sure virtual environment is activated

**Need Help?**
- Check the error logs in `logs/bridge_design_system.log`
- Ask workshop facilitators
- Check project documentation in `tutorials/` folder

## Advanced Features

### Voice Commands
Once voice input is set up, you can use:
- Say "Hello Mave" (wake word) to start voice input
- Speak your design command naturally  
- Examples: "Hello Mave" → "Create a spiral staircase with 10 steps"
- All system commands work: "status", "reset", "exit", etc.

### ROS-Free Mode
To run without ROS dependencies (disables gaze tracking):
```bash
uv run python -m bridge_design_system.main --disable-gaze
```

### LCARS Agent Monitoring Interface

The system includes a Star Trek LCARS-styled real-time monitoring interface to track agent status and activities.

**Start monitoring interface:**
```bash
# Option 1: Start monitoring with the main system
uv run python -m bridge_design_system.main 

# Option 2: Start monitoring interface separately
uv run python -m bridge_design_system.monitoring.lcars_interface
```

**Access the interface:**
- Open your browser to http://localhost:5000
- View real-time agent status (Triage, Geometry, SysLogic agents)
- Monitor task history and tool usage
- LCARS-styled interface with Star Trek theming

**Features:**
- Real-time WebSocket updates
- Agent status indicators (STANDBY, PROCESSING, ACTIVE, etc.)
- Task completion history with expandable details
- Network accessible (viewable from any device on local network)
- Automatic reconnection and heartbeat monitoring

## Architecture Overview

The system operates through the following flow:

```
WSL/Windows Environment -> MCP via STDIO -> STDIO MCP Server -> TCP Bridge (Port 8081) -> Grasshopper MCP Component -> Real-time Geometry Creation
```

### Multi-Agent System
* **Triage Agent**: Orchestrates design workflows.
* **Geometry Agent**: Controls Grasshopper for 3D modeling.
* **SysLogic**: Manages construction material data, validity of the strucutre that is being designed and handles post-rationalization process.

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
