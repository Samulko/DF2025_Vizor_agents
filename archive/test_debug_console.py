#!/usr/bin/env python3
"""
Test the debugging console for chat-to-triage integration.
"""

def test_text_chat_debug():
    """Test the text chat interface with full debugging."""
    print("🧪 Testing Text Chat with Debug Console")
    print("=" * 60)
    
    try:
        from src.bridge_design_system.agents.chat_voice import BridgeTextChatInterface
        
        print("🚀 [TEST] Initializing text chat interface...")
        chat = BridgeTextChatInterface()
        print("✅ [TEST] Text chat interface initialized")
        
        # Test a simple request to see the debug output
        test_request = "What tools are available in the bridge design system?"
        print(f"\n🧪 [TEST] Sending test request: '{test_request}'")
        
        # This should trigger all the debug output
        response = chat.triage_system.handle_design_request(test_request)
        
        print("\n📊 [TEST RESULTS]")
        print(f"✅ Test completed successfully")
        print(f"📝 Response length: {len(response.message) if response.message else 0} characters")
        print(f"🎯 Success status: {response.success}")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_handler_debug():
    """Test the voice handler tool creation with debugging."""
    print("\n🧪 Testing Voice Handler Tool Creation")
    print("=" * 60)
    
    try:
        from src.bridge_design_system.agents.chat_voice import BridgeChatHandler
        
        print("🚀 [TEST] Creating voice handler...")
        handler = BridgeChatHandler()
        print("✅ [TEST] Voice handler created")
        
        print("🛠️ [TEST] Creating Gemini tools...")
        tools = handler._create_gemini_tools()
        print(f"✅ [TEST] Created {len(tools)} tools")
        
        # Test the tool function directly
        tool_func = tools[0]
        test_request = "Show me the current bridge design status"
        
        print(f"\n🧪 [TEST] Testing tool function with: '{test_request}'")
        
        # This should trigger all the debug output including the 🚨 markers
        response = tool_func(test_request)
        
        print("\n📊 [TEST RESULTS]")
        print(f"✅ Tool test completed")
        print(f"📝 Response length: {len(response)} characters")
        print(f"📤 Sample response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🐛 Testing Debug Console for Chat-to-Triage Integration")
    print("=" * 80)
    print("This test will show you all the debug markers you'll see when using the system:")
    print("🚨 = Function calls from Gemini")
    print("🎯 = Triage agent interactions") 
    print("🔧 = Internal debug steps")
    print("📊 = Response information")
    print("💥 = Errors")
    print("🔥 = Tool call handlers")
    print("=" * 80)
    
    success1 = test_text_chat_debug()
    success2 = test_voice_handler_debug()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("✅ All debug tests passed!")
        print()
        print("🎯 Now you can run the actual chat agents and see:")
        print("   - When Gemini calls your functions")
        print("   - When the triage agent is invoked")
        print("   - What responses are generated")
        print("   - Any errors that occur")
        print()
        print("🚀 Ready to launch:")
        print("   uv run python -c \"from src.bridge_design_system.agents.chat_voice import launch_bridge_chat_agent; launch_bridge_chat_agent()\"")
    else:
        print("❌ Some debug tests failed. Check the errors above.")