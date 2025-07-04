#!/usr/bin/env python3
"""Simple test to verify OpenTelemetry is working with smolagents."""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set up basic environment
os.environ["OTEL_BACKEND"] = "console"
os.environ["DEBUG"] = "true"

def test_otel_category_agent():
    """Test OpenTelemetry with the category agent specifically."""
    print("🧪 Testing OpenTelemetry with category agent...")
    
    # Import and set up OpenTelemetry first
    from bridge_design_system.monitoring.otel_config import OpenTelemetryConfig
    
    # Initialize OpenTelemetry with console backend for visibility
    otel_config = OpenTelemetryConfig(backend="console")
    success = otel_config.instrument()
    
    if not success:
        print("❌ OpenTelemetry instrumentation failed")
        return False
        
    print("✅ OpenTelemetry instrumentation successful")
    
    # Now create and test the category agent
    from bridge_design_system.agents.category_smolagent import create_category_agent
    
    print("🎯 Creating category agent...")
    agent = create_category_agent()
    
    print("🚀 Running simple task with category agent...")
    result = agent.run("Calculate the distance between points [0, 0] and [3, 4]")
    
    print(f"📊 Result: {result}")
    print("✅ Category agent with OpenTelemetry test complete!")
    
    # Shutdown
    otel_config.shutdown()
    return True

if __name__ == "__main__":
    try:
        test_otel_category_agent()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()