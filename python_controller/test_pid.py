#!/usr/bin/env python3
"""
Test script for PID Controller
Run without hardware to verify PID algorithm
"""

import sys
import time

# Allow importing from same directory
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pid_controller import PIDController


def test_pid_basic():
    """Test basic PID functionality."""
    print("Testing PID Controller...")
    
    # Create PID controller
    pid = PIDController(kp=1.0, ki=0.1, kd=0.05, setpoint=0.0)
    
    # Simulate error response
    errors = [100, 80, 60, 40, 20, 10, 5, 2, 1, 0, 0, 0]
    
    print("\nError -> Output:")
    for error in errors:
        output = pid.update(-error)  # Negative because error = setpoint - current
        print(f"  {-error:6.1f} -> {output:6.2f}")
        time.sleep(0.05)
    
    print("\n✓ PID basic test passed")


def test_pid_limits():
    """Test output limits."""
    print("\nTesting PID output limits...")
    
    pid = PIDController(kp=10.0, ki=0.0, kd=0.0, 
                       setpoint=0.0, output_limits=(-10, 10))
    
    # Large error should be clamped
    output = pid.update(-100)
    assert output <= 10 and output >= -10, "Output not clamped!"
    print(f"  Large error output: {output:.2f} (clamped to ±10)")
    
    print("✓ Output limits test passed")


def test_pid_reset():
    """Test PID reset."""
    print("\nTesting PID reset...")
    
    pid = PIDController(kp=1.0, ki=0.5, kd=0.1, setpoint=0.0)
    
    # Accumulate some integral
    for _ in range(10):
        pid.update(-50)
        time.sleep(0.01)
    
    output_before = pid.update(-50)
    print(f"  Output before reset: {output_before:.2f}")
    
    # Reset
    pid.reset()
    output_after = pid.update(-50)
    print(f"  Output after reset: {output_after:.2f}")
    
    assert abs(output_after) < abs(output_before), "Reset didn't work!"
    print("✓ Reset test passed")


def test_pid_tuning():
    """Test changing PID parameters."""
    print("\nTesting PID tuning...")
    
    pid = PIDController(kp=1.0, ki=0.0, kd=0.0, setpoint=0.0)
    pid.update(-10)  # Initialize
    time.sleep(0.02)
    output1 = pid.update(-10)
    print(f"  Output with Kp=1.0: {output1:.2f}")
    
    pid.set_tunings(kp=2.0)
    pid.reset()
    pid.update(-10)  # Initialize
    time.sleep(0.02)
    output2 = pid.update(-10)
    print(f"  Output with Kp=2.0: {output2:.2f}")
    
    assert abs(output2) > abs(output1), "Tuning didn't change output!"
    print("✓ Tuning test passed")


if __name__ == '__main__':
    print("=" * 50)
    print("PID Controller Test Suite")
    print("=" * 50)
    
    try:
        test_pid_basic()
        test_pid_limits()
        test_pid_reset()
        test_pid_tuning()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
