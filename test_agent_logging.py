#!/usr/bin/env python3
"""
Test script to verify individual agent logging is working.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper

def test_agent_logging():
    """Test that individual agent logging is working."""
    print("🧪 Testing individual agent logging...")
    
    try:
        # Create triage system
        triage_system = TriageSystemWrapper()
        
        # Test a simple request that should delegate to geometry agent
        print("\n📋 Testing geometry agent delegation...")
        response = triage_system.handle_design_request(
            "Can you tell me how many components are currently in Grasshopper?"
        )
        
        print(f"✅ Response received: {response.message[:100]}...")
        
        # Check if trace files were created
        workshop_logs = Path("workshop_logs/agents")
        trace_files = list(workshop_logs.glob("*_traces.jsonl"))
        
        print(f"\n📊 Trace files found: {len(trace_files)}")
        for trace_file in trace_files:
            print(f"  - {trace_file.name}")
            
            # Read the last line to see recent activity
            if trace_file.exists():
                with open(trace_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"    Last entry: {lines[-1][:100]}...")
        
        if len(trace_files) > 1:
            print("✅ SUCCESS: Multiple agent trace files found!")
        else:
            print("❌ ISSUE: Only found trace files for:", [f.stem for f in trace_files])
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_logging()