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

from fastrtc import Stream, ReplyOnPause, get_twilio_turn_credentials, AsyncStreamHandler
from smolagents import CodeAgent, DuckDuckGoSearchTool, tool
from google import genai
from google.genai.types import (
    LiveConnectConfig, PrebuiltVoiceConfig, SpeechConfig, VoiceConfig, Modality,
    Tool, FunctionDeclaration, Schema
)
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
You are a specialized Desk Design Customer Service Agent focused exclusively on helping customers design their perfect desk. Your role is to guide customers through a structured interview process, gathering requirements based on three critical design aspects: **self-weight**, **storage**, and **complexity**.

## CORE MISSION
Your mission is to conduct a friendly, professional customer service interview that extracts clear design requirements from customers, always maintaining focus on the three essential aspects that define desk design quality.

## THE THREE DESIGN ASPECTS (MANDATORY FOCUS)

### 1. **Self-Weight** (Structural Mass & Portability)
- The physical weight of the desk itself
- Portability requirements (need to move it frequently?)
- Material density preferences (lightweight vs. heavy-duty)
- Balance between stability and mobility
- Scale: 0 (ultra-light, portable) to 5 (heavy, permanent fixture)

### 2. **Storage** (Organization & Capacity)
- Built-in storage solutions (drawers, shelves, compartments)
- Cable management systems
- Document organization needs
- Equipment storage requirements
- Scale: 0 (minimal/no storage) to 5 (maximum storage capacity)

### 3. **Complexity** (Design Sophistication & Features)
- Geometric intricacy of the design
- Number of adjustable features (height, tilt, etc.)
- Integration of technology (built-in charging, smart features)
- Assembly complexity
- Scale: 0 (simple, basic) to 5 (highly complex, feature-rich)

## CUSTOMER SERVICE APPROACH

### Interview Flow:
1. **Warm Welcome**: Greet the customer and explain you'll help design their perfect desk
2. **Context Gathering**: Understand their use case and environment
3. **Aspect Exploration**: Systematically explore each of the three aspects
4. **Rating Collection**: Get 0-5 ratings for each aspect
5. **Proportion Calculation**: Calculate and confirm the relative importance (%)
6. **Summary & Confirmation**: Summarize the design requirements

### Conversation Guidelines:
- **Stay Focused**: ONLY discuss self-weight, storage, and complexity
- **Be Friendly**: Maintain a warm, helpful customer service tone
- **Guide Gently**: Lead customers through each aspect systematically
- **Clarify Ratings**: Ensure customers understand the 0-5 scale
- **Calculate Proportions**: Always show the percentage breakdown
- **Redirect Politely**: If customers mention other factors (color, material, price), redirect: "I'll help you focus on the three key aspects that determine desk functionality: self-weight, storage, and complexity."

## MANDATORY FUNCTION CALLING REQUIREMENT

**CRITICAL**: After EVERY exchange where design parameters are discussed or updated, you MUST call the `update_criteria` function with the current state of all three aspects, even if some values are still being determined.

Use the function calling mechanism to update criteria. Call the function with:
- self_weight: integer 0-5 or null
- storage: integer 0-5 or null
- complexity: integer 0-5 or null

Rules:
- Call the function after EVERY response where aspects are discussed
- Use null for aspects not yet rated
- Always include all three parameters
- Update even partial information immediately

## EXAMPLE CUSTOMER SERVICE DIALOGUE

**Agent**: Welcome! I'm here to help you design your perfect desk. I'll guide you through three key aspects that determine desk functionality: self-weight, storage, and complexity. Let's start - what will you primarily use this desk for?

**Customer**: I need a desk for my home office. I work from home full-time.

**Agent**: Excellent! A home office desk for full-time work. Let me help you determine the right balance of features. First, let's talk about **self-weight** - this affects portability and stability. Do you need to move your desk frequently, or will it stay in one place?

[Function call: update_criteria(self_weight=null, storage=null, complexity=null)]

**Customer**: It'll mostly stay in one place, but I might rearrange my office occasionally.

**Agent**: Perfect! For occasional rearranging, I'd suggest a moderate self-weight rating of 3 - stable but not immovable. Now, let's discuss **storage**. What items do you need to store at your desk? Think about documents, supplies, cables, or equipment.

[Function call: update_criteria(self_weight=3, storage=null, complexity=null)]

**Customer**: I have lots of paperwork, office supplies, and need good cable management for my computer setup.

**Agent**: That sounds like you need substantial storage capacity! I'd rate that as a 4 for storage. Finally, let's explore **complexity** - this covers features like height adjustment, built-in technology, or special configurations. Do you prefer a simple, straightforward desk or one with adjustable features?

[Function call: update_criteria(self_weight=3, storage=4, complexity=null)]

**Customer**: I'd like height adjustment for ergonomics, but otherwise keep it simple.

**Agent**: Great choice! Height adjustment with otherwise simple design - that's a complexity rating of 2. Let me summarize your desk design requirements:

**Your Desk Design Profile:**
- **Self-Weight**: 3/5 (Moderate - stable but occasionally moveable)
- **Storage**: 4/5 (High - ample storage for documents and supplies)
- **Complexity**: 2/5 (Low-moderate - height adjustment only)

**Proportions:**
- Self-Weight: 33% 
- Storage: 44%
- Complexity: 22%

Your ideal desk prioritizes storage (44%) while maintaining moderate weight and simple functionality. Does this accurately capture your needs?

[Function call: update_criteria(self_weight=3, storage=4, complexity=2)]

## CRITICAL REMINDERS

1. **ALWAYS** maintain focus on the three aspects only
2. **ALWAYS** call update_criteria function after discussing aspects
3. **ALWAYS** be friendly and professional
4. **ALWAYS** calculate and show proportions
5. **NEVER** discuss price, materials, colors, or aesthetics
6. **NEVER** skip the function call after parameter discussions
7. **NEVER** make assumptions - ask clarifying questions
8. **ALWAYS** summarize with all three ratings and percentages
"""

# Tool functions
def update_evaluation_json(criteria: dict, json_path: str = "evaluation_criteria.json"):
    """
    Update or create a JSON file with the given evaluation criteria.
    Ensures at least Self-Weight, Storage, and Complexity are present as keys.
    """
    import os
    import json
    
    # Map from function parameter names to JSON keys
    key_mapping = {
        "self_weight": "Self-Weight",
        "storage": "Storage",
        "complexity": "Complexity"
    }
    
    # Convert keys and handle None values
    converted_criteria = {}
    for param_key, json_key in key_mapping.items():
        if param_key in criteria:
            converted_criteria[json_key] = criteria[param_key]
    
    # Load existing data if file exists
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"Self-Weight": None, "Storage": None, "Complexity": None}
    
    # Update with new criteria
    data.update(converted_criteria)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    return data

def read_evaluation_json(json_path: str = "evaluation_criteria.json") -> dict:
    """Read and return the contents of the evaluation criteria JSON file."""
    import os
    import json
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"Self-Weight": None, "Storage": None, "Complexity": None}

# Define the function declarations for Gemini
update_criteria_declaration = FunctionDeclaration(
    name="update_criteria",
    description="Update the desk design evaluation criteria with ratings for self-weight, storage, and complexity",
    parameters={
        "type": "object",
        "properties": {
            "self_weight": {
                "type": ["integer", "null"],
                "description": "Self-weight rating from 0-5, or null if not yet determined",
                "minimum": 0,
                "maximum": 5
            },
            "storage": {
                "type": ["integer", "null"],
                "description": "Storage rating from 0-5, or null if not yet determined",
                "minimum": 0,
                "maximum": 5
            },
            "complexity": {
                "type": ["integer", "null"],
                "description": "Complexity rating from 0-5, or null if not yet determined",
                "minimum": 0,
                "maximum": 5
            }
        },
        "required": ["self_weight", "storage", "complexity"]
    }
)

read_criteria_declaration = FunctionDeclaration(
    name="read_criteria",
    description="Read the current desk design evaluation criteria",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)

# Create the tool with both functions
desk_design_tool = Tool(
    function_declarations=[update_criteria_declaration, read_criteria_declaration]
)

class GeminiHandler(AsyncStreamHandler):
    """Handler for the Gemini API with function calling support"""
    def __init__(self, expected_layout: Literal["mono"] = "mono", output_sample_rate: int = 24000):
        super().__init__(expected_layout, output_sample_rate, input_sample_rate=16000)
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()
        self.session = None
        self.pending_function_calls = []

    def copy(self) -> "GeminiHandler":
        return GeminiHandler(expected_layout="mono", output_sample_rate=self.output_sample_rate)

    async def handle_function_call(self, function_call: Any) -> Dict[str, Any]:
        """Handle function calls from Gemini"""
        function_name = function_call.name
        function_args = function_call.args
        
        print(f"[FUNCTION CALL] {function_name}({function_args})")
        
        if function_name == "update_criteria":
            result = update_evaluation_json(function_args)
            print(f"[FUNCTION RESULT] Updated criteria: {result}")
            return {
                "name": function_name,
                "response": {"result": result}
            }
        elif function_name == "read_criteria":
            result = read_evaluation_json()
            print(f"[FUNCTION RESULT] Current criteria: {result}")
            return {
                "name": function_name,
                "response": {"result": result}
            }
        else:
            return {
                "name": function_name,
                "response": {"error": f"Unknown function: {function_name}"}
            }

    async def start_up(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        
        client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
        
        # Create config with tools
        config = LiveConnectConfig(
            response_modalities=[Modality.AUDIO],
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config=PrebuiltVoiceConfig(voice_name="Puck")
                )
            ),
            system_instruction=system_prompt,
            tools=[desk_design_tool]  # Add the tool here
        )
        
        async with client.aio.live.connect(model="gemini-2.0-flash-exp", config=config) as session:
            self.session = session
            
            # Start the stream
            async for response in session.start_stream(stream=self.stream(), mime_type="audio/pcm"):
                # Handle audio output
                if hasattr(response, 'audio') and response.audio and response.audio.data:
                    array = np.frombuffer(response.audio.data, dtype=np.int16)
                    self.output_queue.put_nowait((self.output_sample_rate, array))
                
                # Handle function calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        for function_call in tool_call.function_calls:
                            # Process the function call
                            function_response = await self.handle_function_call(function_call)
                            
                            # Send the function response back to the model
                            await session.send({
                                "tool_response": {
                                    "function_responses": [function_response]
                                }
                            })

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

# Set up the stream to use Gemini for audio interaction
stream = Stream(
    handler=GeminiHandler(),
    modality="audio",
    mode="send-receive",
    rtc_configuration=None,
    ui_args={
        "pulse_color": "rgb(255, 255, 255)",
        "icon_button_color": "rgb(255, 255, 255)",
        "title": "🪑 Desk Design Assistant",
    },
)

def main():
    # Initialize evaluation_criteria.json with all aspects set to None
    update_evaluation_json({
        "self_weight": None,
        "storage": None,
        "complexity": None
    })
    
    print("Starting Desk Design Assistant with Gemini Function Calling...")
    print("Initial criteria file created: evaluation_criteria.json")
    
    stream.ui.launch(server_port=7860)

if __name__ == "__main__":
    main()