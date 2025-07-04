#!/usr/bin/env python3
"""
Test script for Gemini function calling with the triage agent.

This demonstrates the proper Gemini format vs SmolaAgents format.
"""

import os
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_function_calling_formats():
    """Test both formats to show the difference."""
    
    print("🔬 Testing Gemini Function Calling Formats")
    print("=" * 60)
    
    # Test 1: Initialize the multimodal handler
    print("1. Testing multimodal handler initialization...")
    try:
        from src.bridge_design_system.agents.chat_multimodel import GeminiHandler
        handler = GeminiHandler()
        tools = handler._create_gemini_tools()
        
        print(f"✅ Created {len(tools)} Gemini tools in Python function format")
        
        # Show tool signatures
        for i, tool in enumerate(tools, 1):
            print(f"   Tool {i}: {tool.__name__}")
            print(f"            {tool.__doc__.split('.')[0] if tool.__doc__ else 'No description'}")
            
            # Show function signature
            import inspect
            sig = inspect.signature(tool)
            print(f"            Signature: {tool.__name__}{sig}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Test direct function calls
    print("2. Testing direct function calls...")
    try:
        # Test bridge status
        status_tool = tools[1]  # get_bridge_status
        result = status_tool()
        print(f"✅ Bridge status call successful")
        print(f"   Result length: {len(result)} characters")
        print(f"   Sample: {result[:100]}...")
        print()
        
        # Test bridge design
        design_tool = tools[0]  # process_bridge_design
        result = design_tool(
            design_requirements="Create a simple beam bridge spanning 50 meters",
            component_type="beam"
        )
        print(f"✅ Bridge design call successful")
        print(f"   Result length: {len(result)} characters")
        print(f"   Sample: {result[:100]}...")
        print()
        
    except Exception as e:
        print(f"❌ Function call error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Show the old vs new format
    print("3. Format comparison:")
    print("OLD (SmolaAgents JSON Schema):")
    print('''   {
     "function_declarations": [{
       "name": "process_bridge_design",
       "description": "Process bridge design...",
       "parameters": {
         "type": "object",
         "properties": {
           "design_requirements": {"type": "string", ...}
         }
       }
     }]
   }''')
    print()
    print("NEW (Gemini Python Functions):")
    print(f"   [{tools[0].__name__}, {tools[1].__name__}, {tools[2].__name__}]")
    print("   # Direct Python functions with type hints and docstrings")
    print()
    
    print("✅ All tests passed! Gemini function calling is properly implemented.")
    return True

def test_with_actual_gemini():
    """Test with actual Gemini API if API key is available."""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set, skipping live API test")
        return
    
    print("4. Testing with actual Gemini API...")
    try:
        from google import genai
        from google.genai import types
        
        # Initialize client
        client = genai.Client(api_key=api_key)
        
        # Create tools
        from src.bridge_design_system.agents.chat_multimodel import GeminiHandler
        handler = GeminiHandler()
        tools = handler._create_gemini_tools()
        
        # Create chat with tools
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                tools=tools,
                system_instruction="You are a bridge design assistant. Use the available tools to help with bridge engineering tasks."
            )
        )
        
        # Test function calling
        response = chat.send_message("What's the current status of the bridge design system?")
        
        print("✅ Gemini API call successful")
        print(f"   Response: {response.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_function_calling_formats()
    
    if success:
        test_with_actual_gemini()
        
        print("\n🎉 Function calling implementation complete!")
        print("   - Gemini format: Python functions with type hints")
        print("   - SmolaAgents format: JSON schemas (old way)")
        print("   - Ready for testing in multimodal chat agent")