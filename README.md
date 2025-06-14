# Vizor Agents - AR Bridge Design System

An AI-assisted bridge design system that uses intelligent agents to control Rhino Grasshopper for parametric design generation. Features multi-provider AI model support and MCP (Model Context Protocol) integration via STDIO transport for collaborative, iterative geometry creation.

## 🎯 Quick Start

### Prerequisites
- **Windows 10/11** (with optional WSL2)
- **Rhino 8** with Grasshopper
- **Python 3.10+**
- **UV package manager** ([install guide](https://docs.astral.sh/uv/))

### Installation

**1. Clone and Setup**

Windows (PowerShell):
```powershell
# Install UV if not already installed
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and setup
git clone <repository-url>
cd vizor_agents
uv venv
.venv\Scripts\activate
uv pip install -e .
```

WSL2/Linux:
```bash
git clone <repository-url>
cd vizor_agents
uv venv
source .venv/bin/activate
uv pip install -e .
```

**2. Configure API Keys**

Copy the example environment file and add your API keys:

Windows:
```powershell
copy .env.example .env
notepad .env
```

WSL2/Linux:
```bash
cp .env.example .env
nano .env  # or vim/code
```

The `.env.example` file contains:
```bash
# API Keys for LLM Providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
TOGETHER_API_KEY=your_together_key_here
HF_TOKEN=your_huggingface_token_here

# Model Selection for Each Agent
TRIAGE_AGENT_PROVIDER=deepseek
TRIAGE_AGENT_MODEL=deepseek-chat

GEOMETRY_AGENT_PROVIDER=anthropic
GEOMETRY_AGENT_MODEL=claude-3-5-sonnet-latest

# Additional configuration options...
```

**3. Setup Grasshopper Component**

**Option A: Use Pre-built Component**
- Copy the provided `GH_MCP.gha` file to `%APPDATA%\Grasshopper\Libraries\`

**Option B: For Developers**
- Open the solution in Visual Studio 2022
- Run in debug mode with the `.stp` file

**4. Configure Grasshopper**
- Restart Grasshopper
- Add "Grasshopper MCP" component to canvas
- Set: **Enabled=True**, **Port=8081**, **Address=0.0.0.0**

### Usage

Start a collaborative design session:
```powershell
uv run python -m bridge_design_system.main

# Start creating geometry with natural language:
# Designer> create a spiral staircase
# Designer> make the steps wider
# Designer> what are the available mcp tools?
```

**Available Commands:**
- `help` or `h` - Show available commands
- `status` or `st` - Show agent status and MCP connection
- `reset` or `rs` - Reset conversation history
- `clear` - Clear screen
- `exit` or `q` - Exit system

### Memory System

The bridge design system includes persistent memory that allows agents to remember context across sessions:

**How it works:**
- Components are automatically remembered when created
- Design context persists between conversations
- No more "what were we working on?" moments

**Memory Categories:**
- `components` - All created Grasshopper components with IDs and descriptions
- `context` - Current design goals, requirements, and session state
- `geometry` - Active geometry work and modifications
- `errors` - Problems encountered and their solutions

**Example Session:**
```powershell
# Session 1: Start a design
Designer> Create a timber truss bridge with 50m span
Agent: I'll create a timber truss bridge... [creates components]
       Stored component IDs: comp_truss_001, comp_deck_001

# Session 2: Continue work (even after restart)
Designer> What components have we created?
Agent: I can see from memory we have:
       - comp_truss_001: Main timber truss (50m span)
       - comp_deck_001: Bridge deck surface

Designer> Make the truss taller
Agent: I'll modify comp_truss_001 to increase height...
```

**Memory is stored in:** `src/bridge_design_system/data/memory/session_*.json`

## 🚀 Architecture

```
✅ WSL/Windows Environment (Multi-Provider AI)
    ↓ MCP via STDIO Transport
✅ STDIO MCP Server (Proven, reliable)
    ↓ Direct communication
✅ TCP Bridge (Port 8081)
    ↓ JSON command protocol
✅ Grasshopper MCP Component (C# bridge)
    ↓ Direct tool execution
✅ Real-time Collaborative Geometry Creation
```

**Key Features:**
- ✅ **Multi-Provider Support**: Gemini, OpenAI, Anthropic, DeepSeek, HuggingFace
- ✅ **Collaborative Design**: Iterative back-and-forth conversations
- ✅ **AI-generated 3D geometry**: Spirals, bridges, complex structures
- ✅ **6 core MCP tools** optimized for stability
- ✅ **Cross-platform**: WSL2 + native Windows support
- 🎉 **Conversation Memory**: Agents remember context between interactions
- 🎯 **Natural Modifications**: Say "make it wider" and the agent knows what to modify
- 🔧 **Dynamic Tool Discovery**: Ask "what are the available mcp tools?" for current capabilities
- 💬 **Interactive CLI**: User-friendly interface with commands and real-time status

### Multi-Agent System
- **Triage Agent**: Orchestrates complex design workflows
- **Geometry Agent**: Controls Grasshopper for 3D modeling ✅ **Working**
- **Material Agent**: Manages construction materials database
- **Structural Agent**: Performs engineering analysis

### MCP Integration (Model Context Protocol)

**STDIO Transport:**
- **Proven Architecture**: Reliable, works everywhere
- **On-demand Spawning**: Automatic lifecycle management
- **Direct Communication**: Seamless agent-to-Grasshopper connection

**Core Features:**
- **6 Optimized Tools**: Python scripting, component info, document management
- **TCP Bridge**: Custom C# component on port 8081
- **Session Management**: Proper connection lifecycle handling

### Multi-Provider AI Support
- **Anthropic**: Claude models for complex reasoning
- **DeepSeek**: Cost-effective option for orchestration
- **OpenAI**: GPT-4, GPT-3.5 models
- **HuggingFace & Together AI**: Additional options
- **Configurable Models**: Different agents can use different providers

## 📖 Available Tools

The system provides 6 optimized MCP tools for stable operation:

### Core Tools
- `add_python3_script` ✅ **Primary tool for geometry creation**
- `get_python3_script` - Retrieve script content
- `edit_python3_script` - Modify existing scripts
- `get_python3_script_errors` - Debug script issues
- `get_component_info_enhanced` - Component details
- `get_all_components_enhanced` - Document overview

### Why Only 6 Tools?
- **Stability First**: Minimal tool set ensures reliable operation
- **Python Power**: The Python script tool can create ANY geometry
- **Future Expansion**: Additional tools can be enabled as needed

### Python Script Examples
```python
# Create a spiral
import Rhino.Geometry as rg
import math
points = []
for i in range(50):
    t = i / 49.0
    angle = t * 2 * math.pi * 3
    radius = t * 5
    height = t * 10
    points.append(rg.Point3d(radius * math.cos(angle), 
                            radius * math.sin(angle), height))
a = rg.NurbsCurve.CreateInterpolatedCurve(points, 3)
```

## 🚨 Known Issues

*Currently no known issues. Please report any problems at the project repository.*

## 🔧 Configuration

### Network Configuration
The system automatically detects WSL network settings:
- **Auto-detection**: Uses `ip route` to find Windows host IP
- **Fallback**: Uses `/etc/resolv.conf` if needed
- **Configurable**: TCP bridge accepts custom bind addresses

## 🚨 Troubleshooting

### Common Issues

**1. Connection Refused**

Windows (PowerShell as Administrator):
```powershell
# Check Windows firewall for TCP bridge port
New-NetFirewallRule -DisplayName "MCP TCP Bridge" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow
```

WSL2 Specific:
```bash
# If WSL2 can't connect to Windows Grasshopper
# Check Windows host IP detection
ip route | grep default  # Should show Windows host IP
```

**2. Component Not Found**
```powershell
# Verify component deployment
dir "%APPDATA%\Grasshopper\Libraries\GH_MCP.gha"
```

**3. Platform-Specific Notes**

Windows Native:
- ✅ **Best Performance**: Direct localhost connections
- ✅ **UV Installation**: Use PowerShell installer script
- ✅ **Path Handling**: Automatic Windows path conversion
- ⚠️ **Admin Rights**: May need for firewall rules

WSL2:
- ✅ **Auto-Detection**: Finds Windows host IP automatically
- ✅ **Cross-Network**: Seamless WSL↔Windows communication
- 💡 **Tip**: Use `ip route | grep default` to verify connection

## 📚 Development

### Project Structure
```
vizor_agents/
├── src/bridge_design_system/          # Main system
│   ├── agents/                        # AI agents
│   │   ├── triage_agent.py           # Main orchestrator
│   │   └── geometry_agent_mcpadapt.py # Geometry control agent
│   ├── config/                        # Model & system configuration
│   ├── tools/                         # Agent tools
│   └── mcp/                          # MCP integration
│       └── GH_MCP/                   # C# Grasshopper component
├── tests/                            # Integration tests
└── main.py                           # Entry point
```

### Contributing
```bash
# Format code
black src/ tests/

# Run lints  
ruff check src/ tests/

# Run tests
pytest tests/
```

## 📄 License

MIT License - See LICENSE file for details.