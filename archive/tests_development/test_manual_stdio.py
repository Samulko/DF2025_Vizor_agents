#!/usr/bin/env python3
"""
Manual STDIO Test

Test direct communication with the MCP server to isolate the issue.
"""

import subprocess
import json
import sys
import time

def test_manual_stdio():
    """Test manual STDIO communication with the server."""
    print("Starting manual STDIO test...")
    
    # Start the server process
    process = subprocess.Popen(
        ["uv", "run", "python", "-m", "grasshopper_mcp.bridge"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0  # Unbuffered
    )
    
    try:
        print("Server started, sending initialization request...")
        
        # Send MCP initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send the request
        request_json = json.dumps(init_request) + "\n"
        print(f"Sending: {request_json.strip()}")
        
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Try to read response with timeout
        print("Waiting for response...")
        
        # Set a timeout for reading
        import select
        import os
        
        # For Windows, we need a different approach
        if os.name == 'nt':
            # Windows doesn't support select on pipes
            # Try reading with a short timeout
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print("✅ Server is still running after request")
                
                # Try to read stderr for any output
                try:
                    stderr_output = process.stderr.read(1000)
                    if stderr_output:
                        print(f"Server stderr: {stderr_output}")
                except:
                    pass
                
                print("❌ Cannot read stdout on Windows without blocking")
                print("This indicates a Windows STDIO communication issue")
                
                # Terminate the process
                process.terminate()
                return False
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Server exited with code: {process.returncode}")
                print(f"Stdout: {stdout}")
                print(f"Stderr: {stderr}")
                return False
        else:
            # Unix-like system
            ready, _, _ = select.select([process.stdout], [], [], 5)
            
            if ready:
                response = process.stdout.readline()
                print(f"✅ Received response: {response.strip()}")
                
                try:
                    response_data = json.loads(response)
                    print(f"✅ Valid JSON response received")
                    return True
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    return False
            else:
                print("❌ No response within 5 seconds")
                return False
                
    except Exception as e:
        print(f"❌ Error during communication: {e}")
        return False
        
    finally:
        # Clean up
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()

def test_process_creation():
    """Test if we can create the process correctly."""
    print("\nTesting process creation...")
    
    try:
        # Test if we can start and stop the process
        process = subprocess.Popen(
            ["uv", "run", "python", "-m", "grasshopper_mcp.bridge"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it time to start
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ Process created and running successfully")
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Process exited immediately: {process.returncode}")
            print(f"Stderr: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to create process: {e}")
        return False

def main():
    """Run manual STDIO tests."""
    print("=" * 50)
    print("Manual STDIO Communication Test")
    print("=" * 50)
    
    # Test 1: Process creation
    process_ok = test_process_creation()
    
    if not process_ok:
        print("\n❌ Cannot create server process")
        return
    
    # Test 2: STDIO communication
    stdio_ok = test_manual_stdio()
    
    print("\n" + "=" * 50)
    print("ANALYSIS")
    print("=" * 50)
    
    if stdio_ok:
        print("✅ Manual STDIO communication works")
        print("The issue is with smolagents' process management")
    else:
        print("❌ STDIO communication doesn't work")
        print("This is a Windows pipe communication issue")
        
        print("\nPossible solutions:")
        print("1. Use HTTP transport instead of STDIO")
        print("2. Create Windows-specific STDIO wrapper")
        print("3. Use Named Pipes on Windows")
    
    print(f"\nRunning on: {sys.platform}")
    print("This will help determine if it's Windows-specific")

if __name__ == "__main__":
    main()