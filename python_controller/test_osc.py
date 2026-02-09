#!/usr/bin/env python3
"""
Test OSC Client (requires ESP32 to be running)
Send test commands to verify communication
"""

import sys
import time
sys.path.insert(0, '/home/runner/work/DATT3700/DATT3700/python_controller')

from osc_client import FlowerOSCClient


def test_osc_connection(ip="192.168.1.100", port=8000):
    """Test OSC connection and commands."""
    print(f"Testing OSC connection to {ip}:{port}")
    print("Note: ESP32 must be running and connected to network")
    print("Check ESP32 Serial Monitor for received messages")
    print("-" * 50)
    
    try:
        client = FlowerOSCClient(ip, port)
        print("✓ OSC client created")
        
        # Test servo commands
        print("\nTest 1: Servo center position")
        client.send_servo_command(90, 90)
        time.sleep(1)
        
        print("Test 2: Pan servo sweep")
        for angle in range(60, 121, 10):
            print(f"  Pan: {angle}°")
            client.send_servo_command(angle, 90)
            time.sleep(0.3)
        
        print("Test 3: Tilt servo sweep")
        for angle in range(60, 121, 10):
            print(f"  Tilt: {angle}°")
            client.send_servo_command(90, angle)
            time.sleep(0.3)
        
        # Return to center
        print("  Return to center")
        client.send_servo_command(90, 90)
        time.sleep(1)
        
        # Test flower state
        print("\nTest 4: Flower open/close")
        print("  Opening...")
        for openness in [0.0, 0.25, 0.5, 0.75, 1.0]:
            client.send_flower_state(openness)
            print(f"    Openness: {openness*100:.0f}%")
            time.sleep(0.5)
        
        time.sleep(1)
        
        print("  Closing...")
        for openness in [1.0, 0.75, 0.5, 0.25, 0.0]:
            client.send_flower_state(openness)
            print(f"    Openness: {openness*100:.0f}%")
            time.sleep(0.5)
        
        # Test motor commands
        print("\nTest 5: Motor speed")
        print("  Forward 50%")
        client.send_motor_speed(50)
        time.sleep(1)
        print("  Stop")
        client.send_motor_speed(0)
        time.sleep(0.5)
        print("  Reverse 50%")
        client.send_motor_speed(-50)
        time.sleep(1)
        print("  Stop")
        client.send_motor_speed(0)
        
        # Test tracking mode
        print("\nTest 6: Tracking mode")
        print("  Enable tracking")
        client.send_tracking_mode(1)
        time.sleep(1)
        print("  Disable tracking")
        client.send_tracking_mode(0)
        
        print("\n" + "=" * 50)
        print("✓ All OSC commands sent successfully!")
        print("Check ESP32 Serial Monitor to verify reception")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify ESP32 is powered and running firmware")
        print("2. Check ESP32 WiFi connection (check Serial Monitor)")
        print("3. Verify ESP32 IP address matches the one used")
        print("4. Ensure computer and ESP32 are on same network")
        print("5. Check firewall settings (allow UDP port 8000)")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("OSC Client Test Suite")
    print("=" * 50)
    
    # Get IP from command line or use default
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("Enter ESP32 IP address (default: 192.168.1.100): ").strip()
        if not ip:
            ip = "192.168.1.100"
    
    port = 8000
    
    print(f"\nTarget: {ip}:{port}\n")
    
    try:
        test_osc_connection(ip, port)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
