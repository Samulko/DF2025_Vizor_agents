#!/usr/bin/env python3
"""
Quick test of HTTP vs STDIO for simple query commands.
"""

import logging
import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.geometry_agent_hybrid import GeometryAgentHybrid

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_simple_query_via_agent():
    """Test simple query command through the hybrid agent to see HTTP vs STDIO behavior."""
    logger.info("=== Testing Simple Query Commands via Hybrid Agent ===")
    
    # Create hybrid agent
    agent = GeometryAgentHybrid()
    
    # Test a simple query task
    query_task = "What components are currently on the Grasshopper canvas? Just tell me what's there."
    
    logger.info(f"🔍 Query task: {query_task}")
    
    start_time = time.time()
    result = agent.run(query_task)
    execution_time = time.time() - start_time
    
    logger.info(f"⏱️  Total execution time: {execution_time:.2f}s")
    logger.info(f"📝 Result: {str(result)[:200]}...")
    
    return result, execution_time


def test_simple_creation_via_agent():
    """Test simple creation command for comparison."""
    logger.info("=== Testing Simple Creation Command via Hybrid Agent ===")
    
    # Create hybrid agent
    agent = GeometryAgentHybrid()
    
    # Test a simple creation task
    creation_task = "Create a single point at coordinates (1, 2, 3)"
    
    logger.info(f"⚡ Creation task: {creation_task}")
    
    start_time = time.time()
    result = agent.run(creation_task)
    execution_time = time.time() - start_time
    
    logger.info(f"⏱️  Total execution time: {execution_time:.2f}s")
    logger.info(f"📝 Result: {str(result)[:200]}...")
    
    return result, execution_time


def main():
    """Compare query vs creation commands."""
    logger.info("🔍 HTTP Query vs Creation Command Test")
    logger.info("=" * 50)
    
    # Test 1: Simple Query
    try:
        query_result, query_time = test_simple_query_via_agent()
        query_success = True
    except Exception as e:
        logger.error(f"❌ Query test failed: {e}")
        query_success = False
        query_time = 0
    
    # Test 2: Simple Creation
    logger.info("\n" + "=" * 50)
    try:
        creation_result, creation_time = test_simple_creation_via_agent()
        creation_success = True
    except Exception as e:
        logger.error(f"❌ Creation test failed: {e}")
        creation_success = False
        creation_time = 0
    
    # Analysis
    logger.info("\n" + "=" * 50)
    logger.info("📊 COMPARISON ANALYSIS")
    logger.info("=" * 50)
    
    if query_success and creation_success:
        logger.info(f"🔍 Query Command: ✅ Success ({query_time:.2f}s)")
        logger.info(f"⚡ Creation Command: ✅ Success ({creation_time:.2f}s)")
        
        time_diff = abs(query_time - creation_time)
        if time_diff < 1.0:
            logger.info("📝 Both commands have similar execution times")
        elif query_time < creation_time:
            logger.info("📝 Query commands are faster than creation commands")
        else:
            logger.info("📝 Creation commands are faster than query commands")
            
    elif query_success:
        logger.info(f"🔍 Query Command: ✅ Success ({query_time:.2f}s)")
        logger.info(f"⚡ Creation Command: ❌ Failed")
        logger.info("📝 Queries work but creation fails")
        
    elif creation_success:
        logger.info(f"🔍 Query Command: ❌ Failed")
        logger.info(f"⚡ Creation Command: ✅ Success ({creation_time:.2f}s)")
        logger.info("📝 Creation works but queries fail")
        
    else:
        logger.info("🔍 Query Command: ❌ Failed")
        logger.info("⚡ Creation Command: ❌ Failed")
        logger.info("📝 Both types of commands failed")
    
    # Key insight
    logger.info("\n💡 KEY INSIGHT:")
    logger.info("   Both query and creation commands go through the SAME execution path")
    logger.info("   in our hybrid agent (STDIO for execution), so timing should be similar.")
    logger.info("   The HTTP optimization is only used for tool DISCOVERY, not execution.")


if __name__ == "__main__":
    main()