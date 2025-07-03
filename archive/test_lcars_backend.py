"""Test LCARS backend configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_lcars_backend():
    """Test LCARS backend specifically."""
    print("🧪 Testing LCARS backend configuration...")
    
    from bridge_design_system.monitoring.otel_config import OpenTelemetryConfig
    
    # Test with actual span generation
    config = OpenTelemetryConfig(backend="console")  # Use console to see spans
    success = config.instrument()
    
    if not success:
        print("❌ OpenTelemetry configuration failed")
        return False
    
    # Generate test spans to see if they flow through
    from opentelemetry import trace
    
    tracer = trace.get_tracer(__name__)
    print("🎯 Generating test spans...")
    
    with tracer.start_as_current_span("lcars_test_span") as span:
        span.set_attribute("test.backend", "lcars")
        span.set_attribute("test.purpose", "cross_process_verification")
        print("✅ Test span created")
        
        # Try LCARS specific operations
        try:
            from bridge_design_system.api.status_broadcaster import get_status_tracker
            status_tracker = get_status_tracker()
            
            if status_tracker:
                print("✅ Status tracker available - LCARS should receive spans")
            else:
                print("⚠️ Status tracker not available - cross-process issue confirmed")
                
        except Exception as e:
            print(f"⚠️ Status tracker test failed: {e}")
    
    config.shutdown()
    return True

if __name__ == "__main__":
    test_lcars_backend()