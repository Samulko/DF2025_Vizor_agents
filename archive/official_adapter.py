"""Official MCP integration with smolagents using the MCP Python SDK.

This replaces our custom HTTP adapter with the official MCP client.
"""
import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from smolagents import Tool

logger = logging.getLogger(__name__)


class OfficialMCPAdapter:
    """Official MCP adapter using the MCP Python SDK."""
    
    def __init__(self, grasshopper_url: str = "http://localhost:8080"):
        """Initialize the MCP adapter.
        
        Args:
            grasshopper_url: URL of the Grasshopper HTTP server
        """
        self.grasshopper_url = grasshopper_url
        self.session: Optional[ClientSession] = None
        self._server_process: Optional[subprocess.Popen] = None
        
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            # Get path to our MCP server script
            server_script = Path(__file__).parent / "grasshopper_mcp" / "official_mcp_server.py"
            
            # Start the MCP server as a subprocess
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(server_script), "--grasshopper-url", self.grasshopper_url]
            )
            
            # Create client session
            self.session = await stdio_client(server_params)
            
            # Initialize the session
            init_result = await self.session.initialize()
            logger.info(f"MCP session initialized: {init_result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.error(f"Error closing MCP session: {e}")
            finally:
                self.session = None
        
        if self._server_process:
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._server_process.kill()
            except Exception as e:
                logger.error(f"Error stopping MCP server: {e}")
            finally:
                self._server_process = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        if not self.session:
            logger.error("MCP session not connected")
            return []
        
        try:
            result = await self.session.list_tools()
            return [tool.model_dump() for tool in result.tools]
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.session:
            logger.error("MCP session not connected")
            return {"success": False, "error": "MCP session not connected"}
        
        try:
            result = await self.session.call_tool(name, arguments)
            
            # Extract text content from the result
            if result.content:
                text_content = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        text_content.append(content.text)
                
                return {
                    "success": True,
                    "result": "\n".join(text_content) if text_content else "Tool executed successfully"
                }
            else:
                return {"success": True, "result": "Tool executed successfully"}
                
        except Exception as e:
            logger.error(f"Tool call failed: {name}, Error: {e}")
            return {"success": False, "error": str(e)}
    
    def create_smolagents_tools(self) -> List[Tool]:
        """Create smolagents Tool instances from MCP tools."""
        
        class MCPTool(Tool):
            """Base class for MCP tools in smolagents."""
            
            def __init__(self, tool_name: str, description: str, inputs: Dict[str, Any]):
                self.name = tool_name
                self.description = description
                self.inputs = inputs
                self.output_type = "dict"
                self._adapter = None
            
            def set_adapter(self, adapter: 'OfficialMCPAdapter'):
                """Set the MCP adapter for this tool."""
                self._adapter = adapter
            
            def forward(self, **kwargs) -> Dict[str, Any]:
                """Execute the tool via MCP."""
                if not self._adapter:
                    return {"success": False, "error": "MCP adapter not set"}
                
                # Handle async execution in sync context
                loop = asyncio.get_event_loop()
                
                if loop.is_running():
                    # If we're already in an async context, we need to run in a thread
                    import threading
                    import queue
                    
                    result_queue = queue.Queue()
                    
                    def run_async():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            # Create new adapter instance for thread safety
                            adapter = OfficialMCPAdapter(self._adapter.grasshopper_url)
                            
                            async def execute():
                                await adapter.connect()
                                try:
                                    result = await adapter.call_tool(self.name, kwargs)
                                    return result
                                finally:
                                    await adapter.disconnect()
                            
                            result = new_loop.run_until_complete(execute())
                            result_queue.put(result)
                        except Exception as e:
                            result_queue.put({"success": False, "error": str(e)})
                        finally:
                            new_loop.close()
                    
                    thread = threading.Thread(target=run_async)
                    thread.start()
                    thread.join()
                    
                    return result_queue.get()
                else:
                    # No loop running, we can use the current one
                    async def execute():
                        if not self._adapter.session:
                            await self._adapter.connect()
                        return await self._adapter.call_tool(self.name, kwargs)
                    
                    return loop.run_until_complete(execute())
        
        # Create specific tool instances
        tools = []
        
        # Add Component Tool
        add_component_tool = MCPTool(
            tool_name="add_component",
            description="Add a component to the Grasshopper canvas",
            inputs={
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
        )
        add_component_tool.set_adapter(self)
        tools.append(add_component_tool)
        
        # Connect Components Tool
        connect_tool = MCPTool(
            tool_name="connect_components",
            description="Connect two components in Grasshopper",
            inputs={
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
        )
        connect_tool.set_adapter(self)
        tools.append(connect_tool)
        
        # Get All Components Tool
        get_all_tool = MCPTool(
            tool_name="get_all_components",
            description="Get all components in the Grasshopper document",
            inputs={}
        )
        get_all_tool.set_adapter(self)
        tools.append(get_all_tool)
        
        # Set Component Value Tool
        set_value_tool = MCPTool(
            tool_name="set_component_value",
            description="Set the value of a component parameter",
            inputs={
                "component_id": {
                    "type": "string",
                    "description": "ID of the component"
                },
                "parameter_name": {
                    "type": "string",
                    "description": "Name of the parameter to set"
                },
                "value": {
                    "type": ["string", "number", "boolean"],
                    "description": "Value to set"
                }
            }
        )
        set_value_tool.set_adapter(self)
        tools.append(set_value_tool)
        
        # Clear Document Tool
        clear_tool = MCPTool(
            tool_name="clear_document",
            description="Clear all components from the Grasshopper document",
            inputs={}
        )
        clear_tool.set_adapter(self)
        tools.append(clear_tool)
        
        # Save Document Tool
        save_tool = MCPTool(
            tool_name="save_document",
            description="Save the current Grasshopper document",
            inputs={
                "filename": {
                    "type": "string",
                    "description": "Filename to save to (optional)"
                }
            }
        )
        save_tool.set_adapter(self)
        tools.append(save_tool)
        
        return tools


def get_official_mcp_tools(grasshopper_url: str = "http://localhost:8080") -> List[Tool]:
    """Get official MCP tools for smolagents integration.
    
    Args:
        grasshopper_url: URL of the Grasshopper HTTP server
        
    Returns:
        List of Tool instances ready for use with smolagents agents
    """
    adapter = OfficialMCPAdapter(grasshopper_url)
    return adapter.create_smolagents_tools()