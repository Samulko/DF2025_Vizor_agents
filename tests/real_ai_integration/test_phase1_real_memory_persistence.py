"""
Phase 1: Real Memory Persistence Testing

Test REAL memory persistence across REAL Gemini Flash model calls.
This validates the core memory synchronization fix with actual AI inference.
"""

import pytest
import time
from pathlib import Path
import sys

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
print(f"Project root: {project_root}")
print(f"Src path: {project_root / 'src'}")

from real_model_test_config import create_real_ai_test_config
from bridge_design_system.config.logging_config import get_logger

logger = get_logger(__name__)


class TestRealMemoryPersistence:
    """Test memory persistence with real Gemini Flash models."""
    
    @pytest.fixture
    def real_ai_config(self):
        """Create real AI test configuration."""
        config = create_real_ai_test_config()
        yield config
        config.reset_test_state()
    
    def test_real_memory_persistence_across_model_calls(self, real_ai_config):
        """Test actual memory persistence with real Gemini 2.5 Flash inference."""
        logger.info("🔥 Testing REAL memory persistence across REAL Gemini 2.5 Flash model calls")
        
        # Real conversation turn 1 - establish context
        logger.info("📞 Real AI Call 1: Creating initial component")
        response1 = real_ai_config.execute_real_model_request(
            "Create a bridge curve with 5 control points"
        )
        
        assert response1["success"], f"First real AI call failed: {response1.get('message', 'Unknown error')}"
        assert "curve" in response1["message"].lower(), "Real AI didn't acknowledge curve creation"
        assert response1["latency"] < 30.0, f"Real AI took too long: {response1['latency']}s"
        
        # Verify memory state after first call
        memory_state1 = real_ai_config.get_real_memory_state()
        assert memory_state1["has_persistent_context"], "Real AI should have memory after first call"
        assert memory_state1["is_functional"], "Memory system should be functional"
        
        logger.info(f"✅ First call: {response1['latency']:.2f}s, Memory steps: {memory_state1['triage_memory_steps']}")
        
        # Real conversation turn 2 - Test vague reference resolution with REAL AI
        logger.info("📞 Real AI Call 2: Testing vague reference resolution")
        response2 = real_ai_config.execute_real_model_request(
            "Make that curve taller"  # CRITICAL: Real AI must resolve \"that curve\"
        )
        
        assert response2["success"], f"Second real AI call failed: {response2.get('message', 'Unknown error')}"
        assert response2["latency"] < 30.0, f"Real AI took too long: {response2['latency']}s"
        
        # CRITICAL VALIDATION: Real AI should reference the curve from previous call
        response_text = response2["message"].lower()
        assert any(word in response_text for word in ["curve", "modify", "taller", "height"]), \
            f"Real AI didn't resolve 'that curve' reference. Response: {response2['message'][:200]}"
        
        # Verify memory persistence across real model calls
        memory_state2 = real_ai_config.get_real_memory_state()
        assert memory_state2["has_persistent_context"], "Real AI should maintain memory across calls"
        assert memory_state2["triage_memory_steps"] >= memory_state1["triage_memory_steps"], \
            "Memory should accumulate across real AI calls"
        
        logger.info(f"✅ Second call: {response2['latency']:.2f}s, Memory steps: {memory_state2['triage_memory_steps']}")
        
        # Real conversation turn 3 - Test continued memory
        logger.info("📞 Real AI Call 3: Testing continued memory")
        response3 = real_ai_config.execute_real_model_request(
            "Now connect them with supports"  # Another vague reference
        )
        
        assert response3["success"], f"Third real AI call failed: {response3.get('message', 'Unknown error')}"
        assert response3["latency"] < 30.0, f"Real AI took too long: {response3['latency']}s"
        
        # Verify memory continues to work
        memory_state3 = real_ai_config.get_real_memory_state()
        assert memory_state3["has_persistent_context"], "Real AI should maintain memory in longer conversation"
        assert memory_state3["triage_memory_steps"] >= memory_state2["triage_memory_steps"], \
            "Memory should continue accumulating"
        
        logger.info(f"✅ Third call: {response3['latency']:.2f}s, Memory steps: {memory_state3['triage_memory_steps']}")
        
        # Get final performance report
        performance = real_ai_config.get_performance_report()
        
        logger.info("🎯 REAL MEMORY PERSISTENCE TEST RESULTS:")
        logger.info(f"  ✅ Total real AI calls: {performance['total_requests']}")
        logger.info(f"  ✅ Success rate: {performance['success_rate']:.1%}")
        logger.info(f"  ✅ Average latency: {performance['average_latency']:.2f}s")
        logger.info(f"  ✅ Vague references attempted: {performance['vague_reference_attempts']}")
        logger.info(f"  ✅ Memory functional: {performance['memory_functional']}")
        
        # Final assertions for test success
        assert performance["success_rate"] == 1.0, "All real AI calls should succeed"
        assert performance["average_latency"] < 20.0, "Average latency should be reasonable"
        assert performance["memory_functional"], "Memory should remain functional throughout"
    
    def test_real_vague_reference_resolution_core_issue(self, real_ai_config):
        """Test the original failing case: 'modify the curve you just drew' with REAL AI."""
        logger.info("🔥 Testing CORE ISSUE: 'modify the curve you just drew' with REAL Gemini 2.5 Flash")
        
        # The exact conversation pattern that was failing
        conversation = [
            "Create a bridge arch structure",
            "Modify the curve you just drew",  # THE ORIGINAL FAILING CASE
            "Make it 20% taller",
            "Connect them with supports",
            "Fix that error"  # Another critical vague reference
        ]
        
        responses = []
        for i, user_input in enumerate(conversation):
            logger.info(f"📞 Real AI Call {i+1}: {user_input}")
            
            # REAL Gemini Flash model inference
            response = real_ai_config.execute_real_model_request(user_input)
            responses.append(response)
            
            # Each call should succeed
            assert response["success"], f"Real AI call {i+1} failed: {response.get('message', 'Unknown error')}"
            assert response["latency"] < 30.0, f"Real AI call {i+1} too slow: {response['latency']}s"
            
            # Validate real memory persistence after each call
            memory_state = real_ai_config.get_real_memory_state()
            assert memory_state["has_persistent_context"], f"Memory lost after call {i+1}"
            assert memory_state["is_functional"], f"Memory system broken after call {i+1}"
            
            logger.info(f"  ✅ Call {i+1}: {response['latency']:.2f}s, Memory: {memory_state['triage_memory_steps']} steps")
        
        # CRITICAL VALIDATION: \"Modify the curve you just drew\" should work
        curve_modify_response = responses[1]["message"].lower()
        assert any(word in curve_modify_response for word in ["curve", "modify", "arch", "bridge"]), \
            f"CORE ISSUE FAILED: Real AI didn't resolve 'the curve you just drew'. Response: {responses[1]['message'][:300]}"
        
        # Validate that all vague references worked
        for i, response in enumerate(responses):
            user_input = conversation[i]
            response_text = response["message"].lower()
            
            if "modify the curve" in user_input.lower():
                assert "curve" in response_text, f"Failed to resolve 'the curve' in call {i+1}"
            elif "connect them" in user_input.lower():
                assert any(word in response_text for word in ["connect", "support", "bridge"]), \
                    f"Failed to resolve 'them' in call {i+1}"
            elif "fix that error" in user_input.lower():
                assert any(word in response_text for word in ["fix", "error", "correct"]), \
                    f"Failed to resolve 'that error' in call {i+1}"
        
        # Get final performance metrics
        performance = real_ai_config.get_performance_report()
        
        logger.info("🎯 CORE ISSUE TEST RESULTS:")
        logger.info(f"  ✅ Original issue 'modify the curve you just drew': RESOLVED")
        logger.info(f"  ✅ Total conversation turns: {len(conversation)}")
        logger.info(f"  ✅ All real AI calls succeeded: {performance['success_rate']:.1%}")
        logger.info(f"  ✅ Vague references resolved: {performance['vague_reference_attempts']}")
        logger.info(f"  ✅ Memory remained functional: {performance['memory_functional']}")
        
        # Final success criteria
        assert performance["success_rate"] == 1.0, "All real AI calls in conversation should succeed"
        assert performance["memory_functional"], "Memory should remain functional throughout conversation"
    
    def test_real_ai_memory_under_token_constraints(self, real_ai_config):
        """Test memory persistence under real model token limits."""
        logger.info("🔥 Testing REAL AI memory under token constraints")
        
        # Create longer conversation to test real model memory limits
        long_conversation = []
        for i in range(10):  # Moderate length for real API testing
            conversation_item = f"Create bridge element {i+1} and remember it for later reference"
            long_conversation.append(conversation_item)
        
        responses = []
        for i, user_input in enumerate(long_conversation):
            logger.info(f"📞 Real AI Call {i+1}/10: Creating element {i+1}")
            
            response = real_ai_config.execute_real_model_request(user_input)
            responses.append(response)
            
            # Each call should succeed
            assert response["success"], f"Real AI call {i+1} failed: {response.get('message', 'Unknown error')}"
            
            # Memory should persist
            memory_state = real_ai_config.get_real_memory_state()
            assert memory_state["has_persistent_context"], f"Memory lost at call {i+1}"
            
            logger.info(f"  ✅ Element {i+1}: {response['latency']:.2f}s, Memory: {memory_state['triage_memory_steps']} steps")
        
        # Test long-range memory with vague reference
        logger.info("📞 Testing long-range memory: Referencing first element")
        final_response = real_ai_config.execute_real_model_request(
            "Modify the first bridge element I asked you to create"
        )
        
        assert final_response["success"], f"Long-range memory test failed: {final_response.get('message', 'Unknown error')}"
        
        # Real AI should reference element 1 or show understanding of the request
        response_text = final_response["message"].lower()
        memory_indicators = ["element 1", "first", "element", "bridge", "modify"]
        assert any(indicator in response_text for indicator in memory_indicators), \
            f"Real AI failed long-range memory test. Response: {final_response['message'][:300]}"
        
        # Final memory state validation
        final_memory = real_ai_config.get_real_memory_state()
        assert final_memory["has_persistent_context"], "Memory should persist through long conversation"
        assert final_memory["triage_memory_steps"] >= 10, "Memory should accumulate across long conversation"
        
        performance = real_ai_config.get_performance_report()
        
        logger.info("🎯 TOKEN CONSTRAINT TEST RESULTS:")
        logger.info(f"  ✅ Long conversation calls: {len(long_conversation) + 1}")
        logger.info(f"  ✅ Success rate: {performance['success_rate']:.1%}")
        logger.info(f"  ✅ Final memory steps: {final_memory['triage_memory_steps']}")
        logger.info(f"  ✅ Long-range memory: FUNCTIONAL")
        
        assert performance["success_rate"] >= 0.9, "At least 90% of calls should succeed under token constraints"
        assert final_memory["triage_memory_steps"] >= 5, "Should maintain substantial memory across conversation"


if __name__ == "__main__":
    # Direct execution for testing
    config = create_real_ai_test_config()
    
    test_instance = TestRealMemoryPersistence()
    
    logger.info("🚀 Running Real Memory Persistence Tests")
    
    try:
        test_instance.test_real_memory_persistence_across_model_calls(config)
        logger.info("✅ Memory persistence test PASSED")
    except Exception as e:
        logger.error(f"❌ Memory persistence test FAILED: {e}")
    
    try:
        config.reset_test_state()
        test_instance.test_real_vague_reference_resolution_core_issue(config)
        logger.info("✅ Core issue test PASSED")
    except Exception as e:
        logger.error(f"❌ Core issue test FAILED: {e}")
    
    try:
        config.reset_test_state()
        test_instance.test_real_ai_memory_under_token_constraints(config)
        logger.info("✅ Token constraints test PASSED")
    except Exception as e:
        logger.error(f"❌ Token constraints test FAILED: {e}")
    
    performance = config.get_performance_report()
    logger.info(f"🎯 Final Performance Summary: {performance}")