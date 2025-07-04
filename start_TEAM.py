#!/usr/bin/env python3
"""
TEAM Launcher - Start the complete bridge design system.
Starts Phoenix tracing, LCARS monitoring, and the interactive main system.
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def run_command_in_background(cmd, name):
    """Run a command in the background and return the process."""
    print(f"🚀 Starting {name}...")
    try:
        # Start process with environment variables
        env = os.environ.copy()
        if name == "Main System":
            env["OTEL_BACKEND"] = "phoenix"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        print(f"✅ {name} started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    raise KeyboardInterrupt()

def main():
    """Main launcher function."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🌉 Bridge Design System - TEAM Launch")
    print("=" * 60)
    
    processes = []
    
    try:
        # 1. Start Phoenix server
        phoenix_process = run_command_in_background(
            "uv run python -m phoenix.server.main serve",
            "Phoenix Server"
        )
        if phoenix_process:
            processes.append(("Phoenix", phoenix_process))
            time.sleep(3)  # Wait for Phoenix to start
        
        # 2. Start LCARS monitoring server
        lcars_process = run_command_in_background(
            "uv run python -m bridge_design_system.monitoring.lcars_interface",
            "LCARS Monitoring"
        )
        if lcars_process:
            processes.append(("LCARS", lcars_process))
            time.sleep(2)  # Wait for LCARS to start
        
        print("\n" + "=" * 60)
        print("🎯 Background services started successfully!")
        print("=" * 60)
        print("📊 Phoenix UI:     http://localhost:6006")
        print("🖥️  LCARS Monitor:  http://localhost:5000")
        print("📡 TCP Command:    localhost:8082")
        print("=" * 60)
        print("🚀 Starting Main System in foreground...")
        print("   (You can interact with it normally)")
        print("   (Voice interface: python -m bridge_design_system.agents.chat_voice voice)")
        print("   (Press Ctrl+C to stop all services)")
        print("=" * 60)
        
        # Start main system in foreground (interactive)
        env = os.environ.copy()
        env["OTEL_BACKEND"] = "phoenix"
        
        # Build command with any additional arguments passed to this script
        cmd = ["uv", "run", "python", "-m", "bridge_design_system.main", 
               "--interactive", "--enable-command-server", "--disable-gaze"]
        
        # Add any additional arguments passed to this launcher
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
            print(f"📝 Additional flags: {' '.join(sys.argv[1:])}")
        
        main_result = subprocess.run(cmd, env=env)
        
        print(f"\n📋 Main system exited with code: {main_result.returncode}")
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        
    finally:
        # Clean up all processes
        for name, process in processes:
            if process and process.poll() is None:
                print(f"🔌 Stopping {name}...")
                try:
                    process.terminate()
                    # Give it 5 seconds to terminate gracefully
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print(f"⚡ Force killing {name}...")
                        process.kill()
                        process.wait()
                except Exception as e:
                    print(f"⚠️  Error stopping {name}: {e}")
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()