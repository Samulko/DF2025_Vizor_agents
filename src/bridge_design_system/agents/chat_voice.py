"""
Bridge Design Chat Agent using Gemini Live API.

Handles real-time voice conversation and delegates complex bridge design tasks
to the BridgeDesignSupervisor via tools. Follows OpenAI realtime agents pattern.
"""

import asyncio
import base64
import json
import os
import pathlib
from typing import AsyncGenerator, Literal, Dict, Any, List
import numpy as np
from dotenv import load_dotenv

try:
    from fastrtc import AsyncStreamHandler, Stream, wait_for_item
    from google import genai
    from google.genai.types import LiveConnectConfig, PrebuiltVoiceConfig, SpeechConfig, VoiceConfig
    CHAT_DEPENDENCIES_AVAILABLE = True
except ImportError:
    CHAT_DEPENDENCIES_AVAILABLE = False

from .triage_agent_smolagents import TriageSystemWrapper
from ..config.logging_config import get_logger

logger = get_logger(__name__)
load_dotenv()


def encode_audio(data: np.ndarray) -> str:
    """Encode Audio data to send to the server"""
    return base64.b64encode(data.tobytes()).decode("UTF-8")


class BridgeChatHandler(AsyncStreamHandler):
    """
    Chat handler for bridge design using Gemini Live API with bridge design supervisor tools.
    
    This handles:
    - Real-time voice conversation 
    - Simple bridge engineering questions
    - Tool calls to bridge design supervisor for complex tasks
    """

    def __init__(self, expected_layout: Literal["mono"] = "mono", output_sample_rate: int = 24000):
        super().__init__(expected_layout, output_sample_rate, input_sample_rate=16000)
        
        # Initialize triage system directly
        self.triage_system = TriageSystemWrapper()
        
        # Async queues for audio
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()
        
        logger.info("🌉 Bridge chat handler initialized with triage system")

    def copy(self) -> "BridgeChatHandler":
        return BridgeChatHandler(expected_layout="mono", output_sample_rate=self.output_sample_rate)

    async def start_up(self):
        """Initialize Gemini Live session with bridge design tools."""
        print("🔧 [DEBUG] Starting Gemini Live session initialization...")
        
        # Get API key from environment directly (no user input required)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
        
        print("✅ [DEBUG] API key found, creating Gemini client...")
        
        # Get voice selection from UI if available, otherwise default
        if not self.phone_mode:
            print("🎤 [DEBUG] Waiting for voice selection from UI...")
            await self.wait_for_args()
            voice_name = self.latest_args[1] if len(self.latest_args) > 1 else "Puck"
        else:
            voice_name = "Puck"  # Default voice for phone mode
        
        print(f"🗣️  [DEBUG] Selected voice: {voice_name}")
        
        client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"},
        )

        # Create tools and get debug info
        tools = self._create_gemini_tools()
        print(f"🛠️  [DEBUG] Created {len(tools)} Gemini tools for function calling")
        for i, tool in enumerate(tools):
            # Handle new dictionary format for Live API tools
            if isinstance(tool, dict) and 'function_declarations' in tool:
                for func_decl in tool['function_declarations']:
                    print(f"    Tool {i+1}: {func_decl['name']} - {func_decl['description'][:50]}...")
                    print(f"    Tool {i+1} Parameters: {list(func_decl['parameters']['properties'].keys())}")
            else:
                # Fallback for old format (shouldn't happen now)
                print(f"    Tool {i+1}: {tool} - Unknown format")

        # Use Gemini API-compliant tool declaration
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": voice_name}
                }
            },
            "tools": tools,
            "system_instruction": self._get_bridge_chat_prompt(),
        }
        
        print("🚀 [DEBUG] Connecting to Gemini Live API...")

        print(f"🔧 [DEBUG] Config being sent to Gemini Live API:")
        print(f"    Response Modalities: {config['response_modalities']}")
        print(f"    Voice Name: {config['speech_config']['voice_config']['prebuilt_voice_config']['voice_name']}")
        print(f"    Tools: {[tool['function_declarations'][0]['name'] for tool in config['tools']]}")
        print(f"    System Instruction Length: {len(config['system_instruction'])} chars")
        
        async with client.aio.live.connect(model="gemini-2.0-flash-live-001", config=config) as session:
            print("✅ [DEBUG] Connected to Gemini Live API successfully!")
            print(f"🔗 [DEBUG] Session object: {type(session)}")
            print(f"🔧 [DEBUG] Session available methods: {[attr for attr in dir(session) if not attr.startswith('_')]}")
            print("🎧 [DEBUG] Audio streaming active - you can now speak to the system")
            print("🔄 [DEBUG] Waiting for user input...")
            
            # Handle tool calls with enhanced debugging
            print("🛠️  [DEBUG] Using manual tool call detection (Live API requires manual handling)")
            
            # Check if session has tool-related attributes
            tool_attrs = [attr for attr in dir(session) if 'tool' in attr.lower()]
            if tool_attrs:
                print(f"🔍 [DEBUG] Session tool-related attributes: {tool_attrs}")
            
            # Store session for manual tool handling
            self.session = session
            
            print("🛠️  [DEBUG] Starting audio stream with manual tool detection...")
            
            # Use start_stream like the multimodal version but with manual tool detection
            async for audio in session.start_stream(stream=self.stream(), mime_type="audio/pcm"):
                print(f"📨 [DEBUG] Received audio response: {type(audio)}")
                
                # Enhanced response debugging
                if hasattr(audio, '__dict__'):
                    print(f"📨 [DEBUG] Audio response attributes: {list(audio.__dict__.keys())}")
                
                # Handle audio data
                if audio.data:
                    print(f"🔊 [DEBUG] Audio data received: {len(audio.data)} bytes")
                    array = np.frombuffer(audio.data, dtype=np.int16)
                    self.output_queue.put_nowait((self.output_sample_rate, array))
                
                # Check for tool calls in the audio response
                if hasattr(audio, 'tool_call') and audio.tool_call:
                    print("\n" + "🎆"*60)
                    print("🎆 [BREAKTHROUGH] VOICE TOOL CALL IN AUDIO! 🎆")
                    print("🎆"*60)
                    await self._handle_tool_call(audio.tool_call)
                
                # Check for server content with tool calls
                if hasattr(audio, 'server_content') and audio.server_content:
                    if hasattr(audio.server_content, 'tool_call') and audio.server_content.tool_call:
                        print("\n" + "🎆"*60)
                        print("🎆 [BREAKTHROUGH] VOICE TOOL CALL IN SERVER CONTENT! 🎆")
                        print("🎆"*60)
                        await self._handle_tool_call(audio.server_content.tool_call)
    

    def _create_gemini_tools(self):
        """Create tool declarations for Gemini Live API (function_declarations format)."""
        
        # Define the function declaration for Live API
        bridge_design_request_declaration = {
            "name": "bridge_design_request",
            "description": "Send user request directly to the bridge design triage agent. This function implements the chat-to-triage pattern where the chat agent forwards all bridge design requests to the smolagents triage system which coordinates geometry agents, structural analysis, and other specialized agents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "The user's request about bridge design, engineering, or system operations"
                    }
                },
                "required": ["user_request"]
            }
        }
        
        # Return in Live API format
        tools = [{"function_declarations": [bridge_design_request_declaration]}]
        logger.info(f"✅ Created {len(tools)} tool declarations for Live API")
        return tools
    
    def _execute_bridge_design_request(self, user_request: str) -> str:
        """Execute the bridge design request - the actual Python function."""
        import time
        print("\n" + "🎆"*50)
        print("🎆 [MAJOR SUCCESS] VOICE TOOL FUNCTION CALLED! 🎆")
        print("🎆"*50)
        print("\n" + "="*80)
        print("🚨 [FUNCTION CALL] Executing bridge_design_request()")
        print(f"📝 [USER REQUEST] {user_request}")
        print(f"🕰 [TIMESTAMP] {time.time()}")
        print(f"🔍 [CALL STACK] Called from Gemini Live API")
        print("="*80)
        
        try:
            # ALL triage system calls should run in background to keep voice interface responsive
            # Even "simple" queries can take 10-20 seconds due to MCP connections and agent coordination
            print("🎯 [DEBUG] Running all triage requests in background to maintain voice responsiveness...")
            logger.info(f"🎯 Background task forwarded to triage agent: {user_request[:100]}...")
            
            # Start the task asynchronously but return immediate response
            import asyncio
            asyncio.create_task(self._run_background_task(user_request))
            
            return f"I'm processing your request: '{user_request}'. The bridge design agents are working on this. You can continue chatting with me while they work - I'll respond with the results shortly!"
                
        except Exception as e:
            print(f"💥 [ERROR] Exception in bridge_design_request: {e}")
            logger.error(f"Error calling triage agent: {e}")
            import traceback
            traceback.print_exc()
            return f"Error communicating with bridge design system: {str(e)}"

    async def _run_background_task(self, user_request: str):
        """Execute bridge design task in background while allowing continued conversation."""
        try:
            print(f"🎯 [BACKGROUND] Starting background task: {user_request[:50]}...")
            logger.info(f"🎯 Starting background task: {user_request[:100]}...")
            
            # Call the triage system directly (this is the blocking call that now runs in background)
            print("🔧 [BACKGROUND] Calling triage system...")
            response = self.triage_system.handle_design_request(user_request)
            
            print(f"📊 [BACKGROUND] Background task completed:")
            print(f"    Success: {response.success}")
            print(f"    Message length: {len(response.message) if response.message else 0} characters")
            
            if response.success:
                print("✅ [BACKGROUND] Background task completed successfully")
                print(f"📤 [BACKGROUND RESULT] {response.message}")
                logger.info(f"✅ Background task completed: {response.message}")
                
                # TODO: In future, could send this result back to user via voice
                # For now, user can ask "what was the result?" to get updates
                
            else:
                print(f"❌ [BACKGROUND] Background task failed: {response.message}")
                logger.error(f"❌ Background task failed: {response.message}")
                
        except Exception as e:
            print(f"💥 [BACKGROUND] Background task exception: {e}")
            logger.error(f"Background task error: {e}")
            import traceback
            traceback.print_exc()

    async def _handle_tool_call(self, tool_call):
        """Handle tool calls from Gemini Live session."""
        try:
            print("\n" + "🎆"*50)
            print("🎆 [BREAKTHROUGH] GEMINI TOOL CALL HANDLER TRIGGERED! 🎆")
            print("🎆"*50)
            print("\n" + "🔥"*50)
            print("🔥 [TOOL CALL HANDLER] Gemini Live called _handle_tool_call()")
            print(f"🔥 [TOOL CALL TYPE] {type(tool_call)}")
            print(f"🔥 [TOOL CALL DETAILS] {tool_call}")
            print(f"🔥 [TOOL CALL ATTRS] {dir(tool_call) if hasattr(tool_call, '__dict__') else 'No attributes'}")
            if hasattr(tool_call, '__dict__'):
                print(f"🔥 [TOOL CALL DICT] {tool_call.__dict__}")
            print("🔥"*50)
            
            logger.info(f"🛠️ Handling Gemini function call: {tool_call}")
            
            # Handle manual function calls - Live API requires manual handling
            if hasattr(tool_call, 'function_calls'):
                function_responses = []
                
                for fc in tool_call.function_calls:
                    print(f"📝 [FUNCTION CALL] Name: {fc.name}")
                    print(f"📝 [FUNCTION CALL] ID: {fc.id}")
                    print(f"📝 [FUNCTION CALL] Args: {fc.args}")
                    
                    # Execute the actual function based on name
                    if fc.name == "bridge_design_request":
                        # Extract arguments
                        user_request = fc.args.get("user_request", "")
                        
                        print(f"🎯 [EXECUTING] bridge_design_request with args: {fc.args}")
                        
                        # Call the actual function
                        result = self._execute_bridge_design_request(user_request)
                        
                        # Create function response for Live API
                        from google.genai import types
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response={"result": result}
                        )
                        function_responses.append(function_response)
                        
                        print(f"✅ [FUNCTION RESPONSE] Created response for {fc.name}")
                    else:
                        print(f"❌ [UNKNOWN FUNCTION] {fc.name}")
                        # Create error response
                        from google.genai import types
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response={"error": f"Unknown function: {fc.name}"}
                        )
                        function_responses.append(function_response)
                
                # Send tool responses back to Gemini Live API
                if function_responses:
                    print(f"📤 [SENDING RESPONSES] {len(function_responses)} responses to Gemini")
                    await self.session.send_tool_response(function_responses=function_responses)
                    print("✅ [RESPONSES SENT] Tool responses sent to Gemini Live API")
                
                return {"status": "Function calls handled successfully"}
            else:
                print("❌ [ERROR] No function_calls attribute found in tool_call")
                return {"error": "No function_calls found in tool_call"}
                
        except Exception as e:
            print(f"💥 [ERROR] Tool call handler failed: {e}")
            logger.error(f"❌ Tool call handler error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _get_bridge_chat_prompt(self) -> str:
        """Get system prompt for bridge design chat agent from markdown file."""
        prompt_path = pathlib.Path(__file__).parent.parent.parent / ".." / ".." / "system_prompts" / "chat_agent.md"
        prompt_path = prompt_path.resolve()
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not load system prompt from {prompt_path}: {e}. Using fallback.")
            return """You are a helpful bridge design assistant that can have natural conversations about bridge engineering.

You have access to a specialized bridge design supervisor that coordinates geometry and structural analysis agents for complex tasks.

**CRITICAL: You MUST use the bridge_design_request tool for ALL bridge design requests, no matter how simple they seem.**

**For simple questions**, you can respond directly:
- Basic bridge engineering concepts
- Material properties and standards
- General design principles
- Terminology explanations

**For ANY bridge design tasks**, you MUST use the bridge_design_request tool:
- Creating or modifying bridge components
- Structural analysis and calculations  
- Parametric design in Grasshopper
- Multi-step engineering workflows
- Component coordination
- System status checks
- Any request related to bridge design

Available tools:
- `bridge_design_request`: For ALL bridge design and engineering tasks - USE THIS TOOL FREQUENTLY

Examples of when to use bridge_design_request:
- "Show me the current bridge design status" -> USE TOOL
- "Create a simple beam bridge" -> USE TOOL  
- "What tools are available?" -> USE TOOL
- "Reset the design session" -> USE TOOL

Keep responses concise and natural for voice interaction. Be technical but accessible. When using tools, explain what you're doing and interpret the results for the user.

REMEMBER: When in doubt, use the bridge_design_request tool. It's better to use it too often than not enough."""

    async def stream(self) -> AsyncGenerator[bytes, None]:
        """Stream audio data to Gemini Live."""
        while not self.quit.is_set():
            try:
                audio = await asyncio.wait_for(self.input_queue.get(), 0.1)
                yield audio
            except (asyncio.TimeoutError, TimeoutError):
                pass

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        """Receive audio frame from user."""
        _, array = frame
        array = array.squeeze()
        audio_message = encode_audio(array)
        self.input_queue.put_nowait(audio_message)

    async def emit(self) -> tuple[int, np.ndarray] | None:
        """Emit audio response to user."""
        return await wait_for_item(self.output_queue)

    def shutdown(self) -> None:
        """Shutdown handler."""
        self.quit.set()


# Factory function to create the complete bridge chat system
def create_bridge_chat_stream(server_port: int = 7860, share: bool = False):
    """
    Create bridge design chat stream with Gemini Live API and supervisor tools.
    
    This replaces the mixed VoiceBridgeDesignAgent with clean separation:
    - Chat: Gemini Live API handles voice and conversation
    - Supervisor: Bridge design coordination via tools
    """
    if not CHAT_DEPENDENCIES_AVAILABLE:
        raise ImportError(
            "Chat dependencies not available. Install with:\n"
            "  uv add google-genai fastrtc"
        )
    
    import gradio as gr
    
    stream = Stream(
        modality="audio",
        mode="send-receive",
        handler=BridgeChatHandler(),
        concurrency_limit=5,
        time_limit=90,
        ui_args={
            "pulse_color": "rgb(0, 123, 255)",  # Bridge blue
            "icon_button_color": "rgb(0, 123, 255)",
            "title": "🌉 Bridge Design Chat Assistant (Chat-Supervisor)",
            "description": "Voice chat for bridge design with specialized supervisor coordination",
        },
        additional_inputs=[
            gr.Dropdown(
                label="Voice",
                choices=["Puck", "Charon", "Kore", "Fenrir", "Aoede"],
                value="Puck",
                info="Select Gemini voice for responses"
            ),
        ],
    )
    
    logger.info(f"✅ Bridge chat stream ready on port {server_port}")
    return stream


def launch_bridge_chat_agent(server_port: int = 7860, share: bool = False, debug: bool = True):
    """Launch bridge design chat agent with voice interface."""
    
    if not CHAT_DEPENDENCIES_AVAILABLE:
        print("❌ Chat dependencies not available.")
        print("Install with:")
        print("  uv add google-genai fastrtc")
        return
    
    print("🌉 Starting Bridge Design Chat Agent (Chat-Supervisor Pattern)")
    print("=" * 60)
    print("💬 Chat Layer: Gemini Live API")  
    print("🔧 Supervisor Layer: Bridge Design Coordination")
    print("🎤 Voice Interface: Real-time conversation")
    print("🛠️ Tools: Bridge design supervisor callable via voice")
    print(f"🌐 Web Interface: http://localhost:{server_port}")
    print()
    print("🐛 [DEBUG MODE] Console debugging enabled:")
    print("   - Function calls will be logged with 🚨 markers")
    print("   - Triage agent interactions will be logged with 🎯 markers")
    print("   - Errors will be logged with 💥 markers")
    print("   - Tool calls will be logged with 🔥 markers")
    print()
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your API key in your .env file:")
        print("  echo 'GEMINI_API_KEY=your_api_key_here' >> .env")
        print("Then restart the application.")
        return
    
    print("✅ [DEBUG] GEMINI_API_KEY found in environment")
    
    try:
        print("🚀 [DEBUG] Creating bridge chat stream...")
        # Create and launch
        chat_stream = create_bridge_chat_stream(server_port, share)
        print("🌐 [DEBUG] Launching web interface...")
        print(f"📱 [DEBUG] Open your browser to: http://localhost:{server_port}")
        print("🎤 [DEBUG] Click the microphone button and speak to test the system")
        print()
        print("💡 [USAGE TIP] Try saying:")
        print("   'What is the current bridge design status?'")
        print("   'Create a simple beam bridge'")
        print("   'Show me available tools'")
        print()
        chat_stream.ui.launch(server_port=server_port, share=share, debug=debug)
        
    except Exception as e:
        logger.error(f"Failed to launch chat agent: {e}")
        print(f"❌ Launch failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check API key: export GEMINI_API_KEY=your_key")
        print("2. Install dependencies: uv add google-genai fastrtc")
        print("3. Check network connectivity")


# Alternative text-based chat interface for testing
class BridgeTextChatInterface:
    """
    Text-based interface for bridge design chat (for testing without voice).
    
    Uses the same supervisor tools but via text input/output.
    """
    
    def __init__(self):
        """Initialize text chat interface."""
        self.triage_system = TriageSystemWrapper()
        logger.info("🌉 Bridge text chat interface initialized")
    
    def chat_loop(self):
        """Run interactive text chat loop."""
        print("🌉 Bridge Design Text Chat Interface")
        print("=" * 50)
        print("Available commands:")
        print("  <any request>    - Send request to triage agent")
        print("  status           - Get system status")
        print("  reset            - Reset design session")
        print("  help             - Show this help")
        print("  exit             - Exit chat")
        print()
        
        while True:
            try:
                user_input = input("🌉 Bridge Chat> ").strip()
                
                if user_input.lower() == "exit":
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == "help":
                    self._show_help()
                elif user_input.lower() == "status":
                    status = self.triage_system.get_status()
                    print(f"📊 Status: {json.dumps(status, indent=2)}")
                elif user_input.lower() == "reset":
                    self.triage_system.reset_all_agents()
                    print("🔄 Reset: All agent memories cleared")
                elif user_input:
                    # Send any non-empty request to triage agent
                    print("\n" + "="*60)
                    print("🎯 [TEXT CHAT] Sending to triage agent...")
                    print(f"📝 [USER INPUT] {user_input}")
                    print("="*60)
                    
                    try:
                        print("🔧 [DEBUG] Calling triage_system.handle_design_request()...")
                        response = self.triage_system.handle_design_request(user_input)
                        
                        print(f"📊 [DEBUG] Response received:")
                        print(f"    Success: {response.success}")
                        print(f"    Message length: {len(response.message) if response.message else 0} characters")
                        
                        if response.success:
                            print("✅ [SUCCESS] Triage agent completed successfully")
                            print(f"📤 [RESPONSE] {response.message}")
                        else:
                            print("❌ [FAILURE] Triage agent failed")
                            print(f"💥 [ERROR] {response.message}")
                            
                    except Exception as e:
                        print(f"💥 [EXCEPTION] Error in text chat: {e}")
                        import traceback
                        traceback.print_exc()
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information."""
        print("🌉 Bridge Design Chat Commands:")
        print("  <any request>    - Send any request to triage agent")
        print("                     Examples:")
        print("                     'Create a cable stayed bridge'")
        print("                     'Modify element 021 center point'")
        print("                     'What is the current design status?'")
        print("  status           - Check triage system and agent status")
        print("  reset            - Clear all agent memories for fresh start")
        print("  help             - Show this help message")
        print("  exit             - Exit the chat interface")
        print()
        print("💡 All requests are sent to the triage agent which")
        print("   coordinates geometry and rational agents automatically.")


def launch_text_chat():
    """Launch text-based bridge design chat for testing."""
    try:
        chat = BridgeTextChatInterface()
        chat.chat_loop()
    except Exception as e:
        logger.error(f"Text chat failed: {e}")
        print(f"❌ Text chat error: {e}")


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "voice":
            launch_bridge_chat_agent(debug=True)
        elif sys.argv[1] == "text":
            launch_text_chat()
        else:
            print("Usage: python bridge_chat_agent.py [voice|text]")
    else:
        print("🌉 Bridge Design Chat Agent")
        print("Usage:")
        print("  python bridge_chat_agent.py voice  # Voice interface")
        print("  python bridge_chat_agent.py text   # Text interface")
        print()
        print("Dependencies:")
        print("  uv add google-genai fastrtc") 