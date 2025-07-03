#!/usr/bin/env python3
"""
Launcher for the multimodal bridge design chat agent.
"""

if __name__ == "__main__":
    import logging
    import os
    from src.bridge_design_system.agents.chat_multimodel import launch_multimodal_bridge_chat
    
    # Enable detailed debug logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set debug environment
    os.environ['DEBUG'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    print("🚀 Launching Multimodal Bridge Design Chat Agent (DEBUG MODE)...")
    print("🐛 Debug logging enabled")
    print("📊 Gradio debug mode: ON")
    
    launch_multimodal_bridge_chat(
        debug=True,           # Gradio debug mode
        show_error=True,      # Show detailed errors
        server_port=7860      # Default port
    )