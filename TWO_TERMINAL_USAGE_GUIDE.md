# Two-Terminal Architecture Usage Guide

The bridge design system now supports a **two-terminal architecture** where the voice interface runs separately from the main bridge design system, communicating via TCP IPC.

## Architecture Overview

```
Terminal 1: main.py                    Terminal 2: chat_voice.py
┌─────────────────────────────┐       ┌─────────────────────────────┐
│ Bridge Design System        │       │ Voice Interface             │
│                             │       │                             │
│ • Triage Agent             │◄─────►│ • Gemini Live API           │
│ • Geometry Agent           │  TCP  │ • Audio Streaming           │
│ • Material Agent           │ 8082  │ • Function Calls            │
│ • Component Registry       │       │ • IPC Client                │
│ • Command Server           │       │                             │
└─────────────────────────────┘       └─────────────────────────────┘
```

## Benefits

✅ **Reliable**: Voice session crashes don't affect main bridge design system  
✅ **Scalable**: Multiple voice clients can connect to one main system  
✅ **Fast**: No session timeouts or complex threading  
✅ **Debuggable**: Clear separation of voice vs bridge design processing  

## Quick Start

### Step 1: Start Main Bridge Design System (Terminal 1)

```bash
# Start the main bridge design system with command server
python -m bridge_design_system.main --interactive --enable-command-server

# Or use the shorter version
python -m bridge_design_system.main -i --enable-command-server
```

**Expected Output:**
```
🚀 Starting TCP command server for external voice interfaces...
✅ TCP command server started on localhost:8082
📡 External voice interfaces can now connect

AR-Assisted Bridge Design System
🚀 Using smolagents-native implementation (DEFAULT)
⌨️ Keyboard input mode - type commands normally
🚀 TCP Command Server enabled on localhost:8082
📡 External voice interfaces can connect via TCP
🎤 Use voice chat agent in separate terminal

Designer> 
```

### Step 2: Start Voice Interface (Terminal 2)

```bash
# Start the voice interface
python -m bridge_design_system.agents.chat_voice voice

# Or start text interface for testing
python -m bridge_design_system.agents.chat_voice text
```

**Expected Output:**
```
🌉 Starting Bridge Design Chat Agent (Chat-Supervisor Pattern)
💬 Chat Layer: Gemini Live API  
🔧 Supervisor Layer: Bridge Design Coordination
🎤 Voice Interface: Real-time conversation
🛠️ Tools: Bridge design supervisor callable via voice
🌐 Web Interface: http://localhost:7860

✅ [DEBUG] GEMINI_API_KEY found in environment
🚀 [DEBUG] Creating bridge chat stream...
```

## Testing the Architecture

### Test 1: Voice Interface

1. Open browser to `http://localhost:7860`
2. Click the microphone button
3. Say: "What is the current bridge design status?"
4. Observe:
   - Terminal 2 shows IPC communication
   - Terminal 1 processes the request
   - Voice response is generated

### Test 2: Text Interface

```bash
# In Terminal 2
python -m bridge_design_system.agents.chat_voice text
```

Type commands like:
- `Create a simple beam bridge`
- `What tools are available?`
- `Show me the current design status`

### Test 3: CLI Commands

In Terminal 1, you can still use CLI commands:
- `status` - See system status
- `reset` - Reset agent memories
- `exit` - Exit system

## Command Flow

1. **User speaks** to voice interface (Terminal 2)
2. **Gemini Live API** processes speech and calls `bridge_design_request` tool
3. **IPC Client** sends request via TCP to main system (Terminal 1)
4. **Command Server** receives request and forwards to triage agent
5. **Triage Agent** processes request using geometry/material agents
6. **Response** sent back via TCP to voice interface
7. **Voice response** generated and played to user

## Troubleshooting

### Connection Refused
```
❌ Connection refused to localhost:8082
💡 Make sure main.py is running with --enable-command-server
```
**Solution**: Start Terminal 1 first with `--enable-command-server`

### Voice Dependencies Missing
```
❌ Chat dependencies not available.
Install with: uv add google-genai fastrtc
```
**Solution**: Install voice dependencies
```bash
uv add google-genai fastrtc
```

### API Key Missing
```
❌ Error: GEMINI_API_KEY not found in environment variables
```
**Solution**: Add to your `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

## Advanced Usage

### Multiple Voice Clients
You can run multiple voice interfaces connecting to the same main system:

```bash
# Terminal 1: Main system
python -m bridge_design_system.main -i --enable-command-server

# Terminal 2: Voice client 1 (port 7860)
python -m bridge_design_system.agents.chat_voice voice

# Terminal 3: Voice client 2 (port 7861)  
# Modify port in chat_voice.py or add CLI argument
```

### Monitoring
Enable monitoring in main system:
```bash
python -m bridge_design_system.main -i --enable-command-server --monitoring
```

Access monitoring at `http://localhost:5000`

### Voice Input for Main System
You can still use voice input in the main system:
```bash
python -m bridge_design_system.main -i --enable-command-server --voice-input
```

## Architecture Details

### IPC Protocol
- **Transport**: TCP socket on localhost:8082
- **Format**: JSON messages with length prefix
- **Timeout**: 30 seconds per request
- **Concurrent**: Multiple clients supported

### Message Format
```json
// Request (Terminal 2 → Terminal 1)
{
  "type": "bridge_design_request",
  "task_id": "abc123",
  "user_request": "Create a cable stayed bridge", 
  "timestamp": "2025-01-04T10:30:00Z"
}

// Response (Terminal 1 → Terminal 2)
{
  "type": "bridge_design_response",
  "task_id": "abc123", 
  "success": true,
  "message": "Bridge created successfully...",
  "timestamp": "2025-01-04T10:30:05Z"
}
```

### Error Handling
- **Connection errors**: Automatic retry with exponential backoff
- **Timeout errors**: Graceful degradation with error messages  
- **Processing errors**: Detailed error reporting via IPC
- **Voice errors**: Fallback to keyboard input

## Migration from Single Terminal

If you were previously using:
```bash
python -m bridge_design_system.main --interactive --voice-input
```

Now use this two-terminal approach:
```bash
# Terminal 1
python -m bridge_design_system.main -i --enable-command-server

# Terminal 2  
python -m bridge_design_system.agents.chat_voice voice
```

The new architecture provides better reliability and separation of concerns.