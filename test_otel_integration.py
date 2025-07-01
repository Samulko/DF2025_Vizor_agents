#!/usr/bin/env python3
"""Test OpenTelemetry integration with bridge design system."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.monitoring.otel_config import OpenTelemetryConfig
from bridge_design_system.config.logging_config import get_logger

logger = get_logger(__name__)


def test_console_backend():
    """Test OpenTelemetry with console backend."""
    print("🧪 Testing OpenTelemetry Console Backend...")
    
    config = OpenTelemetryConfig(backend="console")
    success = config.instrument()
    
    if success:
        print("✅ Console backend configured successfully")
        
        # Test with a simple smolagents operation
        try:
            from smolagents import ToolCallingAgent, tool
            from smolagents.models import InferenceClientModel
            
            # Create a simple test tool
            @tool
            def test_tool(message: str) -> str:
                """Test tool for OpenTelemetry."""
                return f"Test tool received: {message}"
            
            # Create agent with our test tool
            model = InferenceClientModel(model_id="microsoft/DialoGPT-medium")
            agent = ToolCallingAgent(
                tools=[test_tool],
                model=model,
                name="test_agent",
                description="Test agent for OpenTelemetry integration"
            )
            
            # Run a simple task
            print("🤖 Running test agent task...")
            result = agent.run("Use the test tool to say hello")
            print(f"📝 Agent result: {result}")
            
        except Exception as e:
            print(f"⚠️ Agent test failed (this is expected without API keys): {e}")
            
        config.shutdown()
        print("✅ Console backend test completed")
        return True
    else:
        print("❌ Console backend configuration failed")
        return False


def test_hybrid_backend():
    """Test OpenTelemetry with hybrid backend (console + LCARS simulation)."""
    print("\n🧪 Testing OpenTelemetry Hybrid Backend...")
    
    # Create mock LCARS status tracker
    class MockStatusTracker:
        def __init__(self):
            self.updates = []
            
        async def update_status(self, agent_name: str, **kwargs):
            self.updates.append({"agent": agent_name, "data": kwargs})
            print(f"📊 LCARS Update: {agent_name} -> {kwargs}")
    
    # Create LCARS exporter
    from bridge_design_system.monitoring.lcars_otel_bridge import create_lcars_exporter
    
    mock_tracker = MockStatusTracker()
    lcars_exporter = create_lcars_exporter(mock_tracker)
    
    config = OpenTelemetryConfig(backend="hybrid")
    success = config.instrument(lcars_exporter)
    
    if success:
        print("✅ Hybrid backend configured successfully")
        print("✅ LCARS exporter integrated")
        
        config.shutdown()
        return True
    else:
        print("❌ Hybrid backend configuration failed")
        return False


def test_langfuse_backend():
    """Test OpenTelemetry with Langfuse backend (if keys available)."""
    print("\n🧪 Testing OpenTelemetry Langfuse Backend...")
    
    from bridge_design_system.config.settings import settings
    
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        print("⏭️ Skipping Langfuse test - no API keys configured")
        return True
        
    config = OpenTelemetryConfig(backend="langfuse")
    success = config.instrument()
    
    if success:
        print("✅ Langfuse backend configured successfully")
        config.shutdown()
        return True
    else:
        print("❌ Langfuse backend configuration failed")
        return False


def main():
    """Run all OpenTelemetry tests."""
    print("🚀 Starting OpenTelemetry Integration Tests")
    print("=" * 50)
    
    results = []
    
    # Test console backend
    results.append(test_console_backend())
    
    # Test hybrid backend
    results.append(test_hybrid_backend())
    
    # Test Langfuse backend
    results.append(test_langfuse_backend())
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        return 0
    else:
        print(f"⚠️ {passed}/{total} tests passed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)