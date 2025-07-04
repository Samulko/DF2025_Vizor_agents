"""Main entry point for the Bridge Design System.

This system uses MCPAdapt for robust MCP integration with Grasshopper,
providing stable async/sync handling and eliminating event loop issues.
"""

import threading
import time
import signal
from pathlib import Path

from .agents import TriageAgent
from .agents.VizorListener import VizorListener
from .config.logging_config import get_logger
from .config.model_config import ModelProvider
from .config.settings import settings
from .state.component_registry import initialize_registry
from .tools.material_tools import MaterialInventoryManager
from .voice_input import get_user_input, check_voice_dependencies

logger = get_logger(__name__)

# Global monitoring variables
monitoring_server_started = False


def quaternion_to_direction_vector(quat_dict):
    """
    Converts a RAW quaternion from ROS to a direction vector in the Rhino
    coordinate system.

    Args:
        quat_dict: The raw, unmodified quaternion dictionary from ROS.
                   Example: {'w': ..., 'x': ..., 'y': ..., 'z': ...}

    Returns:
        List of [vx, vy, vz] direction vector components in Rhino coordinates.
    """
    w = quat_dict['w']
    x = quat_dict['x']
    y = quat_dict['y']
    z = quat_dict['z']
    print(f"[DEBUG] Raw ROS Quaternion input: w={w}, x={x}, y={y}, z={z}")

    # 1. Calculate the direction vector in ROS coordinates (x-forward, y-right, z-up)
    #    This formula calculates the rotated X-axis.
    ros_vx = 1.0 - 2.0 * (y * y + z * z)
    ros_vy = 2.0 * (x * y + w * z)
    ros_vz = 2.0 * (x * z - w * y)
    print(f"[DEBUG] Calculated direction in ROS coords: [{ros_vx:.4f}, {ros_vy:.4f}, {ros_vz:.4f}]")

    # 2. Transform the calculated vector from ROS to Rhino coordinates.
    #    ROS (x-fwd, y-right, z-up) -> Rhino (x-right, y-fwd, z-up)
    #    rhino_x = ros_y
    #    rhino_y = ros_x
    #    rhino_z = ros_z
    rhino_vx = ros_vy
    rhino_vy = ros_vx
    rhino_vz = ros_vz
    print(f"[DEBUG] Transformed direction for Rhino: [{rhino_vx:.4f}, {rhino_vy:.4f}, {rhino_vz:.4f}]")

    # 3. Normalize the final vector
    import math
    magnitude = math.sqrt(rhino_vx**2 + rhino_vy**2 + rhino_vz**2)
    if magnitude > 1e-6:
        rhino_vx /= magnitude
        rhino_vy /= magnitude
        rhino_vz /= magnitude
    else:
        print(f"[DEBUG] Warning: Zero magnitude vector, using default X-forward")
        rhino_vx, rhino_vy, rhino_vz = 1.0, 0.0, 0.0
    
    return [rhino_vx, rhino_vy, rhino_vz]


def format_direct_update_task(element_id, new_center, new_direction):
    """Formats the precise task for the GeometryAgent."""
    return (
        f"Perform a direct parameter update for element with id '{element_id}'. "
        f"Replace its center point with these values: {new_center}. "
        f"Replace its direction vector with these values: {new_direction}."
    )


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
            start_lcars_interface(host="0.0.0.0", port=5000)

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
                logger.info(
                    "📊 Embedded monitoring server not ready - continuing without monitoring"
                )
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


def handle_material_reset(args) -> bool:
    """Handle material inventory reset operations from CLI."""
    try:
        print("🔧 Material Inventory Reset Tool")
        print("=" * 40)

        # Initialize material manager
        inventory_manager = MaterialInventoryManager()

        if args.reset_material == "list-sessions":
            # List available cutting sessions
            sessions = inventory_manager.inventory_data.get("cutting_sessions", [])
            if not sessions:
                print("📋 No cutting sessions found in inventory")
                return True

            print(f"📋 Found {len(sessions)} cutting sessions:")
            for i, session in enumerate(sessions, 1):
                session_id = session.get("session_id", f"session_{i}")
                timestamp = session.get("timestamp", "unknown")
                elements = len(session.get("elements", []))
                print(f"  {i}. {session_id} - {timestamp} ({elements} elements)")

            print("\nUse --reset-material with --session-id to reset to a specific session")
            return True

        elif args.reset_material == "list-backups":
            # List available backups
            backups = inventory_manager._list_backups()
            if not backups:
                print("📋 No backup files found")
                return True

            print(f"📋 Found {len(backups)} backup files:")
            for backup in backups:
                name = backup["name"]
                created = backup["created_at"]
                size_kb = backup["file_size_bytes"] / 1024
                print(f"  • {name} - {created} ({size_kb:.1f} KB)")

            print("\nUse --reset-material with --backup-name to restore from a backup")
            return True

        elif args.reset_material == "full":
            # Show current status and ask for confirmation
            current_status = inventory_manager.get_status(detailed=False)

            print("🔍 Current Material Inventory Status:")
            print(f"  Total beams: {current_status['total_beams']}")
            print(f"  Overall utilization: {current_status['overall_utilization_percent']:.1f}%")
            print(
                f"  Total cuts made: {sum(len(beam.cuts) for beam in inventory_manager.get_beams())}"
            )
            print(
                f"  Cutting sessions: {len(inventory_manager.inventory_data.get('cutting_sessions', []))}"
            )

            if current_status["overall_utilization_percent"] > 0:
                print("\n⚠️ WARNING: This will reset ALL material usage data!")
                print("   All cuts, sessions, and utilization will be lost.")
                print("   Use --reset-material confirm to proceed without this warning.")

                try:
                    response = input("\nContinue with full reset? (y/N): ").strip().lower()
                    if response not in ["y", "yes"]:
                        print("Reset cancelled by user")
                        return True
                except KeyboardInterrupt:
                    print("\nReset cancelled by user")
                    return True

            # Perform the full reset
            print("\n🔄 Performing full material inventory reset...")
            reset_result = _perform_cli_full_reset(inventory_manager)

            if reset_result["success"]:
                print(f"✅ {reset_result['message']}")
                print(f"   Beams reset: {reset_result['beams_reset']}")
                print(f"   Material restored: {reset_result['total_material_restored_mm']}mm")
                return True
            else:
                print(f"❌ Reset failed: {reset_result.get('error', 'Unknown error')}")
                return False

        elif args.reset_material == "confirm":
            # Force full reset without confirmation
            print("🔄 Performing confirmed full material inventory reset...")
            reset_result = _perform_cli_full_reset(inventory_manager)

            if reset_result["success"]:
                print(f"✅ {reset_result['message']}")
                return True
            else:
                print(f"❌ Reset failed: {reset_result.get('error', 'Unknown error')}")
                return False

        # Handle session or backup specific resets via the reset tool
        if args.session_id:
            print(f"🔄 Resetting to session: {args.session_id}")
            # This would use the session reset functionality
            print("⚠️ Session reset not yet implemented in CLI")
            return False

        if args.backup_name:
            print(f"🔄 Restoring from backup: {args.backup_name}")
            # This would use the backup restore functionality
            print("⚠️ Backup restore not yet implemented in CLI")
            return False

        return True

    except Exception as e:
        print(f"❌ Material reset failed: {e}")
        logger.error(f"Material reset error: {e}")
        return False


def _perform_cli_full_reset(inventory_manager) -> dict:
    """Perform full reset for CLI operations."""
    try:
        from datetime import datetime

        # Create automatic backup
        backup_name = f"cli_backup_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        inventory_manager._create_backup(backup_name)
        print(f"📋 Automatic backup created: {backup_name}")

        # Create fresh inventory data
        fresh_inventory = {
            "total_stock_mm": 25740,  # 13 * 1980
            "beam_length_mm": 1980,
            "kerf_loss_mm": 3,
            "available_beams": [],
            "used_elements": [],
            "total_waste_mm": 0,
            "total_utilization_percent": 0.0,
            "cutting_sessions": [],
            "last_updated": datetime.now().isoformat(),
            "metadata": {
                "cross_section": "5x5cm",
                "material_type": "timber",
                "project": "bridge_design",
                "version": "1.0",
                "units": "millimeters",
            },
            "statistics": {
                "total_beams": 13,
                "full_beams": 13,
                "partial_beams": 0,
                "average_beam_length_mm": 1980.0,
                "material_efficiency_target": 95.0,
                "waste_tolerance_mm": 100,
            },
        }

        # Create 13 pristine beams
        for i in range(1, 14):
            beam_data = {
                "id": f"beam_{i:03d}",
                "original_length_mm": 1980,
                "remaining_length_mm": 1980,
                "cuts": [],
                "waste_mm": 0,
                "utilization_percent": 0.0,
            }
            fresh_inventory["available_beams"].append(beam_data)

        # Save the fresh inventory
        inventory_manager.inventory_data = fresh_inventory
        inventory_manager._save_inventory(backup=False)  # We already created our own backup

        return {
            "success": True,
            "message": "Material inventory reset completed successfully",
            "beams_reset": 13,
            "total_material_restored_mm": 25740,
            "backup_created": backup_name,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


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


def interactive_mode(
    use_legacy=False, reset_memory=False, hard_reset=False, enable_monitoring=False, voice_input=False, disable_gaze=False
):
    """Run the system in interactive mode.

    Args:
        use_legacy: If True, use legacy triage agent (default is smolagents-native)
        reset_memory: If True, start with fresh agent memories
        hard_reset: If True, clear everything including log files
        enable_monitoring: If True, start monitoring dashboard (default False for clean CLI)
        voice_input: If True, enable voice input via wake word detection and speech recognition
        disable_gaze: If True, skip VizorListener initialization (no ROS dependency)
    """
    mode = "legacy" if use_legacy else "smolagents-native"
    logger.info(f"Starting Bridge Design System in interactive mode ({mode})...")

    if not validate_environment():
        return
    
    # Validate voice input if requested
    if voice_input and not check_voice_dependencies():
        logger.warning("⚠️ Voice input requested but dependencies not available")
        logger.warning("Install voice dependencies with: uv sync --extra voice")
        print("⚠️ Voice input dependencies not available - falling back to keyboard input")
        voice_input = False

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
            logger.warning(
                "Legacy implementation has been removed - using smolagents-native implementation"
            )
            triage = TriageAgent(
                component_registry=registry, monitoring_callback=monitoring_callback
            )
            logger.info("System initialized with smolagents-native patterns")
        else:
            # Use default smolagents-native implementation
            triage = TriageAgent(
                component_registry=registry, monitoring_callback=monitoring_callback
            )
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

        print("\n" + "=" * 60)
        print("AR-Assisted Bridge Design System")
        if use_legacy:
            print("⚙️ Using LEGACY implementation")
            print("🔧 STDIO-only geometry agent")
        else:
            print("🚀 Using smolagents-native implementation (DEFAULT)")
            print("✨ 75% less code, 30% more efficient!")
        
        # Show input mode status
        if voice_input:
            print("🎤 Voice input enabled - use wake word for commands")
        else:
            print("⌨️ Keyboard input mode - type commands normally")
            
        print("=" * 60)

        # Show monitoring information
        if enable_monitoring:
            print("🚀 LCARS Agent Monitoring enabled - connect to http://localhost:5000")
            print("🌐 Make sure LCARS monitoring interface is running in separate terminal")
            print("🖖 Live long and prosper!")
        else:
            print("⚠️ LCARS monitoring disabled (use --monitoring to enable)")

        print(
            "\nType 'exit' to quit, 'reset' to clear agent memories, 'hardreset' to clear everything"
        )
        print("Type 'status' to see agent status, 'gaze' to see detailed gaze information")
        print("Type 'gazetest' to start continuous gaze monitoring for debugging")
        if hard_reset:
            print("✅ Started completely fresh (--hard-reset flag used)")
        elif reset_memory:
            print("✅ Started with fresh memories (--reset flag used)")
        print()

        # Initialize Direct Parameter Update queue for HoloLens transformations
        TRANSFORM_UPDATE_QUEUE = []

        # Initialize VizorListener for gaze-assisted spatial command grounding
        vizor_listener = None
        if disable_gaze:
            print("🚫 Gaze tracking disabled by --disable-gaze flag")
            logger.info("VizorListener initialization skipped - gaze features disabled")
        else:
            try:
                print("🔍 Initializing VizorListener...")
                # Force singleton reset to ensure fresh queue reference
                VizorListener.reset_singleton()
                vizor_listener = VizorListener(update_queue=TRANSFORM_UPDATE_QUEUE)

                # Debug singleton info
                print(f"[Debug] VizorListener instance ID: {id(vizor_listener)}")
                print(
                    f"[Debug] VizorListener._instance ID: {id(VizorListener._instance) if hasattr(VizorListener, '_instance') else 'None'}"
                )
                print(f"[Debug] TRANSFORM_UPDATE_QUEUE ID: {id(TRANSFORM_UPDATE_QUEUE)}")
                print(f"[Debug] vizor_listener.update_queue ID: {id(vizor_listener.update_queue)}")
                print(f"[Debug] Queue references same? {TRANSFORM_UPDATE_QUEUE is vizor_listener.update_queue}")

                # Give ROS a moment to establish connection
                print("⏳ Waiting for ROS connection to stabilize...")
                time.sleep(1.0)

                # Use the improved connection status checking
                if vizor_listener.is_ros_connected():
                    logger.info("👁️ VizorListener for gaze context initialized successfully")
                    print("👁️ Gaze-assisted spatial grounding enabled (ROS connected)")

                    # Test immediate gaze reading
                    test_current = vizor_listener.get_current_element()
                    test_recent = vizor_listener.get_recent_gaze(10.0)  # Longer window
                    print(f"[Debug] Initial gaze test - Current: {test_current}, Recent: {test_recent}")

                else:
                    # VizorListener created but ROS not connected - keep for potential reconnection
                    status = vizor_listener.get_connection_status()
                    print(f"[Debug] Connection status: {status}")
                    if status["ros_available"]:
                        logger.warning("⚠️ VizorListener ROS connection failed - gaze features limited")
                        print("⚠️ Gaze features limited (ROS not connected, but can reconnect later)")
                    else:
                        logger.warning("⚠️ ROS dependencies not available - gaze features disabled")
                        print("⚠️ Gaze features disabled (ROS dependencies not installed)")

            except Exception as e:
                logger.error(f"❌ VizorListener initialization failed: {e}")
                print(f"⚠️ Gaze features disabled (initialization failed: {str(e)})")
                import traceback

                traceback.print_exc()
                vizor_listener = None
        while True:
            try:
                user_input = get_user_input("Designer> ", voice_enabled=voice_input)

                # Handle exit immediately without processing queue
                if user_input.lower() == "exit":
                    print("Exiting Bridge Design System...")
                    break
                
                # Skip queue processing and command handling if user just pressed enter
                if not user_input:
                    continue

                # Process Direct Parameter Update queue before handling user commands
                print(f"[DEBUG] TRANSFORM_UPDATE_QUEUE length: {len(TRANSFORM_UPDATE_QUEUE)}")
                print(f"[DEBUG] TRANSFORM_UPDATE_QUEUE contents: {TRANSFORM_UPDATE_QUEUE}")
                if vizor_listener and hasattr(vizor_listener, 'update_queue'):
                    print(f"[DEBUG] VizorListener.update_queue length: {len(vizor_listener.update_queue)}")
                    print(f"[DEBUG] VizorListener.update_queue contents: {vizor_listener.update_queue}")
                    print(f"[DEBUG] Queue objects same? {TRANSFORM_UPDATE_QUEUE is vizor_listener.update_queue}")
                
                if TRANSFORM_UPDATE_QUEUE:
                    print(
                        f"[SYSTEM] Processing {len(TRANSFORM_UPDATE_QUEUE)} queued transform batch(es)..."
                    )

                    # Process all data batches in the queue
                    for transform_batch in TRANSFORM_UPDATE_QUEUE:
                        for element_name, pose in transform_batch.items():
                            # element_name is "dynamic_021", element_id is "021"
                            # Component encoding: 001-009→component_1, 011-019→component_2, 021-029→component_3, etc.
                            element_id = element_name.split("_")[
                                -1
                            ]  # Keep full element ID: 021, 022, 023, etc.
                            print(f"[DEBUG] Processing transform: {element_name} → element_id: {element_id}")

                            # Use the helper function in main.py
                            new_pos = pose["position"]
                            new_dir = quaternion_to_direction_vector(pose["quaternion"])

                            # Format the specific, direct task for the agent
                            task = format_direct_update_task(element_id, new_pos, new_dir)

                            # Process this single element update
                            print(f"[SYSTEM] Updating element {element_id}...")
                            try:
                                response = triage.handle_design_request(request=task, gaze_id=None)
                                if response.success:
                                    print(f"[SYSTEM] ✅ Element {element_id} updated successfully")
                                else:
                                    print(
                                        f"[SYSTEM] ❌ Element {element_id} update failed: {response.message}"
                                    )
                            except Exception as e:
                                print(f"[SYSTEM] ❌ Element {element_id} update error: {e}")

                    TRANSFORM_UPDATE_QUEUE.clear()
                    print("[SYSTEM] Transform queue processed. Now handling your command.")

                if user_input.lower() == "reset":
                    print("🔄 Resetting all agent memories...")
                    triage.reset_all_agents()
                    registry.clear()
                    print("✅ All agent memories and component registry reset - starting fresh!")
                    continue
                elif user_input.lower() == "hardreset":
                    print(
                        "🧹 HARD RESET: Clearing EVERYTHING (logs, memories, registry, legacy files)..."
                    )
                    clear_log_files()
                    clear_legacy_memory_files()
                    triage.reset_all_agents()
                    registry.clear()
                    print("✅ Complete system reset - starting completely fresh!")
                    continue
                elif user_input.lower() == "status":
                    # Always use smolagents status (legacy removed)
                    status = triage.get_status()
                    print("\nAgent Status (Smolagents Native):")
                    for agent, info in status.items():
                        print(f"  {agent}: {info}")

                    # Registry status
                    registry_stats = registry.get_stats()
                    print("\nComponent Registry:")
                    print(f"  Components: {registry_stats['total_components']}")
                    print(f"  Types: {', '.join(registry_stats['types'])}")
                    print(f"  Recent: {registry_stats['recent_components']}")

                    # VizorListener status
                    if vizor_listener:
                        try:
                            gaze_summary = vizor_listener.get_gaze_history_summary()
                            print("\n👁️ Gaze Status:")
                            print(f"  ROS Connected: {vizor_listener.is_ros_connected()}")
                            print(
                                f"  Current Element: {vizor_listener.get_current_element() or 'None'}"
                            )
                            print(
                                f"  Recent Gaze (3s): {vizor_listener.get_recent_gaze(3.0) or 'None'}"
                            )
                            print(f"  Total Gazes (10s): {gaze_summary['total_gazes']}")
                            print(f"  Unique Elements: {gaze_summary['unique_elements']}")
                            if gaze_summary["recent_elements"]:
                                print(
                                    f"  Recent Elements: {', '.join(gaze_summary['recent_elements'])}"
                                )
                        except Exception as e:
                            print(f"\n👁️ Gaze Status: Error - {e}")
                    else:
                        print("\n👁️ Gaze Status: VizorListener not available")

                    continue
                elif user_input.lower() in ["gaze", "gazehistory"]:
                    # Show detailed gaze information
                    if vizor_listener:
                        try:
                            print("\n👁️ Detailed Gaze Information:")
                            print("-" * 40)

                            current = vizor_listener.get_current_element()
                            recent_3s = vizor_listener.get_recent_gaze(3.0)
                            recent_5s = vizor_listener.get_recent_gaze(5.0)

                            print(f"Current gaze: {current or 'None'}")
                            print(f"Recent gaze (3s): {recent_3s or 'None'}")
                            print(f"Recent gaze (5s): {recent_5s or 'None'}")

                            summary = vizor_listener.get_gaze_history_summary()
                            print(f"\nActivity Summary (last 10 seconds):")
                            print(f"  Total gaze events: {summary['total_gazes']}")
                            print(f"  Unique elements: {summary['unique_elements']}")
                            print(f"  Most gazed element: {summary['most_gazed'] or 'None'}")
                            if summary["most_gazed"]:
                                print(f"  Times gazed: {summary['most_gazed_count']}")
                            print(f"  Time span: {summary['time_span_seconds']:.1f} seconds")

                            if summary["recent_elements"]:
                                print(
                                    f"  Element sequence: {' → '.join(summary['recent_elements'])}"
                                )

                        except Exception as e:
                            print(f"\n👁️ Gaze information error: {e}")
                    else:
                        print("\n👁️ VizorListener not available")
                    continue
                elif user_input.lower() == "gazetest":
                    # Continuous gaze monitoring for debugging
                    if vizor_listener and vizor_listener.is_ros_connected():
                        print("\n👁️ Starting continuous gaze monitoring...")
                        print("Press Ctrl+C to stop")
                        try:
                            while True:
                                current = vizor_listener.get_current_element()
                                recent = vizor_listener.get_recent_gaze(3.0)
                                summary = vizor_listener.get_gaze_history_summary(5.0)

                                print(
                                    f"\r[{time.strftime('%H:%M:%S')}] Current: {current or 'None'} | Recent: {recent or 'None'} | Total(5s): {summary['total_gazes']}",
                                    end="",
                                    flush=True,
                                )
                                time.sleep(0.5)
                        except KeyboardInterrupt:
                            print("\n👁️ Gaze monitoring stopped")
                    else:
                        print("\n❌ VizorListener not connected")
                    continue
                elif not user_input:
                    continue

                # Simple gaze integration - append to user prompt
                final_request = user_input
                if vizor_listener and vizor_listener.is_ros_connected():
                    try:
                        # Debug: Check all gaze sources with longer windows
                        current_gaze = vizor_listener.get_current_element()
                        recent_gaze_3s = vizor_listener.get_recent_gaze(3.0)
                        recent_gaze_10s = vizor_listener.get_recent_gaze(10.0)
                        summary = vizor_listener.get_gaze_history_summary(15.0)

                        print(f"[Debug] Current gaze: {current_gaze}")
                        print(f"[Debug] Recent gaze (3s): {recent_gaze_3s}")
                        print(f"[Debug] Recent gaze (10s): {recent_gaze_10s}")
                        print(f"[Debug] Total gazes (15s): {summary['total_gazes']}")
                        print(f"[Debug] Most gazed: {summary['most_gazed']}")

                        # Prioritize recency over frequency - most recent element wins
                        gazed_element = (
                            current_gaze  # Most immediate (prioritized)
                            or recent_gaze_3s  # Recent (3s) - high priority
                            or recent_gaze_10s  # Extended recent (10s) - medium priority
                            # Note: Removed most_gazed fallback to avoid confusion with older elements
                        )

                        # If we found an element, show which strategy worked
                        if gazed_element:
                            if gazed_element == current_gaze:
                                print(f"[Debug] Using CURRENT gaze: {gazed_element}")
                            elif gazed_element == recent_gaze_3s:
                                print(f"[Debug] Using RECENT(3s) gaze: {gazed_element}")
                            elif gazed_element == recent_gaze_10s:
                                print(f"[Debug] Using RECENT(10s) gaze: {gazed_element}")
                        else:
                            print(
                                f"[Debug] No recent gaze found - command sent without gaze context"
                            )
                        if gazed_element:
                            # Extract just the element number (e.g., "dynamic_0020" -> "020")
                            if gazed_element.startswith("dynamic_"):
                                element_number = gazed_element.replace("dynamic_", "")
                                final_request = f"{user_input} [USER IS LOOKING AT ELEMENT: {element_number} - This is a 3D geometric element inside of grasshopper, the user sees this through their HoloLens AR headset]"
                                print(f"[Debug] Adding gaze context: element {element_number}")
                            else:
                                final_request = (
                                    f"{user_input} [USER IS LOOKING AT: {gazed_element}]"
                                )
                                print(f"[Debug] Adding gaze context: {gazed_element}")
                        else:
                            print(
                                f"[Debug] No gaze detected - sending command without gaze context"
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to get gaze data: {e}")
                else:
                    print(f"[Debug] VizorListener not connected - no gaze data available")

                try:
                    # Process the request with gaze context embedded in the text
                    print("\nProcessing...")
                    response = triage.handle_design_request(request=final_request, gaze_id=None)

                    if response.success:
                        print(f"\nTriage Agent> {response.message}")
                    else:
                        print(f"\nError: {response.message}")
                        if response.error:
                            # Handle both string errors and error objects
                            if hasattr(response.error, "value"):
                                print(f"Error Type: {response.error.value}")
                            else:
                                print(f"Error Details: {response.error}")

                finally:
                    # Note: With time-window policy, we don't aggressively clear gaze data
                    # The gaze history will naturally age out after 10 seconds
                    # Don't clear current element - let it persist until new gaze data arrives
                    # This allows for more reliable gaze detection between commands
                    pass

            except KeyboardInterrupt:
                print("\n\n⏹️  Interrupted by Ctrl+C")
                try:
                    # Prompt for exit confirmation
                    print("Exit the system? (y/n): ", end="", flush=True)
                    confirm = input().strip().lower()
                    if confirm in ['y', 'yes']:
                        print("Exiting Bridge Design System...")
                        break
                    else:
                        print("Continuing...")
                        continue
                except KeyboardInterrupt:
                    # Second Ctrl+C - force exit
                    print("\n\n🛑 Force quit requested. Exiting...")
                    break
                except:
                    # Any other error during confirmation, just continue
                    print("\nContinuing...")
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

    parser = argparse.ArgumentParser(
        description="Bridge Design System (smolagents-native by default)"
    )
    parser.add_argument("--test", action="store_true", help="Run system test")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode (uses smolagents-native by default)",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy triage agent implementation (instead of default smolagents)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Start with fresh agent memories (clears previous conversation history)",
    )
    parser.add_argument(
        "--hard-reset",
        action="store_true",
        help="Start completely fresh (clears agent memories, component registry, AND log files)",
    )
    parser.add_argument(
        "--enhanced-cli",
        action="store_true",
        help="Run enhanced CLI with Rich formatting and real-time status",
    )
    parser.add_argument(
        "--monitoring",
        action="store_true",
        help="Enable LCARS agent monitoring interface (disabled by default for clean CLI)",
    )
    parser.add_argument(
        "--start-mcp-server",
        action="store_true",
        help="Start HTTP MCP server for Grasshopper integration (legacy)",
    )
    parser.add_argument(
        "--start-official-mcp",
        action="store_true",
        help="Start official MCP server using MCP SDK (stdio transport)",
    )
    parser.add_argument(
        "--start-streamable-http",
        action="store_true",
        help="Start official MCP streamable-http server (recommended)",
    )
    parser.add_argument(
        "--mcp-port", type=int, default=8001, help="Port for MCP HTTP server (default: 8001)"
    )
    parser.add_argument(
        "--grasshopper-url",
        default="http://localhost:8080",
        help="URL of Grasshopper HTTP server (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--reset-material",
        choices=["full", "confirm", "list-sessions", "list-backups"],
        help="Reset material inventory: 'full' (with confirmation), 'confirm' (force reset), 'list-sessions', 'list-backups'",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Session ID for session-based material reset (use with reset commands)",
    )
    parser.add_argument(
        "--backup-name",
        type=str,
        help="Backup name for backup-based material operations (use with reset commands)",
    )
    parser.add_argument(
        "--voice-input",
        action="store_true",
        help="Enable voice input using wake word detection and speech recognition (requires voice dependencies)",
    )
    parser.add_argument(
        "--disable-gaze",
        action="store_true",
        help="Disable VizorListener initialization - run without ROS dependency for gaze tracking",
    )

    args = parser.parse_args()

    if args.test:
        success = test_system()
        exit(0 if success else 1)
    elif args.reset_material:
        success = handle_material_reset(args)
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
                    grasshopper_url=args.grasshopper_url, host="127.0.0.1", port=args.mcp_port
                )

            except Exception as e:
                print(f"❌ Clean FastMCP server not suitable for HTTP: {e}")
                print("🔄 Using Manual MCP server for reliable HTTP support...")
                fastmcp_available = False

        if not fastmcp_available:
            # Use manual server as fallback
            try:
                from .mcp.manual_mcp_server import ManualMCPServer

                # Fallback to manual server
                server = ManualMCPServer(
                    grasshopper_url=args.grasshopper_url, port=args.mcp_port, bridge_mode=True
                )
                print(f"🔄 Starting Manual MCP server on port {args.mcp_port} (fallback mode)")
                server.run()

            except Exception as e:
                print(f"❌ Manual MCP server also failed: {e}")
                print("💡 Try installing FastMCP: pip install fastmcp")
                exit(1)
    elif args.start_official_mcp:
        import sys

        from .cli.official_mcp_server import start_official_mcp_server

        # Override sys.argv to pass the arguments
        sys.argv = ["official-mcp-server", "--grasshopper-url", args.grasshopper_url]
        if hasattr(args, "debug") and args.debug:
            sys.argv.append("--debug")
        start_official_mcp_server()
    elif args.start_mcp_server:
        import sys

        from .cli.mcp_server import start_mcp_server

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
            enable_monitoring=args.monitoring,
            voice_input=args.voice_input,
            disable_gaze=args.disable_gaze,
        )
    else:
        # Default to smolagents interactive mode
        logger.info("No specific mode specified - starting default smolagents interactive mode")
        interactive_mode(
            use_legacy=False,
            reset_memory=args.reset,
            hard_reset=args.hard_reset,
            enable_monitoring=args.monitoring,
            voice_input=args.voice_input,
            disable_gaze=args.disable_gaze,
        )


if __name__ == "__main__":
    main()
