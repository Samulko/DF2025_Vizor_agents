#!/usr/bin/env python3
"""Test script to verify category agent monitoring is working"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents import TriageAgent
from bridge_design_system.config.model_config import ModelProvider
from bridge_design_system.monitoring.trace_logger import get_trace_logger, finalize_workshop_session

def test_category_agent_monitoring():
    """Test if category agent monitoring is working"""
    print("🔍 Testing category agent monitoring...")
    
    # Initialize trace logger
    trace_logger = get_trace_logger()
    print(f"📊 Trace logger initialized: {trace_logger.current_session_id}")
    
    # Create triage agent with monitoring
    triage_agent = TriageAgent()
    
    # Test query that should trigger category agent
    test_query = "please use the category agent to calculate the distance between points [0,0] and [3,4]"
    print(f"🚀 Sending test query: {test_query}")
    
    try:
        response = triage_agent.handle_design_request(test_query)
        print(f"✅ Response received: {str(response)[:200]}...")
        
        # Check if category agent traces were created
        workshop_logs_dir = Path("workshop_logs/agents")
        category_traces_file = workshop_logs_dir / "category_material_agent_traces.jsonl"
        
        print(f"🔍 Checking for traces at: {category_traces_file}")
        
        if category_traces_file.exists():
            print("✅ Category agent traces file found!")
            with open(category_traces_file, 'r') as f:
                lines = f.readlines()
                print(f"📈 Found {len(lines)} trace entries")
                if lines:
                    print(f"🔬 Latest entry: {lines[-1][:100]}...")
        else:
            print("❌ Category agent traces file not found")
            print("📂 Available files:")
            if workshop_logs_dir.exists():
                for f in workshop_logs_dir.iterdir():
                    print(f"   - {f.name}")
            else:
                print("   Workshop logs directory doesn't exist")
                
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    # Finalize session
    finalize_workshop_session(
        participant_id="test_user",
        workshop_group="monitoring_test",
        session_notes="Testing category agent monitoring integration"
    )
    
    print("🏁 Test completed")

if __name__ == "__main__":
    test_category_agent_monitoring()