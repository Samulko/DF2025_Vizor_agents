"""
Test configuration for memory synchronization testing.

This module sets up a realistic test environment that mocks our
CodeAgent→ToolCallingAgent delegation pattern using enhanced mock MCP tools.
"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any, List, Optional
import logging

from smolagents import CodeAgent, ToolCallingAgent, tool
from smolagents.models import MockModel

from .mock_mcp_tools import (
    create_mock_mcp_tools,
    reset_mock_state,
    get_test_state_summary,
    get_components_by_type,
    get_most_recent_component_of_type,
    verify_no_components_have_errors,
    simulate_error_type,
)


class MockTriageTestConfig:
    """Test configuration that creates a realistic triage system for memory testing."""

    def __init__(self):
        self.mock_model = MockModel()
        self.mock_mcp_tools = None
        self.triage_agent = None
        self.geometry_agent = None
        self.recent_components = []  # Shared cache matching our memory fix

    def setup_test_environment(self):
        """Set up the complete test environment with mock agents."""

        # Reset mock state for clean test
        reset_mock_state()
        self.recent_components.clear()

        # Create mock MCP tools
        self.mock_mcp_tools = create_mock_mcp_tools()

        # Create mock geometry agent (ToolCallingAgent pattern)
        self.geometry_agent = ToolCallingAgent(
            tools=self.mock_mcp_tools,
            model=self.mock_model,
            max_steps=6,
            name="geometry_agent",
            description="Creates 3D geometry in Rhino Grasshopper using mock MCP tools",
        )

        # Create mock coordination tools for triage agent
        coordination_tools = self._create_mock_coordination_tools()

        # Create mock triage agent (CodeAgent pattern)
        self.triage_agent = CodeAgent(
            tools=coordination_tools,
            managed_agents=[self.geometry_agent],
            model=self.mock_model,
            max_steps=6,
            name="triage_agent",
            description="Coordinates bridge design tasks by delegating to specialized agents",
        )

        # Add mock memory tools to triage agent (matching our memory fix)
        memory_tools = self._create_mock_memory_tools()
        for memory_tool in memory_tools:
            self.triage_agent.tools[memory_tool.name] = memory_tool

        return self.triage_agent

    def _create_mock_coordination_tools(self):
        """Create mock coordination tools for the triage agent."""

        @tool
        def debug_component_tracking() -> str:
            """Debug tool to show current component tracking state."""
            summary = get_test_state_summary()
            recent_info = f"Recent components: {len(self.recent_components)}"
            return f"Component tracking state: {summary}. {recent_info}"

        return [debug_component_tracking]

    def _create_mock_memory_tools(self):
        """Create mock memory tools that simulate our memory fix."""

        @tool
        def get_most_recent_component(component_type: str = "") -> str:
            """Get the most recently created component, optionally filtered by type."""
            if component_type:
                component = get_most_recent_component_of_type(component_type)
            else:
                component = get_most_recent_component_of_type()

            if component:
                # Track this lookup in our shared cache (simulating the memory fix)
                if component not in self.recent_components:
                    self.recent_components.append(component)
                return f"Found recent component: {component['name']} (ID: {component['id'][:8]})"
            else:
                return f"No recent component found for type: {component_type}"

        @tool
        def track_geometry_result(geometry_result: str, task_description: str) -> str:
            """Track components from a geometry agent result for future reference."""
            # Extract component IDs from geometry result (simulating our regex extraction)
            import re

            component_ids = re.findall(
                r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", geometry_result
            )

            tracked_count = 0
            for comp_id in component_ids:
                # Find the component in mock state
                summary = get_test_state_summary()
                # Add to recent components cache
                mock_comp = {"id": comp_id, "task": task_description}
                if mock_comp not in self.recent_components:
                    self.recent_components.append(mock_comp)
                    tracked_count += 1

            return f"Tracked {tracked_count} components from geometry result: {task_description[:50]}..."

        return [get_most_recent_component, track_geometry_result]

    def simulate_user_request(self, user_input: str) -> str:
        """Simulate a user request to the triage agent."""
        if not self.triage_agent:
            raise RuntimeError("Test environment not set up. Call setup_test_environment() first.")

        try:
            result = self.triage_agent.run(user_input)

            # Extract and track any new components (simulating our memory fix)
            self._extract_and_track_components_from_result(result, user_input)

            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    def _extract_and_track_components_from_result(self, result: Any, task: str):
        """Extract and track components from agent result (simulating memory fix)."""
        import re

        result_str = str(result)

        # Extract component IDs using regex (matching our implementation)
        component_ids = re.findall(
            r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", result_str
        )

        for comp_id in component_ids:
            # Add to recent components cache
            self.recent_components.append(
                {"id": comp_id, "task": task, "timestamp": "mock_timestamp"}
            )

    def get_memory_state(self) -> Dict[str, Any]:
        """Get current memory state for assertions."""
        return {
            "recent_components_count": len(self.recent_components),
            "recent_components": self.recent_components[-5:],  # Last 5 for brevity
            "triage_memory_steps": len(self.triage_agent.memory.steps) if self.triage_agent else 0,
            "geometry_memory_steps": (
                len(self.geometry_agent.memory.steps) if self.geometry_agent else 0
            ),
            "mock_state_summary": get_test_state_summary(),
        }

    def assert_no_stale_component_errors(self):
        """Assert that no stale component ID errors have occurred."""
        if not verify_no_components_have_errors():
            errors = [comp for comp in get_test_state_summary()["components_with_errors"]]
            raise AssertionError(f"Found components with errors: {errors}")

    def assert_component_was_tracked(self, expected_type: str) -> bool:
        """Assert that a component of the expected type was tracked."""
        components = get_components_by_type(expected_type)
        return len(components) > 0

    def assert_memory_persistence(self) -> bool:
        """Assert that memory persists across requests."""
        return len(self.recent_components) > 0 or (
            self.triage_agent and len(self.triage_agent.memory.steps) > 0
        )

    def cleanup(self):
        """Clean up test environment."""
        reset_mock_state()
        self.recent_components.clear()


class MemoryTestCase(unittest.TestCase):
    """Base test case for memory synchronization tests."""

    def setUp(self):
        """Set up test configuration."""
        self.config = MockTriageTestConfig()
        self.triage_agent = self.config.setup_test_environment()

    def tearDown(self):
        """Clean up after test."""
        self.config.cleanup()

    def simulate_conversation_exchange(self, user_inputs: List[str]) -> List[str]:
        """Simulate multiple conversation exchanges."""
        responses = []
        for user_input in user_inputs:
            response = self.config.simulate_user_request(user_input)
            responses.append(response)
        return responses

    def assert_vague_reference_resolved(self, user_input: str, expected_component_type: str):
        """Assert that a vague reference like 'modify the curve' was resolved correctly."""
        response = self.config.simulate_user_request(user_input)

        # Check that the expected component type exists
        self.assertTrue(
            self.config.assert_component_was_tracked(expected_component_type),
            f"Expected component type {expected_component_type} was not found",
        )

        # Check that no errors occurred
        self.config.assert_no_stale_component_errors()

        return response
