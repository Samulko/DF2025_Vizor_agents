"""Sync wrappers for MCP tools to work with smolagents CodeAgent.

This module provides synchronous wrapper functions around the async MCP tools,
allowing them to work properly with smolagents while maintaining the bridge architecture.
"""
import asyncio
import logging
import threading
import httpx
from typing import Any, Dict, List, Optional
from functools import wraps

from smolagents import tool

logger = logging.getLogger(__name__)


class SyncMCPClient:
    """Simplified synchronous wrapper using direct HTTP calls."""
    
    def __init__(self, server_url: str = "http://localhost:8001/mcp/"):
        """Initialize the sync MCP client.
        
        Args:
            server_url: URL of the MCP streamable HTTP server (note trailing slash)
        """
        self.server_url = server_url
        self._session_id: Optional[str] = None
        self._connected = False
        
    def _parse_sse_response(self, text: str) -> Dict[str, Any]:
        """Parse Server-Sent Events response format."""
        try:
            lines = text.strip().split('\n')
            data_line = None
            
            for line in lines:
                if line.startswith('data: '):
                    data_line = line[6:]  # Remove 'data: ' prefix
                    break
            
            if data_line:
                import json
                return json.loads(data_line)
            else:
                return {"error": "No data found in SSE response"}
                
        except Exception as e:
            return {"error": f"Failed to parse SSE: {e}"}
    
    def _make_request(self, payload: Dict[str, Any], capture_session: bool = False) -> Dict[str, Any]:
        """Make a direct HTTP request to the MCP server."""
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"  # MCP requires BOTH
            }
            
            if self._session_id:
                headers["mcp-session-id"] = self._session_id
            
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.post(self.server_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    # Capture session ID from headers if needed
                    if capture_session:
                        session_id = response.headers.get("mcp-session-id")
                        if session_id:
                            self._session_id = session_id
                            logger.info(f"Captured session ID: {session_id}")
                    
                    # Parse Server-Sent Events format
                    return self._parse_sse_response(response.text)
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    def connect(self) -> bool:
        """Connect to the MCP server by initializing a session."""
        try:
            # Initialize session
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "sync-mcp-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            result = self._make_request(init_payload, capture_session=True)
            
            if "error" not in result:
                self._connected = True
                logger.info("Successfully connected to MCP server")
                return True
            else:
                logger.error(f"Failed to initialize MCP session: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self._connected = False
            return False
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool using JSON-RPC over HTTP."""
        if not self._connected:
            logger.warning("Not connected, attempting to connect...")
            if not self.connect():
                return {"success": False, "error": "Failed to connect to MCP server"}
        
        try:
            payload = {
                "jsonrpc": "2.0", 
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }
            
            result = self._make_request(payload)
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            elif "result" in result:
                # Extract result from JSON-RPC response
                tool_result = result["result"]
                if isinstance(tool_result, list) and len(tool_result) > 0:
                    content = tool_result[0]
                    if isinstance(content, dict) and "text" in content:
                        text = content["text"]
                        if "successfully" in text.lower() or "Tool" in text and "executed successfully" in text:
                            return {"success": True, "result": text}
                        else:
                            return {"success": False, "error": text}
                
                return {"success": True, "result": str(tool_result)}
            else:
                return {"success": False, "error": "Unexpected response format"}
                
        except Exception as e:
            logger.error(f"Tool call failed: {name} - {e}")
            return {"success": False, "error": str(e)}
    
    def disconnect(self):
        """Disconnect from the MCP server."""
        self._connected = False
        self._session_id = None


# Global client instance  
_mcp_client = SyncMCPClient("http://localhost:8001/mcp/")


def ensure_connection():
    """Ensure MCP client is connected."""
    if not _mcp_client._connected:
        success = _mcp_client.connect()
        if not success:
            raise RuntimeError("Failed to connect to MCP server")


# Sync wrapper tools for smolagents
@tool
def add_component(component_type: str, x: float, y: float) -> str:
    """Add a component to the Grasshopper canvas.
    
    Args:
        component_type: Type of component (point, line, circle, slider, panel, etc.)
        x: X coordinate on the canvas
        y: Y coordinate on the canvas
        
    Returns:
        Result of the component creation
    """
    ensure_connection()
    
    result = _mcp_client.call_tool("add_component", {
        "component_type": component_type,
        "x": x,
        "y": y
    })
    
    if result.get("success"):
        return f"Successfully added {component_type} component at ({x}, {y}). {result.get('result', '')}"
    else:
        return f"Failed to add component: {result.get('error', 'Unknown error')}"


@tool  
def connect_components(source_id: str, target_id: str, source_param: Optional[str] = None, target_param: Optional[str] = None) -> str:
    """Connect two components in Grasshopper.
    
    Args:
        source_id: ID of the source component
        target_id: ID of the target component  
        source_param: Source parameter name (optional)
        target_param: Target parameter name (optional)
        
    Returns:
        Result of the connection
    """
    ensure_connection()
    
    arguments = {
        "source_id": source_id,
        "target_id": target_id
    }
    if source_param:
        arguments["source_param"] = source_param
    if target_param:
        arguments["target_param"] = target_param
    
    result = _mcp_client.call_tool("connect_components", arguments)
    
    if result.get("success"):
        return f"Successfully connected {source_id} to {target_id}. {result.get('result', '')}"
    else:
        return f"Failed to connect components: {result.get('error', 'Unknown error')}"


@tool
def get_all_components() -> str:
    """Get all components in the Grasshopper document.
    
    Returns:
        List of all components in the document
    """
    ensure_connection()
    
    result = _mcp_client.call_tool("get_all_components", {})
    
    if result.get("success"):
        return f"Components in document: {result.get('result', '')}"
    else:
        return f"Failed to get components: {result.get('error', 'Unknown error')}"


@tool
def set_component_value(component_id: str, parameter_name: str, value: Any) -> str:
    """Set the value of a component parameter.
    
    Args:
        component_id: ID of the component
        parameter_name: Name of the parameter to set
        value: Value to set (string, number, or boolean)
        
    Returns:
        Result of the parameter setting
    """
    ensure_connection()
    
    result = _mcp_client.call_tool("set_component_value", {
        "component_id": component_id,
        "parameter_name": parameter_name,
        "value": value
    })
    
    if result.get("success"):
        return f"Successfully set {parameter_name} = {value} on {component_id}. {result.get('result', '')}"
    else:
        return f"Failed to set component value: {result.get('error', 'Unknown error')}"


@tool
def clear_document() -> str:
    """Clear all components from the Grasshopper document.
    
    Returns:
        Result of the document clearing
    """
    ensure_connection()
    
    result = _mcp_client.call_tool("clear_document", {})
    
    if result.get("success"):
        return f"Successfully cleared document. {result.get('result', '')}"
    else:
        return f"Failed to clear document: {result.get('error', 'Unknown error')}"


@tool
def save_document(filename: Optional[str] = None) -> str:
    """Save the current Grasshopper document.
    
    Args:
        filename: Filename to save to (optional)
        
    Returns:
        Result of the document saving
    """
    ensure_connection()
    
    arguments = {}
    if filename:
        arguments["filename"] = filename
    
    result = _mcp_client.call_tool("save_document", arguments)
    
    if result.get("success"):
        return f"Successfully saved document. {result.get('result', '')}"
    else:
        return f"Failed to save document: {result.get('error', 'Unknown error')}"


def get_sync_grasshopper_tools() -> List:
    """Get sync Grasshopper tools for use with smolagents.
    
    Returns:
        List of sync tool functions
    """
    return [
        add_component,
        connect_components, 
        get_all_components,
        set_component_value,
        clear_document,
        save_document
    ]


def cleanup_mcp_client():
    """Cleanup the MCP client connection."""
    global _mcp_client
    if _mcp_client:
        _mcp_client.disconnect()