"""WebSocket server for real-time agent status visualization."""

import asyncio
import logging
import signal
import sys

from .status_broadcaster import AgentStatusBroadcaster


class VisualizationServer:
    """WebSocket server for agent visualization."""

    def __init__(self, port: int = 8765):
        """Initialize the visualization server.

        Args:
            port: WebSocket server port
        """
        self.port = port
        self.broadcaster = AgentStatusBroadcaster(port)
        self.logger = logging.getLogger(__name__)
        self.running = False

    async def start(self):
        """Start the visualization server."""
        try:
            await self.broadcaster.start_server()
            self.running = True

            self.logger.info(f"Visualization server started on port {self.port}")
            self.logger.info("Ready to serve agent status updates to visualization clients")

            # Keep the server running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the visualization server."""
        if self.broadcaster:
            await self.broadcaster.stop_server()
        self.running = False
        self.logger.info("Visualization server stopped")

    def get_status(self) -> dict:
        """Get server status information."""
        return {
            "running": self.running,
            "port": self.port,
            "broadcaster_status": self.broadcaster.get_status_summary(),
        }


def setup_signal_handlers(server: VisualizationServer):
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        asyncio.create_task(server.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_server(port: int = 8765):
    """Run the visualization server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    server = VisualizationServer(port)
    setup_signal_handlers(server)

    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


def main():
    """Main entry point for the WebSocket server."""
    import argparse

    parser = argparse.ArgumentParser(description="Bridge Design System - Visualization Server")
    parser.add_argument(
        "--port", type=int, default=8765, help="WebSocket server port (default: 8765)"
    )

    args = parser.parse_args()

    print(f"Starting Bridge Design System Visualization Server on port {args.port}")
    print("Press Ctrl+C to stop")

    try:
        asyncio.run(run_server(args.port))
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
