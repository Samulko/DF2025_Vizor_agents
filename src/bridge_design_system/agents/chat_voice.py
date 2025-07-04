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
import time
import uuid
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

from ..config.logging_config import get_logger
from ..ipc import send_bridge_design_request

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
        
        # Async queues for audio
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()
        
        # Initialize session as None - will be set in start_up
        self.session = None
        
        # Two-terminal architecture: shared state for IPC communication
        self.processing_tasks: Dict[str, Dict] = {}  # Track active processing tasks
        self.task_lock = asyncio.Lock()  # Thread-safe access to shared state
        
        logger.info("🌉 Bridge chat handler initialized for two-terminal IPC architecture")

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
        
        async with client.aio.live.connect(model="gemini-live-2.5-flash-preview", config=config) as session:
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
            
            # CRITICAL: Live API terminates start_stream after tool calls
            # Solution: Restart stream within same session after each tool call
            print("🔄 [SESSION] Starting perpetual audio stream with restart capability...")
            
            while not self.quit.is_set():
                try:
                    print("🎤 [SESSION] Starting/Restarting audio stream...")
                    stream_iteration = 0
                    
                    async for audio in session.start_stream(stream=self.stream(), mime_type="audio/pcm"):
                        stream_iteration += 1
                        print(f"📨 [DEBUG] Stream iteration {stream_iteration}: Received {type(audio)}")
                        
                        # Enhanced response debugging
                        if hasattr(audio, '__dict__'):
                            print(f"📨 [DEBUG] Audio response attributes: {list(audio.__dict__.keys())}")
                        
                        # Handle audio data
                        if audio.data:
                            print(f"🔊 [DEBUG] Audio data received: {len(audio.data)} bytes")
                            array = np.frombuffer(audio.data, dtype=np.int16)
                            self.output_queue.put_nowait((self.output_sample_rate, array))
                        
                        # Check for tool calls in the audio response
                        tool_called = False
                        if hasattr(audio, 'tool_call') and audio.tool_call:
                            print("\n" + "🎆"*60)
                            print("🎆 [BREAKTHROUGH] VOICE TOOL CALL IN AUDIO! 🎆")
                            print("🎆"*60)
                            await self._handle_tool_call(audio.tool_call)
                            tool_called = True
                        
                        # Check for server content with tool calls
                        if hasattr(audio, 'server_content') and audio.server_content:
                            if hasattr(audio.server_content, 'tool_call') and audio.server_content.tool_call:
                                print("\n" + "🎆"*60)
                                print("🎆 [BREAKTHROUGH] VOICE TOOL CALL IN SERVER CONTENT! 🎆")
                                print("🎆"*60)
                                await self._handle_tool_call(audio.server_content.tool_call)
                                tool_called = True
                        
                        # If tool was called, the stream will likely end soon
                        if tool_called:
                            print("⚠️ [SESSION] Tool called - stream will likely terminate, preparing to restart...")
                    
                    # Stream ended (normal after tool calls)
                    print("🔄 [SESSION] Stream ended (expected after tool call), restarting in 0.5s...")
                    await asyncio.sleep(0.5)  # Brief pause before restart
                    
                except asyncio.CancelledError:
                    print("🛑 [SESSION] Stream cancelled, exiting...")
                    break
                except Exception as e:
                    print(f"💥 [SESSION ERROR] Stream exception: {e}")
                    logger.error(f"Stream error: {e}")
                    import traceback
                    traceback.print_exc()
                    print("🔄 [SESSION] Attempting to restart after error...")
                    await asyncio.sleep(1.0)  # Longer pause after error
            
            print("🏁 [SESSION] Exited perpetual stream loop")
    

    def _create_gemini_tools(self):
        """Create tool declarations for Gemini Live API (function_declarations format)."""
        
        # Define the function declarations for Live API - Two-terminal architecture
        bridge_design_request_declaration = {
            "name": "bridge_design_request",
            "description": "Send bridge design request to main.py system via TCP IPC. This implements two-terminal architecture: voice terminal communicates with main bridge design terminal.",
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
        
        # Status checking tool for two-terminal architecture
        are_smolagents_finished_declaration = {
            "name": "are_smolagents_finished_yet",
            "description": "Check if the main.py system has finished processing bridge design tasks. Returns status and results if available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string", 
                        "description": "Optional task ID to check specific task. If not provided, checks all active tasks."
                    }
                },
                "required": []
            }
        }
        
        # Return in Live API format - both tools
        tools = [{"function_declarations": [bridge_design_request_declaration, are_smolagents_finished_declaration]}]
        logger.info(f"✅ Created {len(tools[0]['function_declarations'])} tool declarations for Live API")
        return tools
    
    def _execute_bridge_design_request(self, user_request: str) -> str:
        """Execute bridge design request - Send via IPC to main.py system, returns immediately."""
        print("\n" + "🎆"*50)
        print("🎆 [TWO-TERMINAL] VOICE TERMINAL SENDING TO MAIN TERMINAL! 🎆")
        print("🎆"*50)
        
        # Check if there are any active processing tasks
        active_tasks = [tid for tid, task in self.processing_tasks.items() 
                       if task["status"] in ["started", "processing"]]
        
        if active_tasks:
            active_task_info = []
            for tid in active_tasks:
                task = self.processing_tasks[tid]
                elapsed = time.time() - task["started_at"]
                active_task_info.append(f"Task {tid}: '{task['user_request'][:30]}...' ({elapsed:.1f}s)")
            
            print(f"⚠️ [VOICE TERMINAL] Blocking new request - {len(active_tasks)} active tasks")
            for info in active_task_info:
                print(f"   📋 {info}")
            
            return f"⚠️ Please wait! I'm still processing {len(active_tasks)} task{'s' if len(active_tasks) > 1 else ''}:\n" + \
                   "\n".join([f"• {info}" for info in active_task_info]) + \
                   f"\n\nAsk me 'are the smolagents finished yet?' to check status, then try your request again when completed."
        
        # Generate unique task ID for tracking
        task_id = str(uuid.uuid4())[:8]
        timestamp = time.time()
        
        print(f"🚨 [VOICE TERMINAL] Starting bridge_design_request()")
        print(f"📝 [USER REQUEST] {user_request}")
        print(f"🏷️ [TASK ID] {task_id}")
        print(f"🕰 [TIMESTAMP] {timestamp}")
        
        try:
            # Initialize task state in shared memory (thread-safe)
            task_state = {
                "task_id": task_id,
                "user_request": user_request,
                "status": "started",
                "started_at": timestamp,
                "finished_at": None,
                "result": None,
                "error": None
            }
            
            # Thread-safe: Add to shared state
            self.processing_tasks[task_id] = task_state
            
            print(f"🧵 [VOICE TERMINAL] Task {task_id} added to shared state")
            print("🎯 [VOICE TERMINAL] Starting IPC processing thread...")
            
            # Start processing in separate thread (async task)
            asyncio.create_task(self._run_ipc_processing_thread(task_id))
            
            return f"🚀 Started processing your request (Task ID: {task_id}). The main bridge design system is working on it. You can ask me 'are the smolagents finished yet?' to check status, or continue our conversation!"
                
        except Exception as e:
            print(f"💥 [VOICE TERMINAL ERROR] Exception in bridge_design_request: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error starting processing: {str(e)}"
    
    def _execute_are_smolagents_finished_yet(self, task_id: str = None) -> str:
        """Check if main.py processing has finished - Voice terminal polls status."""
        print(f"🔍 [VOICE TERMINAL] Checking main.py status for task_id: {task_id}")
        
        try:
            if not self.processing_tasks:
                return "🤷 No active processing tasks found. Start a task first with bridge_design_request."
            
            if task_id:
                # Check specific task
                if task_id not in self.processing_tasks:
                    return f"❌ Task ID {task_id} not found. Active tasks: {list(self.processing_tasks.keys())}"
                    
                task = self.processing_tasks[task_id]
                status = task["status"]
                
                if status == "completed":
                    result = task["result"]
                    elapsed = task["finished_at"] - task["started_at"] 
                    # Clean up completed task
                    del self.processing_tasks[task_id]
                    return f"✅ Task {task_id} completed! ({elapsed:.1f}s)\n\nResult: {result}"
                elif status == "error":
                    error = task["error"]
                    # Clean up failed task
                    del self.processing_tasks[task_id]
                    return f"❌ Task {task_id} failed: {error}"
                else:
                    elapsed = time.time() - task["started_at"]
                    return f"🔄 Task {task_id} still processing... ({elapsed:.1f}s elapsed). Request: '{task['user_request'][:50]}...'"
            
            else:
                # Check all tasks
                results = []
                for tid, task in list(self.processing_tasks.items()):
                    if task["status"] == "completed":
                        result = task["result"]
                        elapsed = task["finished_at"] - task["started_at"]
                        results.append(f"✅ Task {tid} completed ({elapsed:.1f}s): {result}")
                        del self.processing_tasks[tid]
                    elif task["status"] == "error":
                        error = task["error"] 
                        results.append(f"❌ Task {tid} failed: {error}")
                        del self.processing_tasks[tid]
                    else:
                        elapsed = time.time() - task["started_at"]
                        results.append(f"🔄 Task {tid} processing ({elapsed:.1f}s): '{task['user_request'][:30]}...'")
                
                if not results:
                    return "🤷 No active tasks found."
                    
                return "\n".join(results)
                
        except Exception as e:
            print(f"💥 [VOICE TERMINAL ERROR] Exception checking status: {e}")
            return f"❌ Error checking status: {str(e)}"

    async def _run_ipc_processing_thread(self, task_id: str):
        """Execute bridge design request via IPC to main.py - updates shared state when done."""
        try:
            print(f"🧵 [IPC THREAD] Starting IPC processing for task {task_id}")
            
            # Get task from shared state
            task = self.processing_tasks.get(task_id)
            if not task:
                print(f"💥 [IPC THREAD] Task {task_id} not found in shared state!")
                return
                
            user_request = task["user_request"]
            print(f"🎯 [IPC THREAD] Processing: {user_request[:50]}...")
            
            # Update status to processing
            async with self.task_lock:
                self.processing_tasks[task_id]["status"] = "processing"
            
            # Send request via IPC to main.py (this is the heavy, blocking operation)
            print("🔧 [IPC THREAD] Sending request to main.py via TCP...")
            logger.info(f"🎯 IPC thread processing: {user_request[:100]}...")
            
            response = await send_bridge_design_request(user_request)
            
            print(f"📊 [IPC THREAD] Processing completed for task {task_id}:")
            print(f"    Success: {response.success}")
            print(f"    Message length: {len(response.message) if response.message else 0} characters")
            
            # Update shared state with results (thread-safe)
            async with self.task_lock:
                if response.success:
                    self.processing_tasks[task_id]["status"] = "completed"
                    self.processing_tasks[task_id]["result"] = response.message
                    self.processing_tasks[task_id]["announced"] = False  # Track if result was announced
                    print(f"✅ [IPC THREAD] Task {task_id} completed successfully")
                    print(f"📤 [IPC RESULT] {response.message}")
                    logger.info(f"✅ IPC task {task_id} completed: {response.message}")
                else:
                    self.processing_tasks[task_id]["status"] = "error"
                    self.processing_tasks[task_id]["error"] = response.message
                    print(f"❌ [IPC THREAD] Task {task_id} failed: {response.message}")
                    logger.error(f"❌ IPC task {task_id} failed: {response.message}")
                
                self.processing_tasks[task_id]["finished_at"] = time.time()
                
        except Exception as e:
            print(f"💥 [IPC THREAD] Exception in task {task_id}: {e}")
            logger.error(f"IPC thread error for task {task_id}: {e}")
            
            # Update shared state with error (thread-safe)
            async with self.task_lock:
                if task_id in self.processing_tasks:
                    self.processing_tasks[task_id]["status"] = "error"
                    self.processing_tasks[task_id]["error"] = str(e)
                    self.processing_tasks[task_id]["finished_at"] = time.time()
            
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
                    
                    # Execute the actual function based on name - Two-thread architecture
                    if fc.name == "bridge_design_request":
                        # Extract arguments
                        user_request = fc.args.get("user_request", "")
                        
                        print(f"🎯 [EXECUTING] bridge_design_request with args: {fc.args}")
                        
                        # Call the actual function (STS thread)
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
                    
                    elif fc.name == "are_smolagents_finished_yet":
                        # Extract arguments for status check
                        task_id = fc.args.get("task_id", None)
                        
                        print(f"🔍 [EXECUTING] are_smolagents_finished_yet with args: {fc.args}")
                        
                        # Call the status check function (STS thread)
                        result = self._execute_are_smolagents_finished_yet(task_id)
                        
                        # Create function response for Live API
                        from google.genai import types
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response={"result": result}
                        )
                        function_responses.append(function_response)
                        
                        print(f"✅ [FUNCTION RESPONSE] Created status response for {fc.name}")
                    
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

You operate in a two-terminal architecture where you send requests to the main bridge design system via TCP IPC.

**CRITICAL TASK MANAGEMENT RULE:**
BEFORE sending ANY new bridge_design_request, you MUST FIRST check if previous tasks are finished by calling the are_smolagents_finished_yet tool. Only send new requests when all previous tasks are completed or failed.

**WORKFLOW:**
1. For bridge design tasks: First call are_smolagents_finished_yet
2. If tasks are still processing: Tell user to wait and explain what's being processed
3. If tasks are finished: Then proceed with bridge_design_request
4. For simple questions: Respond directly without tools

**For simple questions**, you can respond directly:
- Basic bridge engineering concepts
- Material properties and standards
- General design principles
- Terminology explanations

**For ANY bridge design tasks**, you MUST follow the workflow above:
- Creating or modifying bridge components
- Structural analysis and calculations  
- Parametric design in Grasshopper
- Multi-step engineering workflows
- Component coordination
- System status checks
- Any request related to bridge design

Available tools:
- `are_smolagents_finished_yet`: Check if main.py has finished processing tasks - CALL THIS FIRST
- `bridge_design_request`: Sends requests to main.py bridge design system via TCP IPC - ONLY AFTER CHECKING STATUS

Examples of proper workflow:
- User: "Create a simple beam bridge"
- Assistant: [calls are_smolagents_finished_yet first]
- If busy: "I'm still processing a previous task. Please wait..."
- If free: [calls bridge_design_request with the user's request]

Two-Terminal Architecture:
- Terminal 1: main.py (bridge design system with --enable-command-server)
- Terminal 2: voice chat (this interface) communicates via TCP

Keep responses concise and natural for voice interaction. Be technical but accessible. When using tools, explain what you're doing and interpret the results for the user.

REMEMBER: ALWAYS check task status BEFORE sending new bridge design requests. This prevents overwhelming the main system."""

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
        time_limit=300,  # 5 minutes session limit
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
    
    Uses IPC to communicate with main.py system via text input/output.
    """
    
    def __init__(self):
        """Initialize text chat interface."""
        logger.info("🌉 Bridge text chat interface initialized for two-terminal architecture")
    
    def chat_loop(self):
        """Run interactive text chat loop."""
        print("🌉 Bridge Design Text Chat Interface (Two-Terminal Architecture)")
        print("=" * 70)
        print("Available commands:")
        print("  <any request>    - Send request to main.py via IPC")
        print("  status           - Check interface status")
        print("  reset            - Use 'reset' in main.py terminal")
        print("  help             - Show this help")
        print("  exit             - Exit chat")
        print("💡 Make sure main.py is running with --enable-command-server")
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
                    print("📊 Status: Text chat interface using two-terminal IPC architecture")
                    print("   Main.py system should be running with --enable-command-server")
                elif user_input.lower() == "reset":
                    print("🔄 Reset: Use 'reset' command in main.py terminal")
                elif user_input:
                    # Send any non-empty request to main.py via IPC
                    print("\n" + "="*60)
                    print("🎯 [TEXT CHAT] Sending to main.py via IPC...")
                    print(f"📝 [USER INPUT] {user_input}")
                    print("="*60)
                    
                    try:
                        print("🔧 [DEBUG] Calling main.py via TCP IPC...")
                        response = asyncio.run(send_bridge_design_request(user_input))
                        
                        print(f"📊 [DEBUG] Response received:")
                        print(f"    Success: {response.success}")
                        print(f"    Message length: {len(response.message) if response.message else 0} characters")
                        
                        if response.success:
                            print("✅ [SUCCESS] Main.py processing completed successfully")
                            print(f"📤 [RESPONSE] {response.message}")
                        else:
                            print("❌ [FAILURE] Main.py processing failed")
                            print(f"💥 [ERROR] {response.message}")
                            
                    except Exception as e:
                        print(f"💥 [EXCEPTION] Error in text chat: {e}")
                        print("💡 Make sure main.py is running with --enable-command-server")
                        import traceback
                        traceback.print_exc()
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information."""
        print("🌉 Bridge Design Chat Commands (Two-Terminal Architecture):")
        print("  <any request>    - Send any request to main.py via IPC")
        print("                     Examples:")
        print("                     'Create a cable stayed bridge'")
        print("                     'Modify element 021 center point'")
        print("                     'What is the current design status?'")
        print("  status           - Check text chat interface status")
        print("  reset            - Use 'reset' command in main.py terminal")
        print("  help             - Show this help message")
        print("  exit             - Exit the chat interface")
        print()
        print("💡 All requests are sent via TCP to main.py which runs")
        print("   the bridge design system with triage agent coordination.")
        print("💡 Make sure main.py is running with --enable-command-server")


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