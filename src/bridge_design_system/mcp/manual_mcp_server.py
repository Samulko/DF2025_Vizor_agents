"""Manual MCP HTTP Server implementation.

This implements the MCP protocol directly over HTTP without using the problematic
StreamableHTTPSessionManager, avoiding the "Task group is not initialized" error.
"""
import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
from datetime import datetime

import click
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response, JSONResponse
from starlette.requests import Request
from starlette.types import Receive, Scope, Send
import uvicorn

from .grasshopper_mcp.utils.communication import GrasshopperHttpClient

# Configure logging
logger = logging.getLogger(__name__)


class ManualMCPServer:
    """Manual MCP server implementation that avoids StreamableHTTPSessionManager issues."""
    
    def __init__(self, grasshopper_url: str = "http://localhost:8080", port: int = 8001, bridge_mode: bool = True):
        """Initialize the manual MCP server.
        
        Args:
            grasshopper_url: URL of the Grasshopper HTTP server (for direct mode)
            port: Port for the MCP server
            bridge_mode: If True, queue commands for bridge. If False, call Grasshopper directly.
        """
        self.grasshopper_url = grasshopper_url
        self.port = port
        self.bridge_mode = bridge_mode
        self.grasshopper_client = GrasshopperHttpClient(grasshopper_url)
        
        # Bridge polling state
        self.pending_commands: List[Dict] = []
        self.command_results: Dict[str, Dict] = {}
        self.command_history: List[Dict] = []
        
        # Session management
        self.sessions: Dict[str, Dict] = {}
        
        # MCP Tools definition
        self.tools = [
            {
                "name": "add_component",
                "description": "Add a component to the Grasshopper canvas",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_type": {
                            "type": "string",
                            "description": "Type of component (point, line, circle, slider, panel, etc.)"
                        },
                        "x": {
                            "type": "number",
                            "description": "X coordinate on the canvas"
                        },
                        "y": {
                            "type": "number",
                            "description": "Y coordinate on the canvas"
                        }
                    },
                    "required": ["component_type", "x", "y"]
                }
            },
            {
                "name": "connect_components",
                "description": "Connect two components in Grasshopper",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_id": {
                            "type": "string",
                            "description": "ID of the source component"
                        },
                        "target_id": {
                            "type": "string",
                            "description": "ID of the target component"
                        },
                        "source_param": {
                            "type": "string",
                            "description": "Source parameter name (optional)"
                        },
                        "target_param": {
                            "type": "string",
                            "description": "Target parameter name (optional)"
                        }
                    },
                    "required": ["source_id", "target_id"]
                }
            },
            {
                "name": "get_all_components",
                "description": "Get all components in the Grasshopper document",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "set_component_value",
                "description": "Set the value of a component parameter",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_id": {
                            "type": "string",
                            "description": "ID of the component"
                        },
                        "parameter_name": {
                            "type": "string",
                            "description": "Name of the parameter to set"
                        },
                        "value": {
                            "type": "any",
                            "description": "Value to set (string, number, or boolean)"
                        }
                    },
                    "required": ["component_id", "parameter_name", "value"]
                }
            },
            {
                "name": "clear_document",
                "description": "Clear all components from the Grasshopper document",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "save_document",
                "description": "Save the current Grasshopper document",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Filename to save to (optional)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "add_python3_script",
                "description": "Add a Python 3 Script component with pre-populated code to the Grasshopper canvas. This allows dynamic geometry creation, data processing, and custom operations. The script parameter must contain the actual Python code as a string. The output variable 'a' is automatically connected to the component's output. Example: create a circle with 'import Rhino.Geometry as rg; circle = rg.Circle(rg.Point3d(0,0,0), 5); a = circle'",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "number",
                            "description": "X coordinate on the canvas (default: 100.0)"
                        },
                        "y": {
                            "type": "number",
                            "description": "Y coordinate on the canvas (default: 100.0)"
                        },
                        "script": {
                            "type": "string",
                            "description": "Python script content to populate in the component. Use 'a' as output variable. Example: 'import Rhino.Geometry as rg\\ncircle = rg.Circle(rg.Point3d(0,0,0), 5)\\na = circle'"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name for the script component (optional, default: 'Python Script')"
                        }
                    },
                    "required": ["x", "y", "script"]
                }
            },
            {
                "name": "get_python3_script",
                "description": "Get the script content from an existing Python 3 Script component. This allows reading and understanding the current code in a Python script component, enabling code inspection and informed editing. Returns the component info and script content, allowing you to analyze existing code before making modifications.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_id": {
                            "type": "string",
                            "description": "ID of the Python 3 Script component to read from. Example: 'd18eee48-60ef-4b2a-bda4-0be546f1586a'"
                        }
                    },
                    "required": ["component_id"]
                }
            },
            {
                "name": "edit_python3_script",
                "description": "Edit the script content of an existing Python 3 Script component without creating a new one. This allows modifying existing Python scripts in place, enabling iterative development and refinement of code without cluttering the canvas. IMPORTANT: This modifies the existing component rather than creating a new one. The script parameter must contain the complete new Python code as a string. The output variable 'a' is automatically connected to the component's output.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_id": {
                            "type": "string",
                            "description": "ID of the existing Python 3 Script component to modify. Example: 'd18eee48-60ef-4b2a-bda4-0be546f1586a'"
                        },
                        "script": {
                            "type": "string",
                            "description": "New Python script content to replace the existing code. Must be complete valid Python code. Example: 'import Rhino.Geometry as rg\\nimport math\\nspheres = []\\nfor i in range(10):\\n    center = rg.Point3d(i*2, 0, 0)\\n    sphere = rg.Sphere(center, 1)\\n    spheres.append(sphere)\\na = spheres'"
                        }
                    },
                    "required": ["component_id", "script"]
                }
            },
            {
                "name": "get_python3_script_errors",
                "description": "Get error and warning messages from an existing Python 3 Script component. This allows checking for syntax errors, runtime exceptions, warnings, and other issues in Python script components, enabling debugging and error resolution. IMPORTANT: This reads runtime messages that are generated when the component executes. If the component hasn't run yet or had no errors, the result may be empty.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_id": {
                            "type": "string",
                            "description": "ID of the Python 3 Script component to check for errors. Returns categorized errors, warnings, and all messages. Example: 'd18eee48-60ef-4b2a-bda4-0be546f1586a'"
                        }
                    },
                    "required": ["component_id"]
                }
            },
            {
                "name": "get_all_components_enhanced",
                "description": "Get a list of all components in the current Grasshopper document with enhanced details. This is an enhanced version that includes additional metadata beyond the basic component list, providing component types, positions, connections, parameter values, and other detailed information useful for analysis and manipulation of the Grasshopper definition.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def _create_session(self) -> str:
        """Create a new MCP session."""
        session_id = str(uuid.uuid4()).replace('-', '')
        self.sessions[session_id] = {
            "id": session_id,
            "created": datetime.utcnow().isoformat(),
            "initialized": False
        }
        logger.info(f"Created new MCP session: {session_id}")
        return session_id
    
    def _get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def _create_sse_response(self, data: Dict[str, Any]) -> str:
        """Create Server-Sent Events formatted response."""
        json_data = json.dumps(data)
        return f"event: message\ndata: {json_data}\n\n"
    
    def _create_jsonrpc_response(self, request_id: Any, result: Any = None, error: Any = None) -> Dict[str, Any]:
        """Create JSON-RPC 2.0 response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id
        }
        
        if error:
            response["error"] = error
        else:
            response["result"] = result
            
        return response
    
    def _create_jsonrpc_error(self, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """Create JSON-RPC 2.0 error object."""
        error = {
            "code": code,
            "message": message
        }
        if data:
            error["data"] = data
        return error
    
    async def handle_mcp_request(self, request: Request) -> Response:
        """Handle MCP protocol requests."""
        try:
            # Parse JSON-RPC request
            try:
                body = await request.json()
            except Exception as e:
                error_response = self._create_jsonrpc_response(
                    None,
                    error=self._create_jsonrpc_error(-32700, "Parse error", str(e))
                )
                return Response(
                    self._create_sse_response(error_response),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                )
            
            # Validate JSON-RPC structure
            if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
                error_response = self._create_jsonrpc_response(
                    body.get("id"),
                    error=self._create_jsonrpc_error(-32600, "Invalid Request")
                )
                return Response(
                    self._create_sse_response(error_response),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                )
            
            request_id = body.get("id")
            method = body.get("method")
            params = body.get("params", {})
            
            logger.info(f"Handling MCP request: {method} with params: {params}")
            
            # Handle session management
            session_id = request.headers.get("mcp-session-id")
            if not session_id and method != "initialize":
                session_id = self._create_session()
            
            # Handle different MCP methods
            if method == "initialize":
                result = await self._handle_initialize(params)
                session_id = self._create_session()
                self.sessions[session_id]["initialized"] = True
                
                response = self._create_jsonrpc_response(request_id, result)
                sse_response = self._create_sse_response(response)
                
                return Response(
                    sse_response,
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "mcp-session-id": session_id
                    }
                )
            
            elif method == "tools/list":
                result = await self._handle_tools_list()
                response = self._create_jsonrpc_response(request_id, result)
                sse_response = self._create_sse_response(response)
                
                return Response(
                    sse_response,
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "mcp-session-id": session_id
                    }
                )
            
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
                response = self._create_jsonrpc_response(request_id, result)
                sse_response = self._create_sse_response(response)
                
                return Response(
                    sse_response,
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "mcp-session-id": session_id
                    }
                )
            
            else:
                error_response = self._create_jsonrpc_response(
                    request_id,
                    error=self._create_jsonrpc_error(-32601, f"Method not found: {method}")
                )
                return Response(
                    self._create_sse_response(error_response),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                )
                
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}", exc_info=True)
            error_response = self._create_jsonrpc_response(
                None,
                error=self._create_jsonrpc_error(-32603, "Internal error", str(e))
            )
            return Response(
                self._create_sse_response(error_response),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        logger.info("Handling MCP initialize request")
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False
                },
                "experimental": {}
            },
            "serverInfo": {
                "name": "grasshopper-mcp-manual",
                "version": "1.0.0"
            }
        }
    
    async def _handle_tools_list(self) -> Dict[str, Any]:
        """Handle tools/list request."""
        logger.info("Handling tools/list request")
        return {
            "tools": self.tools
        }
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"Handling tools/call: {name} with args: {arguments}")
        
        try:
            # Execute the tool
            if self.bridge_mode:
                result = await self._handle_bridge_mode_tool(name, arguments)
            else:
                result = await self._execute_tool_direct(name, arguments)
            
            # Format as MCP content response
            if isinstance(result, dict) and result.get("success", True):
                content = {
                    "type": "text",
                    "text": f"Tool '{name}' executed successfully. Result: {result}"
                }
            else:
                content = {
                    "type": "text",
                    "text": f"Tool '{name}' failed. Error: {result.get('error', 'Unknown error')}"
                }
            
            return {
                "content": [content]
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {name}, Error: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Tool execution failed: {str(e)}"
                }]
            }
    
    async def _execute_tool_direct(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool directly (non-bridge mode)."""
        if name == "add_component":
            return await self._add_component(
                component_type=arguments["component_type"],
                x=arguments["x"],
                y=arguments["y"]
            )
        elif name == "connect_components":
            return await self._connect_components(
                source_id=arguments["source_id"],
                target_id=arguments["target_id"],
                source_param=arguments.get("source_param"),
                target_param=arguments.get("target_param")
            )
        elif name == "get_all_components":
            return await self._get_all_components()
        elif name == "set_component_value":
            return await self._set_component_value(
                component_id=arguments["component_id"],
                parameter_name=arguments["parameter_name"],
                value=arguments["value"]
            )
        elif name == "clear_document":
            return await self._clear_document()
        elif name == "save_document":
            return await self._save_document(
                filename=arguments.get("filename")
            )
        elif name == "add_python3_script":
            return await self._add_python3_script(
                x=arguments["x"],
                y=arguments["y"],
                script=arguments["script"],
                name=arguments.get("name")
            )
        elif name == "get_python3_script":
            return await self._get_python3_script(
                component_id=arguments["component_id"]
            )
        elif name == "edit_python3_script":
            return await self._edit_python3_script(
                component_id=arguments["component_id"],
                script=arguments["script"]
            )
        elif name == "get_python3_script_errors":
            return await self._get_python3_script_errors(
                component_id=arguments["component_id"]
            )
        elif name == "get_all_components_enhanced":
            return await self._get_all_components_enhanced()
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    # Tool implementation methods (same as before)
    async def _add_component(self, component_type: str, x: float, y: float) -> Dict[str, Any]:
        """Add a component to Grasshopper canvas."""
        try:
            response = await self.grasshopper_client.send_command(
                "add_component",
                {
                    "component_type": component_type,
                    "x": x,
                    "y": y
                }
            )
            return response
        except Exception as e:
            logger.error(f"Failed to add component: {e}")
            return {"success": False, "error": str(e)}
    
    async def _connect_components(
        self, 
        source_id: str, 
        target_id: str, 
        source_param: Optional[str] = None, 
        target_param: Optional[str] = None
    ) -> Dict[str, Any]:
        """Connect two components in Grasshopper."""
        try:
            params = {
                "source_id": source_id,
                "target_id": target_id
            }
            if source_param:
                params["source_param"] = source_param
            if target_param:
                params["target_param"] = target_param
                
            response = await self.grasshopper_client.send_command("connect_components", params)
            return response
        except Exception as e:
            logger.error(f"Failed to connect components: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_all_components(self) -> Dict[str, Any]:
        """Get all components from Grasshopper document."""
        try:
            response = await self.grasshopper_client.send_command("get_all_components", {})
            return response
        except Exception as e:
            logger.error(f"Failed to get components: {e}")
            return {"success": False, "error": str(e)}
    
    async def _set_component_value(
        self, 
        component_id: str, 
        parameter_name: str, 
        value: Any
    ) -> Dict[str, Any]:
        """Set a component parameter value."""
        try:
            response = await self.grasshopper_client.send_command(
                "set_component_value",
                {
                    "component_id": component_id,
                    "parameter_name": parameter_name,
                    "value": value
                }
            )
            return response
        except Exception as e:
            logger.error(f"Failed to set component value: {e}")
            return {"success": False, "error": str(e)}
    
    async def _clear_document(self) -> Dict[str, Any]:
        """Clear the Grasshopper document."""
        try:
            response = await self.grasshopper_client.send_command("clear_document", {})
            return response
        except Exception as e:
            logger.error(f"Failed to clear document: {e}")
            return {"success": False, "error": str(e)}
    
    async def _save_document(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Save the Grasshopper document."""
        try:
            params = {}
            if filename:
                params["filename"] = filename
                
            response = await self.grasshopper_client.send_command("save_document", params)
            return response
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return {"success": False, "error": str(e)}
    
    # Python script component methods
    async def _add_python3_script(self, x: float, y: float, script: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Add a Python 3 script component to Grasshopper."""
        try:
            # Use the same approach as the reference implementation
            params = {
                "type": "Py3",  # Use Py3 which is the proper Python 3 component in Rhino 8
                "x": x,
                "y": y
            }
            
            if script:
                params["script"] = script
            else:
                # Provide a default template
                params["script"] = """# Python 3 Script in Grasshopper
# Access inputs through variable names matching input parameters
# Return outputs as a tuple or single value

import Rhino.Geometry as rg

# Your code here
result = "Hello from Python 3!"

# Return output
result"""
            
            response = await self.grasshopper_client.send_command("add_component", params)
            return response
        except Exception as e:
            logger.error(f"Failed to add Python script: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_python3_script(self, component_id: str) -> Dict[str, Any]:
        """Get the Python script code from a component."""
        try:
            params = {
                "id": component_id  # Use "id" to match C# expectation
            }
            
            response = await self.grasshopper_client.send_command("get_python_script_content", params)
            return response
        except Exception as e:
            logger.error(f"Failed to get Python script: {e}")
            return {"success": False, "error": str(e)}
    
    async def _edit_python3_script(self, component_id: str, script: str) -> Dict[str, Any]:
        """Edit the Python script code in a component."""
        try:
            params = {
                "id": component_id,  # Use "id" to match C# expectation
                "script": script
            }
            
            response = await self.grasshopper_client.send_command("set_python_script_content", params)
            return response
        except Exception as e:
            logger.error(f"Failed to edit Python script: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_python3_script_errors(self, component_id: str) -> Dict[str, Any]:
        """Get runtime errors from a Python script component."""
        try:
            params = {
                "id": component_id  # Use "id" to match C# expectation
            }
            
            response = await self.grasshopper_client.send_command("get_python_script_errors", params)
            return response
        except Exception as e:
            logger.error(f"Failed to get Python script errors: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_all_components_enhanced(self) -> Dict[str, Any]:
        """Get all components with enhanced details."""
        try:
            # Use get_document_info and extract components list
            doc_info = await self.grasshopper_client.send_command("get_document_info", {})
            
            if doc_info.get("success") and "result" in doc_info:
                result_data = doc_info["result"]
                if "components" in result_data:
                    return {
                        "success": True,
                        "result": result_data["components"]
                    }
            
            return doc_info
        except Exception as e:
            logger.error(f"Failed to get enhanced components: {e}")
            return {"success": False, "error": str(e)}
    
    def _queue_command_for_bridge(self, command_type: str, parameters: Dict[str, Any]) -> str:
        """Queue a command for the bridge to execute."""
        command_id = str(uuid.uuid4())
        command = {
            "id": command_id,
            "type": command_type,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.pending_commands.append(command)
        logger.info(f"Queued command for bridge: {command_type} [{command_id}]")
        return command_id
    
    async def _handle_bridge_mode_tool(self, name: str, arguments: dict) -> Dict[str, Any]:
        """Handle tool execution in bridge mode (queue for bridge)."""
        try:
            command_id = self._queue_command_for_bridge(name, arguments)
            
            # Wait for result with timeout
            max_wait = 30  # seconds
            wait_interval = 0.5
            waited = 0
            
            while waited < max_wait:
                if command_id in self.command_results:
                    result = self.command_results[command_id]
                    # Clean up
                    del self.command_results[command_id]
                    return result
                
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Timeout
            return {"success": False, "error": "Bridge execution timeout"}
            
        except Exception as e:
            logger.error(f"Bridge mode tool execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Bridge polling endpoints
    async def get_pending_commands(self, request: Request) -> JSONResponse:
        """Get pending commands for bridge to execute."""
        commands = self.pending_commands.copy()
        self.pending_commands.clear()  # Clear after sending
        logger.info(f"Bridge requested commands: {len(commands)} pending")
        return JSONResponse(commands)
    
    async def receive_command_result(self, request: Request) -> JSONResponse:
        """Receive command execution result from bridge."""
        try:
            data = await request.json()
            command_id = data["command_id"]
            success = data["success"]
            result = data["result"]
            
            # Store result
            self.command_results[command_id] = {
                "success": success,
                "result": result
            }
            
            # Add to history
            self.command_history.append({
                "command_id": command_id,
                "success": success,
                "result": result,
                "timestamp": data.get("timestamp", datetime.utcnow().isoformat())
            })
            
            # Keep only last 100 in history
            if len(self.command_history) > 100:
                self.command_history.pop(0)
            
            logger.info(f"Received result from bridge: {command_id} - {'SUCCESS' if success else 'FAILED'}")
            return JSONResponse({"status": "received"})
            
        except Exception as e:
            logger.error(f"Error receiving command result: {e}")
            return JSONResponse({"error": str(e)}, status_code=400)
    
    async def get_bridge_status(self, request: Request) -> JSONResponse:
        """Get bridge status and command history."""
        return JSONResponse({
            "pending_commands": len(self.pending_commands),
            "completed_commands": len(self.command_results),
            "command_history": self.command_history[-10:],  # Last 10
            "server_time": datetime.utcnow().isoformat(),
            "sessions": len(self.sessions)
        })
    
    async def health_check(self, request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "healthy",
            "server": "manual-mcp-server",
            "version": "1.0.0",
            "bridge_mode": self.bridge_mode,
            "sessions": len(self.sessions)
        })
    
    def create_app(self) -> Starlette:
        """Create the ASGI application."""
        return Starlette(
            debug=True,
            routes=[
                # MCP protocol endpoint
                Route("/mcp", self.handle_mcp_request, methods=["POST", "GET"]),
                Route("/mcp/", self.handle_mcp_request, methods=["POST", "GET"]),
                
                # Bridge polling endpoints
                Route("/grasshopper/pending_commands", self.get_pending_commands, methods=["GET"]),
                Route("/grasshopper/command_result", self.receive_command_result, methods=["POST"]),
                Route("/grasshopper/status", self.get_bridge_status, methods=["GET"]),
                
                # Health check
                Route("/health", self.health_check, methods=["GET"]),
            ]
        )
    
    def run(self) -> None:
        """Run the MCP server."""
        app = self.create_app()
        logger.info(f"Starting Manual MCP HTTP server on port {self.port}")
        logger.info(f"Bridge mode: {self.bridge_mode}")
        logger.info(f"Grasshopper URL: {self.grasshopper_url}")
        uvicorn.run(app, host="127.0.0.1", port=self.port)


@click.command()
@click.option("--port", default=8001, help="Port to listen on for HTTP")
@click.option(
    "--grasshopper-url", 
    default="http://localhost:8080",
    help="URL of the Grasshopper HTTP server"
)
@click.option(
    "--bridge-mode/--direct-mode",
    default=True,
    help="Enable bridge mode (default) or direct mode"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(port: int, grasshopper_url: str, bridge_mode: bool, log_level: str) -> int:
    """Start the Manual MCP HTTP server."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create and run server
    server = ManualMCPServer(grasshopper_url, port, bridge_mode)
    server.run()
    
    return 0


if __name__ == "__main__":
    main()