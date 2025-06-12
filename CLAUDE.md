```markdown
# CLAUDE.md

AR-assisted bridge design system using AI agents for Rhino Grasshopper.

## Quick Start
```bash
# Windows only - run in PowerShell/Command Prompt (NOT WSL2)
uv venv
.venv\Scripts\activate
uv pip install -e .

# Test the system
uv run python -m bridge_design_system.main --test

# Start HTTP MCP server (separate terminal)
uv run python -m bridge_design_system.mcp.http_mcp_server --port 8001

# Run interactive mode
uv run python -m bridge_design_system.main --interactive
```

## Key Commands
- `uv run pytest tests/` - Run tests
- `uv run black src/ tests/` - Format code
- `uv run ruff check src/ tests/` - Lint code
- `uv run python test_http_mcp_integration.py` - Test MCP integration

## Architecture
- **Triage Agent**: Main orchestrator in `agents/triage_agent.py`
- **Geometry Agent**: Handles 3D geometry via MCP in `agents/geometry_agent_mcpadapt.py`
- **MCP Server**: HTTP server at port 8001 with 6 Grasshopper tools
- **TCP Bridge**: C# component communicates on port 8081

## Code Style
- Type hints required for all functions
- Google-style docstrings
- Use `@tool` decorator for agent tools
- Maximum 100 chars per line

## Git Workflow
- Branch from master: `feature/description`
- Keep branches short-lived (2-3 days max)
- Squash merge back to master
- Atomic commits with clear messages

## Environment Setup
1. Copy `.env.example` to `.env`
2. Set API keys (ANTHROPIC_API_KEY, etc.)
3. Default model: Gemini 2.5 Flash

## Common Issues
- WSL2 doesn't work - use native Windows
- MCP server must be running before agents
- TCP bridge component must be loaded in Grasshopper
- Port 8081 must be available for TCP bridge

## Project Structure
```
src/bridge_design_system/
├── agents/           # Agent implementations
├── config/           # Settings and configuration
├── tools/            # Agent tools
├── mcp/              # MCP integration
│   ├── http_mcp_server.py    # Main MCP server
│   └── GH_MCP/               # C# Grasshopper component
└── main.py           # Entry point
```
```

**What I changed:**
- Removed all emojis and visual clutter
- Cut 90% of the architectural exposition that Claude doesn't need
- Focused on commands Claude will actually use
- Removed redundant sections and implementation details
- Made it scannable with clear sections
- Kept only the most essential troubleshooting info
- Removed the "memories" sections which don't belong in CLAUDE.md

This follows the best practices from the Claude Code documentation - keep it concise, practical, and focused on what Claude needs to know to help you code effectively.