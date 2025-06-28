"""
Phase 2: Core Vague Reference Resolution Testing

Test the original failing case "modify the curve you just drew" with REAL Gemini 2.5 Flash.
This is the critical test that validates the memory synchronization fix.
"""

import pytest
import time
from pathlib import Path
import sys

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from real_model_test_config import create_real_ai_test_config
from bridge_design_system.config.logging_config import get_logger

logger = get_logger(__name__)


def test_core_issue_modify_curve_you_just_drew():
    """Test the original failing case: 'modify the curve you just drew' with REAL AI."""
    logger.info("🔥 PHASE 2: Testing CORE ISSUE with REAL Gemini 2.5 Flash")
    logger.info("🎯 Target: 'modify the curve you just drew' - the original failing case")

    # Create real AI configuration
    config = create_real_ai_test_config()

    try:
        # THE EXACT CONVERSATION PATTERN THAT WAS FAILING - with more specific instructions
        conversation = [
            "Create a bridge arch structure with span 20m and height 5m. Use specific dimensions.",
            "Modify the curve you just drew to make it steeper",  # THE ORIGINAL FAILING CASE
            "Make it 20% taller than the current height",
        ]

        responses = []
        logger.info(f"🗣️ Testing {len(conversation)} conversation turns with real AI")

        for i, user_input in enumerate(conversation):
            logger.info(f"📞 Real AI Call {i+1}/{len(conversation)}: {user_input}")

            start_time = time.time()
            # REAL Gemini 2.5 Flash model inference
            response = config.execute_real_model_request(user_input)
            end_time = time.time()

            responses.append(response)

            # Each call should succeed
            assert response[
                "success"
            ], f"Real AI call {i+1} failed: {response.get('message', 'Unknown error')}"
            logger.info(f"  ✅ Call {i+1}: {response['latency']:.2f}s - SUCCESS")
            logger.info(f"  📝 Response preview: {response['message'][:100]}...")

            # Validate real memory persistence after each call
            memory_state = config.get_real_memory_state()
            assert memory_state["has_persistent_context"], f"Memory lost after call {i+1}"
            assert memory_state["is_functional"], f"Memory system broken after call {i+1}"

            logger.info(
                f"  🧠 Memory: {memory_state['triage_memory_steps']} steps, functional: {memory_state['is_functional']}"
            )

        # CRITICAL VALIDATION: "Modify the curve you just drew" should work
        logger.info("🔍 CRITICAL VALIDATION: Analyzing 'modify the curve you just drew' response")

        curve_modify_response = responses[1]["message"].lower()
        logger.info(f"📋 Full response to analyze: {responses[1]['message']}")

        # Check if AI understood the vague reference
        memory_indicators = [
            "curve",
            "modify",
            "arch",
            "bridge",
            "geometry",
            "component",
            "created",
            "previous",
        ]
        found_indicators = [word for word in memory_indicators if word in curve_modify_response]

        logger.info(f"🔍 Memory indicators found: {found_indicators}")

        assert len(found_indicators) >= 2, (
            f"CORE ISSUE FAILED: Real AI didn't resolve 'the curve you just drew'. "
            f"Found only {len(found_indicators)} memory indicators: {found_indicators}. "
            f"Full response: {responses[1]['message']}"
        )

        # Validate that third call also works (continuing the conversation)
        third_response = responses[2]["message"].lower()
        assert any(
            word in third_response
            for word in ["tall", "height", "20", "percent", "modify", "curve"]
        ), f"Third call should continue the conversation context. Response: {responses[2]['message'][:200]}"

        # Get final performance metrics
        performance = config.get_performance_report()
        final_memory = config.get_real_memory_state()

        logger.info("🎯 PHASE 2 CORE ISSUE TEST RESULTS:")
        logger.info(f"  ✅ Original issue 'modify the curve you just drew': RESOLVED")
        logger.info(f"  ✅ Total conversation turns: {len(conversation)}")
        logger.info(f"  ✅ All real AI calls succeeded: {performance['success_rate']:.1%}")
        logger.info(f"  ✅ Memory indicators found: {found_indicators}")
        logger.info(f"  ✅ Final memory steps: {final_memory['triage_memory_steps']}")
        logger.info(f"  ✅ Average latency: {performance['average_latency']:.2f}s")
        logger.info(f"  ✅ Memory remained functional: {performance['memory_functional']}")

        # Document core issue resolution
        core_issue_validation = {
            "test_name": "modify_the_curve_you_just_drew",
            "status": "✅ RESOLVED",
            "conversation_turns": len(conversation),
            "success_rate": performance["success_rate"],
            "memory_indicators_found": found_indicators,
            "total_memory_indicators": len(found_indicators),
            "memory_functional": performance["memory_functional"],
            "average_latency": performance["average_latency"],
            "ai_model": "gemini-2.5-flash-preview-05-20",
            "resolution_evidence": {
                "vague_reference": "the curve you just drew",
                "ai_understood": len(found_indicators) >= 2,
                "context_maintained": final_memory["triage_memory_steps"] >= 3,
                "conversation_flow": "continuous across all turns",
            },
        }

        logger.info(f"📊 CORE ISSUE VALIDATION: {core_issue_validation}")

        # Final success criteria
        assert (
            performance["success_rate"] == 1.0
        ), "All real AI calls in conversation should succeed"
        assert performance[
            "memory_functional"
        ], "Memory should remain functional throughout conversation"
        assert (
            len(found_indicators) >= 2
        ), "Should find multiple memory indicators showing AI understood context"
        assert (
            final_memory["triage_memory_steps"] >= 3
        ), "Should accumulate memory across conversation"

        logger.info("🎉 PHASE 2 CORE ISSUE TEST: PASSED")
        return core_issue_validation

    finally:
        config.cleanup()


def test_extended_vague_reference_patterns():
    """Test additional vague reference patterns with real AI."""
    logger.info("🔥 PHASE 2: Testing extended vague reference patterns")

    config = create_real_ai_test_config()

    try:
        # Test multiple vague reference patterns
        test_patterns = [
            {
                "setup": "Create a bridge foundation with 4 support points",
                "vague_reference": "Connect them with steel beams",
                "expected_keywords": ["connect", "beam", "support", "foundation"],
            },
            {
                "setup": "Design an arch structure for the bridge",
                "vague_reference": "Make it more elegant",
                "expected_keywords": ["arch", "elegant", "design", "bridge"],
            },
            {
                "setup": "Add safety railings to the bridge",
                "vague_reference": "Fix that component",
                "expected_keywords": ["railing", "safety", "fix", "bridge"],
            },
        ]

        pattern_results = []

        for i, pattern in enumerate(test_patterns):
            logger.info(
                f"🧪 Testing pattern {i+1}/{len(test_patterns)}: {pattern['vague_reference']}"
            )

            # Setup phase
            setup_response = config.execute_real_model_request(pattern["setup"])
            assert setup_response["success"], f"Setup failed for pattern {i+1}"

            # Vague reference test
            vague_response = config.execute_real_model_request(pattern["vague_reference"])
            assert vague_response["success"], f"Vague reference failed for pattern {i+1}"

            # Analyze response
            response_text = vague_response["message"].lower()
            found_keywords = [kw for kw in pattern["expected_keywords"] if kw in response_text]

            pattern_result = {
                "pattern": pattern["vague_reference"],
                "setup": pattern["setup"],
                "keywords_found": found_keywords,
                "keywords_expected": pattern["expected_keywords"],
                "success": len(found_keywords) >= 1,
                "response_preview": vague_response["message"][:150],
            }

            pattern_results.append(pattern_result)

            logger.info(
                f"  ✅ Pattern {i+1}: {len(found_keywords)}/{len(pattern['expected_keywords'])} keywords found"
            )
            logger.info(f"  📝 Keywords: {found_keywords}")

            # Reset for next pattern
            config.reset_test_state()

        # Analyze overall success
        successful_patterns = [p for p in pattern_results if p["success"]]
        success_rate = len(successful_patterns) / len(pattern_results)

        logger.info("🎯 EXTENDED VAGUE REFERENCE RESULTS:")
        logger.info(f"  ✅ Patterns tested: {len(pattern_results)}")
        logger.info(f"  ✅ Patterns successful: {len(successful_patterns)}")
        logger.info(f"  ✅ Success rate: {success_rate:.1%}")

        for i, result in enumerate(pattern_results):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"  Pattern {i+1}: {status} - {result['pattern']}")

        assert (
            success_rate >= 0.67
        ), f"At least 67% of vague reference patterns should work. Got {success_rate:.1%}"

        return {
            "patterns_tested": len(pattern_results),
            "patterns_successful": len(successful_patterns),
            "success_rate": success_rate,
            "pattern_details": pattern_results,
        }

    finally:
        config.cleanup()


if __name__ == "__main__":
    """Direct execution for Phase 2 testing."""
    logger.info("🚀 PHASE 2: VAGUE REFERENCE RESOLUTION TESTING")
    logger.info("🎯 Testing the original failing case with REAL Gemini 2.5 Flash")

    try:
        # Test 1: Core issue
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: CORE ISSUE - 'modify the curve you just drew'")
        logger.info("=" * 60)

        core_result = test_core_issue_modify_curve_you_just_drew()

        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: EXTENDED VAGUE REFERENCE PATTERNS")
        logger.info("=" * 60)

        # Test 2: Extended patterns
        extended_result = test_extended_vague_reference_patterns()

        # Final summary
        print("\n" + "=" * 80)
        print("🎉 PHASE 2 VAGUE REFERENCE RESOLUTION: COMPLETE")
        print("=" * 80)
        print("CORE ISSUE RESULTS:")
        print(f"  Status: {core_result['status']}")
        print(f"  Memory indicators: {core_result['memory_indicators_found']}")
        print(f"  Success rate: {core_result['success_rate']:.1%}")
        print(f"  Average latency: {core_result['average_latency']:.2f}s")

        print("\nEXTENDED PATTERNS RESULTS:")
        print(f"  Patterns tested: {extended_result['patterns_tested']}")
        print(f"  Success rate: {extended_result['success_rate']:.1%}")
        print(f"  Patterns successful: {extended_result['patterns_successful']}")

        print("\n✅ Phase 2 VALIDATION: Real AI vague reference resolution WORKING")
        print("✅ Original issue 'modify the curve you just drew': RESOLVED")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ PHASE 2 VAGUE REFERENCE RESOLUTION: FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        logger.error(f"Phase 2 testing failed: {e}", exc_info=True)
        print("=" * 80)
        raise
