#!/usr/bin/env python
"""Simple script to start the LCARS monitoring interface."""

from src.bridge_design_system.monitoring.server import start_status_monitor

if __name__ == "__main__":
    print("🚀 Starting LCARS Engineering Systems Monitor...")
    print("⚡ LCARS interface will be available at http://localhost:5000")
    print("🖖 Live long and prosper!")
    start_status_monitor(host='0.0.0.0', port=5000)