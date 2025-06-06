"""Core Grasshopper component management tools."""
import logging
from typing import Any, Dict, Optional

from ...utils.communication import GrasshopperHttpClient

logger = logging.getLogger(__name__)


async def add_number_slider(
    x: float,
    y: float,
    min_value: float = 0.0,
    max_value: float = 10.0,
    value: float = 5.0,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """Add a number slider component to Grasshopper.
    
    Args:
        x: X coordinate on canvas
        y: Y coordinate on canvas
        min_value: Minimum slider value
        max_value: Maximum slider value
        value: Current slider value
        name: Optional slider name
        
    Returns:
        Component creation result
    """
    async with GrasshopperHttpClient() as client:
        return await client.send_command("add_number_slider", {
            "x": x,
            "y": y,
            "min": min_value,
            "max": max_value,
            "value": value,
            "name": name or "Number Slider"
        })


async def add_panel(x: float, y: float, name: Optional[str] = None) -> Dict[str, Any]:
    """Add a panel component for displaying data.
    
    Args:
        x: X coordinate on canvas
        y: Y coordinate on canvas
        name: Optional panel name
        
    Returns:
        Component creation result
    """
    async with GrasshopperHttpClient() as client:
        return await client.send_command("add_panel", {
            "x": x,
            "y": y,
            "name": name or "Panel"
        })


async def add_construct_point(x: float, y: float, name: Optional[str] = None) -> Dict[str, Any]:
    """Add a construct point component.
    
    Args:
        x: X coordinate on canvas
        y: Y coordinate on canvas
        name: Optional component name
        
    Returns:
        Component creation result
    """
    async with GrasshopperHttpClient() as client:
        return await client.send_command("add_construct_point", {
            "x": x,
            "y": y,
            "name": name or "Construct Point"
        })


async def add_line(x: float, y: float, name: Optional[str] = None) -> Dict[str, Any]:
    """Add a line component.
    
    Args:
        x: X coordinate on canvas
        y: Y coordinate on canvas
        name: Optional component name
        
    Returns:
        Component creation result
    """
    async with GrasshopperHttpClient() as client:
        return await client.send_command("add_line", {
            "x": x,
            "y": y,
            "name": name or "Line"
        })


async def add_circle(x: float, y: float, name: Optional[str] = None) -> Dict[str, Any]:
    """Add a circle component.
    
    Args:
        x: X coordinate on canvas
        y: Y coordinate on canvas
        name: Optional component name
        
    Returns:
        Component creation result
    """
    async with GrasshopperHttpClient() as client:
        return await client.send_command("add_circle", {
            "x": x,
            "y": y,
            "name": name or "Circle"
        })


async def add_python3_script(
    x: float,
    y: float,
    script: str,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """Add a Python 3 script component.
    
    Args:
        x: X coordinate on canvas
        y: Y coordinate on canvas
        script: Python script code
        name: Optional component name
        
    Returns:
        Component creation result
    """
    async with GrasshopperHttpClient() as client:
        return await client.send_command("add_python3_script", {
            "x": x,
            "y": y,
            "script": script,
            "name": name or "Python Script"
        })