"""HTTP MCP Adapter for smolagents integration.

This module provides the integration layer between smolagents and the HTTP MCP server.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from smolagents import Tool

logger = logging.getLogger(__name__)


class HttpMCPAdapter:
    """Adapter to integrate HTTP MCP server with smolagents."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8001"):
        """Initialize the adapter.
        
        Args:
            mcp_server_url: URL of the MCP HTTP server
        """
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def check_connection(self) -> bool:
        """Check if MCP server is reachable."""
        try:
            response = await self.client.get(f"{self.mcp_server_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server."""
        try:
            response = await self.client.get(f"{self.mcp_server_url}/mcp/tools/registry")
            if response.status_code == 200:
                data = response.json()
                return data.get("tools", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get tools: {str(e)}")
            return []
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via HTTP MCP.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Execution result
        """
        try:
            payload = {
                "tool_name": tool_name,
                "parameters": parameters
            }
            
            response = await self.client.post(
                f"{self.mcp_server_url}/mcp/tools/{tool_name}",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}, Error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_smolagents_tools(self) -> List[Tool]:
        """Create smolagents Tool instances from MCP tools.
        
        Returns:
            List of Tool instances for smolagents
        """
        tools = []
        
        # Define core tools for bridge design
        class AddComponentTool(Tool):
            name = "add_component"
            description = "Add a component to the Grasshopper canvas"
            inputs = {
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
            }
            output_type = "dict"
            
            def forward(self, component_type: str, x: float, y: float) -> Dict[str, Any]:
                """Execute the add component tool."""
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a new event loop for this execution
                    import threading
                    result = {}
                    
                    def run_async():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            adapter = HttpMCPAdapter()
                            result.update(new_loop.run_until_complete(
                                adapter.execute_tool("add_component", {
                                    "component_type": component_type,
                                    "x": x,
                                    "y": y
                                })
                            ))
                        finally:
                            new_loop.close()
                    
                    thread = threading.Thread(target=run_async)
                    thread.start()
                    thread.join()
                    return result
                else:
                    # Run directly if no loop is running
                    adapter = HttpMCPAdapter()
                    return loop.run_until_complete(
                        adapter.execute_tool("add_component", {
                            "component_type": component_type,
                            "x": x,
                            "y": y
                        })
                    )
        
        class ConnectComponentsTool(Tool):
            name = "connect_components"
            description = "Connect two components in Grasshopper"
            inputs = {
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
            }
            output_type = "dict"
            
            def forward(self, source_id: str, target_id: str, 
                       source_param: Optional[str] = None, 
                       target_param: Optional[str] = None) -> Dict[str, Any]:
                """Execute the connect components tool."""
                loop = asyncio.get_event_loop()
                adapter = HttpMCPAdapter()
                
                params = {
                    "source_id": source_id,
                    "target_id": target_id
                }
                if source_param:
                    params["source_param"] = source_param
                if target_param:
                    params["target_param"] = target_param
                
                if loop.is_running():
                    # Handle running event loop
                    import threading
                    result = {}
                    
                    def run_async():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            adapter = HttpMCPAdapter()
                            result.update(new_loop.run_until_complete(
                                adapter.execute_tool("connect_components", params)
                            ))
                        finally:
                            new_loop.close()
                    
                    thread = threading.Thread(target=run_async)
                    thread.start()
                    thread.join()
                    return result
                else:
                    return loop.run_until_complete(
                        adapter.execute_tool("connect_components", params)
                    )
        
        class GetAllComponentsTool(Tool):
            name = "get_all_components"
            description = "Get all components in the Grasshopper document"
            inputs = {}
            output_type = "dict"
            
            def forward(self) -> Dict[str, Any]:
                """Execute the get all components tool."""
                loop = asyncio.get_event_loop()
                adapter = HttpMCPAdapter()
                
                if loop.is_running():
                    import threading
                    result = {}
                    
                    def run_async():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            adapter = HttpMCPAdapter()
                            result.update(new_loop.run_until_complete(
                                adapter.execute_tool("get_all_components", {})
                            ))
                        finally:
                            new_loop.close()
                    
                    thread = threading.Thread(target=run_async)
                    thread.start()
                    thread.join()
                    return result
                else:
                    return loop.run_until_complete(
                        adapter.execute_tool("get_all_components", {})
                    )
        
        # Add all tools to the list
        tools.extend([
            AddComponentTool(),
            ConnectComponentsTool(),
            GetAllComponentsTool()
        ])
        
        return tools
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def get_http_mcp_tools() -> List[Tool]:
    """Get HTTP MCP tools for smolagents integration.
    
    Returns:
        List of Tool instances ready for use with smolagents agents
    """
    adapter = HttpMCPAdapter()
    return adapter.create_smolagents_tools()