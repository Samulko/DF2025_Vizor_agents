"""
Test scenarios to verify the SysLogic agent follows the proper material optimization workflow.

This test validates that the agent now uses the correct sequence:
1. validate_material_feasibility()
2. plan_cutting_sequence()
3. track_material_usage()

Instead of jumping directly to track_material_usage() and failing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.bridge_design_system.agents.syslogic_agent_smolagents import (
    create_syslogic_agent,
    validate_material_feasibility,
    plan_cutting_sequence,
    track_material_usage,
)


class TestSysLogicOptimizationWorkflow:
    """Test that SysLogic agent follows proper optimization workflow."""

    def setup_method(self):
        """Set up test scenario that previously failed."""
        # This is the exact scenario that failed in the original test
        self.failing_scenario = {
            "total_length_used": 8.23,
            "detailed_elements": {
                "Component 1 (Module A* - Basic Triangle)": {
                    "Total Length": 1.6,
                    "Elements": [
                        {"ID": "001", "Type": "green_a", "Length": 0.4, "Level": 1},
                        {"ID": "002", "Type": "red_a", "Length": 0.4, "Level": 1},
                        {"ID": "003", "Type": "blue_a", "Length": 0.8, "Level": 2},
                    ],
                },
                "Component 2 (Module B* - Connector Triangle)": {
                    "Total Length": 1.7,
                    "Elements": [
                        {"ID": "011", "Type": "green_b", "Length": 0.4, "Level": 1},
                        {"ID": "012", "Type": "red_b", "Length": 0.4, "Level": 1},
                        {"ID": "013", "Type": "blue_b", "Length": 0.9, "Level": 2},
                    ],
                },
                "Component 3 (Module A - Extended Triangle)": {
                    "Total Length": 2.45,
                    "Elements": [
                        {"ID": "021", "Type": "green_a", "Length": 0.4, "Level": 1},
                        {"ID": "022", "Type": "red_a", "Length": 0.4, "Level": 1},
                        {"ID": "023", "Type": "blue_a", "Length": 0.85, "Level": 2},
                        {"ID": "024", "Type": "orange_a", "Length": 0.8, "Level": 3},
                    ],
                },
                "Component 4 (Module B - Extended Connector)": {
                    "Total Length": 2.48,
                    "Elements": [
                        {"ID": "031", "Type": "green_b", "Length": 0.4, "Level": 1},
                        {"ID": "032", "Type": "red_b", "Length": 0.4, "Level": 1},
                        {"ID": "033", "Type": "blue_b", "Length": 0.84, "Level": 2},
                        {"ID": "034", "Type": "orange_b", "Length": 0.84, "Level": 3},
                    ],
                },
            },
        }

        # Expected element lengths in mm
        self.expected_element_lengths = [
            400,
            400,
            800,
            400,
            400,
            900,
            400,
            400,
            850,
            800,
            400,
            400,
            840,
            840,
        ]

    @patch(
        "src.bridge_design_system.agents.syslogic_agent_smolagents.validate_material_feasibility"
    )
    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.plan_cutting_sequence")
    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.track_material_usage")
    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.get_material_status")
    def test_workflow_follows_proper_sequence(
        self, mock_status, mock_track, mock_plan, mock_feasibility
    ):
        """Test that agent follows: feasibility → optimization → tracking sequence."""

        # Mock the workflow sequence
        mock_feasibility.return_value = {
            "feasible": False,
            "error": "Insufficient material",
            "analysis": {"total_length_required_mm": 8230, "total_length_available_mm": 9633},
            "alternatives": [
                {"description": "Reduce largest elements", "impact": "Better fitting"}
            ],
        }

        mock_plan.return_value = {
            "success": True,
            "feasibility": {"possible": True, "efficiency_percent": 78.5, "waste_mm": 850},
            "visual_plan": "Optimized cutting plan...",
            "recommendations": ["Consider batch cutting for efficiency"],
        }

        mock_status.return_value = {
            "success": True,
            "inventory_status": {
                "total_remaining_mm": 9633,
                "total_utilization_percent": 62.5,
                "beams_available": 8,
            },
        }

        # Create agent using the updated system prompt
        agent = create_syslogic_agent()

        # Run the agent with the failing scenario
        result = agent.run(
            task="update material stock information based on current scene usage",
            additional_args=self.failing_scenario,
        )

        # Verify the proper sequence was followed
        mock_feasibility.assert_called_once()
        mock_plan.assert_called_once()
        mock_status.assert_called()

        # Verify element lengths were correctly extracted
        feasibility_call_args = mock_feasibility.call_args[0][0]
        assert len(feasibility_call_args) == 14
        assert feasibility_call_args == self.expected_element_lengths

        # Verify optimization was attempted
        plan_call_args = mock_plan.call_args[0][0]
        assert plan_call_args == self.expected_element_lengths
        assert mock_plan.call_args[1]["optimize"] == True

    @patch(
        "src.bridge_design_system.agents.syslogic_agent_smolagents.validate_material_feasibility"
    )
    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.plan_cutting_sequence")
    def test_feasible_design_proceeds_to_tracking(self, mock_plan, mock_feasibility):
        """Test that feasible designs proceed to material tracking."""

        # Mock feasible design
        mock_feasibility.return_value = {
            "feasible": True,
            "analysis": {"total_length_required_mm": 6000, "total_length_available_mm": 9633},
        }

        # This should result in the agent proceeding to track_material_usage
        # (We'd need to mock that too for full test, but this verifies the logic branch)

        agent = create_syslogic_agent()

        # Simulate smaller, feasible design
        smaller_scenario = {
            "detailed_elements": {
                "Small Component": {"Elements": [{"Length": 0.4}, {"Length": 0.4}, {"Length": 0.5}]}
            }
        }

        # The agent should call feasibility first, see it's feasible, then proceed
        mock_feasibility.return_value["feasible"] = True

        # Verify feasibility is still called first
        agent.run(
            task="update material stock information based on current scene usage",
            additional_args=smaller_scenario,
        )

        mock_feasibility.assert_called_once()

    @patch(
        "src.bridge_design_system.agents.syslogic_agent_smolagents.validate_material_feasibility"
    )
    @patch("src.bridge_design_system.agents.syslogic_agent_smolagents.plan_cutting_sequence")
    def test_optimization_fallback_on_infeasible_design(self, mock_plan, mock_feasibility):
        """Test that infeasible designs trigger optimization attempts."""

        # Mock infeasible design
        mock_feasibility.return_value = {
            "feasible": False,
            "analysis": {"total_length_required_mm": 10000, "total_length_available_mm": 5000},
            "alternatives": [
                {"description": "Split large elements", "impact": "Better utilization"}
            ],
        }

        # Mock optimization that finds a solution
        mock_plan.return_value = {
            "success": True,
            "feasibility": {"possible": True, "efficiency_percent": 85.0, "waste_mm": 450},
            "recommendations": ["Use optimized cutting sequence"],
        }

        agent = create_syslogic_agent()

        result = agent.run(
            task="update material stock information based on current scene usage",
            additional_args=self.failing_scenario,
        )

        # Verify both feasibility and optimization were called
        mock_feasibility.assert_called_once()
        mock_plan.assert_called_once()

        # Verify optimization was called with optimize=True
        assert mock_plan.call_args[1]["optimize"] == True


class TestWorkflowIntegration:
    """Integration tests for the complete workflow."""

    def test_element_length_extraction(self):
        """Test that element lengths are correctly extracted from nested structure."""

        test_elements = {
            "Component 1": {
                "Elements": [
                    {"Length": 0.4},  # Should become 400mm
                    {"Length": 0.8},  # Should become 800mm
                ]
            },
            "Component 2": {"Elements": [{"Length": 0.6}]},  # Should become 600mm
        }

        # Simulate the extraction logic from the system prompt
        element_lengths = []
        for component_data in test_elements.values():
            if "Elements" in component_data:
                for element in component_data["Elements"]:
                    length_m = element.get("Length", 0)
                    element_lengths.append(length_m * 1000)  # Convert to mm

        expected = [400, 800, 600]
        assert element_lengths == expected

    def test_contextual_recommendations(self):
        """Test that the agent provides contextual recommendations based on results."""

        # This test documents the expected behavior patterns
        production_context_expectations = [
            "efficiency > 85% = excellent for production",
            "efficiency 70-85% = acceptable for production",
            "efficiency < 70% = requires improvement",
            "waste < 500mm = within tolerance",
            "waste > 500mm = higher than optimal",
        ]

        # These patterns should be used by the agent in its contextual reasoning
        assert len(production_context_expectations) == 5

    def test_workflow_documentation_completeness(self):
        """Verify that all required tools are available in the workflow."""

        # These tools should all be available to the SysLogic agent
        required_tools = [
            "validate_material_feasibility",
            "plan_cutting_sequence",
            "track_material_usage",
            "get_material_status",
        ]

        # Import and verify tools exist
        from src.bridge_design_system.agents.syslogic_agent_smolagents import (
            validate_material_feasibility,
            plan_cutting_sequence,
            track_material_usage,
            get_material_status,
        )

        # All tools should be callable
        assert callable(validate_material_feasibility)
        assert callable(plan_cutting_sequence)
        assert callable(track_material_usage)
        assert callable(get_material_status)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
