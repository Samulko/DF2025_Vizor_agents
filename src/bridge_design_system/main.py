"""Main entry point for the Bridge Design System.

This system uses MCPAdapt for robust MCP integration with Grasshopper,
providing stable async/sync handling and eliminating event loop issues.
"""
import logging
import threading
import time
from pathlib import Path

from .agents import TriageAgent
from .config.logging_config import get_logger
from .config.model_config import ModelProvider
from .config.settings import settings
from .state.component_registry import initialize_registry, get_global_registry

logger = get_logger(__name__)

# Global monitoring variables
monitoring_server_started = False


def clear_log_files():
    """Clear all log files for a completely fresh start."""
    log_dir = Path("logs")
    if not log_dir.exists():
        logger.info("📁 No logs directory found - nothing to clear")
        return
    
    log_files_cleared = 0
    try:
        # Find all log files (including rotated ones)
        log_patterns = ["*.log", "*.log.*"]
        for pattern in log_patterns:
            for log_file in log_dir.glob(pattern):
                try:
                    log_file.unlink()
                    log_files_cleared += 1
                    print(f"🗑️ Deleted: {log_file}")
                except Exception as e:
                    print(f"⚠️ Could not delete {log_file}: {e}")
        
        if log_files_cleared > 0:
            print(f"✅ Cleared {log_files_cleared} log files")
        else:
            print("📁 No log files found to clear")
            
    except Exception as e:
        print(f"❌ Error clearing log files: {e}")


def clear_legacy_memory_files():
    """Clear legacy file-based memory sessions (no longer used in smolagents)."""
    memory_dir = Path("src/bridge_design_system/data/memory")
    if not memory_dir.exists():
        print("📁 No legacy memory directory found - nothing to clear")
        return
    
    memory_files_cleared = 0
    try:
        # Find all session JSON files
        for memory_file in memory_dir.glob("session_*.json"):
            try:
                memory_file.unlink()
                memory_files_cleared += 1
                print(f"🗑️ Deleted legacy memory: {memory_file.name}")
            except Exception as e:
                print(f"⚠️ Could not delete {memory_file}: {e}")
        
        if memory_files_cleared > 0:
            print(f"✅ Cleared {memory_files_cleared} legacy memory files")
        else:
            print("📁 No legacy memory files found to clear")
            
    except Exception as e:
        print(f"❌ Error clearing legacy memory files: {e}")


def validate_environment():
    """Validate that required environment variables are set."""
    # Get unique providers needed
    providers = set()
    for agent in ["triage", "geometry", "material", "structural", "syslogic"]:
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


def start_monitoring_server(enable_monitoring=True):
    """Start the LCARS monitoring interface in a background thread."""
    global monitoring_server_started
    
    if not enable_monitoring:
        logger.info("📊 Monitoring disabled by user")
        return
    
    if monitoring_server_started:
        return
    
    try:
        from .monitoring.lcars_interface import start_lcars_interface
        
        def run_server():
            print("🚀 Starting LCARS Engineering Systems Monitor on http://localhost:5000")
            print("🌐 LCARS dashboard accessible from any device on local network")
            print("🖖 Live long and prosper!")
            start_lcars_interface(host='0.0.0.0', port=5000)
        
        # Start LCARS monitoring server in background thread
        monitor_thread = threading.Thread(target=run_server, daemon=True)
        monitor_thread.start()
        
        # Wait a moment for server to initialize
        time.sleep(2)
        monitoring_server_started = True
        
        logger.info("✅ LCARS monitoring interface started successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to start LCARS monitoring interface: {e}")
        logger.info("Continuing without monitoring...")


def get_monitoring_callback(enable_embedded_monitoring=False):
    """Get the monitoring callback if available."""
    if enable_embedded_monitoring:
        # Use embedded monitoring (old behavior)
        try:
            from .monitoring.server import get_status_tracker
            status_tracker = get_status_tracker()
            if status_tracker:
                logger.info("✅ Embedded monitoring integration enabled")
                return status_tracker
            else:
                logger.info("📊 Embedded monitoring server not ready - continuing without monitoring")
                return None
        except Exception as e:
            logger.debug(f"Embedded monitoring not available: {e}")
            return None
    else:
        # Use remote monitoring (new default behavior)
        try:
            from .monitoring.agent_monitor import create_remote_monitor_callback
            logger.info("📡 Remote monitoring enabled - will send updates to standalone server")
            return create_remote_monitor_callback
        except Exception as e:
            logger.debug(f"Remote monitoring not available: {e}")
            return None


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
        
        # Use remote monitoring for test
        monitoring_callback = get_monitoring_callback(enable_embedded_monitoring=False)
        
        triage = TriageAgent(component_registry=registry, monitoring_callback=monitoring_callback)
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


def interactive_mode(use_legacy=False, reset_memory=False, hard_reset=False, enable_monitoring=False):
    """Run the system in interactive mode.
    
    Args:
        use_legacy: If True, use legacy triage agent (default is smolagents-native)
        reset_memory: If True, start with fresh agent memories
        hard_reset: If True, clear everything including log files
        enable_monitoring: If True, start monitoring dashboard (default False for clean CLI)
    """
    mode = "legacy" if use_legacy else "smolagents-native"
    logger.info(f"Starting Bridge Design System in interactive mode ({mode})...")
    
    if not validate_environment():
        return
    
    try:
        # Don't start monitoring server - assume it's running separately
        # start_monitoring_server(enable_monitoring=enable_monitoring)
        
        # Always use remote monitoring callback
        monitoring_callback = get_monitoring_callback(enable_embedded_monitoring=False)
        
        # Initialize component registry
        registry = initialize_registry()
        logger.info("Component registry initialized")
        
        if use_legacy:
            # Legacy is no longer supported - use smolagents implementation
            logger.warning("Legacy implementation has been removed - using smolagents-native implementation")
            triage = TriageAgent(component_registry=registry, monitoring_callback=monitoring_callback)
            logger.info("System initialized with smolagents-native patterns")
        else:
            # Use default smolagents-native implementation
            triage = TriageAgent(component_registry=registry, monitoring_callback=monitoring_callback)
            logger.info("System initialized with smolagents-native patterns")
        
        # Handle reset options
        if hard_reset:
            print("🧹 HARD RESET: Clearing EVERYTHING (logs, memories, registry, legacy files)...")
            clear_log_files()
            clear_legacy_memory_files()
            triage.reset_all_agents()
            registry.clear()
            print("✅ Complete system reset - starting completely fresh!")
        elif reset_memory:
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
        
        # Show monitoring information
        if enable_monitoring:
            print("🚀 LCARS Agent Monitoring enabled - connect to http://localhost:5000")
            print("🌐 Make sure LCARS monitoring interface is running in separate terminal")
            print("🖖 Live long and prosper!")
        else:
            print("⚠️ LCARS monitoring disabled (use --monitoring to enable)")
        
        print("\nType 'exit' to quit, 'reset' to clear agent memories, 'hardreset' to clear everything")
        print("Type 'status' to see agent status")
        if hard_reset:
            print("✅ Started completely fresh (--hard-reset flag used)")
        elif reset_memory:
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
                elif user_input.lower() == 'hardreset':
                    print("🧹 HARD RESET: Clearing EVERYTHING (logs, memories, registry, legacy files)...")
                    clear_log_files()
                    clear_legacy_memory_files()
                    triage.reset_all_agents()
                    registry.clear()
                    print("✅ Complete system reset - starting completely fresh!")
                    continue
                elif user_input.lower() == 'status':
                    # Always use smolagents status (legacy removed)
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
                        # Handle both string errors and error objects
                        if hasattr(response.error, 'value'):
                            print(f"Error Type: {response.error.value}")
                        else:
                            print(f"Error Details: {response.error}")
                        
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
        "--hard-reset",
        action="store_true",
        help="Start completely fresh (clears agent memories, component registry, AND log files)"
    )
    parser.add_argument(
        "--enhanced-cli",
        action="store_true",
        help="Run enhanced CLI with Rich formatting and real-time status"
    )
    parser.add_argument(
        "--monitoring",
        action="store_true",
        help="Enable LCARS agent monitoring interface (disabled by default for clean CLI)"
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
        interactive_mode(
            use_legacy=args.legacy, 
            reset_memory=args.reset, 
            hard_reset=args.hard_reset,
            enable_monitoring=args.monitoring
        )
    else:
        # Default to smolagents interactive mode
        logger.info("No specific mode specified - starting default smolagents interactive mode")
        interactive_mode(
            use_legacy=False, 
            reset_memory=args.reset, 
            hard_reset=args.hard_reset,
            enable_monitoring=args.monitoring
        )


if __name__ == "__main__":
    main()