"""
Test Scenario 8: Natural Conversation Flow with Memory Persistence

This test validates natural conversation patterns and memory persistence:
1. Natural back-and-forth conversation patterns
2. Memory persistence across multiple conversation turns
3. Context building and accumulation over time
4. Realistic user interaction patterns
5. Long conversation sessions (10+ exchanges)
6. Topic switching and returning to previous contexts
7. Interruptions and resumptions

This addresses the core memory synchronization issue - maintaining context
across natural conversation flows where users build on previous interactions.
"""

import unittest
import time
from .test_agent_config import MemoryTestCase
from .mock_mcp_tools import (
    get_test_state_summary,
    get_components_by_type,
    get_most_recent_component_of_type,
)


class TestNaturalConversationFlow(MemoryTestCase):
    """Test natural conversation patterns with memory persistence."""

    def test_basic_conversation_flow(self):
        """Test basic back-and-forth conversation flow."""
        print("\n=== Test: Basic Conversation Flow ===")

        # Simulate natural conversation about bridge design
        conversation = [
            "Hi, I'd like to design a bridge",
            "Let's start with a simple arch bridge",
            "Great! Can you create the foundation points first?",
            "Perfect. Now connect them with a curve",
            "Excellent! Can you make it into an arch shape?",
            "That looks good. Can you add some height to it?",
            "Nice! What do you think of the design so far?",
            "Can you show me what we've built?",
            "Let's make one more adjustment - can you widen it a bit?",
            "Perfect! I think we're done with this design",
        ]

        responses = []
        memory_progression = []

        for i, user_input in enumerate(conversation):
            print(f"\nUser {i+1}: {user_input}")
            response = self.config.simulate_user_request(user_input)
            responses.append(response)
            print(f"Agent {i+1}: {response}")

            # Track memory progression
            state = self.config.get_memory_state()
            memory_progression.append(state["triage_memory_steps"])
            print(f"Memory steps after exchange {i+1}: {state['triage_memory_steps']}")

        # Verify conversation flow
        print(f"\nConversation memory progression: {memory_progression}")

        # Memory should accumulate throughout conversation
        for i in range(1, len(memory_progression)):
            self.assertGreaterEqual(
                memory_progression[i],
                memory_progression[i - 1],
                f"Memory should persist/grow from exchange {i} to {i+1}",
            )

        # Should have substantial memory by end
        final_state = self.config.get_memory_state()
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            len(conversation),
            "Should have memory from all conversation exchanges",
        )

        # Should have created and tracked components
        self.assertGreater(
            final_state["recent_components_count"],
            0,
            "Should have tracked components through conversation",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Basic conversation flow test passed")

    def test_context_building_conversation(self):
        """Test context building over extended conversation."""
        print("\n=== Test: Context Building Conversation ===")

        # Extended conversation that builds context
        context_conversation = [
            "I want to design a pedestrian bridge for a park",
            "The span should be about 30 meters",
            "Let's make it an arch design for aesthetic appeal",
            "Create the initial arch structure",
            "Good! Now let's add railings on both sides",
            "The railings should be 1.2 meters high for safety",
            "Can you add decorative elements to the arch?",
            "Let's add some lighting fixtures along the railings",
            "Now add stairs at both ends for access",
            "The stairs should have proper handrails too",
            "Can you adjust the arch curve to be more dramatic?",
            "Perfect! Let's add some planters at the entrance points",
            "Now show me the complete bridge design",
            "I'd like to make the arch 20% taller",
            "Excellent! This looks like exactly what the park needs",
        ]

        context_states = []
        for i, context_input in enumerate(context_conversation):
            print(f"\nContext {i+1}: {context_input}")
            response = self.config.simulate_user_request(context_input)
            print(f"Context response {i+1}: {response}")

            # Track context building
            state = self.config.get_memory_state()
            context_states.append(state)

            # Verify context accumulation
            if i > 0:
                self.assertGreaterEqual(
                    state["triage_memory_steps"],
                    context_states[i - 1]["triage_memory_steps"],
                    f"Context should build through exchange {i+1}",
                )

        # Verify rich context building
        final_context = context_states[-1]
        print(f"Final context state: {final_context}")

        # Should have built substantial context
        self.assertGreaterEqual(
            final_context["triage_memory_steps"],
            len(context_conversation),
            "Should have rich context from extended conversation",
        )

        # Should have tracked multiple components/elements
        final_summary = get_test_state_summary()
        print(f"Final design summary: {final_summary}")
        self.assertGreater(
            final_summary["total_components"], 2, "Should have created multiple design elements"
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Context building conversation test passed")

    def test_topic_switching_and_return(self):
        """Test switching topics and returning to previous contexts."""
        print("\n=== Test: Topic Switching and Return ===")

        # Conversation that switches topics and returns
        switching_conversation = [
            # Initial bridge topic
            "Create a suspension bridge design",
            "Make the main span 100 meters",
            "Add cable towers at each end",
            # Switch to different topic
            "Actually, let's also think about a beam bridge option",
            "Create a simple beam bridge with 50-meter span",
            "Add support piers in the middle",
            # Return to original topic
            "Now back to the suspension bridge - can you add the cables?",
            "Make the suspension cables curve naturally",
            "Add deck structure between the cables",
            # Switch again
            "Let's compare - how does the beam bridge look?",
            "Can you strengthen the beam bridge piers?",
            # Final return
            "Back to suspension - let's finalize that design",
            "Add approach spans to the suspension bridge",
            "Show me both bridge designs we've created",
        ]

        topic_responses = []
        for i, topic_input in enumerate(switching_conversation):
            print(f"\nTopic switch {i+1}: {topic_input}")
            response = self.config.simulate_user_request(topic_input)
            topic_responses.append(response)
            print(f"Topic response {i+1}: {response}")

        # Verify topic switching handling
        final_state = self.config.get_memory_state()
        print(f"Topic switching final state: {final_state}")

        # Should maintain memory across topic switches
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            len(switching_conversation),
            "Should maintain memory across topic switches",
        )

        # Should have components from both topics
        final_summary = get_test_state_summary()
        self.assertGreater(
            final_summary["total_components"], 3, "Should have components from multiple topics"
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Topic switching and return test passed")

    def test_interruption_and_resumption(self):
        """Test conversation interruptions and resumptions."""
        print("\n=== Test: Interruption and Resumption ===")

        # Conversation with interruptions
        interruption_conversation = [
            # Start main task
            "Design a cable-stayed bridge",
            "Make it 80 meters long",
            "Add the main tower in the center",
            # Interruption - quick question
            "Wait, what components do we have so far?",
            "OK thanks",
            # Resume main task
            "Continue with the cable-stayed bridge",
            "Add cables from the tower to the deck",
            "Make sure the cables are properly tensioned",
            # Another interruption - modification request
            "Actually, can you debug the current state?",
            "Show me what's in memory right now",
            # Resume and continue
            "Great, now back to the bridge",
            "Add approach spans on both sides",
            "Finalize the cable-stayed design",
            # Final check
            "Show me the completed cable-stayed bridge",
        ]

        interruption_responses = []
        for i, interruption_input in enumerate(interruption_conversation):
            print(f"\nInterruption {i+1}: {interruption_input}")
            response = self.config.simulate_user_request(interruption_input)
            interruption_responses.append(response)
            print(f"Interruption response {i+1}: {response}")

        # Verify interruption handling
        final_state = self.config.get_memory_state()
        print(f"Interruption handling final state: {final_state}")

        # Should handle interruptions without losing context
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            len(interruption_conversation),
            "Should handle interruptions without losing memory",
        )

        # Should maintain component tracking through interruptions
        self.assertGreater(
            final_state["recent_components_count"],
            0,
            "Should maintain component tracking through interruptions",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Interruption and resumption test passed")

    def test_long_session_memory_persistence(self):
        """Test memory persistence in very long conversation sessions."""
        print("\n=== Test: Long Session Memory Persistence ===")

        # Very long conversation session (20+ exchanges)
        long_session = [
            "Start a new bridge project",
            "This will be a major highway bridge",
            "The span needs to be 150 meters",
            "Use a truss design for strength",
            "Create the main truss structure",
            "Add vertical supports every 15 meters",
            "Include diagonal bracing for stability",
            "Now add the deck structure on top",
            "The deck should be 12 meters wide",
            "Add guardrails on both sides",
            "Include expansion joints at key points",
            "Add lighting systems along the deck",
            "Include drainage systems",
            "Add approach ramps at both ends",
            "The approach angle should be gentle",
            "Include safety barriers on approaches",
            "Add inspection walkways under the deck",
            "Include seismic damping systems",
            "Add wind resistance features",
            "Include maintenance access points",
            "Add emergency communication systems",
            "Finalize all structural connections",
            "Review the complete highway bridge design",
            "This looks excellent for heavy traffic",
        ]

        session_memory_points = []
        for i, session_input in enumerate(long_session):
            print(f"\nLong session {i+1}: {session_input}")
            response = self.config.simulate_user_request(session_input)
            print(f"Session response {i+1}: {response}")

            # Track memory at key points
            if i % 5 == 0:  # Every 5th exchange
                state = self.config.get_memory_state()
                session_memory_points.append((i, state["triage_memory_steps"]))
                print(
                    f"Memory checkpoint {len(session_memory_points)}: {state['triage_memory_steps']} steps"
                )

        # Final memory check
        final_session_state = self.config.get_memory_state()
        session_memory_points.append(
            (len(long_session), final_session_state["triage_memory_steps"])
        )

        print(f"Long session memory progression: {session_memory_points}")

        # Verify memory persistence throughout long session
        for i in range(1, len(session_memory_points)):
            prev_memory = session_memory_points[i - 1][1]
            curr_memory = session_memory_points[i][1]
            self.assertGreaterEqual(
                curr_memory,
                prev_memory,
                f"Memory should persist through long session checkpoint {i}",
            )

        # Should have substantial memory accumulation
        self.assertGreaterEqual(
            final_session_state["triage_memory_steps"],
            len(long_session),
            "Should have memory from entire long session",
        )

        # Should have created comprehensive bridge design
        final_summary = get_test_state_summary()
        self.assertGreater(
            final_summary["total_components"], 5, "Long session should create comprehensive design"
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Long session memory persistence test passed")

    def test_natural_language_variations(self):
        """Test natural language variations and informal conversation."""
        print("\n=== Test: Natural Language Variations ===")

        # Conversation with natural language variations
        natural_variations = [
            "Hey, let's build a bridge!",
            "Um, maybe start with something simple?",
            "Yeah, that works. Can you make it, like, an arch?",
            "Cool! Hmm, maybe make it a bit taller?",
            "Nice! Oh wait, can you add some stuff to make it stronger?",
            "Awesome. What if we made it wider too?",
            "Perfect! Oh, one more thing - can you add railings?",
            "Great! Actually, you know what? Let's see the whole thing",
            "Wow, that looks amazing! Maybe just tweak the height a little?",
            "Brilliant! I think we're all set with this design",
        ]

        variation_responses = []
        for i, variation_input in enumerate(natural_variations):
            print(f"\nVariation {i+1}: {variation_input}")
            response = self.config.simulate_user_request(variation_input)
            variation_responses.append(response)
            print(f"Variation response {i+1}: {response}")

        # Verify natural language handling
        final_state = self.config.get_memory_state()
        print(f"Natural variations final state: {final_state}")

        # Should handle informal language while maintaining memory
        self.assertGreaterEqual(
            final_state["triage_memory_steps"],
            len(natural_variations),
            "Should handle natural language variations",
        )

        # Should have created and tracked components despite informal language
        self.assertGreater(
            final_state["recent_components_count"],
            0,
            "Should track components despite informal language",
        )

        # Verify no errors
        self.config.assert_no_stale_component_errors()

        print("✅ Natural language variations test passed")


if __name__ == "__main__":
    # Run individual test
    unittest.main(verbosity=2)
