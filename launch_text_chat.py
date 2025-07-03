#!/usr/bin/env python3
"""
Simple text-based launcher for testing the multimodal bridge design chat agent.
"""

if __name__ == "__main__":
    import os
    from src.bridge_design_system.agents.chat_multimodel import create_multimodal_bridge_interface
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY environment variable not set!")
        print("Please set it with: export GEMINI_API_KEY=your_key_here")
        exit(1)
    
    print("🚀 Launching Text-Based Multimodal Bridge Design Chat Agent...")
    print("🌐 This will open a web interface where you can type commands")
    print("📝 Focus on text interaction first, then add voice/video")
    
    try:
        demo = create_multimodal_bridge_interface()
        demo.launch(
            server_port=7860,
            share=False,
            debug=True,
            show_error=True,
            inbrowser=True  # Automatically open browser
        )
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure GEMINI_API_KEY is set: export GEMINI_API_KEY=your_key")
        print("2. Check dependencies: uv add google-genai fastrtc gradio pillow")
        print("3. Try the voice agent first: uv run python launch_voice_agent.py voice")