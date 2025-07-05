from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import os
from typing import List, Dict, AsyncGenerator, Literal, Any
import asyncio
import base64
import json
import re
import ast
import time
import uuid

from fastrtc import Stream, ReplyOnPause, get_twilio_turn_credentials, AsyncStreamHandler, wait_for_item
from smolagents import CodeAgent, DuckDuckGoSearchTool, tool
# cSpell:ignore genai
from google import genai
from google.genai.types import LiveConnectConfig, PrebuiltVoiceConfig, SpeechConfig, VoiceConfig, Modality
from pydantic import BaseModel

# IPC imports for two-terminal architecture
from ..config.logging_config import get_logger
from ..ipc import send_bridge_design_request

logger = get_logger(__name__)

# Load environment variables
load_dotenv()


def encode_audio(data: np.ndarray) -> str:
    """Encode Audio data to send to the server"""
    return base64.b64encode(data.tobytes()).decode("UTF-8")

# Initialize models (Gemini audio only, no STT/TTS wrappers)
stt_model = None  # Not used, handled by GeminiHandler
tts_model = None  # Not used, handled by GeminiHandler

# Conversation state to maintain history
conversation_state: List[Dict[str, str]] = []

def print_conversation_state():
    print("\n--- Conversation State ---")
    for i, turn in enumerate(conversation_state):
        print(f"Turn {i+1}: {turn}")
    print("-------------------------\n")

# System prompt for agent
system_prompt = """
You are a specialized Desk Design Customer Service Agent focused exclusively on helping customers design their perfect desk. Your role is to guide customers through a structured interview process, gathering requirements based on three critical design aspects: **self weight**, **storage**, and **complexity**.

## CORE MISSION
Your mission is to conduct a friendly, professional customer service interview that extracts clear design requirements from customers, always maintaining focus on the three essential aspects that define desk priorities.

<CRITICAL>
- You MUST ALWAYS be short with your responses
- You MUST ALWAYS be friendly and professional
- If the user asks for DEBUG mode, you will generate random values and export the JSON using the export_design_profile tool
- If the user asks to save, save file, or save JSON, you MUST call the export_design_profile tool to generate and persist the JSON summary.
- When calling export_design_profile, include all rated aspects as keys with integer values (0-100), always including the main settings: self_weight, storage, complexity.
- If the user provides a rating outside the 0-100 range, automatically determine the original scale (e.g., 0-5 or 0-10) and convert it to the equivalent 0-100 value without prompting the user for a new value.
</CRITICAL>

## TWO-TERMINAL ARCHITECTURE WITH ENGINEERING CAPABILITY
You operate in a two-terminal architecture where you can send complex engineering requests to the main smolagents system via TCP IPC.

**CRITICAL TASK MANAGEMENT RULE:**
BEFORE sending ANY new desk_design_request, you MUST FIRST check if previous tasks are finished by calling the are_smolagents_finished_yet tool. Only send new requests when all previous tasks are completed or failed.

**WORKFLOW:**
1. For complex desk engineering tasks: First call are_smolagents_finished_yet
2. If tasks are still processing: Tell user to wait and explain what's being processed
3. If tasks are finished: Then proceed with desk_design_request
4. For simple desk design questions: Respond directly without tools

**For simple desk design questions**, you can respond directly:
- Basic desk design concepts (self weight, storage, complexity ratings)
- Customer service interview questions
- Rating explanations and guidance
- Simple desk feature discussions

**For complex desk engineering tasks**, you MUST follow the workflow above:
- Structural analysis and load calculations
- CAD generation and 3D modeling
- Material selection and optimization
- Engineering simulations
- Manufacturing specifications
- Complex design modifications

Available tools:
- `export_design_profile`: Save desk design ratings to JSON file
- `are_smolagents_finished_yet`: Check if main.py has finished processing engineering tasks - CALL THIS FIRST
- `desk_design_request`: Sends complex engineering requests to main.py system via TCP IPC - ONLY AFTER CHECKING STATUS

Examples of proper workflow:
- User: "Can you calculate the load bearing capacity of my desk design?"
- Assistant: [calls are_smolagents_finished_yet first]
- If busy: "I'm still processing a previous engineering task. Please wait..."
- If free: [calls desk_design_request with the user's engineering request]

Two-Terminal Architecture:
- Terminal 1: main.py (bridge design system with --enable-command-server)
- Terminal 2: desk design voice chat (this interface) communicates via TCP

REMEMBER: ALWAYS check task status BEFORE sending new engineering requests. Focus on desk design customer service, but delegate complex engineering to the main system.</CRITICAL>

## THE THREE DESIGN ASPECTS (MANDATORY FOCUS)

### 1. **Self Weight** (Importance of Desk Weight)
- Reflects how important desk weight is for portability versus stability
- Higher value = weight is more important (prefer lighter desk)
- Scale: 0 (weight not important) to 100 (weight critically important)

### 2. **Storage** (Desk Storage Capacity)
- Determines how much storage space the desk provides for items and tools
- Higher value = storage is more important
- Scale: 0 (no storage needed) to 100 (maximum storage needed)

### 3. **Complexity** (Angles & Shape Features)
- Measures geometric complexity: angles, twists, or curves
- Higher value = more complex design
- Scale: 0 (simple, no angles) to 100 (highly complex, many features)

## CUSTOMER SERVICE APPROACH

### Interview Flow:
1. **Warm Welcome**: Greet the customer and explain you'll help design their perfect desk
2. **Context Gathering**: Understand their use case and environment
3. **Aspect Exploration**: Systematically explore each of the three aspects
4. **Rating Collection**: Get 0-100 integer ratings for each aspect
5. **Summary & Confirmation**: Summarize the design requirements

### Conversation Guidelines:
- **Stay Focused**: ONLY discuss self weight, storage, and complexity
- **Be Friendly**: Maintain a warm, helpful customer service tone
- **Guide Gently**: Lead customers through each aspect systematically
- **Clarify Ratings**: If the user uses another scale, automatically map it to a 0-100 value internally and proceed.
- **Redirect Politely**: If customers mention other factors, redirect focus to self weight, storage, and complexity

## EXAMPLE CUSTOMER SERVICE DIALOGUE

**Agent**: Welcome! I'm here to help you design your perfect desk focusing on self weight, storage, and complexity. Let's start - what will you primarily use this desk for?

**Customer**: I need a desk for a craft workshop and need ample storage.

**Agent**: Great! How important is storage to you on a scale of 0-100?

**Customer**: I'd say about 80% important.

**Agent**: Perfect! Storage is 80% important. Now, let's discuss **self weight**. How important is the weight of the desk to you on a scale of 0-100?

**Customer**: I'd say about 70% important.

**Agent**: Excellent! Self weight is 70% important. Finally, let's explore **complexity**. How complex is the design of the desk?

**Customer**: I'd say about 60% complex.

**Agent**: Great choice! The design is 60% complex. Let me summarize your desk design requirements:

**Your Desk Design Profile:**
- **Self Weight**: 70%
- **Storage**: 80%
- **Complexity**: 60%

Your ideal desk prioritizes storage (80%) while maintaining moderate self weight and simple functionality. Does this accurately capture your needs?

## CRITICAL REMINDERS

1. **ALWAYS** maintain focus on the three aspects only
2. **ALWAYS** be friendly and professional
3. **NEVER** discuss price, materials, colors, or aesthetics
4. **NEVER** make assumptions - ask clarifying questions
5. **ALWAYS** summarize with all three ratings
6. **ALWAYS** when sending instructions to the smolagents, do not pass the values but rather give the instructions for the design agent to read the design_profile.json
 """

class GeminiHandler(AsyncStreamHandler):
    """Handler for the Gemini API with desk design focus and IPC capability"""
    def __init__(self, expected_layout: Literal["mono"] = "mono", output_sample_rate: int = 24000):
        super().__init__(expected_layout, output_sample_rate, input_sample_rate=16000)
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()
        
        # Initialize session as None - will be set in start_up
        self.session = None
        
        # Two-terminal architecture: shared state for IPC communication
        self.processing_tasks: Dict[str, Dict] = {}  # Track active processing tasks
        self.task_lock = asyncio.Lock()  # Thread-safe access to shared state
        
        logger.info("🪑 Desk design handler initialized with two-terminal IPC architecture")

    def copy(self) -> "GeminiHandler":
        return GeminiHandler(expected_layout="mono", output_sample_rate=self.output_sample_rate)

    async def start_up(self):
        print("🪑 [DEBUG] Starting Desk Design Gemini Live session initialization...")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        
        print("✅ [DEBUG] API key found, creating Gemini client...")
        
        client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
        
        # Create tools for function calling
        tools = self._create_gemini_tools()
        print(f"🛠️  [DEBUG] Created {len(tools[0]['function_declarations'])} Gemini tools for desk design")
        for i, func_decl in enumerate(tools[0]['function_declarations']):
            print(f"    Tool {i+1}: {func_decl['name']} - {func_decl['description'][:50]}...")
        
        # Use raw dict config to include tools
        config = {
            "response_modalities": [Modality.AUDIO],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Puck"}
                }
            },
            "tools": tools,
            "system_instruction": system_prompt,
            # "generation_config": {"temperature": 0.2, "top_p": 0.9},
        }
        
        print("🚀 [DEBUG] Connecting to Gemini Live API...")
        
        async with client.aio.live.connect(model="gemini-live-2.5-flash-preview", config=config) as session:
            print("✅ [DEBUG] Connected to Gemini Live API successfully!")
            print("🎧 [DEBUG] Audio streaming active - you can now speak about desk design")
            
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
                        
                        # Handle audio data
                        if audio.data:
                            print(f"🔊 [DEBUG] Audio data received: {len(audio.data)} bytes")
                            array = np.frombuffer(audio.data, dtype=np.int16)
                            self.output_queue.put_nowait((self.output_sample_rate, array))
                        
                        # Print any textual response from the agent
                        if hasattr(audio, "server_content"):
                            sc = audio.server_content
                            # Try both content and text attributes for the response
                            text = getattr(sc, "content", None) or getattr(sc, "text", None)
                            if text:
                                print("Desk Agent:", text)
                        
                        # Check for tool calls in the audio response
                        tool_called = False
                        if hasattr(audio, 'tool_call') and audio.tool_call:
                            print("\n" + "🪑"*60)
                            print("🪑 [BREAKTHROUGH] DESK DESIGN TOOL CALL IN AUDIO! 🪑")
                            print("🪑"*60)
                            await self._handle_tool_call(audio.tool_call)
                            tool_called = True
                        
                        # Check for server content with tool calls
                        if hasattr(audio, 'server_content') and audio.server_content:
                            if hasattr(audio.server_content, 'tool_call') and audio.server_content.tool_call:
                                print("\n" + "🪑"*60)
                                print("🪑 [BREAKTHROUGH] DESK DESIGN TOOL CALL IN SERVER CONTENT! 🪑")
                                print("🪑"*60)
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

    async def stream(self) -> AsyncGenerator[bytes, None]:
        while not self.quit.is_set():
            try:
                audio = await asyncio.wait_for(self.input_queue.get(), 0.1)
                yield audio
            except asyncio.TimeoutError:
                pass

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        _, array = frame
        array = array.squeeze()
        audio_message = encode_audio(array)
        self.input_queue.put_nowait(audio_message)

    async def emit(self) -> tuple[int, np.ndarray] | None:
        return await wait_for_item(self.output_queue)

    def shutdown(self) -> None:
        self.quit.set()

    def _create_gemini_tools(self):
        """Create tool declarations including desk design export and IPC tools."""
        # Existing export tool
        export_tool = {
            "name": "export_design_profile",
            "description": "Generate a JSON summary of the desk design profile including ratings only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "self_weight": {"type": "integer", "description": "Percentage importance of desk self weight."},
                    "storage": {"type": "integer", "description": "Percentage importance of desk storage capacity."},
                    "complexity": {"type": "integer", "description": "Percentage importance of desk complexity."}
                },
                "required": ["self_weight", "storage", "complexity"]
            }
        }
        
        # New IPC tool for desk engineering requests
        desk_design_request_declaration = {
            "name": "desk_design_request",
            "description": "Send desk engineering request to main.py system via TCP IPC for complex structural analysis, CAD generation, or engineering calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "The user's request about desk engineering, structural analysis, or CAD operations"
                    }
                },
                "required": ["user_request"]
            }
        }
        
        # Status checking tool for two-terminal architecture
        are_smolagents_finished_declaration = {
            "name": "are_smolagents_finished_yet",
            "description": "Check if the main.py system has finished processing desk engineering tasks. Returns status and results if available.",
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
        
        # Return all tools in Live API format
        return [{"function_declarations": [export_tool, desk_design_request_declaration, are_smolagents_finished_declaration]}]

    async def _handle_tool_call(self, tool_call):
        """Handle function calls from Gemini Live session."""
        try:
            print("\n" + "🪑"*50)
            print("🪑 [DESK DESIGN] GEMINI TOOL CALL HANDLER TRIGGERED! 🪑")
            print("🪑"*50)
            print(f"🔥 [TOOL CALL TYPE] {type(tool_call)}")
            print(f"🔥 [TOOL CALL DETAILS] {tool_call}")
            
            logger.info(f"🛠️ Handling Gemini function call: {tool_call}")
            
            # Handle manual function calls - Live API requires manual handling
            if hasattr(tool_call, 'function_calls'):
                function_responses = []
                
                for fc in tool_call.function_calls:
                    print(f"📝 [FUNCTION CALL] Name: {fc.name}")
                    print(f"📝 [FUNCTION CALL] ID: {fc.id}")
                    print(f"📝 [FUNCTION CALL] Args: {fc.args}")
                    
                    # Execute the actual function based on name
                    if fc.name == "export_design_profile":
                        # Parse LLM-provided arguments for ratings based on tool properties
                        ratings = {}
                        # Try both 'arguments' (JSON string) and 'args' (dict)
                        raw_args = getattr(fc, "arguments", None) or getattr(fc, "args", None)
                        if raw_args:
                            try:
                                # If raw_args is a JSON string, parse it; else assume it's a dict
                                parsed = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                                ratings = {k: int(v) for k, v in parsed.items()}
                            except Exception:
                                ratings = {}
                        # Fallback to conversation_state if no arguments provided or parsing failed
                        if not ratings:
                            for turn in conversation_state:
                                for aspect, value in turn.items():
                                    m = re.search(r"(\\d+)", str(value))
                                    if m:
                                        ratings[aspect] = int(m.group(1))
                        # Build result with ratings only
                        result = {"ratings": ratings}
                        print(f"[!!!] Exporting design profile: {result}")
                        # Write JSON summary to file
                        json_path = Path(__file__).parent / "design_profile.json"
                        with open(json_path, "w") as f:
                            json.dump(result, f, indent=2)
                        
                        # Create function response for Live API
                        from google.genai import types
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response=result
                        )
                        function_responses.append(function_response)
                        
                        print(f"✅ [FUNCTION RESPONSE] Created response for {fc.name}")
                    
                    elif fc.name == "desk_design_request":
                        # Extract arguments
                        user_request = fc.args.get("user_request", "")
                        
                        print(f"🎯 [EXECUTING] desk_design_request with args: {fc.args}")
                        
                        # Call the actual function (desk voice thread)
                        result = self._execute_desk_design_request(user_request)
                        
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
                        
                        # Call the status check function (desk voice thread)
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
                        # Create error response with helpful suggestion
                        from google.genai import types
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response={"error": f"Unknown function: {fc.name}. Available functions: export_design_profile, desk_design_request, are_smolagents_finished_yet"}
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

    def _execute_export_design_profile(self):
        """Build JSON summary from conversation_state."""
        ratings = {}
        for turn in conversation_state:
            for aspect, value in turn.items():
                m = re.search(r"(\d+)", str(value))
                if m:
                    ratings[aspect] = int(m.group(1))
        # Return only ratings
        return {"ratings": ratings}
    
    def _execute_desk_design_request(self, user_request: str) -> str:
        """Execute desk design engineering request - Send via IPC to main.py system."""
        print("\n" + "🪑"*50)
        print("🪑 [TWO-TERMINAL] DESK VOICE SENDING TO MAIN SYSTEM! 🪑")
        print("🪑"*50)
        
        # Check if there are any active processing tasks
        active_tasks = [tid for tid, task in self.processing_tasks.items() 
                       if task["status"] in ["started", "processing"]]
        
        if active_tasks:
            active_task_info = []
            for tid in active_tasks:
                task = self.processing_tasks[tid]
                elapsed = time.time() - task["started_at"]
                active_task_info.append(f"Task {tid}: '{task['user_request'][:30]}...' ({elapsed:.1f}s)")
            
            print(f"⚠️ [DESK VOICE] Blocking new request - {len(active_tasks)} active tasks")
            for info in active_task_info:
                print(f"   📋 {info}")
            
            return f"⚠️ Please wait! I'm still processing {len(active_tasks)} task{'s' if len(active_tasks) > 1 else ''}:\n" + \
                   "\n".join([f"• {info}" for info in active_task_info]) + \
                   f"\n\nAsk me 'are the smolagents finished yet?' to check status, then try your request again when completed."
        
        # Generate unique task ID for tracking
        task_id = str(uuid.uuid4())[:8]
        timestamp = time.time()
        
        print(f"🚨 [DESK VOICE] Starting desk_design_request()")
        print(f"📝 [USER REQUEST] {user_request}")
        print(f"🏷️ [TASK ID] {task_id}")
        print(f"🕰 [TIMESTAMP] {timestamp}")
        
        try:
            # Initialize task state in shared memory
            task_state = {
                "task_id": task_id,
                "user_request": user_request,
                "status": "started",
                "started_at": timestamp,
                "finished_at": None,
                "result": None,
                "error": None
            }
            
            # Add to shared state
            self.processing_tasks[task_id] = task_state
            
            print(f"🧵 [DESK VOICE] Task {task_id} added to shared state")
            print("🎯 [DESK VOICE] Starting IPC processing thread...")
            
            # Start processing in separate thread (async task)
            asyncio.create_task(self._run_ipc_processing_thread(task_id))
            
            return f"🚀 Started processing your desk engineering request (Task ID: {task_id}). The main system is working on it. You can ask me 'are the smolagents finished yet?' to check status, or continue our conversation!"
                
        except Exception as e:
            print(f"💥 [DESK VOICE ERROR] Exception in desk_design_request: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error starting processing: {str(e)}"
    
    def _execute_are_smolagents_finished_yet(self, task_id: str = None) -> str:
        """Check if main.py processing has finished - Desk voice terminal polls status."""
        print(f"🔍 [DESK VOICE] Checking main.py status for task_id: {task_id}")
        
        try:
            if not self.processing_tasks:
                return "🤷 No active processing tasks found. Start a task first with desk_design_request."
            
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
            print(f"💥 [DESK VOICE ERROR] Exception checking status: {e}")
            return f"❌ Error checking status: {str(e)}"
    
    async def _run_ipc_processing_thread(self, task_id: str):
        """Execute desk design request via IPC to main.py - updates shared state when done."""
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

# Set up the stream to use Gemini for audio interaction
stream = Stream(
    handler=GeminiHandler(),
    modality="audio",
    mode="send-receive",
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.ideasip.com:3478"]},
            {"urls": ["stun:stun.ekiga.net:3478"]}
        ]
    },
    ui_args={
        "pulse_color": "rgb(255, 255, 255)",
        "icon_button_color": "rgb(255, 255, 255)",
        "title": "🪑 Desk Design Assistant",
    },
)

# Alternative text-based chat interface for testing
class DeskTextChatInterface:
    """
    Text-based interface for desk design chat (for testing without voice).
    
    Uses IPC to communicate with main.py system via text input/output.
    """
    
    def __init__(self):
        """Initialize text chat interface."""
        logger.info("🪑 Desk design text chat interface initialized for two-terminal architecture")
    
    def chat_loop(self):
        """Run interactive text chat loop."""
        print("🪑 Desk Design Text Chat Interface (Two-Terminal Architecture)")
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
                user_input = input("🪑 Desk Chat> ").strip()
                
                if user_input.lower() == "exit":
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == "help":
                    self._show_help()
                elif user_input.lower() == "status":
                    print("📊 Status: Desk design text chat interface using two-terminal IPC architecture")
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
        print("🪑 Desk Design Chat Commands (Two-Terminal Architecture):")
        print("  <any request>    - Send any request to main.py via IPC")
        print("                     Examples:")
        print("                     'Design a desk with high storage priority'")
        print("                     'Calculate load bearing for my desk design'")
        print("                     'What is the current engineering status?'")
        print("  status           - Check text chat interface status")
        print("  reset            - Use 'reset' command in main.py terminal")
        print("  help             - Show this help message")
        print("  exit             - Exit the chat interface")
        print()
        print("💡 All requests are sent via TCP to main.py which runs")
        print("   the engineering system with smolagent coordination.")
        print("💡 Make sure main.py is running with --enable-command-server")


def launch_text_chat():
    """Launch text-based desk design chat for testing."""
    try:
        chat = DeskTextChatInterface()
        chat.chat_loop()
    except Exception as e:
        logger.error(f"Text chat failed: {e}")
        print(f"❌ Text chat error: {e}")


def main():
    import sys
    
    # Check if started via start_TEAM.py (environment variable set by TEAM launcher)
    if os.getenv("OTEL_BACKEND") == "phoenix":
        print("\n" + "🪑" * 60)
        print("🪑 DESK DESIGN ASSISTANT - TEAM INTEGRATION")
        print("🪑" * 60)
        print("📊 Phoenix UI:     http://localhost:6006")
        print("🖥️  LCARS Monitor:  http://localhost:5000")
        print("📡 TCP Command:    localhost:8082")
        print("🎤 Desk Voice UI:  http://localhost:7860")
        print("🪑" * 60)
        print("🚀 Starting Desk Design Voice Interface...")
        print("   Integrated with TEAM architecture")
        print("   Connect to main system via TCP IPC")
        print("🪑" * 60)
        
        # When launched by TEAM, default to voice interface
        launch_voice_interface()
        
    elif len(sys.argv) > 1:
        if sys.argv[1] == "voice":
            launch_voice_interface()
        elif sys.argv[1] == "text":
            launch_text_chat()
        elif sys.argv[1] == "team":
            # Manual TEAM mode
            print("🪑 Starting in TEAM integration mode...")
            launch_voice_interface()
        else:
            print("Usage: python -m bridge_design_system.agents.chat2 [voice|text|team]")
    else:
        print("🪑 Desk Design Assistant")
        print("Usage:")
        print("  python -m bridge_design_system.agents.chat2 voice   # Voice interface")
        print("  python -m bridge_design_system.agents.chat2 text    # Text interface") 
        print("  python -m bridge_design_system.agents.chat2 team    # TEAM integration mode")
        print()
        print("🔧 Features:")
        print("  • Desk design customer service interview")
        print("  • Three design aspects: self_weight, storage, complexity")
        print("  • IPC integration with main smolagents system")
        print("  • Two-terminal architecture for engineering tasks")
        print()
        print("💡 TEAM Integration:")
        print("  Use start_TEAM.py to launch the complete system including:")
        print("  • Phoenix tracing server")
        print("  • LCARS monitoring")
        print("  • Main bridge design system")
        print("  • This desk design interface")


def launch_voice_interface():
    """Launch the voice interface with proper TEAM integration."""
    print("🪑 Starting Desk Design Assistant with Gemini...")
    print("🎤 Voice interface for desk design with IPC capability")
    
    # Check if API key is available
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your API key in your .env file:")
        print("  echo 'GEMINI_API_KEY=your_api_key_here' >> .env")
        print("Then restart the application.")
        return
    
    print("✅ GEMINI_API_KEY found, starting voice interface...")
    
    try:
        # Enhanced launch for TEAM integration
        print("🌐 Launching web interface on http://localhost:7860")
        print("🎧 Click the microphone button to start talking about desk design")
        print("📞 Integrated with main system for complex engineering tasks")
        
        stream.ui.launch(
            server_port=7860,
            share=False,
            debug=True,
            show_error=True,
            quiet=False
        )
        
    except Exception as e:
        logger.error(f"Failed to launch desk design voice interface: {e}")
        print(f"❌ Launch failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check API key: export GEMINI_API_KEY=your_key")
        print("2. Install dependencies: uv add google-genai fastrtc")
        print("3. Check network connectivity")
        print("4. Try text interface: python -m bridge_design_system.agents.chat2 text")
        print("5. Check port availability: netstat -tulpn | grep 7860")


if __name__ == "__main__":
    main()