#!/usr/bin/env python3
"""
Bridge Design Chat Agent Launcher (Chat-Supervisor Pattern)

Clean separation:
- Chat: Gemini Live API for voice interaction  
- Supervisor: Bridge design coordination via tools
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Add necessary paths to Python path for proper imports."""
    # Get project root (where this script is located)
    project_root = Path(__file__).parent.absolute()
    
    # Add src directory to Python path
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Also add project root
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def main():
    """Launch the bridge design chat agent (chat-supervisor pattern)."""
    setup_python_path()
    
    try:
        from bridge_design_system.agents.chat_voice import (
            launch_bridge_chat_agent, 
            launch_text_chat,
            CHAT_DEPENDENCIES_AVAILABLE
        )
        from bridge_design_system.agents.chat_multimodel import (
            launch_multimodal_bridge_chat,
            MULTIMODAL_DEPENDENCIES_AVAILABLE
        )
        
        print("🌉 Bridge Design Chat Agent (Chat-Supervisor Pattern)")
        print("=" * 60)
        
        # Check for command line arguments
        mode = "voice"  # Default mode
        if len(sys.argv) > 1:
            if sys.argv[1] == "text":
                mode = "text"
            elif sys.argv[1] == "voice":
                mode = "voice"
            elif sys.argv[1] == "multimodal":
                mode = "multimodal"
            elif sys.argv[1] == "--help":
                print_help()
                return
        
        if mode == "text":
            # Launch text-based interface (no dependencies required)
            print("📝 Launching text-based bridge design chat...")
            print("💡 This mode doesn't require voice dependencies")
            print()
            launch_text_chat()
            return
        elif mode == "multimodal":
            # Launch multimodal interface (audio + video + images)
            if not MULTIMODAL_DEPENDENCIES_AVAILABLE:
                print("❌ Multimodal chat dependencies not available.")
                print("\nTo install required dependencies:")
                print("   uv add google-genai fastrtc gradio pillow")
                print("\nOr try simpler modes:")
                print("   python launch_voice_agent.py voice    # Audio only")
                print("   python launch_voice_agent.py text     # Text only")
                return
            
            print("🎭 Launching multimodal bridge design chat...")
            print("🎤 Audio: Real-time voice conversation")
            print("📹 Video: Camera input for visual context")
            print("🖼️ Images: Upload design references")
            print("🔧 AI Tools: Bridge design supervisor")
            print()
            
            # Check API key
            if not os.getenv("GEMINI_API_KEY"):
                print("❌ Error: GEMINI_API_KEY not found in environment variables")
                print("Please set your API key in your .env file:")
                print("  echo 'GEMINI_API_KEY=your_api_key_here' >> .env")
                print("Then restart the application.")
                return
            
            print("✅ Multimodal dependencies available")
            print("🚀 Starting multimodal bridge design system...")
            print(f"\n🌐 Open: http://localhost:7860")
            print("Press Ctrl+C to stop")
            print()
            
            # Launch multimodal system
            launch_multimodal_bridge_chat(server_port=7860, share=False, debug=True)
            return
        
        # Voice mode - check dependencies
        if not CHAT_DEPENDENCIES_AVAILABLE:
            print("❌ Voice chat dependencies not available.")
            print("\nTo install required dependencies:")
            print("   uv add google-genai fastrtc")
            print("\nOr try other modes:")
            print("   python launch_voice_agent.py text        # Text only")
            print("   python launch_voice_agent.py multimodal  # Audio + Video")
            return
        
        # Check API key
        if not os.getenv("GEMINI_API_KEY"):
            print("❌ Error: GEMINI_API_KEY not found in environment variables")
            print("Please set your API key in your .env file:")
            print("  echo 'GEMINI_API_KEY=your_api_key_here' >> .env")
            print("Then restart the application.")
            return
        
        print("✅ Chat dependencies available")
        print("🚀 Starting chat-supervisor bridge design system...")
        print("\nArchitecture:")
        print("  💬 Chat Layer: Gemini Live API (real-time voice)")
        print("  🔧 Supervisor: Bridge design coordination") 
        print("  🎯 Tools: Bridge design supervisor callable via voice")
        print(f"\n🌐 Open: http://localhost:7860")
        print("Press Ctrl+C to stop")
        print()
        
        # Launch new chat-supervisor system
        launch_bridge_chat_agent(server_port=7860, share=False, debug=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nInstall dependencies:")
        print("  uv add google-genai fastrtc")
        print("\nOr try text mode:")
        print("  python launch_voice_agent.py text")
    except KeyboardInterrupt:
        print("\n👋 Bridge chat agent stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def print_help():
    """Print help information."""
    print("🌉 Bridge Design Chat Agent Launcher")
    print("=" * 40)
    print("Usage:")
    print("  python launch_voice_agent.py [mode]")
    print()
    print("Modes:")
    print("  voice      - Voice chat with Gemini Live API (default)")
    print("  multimodal - Voice + Video + Image chat (full multimodal)")
    print("  text       - Text-based chat interface (no deps)")
    print("  --help     - Show this help message")
    print()
    print("Examples:")
    print("  python launch_voice_agent.py              # Voice mode")
    print("  python launch_voice_agent.py voice        # Voice mode")
    print("  python launch_voice_agent.py multimodal   # Multimodal mode")
    print("  python launch_voice_agent.py text         # Text mode")
    print()
    print("Dependencies:")
    print("  Voice mode:      uv add google-genai fastrtc")
    print("  Multimodal mode: uv add google-genai fastrtc gradio pillow")
    print("  Text mode:       No additional dependencies")
    print()
    print("Environment:")
    print("  GEMINI_API_KEY=your_api_key_here")
    print("  (Required - must be set in .env file)")

if __name__ == "__main__":
    main() 