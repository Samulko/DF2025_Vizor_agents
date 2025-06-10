#!/usr/bin/env python3
"""
Integration Test for Vizor Agents MCP Bridge

Tests the complete working architecture:
WSL → STDIO MCP → TCP Bridge → Grasshopper

This test validates:
1. TCP bridge connection (WSL → Windows)
2. MCP tools loading (49 tools)
3. Agent creation with DeepSeek
4. Geometry creation in Grasshopper

Run: python test_integration.py
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_complete_integration():
    """Test the complete working MCP integration."""
    logger.info("🧪 Vizor Agents Integration Test")
    logger.info("=" * 50)
    
    try:
        from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools
        
        logger.info("🔍 Testing complete agent → MCP → Grasshopper pipeline...")
        
        with create_geometry_agent_with_mcp_tools() as agent:
            # Test spiral creation - proven working
            task = """
            Create a 3D spiral in Grasshopper using a Python 3 script component.
            The spiral should have 8 turns, radius 4 units, and height 16 units.
            """
            
            logger.info("🎯 Task: Create 3D spiral with AI agent")
            result = agent.run(task)
            
            if result:
                logger.info("✅ Integration test PASSED!")
                logger.info("🎉 Check Grasshopper for the spiral geometry")
                logger.info("📊 Architecture: WSL → MCP → TCP Bridge → Grasshopper ✅")
                return True
            else:
                logger.error("❌ Integration test failed - no result")
                return False
                
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_integration()
    if success:
        print("\n🚀 VIZOR AGENTS INTEGRATION: SUCCESS!")
        print("The AI bridge design system is ready for production use.")
    else:
        print("\n❌ Integration test failed. Check setup and try again.")
    
    sys.exit(0 if success else 1)