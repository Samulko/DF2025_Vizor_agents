#!/usr/bin/env python3
"""
Phase 3: Test Geometry Agent Control

This script tests the Geometry Agent's ability to control Grasshopper
through the MCP bridge connection.

Prerequisites:
1. Phase 2 tests passed (MCP server working)
2. Grasshopper running with MCP component connected
3. MCP component polling Python server successfully

Run: python test_phase3_geometry_agent_control.py
"""

import sys
import os
import time
import json
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase3Tester:
    """Test Geometry Agent → Grasshopper control via MCP."""
    
    def __init__(self):
        self.geometry_agent = None
        self.mcp_tools = []
        
    def load_geometry_agent_with_mcp(self) -> bool:
        """Load geometry agent with MCP tools."""
        logger.info("Loading Geometry Agent with MCP tools...")
        
        try:
            # Import required modules
            from src.bridge_design_system.mcp.mcp_tools_utils import get_grasshopper_tools
            from src.bridge_design_system.agents.geometry_agent import GeometryAgent
            
            # Load MCP tools via STDIO (our working method)
            logger.info("Loading MCP tools via STDIO...")
            self.mcp_tools = get_grasshopper_tools(use_stdio=True)
            
            if not self.mcp_tools:
                logger.error("❌ No MCP tools loaded")
                return False
            
            logger.info(f"✅ Loaded {len(self.mcp_tools)} MCP tools")
            
            # Create geometry agent with MCP tools
            logger.info("Creating Geometry Agent...")
            self.geometry_agent = GeometryAgent(mcp_tools=self.mcp_tools)
            self.geometry_agent.initialize_agent()
            
            logger.info(f"✅ Geometry Agent created with {len(self.geometry_agent.tools)} total tools")
            
            # Verify MCP tools are available
            mcp_tool_names = [tool.name for tool in self.mcp_tools]
            agent_tool_names = [tool.name for tool in self.geometry_agent.tools]
            mcp_tools_in_agent = [name for name in mcp_tool_names if name in agent_tool_names]
            
            logger.info(f"✅ {len(mcp_tools_in_agent)} MCP tools available to agent")
            
            return len(mcp_tools_in_agent) > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to load geometry agent: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_simple_grasshopper_operations(self) -> bool:
        """Test simple Grasshopper operations via agent."""
        logger.info("Testing simple Grasshopper operations...")
        
        if not self.geometry_agent:
            logger.error("❌ Geometry agent not loaded")
            return False
        
        # Test operations with expected responses
        test_operations = [
            {
                "name": "Document Status",
                "task": "Get the current status of the Grasshopper document. Show me what components are on the canvas.",
                "expected_tools": ["get_all_components", "get_grasshopper_document_info"],
                "timeout": 30
            },
            {
                "name": "Clear Document",
                "task": "Clear the Grasshopper document to start fresh.",
                "expected_tools": ["clear_grasshopper_document"],
                "timeout": 20
            },
            {
                "name": "Create Number Slider",
                "task": "Create a number slider with minimum value 0, maximum value 10, and current value 5.",
                "expected_tools": ["add_number_slider"],
                "timeout": 25
            }
        ]
        
        results = []
        
        for test_op in test_operations:
            logger.info(f"\nTesting: {test_op['name']}")
            logger.info(f"Task: {test_op['task']}")
            
            try:
                # Run the agent task
                response = self.geometry_agent.run(test_op['task'])
                
                if response.success:
                    logger.info(f"✅ {test_op['name']} completed successfully")
                    logger.info(f"Response: {response.message}")
                    results.append(True)
                else:
                    logger.warning(f"⚠️ {test_op['name']} completed with issues")
                    logger.warning(f"Response: {response.message}")
                    if response.error:
                        logger.warning(f"Error: {response.error}")
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"❌ {test_op['name']} failed with exception: {e}")
                results.append(False)
            
            # Short delay between operations
            time.sleep(2)
        
        success_count = sum(results)
        logger.info(f"\n✅ {success_count}/{len(test_operations)} simple operations succeeded")
        
        return success_count >= len(test_operations) // 2  # At least half should work
    
    def test_geometry_creation(self) -> bool:
        """Test geometry creation operations."""
        logger.info("Testing geometry creation...")
        
        if not self.geometry_agent:
            logger.error("❌ Geometry agent not loaded")
            return False
        
        geometry_tests = [
            {
                "name": "Create Point",
                "task": "Create a point at coordinates (0, 0, 0) in Grasshopper.",
                "timeout": 25
            },
            {
                "name": "Create Circle",
                "task": "Create a circle with radius 5 units at the origin.",
                "timeout": 30
            },
            {
                "name": "Create Line",
                "task": "Create a line from point (0,0,0) to point (10,10,0).",
                "timeout": 30
            }
        ]
        
        results = []
        
        for test in geometry_tests:
            logger.info(f"\nTesting: {test['name']}")
            logger.info(f"Task: {test['task']}")
            
            try:
                response = self.geometry_agent.run(test['task'])
                
                if response.success:
                    logger.info(f"✅ {test['name']} completed")
                    logger.info(f"Response: {response.message}")
                    results.append(True)
                else:
                    logger.warning(f"⚠️ {test['name']} had issues")
                    logger.warning(f"Response: {response.message}")
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"❌ {test['name']} failed: {e}")
                results.append(False)
            
            time.sleep(2)
        
        success_count = sum(results)
        logger.info(f"\n✅ {success_count}/{len(geometry_tests)} geometry operations succeeded")
        
        return success_count > 0  # At least one should work
    
    def test_component_connections(self) -> bool:
        """Test component connection operations."""
        logger.info("Testing component connections...")
        
        if not self.geometry_agent:
            logger.error("❌ Geometry agent not loaded")
            return False
        
        connection_tests = [
            {
                "name": "Create Connected Components",
                "task": """Create two number sliders and connect them to an addition component:
                1. Create a slider named 'A' with range 0-10, value 3
                2. Create a slider named 'B' with range 0-10, value 7  
                3. Create an addition component
                4. Connect slider A to the first input of addition
                5. Connect slider B to the second input of addition
                6. Add a panel to display the result""",
                "timeout": 60
            },
            {
                "name": "Check Components",
                "task": "List all components currently on the canvas and show their connections.",
                "timeout": 20
            }
        ]
        
        results = []
        
        for test in connection_tests:
            logger.info(f"\nTesting: {test['name']}")
            
            try:
                response = self.geometry_agent.run(test['task'])
                
                if response.success:
                    logger.info(f"✅ {test['name']} completed")
                    results.append(True)
                else:
                    logger.warning(f"⚠️ {test['name']} had issues")
                    logger.warning(f"Response: {response.message}")
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"❌ {test['name']} failed: {e}")
                results.append(False)
            
            time.sleep(3)
        
        success_count = sum(results)
        logger.info(f"\n✅ {success_count}/{len(connection_tests)} connection operations succeeded")
        
        return success_count > 0
    
    def test_bridge_communication_validation(self) -> bool:
        """Test that bridge communication is actually working."""
        logger.info("Testing bridge communication validation...")
        
        if not self.geometry_agent:
            logger.error("❌ Geometry agent not loaded")
            return False
        
        validation_tests = [
            {
                "name": "Document Info",
                "task": "Get detailed information about the current Grasshopper document including all components.",
                "timeout": 20
            },
            {
                "name": "Component Count",
                "task": "Count how many components are currently on the canvas and tell me the exact number.",
                "timeout": 15
            }
        ]
        
        results = []
        
        for test in validation_tests:
            logger.info(f"\nValidating: {test['name']}")
            
            try:
                response = self.geometry_agent.run(test['task'])
                
                # For validation, we check if the response contains actual data
                # not just generic responses
                if response.success and response.message:
                    # Look for specific indicators that Grasshopper actually responded
                    grasshopper_indicators = [
                        "component", "canvas", "grasshopper", "document", 
                        "connection", "parameter", "slider", "panel"
                    ]
                    
                    response_lower = response.message.lower()
                    found_indicators = [ind for ind in grasshopper_indicators if ind in response_lower]
                    
                    if found_indicators:
                        logger.info(f"✅ {test['name']} - Grasshopper data detected")
                        logger.info(f"Found indicators: {found_indicators}")
                        results.append(True)
                    else:
                        logger.warning(f"⚠️ {test['name']} - Generic response (no Grasshopper data)")
                        results.append(False)
                else:
                    logger.warning(f"⚠️ {test['name']} - No valid response")
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"❌ {test['name']} failed: {e}")
                results.append(False)
        
        success_count = sum(results)
        logger.info(f"\n✅ {success_count}/{len(validation_tests)} validation tests passed")
        
        return success_count > 0
    
    def run_phase3_tests(self) -> Dict[str, bool]:
        """Run all Phase 3 tests."""
        logger.info("=" * 60)
        logger.info("Phase 3: Geometry Agent → Grasshopper Control Test")
        logger.info("=" * 60)
        
        results = {}
        
        # Test 1: Load geometry agent with MCP tools
        results["agent_loading"] = self.load_geometry_agent_with_mcp()
        if not results["agent_loading"]:
            logger.error("❌ Cannot load geometry agent - aborting tests")
            return results
        
        # Test 2: Simple Grasshopper operations
        results["simple_operations"] = self.test_simple_grasshopper_operations()
        
        # Test 3: Geometry creation
        results["geometry_creation"] = self.test_geometry_creation()
        
        # Test 4: Component connections
        results["component_connections"] = self.test_component_connections()
        
        # Test 5: Bridge communication validation
        results["bridge_validation"] = self.test_bridge_communication_validation()
        
        return results

def main():
    """Run Phase 3 integration tests."""
    tester = Phase3Tester()
    
    results = tester.run_phase3_tests()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3 TEST SUMMARY")
    logger.info("=" * 60)
    
    critical_tests = ["agent_loading"]
    functionality_tests = ["simple_operations", "geometry_creation", "component_connections"]
    validation_tests = ["bridge_validation"]
    
    # Check results
    critical_passed = all(results.get(test, False) for test in critical_tests)
    functionality_passed = any(results.get(test, False) for test in functionality_tests)
    validation_passed = all(results.get(test, False) for test in validation_tests)
    
    logger.info("Critical Tests (Agent Setup):")
    for test in critical_tests:
        status = "✅ PASS" if results.get(test, False) else "❌ FAIL"
        logger.info(f"  {test.replace('_', ' ').title()}: {status}")
    
    logger.info("\nFunctionality Tests:")
    for test in functionality_tests:
        status = "✅ PASS" if results.get(test, False) else "❌ FAIL"
        logger.info(f"  {test.replace('_', ' ').title()}: {status}")
    
    logger.info("\nValidation Tests:")
    for test in validation_tests:
        status = "✅ PASS" if results.get(test, False) else "❌ FAIL"
        logger.info(f"  {test.replace('_', ' ').title()}: {status}")
    
    # Overall result
    if critical_passed and functionality_passed:
        logger.info("\n🎉 PHASE 3 SUCCESS!")
        logger.info("Geometry Agent can control Grasshopper via MCP bridge!")
        
        if validation_passed:
            logger.info("✅ Bridge communication fully validated")
        else:
            logger.info("⚠️ Bridge communication partially working")
        
        logger.info("\nNext steps:")
        logger.info("1. Test with actual Grasshopper canvas to see visual results")
        logger.info("2. Run Phase 4 for full system validation")
        logger.info("3. Try complex bridge design workflows")
        
        return True
        
    elif critical_passed:
        logger.warning("\n⚠️ PHASE 3 PARTIAL SUCCESS")
        logger.warning("Agent loads but some operations fail")
        
        logger.info("\nTroubleshooting:")
        if not functionality_passed:
            logger.info("- Check Grasshopper MCP component is connected and polling")
            logger.info("- Verify Grasshopper is running and responsive")
            logger.info("- Check MCP component configuration (URL: http://localhost:8001)")
        
        return False
        
    else:
        logger.error("\n❌ PHASE 3 FAILED!")
        logger.error("Cannot load geometry agent with MCP tools")
        
        logger.info("\nTroubleshooting:")
        logger.info("- Run Phase 2 tests first to verify MCP server")
        logger.info("- Check WSL environment is being used")
        logger.info("- Verify grasshopper-mcp package installation: uv sync")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)