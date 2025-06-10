#!/usr/bin/env python3
"""
STDIO Connection Diagnostic Test

This script performs detailed diagnostics of the STDIO connection between 
smolagents and grasshopper_mcp.bridge to identify the exact point of failure.

Run: python test_stdio_diagnostic.py
"""

import sys
import os
import logging
import subprocess
import time
from typing import List, Optional
from mcp import StdioServerParameters

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stdio_diagnostic.log')
    ]
)

logger = logging.getLogger(__name__)

def test_server_startup(command: List[str], description: str) -> bool:
    """Test if the server starts successfully."""
    logger.info(f"Testing server startup: {description}")
    logger.info(f"Command: {' '.join(command)}")
    
    try:
        # Start the process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )
        
        # Give it time to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info(f"✅ Server started successfully: {description}")
            
            # Try to read initial output
            try:
                stdout, stderr = process.communicate(timeout=2)
                if stderr:
                    logger.info(f"Server stderr output: {stderr}")
                if stdout:
                    logger.info(f"Server stdout output: {stdout}")
            except subprocess.TimeoutExpired:
                logger.info("Server is running (no immediate output)")
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ Server exited immediately: {description}")
            logger.error(f"Exit code: {process.returncode}")
            logger.error(f"Stdout: {stdout}")
            logger.error(f"Stderr: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to start server: {description}")
        logger.error(f"Error: {e}")
        return False

def test_smolagents_connection(server_params: StdioServerParameters, description: str) -> bool:
    """Test smolagents STDIO connection."""
    logger.info(f"Testing smolagents connection: {description}")
    
    try:
        from smolagents import ToolCollection
        
        # Increase logging for MCP and smolagents
        logging.getLogger('mcp').setLevel(logging.DEBUG)
        logging.getLogger('smolagents').setLevel(logging.DEBUG)
        
        logger.info("Attempting ToolCollection.from_mcp() connection...")
        
        with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
            tools = list(tool_collection.tools)
            logger.info(f"✅ Connection successful: {description}")
            logger.info(f"Loaded {len(tools)} tools")
            tool_names = [tool.name for tool in tools[:10]]  # Show first 10
            logger.info(f"Sample tools: {tool_names}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Connection failed: {description}")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run comprehensive STDIO diagnostics."""
    logger.info("=" * 60)
    logger.info("STDIO Connection Diagnostic Test")
    logger.info("=" * 60)
    
    # Test different server startup methods
    server_tests = [
        {
            "command": ["python", "-m", "grasshopper_mcp.bridge"],
            "description": "Python module execution"
        },
        {
            "command": ["uv", "run", "python", "-m", "grasshopper_mcp.bridge"],
            "description": "UV module execution"
        },
        {
            "command": ["python", "reference/grasshopper_mcp/bridge.py"],
            "description": "Direct file execution"
        },
        {
            "command": ["uv", "run", "python", "reference/grasshopper_mcp/bridge.py"],
            "description": "UV direct file execution"
        }
    ]
    
    startup_results = []
    
    logger.info("\n1. Testing Server Startup Methods")
    logger.info("-" * 40)
    
    for test in server_tests:
        result = test_server_startup(test["command"], test["description"])
        startup_results.append({
            "test": test,
            "success": result
        })
    
    # Test smolagents connections for successful startup methods
    logger.info("\n2. Testing Smolagents STDIO Connections")
    logger.info("-" * 40)
    
    connection_results = []
    
    for result in startup_results:
        if result["success"]:
            test = result["test"]
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=test["command"][0],
                args=test["command"][1:],
                env=os.environ.copy()
            )
            
            success = test_smolagents_connection(server_params, test["description"])
            connection_results.append({
                "test": test,
                "success": success
            })
    
    # Test environment variations
    logger.info("\n3. Testing Environment Variations")
    logger.info("-" * 40)
    
    # Test with minimal environment
    minimal_env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", "")
    }
    
    # Test the most promising method with clean environment
    if connection_results:
        best_test = connection_results[0]["test"]
        server_params_clean = StdioServerParameters(
            command=best_test["command"][0],
            args=best_test["command"][1:],
            env=minimal_env
        )
        
        clean_success = test_smolagents_connection(
            server_params_clean, 
            f"{best_test['description']} (clean env)"
        )
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)
    
    logger.info("\nServer Startup Results:")
    for i, result in enumerate(startup_results):
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        logger.info(f"{i+1}. {result['test']['description']}: {status}")
    
    logger.info("\nSmolagents Connection Results:")
    for i, result in enumerate(connection_results):
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        logger.info(f"{i+1}. {result['test']['description']}: {status}")
    
    # Recommendations
    successful_connections = [r for r in connection_results if r["success"]]
    
    if successful_connections:
        logger.info(f"\n🎉 Found {len(successful_connections)} working connection(s)!")
        logger.info("Recommended approach:")
        best = successful_connections[0]
        logger.info(f"  Command: {' '.join(best['test']['command'])}")
        logger.info(f"  Description: {best['test']['description']}")
    else:
        logger.info("\n❌ No working connections found.")
        logger.info("Check the detailed logs above for specific error messages.")
        
        # Show which startup methods worked
        successful_startups = [r for r in startup_results if r["success"]]
        if successful_startups:
            logger.info(f"\nServer startup works for {len(successful_startups)} method(s):")
            for startup in successful_startups:
                logger.info(f"  - {startup['test']['description']}")
            logger.info("\nThe issue is in the STDIO communication, not server startup.")
        else:
            logger.info("\nNo server startup methods worked.")
            logger.info("Check package installation: uv sync")
    
    logger.info(f"\nDetailed logs saved to: stdio_diagnostic.log")

if __name__ == "__main__":
    main()