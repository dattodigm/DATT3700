#!/usr/bin/env python3
"""
Simple Example: Manual Flower Control
Control servos and flower manually without vision tracking.
Useful for testing hardware setup.
"""

import sys
import time

# Allow importing from same directory
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from osc_client import FlowerOSCClient


def manual_control(ip="192.168.1.100", port=8000):
    """Manual control interface."""
    client = FlowerOSCClient(ip, port)
    
    pan_angle = 90
    tilt_angle = 90
    flower_open = 0.0
    
    print("\n" + "=" * 50)
    print("Manual Flower Control")
    print("=" * 50)
    print("\nKeyboard Controls:")
    print("  Arrow keys: Pan/Tilt servos")
    print("  'o': Open flower")
    print("  'c': Close flower")
    print("  'r': Reset to center")
    print("  'q': Quit")
    print("\nPress Enter after each command")
    print("-" * 50)
    
    # Initial position
    client.send_servo_command(pan_angle, tilt_angle)
    client.send_flower_state(flower_open)
    
    print(f"Pan: {pan_angle}° | Tilt: {tilt_angle}° | Flower: {flower_open*100:.0f}%")
    
    try:
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'left':
                pan_angle = max(0, pan_angle - 10)
                client.send_servo_command(pan_angle, tilt_angle)
            elif cmd == 'right':
                pan_angle = min(180, pan_angle + 10)
                client.send_servo_command(pan_angle, tilt_angle)
            elif cmd == 'up':
                tilt_angle = max(0, tilt_angle - 10)
                client.send_servo_command(pan_angle, tilt_angle)
            elif cmd == 'down':
                tilt_angle = min(180, tilt_angle + 10)
                client.send_servo_command(pan_angle, tilt_angle)
            elif cmd == 'o':
                flower_open = 1.0
                client.send_flower_state(flower_open)
            elif cmd == 'c':
                flower_open = 0.0
                client.send_flower_state(flower_open)
            elif cmd == 'r':
                pan_angle = 90
                tilt_angle = 90
                client.send_servo_command(pan_angle, tilt_angle)
            else:
                print("Unknown command")
                continue
            
            print(f"Pan: {pan_angle}° | Tilt: {tilt_angle}° | Flower: {flower_open*100:.0f}%")
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    
    finally:
        # Reset to center
        client.send_servo_command(90, 90)
        client.send_flower_state(0.0)
        print("\nReset to center position")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("Enter ESP32 IP address (default: 192.168.1.100): ").strip()
        if not ip:
            ip = "192.168.1.100"
    
    try:
        manual_control(ip)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
