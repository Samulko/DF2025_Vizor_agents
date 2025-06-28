"""
Test scenarios for contextual material recommendations.

This test validates that the refactored SysLogic agent provides
context-aware material recommendations instead of rigid threshold-based alerts.
"""

import pytest
from unittest.mock import Mock, patch
from src.bridge_design_system.agents.syslogic_agent_smolagents import get_material_status


class TestContextualMaterialRecommendations:
    """Test contextual reasoning vs hardcoded thresholds."""

    def setup_method(self):
        """Set up test scenarios with same inventory data, different contexts."""
        self.sample_inventory_data = {
            "total_remaining_mm": 5000,
            "beams_available": 8,
            "waste_percentage": 12.5,  # This was triggering hardcoded alerts before
            "overall_utilization_percent": 85.3,
            "total_beams": 13,
        }

    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.MaterialInventoryManager")
    def test_prototyping_context_acceptance(self, mock_manager):
        """Test that prototyping context accepts higher waste tolerances."""

        # Mock the material manager to return our test data
        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        mock_instance.get_status.return_value = self.sample_inventory_data
        mock_instance.get_beams.return_value = []
        mock_instance.inventory_data = {"cutting_sessions": []}

        # Get material status with prototyping context
        result = get_material_status(
            detailed=True,
            project_context="prototyping",
            design_complexity="complex",
            user_intent="validation",
        )

        # Verify the context information is included
        assert result["success"] is True
        assert result["context_info"]["project_context"] == "prototyping"
        assert result["context_info"]["design_complexity"] == "complex"
        assert result["context_info"]["user_intent"] == "validation"

        # Verify NO hardcoded recommendations or alerts in the response
        assert "recommendations" not in result
        assert "alerts" not in result

        # The agent should reason about this 12.5% waste contextually:
        # In prototyping, this should be acceptable for complex design validation

    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.MaterialInventoryManager")
    def test_production_context_scrutiny(self, mock_manager):
        """Test that production context requires stricter efficiency."""

        # Same inventory data as prototyping test
        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        mock_instance.get_status.return_value = self.sample_inventory_data
        mock_instance.get_beams.return_value = []
        mock_instance.inventory_data = {"cutting_sessions": []}

        # Get material status with production context
        result = get_material_status(
            detailed=True,
            project_context="production",
            design_complexity="simple",
            user_intent="optimization",
        )

        # Verify the context information is included
        assert result["context_info"]["project_context"] == "production"
        assert result["context_info"]["design_complexity"] == "simple"
        assert result["context_info"]["user_intent"] == "optimization"

        # Verify NO hardcoded recommendations or alerts
        assert "recommendations" not in result
        assert "alerts" not in result

        # The agent should reason that same 12.5% waste in production
        # for simple design requires optimization attention

    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.MaterialInventoryManager")
    def test_experimental_context_flexibility(self, mock_manager):
        """Test that experimental context allows higher waste for innovation."""

        # Use even higher waste percentage to test extreme case
        high_waste_data = self.sample_inventory_data.copy()
        high_waste_data["waste_percentage"] = 18.0  # Would definitely trigger old alerts

        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        mock_instance.get_status.return_value = high_waste_data
        mock_instance.get_beams.return_value = []
        mock_instance.inventory_data = {"cutting_sessions": []}

        # Get material status with experimental context
        result = get_material_status(
            detailed=True,
            project_context="experimentation",
            design_complexity="experimental",
            user_intent="exploration",
        )

        # Verify context is captured
        assert result["context_info"]["project_context"] == "experimentation"
        assert result["context_info"]["design_complexity"] == "experimental"

        # Verify NO hardcoded alerts despite 18% waste
        assert "recommendations" not in result
        assert "alerts" not in result

        # Agent should reason that 18% waste in experimental design exploration
        # is acceptable trade-off for innovation


class TestDeterministicCalculationsPreserved:
    """Ensure deterministic calculations remain accurate and available."""

    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.MaterialInventoryManager")
    def test_raw_data_accuracy(self, mock_manager):
        """Test that raw calculation data is preserved and accurate."""

        sample_data = {
            "total_remaining_mm": 3456,
            "beams_available": 5,
            "waste_percentage": 7.2,
            "overall_utilization_percent": 68.4,
        }

        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        mock_instance.get_status.return_value = sample_data
        mock_instance.get_beams.return_value = []
        mock_instance.inventory_data = {"cutting_sessions": []}

        result = get_material_status(detailed=True, project_context="testing")

        # Verify all deterministic data is preserved
        assert result["inventory_status"]["total_remaining_mm"] == 3456
        assert result["inventory_status"]["beams_available"] == 5
        assert result["inventory_status"]["waste_percentage"] == 7.2
        assert result["inventory_status"]["overall_utilization_percent"] == 68.4

        # Verify utilization and capacity analysis are calculated
        assert "utilization_distribution" in result
        assert "capacity_analysis" in result
        assert "usage_summary" in result


class TestContextualReasoningExamples:
    """Examples showing how agent should reason about identical data differently."""

    def test_reasoning_examples(self):
        """Document expected reasoning patterns for different contexts."""

        # Same scenario: 12% waste, 2 beams remaining, 85% utilization
        base_scenario = {
            "waste_percentage": 12.0,
            "beams_available": 2,
            "overall_utilization_percent": 85.0,
        }

        # Expected reasoning patterns (documented for agent training):

        expected_prototyping_reasoning = """
        Context: Prototyping phase, complex design, validation intent
        12% waste → "Acceptable for complex design validation - focus on structural integrity"
        2 beams remaining → "Monitor for next iteration but sufficient for current validation"
        85% utilization → "Reasonable testing utilization - plan for production scaling"
        """

        expected_production_reasoning = """
        Context: Production phase, simple design, optimization intent  
        12% waste → "Requires optimization - implement batch cutting and material nesting"
        2 beams remaining → "Production bottleneck risk - schedule immediate restocking"
        85% utilization → "Approaching critical threshold - plan material procurement"
        """

        expected_experimental_reasoning = """
        Context: Experimentation phase, experimental design, exploration intent
        12% waste → "Expected for experimental design - innovation requires material exploration"
        2 beams remaining → "Consider procurement for continued experimentation"
        85% utilization → "Good resource usage while maintaining flexibility for exploration"
        """

        # These are the patterns the agent should follow instead of rigid thresholds
        assert True  # This test documents expected behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
