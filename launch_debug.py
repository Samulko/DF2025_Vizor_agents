#!/usr/bin/env python3
"""
Enhanced debug launcher for the multimodal bridge design chat agent.
"""

if __name__ == "__main__":
    import logging
    import os
    import sys
    
    # Set maximum debug level
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug_multimodal.log')
        ]
    )
    
    # Enable all debug options
    os.environ['DEBUG'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['GRADIO_DEBUG'] = 'true'
    
    # Debug specific libraries
    logging.getLogger('google_genai').setLevel(logging.DEBUG)
    logging.getLogger('fastrtc').setLevel(logging.INFO)  # Too verbose on DEBUG
    logging.getLogger('src.bridge_design_system').setLevel(logging.DEBUG)
    
    print("🚀 Launching ENHANCED DEBUG Multimodal Bridge Design Chat Agent...")
    print("🐛 Maximum debugging enabled")
    print("📝 Debug log: debug_multimodal.log")
    print("🔍 Tool calls will be logged in detail")
    print("🌐 Web Interface: http://localhost:7860")
    print()
    
    try:
        from src.bridge_design_system.agents.chat_multimodel import launch_multimodal_bridge_chat
        
        launch_multimodal_bridge_chat(
            debug=True,
            show_error=True,
            server_port=7860
        )
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        import traceback
        traceback.print_exc()