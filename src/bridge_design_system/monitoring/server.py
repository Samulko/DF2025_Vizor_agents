"""Enhanced FastAPI server for real-time agent status monitoring via step_callbacks."""

import asyncio
import json
from pathlib import Path
from typing import Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .agent_monitor import AgentStatusTracker, WebSocketManager, create_agent_monitor_system
from ..config.logging_config import get_logger

logger = get_logger(__name__)


app = FastAPI(title="Agent Status Monitor")

# Global monitoring system
status_tracker: Optional[AgentStatusTracker] = None
websocket_manager: Optional[WebSocketManager] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the monitoring system on server startup."""
    global status_tracker, websocket_manager
    status_tracker, websocket_manager = create_agent_monitor_system()
    
    # Register the three agents we'll be monitoring
    status_tracker.register_agent("triage_agent", "CodeAgent")
    status_tracker.register_agent("geometry_agent", "ToolCallingAgent") 
    status_tracker.register_agent("syslogic_agent", "CodeAgent")
    
    # NEW AGENT TEMPLATE - UNCOMMENT AND MODIFY FOR NEW AGENTS
    # status_tracker.register_agent("material_agent", "ToolCallingAgent")
    
    # AGENT TYPE REFERENCE:
    # - "CodeAgent" for agents that execute code (triage_agent, syslogic_agent)
    # - "ToolCallingAgent" for agents that use tools (geometry_agent)
    #
    # TEMPLATE USAGE:
    # 1. Uncomment the line above
    # 2. Replace "material_agent" with your agent name
    # 3. Choose appropriate agent type
    # 4. Update the count in the print statement below
    
    # Start periodic cleanup task for stale WebSocket connections
    asyncio.create_task(periodic_cleanup())
    
    print("📊 Agent monitoring system initialized with 3 agents")
    # NOTE: Update the agent count above when adding new agents


async def periodic_cleanup():
    """Periodically clean up stale WebSocket connections."""
    while True:
        try:
            await asyncio.sleep(60)  # Clean up every minute
            if websocket_manager:
                websocket_manager.cleanup_stale_connections()
        except Exception as e:
            logger.debug(f"🧹 Cleanup task error: {e}")
            await asyncio.sleep(60)


@app.websocket("/status")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time status updates."""
    if not websocket_manager:
        await websocket.close(code=1000, reason="Monitoring system not initialized")
        return
    
    try:
        await websocket_manager.connect(websocket)
        
        # Send initial status
        if status_tracker:
            initial_status = {
                name: {
                    "name": agent.name,
                    "status": agent.status,
                    "step_number": agent.step_number,
                    "current_task": agent.current_task,
                    "last_update": agent.last_update,
                    "error_message": agent.error_message,
                    "memory_size": agent.memory_size,
                    "tool_calls": agent.tool_calls,
                    "timestamp": "initial"
                }
                for name, agent in status_tracker.agents.items()
            }
            await websocket.send_json({
                "type": "status_update",
                "data": initial_status
            })
        
        # Keep connection alive and handle heartbeat
        while True:
            try:
                data = await websocket.receive_text()
                # Handle heartbeat messages
                try:
                    message = json.loads(data)
                    if message.get('type') == 'ping':
                        await websocket.send_json({"type": "pong"})
                    elif message.get('type') == 'pong':
                        logger.debug("📡 Received pong from client")
                except (json.JSONDecodeError, KeyError):
                    # Ignore invalid messages
                    pass
            except Exception as e:
                logger.debug(f"📡 WebSocket receive error: {e}")
                break
            
    except WebSocketDisconnect:
        logger.debug("📡 WebSocket client disconnected normally")
        websocket_manager.disconnect(websocket)
    except Exception as e:
        error_msg = str(e)
        if "websocket.close" in error_msg or "connection closed" in error_msg.lower():
            logger.debug("📡 WebSocket connection closed by client")
        else:
            logger.debug(f"📡 WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


@app.get("/")
async def read_index():
    """Serve the enhanced status dashboard."""
    html_path = Path(__file__).parent / "status.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>Agent Status Monitor</title></head>
            <body>
                <h1>🤖 Agent Status Monitor</h1>
                <p>Enhanced dashboard not found. Please ensure status.html exists.</p>
                <p>The monitoring system should be running with real-time agent callbacks.</p>
            </body>
        </html>
        """)


@app.post("/api/status")
async def receive_status_update(request: Request):
    """Receive status updates from external processes (main CLI)."""
    try:
        data = await request.json()
        
        if status_tracker and 'agent_name' in data:
            agent_name = data.pop('agent_name')
            await status_tracker.update_status(agent_name, **data)
            logger.debug(f"📨 Received external status update for {agent_name}")
            return {"status": "success"}
        else:
            logger.warning("⚠️ Invalid status update received")
            return {"status": "error", "message": "Invalid data"}
            
    except Exception as e:
        logger.error(f"❌ Error processing status update: {e}")
        return {"status": "error", "message": str(e)}


def start_status_monitor(host: str = "0.0.0.0", port: int = 5000):
    """Start the enhanced status monitor server with network access."""
    import uvicorn
    print(f"📊 Starting Enhanced Agent Status Monitor on http://{host}:{port}")
    print(f"🌐 Dashboard accessible from any device on local network")
    uvicorn.run(app, host=host, port=port, log_level="error")


def get_status_tracker() -> Optional[AgentStatusTracker]:
    """Get the global status tracker for integration with agents."""
    return status_tracker