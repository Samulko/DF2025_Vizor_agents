#!/usr/bin/env python3
"""
Grasshopper Bridge Test Server

Simple HTTP server to test the Grasshopper MCP Bridge component.
Provides the endpoints that the bridge expects for command polling.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel


class CommandResult(BaseModel):
    command_id: str
    success: bool
    result: dict
    timestamp: str


class TestServer:
    def __init__(self):
        self.app = FastAPI(title="Grasshopper Bridge Test Server")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Command queue and results storage
        self.pending_commands: List[Dict] = []
        self.command_results: Dict[str, CommandResult] = {}
        self.command_history: List[Dict] = []
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all HTTP routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "Grasshopper Bridge Test Server",
                "status": "running",
                "pending_commands": len(self.pending_commands),
                "completed_commands": len(self.command_results)
            }
        
        @self.app.get("/grasshopper/pending_commands")
        async def get_pending_commands():
            """Get pending commands for the bridge to execute"""
            commands = self.pending_commands.copy()
            self.pending_commands.clear()  # Clear after sending
            print(f"Sending {len(commands)} pending commands to bridge")
            return commands
        
        @self.app.post("/grasshopper/command_result")
        async def receive_command_result(result: CommandResult):
            """Receive command execution results from the bridge"""
            print(f"Received result for command {result.command_id}: {'SUCCESS' if result.success else 'FAILED'}")
            self.command_results[result.command_id] = result
            
            # Add to history
            self.command_history.append({
                "command_id": result.command_id,
                "success": result.success,
                "result": result.result,
                "timestamp": result.timestamp
            })
            
            return {"status": "received"}
        
        @self.app.get("/test/status")
        async def get_test_status():
            """Get current test status"""
            return {
                "pending_commands": len(self.pending_commands),
                "completed_commands": len(self.command_results),
                "command_history": self.command_history[-10:],  # Last 10 commands
                "server_time": datetime.utcnow().isoformat()
            }
        
        # Test command endpoints
        @self.app.post("/test/add_point_component")
        async def test_add_point():
            """Test: Add a point component"""
            command_id = str(uuid.uuid4())
            command = {
                "id": command_id,
                "type": "add_component",
                "parameters": {
                    "component_type": "point",
                    "x": 100,
                    "y": 200
                }
            }
            self.pending_commands.append(command)
            print(f"Queued ADD POINT command: {command_id}")
            return {"command_id": command_id, "status": "queued"}
        
        @self.app.post("/test/add_number_slider")
        async def test_add_number():
            """Test: Add a number slider"""
            command_id = str(uuid.uuid4())
            command = {
                "id": command_id,
                "type": "add_component",
                "parameters": {
                    "component_type": "number",
                    "x": 50,
                    "y": 100
                }
            }
            self.pending_commands.append(command)
            print(f"Queued ADD NUMBER command: {command_id}")
            return {"command_id": command_id, "status": "queued"}
        
        @self.app.post("/test/connect_components")
        async def test_connect():
            """Test: Connect two components (requires existing components)"""
            # This is a simplified test - in real scenarios you'd use actual component IDs
            command_id = str(uuid.uuid4())
            command = {
                "id": command_id,
                "type": "connect_components",
                "parameters": {
                    "source_id": "comp_1",
                    "target_id": "comp_2",
                    "source_param": "",
                    "target_param": ""
                }
            }
            self.pending_commands.append(command)
            print(f"Queued CONNECT command: {command_id}")
            return {"command_id": command_id, "status": "queued"}
        
        @self.app.post("/test/set_value")
        async def test_set_value():
            """Test: Set component value"""
            command_id = str(uuid.uuid4())
            command = {
                "id": command_id,
                "type": "set_component_value",
                "parameters": {
                    "component_id": "comp_1",
                    "parameter_name": "N",
                    "value": 42.0
                }
            }
            self.pending_commands.append(command)
            print(f"Queued SET VALUE command: {command_id}")
            return {"command_id": command_id, "status": "queued"}
        
        @self.app.post("/test/clear_document")
        async def test_clear():
            """Test: Clear Grasshopper document"""
            command_id = str(uuid.uuid4())
            command = {
                "id": command_id,
                "type": "clear_document",
                "parameters": {}
            }
            self.pending_commands.append(command)
            print(f"Queued CLEAR DOCUMENT command: {command_id}")
            return {"command_id": command_id, "status": "queued"}
        
        @self.app.post("/test/batch_commands")
        async def test_batch():
            """Test: Send multiple commands in sequence"""
            commands = []
            
            # Add point
            cmd1_id = str(uuid.uuid4())
            commands.append({
                "id": cmd1_id,
                "type": "add_component",
                "parameters": {"component_type": "point", "x": 100, "y": 100}
            })
            
            # Add number slider
            cmd2_id = str(uuid.uuid4())
            commands.append({
                "id": cmd2_id,
                "type": "add_component", 
                "parameters": {"component_type": "number", "x": 300, "y": 100}
            })
            
            # Add text panel
            cmd3_id = str(uuid.uuid4())
            commands.append({
                "id": cmd3_id,
                "type": "add_component",
                "parameters": {"component_type": "panel", "x": 200, "y": 300}
            })
            
            self.pending_commands.extend(commands)
            print(f"Queued BATCH of {len(commands)} commands")
            return {
                "command_ids": [cmd["id"] for cmd in commands],
                "status": "queued",
                "count": len(commands)
            }


def create_test_server():
    """Create and configure the test server"""
    return TestServer()


async def run_server(port: int = 8001):
    """Run the test server"""
    server = create_test_server()
    
    print(f"""
🧪 Grasshopper Bridge Test Server Starting...

Server URL: http://localhost:{port}
Bridge URL: http://localhost:{port}/grasshopper/

Test Commands:
- POST /test/add_point_component
- POST /test/add_number_slider  
- POST /test/connect_components
- POST /test/set_value
- POST /test/clear_document
- POST /test/batch_commands

Status: GET /test/status
    """)
    
    config = uvicorn.Config(
        server.app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(run_server())