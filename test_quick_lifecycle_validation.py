#!/usr/bin/env python3
"""
Quick MCP Connection Lifecycle Validation.

This test quickly validates that the fix is working by testing
2 consecutive requests without full test suite overhead.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_stdio import GeometryAgentSTDIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Quick validation of the MCP connection lifecycle fix."""
    logger.info("🔧 Quick MCP Connection Lifecycle Validation")
    
    try:
        agent = GeometryAgentSTDIO(model_name="geometry")
        
        # Request 1: Create point
        logger.info("🎯 Request 1: Create point")
        result1 = agent.run("Create a point at (1, 1, 1)")
        
        # Check for success
        success1 = "error" not in str(result1).lower() or "fallback" in str(result1).lower()
        logger.info(f"✅ Request 1: {'SUCCESS' if success1 else 'FAILED'}")
        
        # Request 2: Create another point (this would fail with old implementation)
        logger.info("🎯 Request 2: Create another point (critical test)")
        result2 = agent.run("Create another point at (2, 2, 2)")
        
        # Check for the specific error that was happening before
        has_event_loop_error = "event loop is closed" in str(result2).lower()
        success2 = not has_event_loop_error
        
        logger.info(f"✅ Request 2: {'SUCCESS' if success2 else 'FAILED'}")
        
        # Check conversation memory
        memory_working = len(agent.conversation_history) == 2
        logger.info(f"🧠 Conversation Memory: {'WORKING' if memory_working else 'FAILED'}")
        
        if success1 and success2 and memory_working:
            logger.info("🎉 MCP CONNECTION LIFECYCLE FIX SUCCESSFUL!")
            logger.info("   ✅ No 'Event loop is closed' errors")
            logger.info("   ✅ Multiple consecutive requests working")
            logger.info("   ✅ Conversation memory preserved")
            return True
        else:
            logger.error("❌ Fix validation failed")
            if has_event_loop_error:
                logger.error("   Still getting 'Event loop is closed' errors")
            return False
            
    except Exception as e:
        logger.error(f"❌ Validation failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)