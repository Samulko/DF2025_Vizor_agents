"""Verify OpenTelemetry span generation without agents."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

def test_basic_span_generation():
    """Test if OpenTelemetry can generate spans at all."""
    print("🧪 Testing basic OpenTelemetry span generation...")
    
    # Create minimal setup
    provider = TracerProvider()
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    # Create test span
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("test_span") as span:
        span.set_attribute("test.attribute", "test_value")
        span.set_attribute("test.component", "basic_verification")
        print("✅ Test span created successfully")
    
    print("🎯 If you see span output above, basic OpenTelemetry works")
    
    # Shutdown to flush any remaining spans
    provider.shutdown()
    return True

if __name__ == "__main__":
    test_basic_span_generation()