"""Simple log monitor that extracts agent status from log files."""

import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Set


class AgentStatusMonitor:
    """Monitors log files to extract agent status (working/ready/error)."""
    
    STATUS_PATTERNS = {
        "working": [
            r"🎯 Executing task",
            r"Processing request",
            r"Running",
            r"Delegating to",
            r"🔍 Searching",
            r"📝 Creating",
            r"🔧 Generating",
        ],
        "ready": [
            r"✅ Task completed",
            r"✅ .* completed successfully",
            r"Initialized successfully",
            r"Ready",
            r"Idle",
            r"initialized successfully",
        ],
        "error": [
            r"❌ Error:",
            r"❌ Failed",
            r"Exception:",
            r"execution failed",
        ]
    }
    
    def __init__(self, log_dir: Path = Path("logs")):
        self.log_dir = log_dir
        self.agent_status = {
            "triage_agent": "ready",
            "geometry_agent": "ready", 
            "syslogic_agent": "ready"
        }
        self.file_positions = {}
        self.callbacks: Set = set()
        
    def add_callback(self, callback):
        """Add a callback to be notified of status changes."""
        self.callbacks.add(callback)
        
    def remove_callback(self, callback):
        """Remove a callback."""
        self.callbacks.discard(callback)
        
    async def _notify_callbacks(self):
        """Notify all callbacks of status change."""
        for callback in self.callbacks:
            await callback(self.agent_status.copy())
    
    def _extract_agent_name(self, line: str) -> Optional[str]:
        """Extract agent name from log line."""
        # Look for agent names in the log line
        line_lower = line.lower()
        if "triage" in line_lower:
            return "triage_agent"
        elif "geometry" in line_lower:
            return "geometry_agent"
        elif "syslogic" in line_lower:
            return "syslogic_agent"
        return None
    
    def _determine_status(self, line: str) -> Optional[str]:
        """Determine status from log line."""
        # Check each status pattern
        for status, patterns in self.STATUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return status
        return None
    
    async def _read_new_lines(self, file_path: Path):
        """Read new lines from a log file."""
        if not file_path.exists():
            return
            
        # Get last position or start from beginning
        last_pos = self.file_positions.get(str(file_path), 0)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                self.file_positions[str(file_path)] = f.tell()
                
            # Process new lines
            for line in new_lines:
                agent_name = self._extract_agent_name(line)
                if agent_name:
                    new_status = self._determine_status(line)
                    if new_status and self.agent_status.get(agent_name) != new_status:
                        self.agent_status[agent_name] = new_status
                        await self._notify_callbacks()
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    async def start_monitoring(self):
        """Start monitoring log files for status changes."""
        print(f"📊 Starting status monitor on {self.log_dir}")
        
        while True:
            try:
                # Check all log files
                if self.log_dir.exists():
                    for log_file in self.log_dir.glob("*.log"):
                        await self._read_new_lines(log_file)
                        
                # Small delay to avoid excessive CPU usage
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(1)