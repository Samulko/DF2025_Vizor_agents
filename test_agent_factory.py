#!/usr/bin/env python3
"""Test script for the new AgentFactory pattern.

This script validates that the new factory pattern works correctly
and can replace the old BaseAgent inheritance pattern.
"""
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.bridge_design_system.agents.agent_factory import AgentFactory
from src.bridge_design_system.agents.agent_templates import AgentTemplates, ProductionConfig
from src.bridge_design_system.agents.smolagents_exceptions import (
    SmolagentsExceptionMapper, 
    SmolagentsResponseHelper,
    validate_smolagents_integration
)
from src.bridge_design_system.tools.material_tools import (
    check_material_inventory,
    find_best_piece_for_cut, 
    cut_timber_piece,
    add_timber_stock,
    get_material_statistics
)


def test_smolagents_integration():
    """Test that smolagents exceptions are properly integrated."""
    print("🔧 Testing Smolagents Integration")
    
    validation = validate_smolagents_integration()
    print(f"  Integration valid: {validation['integration_valid']}")
    print(f"  Available exceptions: {len(validation['available_exceptions'])}")
    
    if validation['integration_valid']:
        print("  ✅ All smolagents exceptions available")
        return True
    else:
        print(f"  ❌ Integration failed: {validation.get('error', 'Unknown error')}")
        return False


def test_agent_templates():
    """Test agent template creation and validation."""
    print("\n🔧 Testing Agent Templates")
    
    try:
        # Test individual templates
        geometry_template = AgentTemplates.get_development_template("geometry")
        material_template = AgentTemplates.get_production_template("material")
        
        print(f"  ✅ Geometry template: {geometry_template.description}")
        print(f"  ✅ Material template: {material_template.description}")
        
        # Test template validation
        geo_validation = AgentTemplates.validate_template(geometry_template)
        mat_validation = AgentTemplates.validate_template(material_template)
        
        print(f"  Geometry validation: {geo_validation['valid']}")
        print(f"  Material validation: {mat_validation['valid']}")
        
        if not geo_validation['valid']:
            print(f"    Issues: {geo_validation['issues']}")
        if not mat_validation['valid']:
            print(f"    Issues: {mat_validation['issues']}")
        
        # Test system configuration
        dev_config = ProductionConfig.get_development_config()
        prod_config = ProductionConfig.get_bridge_system_config()
        
        print(f"  ✅ Development config: {len(dev_config)} agents")
        print(f"  ✅ Production config: {len(prod_config)} agents")
        
        # Validate system configurations
        dev_validation = ProductionConfig.validate_system_config(dev_config)
        prod_validation = ProductionConfig.validate_system_config(prod_config)
        
        print(f"  Development system valid: {dev_validation['overall_valid']}")
        print(f"  Production system valid: {prod_validation['overall_valid']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Template testing failed: {e}")
        traceback.print_exc()
        return False


def test_agent_factory_validation():
    """Test agent factory validation methods."""
    print("\n🔧 Testing Agent Factory Validation")
    
    try:
        # Test validation for each agent type
        agent_types = ["geometry", "material", "structural", "triage"]
        
        for agent_type in agent_types:
            validation = AgentFactory.validate_agent_creation(agent_type)
            print(f"  {agent_type}: {validation['valid']}")
            
            if not validation['valid']:
                print(f"    Error: {validation['error']}")
            else:
                model_info = validation['model_info']
                print(f"    Model: {model_info['provider']}/{model_info['model']}")
                print(f"    API Key: {'✅' if model_info['has_api_key'] else '❌'}")
                
                # Special handling for geometry agent MCP status
                if agent_type == "geometry" and validation.get('mcp_status'):
                    mcp_status = validation['mcp_status']
                    if mcp_status['connected']:
                        print(f"    MCP: ✅ {mcp_status['tool_count']} tools")
                    else:
                        print(f"    MCP: ❌ {mcp_status['error']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Factory validation failed: {e}")
        traceback.print_exc()
        return False


def test_material_agent_creation():
    """Test material agent creation with factory pattern."""
    print("\n🔧 Testing Material Agent Creation")
    
    try:
        # Prepare material tools
        material_tools = [
            check_material_inventory,
            find_best_piece_for_cut,
            cut_timber_piece,
            add_timber_stock,
            get_material_statistics
        ]
        
        # Create material agent using factory
        material_agent = AgentFactory.create_material_agent(
            tools=material_tools,
            model_name="material"
        )
        
        print(f"  ✅ Material agent created: {type(material_agent).__name__}")
        print(f"  Tools: {len(material_agent.tools)}")
        print(f"  Model: {material_agent.model}")
        print(f"  Max steps: {material_agent.max_steps}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Material agent creation failed: {e}")
        traceback.print_exc()
        return False


def test_geometry_agent_creation():
    """Test geometry agent creation with factory pattern."""
    print("\n🔧 Testing Geometry Agent Creation")
    
    try:
        # Create geometry agent using factory
        geometry_agent = AgentFactory.create_geometry_agent(
            model_name="geometry"
        )
        
        print(f"  ✅ Geometry agent created: {type(geometry_agent).__name__}")
        print(f"  Tools: {len(geometry_agent.tools)}")
        print(f"  Model: {geometry_agent.model}")
        print(f"  Max steps: {geometry_agent.max_steps}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Geometry agent creation failed: {e}")
        print(f"  This may be expected if MCP server is not running")
        traceback.print_exc()
        return False


def test_generic_agent_creation():
    """Test generic agent creation patterns."""
    print("\n🔧 Testing Generic Agent Creation")
    
    try:
        from smolagents import tool
        
        # Create a simple test tool
        @tool
        def test_tool(message: str) -> str:
            """Test tool for validation."""
            return f"Processed: {message}"
        
        # Test generic code agent creation
        code_agent = AgentFactory.create_agent(
            agent_type="code",
            tools=[test_tool],
            model_name="triage"
        )
        
        print(f"  ✅ Generic code agent created: {type(code_agent).__name__}")
        print(f"  Tools: {len(code_agent.tools)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Generic agent creation failed: {e}")
        traceback.print_exc()
        return False


def test_error_handling_patterns():
    """Test error handling with smolagents exceptions."""
    print("\n🔧 Testing Error Handling Patterns")
    
    try:
        from smolagents import AgentError, AgentExecutionError
        
        # Test error mapping
        legacy_error = SmolagentsExceptionMapper.create_geometry_error(
            "Test geometry error",
            original_exception=ValueError("Original error")
        )
        
        print(f"  ✅ Geometry error created: {type(legacy_error).__name__}")
        
        # Test response helper
        success_response = SmolagentsResponseHelper.create_success_response(
            result="Test result",
            metadata={"test": True}
        )
        
        print(f"  ✅ Success response: {success_response['success']}")
        
        # Test error response
        error_response = SmolagentsResponseHelper.handle_agent_error(
            AgentExecutionError("Test execution error"),
            context="test_context"
        )
        
        print(f"  ✅ Error response: {error_response['error_type']}")
        print(f"  Recoverable: {error_response['recoverable']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all factory pattern tests."""
    print("🚀 Starting Agent Factory Pattern Tests\n")
    
    tests = [
        test_smolagents_integration,
        test_agent_templates,
        test_agent_factory_validation,
        test_material_agent_creation,
        test_geometry_agent_creation,
        test_generic_agent_creation,
        test_error_handling_patterns
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Agent factory pattern is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)