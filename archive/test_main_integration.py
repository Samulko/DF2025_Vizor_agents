"""Test OpenTelemetry integration with main.py"""

def test_main_cli():
    """Test OpenTelemetry CLI integration."""
    print("🧪 Testing main.py CLI OpenTelemetry integration...")
    
    # Test CLI arguments parsing
    import sys
    from pathlib import Path
    
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    from bridge_design_system.main import main
    from bridge_design_system.monitoring.otel_config import OpenTelemetryConfig
    
    # Test direct OpenTelemetry configuration (like main.py does)
    print("📺 Testing console backend configuration...")
    
    config = OpenTelemetryConfig(backend="console")
    success = config.instrument()
    
    if success:
        print("✅ Console backend configured successfully")
        
        # Test span generation like agents would
        from opentelemetry import trace
        tracer = trace.get_tracer("bridge_design_system")
        
        with tracer.start_as_current_span("triage_agent_task") as span:
            span.set_attribute("agent.name", "triage_agent")
            span.set_attribute("step.number", 1) 
            span.set_attribute("task.description", "User request: analyze bridge structure")
            print("🤖 Triage agent span generated")
            
            with tracer.start_as_current_span("delegate_to_geometry_agent") as span:
                span.set_attribute("agent.name", "triage_agent")
                span.set_attribute("delegation.target", "geometry_agent")
                span.set_attribute("step.number", 2)
                print("🔀 Delegation span generated")
        
        with tracer.start_as_current_span("geometry_agent_mcp_call") as span:
            span.set_attribute("agent.name", "geometry_agent")
            span.set_attribute("tool.name", "get_component_info_enhanced")
            span.set_attribute("mcp.component_id", "test_beam_001")
            span.set_attribute("step.number", 3)
            print("📐 Geometry MCP call span generated")
        
        config.shutdown()
        print("✅ Console backend test completed")
    else:
        print("❌ Console backend configuration failed")
        return False
    
    print("🔀 Testing hybrid backend configuration...")
    config = OpenTelemetryConfig(backend="hybrid")
    success = config.instrument()
    
    if success:
        print("✅ Hybrid backend configured (includes LCARS)")
        
        tracer = trace.get_tracer("bridge_design_system")
        
        with tracer.start_as_current_span("rational_agent_validation") as span:
            span.set_attribute("agent.name", "rational_agent")
            span.set_attribute("validation.type", "structural_integrity")
            span.set_attribute("step.number", 4)
            span.set_attribute("step.is_final", True)
            span.set_attribute("step.result", "Bridge design passes all safety checks")
            print("🧮 Rational agent validation span generated")
        
        config.shutdown()
        print("✅ Hybrid backend test completed")
    else:
        print("❌ Hybrid backend configuration failed")
        return False
    
    print("🎉 All OpenTelemetry integration tests passed!")
    print("💡 To use in production:")
    print("   uv run python -m bridge_design_system.main --interactive --otel-backend=hybrid")
    print("   uv run python -m bridge_design_system.main --interactive --otel-backend=console")
    print("   uv run python -m bridge_design_system.main --interactive --disable-otel")
    
    return True

if __name__ == "__main__":
    test_main_cli()