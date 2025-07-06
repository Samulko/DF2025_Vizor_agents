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

def calculate_percentages(ratings: Dict[str, int]) -> Dict[str, float]:
    """Calculate percentage proportions from 0-5 ratings."""
    total = sum(ratings.values())
    if total == 0:
        return {k: 0.0 for k in ratings.keys()}
    
    percentages = {}
    for aspect, rating in ratings.items():
        percentages[aspect] = round((rating / total) * 100, 1)
    
    return percentages

# System prompt for agent
system_prompt = """
You are a specialized Desk Design Customer Service Agent focused exclusively on helping customers design their perfect desk. Your role is to guide customers through a structured interview process, gathering requirements based on three critical design aspects: **timber layers**, **surface area**, and **complexity**.

## CORE MISSION
Your mission is to conduct a friendly, professional customer service interview that extracts clear design requirements from customers, always maintaining focus on the three essential aspects that define desk design quality.

<CRITICAL>
- You MUST ALWAYS be short with your responses
- You MUST ALWAYS be friendly and professional
- If the user asks forD EBUG mode, you will generate random values and export the JSON using the export_design_profile tool
- If the user asks to save, save file, or save JSON, you MUST call the export_design_profile tool to generate and persist the JSON summary.
- When calling export_design_profile, include all rated aspects as keys with integer values (0-5), always including the main settings: timber_layers, surface_area, complexity.
- If the user provides a rating outside the 0-5 range, automatically determine the original scale (e.g., 0-10 or 0-100) and convert it to the equivalent 0-5 value without prompting the user for a new value.
</CRITICAL>

## THE THREE DESIGN ASPECTS (MANDATORY FOCUS)

### 1. **Timber Layers** (Structural Layers of Wood)
- The number of wood timber layers used in the desk's construction
- Affects strength, durability, and weight
- More layers = heavier and stronger; fewer layers = lighter and less robust
- Portability and stability considerations
- Scale: 0 (single layer, ultra-light) to 5 (many layers, very sturdy)

### 2. **Surface Area** (Usable Desk Top Space)
- The total usable surface area of the desk
- Determines how many items can be placed on the desk at once
- Affects workspace organization and capacity
- Scale: 0 (minimal surface, holds very little) to 5 (maximum surface, holds many items)

### 3. **Complexity** (Angles & Shape Twists)
- The geometric angles and twists in the desk's shape
- Number and sharpness of angles in the design
- How much the desk shape twists or curves
- Angular complexity vs. straight, simple lines
- Scale: 0 (simple, no angles) to 5 (complex, big twist in shape)

## CUSTOMER SERVICE APPROACH

### Interview Flow:
1. **Warm Welcome**: Greet the customer and explain you'll help design their perfect desk
2. **Context Gathering**: Understand their use case and environment
3. **Aspect Exploration**: Systematically explore each of the three aspects
4. **Rating Collection**: Get 0-5 ratings for each aspect
5. **Proportion Calculation**: Calculate and confirm the relative importance (%)
6. **Summary & Confirmation**: Summarize the design requirements

### Conversation Guidelines:
- **Stay Focused**: ONLY discuss timber layers, surface area, and complexity
- **Be Friendly**: Maintain a warm, helpful customer service tone
- **Guide Gently**: Lead customers through each aspect systematically
- **Clarify Ratings**: Ensure customers understand the 0-5 scale
- **Calculate Proportions**: Always show the percentage breakdown
- **Redirect Politely**: If customers mention other factors (color, material, price), redirect: "I'll help you focus on the three key aspects that determine desk functionality: timber layers, surface area, and complexity."
- **Concise Conclusions**: Only provide a final summary when ALL THREE parameters are determined. Avoid repetitive partial summaries.
- **Be Flexible**: Adapt to different communication styles - some users give detailed answers, others give brief responses
- **Handle Ambiguity**: If a user's response is unclear, ask ONE specific clarifying question rather than multiple questions
- **Context Awareness**: Remember previous responses and build on them naturally
- **Natural Flow**: Don't be robotic - respond naturally while staying on topic

### Response Flexibility:
- **Detailed Users**: If someone gives a long, detailed response, acknowledge their thoughtfulness and extract the relevant information
- **Brief Users**: If someone gives short answers, gently encourage more detail with specific questions
- **Vague Users**: If someone says "I don't know" or "whatever works," help them think through it with concrete examples
- **Off-Topic Users**: Politely redirect while acknowledging their interest in other aspects
- **Technical Users**: If someone uses technical terms, match their level while keeping it accessible

### Intelligent Context Handling:
- **Remember Previous Answers**: Don't ask for information already provided
- **Build on Responses**: Use what they've already told you to inform next questions
- **Adapt Question Style**: If someone prefers direct questions, be direct. If they prefer conversational flow, be conversational
- **Handle Interruptions**: If someone changes topics mid-conversation, acknowledge and gently guide back to the design process

## FINAL SUMMARY REQUIREMENTS

**ONLY provide a complete design summary when you have ratings for ALL THREE aspects:**
- Timber Layers: [0-5 rating]
- Surface Area: [0-5 rating] 
- Complexity: [0-5 rating]

**When all three are determined, provide this EXACT format:**
```
DESIGN SUMMARY:
Timber Layers: [X]/5 - [brief description]
Surface Area: [X]/5 - [brief description]
Complexity: [X]/5 - [brief description]

Proportions: [X]% | [X]% | [X]%

Your desk prioritizes [aspect] while maintaining [other aspects]. Ready to proceed?
```

**DO NOT provide summaries until all three parameters are complete.**

## EXAMPLE CUSTOMER SERVICE DIALOGUE

**Agent**: Welcome! I'm here to help you design your perfect desk. I'll guide you through three key aspects that determine desk functionality: timber layers, surface area, and complexity. Let's start - what will you primarily use this desk for?

**Customer**: I need a desk for my home office. I work from home full-time.

**Agent**: Excellent! A home office desk for full-time work. Let me help you determine the right balance of features. First, let's talk about **timber layers** - this affects strength, durability, and weight. Do you prefer a lighter desk with fewer layers, or a sturdier desk with more layers?

**Customer**: It'll mostly stay in one place, but I might rearrange my office occasionally.

**Agent**: Perfect! For occasional rearranging, I'd suggest a moderate timber layers rating of 3 - stable but not immovable. Now, let's discuss **surface area**. How much space do you need on your desk for your work items? Think about computers, paperwork, and other essentials.

**Customer**: I have lots of paperwork, office supplies, and need space for my computer setup.

**Agent**: That sounds like you need substantial surface area! I'd rate that as a 4 for surface area. Finally, let's explore **complexity** - this covers the angles and twists in the desk's shape. Do you prefer a desk with straight, simple lines, or one with more angular, twisted shapes?

**Customer**: I'd like some gentle curves but mostly straight lines.

**Agent**: Perfect! That's a complexity rating of 2. Now I have all three parameters. Let me provide your complete design summary:

DESIGN SUMMARY:
Timber Layers: 3/5 - Moderate stability, occasionally moveable
Surface Area: 4/5 - High capacity for documents and supplies
Complexity: 2/5 - Gentle curves with straight lines

Proportions: 33% | 44% | 22%

Your desk prioritizes surface area while maintaining moderate timber layers and simple geometry. Ready to proceed?

## ALTERNATIVE RESPONSE EXAMPLES

**For Brief Users:**
Customer: "Just need a desk for work."
Agent: "Got it! For work, let's figure out what you need. First, about timber layers - do you want something lightweight you can move around, or a solid desk that stays put?"

**For Vague Users:**
Customer: "I don't know, whatever works."
Agent: "No worries! Let me help you figure it out. For timber layers, think about this: do you ever need to move your desk, or will it stay in one spot?"

**For Detailed Users:**
Customer: "Well, I work from home full-time as a graphic designer, so I need space for my drawing tablet, two monitors, keyboard, mouse, and lots of reference materials. I also have a cat that likes to sit on my desk sometimes..."
Agent: "That's very helpful detail! I can see you need substantial surface area for all your equipment. Let me note that as a 4 for surface area. Now, about timber layers - with all that equipment, do you want a very sturdy desk, or something lighter?"

**For Off-Topic Users:**
Customer: "I really like the color blue. Can we make it blue?"
Agent: "I understand you're thinking about aesthetics! Let's focus on the functional aspects first - timber layers, surface area, and complexity. These determine how well the desk will work for you. We can discuss colors later."

## CRITICAL REMINDERS

1. **ALWAYS** maintain focus on the three aspects only
2. **ALWAYS** be friendly and professional
3. **ONLY** provide final summary when ALL THREE parameters are complete
4. **NEVER** discuss price, materials, colors, or aesthetics
5. **NEVER** make assumptions - ask clarifying questions
6. **AVOID** repetitive partial summaries throughout the conversation
7. **ADAPT** to the user's communication style
8. **REMEMBER** previous responses and build on them
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
                    "timber_layers": {"type": "integer", "description": "Rating for timber layers (0-5 scale)."},
                    "surface_area": {"type": "integer", "description": "Rating for surface area (0-5 scale)."},
                    "complexity": {"type": "integer", "description": "Rating for complexity (0-5 scale)."}
                },
                "required": ["timber_layers", "surface_area", "complexity"]
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
                            m = re.search(r"(\d+)", str(value))
                            if m:
                                ratings[aspect] = int(m.group(1))
                
                # Calculate percentages from ratings
                percentages = calculate_percentages(ratings)
                
                # Build result with both ratings and percentages
                result = {
                    "ratings": ratings,
                    "percentages": percentages
                }
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
        
        # Calculate percentages from ratings
        percentages = calculate_percentages(ratings)
        
        # Return both ratings and percentages
        return {
            "ratings": ratings,
            "percentages": percentages
        }

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