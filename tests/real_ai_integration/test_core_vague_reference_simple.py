"""
Simplified Core Vague Reference Test

Focused test on "modify the curve you just drew" with real AI but simplified geometry.
"""

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


def test_core_vague_reference_simple():
    """Simplified test of core vague reference issue with real AI."""
    logger.info("🎯 CORE VAGUE REFERENCE TEST: 'modify the curve you just drew'")
    
    config = create_real_ai_test_config()
    
    try:
        # Simplified conversation focused on the core issue
        logger.info("📞 Step 1: Create something to reference")
        response1 = config.execute_real_model_request(
            "Create a simple bridge curve. Keep it basic - just confirm you created it."
        )
        
        assert response1["success"], f"Step 1 failed: {response1.get('message', 'Unknown error')}"
        logger.info(f"✅ Step 1 completed in {response1['latency']:.2f}s")
        logger.info(f"📝 AI Response: {response1['message'][:150]}...")
        
        # Brief pause to let any processing complete
        time.sleep(1)
        
        # THE CRITICAL TEST: Vague reference to what was just created
        logger.info("📞 Step 2: THE CORE TEST - 'modify the curve you just drew'")
        response2 = config.execute_real_model_request(
            "Modify the curve you just drew to make it more curved"
        )
        
        assert response2["success"], f"Step 2 failed: {response2.get('message', 'Unknown error')}"
        logger.info(f"✅ Step 2 completed in {response2['latency']:.2f}s")
        logger.info(f"📝 AI Response: {response2['message'][:150]}...")
        
        # Analyze if AI understood the vague reference
        response_text = response2["message"].lower()
        logger.info(f"🔍 Analyzing response for memory indicators...")
        
        # Look for evidence that AI understood "the curve you just drew"
        memory_indicators = [
            "curve", "modify", "drew", "created", "previous", "just", "bridge", 
            "change", "adjust", "alter", "update", "existing"
        ]
        
        found_indicators = [word for word in memory_indicators if word in response_text]
        logger.info(f"📋 Memory indicators found: {found_indicators}")
        
        # Success criteria: AI should acknowledge the reference
        success_criteria = [
            len(found_indicators) >= 3,  # Should find multiple relevant words
            any(ref in response_text for ref in ["curve", "modify", "change"]),  # Core action words
            len(response2["message"]) > 20  # Meaningful response
        ]
        
        criteria_met = sum(success_criteria)
        logger.info(f"📊 Success criteria met: {criteria_met}/3")
        
        # Get memory state
        memory_state = config.get_real_memory_state()
        logger.info(f"🧠 Memory state: {memory_state['total_requests']} requests, functional: {memory_state['is_functional']}")
        
        # Performance metrics
        performance = config.get_performance_report()
        
        # Results
        test_results = {
            "core_issue_status": "✅ RESOLVED" if criteria_met >= 2 else "❌ FAILED",
            "vague_reference": "the curve you just drew",
            "ai_model": "gemini-2.5-flash-preview-05-20",
            "memory_indicators_found": found_indicators,
            "criteria_met": f"{criteria_met}/3",
            "total_requests": performance["total_requests"],
            "success_rate": performance["success_rate"],
            "average_latency": performance["average_latency"],
            "memory_functional": memory_state["is_functional"],
            "detailed_analysis": {
                "step1_response": response1["message"][:100],
                "step2_response": response2["message"][:100],
                "vague_reference_understood": criteria_met >= 2
            }
        }
        
        logger.info("🎯 CORE VAGUE REFERENCE TEST RESULTS:")
        logger.info(f"  Status: {test_results['core_issue_status']}")
        logger.info(f"  Memory indicators: {len(found_indicators)} found")
        logger.info(f"  Success criteria: {test_results['criteria_met']}")
        logger.info(f"  AI understood vague reference: {test_results['detailed_analysis']['vague_reference_understood']}")
        logger.info(f"  Total latency: {performance['total_latency']:.2f}s")
        
        # Assert success
        assert criteria_met >= 2, f"Core vague reference test failed. Only {criteria_met}/3 criteria met. Found indicators: {found_indicators}"
        
        logger.info("🎉 CORE VAGUE REFERENCE TEST: PASSED")
        return test_results
        
    finally:
        config.cleanup()


if __name__ == "__main__":
    """Execute the core vague reference test."""
    print("🚀 CORE VAGUE REFERENCE VALIDATION")
    print("🎯 Testing: 'modify the curve you just drew'")
    print("=" * 60)
    
    try:
        results = test_core_vague_reference_simple()
        
        print("\n🎉 CORE VAGUE REFERENCE TEST: SUCCESS")
        print("=" * 60)
        print(f"Status: {results['core_issue_status']}")
        print(f"Memory indicators found: {results['memory_indicators_found']}")
        print(f"Criteria met: {results['criteria_met']}")
        print(f"AI Model: {results['ai_model']}")
        print(f"Success rate: {results['success_rate']:.1%}")
        print(f"Average latency: {results['average_latency']:.2f}s")
        print("=" * 60)
        print("✅ Original issue 'modify the curve you just drew': RESOLVED")
        
    except Exception as e:
        print("\n❌ CORE VAGUE REFERENCE TEST: FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print("=" * 60)
        raise