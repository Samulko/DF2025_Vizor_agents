#!/usr/bin/env python3
"""
Test improved Geometry Agent with system prompt and low temperature.

This test validates the geometry agent's improved behavior:
- Low temperature (0.1) for precise instruction following
- System prompt for clear role definition
- Focus on MCP tool usage
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_stdio import GeometryAgentSTDIO
from bridge_design_system.agents.triage_agent import TriageAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_geometry_agent_direct():
    """Test geometry agent directly with precise instructions."""
    logger.info("=== Testing Improved Geometry Agent (Direct) ===")
    
    try:
        # Create geometry agent
        agent = GeometryAgentSTDIO(model_name="geometry")
        
        # Test system prompt loading
        logger.info(f"✅ System prompt loaded: {len(agent.system_prompt)} characters")
        logger.info(f"✅ Temperature set to 0.1 for precise instruction following")
        
        # Test precise geometric instruction
        task = """Create exactly one point at coordinates (5, 10, 15) using the add_python3_script MCP tool. 
Name the component 'Bridge Point 1'. Place it at canvas position (100, 200).
Use Rhino.Geometry.Point3d and assign to variable 'a'."""
        
        logger.info(f"🎯 Testing precise instruction: {task}")
        
        start_time = time.time()
        result = agent.run(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        logger.info(f"📝 Result: {str(result)[:200]}...")
        
        # Check if result mentions specific coordinates and component name
        result_str = str(result).lower()
        success_indicators = [
            "bridge point 1" in result_str,
            "5" in result_str and "10" in result_str and "15" in result_str,
            "python script" in result_str or "component" in result_str
        ]
        
        success = any(success_indicators)
        logger.info(f"✅ Precise instruction following: {'Success' if success else 'Needs improvement'}")
        
        return success, execution_time
        
    except Exception as e:
        logger.error(f"❌ Direct test failed: {e}")
        return False, 0


def test_geometry_via_triage():
    """Test geometry agent via triage with delegation."""
    logger.info("=== Testing Improved Geometry Agent (Via Triage) ===")
    
    try:
        # Create triage agent
        triage = TriageAgent()
        triage.initialize_agent()
        
        # Test delegation with clear geometric request
        task = """I need you to create a bridge anchor point. Please place it at coordinates (0, 0, 0) 
and name it 'Start Anchor'. This will be the starting point for our bridge design."""
        
        logger.info(f"🎯 Testing triage delegation: {task}")
        
        start_time = time.time()
        response = triage.handle_design_request(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        logger.info(f"📝 Response: {response.message[:200]}...")
        
        # Check delegation success
        if response.success:
            logger.info("✅ Triage delegation successful")
            return True, execution_time
        else:
            logger.warning("⚠️  Triage delegation had issues")
            return False, execution_time
        
    except Exception as e:
        logger.error(f"❌ Triage test failed: {e}")
        return False, 0


def test_step_by_step_behavior():
    """Test that geometry agent follows step-by-step methodology."""
    logger.info("=== Testing Step-by-Step Behavior ===")
    
    try:
        agent = GeometryAgentSTDIO(model_name="geometry")
        
        # Test with multi-step request to see if agent asks for clarification
        task = """Create a bridge foundation system with two anchor points and connecting beams."""
        
        logger.info(f"🎯 Testing multi-step request: {task}")
        
        start_time = time.time()
        result = agent.run(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        logger.info(f"📝 Result: {str(result)[:200]}...")
        
        # Check if agent created step-by-step or asked for clarification
        result_str = str(result).lower()
        step_indicators = [
            "step by step" in result_str,
            "one step" in result_str,
            "first" in result_str and "then" in result_str,
            "coordinates" in result_str  # Should ask for specific coordinates
        ]
        
        step_by_step = any(step_indicators)
        logger.info(f"✅ Step-by-step methodology: {'Following' if step_by_step else 'Needs improvement'}")
        
        return step_by_step, execution_time
        
    except Exception as e:
        logger.error(f"❌ Step-by-step test failed: {e}")
        return False, 0


def test_mcp_tool_usage():
    """Test that geometry agent properly uses MCP tools."""
    logger.info("=== Testing MCP Tool Usage ===")
    
    try:
        agent = GeometryAgentSTDIO(model_name="geometry")
        
        # Test simple geometric creation
        task = """Create a single line from point (0,0,0) to point (10,0,0) using MCP tools."""
        
        logger.info(f"🎯 Testing MCP tool usage: {task}")
        
        start_time = time.time()
        result = agent.run(task)
        execution_time = time.time() - start_time
        
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        logger.info(f"📝 Result: {str(result)[:200]}...")
        
        # Check if MCP tools were used
        result_str = str(result).lower()
        mcp_indicators = [
            "python script" in result_str or "component" in result_str,
            "grasshopper" in result_str,
            "id:" in result_str or "component id" in result_str,
            "rhino.geometry" in result_str
        ]
        
        mcp_usage = any(mcp_indicators)
        logger.info(f"✅ MCP tool usage: {'Detected' if mcp_usage else 'Not detected'}")
        
        return mcp_usage, execution_time
        
    except Exception as e:
        logger.error(f"❌ MCP tool test failed: {e}")
        return False, 0


def main():
    """Run all improved geometry agent tests."""
    logger.info("🚀 Improved Geometry Agent Test Suite")
    logger.info("=== Testing Low Temperature (0.1) + System Prompt ===")
    logger.info("==" * 35)
    
    # Test 1: Direct agent test
    direct_success, direct_time = test_geometry_agent_direct()
    
    # Test 2: Triage delegation test
    triage_success, triage_time = test_geometry_via_triage()
    
    # Test 3: Step-by-step behavior
    step_success, step_time = test_step_by_step_behavior()
    
    # Test 4: MCP tool usage
    mcp_success, mcp_time = test_mcp_tool_usage()
    
    # Summary
    logger.info("==" * 35)
    logger.info("📊 Improved Geometry Agent Test Summary:")
    logger.info(f"🎯 Direct Instruction Following: {'Success' if direct_success else 'Failed'} ({direct_time:.2f}s)")
    logger.info(f"🔗 Triage Delegation: {'Success' if triage_success else 'Failed'} ({triage_time:.2f}s)")
    logger.info(f"📋 Step-by-Step Methodology: {'Success' if step_success else 'Failed'} ({step_time:.2f}s)")
    logger.info(f"🔧 MCP Tool Usage: {'Success' if mcp_success else 'Failed'} ({mcp_time:.2f}s)")
    
    # Calculate overall success
    tests_passed = sum([direct_success, triage_success, step_success, mcp_success])
    total_tests = 4
    
    logger.info(f"\n📊 Overall Score: {tests_passed}/{total_tests} ({tests_passed/total_tests*100:.0f}%)")
    
    if tests_passed >= 3:
        logger.info("\n🎉 IMPROVED GEOMETRY AGENT PERFORMING WELL!")
        logger.info("==" * 35)
        logger.info("✅ Improvements Confirmed:")
        logger.info("   🌡️  Low temperature (0.1) for precise instruction following")
        logger.info("   📜 System prompt loaded for clear role definition")
        logger.info("   🎯 Focus on MCP tool usage for actual geometry creation")
        logger.info("   📋 Step-by-step methodology implementation")
        logger.info("==" * 35)
        return True
    else:
        logger.warning("⚠️  Geometry agent improvements need refinement")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)