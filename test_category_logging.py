#!/usr/bin/env python3
"""
Quick test to verify category agent now has workshop logging.
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_category_agent_logging():
    """Test that category agent now logs to workshop_logs/"""
    print("🧪 Testing category agent with workshop logging...")
    
    try:
        from bridge_design_system.agents.category_smolagent import create_category_agent
        
        # Create category agent (should have logging enabled)
        print("1️⃣ Creating category agent...")
        agent = create_category_agent()
        
        # Verify logging was added
        if hasattr(agent, '_workshop_logging_enabled'):
            print("✅ Workshop logging is enabled!")
        else:
            print("❌ Workshop logging not found")
            return False
        
        # Test a simple task
        print("2️⃣ Running test task...")
        result = agent.run("Calculate the distance between points [0, 0] and [3, 4]")
        print(f"📊 Result: {result}")
        
        # Check if log files were created
        logs_dir = Path("workshop_logs")
        if logs_dir.exists():
            print("3️⃣ Checking log files...")
            
            # Check for agent-specific log
            agent_log = logs_dir / "agents" / "category_agent_traces.jsonl"
            if agent_log.exists():
                print(f"✅ Found agent log: {agent_log}")
                # Show last line
                with open(agent_log, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"📝 Latest log entry: {lines[-1].strip()[:100]}...")
            else:
                print(f"❌ Agent log not found: {agent_log}")
            
            # Check for daily log
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            daily_log = logs_dir / "daily" / f"{today}_traces.jsonl"
            if daily_log.exists():
                print(f"✅ Found daily log: {daily_log}")
            else:
                print(f"❌ Daily log not found: {daily_log}")
                
        else:
            print("❌ workshop_logs directory not found")
            return False
        
        print("🎉 Category agent logging test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_category_agent_logging()
    sys.exit(0 if success else 1)