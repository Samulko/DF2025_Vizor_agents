"""Test hybrid backend with LCARS integration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_hybrid_backend():
    """Test hybrid backend with LCARS integration."""
    print("🧪 Testing hybrid backend with LCARS integration...")
    
    from bridge_design_system.monitoring.otel_config import OpenTelemetryConfig
    
    # Test hybrid backend (should include LCARS)
    config = OpenTelemetryConfig(backend="hybrid")
    success = config.instrument()
    
    if not success:
        print("❌ Hybrid backend configuration failed")
        return False
    
    print("✅ Hybrid backend configured successfully")
    
    # Generate test spans to verify all backends work
    from opentelemetry import trace
    
    tracer = trace.get_tracer(__name__)
    print("🎯 Generating test spans for all backends...")
    
    with tracer.start_as_current_span("hybrid_test_span") as span:
        span.set_attribute("agent.name", "test_agent")
        span.set_attribute("test.backend", "hybrid")
        span.set_attribute("test.component", "lcars_integration") 
        span.set_attribute("task.description", "Testing LCARS integration via OpenTelemetry")
        print("✅ Test span created - should appear in all configured backends")
    
    print("🎯 Testing with agent-like span...")
    with tracer.start_as_current_span("geometry_agent_task") as span:
        span.set_attribute("agent.name", "geometry_agent")
        span.set_attribute("step.number", 1)
        span.set_attribute("tool.name", "get_component_info_enhanced")
        span.set_attribute("task.description", "Analyzing bridge component geometry")
        print("✅ Geometry agent span created")
    
    config.shutdown()
    print("🔌 All backends shutdown")
    return True

if __name__ == "__main__":
    test_hybrid_backend()