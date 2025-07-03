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

from .triage_chat_supervisor import BridgeDesignSupervisor, create_bridge_design_supervisor_tools
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
        
        # Initialize bridge design supervisor
        self.bridge_supervisor = BridgeDesignSupervisor()
        self.supervisor_tools = create_bridge_design_supervisor_tools(self.bridge_supervisor)
        
        # Async queues for audio
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()
        
        logger.info("🌉 Bridge chat handler initialized with supervisor tools")

    def copy(self) -> "BridgeChatHandler":
        return BridgeChatHandler(expected_layout="mono", output_sample_rate=self.output_sample_rate)

    async def start_up(self):
        """Initialize Gemini Live session with bridge design tools."""
        # Get API key from environment directly (no user input required)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
        
        # Get voice selection from UI if available, otherwise default
        if not self.phone_mode:
            await self.wait_for_args()
            voice_name = self.latest_args[1] if len(self.latest_args) > 1 else "Puck"
        else:
            voice_name = "Puck"  # Default voice for phone mode
        
        client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"},
        )

        # Use Gemini API-compliant tool declaration
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": voice_name}
                }
            },
            "tools": self._create_gemini_tools(),
            "system_instruction": self._get_bridge_chat_prompt(),
        }

        async with client.aio.live.connect(model="gemini-live-2.5-flash-preview", config=config) as session:
            # Handle tool calls
            session.on_tool_call = self._handle_tool_call
            
            async for audio in session.start_stream(stream=self.stream(), mime_type="audio/pcm"):
                if audio.data:
                    array = np.frombuffer(audio.data, dtype=np.int16)
                    self.output_queue.put_nowait((self.output_sample_rate, array))

    def _create_gemini_tools(self):
        """Convert bridge supervisor tools to Gemini Live API function_declarations format."""
        gemini_tools = []
        for tool_func in self.supervisor_tools:
            try:
                # Handle smolagents tool objects
                if hasattr(tool_func, 'name'):
                    tool_name = tool_func.name
                    tool_description = getattr(tool_func, 'description', f"Bridge design tool: {tool_name}")
                    actual_func = tool_func.fn if hasattr(tool_func, 'fn') else tool_func
                else:
                    tool_name = tool_func.__name__
                    tool_description = tool_func.__doc__ or f"Bridge design tool: {tool_name}"
                    actual_func = tool_func
                import inspect
                sig = inspect.signature(actual_func)
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                for param_name, param in sig.parameters.items():
                    param_type = "string"
                    param_desc = f"Parameter: {param_name}"
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == str:
                            param_type = "string"
                        elif param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == bool:
                            param_type = "boolean"
                        elif param.annotation == dict or param.annotation == Dict:
                            param_type = "object"
                    parameters["properties"][param_name] = {
                        "type": param_type,
                        "description": param_desc
                    }
                    if param.default == inspect.Parameter.empty:
                        parameters["required"].append(param_name)
                tool_def = {
                    "function_declarations": [{
                        "name": tool_name,
                        "description": tool_description,
                        "parameters": parameters
                    }]
                }
                gemini_tools.append(tool_def)
            except Exception as e:
                tool_name = getattr(tool_func, 'name', getattr(tool_func, '__name__', 'unknown'))
                logger.warning(f"Could not convert tool {tool_name}: {e}")
        logger.info(f"✅ Created {len(gemini_tools)} Gemini Live tools (Gemini API format)")
        return gemini_tools

    async def _handle_tool_call(self, tool_call):
        """Handle tool calls from Gemini Live session."""
        try:
            tool_name = tool_call.name
            tool_args = tool_call.args or {}
            
            logger.info(f"🛠️ Handling tool call: {tool_name}")
            
            # Find the corresponding supervisor tool
            tool_func = None
            for func in self.supervisor_tools:
                # Handle both SimpleTool objects and regular functions
                func_name = getattr(func, 'name', getattr(func, '__name__', None))
                if func_name == tool_name:
                    tool_func = func
                    break
            
            if tool_func:
                # Call the supervisor tool (handle SimpleTool vs regular function)
                if hasattr(tool_func, 'fn'):
                    # SimpleTool object - call the wrapped function
                    result = tool_func.fn(**tool_args)
                else:
                    # Regular function
                    result = tool_func(**tool_args)
                    
                logger.info(f"✅ Tool call completed: {tool_name}")
                return result
            else:
                logger.error(f"❌ Unknown tool: {tool_name}")
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"❌ Tool call failed: {e}")
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
            return """You are a helpful bridge design assistant that can have natural conversations about bridge engineering.\n\nYou have access to a specialized bridge design supervisor that coordinates geometry and structural analysis agents for complex tasks.\n\n**For simple questions**, respond directly:\n- Basic bridge engineering concepts\n- Material properties and standards\n- General design principles\n- Terminology explanations\n\n**For complex design tasks**, use the bridge design supervisor tools:\n- Creating or modifying bridge components\n- Structural analysis and calculations  \n- Parametric design in Grasshopper\n- Multi-step engineering workflows\n- Component coordination\n\nAvailable tools:\n- `design_bridge_component`: For actual bridge design and modification tasks\n- `get_bridge_design_status`: To check system status and memory\n- `reset_bridge_design`: To start fresh design sessions\n\nKeep responses concise and natural for voice interaction. Be technical but accessible. When using tools, explain what you're doing and interpret the results for the user."""

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
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your API key in your .env file:")
        print("  echo 'GEMINI_API_KEY=your_api_key_here' >> .env")
        print("Then restart the application.")
        return
    
    try:
        # Create and launch
        chat_stream = create_bridge_chat_stream(server_port, share)
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
        self.bridge_supervisor = BridgeDesignSupervisor()
        self.supervisor_tools = create_bridge_design_supervisor_tools(self.bridge_supervisor)
        
        # Create tool lookup (handle SimpleTool objects)
        self.tool_lookup = {}
        for func in self.supervisor_tools:
            # Handle both SimpleTool objects and regular functions
            func_name = getattr(func, 'name', getattr(func, '__name__', None))
            if func_name:
                self.tool_lookup[func_name] = func
        
        logger.info("🌉 Bridge text chat interface initialized")
    
    def chat_loop(self):
        """Run interactive text chat loop."""
        print("🌉 Bridge Design Text Chat Interface")
        print("=" * 50)
        print("Available commands:")
        print("  design <task>     - Design bridge components")
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
                    tool_func = self.tool_lookup["get_bridge_design_status"]
                    result = tool_func.fn() if hasattr(tool_func, 'fn') else tool_func()
                    print(f"📊 Status: {json.dumps(result, indent=2)}")
                elif user_input.lower() == "reset":
                    tool_func = self.tool_lookup["reset_bridge_design"]
                    result = tool_func.fn() if hasattr(tool_func, 'fn') else tool_func()
                    print(f"🔄 Reset: {result}")
                elif user_input.lower().startswith("design "):
                    task = user_input[7:]  # Remove "design " prefix
                    tool_func = self.tool_lookup["design_bridge_component"]
                    result = tool_func.fn(task) if hasattr(tool_func, 'fn') else tool_func(task)
                    print(f"🔧 Design Result: {json.dumps(result, indent=2)}")
                else:
                    print("❓ Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information."""
        print("🌉 Bridge Design Chat Commands:")
        print("  design <task>     - Send task to bridge design supervisor")
        print("                     Example: design create a cable stayed bridge")
        print("  status           - Check supervisor and agent status")
        print("  reset            - Clear all agent memories for fresh start")
        print("  help             - Show this help message")
        print("  exit             - Exit the chat interface")
        print()
        print("💡 The design command uses the bridge design supervisor")
        print("   which coordinates geometry and rational agents.")


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