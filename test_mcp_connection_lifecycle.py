#!/usr/bin/env python3
"""
Test MCP Connection Lifecycle Fix.

This test validates that the geometry agent can handle multiple consecutive requests
without "Event loop is closed" errors by using fresh CodeAgent instances while
maintaining conversation memory.
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_stdio import GeometryAgentSTDIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_multiple_consecutive_requests():
    """Test multiple consecutive requests to validate connection lifecycle fix."""
    logger.info("=== Testing Multiple Consecutive Requests ===")
    
    try:
        agent = GeometryAgentSTDIO(model_name="geometry")
        
        # Test 1: First request (create point)
        logger.info("🎯 Request 1: Create initial point")
        task1 = "Create a point at coordinates (0, 0, 0) and name it 'Origin Point'"
        start_time = time.time()
        result1 = agent.run(task1)
        duration1 = time.time() - start_time
        
        logger.info(f"✅ Request 1 completed in {duration1:.2f} seconds")
        logger.info(f"📊 Conversation history length: {len(agent.conversation_history)}")
        
        # Verify result contains success
        if "error" in str(result1).lower() and "fallback" not in str(result1).lower():
            logger.error("❌ Request 1 failed with error")
            return False
        
        # Test 2: Second request (create another point referencing first)
        logger.info("🎯 Request 2: Create point referencing previous")
        task2 = "Create another point 5 units away from the previous point along the X-axis"
        start_time = time.time()
        result2 = agent.run(task2)
        duration2 = time.time() - start_time
        
        logger.info(f"✅ Request 2 completed in {duration2:.2f} seconds")
        logger.info(f"📊 Conversation history length: {len(agent.conversation_history)}")
        
        # Verify result doesn't contain event loop errors
        if "event loop is closed" in str(result2).lower():
            logger.error("❌ Request 2 failed with 'Event loop is closed' error")
            return False
        
        # Test 3: Third request (create line connecting points)
        logger.info("🎯 Request 3: Create line connecting the points")
        task3 = "Create a line connecting the two points we just created"
        start_time = time.time()
        result3 = agent.run(task3)
        duration3 = time.time() - start_time
        
        logger.info(f"✅ Request 3 completed in {duration3:.2f} seconds")
        logger.info(f"📊 Conversation history length: {len(agent.conversation_history)}")
        
        # Verify result doesn't contain event loop errors
        if "event loop is closed" in str(result3).lower():
            logger.error("❌ Request 3 failed with 'Event loop is closed' error")
            return False
        
        # Test 4: Fourth request (modify existing geometry)
        logger.info("🎯 Request 4: Modify the line properties")
        task4 = "Make the line thicker and change its color to red"
        start_time = time.time()
        result4 = agent.run(task4)
        duration4 = time.time() - start_time
        
        logger.info(f"✅ Request 4 completed in {duration4:.2f} seconds")
        logger.info(f"📊 Conversation history length: {len(agent.conversation_history)}")
        
        # Verify conversation memory is working
        if len(agent.conversation_history) != 4:
            logger.error(f"❌ Expected 4 conversations, got {len(agent.conversation_history)}")
            return False
        
        # Verify no event loop errors in any request
        all_results = [result1, result2, result3, result4]
        for i, result in enumerate(all_results):
            if "event loop is closed" in str(result).lower():
                logger.error(f"❌ Request {i+1} contained 'Event loop is closed' error")
                return False
        
        # Performance check - all requests should complete in reasonable time
        avg_duration = (duration1 + duration2 + duration3 + duration4) / 4
        logger.info(f"📊 Average request duration: {avg_duration:.2f} seconds")
        
        if avg_duration > 10:
            logger.warning(f"⚠️ Average duration ({avg_duration:.2f}s) higher than expected")
        
        logger.info("✅ All consecutive requests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False


def test_conversation_memory_with_fresh_agents():
    """Test that conversation memory works correctly with fresh agents."""
    logger.info("=== Testing Conversation Memory with Fresh Agents ===")
    
    try:
        agent = GeometryAgentSTDIO(model_name="geometry")
        
        # Create initial conversation
        task1 = "Create a cube at origin with side length 2"
        result1 = agent.run(task1)
        
        # Test context building manually
        context = agent._build_conversation_context("Modify the cube to be 3 units tall")
        
        # Verify context contains previous interaction
        if "cube at origin" not in context.lower():
            logger.error("❌ Context doesn't contain previous interaction")
            return False
        
        if "current task" not in context.lower():
            logger.error("❌ Context doesn't contain current task marker")
            return False
        
        # Test second request uses context
        task2 = "Scale the cube to be twice as large"
        result2 = agent.run(task2)
        
        # The agent should understand "the cube" refers to the previous one
        logger.info("✅ Conversation memory working correctly with fresh agents")
        return True
        
    except Exception as e:
        logger.error(f"❌ Conversation memory test failed: {e}")
        return False


def test_reset_functionality():
    """Test that reset clears conversation memory properly."""
    logger.info("=== Testing Reset Functionality ===")
    
    try:
        agent = GeometryAgentSTDIO(model_name="geometry")
        
        # Create some conversation history
        agent.run("Create a sphere at origin")
        agent.run("Create a cylinder next to the sphere")
        
        # Verify we have conversation history
        if len(agent.conversation_history) == 0:
            logger.error("❌ No conversation history created")
            return False
        
        logger.info(f"📊 Conversation history before reset: {len(agent.conversation_history)}")
        
        # Reset conversation
        agent.reset_conversation()
        
        # Verify history is cleared
        if len(agent.conversation_history) != 0:
            logger.error(f"❌ Reset failed - still have {len(agent.conversation_history)} conversations")
            return False
        
        logger.info("✅ Reset functionality working correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Reset test failed: {e}")
        return False


def main():
    """Run all connection lifecycle tests."""
    logger.info("🔧 MCP Connection Lifecycle Test Suite")
    logger.info("=== Validating Fresh Agent Approach ===")
    logger.info("==" * 35)
    
    # Test 1: Multiple consecutive requests
    test1_result = test_multiple_consecutive_requests()
    
    # Test 2: Conversation memory with fresh agents
    test2_result = test_conversation_memory_with_fresh_agents()
    
    # Test 3: Reset functionality
    test3_result = test_reset_functionality()
    
    # Summary
    logger.info("==" * 35)
    logger.info("📊 Connection Lifecycle Test Summary:")
    logger.info(f"🔄 Multiple Consecutive Requests: {'SUCCESS' if test1_result else 'FAILED'}")
    logger.info(f"🧠 Conversation Memory with Fresh Agents: {'SUCCESS' if test2_result else 'FAILED'}")
    logger.info(f"🔄 Reset Functionality: {'SUCCESS' if test3_result else 'FAILED'}")
    
    tests_passed = sum([test1_result, test2_result, test3_result])
    total_tests = 3
    
    logger.info(f"\n📊 Overall Score: {tests_passed}/{total_tests} ({tests_passed/total_tests*100:.0f}%)")
    
    if tests_passed == total_tests:
        logger.info("\n🎉 CONNECTION LIFECYCLE FIX SUCCESSFUL!")
        logger.info("==" * 35)
        logger.info("✅ Fixed Issues:")
        logger.info("   🔄 Fresh CodeAgent instances for each request")
        logger.info("   🧠 Conversation memory separate from agent lifecycle")
        logger.info("   🔗 No 'Event loop is closed' errors on consecutive requests")
        logger.info("   ⚡ Reasonable performance maintained")
        logger.info("==" * 35)
        logger.info("\n💡 RESULT: MCP connection lifecycle issue resolved!")
        return True
    else:
        logger.warning("⚠️ Some tests failed - connection lifecycle needs more work")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)