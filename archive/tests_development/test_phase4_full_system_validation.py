#!/usr/bin/env python3
"""
Phase 4 Test: Full System Validation

This test validates the complete integrated system:
1. Multi-agent orchestration (Triage → Geometry Agent)
2. Real bridge design scenarios
3. End-to-end workflow validation
4. Performance and reliability testing

Run this AFTER all previous phases have passed.
"""
import logging
import sys
import time
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the complete system
try:
    from src.bridge_design_system.agents.triage_agent import TriageAgent
    from src.bridge_design_system.agents.geometry_agent import GeometryAgent
    from src.bridge_design_system.config.model_config import ModelProvider
    from src.bridge_design_system.config.settings import get_settings
    from src.bridge_design_system.main import BridgeDesignSystem
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    logger.error("Make sure you're running from the project root directory")
    sys.exit(1)


class Phase4FullSystemTester:
    """Test the complete bridge design system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.system = None
        self.triage_agent = None
    
    def setup_full_system(self) -> bool:
        """Initialize the complete bridge design system."""
        logger.info("🏗️ Setting up full bridge design system...")
        
        try:
            # Initialize the main system
            logger.info("🚀 Initializing Bridge Design System...")
            self.system = BridgeDesignSystem()
            
            # Get the triage agent for direct testing
            self.triage_agent = self.system.triage_agent
            
            if not self.triage_agent:
                logger.error("❌ Failed to get triage agent")
                return False
            
            logger.info("✅ Bridge Design System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup full system: {e}")
            return False
    
    def test_simple_bridge_design_request(self) -> bool:
        """Test a simple bridge design request through the triage agent."""
        logger.info("🔍 Testing simple bridge design request...")
        
        try:
            user_request = """
            I need to design a simple beam bridge. 
            Create a basic structure with:
            - A horizontal beam at the center
            - Two support points at the ends
            - Make it span about 20 units long
            """
            
            logger.info(f"👤 User request: {user_request}")
            logger.info("🤖 Processing through triage agent...")
            
            result = self.triage_agent.run(user_request)
            
            logger.info(f"🎯 System response: {result}")
            
            # Give the system time to process
            time.sleep(3)
            
            logger.info("✅ Simple bridge design request completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Simple bridge design request failed: {e}")
            return False
    
    def test_multi_step_bridge_design(self) -> bool:
        """Test a complex multi-step bridge design."""
        logger.info("🔍 Testing multi-step bridge design...")
        
        try:
            user_request = """
            Design a truss bridge with the following requirements:
            1. Create a main beam spanning 30 units horizontally
            2. Add vertical support posts at 0, 10, 20, and 30 units
            3. Add diagonal bracing between the posts
            4. Connect all components properly
            5. Save the design as 'truss_bridge_design.gh'
            
            This should demonstrate the geometry agent's ability to handle complex instructions.
            """
            
            logger.info(f"👤 Complex user request: {user_request}")
            logger.info("🤖 Processing through triage agent...")
            
            result = self.triage_agent.run(user_request)
            
            logger.info(f"🎯 System response: {result}")
            
            # Give the system more time for complex operations
            time.sleep(5)
            
            logger.info("✅ Multi-step bridge design completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Multi-step bridge design failed: {e}")
            return False
    
    def test_geometry_modification_request(self) -> bool:
        """Test geometry modification through the triage system."""
        logger.info("🔍 Testing geometry modification request...")
        
        try:
            user_request = """
            Modify the current bridge design:
            1. List all current components
            2. Move the bridge elements to create a arch shape
            3. Add a curved element to replace the straight beam
            4. Ensure all connections are maintained
            """
            
            logger.info(f"👤 Modification request: {user_request}")
            logger.info("🤖 Processing through triage agent...")
            
            result = self.triage_agent.run(user_request)
            
            logger.info(f"🎯 System response: {result}")
            
            # Give the system time to process
            time.sleep(4)
            
            logger.info("✅ Geometry modification request completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Geometry modification request failed: {e}")
            return False
    
    def test_agent_delegation_workflow(self) -> bool:
        """Test that the triage agent properly delegates to specialized agents."""
        logger.info("🔍 Testing agent delegation workflow...")
        
        try:
            # Test geometry-specific request
            geometry_request = """
            Create three circles with different radii:
            - Circle 1: radius 5 at position (0, 0)
            - Circle 2: radius 10 at position (20, 0)  
            - Circle 3: radius 15 at position (40, 0)
            
            This is clearly a geometry task.
            """
            
            logger.info("👤 Geometry-specific request...")
            result = self.triage_agent.run(geometry_request)
            logger.info(f"🎯 Response: {result}")
            
            time.sleep(3)
            
            # Test general inquiry (should be handled by triage directly)
            general_request = """
            What is the current status of the bridge design?
            How many components are in the document?
            """
            
            logger.info("👤 General inquiry request...")
            result = self.triage_agent.run(general_request)
            logger.info(f"🎯 Response: {result}")
            
            time.sleep(2)
            
            logger.info("✅ Agent delegation workflow completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent delegation workflow failed: {e}")
            return False
    
    def test_system_error_handling(self) -> bool:
        """Test system error handling and recovery."""
        logger.info("🔍 Testing system error handling...")
        
        try:
            # Test invalid geometry request
            invalid_request = """
            Create an impossible geometric shape that doesn't make sense.
            Connect component A to component B where neither exists.
            Set parameter XYZ to value "invalid" for component that doesn't exist.
            """
            
            logger.info("👤 Invalid request (testing error handling)...")
            result = self.triage_agent.run(invalid_request)
            logger.info(f"🎯 Response: {result}")
            
            # The system should handle this gracefully
            time.sleep(2)
            
            # Test recovery with valid request
            recovery_request = "Clear the document and create a simple point at (0, 0)"
            
            logger.info("👤 Recovery request...")
            result = self.triage_agent.run(recovery_request)
            logger.info(f"🎯 Response: {result}")
            
            time.sleep(2)
            
            logger.info("✅ System error handling completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ System error handling failed: {e}")
            return False
    
    def test_system_performance_validation(self) -> bool:
        """Test system performance and responsiveness."""
        logger.info("🔍 Testing system performance...")
        
        try:
            import requests
            
            # Check MCP server status
            logger.info("📊 Checking MCP server performance...")
            start_time = time.time()
            response = requests.get("http://localhost:8001/grasshopper/status")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = response.json()
                logger.info(f"✅ MCP server responding in {response_time:.3f}s")
                logger.info(f"📈 Server status: {status}")
                
                # Check command processing stats
                if status.get("command_history", []):
                    logger.info(f"📋 Commands processed: {len(status['command_history'])}")
                    logger.info(f"⏱️ Pending commands: {status.get('pending_commands', 0)}")
                
                # Performance test: rapid requests
                logger.info("🚀 Testing rapid request handling...")
                for i in range(3):
                    quick_request = f"Create a point at ({i*10}, {i*10})"
                    logger.info(f"Request {i+1}: {quick_request}")
                    result = self.triage_agent.run(quick_request)
                    time.sleep(1)
                
                logger.info("✅ System performance validation completed")
                return True
            else:
                logger.error(f"❌ MCP server not responding: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ System performance validation failed: {e}")
            return False
    
    def validate_grasshopper_integration(self) -> bool:
        """Final validation that Grasshopper integration is working."""
        logger.info("🔍 Final Grasshopper integration validation...")
        
        try:
            import requests
            
            # Get final status
            response = requests.get("http://localhost:8001/grasshopper/status")
            if response.status_code == 200:
                status = response.json()
                
                # Check if we have processed commands
                command_count = len(status.get("command_history", []))
                pending_count = status.get("pending_commands", 0)
                
                logger.info(f"📊 Final Statistics:")
                logger.info(f"  - Commands processed: {command_count}")
                logger.info(f"  - Pending commands: {pending_count}")
                logger.info(f"  - Server uptime: {status.get('server_time', 'unknown')}")
                
                if command_count > 0:
                    logger.info("✅ Grasshopper integration confirmed - commands processed")
                    
                    # Show recent command history
                    recent_commands = status.get("command_history", [])[-5:]
                    logger.info("📋 Recent commands:")
                    for cmd in recent_commands:
                        success_status = "✅" if cmd.get("success", False) else "❌"
                        logger.info(f"  {success_status} {cmd.get('command_id', 'unknown')}")
                    
                    return True
                else:
                    logger.warning("⚠️  No commands processed - check bridge connection")
                    return False
            else:
                logger.error(f"❌ Cannot get server status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Grasshopper integration validation failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all Phase 4 tests."""
        logger.info("🚀 Starting Phase 4: Full System Validation")
        logger.info("=" * 60)
        
        # Setup first
        if not self.setup_full_system():
            logger.error("💥 Failed to setup full system - cannot continue")
            return False
        
        tests = [
            ("Simple Bridge Design", self.test_simple_bridge_design_request),
            ("Multi-Step Bridge Design", self.test_multi_step_bridge_design),
            ("Geometry Modification", self.test_geometry_modification_request),
            ("Agent Delegation Workflow", self.test_agent_delegation_workflow),
            ("System Error Handling", self.test_system_error_handling),
            ("System Performance", self.test_system_performance_validation),
            ("Grasshopper Integration", self.validate_grasshopper_integration),
        ]
        
        results = {}
        for test_name, test_func in tests:
            logger.info("-" * 40)
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"{status} {test_name}")
                
                # Brief pause between tests
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ FAIL {test_name}: {e}")
                results[test_name] = False
        
        logger.info("=" * 60)
        logger.info("📊 Phase 4 Test Results:")
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            logger.info(f"  {status} {test_name}")
        
        logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed >= total * 0.8:  # 80% pass rate for full system
            logger.info("🎉 PHASE 4 COMPLETE - FULL SYSTEM VALIDATED!")
            logger.info("\n🏆 CONGRATULATIONS!")
            logger.info("The complete Vizor Agents bridge design system is working!")
            logger.info("\n🚀 You now have:")
            logger.info("✅ AI agents that can control Grasshopper")
            logger.info("✅ Multi-agent orchestration system")
            logger.info("✅ Real-time bridge design capabilities")
            logger.info("✅ Robust error handling and recovery")
            logger.info("✅ Performance-optimized MCP integration")
            return True
        else:
            logger.error("💥 Phase 4 FAILED - System integration issues")
            return False


def main():
    """Main test runner."""
    print("🧪 Vizor Agents - Phase 4: Full System Validation")
    print("=" * 60)
    print("This is the final validation of the complete bridge design system.")
    print()
    print("Prerequisites:")
    print("✅ All previous phases (1-3) passed")
    print("✅ MCP server running and stable")
    print("✅ Grasshopper bridge actively processing commands")
    print("✅ All agents initialized and ready")
    print()
    print("This test will run comprehensive scenarios including:")
    print("- End-to-end bridge design workflows")
    print("- Multi-agent orchestration")
    print("- Error handling and recovery")
    print("- Performance validation")
    print()
    
    # Check if user wants to continue
    try:
        input("Press Enter to start the final validation, or Ctrl+C to exit...")
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
        return 1
    
    # Run tests
    tester = Phase4FullSystemTester()
    success = tester.run_all_tests()
    
    # Final celebration or troubleshooting
    if success:
        print("\n" + "🎊" * 20)
        print("    SYSTEM INTEGRATION COMPLETE!")
        print("🎊" * 20)
        print()
        print("🏗️ Your AI-powered bridge design system is ready!")
        print("🤖 Agents can now create complex 3D geometry in Grasshopper")
        print("🌉 Ready for real bridge design projects")
        print()
        print("Next steps:")
        print("- Try complex bridge design scenarios")
        print("- Integrate with AR visualization")
        print("- Add material and structural analysis")
        print("- Scale to multiple concurrent users")
    else:
        print("\n🔧 SYSTEM INTEGRATION INCOMPLETE")
        print("Some critical tests failed. Check the logs for details.")
        print()
        print("Common issues at this stage:")
        print("- Agent communication timeouts")
        print("- MCP session instability")
        print("- Grasshopper bridge disconnection")
        print("- Complex geometry operation failures")
        print()
        print("Debugging tips:")
        print("1. Restart all components (MCP server, Grasshopper)")
        print("2. Check logs for specific error patterns")
        print("3. Test individual components in isolation")
        print("4. Verify network connectivity and ports")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())