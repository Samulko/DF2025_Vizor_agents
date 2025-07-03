"""Test Phoenix backend configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_phoenix_backend():
    """Test Phoenix backend specifically."""
    print("🧪 Testing Phoenix backend configuration...")
    
    from bridge_design_system.monitoring.otel_config import OpenTelemetryConfig
    
    # Test Phoenix backend
    config = OpenTelemetryConfig(backend="phoenix")
    success = config.instrument()
    
    if success:
        print("✅ Phoenix backend configured successfully")
        print("🌐 Check Phoenix UI for traces")
    else:
        print("❌ Phoenix backend configuration failed")
        print("💡 This is expected if Phoenix server is not running")
    
    config.shutdown()
    return success

if __name__ == "__main__":
    test_phoenix_backend()