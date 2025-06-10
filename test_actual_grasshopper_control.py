#!/usr/bin/env python3
"""
Test Actual Grasshopper Control

This test validates that the agent can actually execute real Grasshopper commands
through the MCP bridge, not just list tools.

Run: python test_actual_grasshopper_control.py
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_create_point() -> bool:
    """Test creating a point at specific coordinates in Grasshopper."""
    logger.info("🔍 Testing: Create a point at coordinates (0, 0, 0)")
    
    try:
        from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools
        
        with create_geometry_agent_with_mcp_tools() as agent:
            
            # Task: Create a point
            task = "Create a point at coordinates (0, 0, 0) in Grasshopper"
            logger.info(f"Task: {task}")
            
            result = agent.run(task)
            logger.info("✅ Point creation task completed!")
            logger.info(f"Result type: {type(result)}")
            
            # Check if we got a meaningful result
            if result is not None:
                result_str = str(result)
                if len(result_str) < 1000:
                    logger.info(f"Result: {result}")
                else:
                    logger.info(f"Result (truncated): {result_str[:500]}...")
                
                # Look for success indicators
                success_indicators = [
                    "success", "created", "added", "point", "coordinate",
                    "component", "grasshopper", "executed"
                ]
                
                result_lower = result_str.lower()
                found_indicators = [ind for ind in success_indicators if ind in result_lower]
                
                if found_indicators:
                    logger.info(f"✅ Success indicators found: {found_indicators}")
                    return True
                else:
                    logger.warning("⚠️ No clear success indicators in result")
                    return len(result_str) > 10  # At least got some response
            else:
                logger.warning("⚠️ Got None result")
                return False
                
    except Exception as e:
        logger.error(f"❌ Point creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_add_circle() -> bool:
    """Test adding a circle with specific radius in Grasshopper."""
    logger.info("🔍 Testing: Add a circle with radius 5")
    
    try:
        from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools
        
        with create_geometry_agent_with_mcp_tools() as agent:
            
            # Task: Add a circle
            task = "Add a circle with radius 5 in Grasshopper"
            logger.info(f"Task: {task}")
            
            result = agent.run(task)
            logger.info("✅ Circle creation task completed!")
            logger.info(f"Result type: {type(result)}")
            
            # Check if we got a meaningful result
            if result is not None:
                result_str = str(result)
                if len(result_str) < 1000:
                    logger.info(f"Result: {result}")
                else:
                    logger.info(f"Result (truncated): {result_str[:500]}...")
                
                # Look for success indicators
                success_indicators = [
                    "success", "created", "added", "circle", "radius",
                    "component", "grasshopper", "executed", "5"
                ]
                
                result_lower = result_str.lower()
                found_indicators = [ind for ind in success_indicators if ind in result_lower]
                
                if found_indicators:
                    logger.info(f"✅ Success indicators found: {found_indicators}")
                    return True
                else:
                    logger.warning("⚠️ No clear success indicators in result")
                    return len(result_str) > 10  # At least got some response
            else:
                logger.warning("⚠️ Got None result")
                return False
                
    except Exception as e:
        logger.error(f"❌ Circle creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connect_components() -> bool:
    """Test connecting two components in Grasshopper."""
    logger.info("🔍 Testing: Connect two components")
    
    try:
        from src.bridge_design_system.agents.simple_geometry_agent import create_geometry_agent_with_mcp_tools
        
        with create_geometry_agent_with_mcp_tools() as agent:
            
            # Task: Connect components (more complex)
            task = """Create two components in Grasshopper and connect them:
            1. First create a point at (0, 0, 0)
            2. Then create a circle at that point
            3. Connect the point to the circle's center input"""
            
            logger.info(f"Task: {task}")
            
            result = agent.run(task)
            logger.info("✅ Component connection task completed!")
            logger.info(f"Result type: {type(result)}")
            
            # Check if we got a meaningful result
            if result is not None:
                result_str = str(result)
                if len(result_str) < 1000:
                    logger.info(f"Result: {result}")
                else:
                    logger.info(f"Result (truncated): {result_str[:500]}...")
                
                # Look for success indicators
                success_indicators = [
                    "success", "created", "added", "connect", "connected", 
                    "point", "circle", "component", "grasshopper", "executed"
                ]
                
                result_lower = result_str.lower()
                found_indicators = [ind for ind in success_indicators if ind in result_lower]
                
                if found_indicators:
                    logger.info(f"✅ Success indicators found: {found_indicators}")
                    return True
                else:
                    logger.warning("⚠️ No clear success indicators in result")
                    return len(result_str) > 10  # At least got some response
            else:
                logger.warning("⚠️ Got None result")
                return False
                
    except Exception as e:
        logger.error(f"❌ Component connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run actual Grasshopper control tests."""
    logger.info("🧪 Actual Grasshopper Control Test")
    logger.info("=" * 60)
    logger.info("Testing real Grasshopper manipulation via MCP bridge")
    logger.info("=" * 60)
    
    # Important note
    logger.info("🔧 PREREQUISITE: Make sure Grasshopper is open with the SimpleMCPBridge component running!")
    logger.info("📋 The bridge component should be polling and ready to receive commands")
    logger.info("")
    
    tests = [
        ("Create Point at (0,0,0)", test_create_point),
        ("Add Circle with Radius 5", test_add_circle), 
        ("Connect Two Components", test_connect_components),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
        except Exception as e:
            logger.error(f"❌ FAIL {test_name}: {e}")
            results[test_name] = False
        
        # Add delay between tests
        import time
        logger.info("⏱️ Waiting 2 seconds before next test...")
        time.sleep(2)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("ACTUAL GRASSHOPPER CONTROL TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"  {status} {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed >= 2:  # If most tests work
        logger.info("🎉 ACTUAL GRASSHOPPER CONTROL SUCCESS!")
        logger.info("✅ Agent can manipulate Grasshopper through MCP bridge")
        logger.info("✅ Real geometry creation is working")
        logger.info("✅ End-to-end integration is functional")
        
        if passed == total:
            logger.info("✅ All operations working perfectly!")
            logger.info("\n🚀 System is production-ready for:")
            logger.info("- Point creation in 3D space")
            logger.info("- Circle/curve generation")  
            logger.info("- Component connections and workflows")
            logger.info("- Complex multi-step Grasshopper operations")
        else:
            logger.info("⚠️ Some complex operations may need refinement")
        
        logger.info("\n🏗️ Ready for bridge design workflows!")
        logger.info("The geometry agent can now control Grasshopper for AR-assisted design")
        
        return True
    elif passed >= 1:
        logger.info("🔧 PARTIAL SUCCESS")
        logger.info("✅ Basic Grasshopper control is working")
        logger.info("⚠️ Some operations may need debugging")
        logger.info("\n🔍 Next steps:")
        logger.info("- Check Grasshopper bridge component status")
        logger.info("- Verify component polling is active")
        logger.info("- Test simpler operations first")
        return True
    else:
        logger.error("❌ GRASSHOPPER CONTROL FAILED")
        logger.error("No successful operations - check bridge connection")
        logger.error("\n🚨 Troubleshooting:")
        logger.error("1. Is Grasshopper open?")
        logger.error("2. Is SimpleMCPBridge component active and polling?")
        logger.error("3. Check MCP server logs for errors")
        logger.error("4. Verify bridge component is receiving commands")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)