"""
Inter-Process Communication (IPC) module for Bridge Design System.

Provides TCP-based communication between the main bridge design system
and external interfaces like voice chat agents.
"""

from .command_server import (
    BridgeCommandServer,
    CommandRequest,
    CommandResponse,
    get_command_server,
    start_command_server,
    stop_command_server
)

from .command_client import (
    BridgeCommandClient,
    get_command_client,
    send_bridge_design_request
)

__all__ = [
    # Server
    "BridgeCommandServer",
    "CommandRequest", 
    "CommandResponse",
    "get_command_server",
    "start_command_server",
    "stop_command_server",
    
    # Client
    "BridgeCommandClient",
    "get_command_client", 
    "send_bridge_design_request"
]