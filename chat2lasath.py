from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import os
from typing import List, Dict, AsyncGenerator, Literal
import asyncio
import base64
import json
import re
import ast

from fastrtc import Stream, ReplyOnPause, get_twilio_turn_credentials, AsyncStreamHandler
from smolagents import CodeAgent, DuckDuckGoSearchTool, tool
# cSpell:ignore genai
from google import genai
from google.genai.types import LiveConnectConfig, PrebuiltVoiceConfig, SpeechConfig, VoiceConfig, Modality
from pydantic import BaseModel

# Load environment variables
load_dotenv()

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
- If the user asks forD EBUG mode, you will generate random values and export the JSON using the export_design_profile tool
- If the user asks to save, save file, or save JSON, you MUST call the export_design_profile tool to generate and persist the JSON summary.
- When calling export_design_profile, include all rated aspects as keys with integer values (0-100), always including the main settings: self_weight, storage, complexity.
- If the user provides a rating outside the 0-100 range, automatically determine the original scale (e.g., 0-5 or 0-10) and convert it to the equivalent 0-100 value without prompting the user for a new value.
</CRITICAL>

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
"""

class GeminiHandler(AsyncStreamHandler):
    """Handler for the Gemini API"""
    def __init__(self, expected_layout: Literal["mono"] = "mono", output_sample_rate: int = 24000):
        super().__init__(expected_layout, output_sample_rate, input_sample_rate=16000)
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()

    def copy(self) -> "GeminiHandler":
        return GeminiHandler(expected_layout="mono", output_sample_rate=self.output_sample_rate)

    async def start_up(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        
        client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
        
        # Create tools for function calling
        tools = self._create_gemini_tools()
        # Use raw dict config to include tools
        config = {
            "response_modalities": [Modality.AUDIO],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Leda"}
                }
            },
            "tools": tools,
            "system_instruction": system_prompt,
            # "generation_config": {"temperature": 0.2, "top_p": 0.9},
        }
        
        async with client.aio.live.connect(model="gemini-live-2.5-flash-preview", config=config) as session:
            # Keep session reference for sending tool responses
            self.session = session
            async for audio in session.start_stream(stream=self.stream(), mime_type="audio/pcm"):
                if audio.data:
                    array = np.frombuffer(audio.data, dtype=np.int16)
                    self.output_queue.put_nowait((self.output_sample_rate, array))
                # Print any textual response from the agent
                if hasattr(audio, "server_content"):
                    sc = audio.server_content
                    # Try both content and text attributes for the response
                    text = getattr(sc, "content", None) or getattr(sc, "text", None)
                    if text:
                        print("Agent:", text)
                # Handle function calls from Gemini Live
                if hasattr(audio, "tool_call") and audio.tool_call:
                    await self._handle_tool_call(audio.tool_call)
                elif hasattr(audio, "server_content") and getattr(audio.server_content, "tool_call", None):
                    await self._handle_tool_call(audio.server_content.tool_call)

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
        audio_message = base64.b64encode(array.tobytes()).decode("UTF-8")
        self.input_queue.put_nowait(audio_message)

    async def emit(self) -> tuple[int, np.ndarray] | None:
        try:
            return await asyncio.wait_for(self.output_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    def shutdown(self) -> None:
        self.quit.set()

    def _create_gemini_tools(self):
        """Create export_design_profile tool declaration."""
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
        return [{"function_declarations": [export_tool]}]

    async def _handle_tool_call(self, tool_call):
        """Handle function calls from Gemini Live session."""
        from google.genai import types
        responses = []
        for fc in tool_call.function_calls:
            print(fc)
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
            responses.append(types.FunctionResponse(id=fc.id, name=fc.name, response=result))
        if hasattr(self, "session"):
            await self.session.send_tool_response(function_responses=responses)

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

def main():
    print("Starting Desk Design Assistant with Gemini...")
    stream.ui.launch(server_port=7860)

if __name__ == "__main__":
    main()