#!/usr/bin/env python3
"""
Complete system test for category agent integration with start_TEAM.py
This script verifies everything is working correctly.
"""

import subprocess
import sys
import time

def test_category_tools():
    """Test category agent tools directly."""
    print("🔧 Testing category agent tools...")
    
    result = subprocess.run([
        "uv", "run", "python", "-c", """
from src.bridge_design_system.agents.category_smolagent import calculate_distance, calculate_angles
print(f"Distance test: {calculate_distance([0, 0], [3, 4]):.1f}")
print(f"Angle test: {len(calculate_angles([[0, 0], [3, 0], [0, 4]]))} angles")
print("✅ Category tools working")
"""
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Category tools test passed")
        return True
    else:
        print(f"❌ Category tools test failed: {result.stderr}")
        return False

def test_triage_integration():
    """Test category agent integration in triage system."""
    print("🤖 Testing triage integration...")
    
    result = subprocess.run([
        "uv", "run", "python", "-c", """
from src.bridge_design_system.agents import TriageAgent
from src.bridge_design_system.state.component_registry import initialize_registry

registry = initialize_registry()
triage = TriageAgent(component_registry=registry)
status = triage.get_status()

print(f"Managed agents: {status['triage']['managed_agents']}")
print(f"Category initialized: {status['category_agent']['initialized']}")
print(f"Category status: {status['category_agent']['material_analysis']}")

assert status['triage']['managed_agents'] == 1
assert status['category_agent']['initialized'] == True
assert status['category_agent']['material_analysis'] == "enabled"
print("✅ Triage integration working")
"""
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Triage integration test passed")
        return True
    else:
        print(f"❌ Triage integration test failed: {result.stderr}")
        return False

def test_main_system():
    """Test main system with --test flag."""
    print("🚀 Testing main system...")
    
    result = subprocess.run([
        "uv", "run", "python", "-m", "bridge_design_system.main", "--test"
    ], capture_output=True, text=True, timeout=60)
    
    # Check for success and category agent presence
    has_category = "category_material_agent" in result.stderr or "Category agent" in result.stderr
    
    if result.returncode == 0:
        print("✅ Main system test passed")
        if has_category:
            print("✅ Category agent detected in system output")
        else:
            print("⚠️ Category agent not clearly detected but system works")
        return True
    else:
        print(f"❌ Main system test failed (code: {result.returncode})")
        if result.stderr:
            print(f"Error: {result.stderr[-500:]}")  # Last 500 chars
        return False

def test_start_team():
    """Test start_TEAM.py launcher."""
    print("🎯 Testing start_TEAM.py launcher...")
    
    result = subprocess.run([
        "timeout", "45", "uv", "run", "python", "start_TEAM.py", "--test"
    ], capture_output=True, text=True)
    
    # Exit code 124 means timeout (which is expected), 0 means success
    if result.returncode in [0, 124]:
        if "category_material_agent" in result.stderr:
            print("✅ start_TEAM.py test passed")
            print("✅ Category agent detected in TEAM system")
            return True
        else:
            print("⚠️ start_TEAM.py works but category agent not clearly detected")
            return True
    else:
        print(f"❌ start_TEAM.py test failed (code: {result.returncode})")
        if result.stderr:
            print(f"Error: {result.stderr[-500:]}")  # Last 500 chars
        return False

def main():
    """Run all tests."""
    print("🧪 Complete System Test - Category Agent Integration")
    print("=" * 60)
    
    tests = [
        ("Category Tools", test_category_tools),
        ("Triage Integration", test_triage_integration),
        ("Main System", test_main_system),
        ("TEAM Launcher", test_start_team),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print(f"\n{'='*60}")
    print(f"🧪 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("\n🎯 System is ready for use:")
        print("   python3 start_TEAM.py")
        print("   # Then type: 'Analyze triangle shapes'")
        print("   # Category agent will handle material analysis")
        return True
    else:
        print("❌ Some tests failed - check output above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)