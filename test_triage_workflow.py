#!/usr/bin/env python3
"""
Test Triage Agent Workflow with HTTP MCP Integration.

This test validates the complete workflow from triage agent through geometry delegation.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent import TriageAgent
from bridge_design_system.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_triage_initialization():
    """Test triage agent initialization."""
    logger.info("=== Testing Triage Agent Initialization ===")
    
    # Configure HTTP mode
    settings.mcp_transport_mode = "http"
    settings.mcp_http_url = "http://localhost:8001/mcp"
    
    try:
        # Create and initialize triage agent
        triage = TriageAgent()
        triage.initialize_agent()
        
        logger.info("✅ Triage agent initialized")
        
        # Check agent status
        status = triage.get_agent_status()
        logger.info(f"📊 Agent Status: {status}")
        
        return triage
        
    except Exception as e:
        logger.error(f"❌ Triage initialization failed: {e}")
        return None


def test_geometry_delegation(triage):
    """Test geometry task delegation through triage agent."""
    logger.info("=== Testing Geometry Task Delegation ===")
    
    try:
        # Simple geometry task
        task = "Create a point at coordinates (10, 20, 30)"
        
        logger.info(f"🎯 Delegating task: {task}")
        response = triage.handle_design_request(task)
        
        logger.info(f"📝 Response success: {response.success}")
        logger.info(f"📝 Response message: {response.message[:100]}...")
        
        if response.success:
            logger.info("✅ Geometry delegation successful")
            return True
        else:
            logger.warning("⚠️  Geometry delegation had issues")
            return False
        
    except Exception as e:
        logger.error(f"❌ Geometry delegation failed: {e}")
        return False


def test_bridge_design_request(triage):
    """Test a bridge design request through triage."""
    logger.info("=== Testing Bridge Design Request ===")
    
    try:
        # Bridge design task
        task = "Create a simple bridge foundation with two anchor points 15 meters apart"
        
        logger.info(f"🌉 Bridge task: {task}")
        response = triage.handle_design_request(task)
        
        logger.info(f"📝 Bridge response success: {response.success}")
        logger.info(f"📝 Bridge response: {response.message[:150]}...")
        
        if response.success:
            logger.info("✅ Bridge design request successful")
            return True
        else:
            logger.warning("⚠️  Bridge design request had issues")
            return False
        
    except Exception as e:
        logger.error(f"❌ Bridge design request failed: {e}")
        return False


def main():
    """Run triage workflow tests."""
    logger.info("🚀 Triage Workflow Test")
    logger.info("=" * 50)
    
    # Test 1: Triage Initialization
    triage = test_triage_initialization()
    if not triage:
        logger.error("❌ Cannot continue without triage agent")
        return False
    
    # Test 2: Simple Geometry Delegation
    geometry_success = test_geometry_delegation(triage)
    
    # Test 3: Bridge Design Request
    bridge_success = test_bridge_design_request(triage)
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Triage Workflow Summary:")
    logger.info(f"✅ Triage Setup: Success")
    logger.info(f"🎯 Geometry Delegation: {'Success' if geometry_success else 'Failed'}")
    logger.info(f"🌉 Bridge Design: {'Success' if bridge_success else 'Failed'}")
    
    overall_success = geometry_success or bridge_success
    
    if overall_success:
        logger.info("🎉 Triage workflow is working!")
        return True
    else:
        logger.warning("⚠️  Triage workflow needs attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)