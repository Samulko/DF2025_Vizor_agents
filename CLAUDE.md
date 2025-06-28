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

# Run interactive mode (keyboard input)
uv run python -m bridge_design_system.main --interactive

# Run with voice input (requires voice dependencies)
uv run --extra voice python -m bridge_design_system.main --voice-input
```

## Key Commands
- `uv run pytest tests/` - Run tests
- `uv run black src/ tests/` - Format code
- `uv run ruff check src/ tests/` - Lint code
- `uv run python test_http_mcp_integration.py` - Test MCP integration
- `jupyter notebook` - Start educational notebooks (requires `uv pip install jupyter`)

## Workflows

### Explore, Plan, Code, Commit
Best for complex problems that need research:

1. **Explore**: "Read agents/geometry_agent.py and the MCP integration files, but don't write any code yet"
2. **Plan**: "Think hard about how to implement [feature]. Create a plan document"
   - Use: "think" → "think hard" → "think harder" → "ultrathink" for increasing computation
3. **Code**: "Implement the solution from your plan. Verify each step as you go"
4. **Commit**: "Commit the changes and create a PR. Update the README"

### Test-Driven Development
Best for features with clear inputs/outputs:

1. **Write tests**: "Write tests for [feature] using pytest. This is TDD - don't create implementations"
2. **Verify tests fail**: "Run the tests and confirm they fail. Don't write implementation code"
3. **Commit tests**: "Commit just the test files"
4. **Implement**: "Write code to make all tests pass. Don't modify the tests. Keep iterating until green"
5. **Commit code**: "Commit the implementation"

## Architecture
- **Triage Agent**: Main orchestrator in `agents/triage_agent.py`
- **Geometry Agent**: Handles 3D geometry via MCP in `agents/geometry_agent_mcpadapt.py`
- **Bridge Reference Agent**: Searches real-world bridge info in `agents/bridge_reference_agent.py`
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
2. Set API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
3. Default model: Gemini 2.5 Flash

### Voice Input Setup (Optional)
For voice commands instead of typing:
1. **Install voice dependencies**: `uv sync --extra voice`
2. **Get Picovoice access key**: Sign up at [Picovoice Console](https://console.picovoice.ai/)
3. **Add to .env**:
   ```
   ACCESS_KEY=your_picovoice_key_here
   WAKE_WORD_MODEL_PATH=src/bridge_design_system/whisper-voice-assistant/models/hello-mave_en_linux_v3_0_0.ppn
   WHISPER_MODEL=tiny.en
   VAD_SENSITIVITY=0.7
   USE_OPENAI_API=true
   ```
4. **Run with voice**: `uv run --extra voice python -m bridge_design_system.main --voice-input`

## Common Issues
- MCP server must be running before agents
- TCP bridge component must be loaded in Grasshopper
- Port 8081 must be available for TCP bridge

##Tools
- USE context7 mcp and git-mcp to find relevant documentation and information about current tasks.
- Make sure to ask yourself a question if a given task would benefit from more context or beter framework understanding if so you MUST use the mcp tools

## Input Modes

### Keyboard Input (Default)
- Type commands normally in the CLI
- Use for development and testing
- No additional dependencies required

### Voice Input
- **Wake Word**: Say "Hello Mave" to start voice command
- **Voice Activity Detection**: System automatically detects when you stop speaking
- **Speech Recognition**: Uses OpenAI Whisper API for transcription
- **Fallback**: Automatically falls back to keyboard if voice fails
- **All Features**: Gaze tracking and transform processing work with voice commands

**Voice Commands:**
- Say wake word → speak command → system processes speech
- Examples: "Hello Mave" → "Show me the current status"
- System commands: "reset", "status", "exit", "gaze" all work via voice

## Project Structure
```
src/bridge_design_system/
├── agents/           # Agent implementations
├── config/           # Settings and configuration
├── tools/            # Agent tools
├── mcp/              # MCP integration
│   ├── http_mcp_server.py    # Main MCP server
│   └── GH_MCP/               # C# Grasshopper component
├── voice_input.py    # Voice input integration
├── whisper-voice-assistant/  # Voice assistant components
│   ├── voice_assistant.py   # Standalone voice assistant
│   ├── models/              # Wake word models (.ppn files)
│   └── .env                 # Voice configuration
└── main.py           # Entry point
```

## Claude's Operational Directive
- Be direct and critical
- If unsure, say "I don't know"
- If something won't work, clearly state it won't work
- No BS answers
- Prioritize practical, realistic approaches
- Please correct me if I am wrong