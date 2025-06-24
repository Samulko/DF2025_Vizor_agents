"""
Component Registry for tracking Grasshopper components across agents.

This registry provides centralized component tracking that survives fresh CodeAgent 
creation and enables reference resolution for natural language queries.
"""

import json
import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..tools.memory_tools import remember_component

logger = logging.getLogger(__name__)


@dataclass
class ComponentInfo:
    """Information about a Grasshopper component."""
    id: str  # Component UUID from Grasshopper
    type: str  # Inferred type (spiral_staircase, beam, column, etc.)
    name: str  # Human-readable name
    description: str  # What this component does
    location: Optional[Tuple[float, float]] = None  # Canvas coordinates (x, y)
    created_time: float = 0.0  # Unix timestamp
    modified_time: float = 0.0  # Last modification time
    properties: Dict[str, Any] = None  # Additional properties
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.created_time == 0.0:
            self.created_time = time.time()
        if self.modified_time == 0.0:
            self.modified_time = self.created_time


class ComponentRegistry:
    """
    Centralized registry for tracking Grasshopper components across agents.
    
    Features:
    - Thread-safe component CRUD operations
    - Natural language reference resolution 
    - Recent component tracking for "it" resolution
    - Type-based lookup for "the staircase", "the beam"
    - Spatial indexing for location-based queries
    - Persistence for session recovery
    """
    
    def __init__(self, max_recent: int = 20):
        """
        Initialize the component registry.
        
        Args:
            max_recent: Maximum number of recent components to track
        """
        # Core storage
        self.components: Dict[str, ComponentInfo] = {}
        self.recent_components: deque = deque(maxlen=max_recent)
        
        # Indexes for fast lookup
        self.type_index: Dict[str, Set[str]] = {}  # type -> set of component_ids
        self.name_index: Dict[str, str] = {}  # lowercase name -> component_id
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._total_registered = 0
        self._total_lookups = 0
        
        logger.info(f"ComponentRegistry initialized (max_recent={max_recent})")
    
    def register_component(self, component_id: str, component_type: str, 
                         name: str, description: str = "", 
                         location: Optional[Tuple[float, float]] = None,
                         properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a new component in the registry.
        
        Args:
            component_id: Unique component identifier from Grasshopper
            component_type: Type of component (spiral_staircase, beam, etc.)
            name: Human-readable name
            description: Description of what this component does
            location: Canvas coordinates (x, y)
            properties: Additional component properties
            
        Returns:
            True if registered successfully, False if already exists
        """
        with self._lock:
            if component_id in self.components:
                logger.warning(f"Component {component_id} already registered")
                return False
            
            # Create component info
            component_info = ComponentInfo(
                id=component_id,
                type=component_type,
                name=name,
                description=description,
                location=location,
                properties=properties or {}
            )
            
            # Store in main registry
            self.components[component_id] = component_info
            
            # Update indexes
            self._update_indexes(component_id, component_info)
            
            # Store in persistent memory
            try:
                remember_component(component_id, component_type, description if description else name)
                logger.info(f"Component {component_id} stored in persistent memory")
            except Exception as e:
                logger.warning(f"Failed to store component in memory: {e}")
            
            # Track as recent
            self.recent_components.append(component_id)
            
            # Statistics
            self._total_registered += 1
            
            logger.info(f"Registered component: {component_id} ({component_type}) - {name}")
            return True
    
    def update_component(self, component_id: str, **updates) -> bool:
        """
        Update an existing component.
        
        Args:
            component_id: Component to update
            **updates: Fields to update
            
        Returns:
            True if updated successfully, False if not found
        """
        with self._lock:
            if component_id not in self.components:
                logger.warning(f"Component {component_id} not found for update")
                return False
            
            component = self.components[component_id]
            old_type = component.type
            old_name = component.name
            
            # Update fields
            for key, value in updates.items():
                if hasattr(component, key):
                    setattr(component, key, value)
            
            component.modified_time = time.time()
            
            # Update indexes if type or name changed
            if old_type != component.type or old_name != component.name:
                self._remove_from_indexes(component_id, old_type, old_name)
                self._update_indexes(component_id, component)
            
            # Move to front of recent list
            if component_id in self.recent_components:
                self.recent_components.remove(component_id)
            self.recent_components.append(component_id)
            
            # Update in persistent memory
            try:
                description = component.description if component.description else component.name
                remember_component(component_id, component.type, description)
                logger.info(f"Component {component_id} updated in persistent memory")
            except Exception as e:
                logger.warning(f"Failed to update component in memory: {e}")
            
            logger.info(f"Updated component: {component_id}")
            return True
    
    def get_component(self, component_id: str) -> Optional[ComponentInfo]:
        """
        Get component information by ID.
        
        Args:
            component_id: Component identifier
            
        Returns:
            ComponentInfo if found, None otherwise
        """
        with self._lock:
            self._total_lookups += 1
            return self.components.get(component_id)
    
    def resolve_reference(self, user_input: str) -> List[str]:
        """
        Resolve natural language references to component IDs.
        Specialized for timber truss bridge construction terminology.
        
        Args:
            user_input: User's natural language reference
            
        Returns:
            List of matching component IDs (ordered by relevance)
        """
        with self._lock:
            self._total_lookups += 1
            user_lower = user_input.lower().strip()
            
            # Direct ID match
            if user_lower in self.components:
                return [user_lower]
            
            # Recent work references
            if user_lower in ["it", "that", "this", "what i just made", "my last creation", "the last one", 
                             "the script", "that script", "this script", "the component", "that component", 
                             "this component", "the last component", "what i just created"]:
                if self.recent_components:
                    return [self.recent_components[-1]]
                return []
            
            # Timber truss bridge specific patterns
            
            # STRUCTURAL ELEMENTS - "the [element]"
            structural_elements = {
                # Truss components
                "top chord": ["top_chord", "upper_chord", "compression_chord"],
                "bottom chord": ["bottom_chord", "lower_chord", "tension_chord"],
                "web member": ["web_member", "diagonal", "vertical"],
                "diagonal": ["diagonal", "web_member", "brace"],
                "vertical": ["vertical", "post", "web_member"],
                "strut": ["strut", "compression_member"],
                "tie": ["tie", "tension_member"],
                
                # Bridge structure  
                "truss": ["truss", "triangular_truss"],
                "span": ["span", "main_span"],
                "deck": ["deck", "bridge_deck", "roadway"],
                "bearing": ["bearing", "support"],
                "abutment": ["abutment", "end_support"],
                "pier": ["pier", "intermediate_support"],
                
                # Timber elements
                "beam": ["beam", "timber_beam", "rectangular_beam"],
                "post": ["post", "vertical_post", "timber_post"],
                "brace": ["brace", "diagonal_brace", "cross_brace"],
                "plank": ["plank", "deck_plank", "timber_plank"],
                "joint": ["joint", "connection", "timber_joint"],
                "gusset": ["gusset", "gusset_plate", "connection_plate"],
                
                # Grasshopper specific terms
                "script": ["python_script", "script_component", "component"],
                "component": ["grasshopper_component", "gh_component", "python_component"],
                "python": ["python_script", "python3_script", "script"],
                "geometry": ["geometry_component", "geometric_element"],
                "node": ["grasshopper_node", "component", "gh_node"],
                "definition": ["grasshopper_definition", "gh_definition"],
                "canvas": ["grasshopper_canvas", "gh_canvas"],
                "parameter": ["input_parameter", "output_parameter", "gh_parameter"]
            }
            
            # Check for "the [structural element]" patterns
            if user_lower.startswith("the "):
                element_name = user_lower[4:]  # Remove "the "
                
                # Direct structural element match
                if element_name in structural_elements:
                    for element_type in structural_elements[element_name]:
                        matches = self.find_by_type(element_type, limit=3)
                        if matches:
                            return matches
                
                # Fallback to general type search
                return self.find_by_type(element_name, limit=1)
            
            # POSITIONAL REFERENCES - timber bridge specific
            positional_patterns = {
                # Horizontal positions
                ("left", "west"): lambda: self._find_by_position("left"),
                ("right", "east"): lambda: self._find_by_position("right"),
                ("center", "middle", "central"): lambda: self._find_by_position("center"),
                
                # Vertical positions  
                ("top", "upper", "high"): lambda: self._find_by_position("top"),
                ("bottom", "lower", "low"): lambda: self._find_by_position("bottom"),
                
                # Bridge specific positions
                ("upstream", "north"): lambda: self._find_by_position("upstream"),
                ("downstream", "south"): lambda: self._find_by_position("downstream"),
                ("far end", "far side"): lambda: self._find_by_position("far"),
                ("near end", "near side", "this end"): lambda: self._find_by_position("near"),
                
                # Span positions
                ("first span", "span 1"): lambda: self._find_by_span(1),
                ("second span", "span 2"): lambda: self._find_by_span(2),
                ("main span", "center span"): lambda: self._find_by_span("main"),
                ("end span", "side span"): lambda: self._find_by_span("end")
            }
            
            for position_words, finder_func in positional_patterns.items():
                if any(pos in user_lower for pos in position_words):
                    try:
                        results = finder_func()
                        if results:
                            return results
                    except:
                        pass  # Continue to other patterns
            
            # TIMBER & GRASSHOPPER SPECIFIC PATTERNS
            component_patterns = {
                # Material references
                ("timber", "wood"): lambda: self._find_by_material("timber"),
                ("steel", "metal"): lambda: self._find_by_material("steel"),
                
                # Size references
                ("big", "large", "major"): lambda: self._find_by_size("large"),
                ("small", "minor", "little"): lambda: self._find_by_size("small"),
                ("main", "primary", "principal"): lambda: self._find_by_importance("main"),
                ("secondary", "auxiliary"): lambda: self._find_by_importance("secondary"),
                
                # Shape references
                ("rectangular", "square"): lambda: self._find_by_shape("rectangular"),
                ("triangular", "triangle"): lambda: self._find_by_shape("triangular"),
                
                # Function references
                ("compression", "pushing"): lambda: self._find_by_function("compression"),
                ("tension", "pulling"): lambda: self._find_by_function("tension"),
                ("connection", "connecting"): lambda: self._find_by_function("connection"),
                
                # Grasshopper workflow references
                ("broken", "error", "failed"): lambda: self._find_by_status("error"),
                ("working", "green", "success"): lambda: self._find_by_status("success"),
                ("warning", "orange", "yellow"): lambda: self._find_by_status("warning"),
                ("disabled", "gray", "grey"): lambda: self._find_by_status("disabled"),
                
                # Grasshopper component state
                ("selected", "highlighted"): lambda: self._find_by_state("selected"),
                ("preview", "visible"): lambda: self._find_by_state("preview"),
                ("baked", "permanent"): lambda: self._find_by_state("baked"),
                
                # Code/script references
                ("python", "script", "code"): lambda: self._find_by_type_category("script"),
                ("inputs", "parameters", "params"): lambda: self._find_by_type_category("input"),
                ("outputs", "results"): lambda: self._find_by_type_category("output")
            }
            
            for pattern_words, finder_func in component_patterns.items():
                if any(word in user_lower for word in pattern_words):
                    try:
                        results = finder_func()
                        if results:
                            return results
                    except:
                        pass
            
            # QUANTITY REFERENCES
            if any(word in user_lower for word in ["all", "every", "each"]):
                # Return multiple recent components
                return list(reversed(list(self.recent_components)))[:10]
            
            # Direct name match
            if user_lower in self.name_index:
                return [self.name_index[user_lower]]
            
            # Partial name or type match (fallback)
            matches = []
            for name, comp_id in self.name_index.items():
                if user_lower in name or name in user_lower:
                    matches.append(comp_id)
            
            # Type partial match
            for comp_type, comp_ids in self.type_index.items():
                if user_lower in comp_type or comp_type in user_lower:
                    matches.extend(list(comp_ids))
            
            # Remove duplicates while preserving order
            seen = set()
            unique_matches = []
            for comp_id in matches:
                if comp_id not in seen:
                    seen.add(comp_id)
                    unique_matches.append(comp_id)
            
            return unique_matches[:5]  # Limit to top 5 matches
    
    def find_by_type(self, component_type: str, limit: int = 10) -> List[str]:
        """
        Find components by type.
        
        Args:
            component_type: Type to search for
            limit: Maximum number of results
            
        Returns:
            List of component IDs (most recent first)
        """
        with self._lock:
            self._total_lookups += 1
            
            # Exact type match
            if component_type in self.type_index:
                comp_ids = list(self.type_index[component_type])
                # Sort by creation time (most recent first)
                comp_ids.sort(key=lambda cid: self.components[cid].created_time, reverse=True)
                return comp_ids[:limit]
            
            # Partial type match
            matches = []
            for comp_type, comp_ids in self.type_index.items():
                if component_type.lower() in comp_type.lower():
                    matches.extend(comp_ids)
            
            # Sort by creation time (most recent first)
            matches.sort(key=lambda cid: self.components[cid].created_time, reverse=True)
            return matches[:limit]
    
    def find_recent(self, limit: int = 5) -> List[str]:
        """
        Get most recently created/modified components.
        
        Args:
            limit: Maximum number of components to return
            
        Returns:
            List of component IDs (most recent first)
        """
        with self._lock:
            self._total_lookups += 1
            return list(reversed(list(self.recent_components)))[:limit]
    
    def get_all_components(self) -> Dict[str, ComponentInfo]:
        """
        Get all registered components.
        
        Returns:
            Dictionary of component_id -> ComponentInfo
        """
        with self._lock:
            self._total_lookups += 1
            return self.components.copy()
    
    def remove_component(self, component_id: str) -> bool:
        """
        Remove a component from the registry.
        
        Args:
            component_id: Component to remove
            
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if component_id not in self.components:
                return False
            
            component = self.components[component_id]
            
            # Remove from indexes
            self._remove_from_indexes(component_id, component.type, component.name)
            
            # Remove from main registry
            del self.components[component_id]
            
            # Remove from recent list
            if component_id in self.recent_components:
                self.recent_components.remove(component_id)
            
            logger.info(f"Removed component: {component_id}")
            return True
    
    def clear(self):
        """Clear all components from the registry."""
        with self._lock:
            self.components.clear()
            self.recent_components.clear()
            self.type_index.clear()
            self.name_index.clear()
            logger.info("ComponentRegistry cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with registry statistics
        """
        with self._lock:
            return {
                "total_components": len(self.components),
                "total_registered": self._total_registered,
                "total_lookups": self._total_lookups,
                "recent_components": len(self.recent_components),
                "types": list(self.type_index.keys()),
                "type_counts": {t: len(ids) for t, ids in self.type_index.items()},
                "oldest_component": min(
                    (c.created_time for c in self.components.values()), 
                    default=0
                ),
                "newest_component": max(
                    (c.created_time for c in self.components.values()), 
                    default=0
                )
            }
    
    def export_to_json(self, file_path: Optional[Path] = None) -> str:
        """
        Export registry to JSON.
        
        Args:
            file_path: Optional file path to save to
            
        Returns:
            JSON string representation
        """
        with self._lock:
            data = {
                "components": {cid: asdict(comp) for cid, comp in self.components.items()},
                "recent_components": list(self.recent_components),
                "stats": self.get_stats(),
                "export_time": time.time()
            }
            
            json_str = json.dumps(data, indent=2, default=str)
            
            if file_path:
                file_path.write_text(json_str)
                logger.info(f"Registry exported to {file_path}")
            
            return json_str
    
    def import_from_json(self, json_str: str) -> bool:
        """
        Import registry from JSON.
        
        Args:
            json_str: JSON string to import
            
        Returns:
            True if imported successfully
        """
        try:
            with self._lock:
                data = json.loads(json_str)
                
                # Clear existing data
                self.clear()
                
                # Import components
                for comp_id, comp_data in data.get("components", {}).items():
                    component = ComponentInfo(**comp_data)
                    self.components[comp_id] = component
                    self._update_indexes(comp_id, component)
                
                # Import recent components
                for comp_id in data.get("recent_components", []):
                    if comp_id in self.components:
                        self.recent_components.append(comp_id)
                
                logger.info(f"Registry imported: {len(self.components)} components")
                return True
                
        except Exception as e:
            logger.error(f"Failed to import registry: {e}")
            return False
    
    def _update_indexes(self, component_id: str, component: ComponentInfo):
        """Update search indexes for a component."""
        # Type index
        if component.type not in self.type_index:
            self.type_index[component.type] = set()
        self.type_index[component.type].add(component_id)
        
        # Name index
        self.name_index[component.name.lower()] = component_id
    
    def _remove_from_indexes(self, component_id: str, old_type: str, old_name: str):
        """Remove component from search indexes."""
        # Type index
        if old_type in self.type_index:
            self.type_index[old_type].discard(component_id)
            if not self.type_index[old_type]:
                del self.type_index[old_type]
        
        # Name index
        if old_name.lower() in self.name_index:
            del self.name_index[old_name.lower()]
    
    # Helper methods for timber truss bridge reference resolution
    
    def _find_by_position(self, position: str) -> List[str]:
        """Find components by position (left, right, top, bottom, etc.)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check component properties for position indicators
            if component.properties and position in str(component.properties.get('position', '')).lower():
                matches.append(comp_id)
            # Check component name for position indicators  
            elif position in component.name.lower():
                matches.append(comp_id)
            # Check location coordinates if available
            elif component.location and position in ["left", "right"]:
                if position == "left" and component.location[0] < 0:
                    matches.append(comp_id)
                elif position == "right" and component.location[0] > 0:
                    matches.append(comp_id)
        return matches[:5]
    
    def _find_by_span(self, span_id) -> List[str]:
        """Find components by span number or type"""
        matches = []
        for comp_id, component in self.components.items():
            span_info = str(component.properties.get('span', '')).lower()
            if str(span_id).lower() in span_info or str(span_id).lower() in component.name.lower():
                matches.append(comp_id)
        return matches[:5]
    
    def _find_by_material(self, material: str) -> List[str]:
        """Find components by material (timber, steel, etc.)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check properties for material
            if component.properties and material in str(component.properties.get('material', '')).lower():
                matches.append(comp_id)
            # Check component type for material indicators
            elif material in component.type.lower():
                matches.append(comp_id)
            # Check component name for material
            elif material in component.name.lower():
                matches.append(comp_id)
        return matches[:5]
    
    def _find_by_size(self, size: str) -> List[str]:
        """Find components by size (large, small, etc.)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check properties for size indicators
            if component.properties:
                size_info = str(component.properties.get('size', '')).lower()
                dimensions = component.properties.get('dimensions', {})
                if size in size_info or size in component.name.lower():
                    matches.append(comp_id)
                # Size based on actual dimensions if available
                elif isinstance(dimensions, dict) and dimensions:
                    volume = dimensions.get('width', 1) * dimensions.get('height', 1) * dimensions.get('length', 1)
                    if size == "large" and volume > 100:  # Arbitrary threshold
                        matches.append(comp_id)
                    elif size == "small" and volume < 10:
                        matches.append(comp_id)
        return matches[:5]
    
    def _find_by_importance(self, importance: str) -> List[str]:
        """Find components by structural importance (main, secondary, etc.)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check properties and name for importance indicators
            if (component.properties and importance in str(component.properties.get('importance', '')).lower()) or \
               importance in component.name.lower() or \
               importance in component.type.lower():
                matches.append(comp_id)
            # Main structural elements (top chords, bottom chords)
            elif importance == "main" and any(main_type in component.type.lower() 
                                            for main_type in ["top_chord", "bottom_chord", "main_span", "truss"]):
                matches.append(comp_id)
        return matches[:5]
    
    def _find_by_shape(self, shape: str) -> List[str]:
        """Find components by shape (rectangular, triangular, etc.)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check properties for shape
            if component.properties and shape in str(component.properties.get('shape', '')).lower():
                matches.append(comp_id)
            # Check component type for shape indicators
            elif shape in component.type.lower():
                matches.append(comp_id)
            # Infer shape from component type
            elif shape == "rectangular" and any(rect_type in component.type.lower() 
                                              for rect_type in ["beam", "post", "plank"]):
                matches.append(comp_id)
            elif shape == "triangular" and "truss" in component.type.lower():
                matches.append(comp_id)
        return matches[:5]
    
    def _find_by_function(self, function: str) -> List[str]:
        """Find components by structural function (compression, tension, connection)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check properties for function
            if component.properties and function in str(component.properties.get('function', '')).lower():
                matches.append(comp_id)
            # Infer function from component type
            elif function == "compression" and any(comp_type in component.type.lower() 
                                                 for comp_type in ["top_chord", "strut", "post", "column"]):
                matches.append(comp_id)
            elif function == "tension" and any(comp_type in component.type.lower() 
                                             for comp_type in ["bottom_chord", "tie", "cable"]):
                matches.append(comp_id)
            elif function == "connection" and any(comp_type in component.type.lower() 
                                                for comp_type in ["joint", "gusset", "bearing"]):
                matches.append(comp_id)
        return matches[:5]
    
    def _find_by_status(self, status: str) -> List[str]:
        """Find components by Grasshopper status (error, success, warning, disabled)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check properties for status indicators
            if component.properties:
                component_status = str(component.properties.get('status', '')).lower()
                execution_state = str(component.properties.get('execution_state', '')).lower()
                if status in component_status or status in execution_state:
                    matches.append(comp_id)
            # Check component name for status indicators
            elif status in component.name.lower():
                matches.append(comp_id)
        return matches[:5]
    
    def _find_by_state(self, state: str) -> List[str]:
        """Find components by Grasshopper display state (selected, preview, baked)"""
        matches = []
        for comp_id, component in self.components.items():
            # Check properties for state indicators
            if component.properties:
                component_state = str(component.properties.get('state', '')).lower()
                display_state = str(component.properties.get('display_state', '')).lower()
                if state in component_state or state in display_state:
                    matches.append(comp_id)
            # Check component name for state indicators
            elif state in component.name.lower():
                matches.append(comp_id)
        return matches[:5]
    
    def _find_by_type_category(self, category: str) -> List[str]:
        """Find components by type category (script, input, output)"""
        matches = []
        category_types = {
            "script": ["python_script", "python3_script", "script_component", "code"],
            "input": ["input_parameter", "parameter", "slider", "panel"],
            "output": ["output_parameter", "panel", "text_display"]
        }
        
        target_types = category_types.get(category, [category])
        
        for comp_id, component in self.components.items():
            # Check if component type matches category
            if any(comp_type in component.type.lower() for comp_type in target_types):
                matches.append(comp_id)
            # Check component name for category indicators
            elif any(comp_type in component.name.lower() for comp_type in target_types):
                matches.append(comp_id)
        return matches[:5]


# Global registry instance (singleton pattern)
_global_registry: Optional[ComponentRegistry] = None
_registry_lock = threading.Lock()


def get_global_registry() -> ComponentRegistry:
    """
    Get the global component registry instance.
    
    Returns:
        Global ComponentRegistry instance
    """
    global _global_registry
    with _registry_lock:
        if _global_registry is None:
            _global_registry = ComponentRegistry()
        return _global_registry


def reset_global_registry():
    """Reset the global registry instance."""
    global _global_registry
    with _registry_lock:
        if _global_registry is not None:
            _global_registry.clear()
        _global_registry = None


def initialize_registry() -> ComponentRegistry:
    """
    Initialize and return the global registry.
    
    Returns:
        Initialized ComponentRegistry instance
    """
    registry = get_global_registry()
    logger.info("Global ComponentRegistry initialized")
    return registry