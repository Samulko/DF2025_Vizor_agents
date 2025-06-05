"""Main entry point for the Bridge Design System."""
import logging
from pathlib import Path

from .agents.triage_agent import TriageAgent
from .config.logging_config import get_logger
from .config.model_config import ModelProvider
from .config.settings import settings

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
        triage = TriageAgent()
        triage.initialize_agent()
        logger.info("✓ Triage agent initialized successfully")
        
        # Test basic operation
        logger.info("\nTesting basic operation...")
        response = triage.handle_design_request(
            "Hello, I'd like to test the system. Can you tell me what agents are available?"
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


def interactive_mode():
    """Run the system in interactive mode."""
    logger.info("Starting Bridge Design System in interactive mode...")
    
    if not validate_environment():
        return
    
    try:
        # Initialize triage agent
        triage = TriageAgent()
        triage.initialize_agent()
        logger.info("System initialized successfully")
        
        print("\n" + "="*60)
        print("AR-Assisted Bridge Design System")
        print("="*60)
        print("\nType 'exit' to quit, 'reset' to clear conversation")
        print("Type 'status' to see agent status\n")
        
        while True:
            try:
                user_input = input("\nDesigner> ").strip()
                
                if user_input.lower() == 'exit':
                    print("Exiting Bridge Design System...")
                    break
                elif user_input.lower() == 'reset':
                    triage.reset_all_agents()
                    print("All agents reset.")
                    continue
                elif user_input.lower() == 'status':
                    status = triage.get_agent_status()
                    print("\nAgent Status:")
                    for agent, info in status.items():
                        print(f"  {agent}: Steps={info['step_count']}, Initialized={info['initialized']}")
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
    
    parser = argparse.ArgumentParser(description="Bridge Design System")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run system test"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    if args.test:
        success = test_system()
        exit(0 if success else 1)
    elif args.interactive:
        interactive_mode()
    else:
        # Default to interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()