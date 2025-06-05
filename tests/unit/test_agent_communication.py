"""Tests for agent communication and coordination."""
import pytest
from unittest.mock import Mock, patch

from bridge_design_system.agents.base_agent import AgentError, AgentResponse
from bridge_design_system.agents.dummy_agent import DummyAgent
from bridge_design_system.agents.triage_agent import TriageAgent


class TestAgentCommunication:
    """Test suite for agent communication patterns."""
    
    @pytest.fixture
    def mock_model_provider(self):
        """Mock the model provider to avoid API calls."""
        with patch('bridge_design_system.config.model_config.ModelProvider') as mock:
            mock_instance = Mock()
            mock.get_model.return_value = Mock()
            yield mock
    
    @pytest.fixture
    def dummy_agent(self, mock_model_provider):
        """Create a dummy agent for testing."""
        with patch('bridge_design_system.agents.base_agent.ModelProvider', mock_model_provider):
            agent = DummyAgent()
            agent.initialize_agent()
            return agent
    
    def test_agent_initialization(self, dummy_agent):
        """Test that agents initialize correctly."""
        assert dummy_agent.name == "dummy_agent"
        assert dummy_agent.description == "Reference agent for testing patterns and communication"
        assert len(dummy_agent.tools) == 5
        assert dummy_agent._agent is not None
    
    def test_agent_response_format(self, dummy_agent):
        """Test that agent responses follow the correct format."""
        # Mock the agent run method
        dummy_agent._agent.run = Mock(return_value="Test successful")
        
        response = dummy_agent.run("Test task")
        
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert "Test successful" in response.message
        assert response.data is not None
        assert "step_count" in response.data
    
    def test_agent_error_handling(self, dummy_agent):
        """Test agent error handling."""
        # Mock the agent run method to raise an exception
        dummy_agent._agent.run = Mock(side_effect=Exception("Test error"))
        
        response = dummy_agent.run("Error task")
        
        assert response.success is False
        assert "Test error" in response.message
        assert response.error == AgentError.TOOL_EXECUTION_FAILED
    
    def test_conversation_state_management(self, dummy_agent):
        """Test conversation state tracking."""
        dummy_agent._agent.run = Mock(return_value="Response")
        
        # Initial state
        assert dummy_agent.step_count == 0
        assert len(dummy_agent.conversation_history) == 0
        
        # After first run
        dummy_agent.run("First task")
        assert dummy_agent.step_count == 1
        assert len(dummy_agent.conversation_history) == 1
        
        # After second run
        dummy_agent.run("Second task")
        assert dummy_agent.step_count == 2
        assert len(dummy_agent.conversation_history) == 2
        
        # Reset conversation
        dummy_agent.reset_conversation()
        assert dummy_agent.step_count == 0
        assert len(dummy_agent.conversation_history) == 0
    
    def test_max_steps_limit(self, dummy_agent, monkeypatch):
        """Test that agents respect max steps limit."""
        # Set a low max steps for testing
        monkeypatch.setattr('bridge_design_system.config.settings.settings.max_agent_steps', 2)
        
        dummy_agent._agent.run = Mock(return_value="Response")
        
        # First two runs should succeed
        response1 = dummy_agent.run("Task 1")
        assert response1.success is True
        
        response2 = dummy_agent.run("Task 2")
        assert response2.success is True
        
        # Third run should fail due to max steps
        response3 = dummy_agent.run("Task 3")
        assert response3.success is False
        assert response3.error == AgentError.CONTEXT_OVERFLOW
    
    def test_tool_execution(self, dummy_agent):
        """Test tool execution through agent."""
        # Get the process_text tool
        process_text_tool = None
        for tool in dummy_agent.tools:
            if tool.name == "process_text":
                process_text_tool = tool
                break
        
        assert process_text_tool is not None
        
        # Test tool execution
        result = process_text_tool("hello", "uppercase")
        assert result == "HELLO"
        
        result = process_text_tool("WORLD", "lowercase")
        assert result == "world"
        
        result = process_text_tool("test", "reverse")
        assert result == "tset"


class TestTriageAgent:
    """Test suite for triage agent coordination."""
    
    @pytest.fixture
    def mock_agents(self):
        """Mock all managed agents."""
        with patch('bridge_design_system.agents.triage_agent.GeometryAgent'), \
             patch('bridge_design_system.agents.triage_agent.MaterialAgent'), \
             patch('bridge_design_system.agents.triage_agent.StructuralAgent'):
            yield
    
    @pytest.fixture
    def triage_agent(self, mock_agents):
        """Create a triage agent for testing."""
        with patch('bridge_design_system.config.model_config.ModelProvider.get_model'):
            agent = TriageAgent()
            # Don't initialize fully to avoid complex mocking
            agent.managed_agents = {
                "geometry": Mock(),
                "material": Mock(),
                "structural": Mock()
            }
            return agent
    
    def test_triage_initialization(self, triage_agent):
        """Test triage agent initialization."""
        assert triage_agent.name == "triage_agent"
        assert len(triage_agent.managed_agents) == 3
        assert "geometry" in triage_agent.managed_agents
        assert "material" in triage_agent.managed_agents
        assert "structural" in triage_agent.managed_agents
    
    def test_design_state_management(self, triage_agent):
        """Test design state tracking."""
        initial_state = triage_agent.design_state
        assert initial_state["current_step"] == "initial"
        assert initial_state["bridge_type"] is None
        
        # Update state
        triage_agent.update_design_state({
            "bridge_type": "vehicular",
            "start_point": {"x": 0, "y": 0, "z": 0}
        })
        
        assert triage_agent.design_state["bridge_type"] == "vehicular"
        assert triage_agent.design_state["start_point"] == {"x": 0, "y": 0, "z": 0}
        assert triage_agent.design_state["current_step"] == "initial"  # Unchanged
    
    def test_agent_status_reporting(self, triage_agent):
        """Test getting status of managed agents."""
        # Mock agent states
        for name, agent in triage_agent.managed_agents.items():
            agent._agent = Mock()
            agent.conversation_history = []
            agent.step_count = 0
        
        status = triage_agent.get_agent_status()
        
        assert len(status) == 3
        for name in ["geometry", "material", "structural"]:
            assert name in status
            assert status[name]["initialized"] is True
            assert status[name]["conversation_length"] == 0
            assert status[name]["step_count"] == 0
    
    def test_reset_all_agents(self, triage_agent):
        """Test resetting all agents."""
        # Set some state
        triage_agent.design_state["bridge_type"] = "test"
        triage_agent.step_count = 5
        
        # Mock reset methods
        for agent in triage_agent.managed_agents.values():
            agent.reset_conversation = Mock()
        
        triage_agent.reset_all_agents()
        
        # Check resets were called
        for agent in triage_agent.managed_agents.values():
            agent.reset_conversation.assert_called_once()
        
        # Check state reset
        assert triage_agent.design_state["current_step"] == "initial"
        assert triage_agent.design_state["bridge_type"] is None
        assert triage_agent.step_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])