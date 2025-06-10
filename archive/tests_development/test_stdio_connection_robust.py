#!/usr/bin/env python3
"""
Robust STDIO Connection Test with Retry Logic

This script tests STDIO connections with comprehensive retry logic and fallback strategies.

Run: python test_stdio_connection_robust.py
"""

import sys
import os
import time
import logging
from typing import List, Dict, Any, Optional
from mcp import StdioServerParameters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StdioConnectionTester:
    """Robust STDIO connection tester with multiple strategies."""
    
    def __init__(self):
        self.connection_strategies = [
            {
                "name": "UV Module Execution (Fixed)",
                "command": "uv",
                "args": ["run", "python", "-m", "grasshopper_mcp.bridge"],
                "env": os.environ.copy(),
                "timeout": 45,
                "retries": 3
            },
            {
                "name": "Direct Module Execution",
                "command": "python",
                "args": ["-m", "grasshopper_mcp.bridge"],
                "env": os.environ.copy(),
                "timeout": 45,
                "retries": 3
            },
            {
                "name": "UV Direct File",
                "command": "uv",
                "args": ["run", "python", "reference/grasshopper_mcp/bridge.py"],
                "env": os.environ.copy(),
                "timeout": 45,
                "retries": 2
            },
            {
                "name": "Direct File Execution",
                "command": "python",
                "args": ["reference/grasshopper_mcp/bridge.py"],
                "env": os.environ.copy(),
                "timeout": 45,
                "retries": 2
            },
            {
                "name": "Clean Environment UV",
                "command": "uv",
                "args": ["run", "python", "-m", "grasshopper_mcp.bridge"],
                "env": self._get_clean_env(),
                "timeout": 60,
                "retries": 2
            }
        ]
    
    def _get_clean_env(self) -> Dict[str, str]:
        """Get clean environment with minimal variables."""
        return {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")
        }
    
    def test_connection_with_retry(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection with exponential backoff retry."""
        name = strategy["name"]
        max_retries = strategy["retries"]
        base_delay = 2
        
        logger.info(f"Testing strategy: {name}")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"  Attempt {attempt + 1}/{max_retries}")
                
                # Create server parameters
                server_params = StdioServerParameters(
                    command=strategy["command"],
                    args=strategy["args"],
                    env=strategy["env"]
                )
                
                # Test connection
                result = self._test_single_connection(server_params, strategy["timeout"])
                
                if result["success"]:
                    logger.info(f"  ✅ Success on attempt {attempt + 1}")
                    return {
                        "strategy": name,
                        "success": True,
                        "attempt": attempt + 1,
                        "tools_count": result["tools_count"],
                        "tool_names": result["tool_names"],
                        "error": None
                    }
                else:
                    logger.warning(f"  ❌ Failed attempt {attempt + 1}: {result['error']}")
                    
                    # Exponential backoff
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.info(f"  Waiting {delay}s before retry...")
                        time.sleep(delay)
                        
            except Exception as e:
                logger.error(f"  ❌ Exception on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        
        return {
            "strategy": name,
            "success": False,
            "attempt": max_retries,
            "tools_count": 0,
            "tool_names": [],
            "error": "All retry attempts failed"
        }
    
    def _test_single_connection(self, server_params: StdioServerParameters, timeout: int) -> Dict[str, Any]:
        """Test a single STDIO connection."""
        try:
            from smolagents import ToolCollection
            
            logger.debug(f"Starting connection with timeout {timeout}s...")
            
            with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
                tools = list(tool_collection.tools)
                tool_names = [tool.name for tool in tools]
                
                return {
                    "success": True,
                    "tools_count": len(tools),
                    "tool_names": tool_names[:10],  # First 10 tools
                    "error": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "tools_count": 0,
                "tool_names": [],
                "error": str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive connection test with all strategies."""
        logger.info("=" * 60)
        logger.info("Robust STDIO Connection Test")
        logger.info("=" * 60)
        
        results = []
        successful_strategies = []
        
        for strategy in self.connection_strategies:
            result = self.test_connection_with_retry(strategy)
            results.append(result)
            
            if result["success"]:
                successful_strategies.append(result)
                logger.info(f"✅ {result['strategy']}: {result['tools_count']} tools loaded")
            else:
                logger.error(f"❌ {result['strategy']}: {result['error']}")
            
            logger.info("")  # Empty line for readability
        
        # Summary
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        if successful_strategies:
            logger.info(f"🎉 {len(successful_strategies)} successful connection(s) found!")
            
            # Show best strategy
            best = successful_strategies[0]
            logger.info(f"\nRecommended Strategy: {best['strategy']}")
            logger.info(f"  Tools loaded: {best['tools_count']}")
            logger.info(f"  Attempts needed: {best['attempt']}")
            logger.info(f"  Sample tools: {best['tool_names']}")
            
            # Show all successful strategies
            if len(successful_strategies) > 1:
                logger.info(f"\nAll successful strategies:")
                for i, strategy in enumerate(successful_strategies):
                    logger.info(f"  {i+1}. {strategy['strategy']} ({strategy['tools_count']} tools)")
        else:
            logger.error("❌ No successful connections found.")
            logger.info("\nTroubleshooting suggestions:")
            logger.info("1. Check package installation: uv sync")
            logger.info("2. Verify grasshopper-mcp is installed: python -c 'import grasshopper_mcp'")
            logger.info("3. Run diagnostic test: python test_stdio_diagnostic.py")
            logger.info("4. Check for port conflicts or firewall issues")
        
        return {
            "total_strategies": len(self.connection_strategies),
            "successful_strategies": len(successful_strategies),
            "results": results,
            "best_strategy": successful_strategies[0] if successful_strategies else None
        }

def test_geometry_agent_integration(tools_count: int, strategy_name: str) -> bool:
    """Test integration with geometry agent."""
    if tools_count == 0:
        return False
        
    try:
        logger.info(f"\nTesting geometry agent integration with {strategy_name}...")
        
        from src.bridge_design_system.mcp.mcp_tools_utils import get_grasshopper_tools
        
        # Test loading tools via our utility
        tools = get_grasshopper_tools(use_stdio=True)
        
        if tools:
            logger.info(f"✅ Geometry agent integration successful: {len(tools)} tools")
            return True
        else:
            logger.warning("❌ Geometry agent integration failed: No tools loaded")
            return False
            
    except Exception as e:
        logger.error(f"❌ Geometry agent integration failed: {e}")
        return False

def main():
    """Run the robust connection test."""
    tester = StdioConnectionTester()
    summary = tester.run_comprehensive_test()
    
    # Test geometry agent integration if we have a working connection
    if summary["best_strategy"]:
        best = summary["best_strategy"]
        integration_success = test_geometry_agent_integration(
            best["tools_count"], 
            best["strategy"]
        )
        
        if integration_success:
            logger.info("\n🎉 Full integration test successful!")
            logger.info("You can now use the geometry agent with MCP tools.")
        else:
            logger.warning("\n⚠️ STDIO connection works but geometry agent integration failed.")
            logger.info("Check mcp_tools_utils.py configuration.")
    
    # Final recommendations
    logger.info("\n" + "=" * 60)
    logger.info("NEXT STEPS")
    logger.info("=" * 60)
    
    if summary["best_strategy"]:
        best = summary["best_strategy"]
        logger.info("Update your configuration to use the working strategy:")
        logger.info(f"  Strategy: {best['strategy']}")
        logger.info(f"  Tools available: {best['tools_count']}")
        logger.info("\nRun the full integration test:")
        logger.info("  python test_mcp_integration_final.py")
    else:
        logger.info("Run additional diagnostics:")
        logger.info("  python test_stdio_diagnostic.py")
        logger.info("\nCheck package installation:")
        logger.info("  uv sync")
        logger.info("  python -c 'import grasshopper_mcp; print(grasshopper_mcp.__version__)'")

if __name__ == "__main__":
    main()