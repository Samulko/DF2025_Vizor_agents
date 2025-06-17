"""Mock MCP tools for testing memory and conversation flow."""

import uuid
import json
import re
import datetime
from typing import Dict, Any, Optional, List
from smolagents import tool


class MockGrasshopperState:
    """Simulates Grasshopper's component state with realistic geometry tracking."""
    
    def __init__(self):
        self.components = {}
        self.next_error = None  # Can be set to simulate errors
        self.geometry_counter = {"bridge_curve": 0, "bridge_points": 0, "bridge_arch": 0}
        self.component_relationships = {}  # Track which components depend on others
        
    def add_component(self, comp_type: str, x: float, y: float, script: str = None) -> Dict[str, Any]:
        """Add a component and return its data with realistic naming and geometry detection."""
        comp_id = str(uuid.uuid4())
        
        # Analyze script to detect geometry type and generate realistic names
        geometry_type, realistic_name = self._analyze_script_content(script)
        
        component = {
            "id": comp_id,
            "type": comp_type,
            "name": realistic_name,
            "x": x,
            "y": y,
            "script": script,
            "has_error": self.next_error is not None,
            "geometry_type": geometry_type,
            "created_at": datetime.datetime.now().isoformat(),
            "last_modified": datetime.datetime.now().isoformat()
        }
        
        if self.next_error:
            component["error"] = self.next_error
            self.next_error = None
        else:
            # Generate realistic execution output
            component["last_output"] = self._generate_realistic_output(geometry_type, comp_id)
            
        self.components[comp_id] = component
        return component
        
    def _analyze_script_content(self, script: str) -> tuple[str, str]:
        """Analyze script content to detect geometry type and generate realistic names."""
        if not script:
            return "unknown", "Python Script"
            
        script_lower = script.lower()
        
        # Detect bridge geometry patterns
        if "curve" in script_lower and ("bridge" in script_lower or "arc" in script_lower):
            if "arch" in script_lower:
                self.geometry_counter["bridge_arch"] += 1
                return "bridge_arch", f"Bridge Arch {self.geometry_counter['bridge_arch']}"
            else:
                self.geometry_counter["bridge_curve"] += 1
                return "bridge_curve", f"Bridge Curve {self.geometry_counter['bridge_curve']}"
        elif "point" in script_lower and "bridge" in script_lower:
            self.geometry_counter["bridge_points"] += 1
            return "bridge_points", f"Bridge Points {self.geometry_counter['bridge_points']}"
        elif "curve" in script_lower:
            self.geometry_counter["bridge_curve"] += 1
            return "bridge_curve", f"Curve {self.geometry_counter['bridge_curve']}"
        else:
            return "script", "Python Script"
            
    def _generate_realistic_output(self, geometry_type: str, comp_id: str) -> str:
        """Generate realistic execution output based on geometry type."""
        outputs = {
            "bridge_curve": f"Created bridge curve with 12 control points. Curve length: 45.2m",
            "bridge_points": f"Generated 8 bridge foundation points. Span: 40m",
            "bridge_arch": f"Created arch curve with height 8m, span 35m. 15 segments generated",
            "script": f"Script executed successfully. Component ID: {comp_id[:8]}"
        }
        return outputs.get(geometry_type, f"Component {comp_id[:8]} executed successfully")
        
    def edit_component(self, comp_id: str, new_script: str) -> Dict[str, Any]:
        """Edit an existing component with realistic updates."""
        if comp_id not in self.components:
            return {"success": False, "error": f"Component {comp_id} not found"}
            
        # Update script and analyze new content
        self.components[comp_id]["script"] = new_script
        self.components[comp_id]["last_modified"] = datetime.datetime.now().isoformat()
        
        # Re-analyze script content for geometry type changes
        geometry_type, realistic_name = self._analyze_script_content(new_script)
        self.components[comp_id]["geometry_type"] = geometry_type
        
        # Check for errors (either forced or detected)
        detected_error = self._detect_script_errors(new_script)
        if self.next_error:
            self.components[comp_id]["error"] = self.next_error
            self.components[comp_id]["has_error"] = True
            self.next_error = None
        elif detected_error:
            self.components[comp_id]["error"] = detected_error
            self.components[comp_id]["has_error"] = True
        else:
            self.components[comp_id]["error"] = None
            self.components[comp_id]["has_error"] = False
            # Generate new realistic output
            self.components[comp_id]["last_output"] = self._generate_realistic_output(geometry_type, comp_id)
            
        return {"success": True, "data": self.components[comp_id]}
        
    def _detect_script_errors(self, script: str) -> Optional[str]:
        """Detect common script errors for realistic testing."""
        if not script or not script.strip():
            return "Script is empty"
            
        # Detect common Python syntax errors
        if script.count('(') != script.count(')'):
            return "SyntaxError: unmatched parentheses"
        if script.count('[') != script.count(']'):
            return "SyntaxError: unmatched brackets"
        if script.count('{') != script.count('}'):
            return "SyntaxError: unmatched braces"
            
        # Detect specific problematic patterns
        if re.search(r'\bimport\s+(?!rhino|scriptcontext|Grasshopper)', script):
            return "ImportError: unauthorized module import"
        if 'undefined_variable' in script:
            return "NameError: name 'undefined_variable' is not defined"
        if 'syntax_error' in script:
            return "SyntaxError: invalid syntax"
            
        return None
        
    def get_all_components(self) -> Dict[str, Any]:
        """Get all components."""
        return {
            "success": True,
            "data": {
                "name": "test_document",
                "path": None,
                "componentCount": len(self.components),
                "components": list(self.components.values())
            }
        }
        
    def find_components_by_type(self, geometry_type: str) -> List[Dict[str, Any]]:
        """Find components by geometry type."""
        return [comp for comp in self.components.values() 
                if comp.get("geometry_type") == geometry_type]
                
    def get_most_recent_component(self, geometry_type: str = None) -> Optional[Dict[str, Any]]:
        """Get the most recently created component, optionally filtered by type."""
        candidates = list(self.components.values())
        if geometry_type:
            candidates = [comp for comp in candidates 
                         if comp.get("geometry_type") == geometry_type]
        
        if not candidates:
            return None
            
        # Sort by creation time and return most recent
        return max(candidates, key=lambda x: x.get("created_at", ""))
        
    def get_components_with_errors(self) -> List[Dict[str, Any]]:
        """Get all components that currently have errors."""
        return [comp for comp in self.components.values() if comp.get("has_error")]
        
    def simulate_syntax_error_in_next_operation(self, error_type: str = "syntax"):
        """Set up specific error types for testing."""
        error_messages = {
            "syntax": "SyntaxError: invalid syntax at line 5",
            "runtime": "RuntimeError: geometry calculation failed",
            "import": "ImportError: unauthorized module 'os'",
            "name": "NameError: name 'undefined_var' is not defined"
        }
        self.next_error = error_messages.get(error_type, f"Error: {error_type}")
        
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state for test assertions."""
        return {
            "total_components": len(self.components),
            "components_by_type": {
                gtype: len(self.find_components_by_type(gtype)) 
                for gtype in self.geometry_counter.keys()
            },
            "components_with_errors": len(self.get_components_with_errors()),
            "geometry_counters": self.geometry_counter.copy()
        }


# Global state for the mock
grasshopper_state = MockGrasshopperState()


def create_mock_mcp_tools():
    """Create mock MCP tools that simulate Grasshopper behavior."""
    
    @tool
    def add_python3_script(
        x: float, 
        y: float, 
        script: str,
        name: Optional[str] = None,
        input_parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Mock implementation of add_python3_script MCP tool.
        
        Simulates adding a Python script component to Grasshopper.
        """
        component = grasshopper_state.add_component(
            comp_type="Python3Component",
            x=x,
            y=y,
            script=script
        )
        
        return {
            "success": True,
            "data": component,
            "error": component.get("error")
        }
    
    @tool
    def edit_python3_script(
        component_id: str,
        new_script: str
    ) -> Dict[str, Any]:
        """
        Mock implementation of edit_python3_script MCP tool.
        
        Simulates editing an existing Python script component.
        """
        result = grasshopper_state.edit_component(component_id, new_script)
        return result
    
    @tool
    def get_all_components_enhanced() -> Dict[str, Any]:
        """
        Mock implementation of get_all_components_enhanced MCP tool.
        
        Returns all components in the current Grasshopper document.
        """
        return grasshopper_state.get_all_components()
    
    @tool
    def get_component_details(component_id: str) -> Dict[str, Any]:
        """
        Mock implementation of get_component_details MCP tool.
        
        Gets detailed information about a specific component.
        """
        if component_id in grasshopper_state.components:
            return {
                "success": True,
                "data": grasshopper_state.components[component_id]
            }
        else:
            return {
                "success": False,
                "error": f"Component {component_id} not found"
            }
    
    @tool
    def run_python_script(component_id: str) -> Dict[str, Any]:
        """
        Mock implementation of run_python_script MCP tool.
        
        Simulates running a Python script component.
        """
        if component_id not in grasshopper_state.components:
            return {
                "success": False,
                "error": f"Component {component_id} not found"
            }
            
        component = grasshopper_state.components[component_id]
        
        if component.get("has_error"):
            return {
                "success": False,
                "error": component.get("error", "Script has errors")
            }
            
        # Simulate successful execution
        return {
            "success": True,
            "data": {
                "output": "Script executed successfully",
                "component_id": component_id
            }
        }
    
    @tool
    def delete_component(component_id: str) -> Dict[str, Any]:
        """
        Mock implementation of delete_component MCP tool.
        
        Simulates deleting a component from Grasshopper.
        """
        if component_id in grasshopper_state.components:
            del grasshopper_state.components[component_id]
            return {
                "success": True,
                "data": {"message": f"Component {component_id} deleted"}
            }
        else:
            return {
                "success": False,
                "error": f"Component {component_id} not found"
            }
    
    return [
        add_python3_script,
        edit_python3_script,
        get_all_components_enhanced,
        get_component_details,
        run_python_script,
        delete_component
    ]


def reset_mock_state():
    """Reset the mock Grasshopper state for fresh tests."""
    global grasshopper_state
    grasshopper_state = MockGrasshopperState()


def set_next_error(error_msg: str):
    """Set an error to occur on the next component operation."""
    grasshopper_state.next_error = error_msg


def simulate_error_type(error_type: str):
    """Simulate specific error types for testing."""
    grasshopper_state.simulate_syntax_error_in_next_operation(error_type)


def get_mock_state() -> MockGrasshopperState:
    """Get the current mock state for assertions."""
    return grasshopper_state


def get_components_by_type(geometry_type: str) -> List[Dict[str, Any]]:
    """Helper to get components by geometry type."""
    return grasshopper_state.find_components_by_type(geometry_type)


def get_most_recent_component_of_type(geometry_type: str = None) -> Optional[Dict[str, Any]]:
    """Helper to get most recent component, optionally filtered by type."""
    return grasshopper_state.get_most_recent_component(geometry_type)


def get_test_state_summary() -> Dict[str, Any]:
    """Get state summary for test assertions."""
    return grasshopper_state.get_state_summary()


def verify_no_components_have_errors() -> bool:
    """Verify that no components currently have errors."""
    return len(grasshopper_state.get_components_with_errors()) == 0