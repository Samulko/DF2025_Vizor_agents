#!/usr/bin/env python3
"""
Test script to verify rational agent logging is working.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.triage_agent_smolagents import TriageSystemWrapper

def test_rational_agent_logging():
    """Test that rational agent logging is working."""
    print("🧪 Testing rational agent logging...")
    
    try:
        # Create triage system
        triage_system = TriageSystemWrapper()
        
        # Test a request that should delegate to rational agent (level validation)
        print("\n📋 Testing rational agent delegation...")
        response = triage_system.handle_design_request(
            "Can you check if all the bridge elements are properly level (horizontal)? Validate their direction vectors."
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
        
        # Look specifically for rational_agent traces
        rational_traces = [f for f in trace_files if "rational_agent" in f.name]
        if rational_traces:
            print("✅ SUCCESS: Rational agent trace file found!")
        else:
            print("❌ ISSUE: No rational agent trace file found")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rational_agent_logging()