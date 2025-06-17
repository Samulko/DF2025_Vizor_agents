"""
Conversation Logic Tests - Realistic Validation Approach

Tests agent delegation, context preservation, and multi-turn conversation logic
with deterministic mock agents. This tests conversation flow without real AI.

Based on current_task.md honest assessment.
"""

import pytest
from pathlib import Path
import sys
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from bridge_design_system.tools.memory_tools import remember, recall, search_memory, clear_memory
from bridge_design_system.state.component_registry import ComponentRegistry


@dataclass
class MockDelegatedTask:
    """Mock delegated task with context."""
    original_request: str
    context: Dict[str, Any]
    target_agent: str
    
    def has_reference_to(self, reference_type: str) -> bool:
        """Check if task has reference to specific type."""
        # Check in original request
        if reference_type.lower() in self.original_request.lower():
            return True
        # Check in context
        for key, value in self.context.items():
            if reference_type.lower() in str(value).lower():
                return True
        return False


@dataclass 
class MockAgentResponse:
    """Mock agent response with actions and memory usage."""
    original_input: str
    actions: List[str]
    memory_used: Dict[str, Any]
    component_references: List[str]
    success: bool
    
    def used_memory_correctly(self) -> bool:
        """Check if memory was used correctly in response."""
        return len(self.memory_used) > 0 and self.success


class MockTriageAgent:
    """Mock triage agent for testing delegation logic."""
    
    def __init__(self):
        self.context = {}
        self.conversation_history = []
        self.component_registry = ComponentRegistry()
    
    def add_context(self, context_type: str, value: str):
        """Add context for delegation."""
        self.context[context_type] = value
        remember("agent_context", context_type, value)
    
    def delegate_to_geometry(self, task: str) -> MockDelegatedTask:
        """Mock delegation to geometry agent with context preservation."""
        
        # Preserve current context in delegation
        delegation_context = self.context.copy()
        
        # Add conversation history to context
        delegation_context["conversation_history"] = self.conversation_history[-3:]  # Last 3 interactions
        
        # Add any component references from memory
        if "curve" in task.lower():
            curve_memory = search_memory("curve")
            if curve_memory and "No memories found" not in curve_memory:
                delegation_context["relevant_components"] = "curve_references_found"
        
        # Add task context based on recent actions
        recent_context = recall("context")
        if recent_context and "No memories found" not in recent_context:
            delegation_context["recent_context"] = recent_context[:100]  # First 100 chars
        
        return MockDelegatedTask(
            original_request=task,
            context=delegation_context,
            target_agent="geometry"
        )
    
    def process_user_input(self, user_input: str) -> str:
        """Process user input and decide on delegation."""
        self.conversation_history.append(user_input)
        
        # Store conversation in memory
        remember("conversation", f"turn_{len(self.conversation_history)}", user_input)
        
        # Simple delegation logic
        geometry_keywords = ["curve", "modify", "create", "arch", "bridge", "geometry"]
        if any(keyword in user_input.lower() for keyword in geometry_keywords):
            delegated_task = self.delegate_to_geometry(user_input)
            return f"Delegated to geometry agent: {delegated_task.original_request}"
        else:
            return f"Handled by triage: {user_input}"


class MockGeometryAgent:
    """Mock geometry agent for testing context reception."""
    
    def __init__(self):
        self.received_context = {}
        self.component_registry = ComponentRegistry()
    
    def receive_delegation(self, delegated_task: MockDelegatedTask) -> MockAgentResponse:
        """Receive and process delegated task."""
        self.received_context = delegated_task.context
        
        # Mock processing logic based on context
        actions = []
        memory_used = {}
        component_refs = []
        
        # Check for component references in context
        if "user_created" in delegated_task.context:
            component_id = delegated_task.context["user_created"]
            actions.append(f"Found component reference: {component_id}")
            component_refs.append(component_id)
            memory_used["component_context"] = component_id
        
        # Process the task
        if "modify" in delegated_task.original_request.lower():
            if component_refs:
                actions.append(f"Modified component: {component_refs[0]}")
            else:
                actions.append("Modify operation - no specific component found")
        elif "create" in delegated_task.original_request.lower():
            new_component = f"created_component_{int(time.time() * 1000) % 10000}"
            actions.append(f"Created component: {new_component}")
            component_refs.append(new_component)
            memory_used["new_component"] = new_component
        
        return MockAgentResponse(
            original_input=delegated_task.original_request,
            actions=actions,
            memory_used=memory_used,
            component_references=component_refs,
            success=len(actions) > 0
        )


class MockConversationAgent:
    """Mock agent for testing complete conversation flows."""
    
    def __init__(self):
        self.conversation_state = {}
        self.component_registry = ComponentRegistry()
        self.conversation_turn = 0
    
    def process(self, user_input: str) -> MockAgentResponse:
        """Process user input and maintain conversation state."""
        self.conversation_turn += 1
        
        # Store input in conversation memory
        remember("conversation", f"turn_{self.conversation_turn}_input", user_input)
        
        actions = []
        memory_used = {}
        component_refs = []
        
        # Mock conversation logic with deterministic responses
        if "create" in user_input.lower() and ("bridge" in user_input.lower() or "structure" in user_input.lower()):
            # Create bridge component
            component_id = "curve_001"
            actions.append(f"created {component_id}")
            self.conversation_state["last_created"] = component_id
            memory_used["last_action"] = f"created {component_id}"
            component_refs.append(component_id)
            
            # Register in component registry
            self.component_registry.register_component(
                component_id, "curve", "Bridge Arch", "Generated bridge arch curve"
            )
            
        elif "modify" in user_input.lower() and any(ref in user_input.lower() for ref in ["curve", "it", "that", "just drew"]):
            # Modify the recently created component
            if "last_created" in self.conversation_state:
                target_component = self.conversation_state["last_created"]
                actions.append(f"modified {target_component}")
                memory_used["last_action"] = f"modified {target_component}"
                memory_used["referenced_component"] = target_component
                component_refs.append(target_component)
            else:
                actions.append("modify requested but no component found")
                
        elif ("add" in user_input.lower() and any(ref in user_input.lower() for ref in ["arch", "it"])) or \
             ("make" in user_input.lower() and any(ref in user_input.lower() for ref in ["arch", "curved", "curve"])):
            # Add/modify arch - references existing component
            if "last_created" in self.conversation_state:
                target_component = self.conversation_state["last_created"]
                action_type = "added arch to" if "add" in user_input.lower() else "modified"
                actions.append(f"{action_type} {target_component}")
                memory_used["last_action"] = f"{action_type} {target_component}"
                memory_used["referenced_component"] = target_component
                component_refs.append(target_component)
            else:
                actions.append("arch operation requested but no component found")
                
        elif "taller" in user_input.lower() or "height" in user_input.lower() or "adjust" in user_input.lower():
            # Height adjustment
            if "last_created" in self.conversation_state:
                target_component = self.conversation_state["last_created"]
                actions.append(f"adjusted {target_component} height")
                memory_used["last_action"] = f"adjusted {target_component} height"
                component_refs.append(target_component)
            else:
                actions.append("height adjustment requested but no component found")
                
        elif "connect" in user_input.lower() and ("support" in user_input.lower() or "it" in user_input.lower()):
            # Connect with supports
            if "last_created" in self.conversation_state:
                target_component = self.conversation_state["last_created"]
                actions.append(f"created supports connecting to {target_component}")
                memory_used["last_action"] = f"connected supports to {target_component}"
                component_refs.append(target_component)
            else:
                actions.append("support connection requested but no component found")
        
        # Store conversation state in memory
        remember("conversation", f"turn_{self.conversation_turn}_response", str(actions))
        
        return MockAgentResponse(
            original_input=user_input,
            actions=actions,
            memory_used=memory_used,
            component_references=component_refs,
            success=len(actions) > 0
        )


class TestAgentDelegationLogic:
    """Test agent delegation preserves context correctly."""
    
    def setup_method(self):
        """Setup clean state for each test."""
        clear_memory(None, "yes")
        time.sleep(0.1)
    
    def test_agent_delegation_preserves_context(self):
        """Test that context is preserved across agent delegation."""
        
        # Create mock triage and geometry agents
        triage = MockTriageAgent()
        geometry = MockGeometryAgent()
        
        # Simulate conversation with context preservation
        triage.add_context("user_created", "bridge_curve_001")
        triage.add_context("project_type", "pedestrian_bridge")
        
        # Test delegation preserves context
        task = "modify the curve"
        delegated_task = triage.delegate_to_geometry(task)
        
        # Validate context was preserved
        assert "bridge_curve_001" in str(delegated_task.context["user_created"])
        assert delegated_task.has_reference_to("curve")
        assert "pedestrian_bridge" in str(delegated_task.context["project_type"])
        
        # Test geometry agent receives context
        response = geometry.receive_delegation(delegated_task)
        assert response.success
        assert "bridge_curve_001" in response.component_references
        assert "Modified component: bridge_curve_001" in response.actions
    
    def test_delegation_with_conversation_history(self):
        """Test delegation includes conversation history."""
        
        triage = MockTriageAgent()
        
        # Build conversation history
        conversation = [
            "Create a bridge structure",
            "Add some supports", 
            "Make the arch higher",
            "Modify the curve you just drew"
        ]
        
        for user_input in conversation:
            triage.process_user_input(user_input)
        
        # Test delegation includes history
        delegated_task = triage.delegate_to_geometry("Modify the curve")
        
        assert "conversation_history" in delegated_task.context
        assert len(delegated_task.context["conversation_history"]) <= 3  # Last 3 interactions
        assert any("curve" in str(item).lower() for item in delegated_task.context["conversation_history"])
    
    def test_context_enrichment_from_memory(self):
        """Test delegation enriches context from memory."""
        
        # Pre-populate memory with relevant context
        remember("components", "main_curve", "Type: curve, Description: bridge arch curve")
        remember("context", "current_project", "Designing pedestrian bridge")
        
        triage = MockTriageAgent()
        geometry = MockGeometryAgent()
        
        # Delegate task that should find relevant memory
        delegated_task = triage.delegate_to_geometry("Modify the main curve")
        
        # Check that relevant memory was included
        assert "relevant_components" in delegated_task.context or "recent_context" in delegated_task.context
        
        # Process delegation
        response = geometry.receive_delegation(delegated_task)
        assert response.success
        assert len(response.memory_used) > 0


class TestMultiTurnConversationFlow:
    """Test multi-turn conversation state management."""
    
    def setup_method(self):
        """Setup clean state for each test."""
        clear_memory(None, "yes")
        time.sleep(0.1)
    
    def test_complete_conversation_flow(self):
        """Test end-to-end conversation logic with deterministic responses."""
        
        # Simulate complete conversation from current_task.md
        conversation = [
            ("Create a bridge arch", "created curve_001"),
            ("Modify the curve you just drew", "modified curve_001"), 
            ("Make it taller", "adjusted curve_001 height"),
            ("Connect them with supports", "created supports connecting to curve_001")
        ]
        
        # Test conversation maintains memory
        agent = MockConversationAgent()
        for user_input, expected_action in conversation:
            response = agent.process(user_input)
            
            # Validate memory was used correctly
            assert expected_action in str(response.actions)
            assert response.used_memory_correctly()
            assert response.success
            
            # Validate component references are maintained
            if "curve_001" in expected_action:
                assert "curve_001" in response.component_references
    
    def test_vague_reference_resolution_in_conversation(self):
        """Test vague references work across conversation turns."""
        
        agent = MockConversationAgent()
        
        # Turn 1: Create something
        response1 = agent.process("Create a bridge arch")
        assert response1.success
        assert "created curve_001" in str(response1.actions)
        
        # Turn 2: Reference with "it"
        response2 = agent.process("Modify it")  
        assert response2.success
        assert "curve_001" in str(response2.actions)
        assert "modified curve_001" in str(response2.actions)
        
        # Turn 3: Reference with "the curve you just drew"
        response3 = agent.process("Make the curve you just drew taller")
        assert response3.success  
        assert "curve_001" in str(response3.actions)
        assert "adjusted curve_001 height" in str(response3.actions)
        
        # Turn 4: Reference with "them" (plural)
        response4 = agent.process("Connect them with supports")
        assert response4.success
        assert "curve_001" in str(response4.actions)
    
    def test_conversation_memory_persistence(self):
        """Test conversation state persists across multiple interactions."""
        
        agent = MockConversationAgent()
        
        # Multi-turn conversation
        interactions = [
            "Create a bridge structure",
            "Add an arch to it", 
            "Make the arch more curved",
            "Connect it to supports",
            "Adjust the height of the arch"
        ]
        
        responses = []
        for interaction in interactions:
            response = agent.process(interaction)
            responses.append(response)
            assert response.success
        
        # Check conversation memory accumulation
        conversation_memory = search_memory("conversation")
        assert "No memories found" not in conversation_memory
        
        # Check that later responses reference earlier components
        for i, response in enumerate(responses[1:], 1):  # Skip first response
            assert response.used_memory_correctly()
            # Later responses should have component references
            if i > 1:  # After initial creation
                assert len(response.component_references) > 0


class TestErrorHandlingInConversation:
    """Test error handling for invalid references and edge cases."""
    
    def setup_method(self):
        """Setup clean state for each test."""
        clear_memory(None, "yes")
        time.sleep(0.1)
    
    def test_invalid_reference_handling(self):
        """Test handling of invalid or ambiguous references."""
        
        agent = MockConversationAgent()
        
        # Try to reference something that doesn't exist
        response = agent.process("Modify the curve")  # No curve created yet
        assert response.success  # Should not crash
        assert "no component found" in str(response.actions).lower()
        
        # Try vague reference without context
        response = agent.process("Make it taller")  # No previous context
        assert response.success
        assert "no component found" in str(response.actions).lower()
    
    def test_delegation_error_recovery(self):
        """Test delegation handles missing context gracefully."""
        
        triage = MockTriageAgent()
        geometry = MockGeometryAgent()
        
        # Delegate without any context
        delegated_task = triage.delegate_to_geometry("Modify something")
        response = geometry.receive_delegation(delegated_task)
        
        # Should handle gracefully, not crash
        assert response.success
        assert len(response.actions) > 0  # Should have some response
    
    def test_memory_corruption_handling(self):
        """Test conversation continues even with memory issues."""
        
        agent = MockConversationAgent()
        
        # Create normal conversation state
        response1 = agent.process("Create a bridge")
        assert response1.success
        
        # Simulate memory corruption by clearing mid-conversation
        clear_memory("conversation", "yes")
        
        # Conversation should continue (may lose context but not crash)
        response2 = agent.process("Modify the bridge")
        assert response2.success  # Should not crash even with missing memory
    
    def test_concurrent_agent_interactions(self):
        """Test multiple agents don't interfere with each other."""
        
        agent1 = MockConversationAgent() 
        agent2 = MockConversationAgent()
        
        # Both agents work on different things
        response1a = agent1.process("Create bridge arch")
        response2a = agent2.process("Create support beam")
        
        # Each should maintain separate state
        assert response1a.success and response2a.success
        assert "curve_001" in str(response1a.actions)  # Agent 1's component
        assert "curve_001" in str(response2a.actions)  # Agent 2's component (different instance)
        
        # References should work within each agent
        response1b = agent1.process("Modify the arch")
        response2b = agent2.process("Modify the beam") 
        
        assert response1b.success and response2b.success


if __name__ == "__main__":
    """Run the realistic conversation logic tests."""
    print("🧪 REALISTIC VALIDATION: Conversation Logic Tests")
    print("Testing agent delegation, context preservation, and conversation flows")
    print("=" * 70)
    
    # Run tests manually for immediate feedback
    test_classes = [
        TestAgentDelegationLogic,
        TestMultiTurnConversationFlow,
        TestErrorHandlingInConversation
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Testing: {test_class.__name__}")
        print("-" * 50)
        
        test_instance = test_class()
        
        # Get test methods
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        for test_method_name in test_methods:
            total_tests += 1
            try:
                # Setup if exists
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                # Run test
                test_method = getattr(test_instance, test_method_name)
                test_method()
                
                print(f"  ✅ {test_method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {test_method_name}: {e}")
    
    print("\n" + "=" * 70)
    print(f"🎯 REALISTIC CONVERSATION VALIDATION RESULTS:")
    print(f"  Tests passed: {passed_tests}/{total_tests}")
    print(f"  Success rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "  No tests run")
    print(f"  Coverage: Agent delegation, Context preservation, Multi-turn flows, Error handling")
    print("=" * 70)
    
    if passed_tests == total_tests:
        print("✅ CONVERSATION LOGIC: All tests passed")
        print("✅ Agent delegation preserves context correctly") 
        print("✅ Multi-turn conversation state management works")
        print("✅ Vague reference resolution in conversation flows")
        print("✅ Error handling for invalid references functional")
    else:
        print("❌ CONVERSATION LOGIC: Some tests failed")
        print("❌ Conversation flow logic has issues")
        
    print("\n💡 What this validates:")
    print("  - Agent delegation with context preservation")
    print("  - Multi-turn conversation state management")
    print("  - Vague reference resolution in conversation flows")
    print("  - Error handling for missing/invalid references")
    print("  - Memory coordination across conversation turns")
    print("\n💡 What this does NOT validate:")
    print("  - Real AI understanding and behavior")
    print("  - Real agent implementation performance") 
    print("  - Real user conversation patterns")
    print("  - Production-scale conversation handling")
    print("\n🎯 This tests conversation LOGIC - the deterministic parts we control")