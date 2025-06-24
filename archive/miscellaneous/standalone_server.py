"""
Standalone monitoring server that runs independently of the main CLI.

This module provides a monitoring dashboard that can be run in a separate
process/terminal, avoiding log pollution in the main CLI interface.
"""

import logging
from typing import Optional

from .server import start_status_monitor, status_tracker

logger = logging.getLogger(__name__)


def run_standalone_monitoring_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool = False
) -> None:
    """
    Run the monitoring server as a standalone process.
    
    This function starts the monitoring dashboard independently of the main
    Bridge Design System, allowing for clean separation of concerns.
    
    Args:
        host: Host to bind to (default: 0.0.0.0 for network access)
        port: Port to bind to (default: 5000)
        debug: Enable debug mode
    """
    logger.info(f"🚀 Starting standalone monitoring server on {host}:{port}")
    logger.info("📊 Agent monitoring system will initialize automatically")
    logger.info(f"🌐 Dashboard will be accessible at http://{host}:{port}")
    
    # Use the existing start_status_monitor function
    try:
        start_status_monitor(host=host, port=port)
    except Exception as e:
        logger.error(f"❌ Failed to start monitoring server: {e}")
        raise


def get_standalone_monitor() -> Optional:
    """
    Get the standalone monitor instance for external agent connections.
    
    This allows agents running in the main process to connect to the
    standalone monitoring server if desired.
    
    Returns:
        Status tracker instance if available, None otherwise
    """
    try:
        return status_tracker
    except:
        return None