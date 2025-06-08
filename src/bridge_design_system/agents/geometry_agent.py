"""Geometry Agent - Handles 3D geometry operations in Rhino/Grasshopper."""
from typing import List

from smolagents import Tool, tool

from .base_agent import BaseAgent
from ..config.settings import settings
from ..mcp.smolagents_integration import get_grasshopper_tools


class GeometryAgent(BaseAgent):
    """Agent responsible for creating and manipulating 3D geometry.
    
    This agent interfaces with Rhino/Grasshopper through official MCP to create,
    modify, and analyze bridge geometry.
    """
    
    def __init__(self):
        """Initialize the geometry agent."""
        super().__init__(
            name="geometry_agent",
            description="Creates and manipulates 3D geometry for bridge design in Rhino/Grasshopper"
        )
        
        # MCP connection will be established when tools are initialized
        self.mcp_connected = False
        self.use_official_mcp = True  # Use official MCP implementation
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the geometry agent."""
        return """You are an expert Geometry Agent for bridge design in Rhino/Grasshopper.

Your responsibilities:
1. Create and manipulate 3D geometry based on design requirements
2. Work methodically step by step, only creating what is specifically requested
3. Generate points, curves, surfaces, and solid geometry as needed
4. Perform geometric analysis and transformations
5. Ensure all geometry is valid and suitable for bridge construction

Operating principles:
- Only create geometry that has been explicitly requested
- Provide clear feedback about what geometry was created
- Report any issues with invalid or problematic geometry
- Maintain precision appropriate for structural engineering
- Use appropriate units (typically meters for bridge design)

You have access to tools for:
- Creating points, lines, curves, and surfaces
- Performing transformations (move, rotate, scale, etc.)
- Analyzing geometric properties
- Boolean operations
- Mesh generation for visualization

Always confirm successful operations and provide relevant geometric data."""
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize geometry tools using official MCP or fallback to placeholders."""
        
        if self.use_official_mcp:
            try:
                # Use streamable-http MCP integration with smolagents MCPClient
                mcp_server_url = getattr(settings, 'mcp_server_url', 'http://localhost:8001/mcp')
                mcp_tools = get_grasshopper_tools(mcp_server_url)
                
                if mcp_tools:
                    self.mcp_connected = True
                    self.logger.info(f"Geometry agent initialized with {len(mcp_tools)} streamable-http MCP tools")
                    return mcp_tools
                else:
                    raise Exception("No tools returned from MCP server")
                    
            except Exception as e:
                self.logger.warning(f"Failed to initialize MCP tools, falling back to placeholders: {e}")
                self.mcp_connected = False
        
        # Fallback to placeholder tools for testing/development
        @tool
        def create_point(x: float, y: float, z: float, name: str = "") -> dict:
            """Create a 3D point in Rhino space.
            
            Args:
                x: X coordinate in meters
                y: Y coordinate in meters
                z: Z coordinate in meters
                name: Optional name for the point
                
            Returns:
                Dictionary with point data
            """
            # Placeholder implementation
            point_data = {
                "type": "point",
                "coordinates": {"x": x, "y": y, "z": z},
                "name": name or f"Point_{x}_{y}_{z}",
                "id": f"pt_{abs(hash(f'{x}{y}{z}'))}"
            }
            return point_data
        
        @tool
        def create_line(start_point: dict, end_point: dict, name: str = "") -> dict:
            """Create a line between two points.
            
            Args:
                start_point: Starting point dictionary
                end_point: Ending point dictionary
                name: Optional name for the line
                
            Returns:
                Dictionary with line data
            """
            # Placeholder implementation
            line_data = {
                "type": "line",
                "start": start_point,
                "end": end_point,
                "name": name or "Line",
                "length": ((end_point["coordinates"]["x"] - start_point["coordinates"]["x"])**2 +
                          (end_point["coordinates"]["y"] - start_point["coordinates"]["y"])**2 +
                          (end_point["coordinates"]["z"] - start_point["coordinates"]["z"])**2)**0.5
            }
            return line_data
        
        @tool
        def create_curve(points: list, degree: int = 3, name: str = "") -> dict:
            """Create a NURBS curve through points.
            
            Args:
                points: List of point dictionaries
                degree: Curve degree (1=linear, 3=cubic)
                name: Optional name for the curve
                
            Returns:
                Dictionary with curve data
            """
            # Placeholder implementation
            curve_data = {
                "type": "curve",
                "points": points,
                "degree": degree,
                "name": name or "Curve",
                "point_count": len(points)
            }
            return curve_data
        
        @tool
        def analyze_geometry(geometry: dict, analysis_type: str = "properties") -> dict:
            """Analyze geometric properties.
            
            Args:
                geometry: Geometry to analyze
                analysis_type: Type of analysis (properties, validity, intersections)
                
            Returns:
                Analysis results
            """
            # Placeholder implementation
            analysis = {
                "geometry_type": geometry.get("type", "unknown"),
                "analysis_type": analysis_type,
                "valid": True,
                "properties": {
                    "has_transforms": geometry.get("transformed", False)
                }
            }
            
            if geometry.get("type") == "line" and "length" in geometry:
                analysis["properties"]["length"] = geometry["length"]
            
            return analysis
        
        self.logger.info("Geometry agent initialized with placeholder tools")
        return [
            create_point,
            create_line,
            create_curve,
            analyze_geometry
        ]