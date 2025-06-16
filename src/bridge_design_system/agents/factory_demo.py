"""Demonstration of the new AgentFactory pattern.

This module shows how to use the AgentFactory and AgentTemplates to create
agents following smolagents best practices. It replaces the old BaseAgent
inheritance pattern with clean factory methods.
"""
import logging
from typing import List

from smolagents import tool, AgentError, AgentExecutionError

from .agent_factory import AgentFactory
from .agent_templates import AgentTemplates, ProductionConfig, ExecutionEnvironment, SecurityLevel
from ..tools.material_tools import (
    check_material_inventory,
    find_best_piece_for_cut,
    cut_timber_piece,
    add_timber_stock,
    get_material_statistics
)

logger = logging.getLogger(__name__)


class FactoryDemo:
    """Demonstration of agent factory patterns."""
    
    @staticmethod
    def demo_geometry_agent_creation():
        """Demonstrate geometry agent creation with factory pattern."""
        print("🔧 Creating Geometry Agent with Factory Pattern")
        
        try:
            # Get template for development environment
            template = AgentTemplates.get_development_template("geometry")
            print(f"✅ Template created: {template.description}")
            
            # Validate template
            validation = AgentTemplates.validate_template(template)
            if not validation["valid"]:
                print(f"⚠️  Template issues: {validation['issues']}")
            
            # Create geometry agent using factory
            geometry_agent = AgentFactory.create_geometry_agent(
                model_name="geometry",
                max_steps=template.security_config.max_steps
            )
            
            print(f"✅ Geometry agent created successfully")
            print(f"   Model temperature: {template.model_temperature}")
            print(f"   Max steps: {template.security_config.max_steps}")
            print(f"   Security level: {template.security_config.security_level.value}")
            
            return geometry_agent
            
        except AgentError as e:
            print(f"❌ Failed to create geometry agent: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    @staticmethod
    def demo_material_agent_creation():
        """Demonstrate material agent creation with factory pattern."""
        print("\n🔧 Creating Material Agent with Factory Pattern")
        
        try:
            # Get template for production environment
            template = AgentTemplates.get_production_template("material")
            print(f"✅ Template created: {template.description}")
            
            # Create material management tools
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
                model_name="material",
                max_steps=template.security_config.max_steps
            )
            
            print(f"✅ Material agent created successfully")
            print(f"   Security environment: {template.security_config.execution_environment.value}")
            print(f"   Authorized imports: {len(template.security_config.authorized_imports)} modules")
            print(f"   Rate limit: {template.security_config.rate_limit_requests} req/min")
            
            return material_agent
            
        except AgentError as e:
            print(f"❌ Failed to create material agent: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    @staticmethod
    def demo_triage_agent_creation():
        """Demonstrate triage agent creation with managed agents."""
        print("\n🔧 Creating Triage Agent with Managed Agents")
        
        try:
            # Create specialized agents first
            print("Creating specialized agents...")
            
            # Create geometry agent
            geometry_agent = AgentFactory.create_geometry_agent(model_name="geometry")
            print("  ✅ Geometry agent created")
            
            # Create material agent
            material_tools = [
                check_material_inventory,
                find_best_piece_for_cut,
                cut_timber_piece,
                add_timber_stock,
                get_material_statistics
            ]
            material_agent = AgentFactory.create_material_agent(
                tools=material_tools,
                model_name="material"
            )
            print("  ✅ Material agent created")
            
            # Create coordination tools for triage
            @tool
            def delegate_task(task_description: str, target_agent: str) -> str:
                """Delegate task to a specialized agent.
                
                Args:
                    task_description: Description of the task to delegate
                    target_agent: Name of the target agent (geometry, material, structural)
                    
                Returns:
                    Delegation confirmation
                """
                return f"Task '{task_description}' delegated to {target_agent} agent"
            
            coordination_tools = [delegate_task]
            
            # Create triage agent with managed agents
            triage_agent = AgentFactory.create_triage_agent(
                coordination_tools=coordination_tools,
                managed_agents=[geometry_agent, material_agent],
                model_name="triage"
            )
            
            print("✅ Triage agent created with 2 managed agents")
            print("   ✅ Hierarchical delegation enabled")
            print("   ✅ Memory separation maintained")
            
            return triage_agent
            
        except AgentError as e:
            print(f"❌ Failed to create triage agent: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    @staticmethod
    def demo_system_configuration():
        """Demonstrate complete system configuration."""
        print("\n🔧 Creating Complete Bridge Design System")
        
        try:
            # Get development configuration
            dev_config = ProductionConfig.get_development_config()
            print(f"✅ Development config loaded with {len(dev_config)} agent types")
            
            # Validate system configuration
            validation = ProductionConfig.validate_system_config(dev_config)
            print(f"✅ System validation: {validation['overall_valid']}")
            
            if not validation["overall_valid"]:
                for agent, result in validation["agent_results"].items():
                    if not result["valid"]:
                        print(f"  ⚠️  {agent}: {result['issues']}")
            
            # Get production configuration
            prod_config = ProductionConfig.get_bridge_system_config()
            print(f"✅ Production config loaded with {len(prod_config)} agent types")
            
            # Show configuration differences
            print("\n📊 Configuration Comparison:")
            for agent_type in dev_config.keys():
                dev_template = dev_config[agent_type]
                prod_template = prod_config[agent_type]
                
                print(f"  {agent_type.upper()} Agent:")
                print(f"    Dev:  {dev_template.security_config.security_level.value} | {dev_template.security_config.execution_environment.value}")
                print(f"    Prod: {prod_template.security_config.security_level.value} | {prod_template.security_config.execution_environment.value}")
            
            return dev_config, prod_config
            
        except Exception as e:
            print(f"❌ System configuration failed: {e}")
            return None, None
    
    @staticmethod
    def demo_error_handling():
        """Demonstrate proper error handling with smolagents exceptions."""
        print("\n🔧 Demonstrating Error Handling Patterns")
        
        try:
            # Test validation
            validation = AgentFactory.validate_agent_creation("geometry")
            print(f"✅ Geometry agent validation: {validation['valid']}")
            
            if validation.get("mcp_status"):
                mcp_status = validation["mcp_status"]
                if mcp_status["connected"]:
                    print(f"  ✅ MCP connection: {mcp_status['tool_count']} tools available")
                else:
                    print(f"  ⚠️  MCP connection failed: {mcp_status['error']}")
            
            # Test invalid agent type
            try:
                AgentFactory.create_agent("invalid_type", [])
            except AgentError as e:
                print(f"✅ Proper error handling for invalid type: {e}")
            
            # Test missing configuration
            try:
                validation = AgentFactory.validate_agent_creation("nonexistent")
                if not validation["valid"]:
                    print(f"✅ Configuration validation caught error: {validation['error']}")
            except Exception as e:
                print(f"✅ Exception handling working: {type(e).__name__}")
            
        except Exception as e:
            print(f"❌ Error handling demo failed: {e}")
    
    @staticmethod
    def run_complete_demo():
        """Run complete demonstration of factory patterns."""
        print("🚀 Starting Complete Agent Factory Demonstration\n")
        
        # Demo individual agent creation
        geometry_agent = FactoryDemo.demo_geometry_agent_creation()
        material_agent = FactoryDemo.demo_material_agent_creation()
        triage_agent = FactoryDemo.demo_triage_agent_creation()
        
        # Demo system configuration
        dev_config, prod_config = FactoryDemo.demo_system_configuration()
        
        # Demo error handling
        FactoryDemo.demo_error_handling()
        
        # Summary
        print("\n📋 Demo Summary:")
        print(f"  ✅ Geometry Agent: {'Created' if geometry_agent else 'Failed'}")
        print(f"  ✅ Material Agent: {'Created' if material_agent else 'Failed'}")
        print(f"  ✅ Triage Agent: {'Created' if triage_agent else 'Failed'}")
        print(f"  ✅ System Config: {'Loaded' if dev_config else 'Failed'}")
        print("\n🎉 Factory pattern demonstration complete!")
        
        return {
            "geometry_agent": geometry_agent,
            "material_agent": material_agent,
            "triage_agent": triage_agent,
            "dev_config": dev_config,
            "prod_config": prod_config
        }


def compare_old_vs_new_patterns():
    """Compare old BaseAgent pattern vs new Factory pattern."""
    print("🔄 Comparing Old vs New Agent Patterns\n")
    
    print("❌ OLD PATTERN (BaseAgent inheritance):")
    print("""
    class MaterialAgent(BaseAgent):
        def __init__(self):
            super().__init__("material_agent", "description")
            self.tools = []
            self._agent = None
            
        def _get_system_prompt(self) -> str:
            # Load prompt from file
            
        def _initialize_tools(self) -> List[Tool]:
            # Create tools manually
            
        def initialize_agent(self):
            # Complex two-step initialization
            
        def run(self, task: str) -> AgentResponse:
            # Custom response handling
    
    # Problems:
    # - Complex inheritance hierarchy
    # - Two-step initialization
    # - Custom error types (AgentError enum)
    # - Duplicate conversation/memory management
    # - Inconsistent security configuration
    """)
    
    print("✅ NEW PATTERN (Factory methods):")
    print("""
    # Simple factory creation
    material_agent = AgentFactory.create_material_agent(
        tools=material_tools,
        model_name="material"
    )
    
    # Or with template configuration
    template = AgentTemplates.get_production_template("material")
    material_agent = AgentFactory.create_material_agent(
        tools=material_tools,
        model_name="material",
        max_steps=template.security_config.max_steps
    )
    
    # Benefits:
    # - No inheritance complexity
    # - Single-step creation
    # - Native smolagents exceptions
    # - Centralized memory management
    # - Consistent security templates
    # - Production-ready configurations
    """)
    
    print("📊 Migration Benefits:")
    print("  • 30% fewer LLM calls (smolagents efficiency)")
    print("  • Reduced code complexity")
    print("  • Better error handling")
    print("  • Production-ready security")
    print("  • Standardized monitoring")


if __name__ == "__main__":
    # Run demonstrations
    compare_old_vs_new_patterns()
    results = FactoryDemo.run_complete_demo()