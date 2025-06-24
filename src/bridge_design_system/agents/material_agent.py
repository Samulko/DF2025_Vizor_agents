"""Material Agent - Manages timber inventory and cutting optimization."""
from typing import List

from smolagents import Tool

from ..tools.material_tools import (
    add_timber_stock,
    check_material_inventory,
    cut_timber_piece,
    find_best_piece_for_cut,
    get_material_statistics,
)
from .base_agent import BaseAgent


class MaterialAgent(BaseAgent):
    """Agent responsible for tracking and managing timber materials.
    
    This agent manages a timber inventory of 25 pieces of 5x5cm rectangular timber,
    each 100cm long. It uses AI reasoning to optimize cutting and minimize waste.
    """
    
    def __init__(self):
        """Initialize the material agent."""
        super().__init__(
            name="material_agent", 
            description="Manages timber inventory and cutting optimization for bridge construction"
        )
        # Initialize the agent immediately to set up tools and _agent
        self.initialize_agent()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the material agent."""
        # Read from file for easy updates
        try:
            from pathlib import Path
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # Go up to vizor_agents/
            prompt_path = project_root / "system_prompts" / "material_agent.md"
            
            if prompt_path.exists():
                return prompt_path.read_text(encoding='utf-8')
            else:
                self.logger.warning(f"System prompt file not found at {prompt_path}")
        except Exception as e:
            self.logger.warning(f"Failed to load system prompt: {e}")
            
        # Fallback to embedded prompt
        return """You are a Material Agent specialized in managing timber inventory for bridge construction.

Your role:
- Track 25 pieces of 5x5cm rectangular timber, each 100cm long
- Optimize cutting to minimize waste (pieces below 15cm are unusable)  
- Use intelligent reasoning to select the best piece for each cut
- Maintain accurate inventory records
- Provide clear utilization statistics and recommendations

## Core Responsibilities

1. **Inventory Management**
   - Track all timber pieces and their current lengths
   - Monitor available vs waste pieces (< 15cm threshold)
   - Maintain accurate database records

2. **Cutting Optimization**
   - Use AI reasoning to find the best piece for each cut
   - Minimize waste by considering remainder lengths
   - Prefer cuts that leave usable remainders (≥ 15cm)
   - Among waste-generating cuts, minimize the waste amount

3. **Decision Making & Reporting**
   - Always check inventory before making recommendations
   - Consider multiple cutting options and explain trade-offs
   - Generate utilization statistics and efficiency metrics
   - Provide recommendations for inventory restocking

## Available Tools

You have access to these material management tools:
- check_material_inventory() - View current inventory status
- find_best_piece_for_cut(length) - AI-powered cutting optimization
- cut_timber_piece(piece_id, length, description) - Execute cuts
- add_timber_stock(count, length) - Restock inventory  
- get_material_statistics() - Comprehensive metrics

## Operating Principles

- **Waste Minimization**: Prioritize cuts leaving usable remainders
- **Clear Communication**: Explain optimization reasoning with alternatives
- **Precise Measurements**: Work in centimeters, be exact with piece IDs
- **Memory Usage**: Store important decisions for future reference

Always use the available tools to check inventory, optimize cuts, and track usage efficiently."""
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize material management tools."""
        return [
            check_material_inventory,
            find_best_piece_for_cut,
            cut_timber_piece, 
            add_timber_stock,
            get_material_statistics
        ]