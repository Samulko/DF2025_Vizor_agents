#!/usr/bin/env python
"""LCARS Engineering Systems Monitor Interface.

This module provides the Star Trek LCARS-styled monitoring interface
for the bridge design system agents.
"""

from .server import start_status_monitor


def start_lcars_interface(host="0.0.0.0", port=5000):
    """Start the LCARS monitoring interface.

    Args:
        host: Host address to bind to (default: '0.0.0.0' for network access)
        port: Port to bind to (default: 5000)
    """
    print("🚀 Starting LCARS Engineering Systems Monitor...")
    print("⚡ LCARS interface will be available at http://localhost:5000")
    print("🖖 Live long and prosper!")
    start_status_monitor(host=host, port=port)


if __name__ == "__main__":
    start_lcars_interface()
