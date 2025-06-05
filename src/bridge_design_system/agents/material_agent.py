"""Material Agent - Manages construction material inventory and constraints."""
from typing import List

from smolagents import Tool, tool

from .base_agent import BaseAgent


class MaterialAgent(BaseAgent):
    """Agent responsible for tracking and managing construction materials.
    
    This agent interfaces with a material database to track inventory,
    check availability, and optimize material usage for bridge construction.
    """
    
    def __init__(self):
        """Initialize the material agent."""
        super().__init__(
            name="material_agent",
            description="Manages construction material inventory and availability for bridge design"
        )
        
        # Placeholder material database (will be replaced with real DB in Phase 3)
        self.material_inventory = {
            "steel_beam_I_300": {"quantity": 50, "length": 12.0, "section": "I-300"},
            "steel_beam_I_400": {"quantity": 30, "length": 12.0, "section": "I-400"},
            "steel_beam_box_200": {"quantity": 40, "length": 10.0, "section": "Box-200x200"},
            "steel_beam_box_300": {"quantity": 25, "length": 10.0, "section": "Box-300x300"},
            "tension_cable_20": {"quantity": -1, "diameter": 20, "type": "cable"},  # -1 means unlimited
            "tension_cable_30": {"quantity": -1, "diameter": 30, "type": "cable"},
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the material agent."""
        return """You are an expert Material Management Agent for bridge construction.

Your responsibilities:
1. Track available construction materials in the inventory
2. Check material availability for specific design requirements
3. Suggest material optimizations to minimize waste
4. Flag potential material shortages before they impact construction
5. Provide material specifications and properties

Available materials:
- Linear steel elements with different cross-sections (I-beams, box sections)
- Each element has specific length and quantity constraints
- Tension cables (unlimited quantity)
- Materials are tracked by type, section, length, and available quantity

Operating principles:
- Always check current inventory before confirming availability
- Suggest alternatives when requested materials are insufficient
- Consider material efficiency and waste minimization
- Report clear quantities and specifications
- Alert when inventory is running low (less than 20% remaining)

You have access to tools for:
- Querying material inventory
- Checking availability for specific requirements
- Updating material usage
- Calculating material requirements
- Suggesting material alternatives"""
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize material management tools."""
        
        @tool
        def check_material_inventory(material_type: str = "all") -> dict:
            """Check current material inventory.
            
            Args:
                material_type: Specific material type or "all" for full inventory
                
            Returns:
                Dictionary with inventory details
            """
            if material_type == "all":
                return {
                    "inventory": self.material_inventory,
                    "total_types": len(self.material_inventory),
                    "categories": {
                        "beams": sum(1 for k, v in self.material_inventory.items() if v.get("type") != "cable"),
                        "cables": sum(1 for k, v in self.material_inventory.items() if v.get("type") == "cable")
                    }
                }
            elif material_type in self.material_inventory:
                return {
                    "material": material_type,
                    "details": self.material_inventory[material_type],
                    "available": self.material_inventory[material_type]["quantity"] != 0
                }
            else:
                return {
                    "error": f"Material type '{material_type}' not found in inventory",
                    "available_types": list(self.material_inventory.keys())
                }
        
        @tool
        def check_material_availability(material_type: str, required_quantity: int) -> dict:
            """Check if required quantity of material is available.
            
            Args:
                material_type: Type of material needed
                required_quantity: Number of units required
                
            Returns:
                Availability status and details
            """
            if material_type not in self.material_inventory:
                return {
                    "available": False,
                    "reason": "Material type not in inventory",
                    "suggestion": f"Available types: {list(self.material_inventory.keys())}"
                }
            
            material = self.material_inventory[material_type]
            current_qty = material["quantity"]
            
            # Unlimited materials (cables)
            if current_qty == -1:
                return {
                    "available": True,
                    "material": material_type,
                    "required": required_quantity,
                    "in_stock": "unlimited",
                    "remaining_after": "unlimited"
                }
            
            # Limited materials
            is_available = current_qty >= required_quantity
            return {
                "available": is_available,
                "material": material_type,
                "required": required_quantity,
                "in_stock": current_qty,
                "shortage": max(0, required_quantity - current_qty) if not is_available else 0,
                "remaining_after": current_qty - required_quantity if is_available else 0,
                "low_stock_warning": current_qty < 10
            }
        
        @tool
        def calculate_material_requirements(element_type: str, length: float, quantity: int = 1) -> dict:
            """Calculate material requirements for structural elements.
            
            Args:
                element_type: Type of structural element
                length: Required length in meters
                quantity: Number of elements needed
                
            Returns:
                Material requirements and suggestions
            """
            suggestions = []
            
            # Find suitable materials
            suitable_materials = []
            for mat_type, mat_info in self.material_inventory.items():
                if mat_info.get("type") == "cable" and "cable" in element_type.lower():
                    suitable_materials.append({
                        "type": mat_type,
                        "info": mat_info,
                        "pieces_needed": quantity
                    })
                elif mat_info.get("type") != "cable" and "beam" in element_type.lower():
                    if mat_info["length"] >= length:
                        suitable_materials.append({
                            "type": mat_type,
                            "info": mat_info,
                            "pieces_needed": quantity
                        })
            
            return {
                "element_type": element_type,
                "required_length": length,
                "quantity": quantity,
                "suitable_materials": suitable_materials,
                "total_options": len(suitable_materials)
            }
        
        @tool
        def update_material_usage(material_type: str, quantity_used: int) -> dict:
            """Update material inventory after usage.
            
            Args:
                material_type: Type of material used
                quantity_used: Number of units used
                
            Returns:
                Updated inventory status
            """
            if material_type not in self.material_inventory:
                return {"error": f"Material type '{material_type}' not found"}
            
            material = self.material_inventory[material_type]
            
            # Don't update unlimited materials
            if material["quantity"] == -1:
                return {
                    "material": material_type,
                    "used": quantity_used,
                    "remaining": "unlimited",
                    "updated": True
                }
            
            # Check if enough material
            if material["quantity"] < quantity_used:
                return {
                    "error": "Insufficient material",
                    "available": material["quantity"],
                    "requested": quantity_used
                }
            
            # Update inventory
            material["quantity"] -= quantity_used
            
            return {
                "material": material_type,
                "used": quantity_used,
                "remaining": material["quantity"],
                "updated": True,
                "low_stock_warning": material["quantity"] < 10
            }
        
        @tool
        def suggest_material_alternatives(original_type: str, reason: str = "shortage") -> dict:
            """Suggest alternative materials.
            
            Args:
                original_type: Originally requested material
                reason: Reason for needing alternatives
                
            Returns:
                Alternative material suggestions
            """
            alternatives = []
            original = self.material_inventory.get(original_type, {})
            
            for mat_type, mat_info in self.material_inventory.items():
                if mat_type != original_type:
                    # Similar type materials
                    if mat_info.get("type") == original.get("type"):
                        alternatives.append({
                            "type": mat_type,
                            "info": mat_info,
                            "similarity": "same_category"
                        })
                    # Compatible materials
                    elif (original.get("section", "").startswith("I") and 
                          mat_info.get("section", "").startswith("I")):
                        alternatives.append({
                            "type": mat_type,
                            "info": mat_info,
                            "similarity": "compatible_section"
                        })
            
            return {
                "original_request": original_type,
                "reason": reason,
                "alternatives": alternatives,
                "alternative_count": len(alternatives)
            }
        
        return [
            check_material_inventory,
            check_material_availability,
            calculate_material_requirements,
            update_material_usage,
            suggest_material_alternatives
        ]