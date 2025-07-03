"""
Multimodal Bridge Design Chat Agent using Gemini Live API.

Supports real-time audio, video (camera), and text input for comprehensive bridge design workflows.
Engineers can show sketches, CAD models, or point camera at physical structures while discussing design.
"""

import asyncio
import base64
import json
import os
import time
from io import BytesIO
from typing import Dict, Any, List, Optional
import numpy as np
import websockets
from dotenv import load_dotenv
from PIL import Image
import pathlib

try:
    import gradio as gr
    from fastrtc import (
        AsyncAudioVideoStreamHandler,
        Stream,
        WebRTC,
        get_cloudflare_turn_credentials_async,
        wait_for_item,
    )
    from google import genai
    from gradio.utils import get_space
    MULTIMODAL_DEPENDENCIES_AVAILABLE = True
except ImportError:
    MULTIMODAL_DEPENDENCIES_AVAILABLE = False

from .triage_chat_supervisor import BridgeDesignSupervisor, create_bridge_design_supervisor_tools
from ..config.logging_config import get_logger

logger = get_logger(__name__)
load_dotenv()


def encode_audio(data: np.ndarray) -> dict:
    """Encode Audio data to send to Gemini"""
    return {
        "mime_type": "audio/pcm",
        "data": base64.b64encode(data.tobytes()).decode("UTF-8"),
    }


def encode_image(data: np.ndarray) -> dict:
    """Encode image data to send to Gemini"""
    with BytesIO() as output_bytes:
        pil_image = Image.fromarray(data)
        pil_image.save(output_bytes, "JPEG")
        bytes_data = output_bytes.getvalue()
    base64_str = str(base64.b64encode(bytes_data), "utf-8")
    return {"mime_type": "image/jpeg", "data": base64_str}


class GeminiHandler(AsyncAudioVideoStreamHandler):
    """
    Multimodal handler for bridge design using Gemini Live API.
    
    Supports:
    - Real-time voice conversation
    - Camera input for visual context (sketches, CAD models, physical structures)
    - Image upload for design references
    - Bridge design supervisor tools for complex engineering tasks
    """

    def __init__(self):
        super().__init__(
            "mono",
            output_sample_rate=24000,
            input_sample_rate=16000,
        )
        
        # Initialize bridge design supervisor
        self.bridge_supervisor = BridgeDesignSupervisor()
        self.supervisor_tools = create_bridge_design_supervisor_tools(self.bridge_supervisor)
        
        # Async queues for multimodal data
        self.audio_queue = asyncio.Queue()
        self.video_queue = asyncio.Queue()
        self.session = None
        self.last_frame_time = 0
        self.quit = asyncio.Event()
        
        # Visual context tracking for bridge design
        self.current_visual_context = None
        self.uploaded_image_context = None
        
        logger.info("🌉 Bridge multimodal handler initialized with supervisor tools")

    def copy(self) -> "GeminiHandler":
        return GeminiHandler()

    async def start_up(self):
        """Initialize Gemini Live session with multimodal capabilities."""
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"), 
            http_options={"api_version": "v1alpha"}
        )
        
        config = {
            "response_modalities": ["AUDIO"],
            "tools": self._create_gemini_tools(),
            "system_instruction": self._get_multimodal_bridge_prompt(),
        }
        
        async with client.aio.live.connect(
            model="gemini-live-2.5-flash-preview",
            config=config,
        ) as session:
            self.session = session
            
            # Handle tool calls
            session.on_tool_call = self._handle_tool_call
            
            while not self.quit.is_set():
                turn = self.session.receive()
                try:
                    async for response in turn:
                        if data := response.data:
                            audio = np.frombuffer(data, dtype=np.int16).reshape(1, -1)
                            self.audio_queue.put_nowait(audio)
                except websockets.exceptions.ConnectionClosedOK:
                    logger.info("Gemini Live connection closed")
                    break

    async def video_receive(self, frame: np.ndarray):
        """Receive video frame from camera."""
        self.video_queue.put_nowait(frame)
        
        if self.session:
            # Send camera frame every 2 seconds for visual context
            if time.time() - self.last_frame_time > 2:
                self.last_frame_time = time.time()
                
                # Store current visual context for bridge design
                self.current_visual_context = frame
                
                logger.debug("📹 Sending camera frame to Gemini for visual context")
                await self.session.send(input=encode_image(frame))
                
                # Also send uploaded image if available
                if self.uploaded_image_context is not None:
                    logger.debug("🖼️ Sending uploaded image to Gemini")
                    await self.session.send(input=encode_image(self.uploaded_image_context))

    async def video_emit(self):
        """Emit video frame (for display)."""
        frame = await wait_for_item(self.video_queue, 0.01)
        if frame is not None:
            return frame
        else:
            # Return placeholder frame if no video
            return np.zeros((100, 100, 3), dtype=np.uint8)

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        """Receive audio frame from microphone."""
        _, array = frame
        array = array.squeeze()
        audio_message = encode_audio(array)
        if self.session:
            await self.session.send(input=audio_message)

    async def emit(self):
        """Emit audio response."""
        array = await wait_for_item(self.audio_queue, 0.01)
        if array is not None:
            return (self.output_sample_rate, array)
        return array

    async def shutdown(self) -> None:
        """Shutdown handler."""
        if self.session:
            self.quit.set()
            await self.session.close()
            self.quit.clear()

    def update_uploaded_image(self, image: np.ndarray):
        """Update uploaded image context for bridge design."""
        if image is not None:
            self.uploaded_image_context = image
            logger.info("🖼️ Updated uploaded image context for bridge design")
        else:
            self.uploaded_image_context = None

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
        """Handle tool calls from Gemini Live session with visual context."""
        try:
            tool_name = tool_call.name
            tool_args = tool_call.args or {}
            
            logger.info(f"🛠️ Handling multimodal tool call: {tool_name}")
            
            # Add visual context to tool calls if available
            if self.current_visual_context is not None or self.uploaded_image_context is not None:
                visual_context = {
                    "has_camera_input": self.current_visual_context is not None,
                    "has_uploaded_image": self.uploaded_image_context is not None,
                    "visual_analysis": "Visual context available for bridge design analysis"
                }
                tool_args["visual_context"] = visual_context
                logger.debug("📹 Added visual context to tool call")
            
            # Find and call the corresponding supervisor tool
            tool_func = None
            for func in self.supervisor_tools:
                if func.__name__ == tool_name:
                    tool_func = func
                    break
            
            if tool_func:
                # Call the supervisor tool with enhanced context
                result = tool_func(**tool_args)
                logger.info(f"✅ Multimodal tool call completed: {tool_name}")
                return result
            else:
                logger.error(f"❌ Unknown tool: {tool_name}")
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"❌ Multimodal tool call failed: {e}")
            return {"error": str(e)}

    def _get_multimodal_bridge_prompt(self) -> str:
        """Get system prompt for multimodal bridge design chat agent from markdown file."""
        prompt_path = pathlib.Path(__file__).parent.parent.parent / ".." / ".." / "system_prompts" / "chat_agent.md"
        prompt_path = prompt_path.resolve()
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not load system prompt from {prompt_path}: {e}. Using fallback.")
            return """You are an advanced bridge design assistant with multimodal capabilities.\n\nYou can see what the user shows you through their camera or uploaded images, hear their voice, and coordinate complex bridge engineering tasks.\n\n**Visual Capabilities:**\n- Analyze sketches, drawings, and CAD models shown to camera\n- Review uploaded design references and photos\n- Identify bridge types, components, and structural elements\n- Interpret engineering diagrams and technical drawings\n\n**For simple questions**, respond directly:\n- Basic bridge engineering concepts and terminology\n- Material properties and construction methods\n- Design principles and standards\n- Visual analysis of what you can see\n\n**For complex design tasks**, use the bridge design supervisor tools:\n- Creating or modifying bridge components\n- Structural analysis and calculations\n- Parametric design in Grasshopper  \n- Multi-step engineering workflows\n\n**When users show you visual content:**\n- Acknowledge what you can see\n- Provide relevant engineering insights\n- Ask clarifying questions about the design\n- Suggest improvements or alternatives\n\nAvailable tools:\n- `design_bridge_component`: For bridge design and modification\n- `get_bridge_design_status`: To check system status\n- `reset_bridge_design`: For fresh design sessions\n\nKeep responses natural and conversational. Be technical but accessible. When you see visual content, incorporate it into your engineering analysis and recommendations."""


def create_multimodal_bridge_interface():
    """Create the multimodal bridge design interface with audio, video, and image support."""
    
    if not MULTIMODAL_DEPENDENCIES_AVAILABLE:
        raise ImportError(
            "Multimodal dependencies not available. Install with:\n"
            "  uv add google-genai fastrtc gradio pillow\n"
            "  (No Cloudflare TURN or Hugging Face token required)"
        )
    
    css = """
    #video-source {max-width: 600px !important; max-height: 600 !important;}
    #bridge-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    #bridge-info {
        background-color: var(--block-background-fill);
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    }
    """
    
    with gr.Blocks(css=css, title="🌉 Bridge Design Multimodal Assistant") as demo:
        # Header
        gr.HTML(
            """
            <div id="bridge-header">
                <div style='display: flex; align-items: center; justify-content: center; gap: 20px'>
                    <div>
                        <h1>🌉 Bridge Design Multimodal Assistant</h1>
                        <p>Voice + Video + Image AI for Bridge Engineering</p>
                        <p>Show sketches, CAD models, or point camera at structures while discussing design</p>
                    </div>
                </div>
            </div>
            """,
            elem_id="bridge-header"
        )
        
        # Info section
        with gr.Row():
            gr.HTML(
                """
                <div id="bridge-info">
                    <h3>🎯 Multimodal Capabilities</h3>
                    <ul>
                        <li><strong>🎤 Voice:</strong> Natural conversation about bridge engineering</li>
                        <li><strong>📹 Camera:</strong> Show sketches, CAD models, or physical structures</li>
                        <li><strong>🖼️ Images:</strong> Upload design references and technical drawings</li>
                        <li><strong>🔧 AI Tools:</strong> Advanced bridge design coordination and analysis</li>
                    </ul>
                </div>
                """,
                elem_id="bridge-info"
            )
        
        # Main interface
        with gr.Row() as main_row:
            with gr.Column(scale=2):
                webrtc = WebRTC(
                    label="🎥 Bridge Design Video Chat",
                    modality="audio-video",
                    mode="send-receive",
                    elem_id="video-source",
                    # Removed Cloudflare TURN credentials; using default config (no external TURN)
                    rtc_configuration=None,  # No TURN/STUN servers specified
                    icon="https://www.gstatic.com/lamda/images/gemini_favicon_f069958c85030456e93de685481c559f160ea06b.png",
                    pulse_color="rgb(255, 255, 255)",
                    icon_button_color="rgb(255, 255, 255)",
                )
                
            with gr.Column(scale=1):
                gr.Markdown("### 📄 Design References")
                image_input = gr.Image(
                    label="Upload Design Reference",
                    type="numpy",
                    sources=["upload", "clipboard"],
                )
                
                gr.Markdown("### 💡 Usage Tips")
                gr.Markdown("""
                **Voice Commands:**
                - "Create a cable-stayed bridge"
                - "Analyze this structure"
                - "What's the span length?"
                
                **Visual Input:**
                - Show hand-drawn sketches
                - Point camera at CAD screens
                - Upload technical drawings
                - Show physical bridge models
                """)
        
        # Create handler and connect streams
        handler = GeminiHandler()
        
        # Update uploaded image context when image changes
        def update_image_context(image):
            if hasattr(handler, 'update_uploaded_image'):
                handler.update_uploaded_image(image)
            return image
        
        image_input.change(
            fn=update_image_context,
            inputs=[image_input],
            outputs=[image_input]
        )
        
        # Connect WebRTC stream
        webrtc.stream(
            handler,
            inputs=[webrtc, image_input],
            outputs=[webrtc],
            time_limit=300 if get_space() else None,  # 5 minutes
            concurrency_limit=2 if get_space() else None,
        )
        
        # Footer
        gr.HTML(
            """
            <div style='text-align: center; margin-top: 20px; padding: 10px; color: #666;'>
                <p>🌉 Advanced Bridge Design System | Powered by Gemini Live API + Bridge Design Supervisor</p>
            </div>
            """
        )
    
    return demo


def launch_multimodal_bridge_chat(server_port: int = 7860, share: bool = False, debug: bool = True):
    """Launch multimodal bridge design chat agent with audio, video, and image support."""
    
    if not MULTIMODAL_DEPENDENCIES_AVAILABLE:
        print("❌ Multimodal dependencies not available.")
        print("Install with:")
        print("  uv add google-genai fastrtc gradio pillow")
        return
    
    print("🌉 Starting Multimodal Bridge Design Chat Agent")
    print("=" * 60)
    print("🎤 Audio: Real-time voice conversation")
    print("📹 Video: Camera input for visual context")
    print("🖼️ Images: Upload design references and sketches")
    print("🔧 AI Tools: Bridge design supervisor coordination")
    print(f"🌐 Web Interface: http://localhost:{server_port}")
    print()
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ Warning: GEMINI_API_KEY not found in environment")
        print("You'll need to enter it in the web interface")
        print()
    
    try:
        # Create and launch multimodal interface
        demo = create_multimodal_bridge_interface()
        demo.launch(
            server_port=server_port,
            share=share,
            debug=debug,
            show_error=True
        )
        
    except Exception as e:
        logger.error(f"Failed to launch multimodal chat agent: {e}")
        print(f"❌ Launch failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check API key: export GEMINI_API_KEY=your_key")
        print("2. Install dependencies: uv add google-genai fastrtc gradio pillow")
        print("3. Check camera permissions in browser")


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("🌉 Multimodal Bridge Design Chat Agent")
        print("Usage: python bridge_multimodal_chat_agent.py")
        print()
        print("Features:")
        print("  🎤 Real-time voice conversation")
        print("  📹 Camera input for visual context")
        print("  🖼️ Image upload for design references")
        print("  🔧 Bridge design supervisor tools")
        print()
        print("Dependencies:")
        print("  uv add google-genai fastrtc gradio pillow")
        print()
        print("Environment:")
        print("  GEMINI_API_KEY=your_api_key_here")
    else:
        launch_multimodal_bridge_chat(debug=True) 