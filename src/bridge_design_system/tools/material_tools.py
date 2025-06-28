"""
Material tracking and cutting optimization utilities for bridge design system.

This module provides shared functionality for material inventory management,
cutting sequence optimization, and waste minimization algorithms.
"""

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MaterialCut:
    """Represents a single cut made on a beam."""

    element_id: str
    length_mm: int
    position_mm: int  # Position where cut starts on the beam
    kerf_loss_mm: int = 3
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class BeamUtilization:
    """Represents utilization status of a single beam."""

    beam_id: str
    original_length_mm: int
    remaining_length_mm: int
    cuts: List[MaterialCut]
    waste_mm: int
    utilization_percent: float

    def can_accommodate(self, length_mm: int, kerf_loss_mm: int = 3) -> bool:
        """Check if beam can accommodate a cut of given length."""
        required_space = length_mm + kerf_loss_mm
        return self.remaining_length_mm >= required_space

    def add_cut(self, element_id: str, length_mm: int, kerf_loss_mm: int = 3) -> bool:
        """Add a cut to this beam if possible."""
        if not self.can_accommodate(length_mm, kerf_loss_mm):
            return False

        # Calculate position for new cut
        position_mm = self.original_length_mm - self.remaining_length_mm

        # Create the cut
        cut = MaterialCut(
            element_id=element_id,
            length_mm=length_mm,
            position_mm=position_mm,
            kerf_loss_mm=kerf_loss_mm,
        )

        # Update beam state
        self.cuts.append(cut)
        self.remaining_length_mm -= length_mm + kerf_loss_mm
        self.utilization_percent = (
            (self.original_length_mm - self.remaining_length_mm) / self.original_length_mm
        ) * 100

        # Update waste (remaining unusable material)
        if self.remaining_length_mm < 50:  # Unusable if less than 50mm
            self.waste_mm = self.remaining_length_mm

        return True


class MaterialInventoryManager:
    """Manages material inventory operations with persistent JSON storage."""

    def __init__(self, inventory_path: Optional[str] = None):
        """Initialize material inventory manager."""
        if inventory_path is None:
            # Default path relative to this file
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            inventory_path = project_root / "data" / "material_inventory.json"

        self.inventory_path = Path(inventory_path)
        self.inventory_data = self._load_inventory()
        logger.info(f"Material inventory loaded from {self.inventory_path}")

    def _load_inventory(self) -> Dict[str, Any]:
        """Load inventory from JSON file."""
        try:
            if self.inventory_path.exists():
                with open(self.inventory_path, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded existing inventory with {len(data['available_beams'])} beams")
                return data
            else:
                logger.warning(f"Inventory file not found: {self.inventory_path}")
                return self._create_default_inventory()
        except Exception as e:
            logger.error(f"Failed to load inventory: {e}")
            return self._create_default_inventory()

    def _create_default_inventory(self) -> Dict[str, Any]:
        """Create default inventory structure."""
        logger.info("Creating default material inventory")
        return {
            "total_stock_mm": 13000,
            "beam_length_mm": 1980,
            "kerf_loss_mm": 3,
            "available_beams": [],
            "used_elements": [],
            "total_waste_mm": 0,
            "total_utilization_percent": 0.0,
            "cutting_sessions": [],
            "last_updated": datetime.now().isoformat(),
            "metadata": {
                "cross_section": "5x5cm",
                "material_type": "timber",
                "project": "bridge_design",
                "version": "1.0",
                "units": "millimeters",
            },
        }

    def _save_inventory(self, backup: bool = True) -> bool:
        """Save inventory to JSON file with optional backup."""
        try:
            # Create backup if requested
            if backup and self.inventory_path.exists():
                backup_path = self.inventory_path.with_suffix(".json.backup")
                shutil.copy2(self.inventory_path, backup_path)
                logger.debug(f"Created backup at {backup_path}")

            # Ensure directory exists
            self.inventory_path.parent.mkdir(parents=True, exist_ok=True)

            # Update timestamp
            self.inventory_data["last_updated"] = datetime.now().isoformat()

            # Save to file
            with open(self.inventory_path, "w") as f:
                json.dump(self.inventory_data, f, indent=2)

            logger.info(f"Inventory saved to {self.inventory_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save inventory: {e}")
            return False

    def get_beams(self) -> List[BeamUtilization]:
        """Get list of beam utilization objects."""
        beams = []
        for beam_data in self.inventory_data["available_beams"]:
            # Convert cuts data to MaterialCut objects
            cuts = [
                MaterialCut(
                    element_id=cut_data["element_id"],
                    length_mm=cut_data["length_mm"],
                    position_mm=cut_data["position_mm"],
                    kerf_loss_mm=cut_data.get("kerf_loss_mm", 3),
                    timestamp=cut_data.get("timestamp", ""),
                )
                for cut_data in beam_data.get("cuts", [])
            ]

            beam = BeamUtilization(
                beam_id=beam_data["id"],
                original_length_mm=beam_data["original_length_mm"],
                remaining_length_mm=beam_data["remaining_length_mm"],
                cuts=cuts,
                waste_mm=beam_data.get("waste_mm", 0),
                utilization_percent=beam_data.get("utilization_percent", 0.0),
            )
            beams.append(beam)

        return beams

    def update_beams(self, beams: List[BeamUtilization]) -> bool:
        """Update inventory with modified beam utilization data."""
        try:
            # Convert beam objects back to JSON format
            beam_data = []
            total_waste = 0
            total_utilization = 0

            for beam in beams:
                # Convert cuts to dict format
                cuts_data = [
                    {
                        "element_id": cut.element_id,
                        "length_mm": cut.length_mm,
                        "position_mm": cut.position_mm,
                        "kerf_loss_mm": cut.kerf_loss_mm,
                        "timestamp": cut.timestamp,
                    }
                    for cut in beam.cuts
                ]

                beam_dict = {
                    "id": beam.beam_id,
                    "original_length_mm": beam.original_length_mm,
                    "remaining_length_mm": beam.remaining_length_mm,
                    "cuts": cuts_data,
                    "waste_mm": beam.waste_mm,
                    "utilization_percent": beam.utilization_percent,
                }

                beam_data.append(beam_dict)
                total_waste += beam.waste_mm
                total_utilization += beam.utilization_percent

            # Update inventory data
            self.inventory_data["available_beams"] = beam_data
            self.inventory_data["total_waste_mm"] = total_waste
            self.inventory_data["total_utilization_percent"] = (
                total_utilization / len(beams) if beams else 0
            )

            # Save to file
            return self._save_inventory()

        except Exception as e:
            logger.error(f"Failed to update beams: {e}")
            return False

    def get_status(self, detailed: bool = False) -> Dict[str, Any]:
        """Get current inventory status."""
        beams = self.get_beams()

        total_original = sum(beam.original_length_mm for beam in beams)
        total_remaining = sum(beam.remaining_length_mm for beam in beams)
        total_used = total_original - total_remaining
        total_waste = sum(beam.waste_mm for beam in beams)

        status = {
            "total_beams": len(beams),
            "total_original_mm": total_original,
            "total_remaining_mm": total_remaining,
            "total_used_mm": total_used,
            "total_waste_mm": total_waste,
            "overall_utilization_percent": (
                (total_used / total_original * 100) if total_original > 0 else 0
            ),
            "waste_percentage": (total_waste / total_original * 100) if total_original > 0 else 0,
            "beams_available": len([beam for beam in beams if beam.remaining_length_mm > 50]),
        }

        if detailed:
            status["beam_details"] = [
                {
                    "id": beam.beam_id,
                    "remaining_mm": beam.remaining_length_mm,
                    "utilization_percent": beam.utilization_percent,
                    "cuts_count": len(beam.cuts),
                    "waste_mm": beam.waste_mm,
                }
                for beam in beams
            ]

        return status

    def _create_backup(self, backup_name: str) -> str:
        """Create named backup of current inventory state."""
        try:
            # Create backups directory if it doesn't exist
            backups_dir = self.inventory_path.parent / "backups"
            backups_dir.mkdir(exist_ok=True)

            # Create backup file path
            backup_path = backups_dir / f"{backup_name}.json"

            # Copy current inventory to backup
            backup_data = self.inventory_data.copy()
            backup_data["backup_metadata"] = {
                "name": backup_name,
                "original_file": str(self.inventory_path),
                "created_at": datetime.now().isoformat(),
                "source_version": backup_data.get("metadata", {}).get("version", "unknown"),
            }

            with open(backup_path, "w") as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"✅ Backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"❌ Failed to create backup '{backup_name}': {e}")
            raise

    def _restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore inventory from named backup."""
        try:
            # Find backup file
            backups_dir = self.inventory_path.parent / "backups"
            backup_path = backups_dir / f"{backup_name}.json"

            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # Load backup data
            with open(backup_path, "r") as f:
                backup_data = json.load(f)

            # Remove backup metadata for restoration
            backup_data.pop("backup_metadata", None)

            # Update last_updated timestamp
            backup_data["last_updated"] = datetime.now().isoformat()

            # Restore to current inventory
            self.inventory_data = backup_data
            self._save_inventory(backup=False)  # Don't create backup of the restore

            logger.info(f"✅ Inventory restored from backup: {backup_name}")
            return backup_data

        except Exception as e:
            logger.error(f"❌ Failed to restore backup '{backup_name}': {e}")
            raise

    def _list_backups(self) -> List[Dict[str, Any]]:
        """List available backup files with metadata."""
        try:
            backups_dir = self.inventory_path.parent / "backups"

            if not backups_dir.exists():
                return []

            backups = []
            for backup_file in backups_dir.glob("*.json"):
                try:
                    with open(backup_file, "r") as f:
                        backup_data = json.load(f)

                    metadata = backup_data.get("backup_metadata", {})
                    backups.append(
                        {
                            "name": backup_file.stem,
                            "file_path": str(backup_file),
                            "created_at": metadata.get("created_at", "unknown"),
                            "source_version": metadata.get("source_version", "unknown"),
                            "file_size_bytes": backup_file.stat().st_size,
                        }
                    )

                except Exception as e:
                    logger.warning(f"⚠️ Could not read backup metadata from {backup_file}: {e}")

            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)

            logger.info(f"📋 Found {len(backups)} backup files")
            return backups

        except Exception as e:
            logger.error(f"❌ Failed to list backups: {e}")
            return []

    def _delete_backup(self, backup_name: str) -> bool:
        """Delete a named backup file."""
        try:
            backups_dir = self.inventory_path.parent / "backups"
            backup_path = backups_dir / f"{backup_name}.json"

            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"🗑️ Deleted backup: {backup_name}")
                return True
            else:
                logger.warning(f"⚠️ Backup not found: {backup_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to delete backup '{backup_name}': {e}")
            return False


class CuttingOptimizer:
    """Implements cutting sequence optimization algorithms."""

    def __init__(self, kerf_loss_mm: int = 3):
        """Initialize cutting optimizer."""
        self.kerf_loss_mm = kerf_loss_mm
        logger.info(f"Cutting optimizer initialized with {kerf_loss_mm}mm kerf loss")

    def first_fit_decreasing(
        self, required_lengths: List[int], beams: List[BeamUtilization]
    ) -> Dict[str, Any]:
        """
        Implement First Fit Decreasing algorithm for optimal cutting sequence.

        Args:
            required_lengths: List of required element lengths in mm
            beams: List of available beams

        Returns:
            Dict with cutting plan, assignments, and waste analysis
        """
        logger.info(f"Planning cuts for {len(required_lengths)} elements using FFD algorithm")

        # Sort required lengths in decreasing order
        sorted_lengths = sorted(required_lengths, reverse=True)

        # Create working copies of beams
        working_beams = [
            BeamUtilization(
                beam_id=beam.beam_id,
                original_length_mm=beam.original_length_mm,
                remaining_length_mm=beam.remaining_length_mm,
                cuts=beam.cuts.copy(),
                waste_mm=beam.waste_mm,
                utilization_percent=beam.utilization_percent,
            )
            for beam in beams
        ]

        cutting_plan = []
        unassigned = []

        # Try to assign each element to the first beam that can accommodate it
        for i, length in enumerate(sorted_lengths):
            assigned = False
            element_id = f"element_{i+1:03d}"

            for beam in working_beams:
                if beam.can_accommodate(length, self.kerf_loss_mm):
                    if beam.add_cut(element_id, length, self.kerf_loss_mm):
                        cutting_plan.append(
                            {
                                "element_id": element_id,
                                "length_mm": length,
                                "beam_id": beam.beam_id,
                                "position_mm": beam.cuts[-1].position_mm,
                                "kerf_loss_mm": self.kerf_loss_mm,
                            }
                        )
                        assigned = True
                        break

            if not assigned:
                unassigned.append(
                    {
                        "element_id": element_id,
                        "length_mm": length,
                        "reason": "No beam available with sufficient remaining length",
                    }
                )

        # Calculate waste and efficiency
        total_waste = sum(beam.waste_mm for beam in working_beams)
        total_original = sum(beam.original_length_mm for beam in working_beams)
        total_used = sum(cut["length_mm"] + cut["kerf_loss_mm"] for cut in cutting_plan)

        efficiency = ((total_used / total_original) * 100) if total_original > 0 else 0

        return {
            "cutting_plan": cutting_plan,
            "beam_assignments": [
                {
                    "beam_id": beam.beam_id,
                    "original_length_mm": beam.original_length_mm,
                    "remaining_length_mm": beam.remaining_length_mm,
                    "cuts": [asdict(cut) for cut in beam.cuts],
                    "utilization_percent": beam.utilization_percent,
                    "waste_mm": beam.waste_mm,
                }
                for beam in working_beams
            ],
            "unassigned_elements": unassigned,
            "summary": {
                "total_elements": len(required_lengths),
                "assigned_elements": len(cutting_plan),
                "unassigned_elements": len(unassigned),
                "total_waste_mm": total_waste,
                "material_efficiency_percent": efficiency,
                "feasible": len(unassigned) == 0,
            },
        }

    def validate_feasibility(
        self, required_lengths: List[int], beams: List[BeamUtilization]
    ) -> Dict[str, Any]:
        """
        Validate if required cuts are feasible with available material.

        Args:
            required_lengths: List of required element lengths in mm
            beams: List of available beams

        Returns:
            Dict with feasibility analysis and suggestions
        """
        logger.info(f"Validating feasibility for {len(required_lengths)} elements")

        total_required = sum(required_lengths) + (len(required_lengths) * self.kerf_loss_mm)
        total_available = sum(beam.remaining_length_mm for beam in beams)

        # Basic capacity check
        if total_required > total_available:
            return {
                "feasible": False,
                "reason": "Insufficient total material",
                "required_mm": total_required,
                "available_mm": total_available,
                "shortage_mm": total_required - total_available,
                "suggestions": [
                    f"Need additional {total_required - total_available}mm of material",
                    "Consider reducing element lengths",
                    "Optimize design to use fewer elements",
                ],
            }

        # Check if largest element can fit in any beam
        max_length = max(required_lengths) if required_lengths else 0
        max_beam_space = max(beam.remaining_length_mm for beam in beams) if beams else 0

        if max_length + self.kerf_loss_mm > max_beam_space:
            return {
                "feasible": False,
                "reason": "Largest element exceeds maximum beam capacity",
                "largest_element_mm": max_length,
                "max_beam_space_mm": max_beam_space,
                "suggestions": [
                    f"Reduce largest element from {max_length}mm to {max_beam_space - self.kerf_loss_mm}mm",
                    "Split large elements into smaller segments",
                    "Use beam joining techniques for large elements",
                ],
            }

        # Run cutting optimization to check detailed feasibility
        cutting_result = self.first_fit_decreasing(required_lengths, beams)

        return {
            "feasible": cutting_result["summary"]["feasible"],
            "required_mm": total_required,
            "available_mm": total_available,
            "efficiency_percent": cutting_result["summary"]["material_efficiency_percent"],
            "waste_mm": cutting_result["summary"]["total_waste_mm"],
            "unassigned_count": cutting_result["summary"]["unassigned_elements"],
            "suggestions": self._generate_optimization_suggestions(cutting_result),
        }

    def _generate_optimization_suggestions(self, cutting_result: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on cutting results."""
        suggestions = []

        efficiency = cutting_result["summary"]["material_efficiency_percent"]
        waste_mm = cutting_result["summary"]["total_waste_mm"]
        unassigned = cutting_result["summary"]["unassigned_elements"]

        if efficiency < 80:
            suggestions.append(
                f"Material efficiency is low ({efficiency:.1f}%) - consider design optimization"
            )

        if waste_mm > 500:
            suggestions.append(f"High waste detected ({waste_mm}mm) - optimize element lengths")

        if unassigned > 0:
            suggestions.append(f"{unassigned} elements cannot be assigned - insufficient material")

        if efficiency > 95:
            suggestions.append("Excellent material utilization!")

        return suggestions if suggestions else ["Cutting plan is optimal"]


def create_session_record(
    session_id: str, elements: List[Dict[str, Any]], cutting_plan: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a cutting session record for tracking."""
    return {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "elements": elements,
        "cutting_plan": cutting_plan,
        "summary": {
            "total_elements": len(elements),
            "total_length_mm": sum(elem.get("length", 0) for elem in elements),
            "waste_mm": cutting_plan.get("summary", {}).get("total_waste_mm", 0),
            "efficiency_percent": cutting_plan.get("summary", {}).get(
                "material_efficiency_percent", 0
            ),
        },
    }


def extract_element_lengths(elements: List[Any]) -> List[int]:
    """
    Extract lengths from various element formats.

    Args:
        elements: List of elements (AssemblyElement objects, dicts, etc.)

    Returns:
        List of lengths in millimeters
    """
    lengths = []

    for element in elements:
        try:
            # Handle different element formats
            if hasattr(element, "length"):
                # AssemblyElement object or similar
                length = element.length
            elif isinstance(element, dict):
                # Dictionary format
                length = element.get("length", element.get("length_mm", 0))
            elif isinstance(element, (int, float)):
                # Direct length value
                length = element
            else:
                logger.warning(f"Unknown element format: {type(element)}")
                continue

            # Convert to mm if needed (assume cm if < 100)
            if isinstance(length, (int, float)) and length > 0:
                if length < 100:  # Assume centimeters, convert to mm
                    length = int(length * 10)
                else:  # Already in mm
                    length = int(length)

                lengths.append(length)

        except Exception as e:
            logger.warning(f"Failed to extract length from element: {e}")
            continue

    logger.info(f"Extracted {len(lengths)} element lengths: {lengths}")
    return lengths
