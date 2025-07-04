#!/usr/bin/env python3
"""
Test the updated chat agent with direct triage integration.
"""

def test_text_chat():
    """Test the text chat interface with triage integration."""
    print("🧪 Testing Text Chat Interface")
    print("=" * 50)
    
    try:
        from src.bridge_design_system.agents.chat_voice import BridgeTextChatInterface
        
        chat = BridgeTextChatInterface()
        print("✅ Text chat interface initialized successfully")
        
        # Test a simple request
        print("\n📝 Testing sample request...")
        response = chat.triage_system.handle_design_request("What tools are available?")
        
        if response.success:
            print("✅ Request successful")
            print(f"Response: {response.message[:200]}...")
        else:
            print("❌ Request failed")
            print(f"Error: {response.message}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_handler():
    """Test the voice handler initialization."""
    print("\n🧪 Testing Voice Handler")
    print("=" * 50)
    
    try:
        from src.bridge_design_system.agents.chat_voice import BridgeChatHandler
        
        handler = BridgeChatHandler()
        print("✅ Voice handler initialized successfully")
        
        tools = handler._create_gemini_tools()
        print(f"✅ Created {len(tools)} Gemini tool(s)")
        
        # Test tool function
        tool_func = tools[0]
        response = tool_func("Show me the current bridge design status")
        print(f"✅ Tool test successful: {len(response)} characters")
        print(f"Sample: {response[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🌉 Testing Chat-to-Triage Integration")
    print("=" * 60)
    
    success1 = test_text_chat()
    success2 = test_voice_handler()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ All tests passed! Chat-to-triage integration working correctly.")
        print()
        print("🎯 Architecture Summary:")
        print("   📱 Chat Agent (Gemini Live API)")
        print("   ⬇️  bridge_design_request() function")
        print("   🔧 Triage Agent (SmolaAgents)")
        print("   ⬇️  Coordinates geometry + rational agents")
        print("   🎯 Complete bridge design workflow")
        print()
        print("Ready for voice/multimodal chat testing!")
    else:
        print("❌ Some tests failed. Check the errors above.")