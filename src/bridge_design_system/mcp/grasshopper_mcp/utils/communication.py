"""HTTP communication utilities for Grasshopper MCP.

This module replaces TCP socket communication with HTTP requests.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from httpx import AsyncClient, HTTPStatusError, RequestError

logger = logging.getLogger(__name__)


class GrasshopperHttpClient:
    """HTTP client for communicating with Grasshopper."""
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 30.0):
        """Initialize the HTTP client.
        
        Args:
            base_url: Base URL of the Grasshopper HTTP server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client: Optional[AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    def _get_client(self) -> AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self.client
    
    async def send_command(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to Grasshopper via HTTP.
        
        Args:
            command_type: Type of command to execute
            params: Command parameters
            
        Returns:
            Response from Grasshopper
            
        Raises:
            HTTPError: If the request fails
            ConnectionError: If cannot connect to Grasshopper
        """
        client = self._get_client()
        
        try:
            logger.debug(f"Sending HTTP command: {command_type} with params: {params}")
            
            # Prepare the request payload
            payload = {
                "type": command_type,
                "parameters": params
            }
            
            # Send POST request to Grasshopper
            response = await client.post(
                f"/grasshopper/{command_type}",
                json=payload
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            logger.debug(f"Received response: {result}")
            
            return result
            
        except HTTPStatusError as e:
            logger.error(f"HTTP error for command {command_type}: {e.response.status_code} - {e.response.text}")
            raise ConnectionError(f"Grasshopper HTTP error: {e.response.status_code}")
            
        except RequestError as e:
            logger.error(f"Request error for command {command_type}: {str(e)}")
            raise ConnectionError(f"Cannot connect to Grasshopper: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error for command {command_type}: {str(e)}")
            raise
    
    async def check_connection(self) -> bool:
        """Check if Grasshopper is reachable.
        
        Returns:
            True if connected, False otherwise
        """
        client = self._get_client()
        
        try:
            response = await client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Grasshopper connection check failed: {str(e)}")
            return False
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from Grasshopper.
        
        Returns:
            List of available tools with their descriptions
        """
        try:
            result = await self.send_command("get_available_tools", {})
            return result.get("tools", [])
        except Exception as e:
            logger.error(f"Failed to get available tools: {str(e)}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status from Grasshopper.
        
        Returns:
            Status information including components and connections
        """
        try:
            result = await self.send_command("get_document_info", {})
            return {
                "status": "connected",
                "components": result.get("result", {}).get("components", []),
                "connections": result.get("result", {}).get("connections", []),
                "document_info": result.get("result", {})
            }
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}")
            return {
                "status": "disconnected",
                "error": str(e),
                "components": [],
                "connections": []
            }
    
    # Core Grasshopper operations
    async def add_component(self, component_type: str, x: float, y: float, **kwargs) -> Dict[str, Any]:
        """Add a component to Grasshopper canvas."""
        params = {
            "component_type": component_type,
            "x": x,
            "y": y,
            **kwargs
        }
        return await self.send_command("add_component", params)
    
    async def connect_components(
        self, 
        source_id: str, 
        target_id: str,
        source_param: Optional[str] = None,
        target_param: Optional[str] = None
    ) -> Dict[str, Any]:
        """Connect two components in Grasshopper."""
        params = {
            "source_id": source_id,
            "target_id": target_id
        }
        if source_param:
            params["source_param"] = source_param
        if target_param:
            params["target_param"] = target_param
            
        return await self.send_command("connect_components", params)
    
    async def get_all_components(self) -> Dict[str, Any]:
        """Get all components in the Grasshopper document."""
        return await self.send_command("get_all_components", {})
    
    async def get_component_info(self, component_id: str) -> Dict[str, Any]:
        """Get information about a specific component."""
        return await self.send_command("get_component_info", {"component_id": component_id})
    
    async def clear_document(self) -> Dict[str, Any]:
        """Clear the Grasshopper document."""
        return await self.send_command("clear_grasshopper_document", {})
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None


# Backward compatibility function (replaces the old TCP send_to_grasshopper)
async def send_to_grasshopper_http(command_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send command to Grasshopper via HTTP (backward compatibility).
    
    Args:
        command_type: Command type to execute
        params: Optional parameters
        
    Returns:
        Response from Grasshopper
    """
    if params is None:
        params = {}
    
    async with GrasshopperHttpClient() as client:
        return await client.send_command(command_type, params)