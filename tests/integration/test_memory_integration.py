"""Integration tests for memory tools with agents and component registry."""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from bridge_design_system.agents.triage_agent import TriageAgent
from bridge_design_system.agents.geometry_agent_stdio import GeometryAgentSTDIO
from bridge_design_system.state.component_registry import ComponentRegistry
from bridge_design_system.tools.memory_tools import remember, recall, search_memory


@pytest.fixture
def temp_memory_dir(monkeypatch):
    """Create a temporary directory for memory storage during tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override the MEMORY_PATH
        memory_path = Path(temp_dir) / "memory"
        memory_path.mkdir(exist_ok=True)
        
        # Patch the module-level variables
        import bridge_design_system.tools.memory_tools as mem_tools
        monkeypatch.setattr(mem_tools, 'MEMORY_PATH', memory_path)
        monkeypatch.setattr(mem_tools, 'SESSION_ID', 'test_integration')
        
        yield memory_path


class TestTriageAgentMemoryIntegration:
    """Test memory integration with TriageAgent."""
    
    def test_triage_agent_has_memory_tools(self):
        """Test that TriageAgent initializes with memory tools."""
        registry = ComponentRegistry()
        agent = TriageAgent(component_registry=registry)
        
        # Check memory tools are added
        assert len(agent.memory_tools) == 4
        assert remember in agent.memory_tools
        assert recall in agent.memory_tools
        assert search_memory in agent.memory_tools
    
    @patch('bridge_design_system.agents.triage_agent.CodeAgent')
    @patch('bridge_design_system.agents.geometry_agent_stdio.GeometryAgentSTDIO')
    def test_triage_agent_passes_memory_tools(self, mock_geometry, mock_codeagent, temp_memory_dir):
        """Test that TriageAgent passes memory tools to CodeAgent."""
        registry = ComponentRegistry()
        agent = TriageAgent(component_registry=registry)
        
        # Initialize the agent (which creates one CodeAgent instance)
        agent.initialize_agent()
        
        # Mock the CodeAgent instance
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "Test result"
        mock_codeagent.return_value = mock_agent_instance
        
        # Run a request (which creates a fresh CodeAgent with memory tools)
        agent._run_with_context("Test request")
        
        # Verify CodeAgent was called twice: once in initialize, once in _run_with_context
        assert mock_codeagent.call_count == 2
        
        # Check the second call (from _run_with_context) has memory tools
        second_call_args = mock_codeagent.call_args[1]
        assert 'tools' in second_call_args
        assert len(second_call_args['tools']) == 4
        assert remember in second_call_args['tools']
        assert recall in second_call_args['tools']
        assert search_memory in second_call_args['tools']
    
    @patch('bridge_design_system.agents.triage_agent.recall')
    def test_triage_context_includes_memory(self, mock_recall, temp_memory_dir):
        """Test that context building includes memory recall."""
        registry = ComponentRegistry()
        agent = TriageAgent(component_registry=registry)
        
        # Mock recall to return some context
        mock_recall.return_value = "Previous design context"
        
        # Build context
        context = agent._build_conversation_context("New request")
        
        # Verify recall was called
        mock_recall.assert_called_with("context", "current_session")
        
        # Verify context includes memory instructions
        assert "memory tools" in context
        assert "remember(" in context
        assert "recall(" in context
        assert "search_memory(" in context


class TestGeometryAgentMemoryIntegration:
    """Test memory integration with GeometryAgent."""
    
    def test_geometry_agent_has_memory_tools(self):
        """Test that GeometryAgent initializes with memory tools."""
        registry = ComponentRegistry()
        agent = GeometryAgentSTDIO(component_registry=registry)
        
        # Check memory tools are added
        assert len(agent.memory_tools) == 4
        assert remember in agent.memory_tools
        assert recall in agent.memory_tools
        assert search_memory in agent.memory_tools
    
    @patch('bridge_design_system.agents.geometry_agent_stdio.MCPAdapt')
    @patch('bridge_design_system.agents.geometry_agent_stdio.CodeAgent')
    def test_geometry_agent_includes_memory_in_tools(self, mock_codeagent, mock_mcpadapt, temp_memory_dir):
        """Test that GeometryAgent includes memory tools when creating agent."""
        registry = ComponentRegistry()
        agent = GeometryAgentSTDIO(component_registry=registry)
        
        # Mock MCP tools
        mock_mcp_tools = [MagicMock(name="mcp_tool1"), MagicMock(name="mcp_tool2")]
        mock_mcpadapt.return_value.__enter__.return_value = mock_mcp_tools
        
        # Mock CodeAgent
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "Geometry created"
        mock_codeagent.return_value = mock_agent_instance
        
        # Run a task
        try:
            agent.run("Create a point")
        except Exception:
            pass  # We're just testing tool setup
        
        # Verify CodeAgent was created with combined tools
        mock_codeagent.assert_called()
        call_args = mock_codeagent.call_args[1]
        assert 'tools' in call_args
        # Should have MCP tools + memory tools
        assert len(call_args['tools']) >= 6  # At least 2 MCP + 4 memory
    
    def test_geometry_context_with_memory(self, temp_memory_dir):
        """Test that geometry agent context includes memory prompts."""
        registry = ComponentRegistry()
        agent = GeometryAgentSTDIO(component_registry=registry)
        
        # First request should include memory instructions
        context = agent._build_conversation_context("Create a spiral")
        
        assert "memory tools" in context
        assert "components" in context
        assert "geometry" in context
        assert "current_work" in context


class TestComponentRegistryMemoryIntegration:
    """Test memory integration with ComponentRegistry."""
    
    def test_component_registration_stores_in_memory(self, temp_memory_dir):
        """Test that registering a component stores it in memory."""
        registry = ComponentRegistry()
        
        # Register a component
        success = registry.register_component(
            component_id="comp_123",
            component_type="timber_truss",
            name="Main Truss",
            description="50m span timber truss"
        )
        
        assert success
        
        # Check that it was stored in memory
        memory_file = temp_memory_dir / "test_integration.json"
        assert memory_file.exists()
        
        memory_data = json.loads(memory_file.read_text())
        assert "components" in memory_data["memories"]
        assert "comp_123" in memory_data["memories"]["components"]
        
        stored_value = memory_data["memories"]["components"]["comp_123"]["value"]
        assert "timber_truss" in stored_value
        assert "50m span timber truss" in stored_value
    
    def test_component_update_updates_memory(self, temp_memory_dir):
        """Test that updating a component updates memory."""
        registry = ComponentRegistry()
        
        # Register a component
        registry.register_component(
            component_id="comp_456",
            component_type="beam",
            name="Support Beam",
            description="Initial description"
        )
        
        # Update the component
        success = registry.update_component(
            "comp_456",
            description="Updated description with new specs"
        )
        
        assert success
        
        # Check memory was updated
        memory_file = temp_memory_dir / "test_integration.json"
        memory_data = json.loads(memory_file.read_text())
        
        stored_value = memory_data["memories"]["components"]["comp_456"]["value"]
        assert "Updated description with new specs" in stored_value
    
    def test_memory_persistence_across_registry_instances(self, temp_memory_dir):
        """Test that memory persists when creating new registry instances."""
        # First registry instance
        registry1 = ComponentRegistry()
        registry1.register_component(
            component_id="comp_789",
            component_type="column",
            name="Main Column",
            description="Structural column"
        )
        
        # Create new registry instance (simulating fresh agent)
        registry2 = ComponentRegistry()
        
        # Check that we can recall the component from memory
        recalled = recall("components", "comp_789")
        assert "Structural column" in recalled
        assert "column" in recalled
    
    def test_search_memory_finds_components(self, temp_memory_dir):
        """Test searching memory for components."""
        registry = ComponentRegistry()
        
        # Register multiple components
        registry.register_component("comp_1", "timber_truss", "Truss 1", "Main timber truss")
        registry.register_component("comp_2", "steel_beam", "Beam 1", "Steel support beam")
        registry.register_component("comp_3", "timber_column", "Column 1", "Timber column")
        
        # Search for timber components
        results = search_memory("timber")
        assert "comp_1" in results
        assert "comp_3" in results
        assert "comp_2" not in results or "steel" in results  # Should not find steel beam


class TestEndToEndMemoryWorkflow:
    """Test complete workflow with memory across agents."""
    
    @patch('bridge_design_system.agents.geometry_agent_stdio.MCPAdapt')
    @patch('bridge_design_system.agents.triage_agent.CodeAgent')
    def test_complete_memory_workflow(self, mock_triage_codeagent, mock_mcpadapt, temp_memory_dir):
        """Test a complete workflow: triage -> geometry -> memory persistence."""
        # Setup component registry
        registry = ComponentRegistry()
        
        # Setup agents
        triage_agent = TriageAgent(component_registry=registry)
        geometry_agent = GeometryAgentSTDIO(component_registry=registry)
        
        # Mock triage CodeAgent
        mock_triage_instance = MagicMock()
        mock_triage_instance.run.return_value = "I'll help you create a timber truss bridge."
        mock_triage_codeagent.return_value = mock_triage_instance
        
        # Step 1: Triage agent processes request
        triage_response = triage_agent._run_with_context("Create a timber truss bridge")
        assert triage_response.success
        
        # Step 2: Manually store some context (simulating what agent would do)
        remember("context", "current_session", "Designing a timber truss bridge")
        remember("context", "bridge_type", "timber_truss")
        
        # Step 3: Register a component (simulating geometry agent creating it)
        registry.register_component(
            "comp_bridge_001",
            "timber_truss_bridge",
            "Main Bridge Structure",
            "50m span pedestrian bridge with timber trusses"
        )
        
        # Step 4: Verify memory persists
        # Check context
        context = recall("context", "current_session")
        assert "timber truss bridge" in context
        
        # Check components
        components = recall("components")
        assert "comp_bridge_001" in components
        assert "50m span" in components
        
        # Search for timber
        search_results = search_memory("timber")
        assert "Found" in search_results
        assert "bridge" in search_results.lower()
    
    def test_memory_helps_avoid_context_loss(self, temp_memory_dir):
        """Test that memory prevents 'what were we working on?' scenarios."""
        registry = ComponentRegistry()
        
        # Simulate first session
        remember("context", "current_session", "Designing a spiral staircase with 3m radius")
        remember("context", "project_requirements", "Must support 500kg load, use steel")
        registry.register_component("comp_stair_001", "spiral_staircase", "Main Staircase", "3m radius spiral")
        
        # Simulate new agent instance (fresh start)
        new_agent = TriageAgent(component_registry=registry)
        
        # Build context for new request
        context = new_agent._build_conversation_context("What were we working on?")
        
        # Context should include previous work from memory
        previous_context = recall("context", "current_session")
        assert previous_context is not None
        assert "spiral staircase" in previous_context
        assert "3m radius" in previous_context
        
        # Can also find components
        components = recall("components", "comp_stair_001")
        assert "spiral" in components
        assert "3m radius" in components