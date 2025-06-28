#!/usr/bin/env python3
"""
Test script to validate quaternion to direction vector conversion.
Tests known quaternion inputs to verify correct transformation.
"""

import math

def quaternion_to_direction_vector_x_forward(quat_wxyz):
    """Current implementation - X-forward"""
    w, x, y, z = quat_wxyz
    vx = 1.0 - 2.0 * (y * y + z * z)
    vy = 2.0 * (x * y - w * z)
    vz = 2.0 * (x * z + w * y)
    return [vx, vy, vz]

def quaternion_to_direction_vector_z_forward(quat_wxyz):
    """Alternative implementation - Z-forward"""
    w, x, y, z = quat_wxyz
    vx = 2.0 * (x * z - w * y)
    vy = 2.0 * (y * z + w * x)
    vz = 1.0 - 2.0 * (x * x + y * y)
    return [vx, vy, vz]

def test_known_quaternions():
    """Test with known quaternion inputs"""
    print("🧪 Testing Quaternion to Direction Vector Conversion")
    print("=" * 60)
    
    # Test cases: [description, quaternion_wxyz, expected_direction_if_any]
    test_cases = [
        ["Identity (no rotation)", [1.0, 0.0, 0.0, 0.0]],
        ["90° rotation around Z", [0.707, 0.0, 0.0, 0.707]],
        ["180° rotation around Z", [0.0, 0.0, 0.0, 1.0]],
        ["90° rotation around Y", [0.707, 0.0, 0.707, 0.0]],
        ["Real AR data", [-0.8096, 0.4399, -0.2585, 0.2901]],
        ["From logs (converted)", [-0.8096479773521423, -0.2584765553474426, -0.43988776206970215, 0.29010120034217834]]
    ]
    
    for description, quat in test_cases:
        print(f"\n📋 Test: {description}")
        print(f"   Input quaternion [w,x,y,z]: {quat}")
        
        # Test X-forward
        result_x = quaternion_to_direction_vector_x_forward(quat)
        print(f"   X-forward result: [{result_x[0]:.4f}, {result_x[1]:.4f}, {result_x[2]:.4f}]")
        
        # Test Z-forward  
        result_z = quaternion_to_direction_vector_z_forward(quat)
        print(f"   Z-forward result: [{result_z[0]:.4f}, {result_z[1]:.4f}, {result_z[2]:.4f}]")
        
        # Check vector magnitude (should be ~1.0 for valid direction)
        mag_x = math.sqrt(sum(v*v for v in result_x))
        mag_z = math.sqrt(sum(v*v for v in result_z))
        print(f"   Magnitudes: X-forward={mag_x:.4f}, Z-forward={mag_z:.4f}")

def test_coordinate_conversions():
    """Test coordinate system conversions"""
    print("\n\n🔄 Testing Coordinate System Conversions")
    print("=" * 60)
    
    # Example from logs
    original_pos = [0.10074692964553833, -0.10033077001571655, -0.5452945232391357]
    original_quat = [-0.8096479773521423, -0.2584765553474426, -0.43988776206970215, 0.29010120034217834]
    
    print(f"Original AR data:")
    print(f"  Position: {original_pos}")
    print(f"  Quaternion: {original_quat}")
    
    # VizorListener conversion
    converted_pos = [-original_pos[1], original_pos[0], original_pos[2]]
    converted_quat = [original_quat[0], -original_quat[2], original_quat[1], original_quat[3]]
    
    print(f"\nAfter VizorListener conversion:")
    print(f"  Position: {converted_pos}")
    print(f"  Quaternion: {converted_quat}")
    
    # Test both direction approaches
    dir_x = quaternion_to_direction_vector_x_forward(converted_quat)
    dir_z = quaternion_to_direction_vector_z_forward(converted_quat)
    
    print(f"\nDirection vectors:")
    print(f"  X-forward: {dir_x}")
    print(f"  Z-forward: {dir_z}")
    
    # Compare with logged result
    logged_result = [0.44468010068267283, 0.6971610471274907, 0.5623397557101804]
    print(f"  Logged result: {logged_result}")
    
    # Calculate differences
    diff_x = [abs(a - b) for a, b in zip(dir_x, logged_result)]
    diff_z = [abs(a - b) for a, b in zip(dir_z, logged_result)]
    
    print(f"\nDifferences from logged result:")
    print(f"  X-forward diff: {diff_x} (total: {sum(diff_x):.4f})")
    print(f"  Z-forward diff: {diff_z} (total: {sum(diff_z):.4f})")

if __name__ == "__main__":
    test_known_quaternions()
    test_coordinate_conversions()
    
    print("\n\n💡 Analysis:")
    print("1. Check which approach gives unit vectors (magnitude ≈ 1.0)")
    print("2. Compare results with logged actual output")
    print("3. Identity quaternion should give base vector (1,0,0) or (0,0,1)")
    print("4. Look for coordinate system consistency")