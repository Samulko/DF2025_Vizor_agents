"""Main entry point for the Bridge Design System.

This system uses MCPAdapt for robust MCP integration with Grasshopper,
providing stable async/sync handling and eliminating event loop issues.
"""
import logging
from pathlib import Path

from .agents.triage_agent import TriageAgent
from .config.logging_config import get_logger
from .config.model_config import ModelProvider
from .config.settings import settings
from .state.component_registry import initialize_registry, get_global_registry

logger = get_logger(__name__)


def validate_environment():
    """Validate that required environment variables are set."""
    # Get unique providers needed
    providers = set()
    for agent in ["triage", "geometry", "material", "structural"]:
        provider = getattr(settings, f"{agent}_agent_provider", None)
        if provider:
            providers.add(provider)
    
    # Check API keys
    missing = settings.validate_required_keys(list(providers))
    if missing:
        logger.error(f"Missing API keys for providers: {missing}")
        logger.error("Please set the required API keys in your .env file")
        return False
    
    # Check paths
    if not settings.grasshopper_mcp_path:
        logger.warning("GRASSHOPPER_MCP_PATH not set - MCP features will be limited")
    
    return True


def test_system():
    """Run a basic system test."""
    logger.info("Running system test...")
    
    try:
        # Test model configuration
        logger.info("Testing model configuration...")
        results = ModelProvider.validate_all_models()
        
        for agent, success in results.items():
            if success:
                logger.info(f"✓ {agent} agent model validated")
            else:
                logger.error(f"✗ {agent} agent model failed validation")
        
        if not all(results.values()):
            logger.error("Model validation failed")
            return False
        
        # Test agent initialization
        logger.info("\nTesting agent initialization...")
        registry = initialize_registry()
        triage = TriageAgent(component_registry=registry)
        triage.initialize_agent()
        logger.info("✓ Triage agent initialized successfully")
        
        # Test basic operation
        logger.info("\nTesting basic operation...")
        response = triage.handle_design_request(
            "Hello, I'd like to test the system. Can you tell me what agents are available and confirm STDIO-only transport?"
        )
        
        if response.success:
            logger.info("✓ System test completed successfully")
            logger.info(f"Response: {response.message[:200]}...")
            return True
        else:
            logger.error(f"System test failed: {response.message}")
            return False
            
    except Exception as e:
        logger.error(f"System test failed with error: {e}", exc_info=True)
        return False


def interactive_mode(use_legacy=False, reset_memory=False):
    """Run the system in interactive mode.
    
    Args:
        use_legacy: If True, use legacy triage agent (default is smolagents-native)
        reset_memory: If True, start with fresh agent memories
    """
    mode = "legacy" if use_legacy else "smolagents-native"
    logger.info(f"Starting Bridge Design System in interactive mode ({mode})...")
    
    if not validate_environment():
        return
    
    try:
        # Initialize component registry
        registry = initialize_registry()
        logger.info("Component registry initialized")
        
        if use_legacy:
            # Use legacy implementation
            triage = TriageAgent(component_registry=registry)
            triage.initialize_agent()
            logger.info("System initialized with legacy implementation")
        else:
            # Use default smolagents-native implementation
            from .agents.triage_agent_smolagents import TriageSystemWrapper
            triage = TriageSystemWrapper(component_registry=registry)
            logger.info("System initialized with smolagents-native patterns")
        
        # Reset memory if requested
        if reset_memory:
            logger.info("🔄 Resetting agent memories as requested...")
            triage.reset_all_agents()
            registry.clear()
            logger.info("✅ Started with fresh agent memories")
        
        print("\n" + "="*60)
        print("AR-Assisted Bridge Design System")
        if use_legacy:
            print("⚙️ Using LEGACY implementation")
            print("🔧 STDIO-only geometry agent")
        else:
            print("🚀 Using smolagents-native implementation (DEFAULT)")
            print("✨ 75% less code, 30% more efficient!")
        print("="*60)
        print("\nType 'exit' to quit, 'reset' to clear all agent memories")
        print("Type 'status' to see agent status")
        if reset_memory:
            print("✅ Started with fresh memories (--reset flag used)")
        print()
        
        while True:
            try:
                user_input = input("\nDesigner> ").strip()
                
                if user_input.lower() == 'exit':
                    print("Exiting Bridge Design System...")
                    break
                elif user_input.lower() == 'reset':
                    print("🔄 Resetting all agent memories...")
                    triage.reset_all_agents()
                    registry.clear()
                    print("✅ All agent memories and component registry reset - starting fresh!")
                    continue
                elif user_input.lower() == 'status':
                    if use_legacy:
                        # Legacy status
                        status = triage.get_agent_status()
                        print("\nAgent Status (Legacy):")
                        for agent, info in status.items():
                            conversation_len = len(triage.managed_agents[agent].conversation_history) if agent in triage.managed_agents and hasattr(triage.managed_agents[agent], 'conversation_history') else 0
                            print(f"  {agent}: Steps={info['step_count']}, Initialized={info['initialized']}, Conversations={conversation_len}")
                    else:
                        # Smolagents status (default)
                        status = triage.get_status()
                        print("\nAgent Status (Smolagents Native):")
                        for agent, info in status.items():
                            print(f"  {agent}: {info}")
                    
                    # Registry status
                    registry_stats = registry.get_stats()
                    print(f"\nComponent Registry:")
                    print(f"  Components: {registry_stats['total_components']}")
                    print(f"  Types: {', '.join(registry_stats['types'])}")
                    print(f"  Recent: {registry_stats['recent_components']}")
                    continue
                elif not user_input:
                    continue
                
                # Process the request
                print("\nProcessing...")
                response = triage.handle_design_request(user_input)
                
                if response.success:
                    print(f"\nTriage Agent> {response.message}")
                else:
                    print(f"\nError: {response.message}")
                    if response.error:
                        print(f"Error Type: {response.error.value}")
                        
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}", exc_info=True)
                print(f"\nError: {str(e)}")
                
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}", exc_info=True)
        print(f"Initialization failed: {str(e)}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bridge Design System (smolagents-native by default)")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run system test"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode (uses smolagents-native by default)"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy triage agent implementation (instead of default smolagents)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Start with fresh agent memories (clears previous conversation history)"
    )
    parser.add_argument(
        "--enhanced-cli",
        action="store_true",
        help="Run enhanced CLI with Rich formatting and real-time status"
    )
    parser.add_argument(
        "--start-mcp-server",
        action="store_true",
        help="Start HTTP MCP server for Grasshopper integration (legacy)"
    )
    parser.add_argument(
        "--start-official-mcp",
        action="store_true",
        help="Start official MCP server using MCP SDK (stdio transport)"
    )
    parser.add_argument(
        "--start-streamable-http",
        action="store_true",
        help="Start official MCP streamable-http server (recommended)"
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=8001,
        help="Port for MCP HTTP server (default: 8001)"
    )
    parser.add_argument(
        "--grasshopper-url",
        default="http://localhost:8080",
        help="URL of Grasshopper HTTP server (default: http://localhost:8080)"
    )
    
    args = parser.parse_args()
    
    if args.test:
        success = test_system()
        exit(0 if success else 1)
    elif args.start_streamable_http:
        # Use Clean FastMCP implementation (recommended approach)
        print("🔍 Checking for FastMCP server availability...")
        
        fastmcp_available = False
        try:
            # Test FastMCP imports before attempting to use
            from mcp.server.fastmcp import FastMCP
            print("✅ FastMCP framework available")
            fastmcp_available = True
        except ImportError as e:
            print(f"⚠️ FastMCP framework not available: {e}")
        
        if fastmcp_available:
            try:
                from .mcp.fastmcp_server_clean import run_clean_fastmcp_server
                
                print("🚀 Starting Clean FastMCP server (pure FastMCP architecture)")
                print("🎯 Architecture: FastMCP with @custom_route decorators for bridge endpoints")
                print("✅ Note: Using FastMCP @custom_route for bridge compatibility")
                
                # Use the clean FastMCP approach - let FastMCP own everything
                run_clean_fastmcp_server(
                    grasshopper_url=args.grasshopper_url,
                    host="127.0.0.1",
                    port=args.mcp_port
                )
                
            except Exception as e:
                print(f"❌ Clean FastMCP server not suitable for HTTP: {e}")
                print(f"🔄 Using Manual MCP server for reliable HTTP support...")
                fastmcp_available = False
        
        if not fastmcp_available:
            # Use manual server as fallback
            try:
                from .mcp.manual_mcp_server import ManualMCPServer
                
                # Fallback to manual server
                server = ManualMCPServer(
                    grasshopper_url=args.grasshopper_url, 
                    port=args.mcp_port,
                    bridge_mode=True
                )
                print(f"🔄 Starting Manual MCP server on port {args.mcp_port} (fallback mode)")
                server.run()
                
            except Exception as e:
                print(f"❌ Manual MCP server also failed: {e}")
                print("💡 Try installing FastMCP: pip install fastmcp")
                exit(1)
    elif args.start_official_mcp:
        from .cli.official_mcp_server import start_official_mcp_server
        import sys
        # Override sys.argv to pass the arguments
        sys.argv = [
            "official-mcp-server",
            "--grasshopper-url", args.grasshopper_url
        ]
        if hasattr(args, 'debug') and args.debug:
            sys.argv.append("--debug")
        start_official_mcp_server()
    elif args.start_mcp_server:
        from .cli.mcp_server import start_mcp_server
        import sys
        # Override sys.argv to pass the port argument
        sys.argv = ["mcp-server", "--port", str(args.mcp_port)]
        start_mcp_server()
    elif args.enhanced_cli:
        from .cli.enhanced_interface import run_enhanced_cli
        run_enhanced_cli(simple_mode=False)
    elif args.interactive:
        interactive_mode(use_legacy=args.legacy, reset_memory=args.reset)
    else:
        # Default to smolagents interactive mode
        logger.info("No specific mode specified - starting default smolagents interactive mode")
        interactive_mode(use_legacy=False, reset_memory=args.reset)


if __name__ == "__main__":
    main()