#!/usr/bin/env python3
"""
Vision PID Control System - Main Application
Tracks face or colored object and controls ESP32-driven flower.
"""

import cv2
import argparse
import sys
import time
from pid_controller import PIDController
from vision_tracker import FaceTracker, ColorTracker
from osc_client import FlowerOSCClient


class FlowerControlSystem:
    """Main control system for the flower tracker."""
    
    def __init__(self, tracker_type='face', esp32_ip='192.168.1.100', 
                 esp32_port=8000, camera_id=0):
        """
        Initialize the control system.
        
        Args:
            tracker_type: Type of tracker ('face' or 'color')
            esp32_ip: IP address of ESP32
            esp32_port: UDP port for OSC
            camera_id: Camera device ID
        """
        print(f"Initializing Flower Control System...")
        
        # Initialize camera
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera")
        
        # Set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Camera initialized: {frame_width}x{frame_height}")
        
        # Initialize tracker
        if tracker_type == 'face':
            self.tracker = FaceTracker(frame_width, frame_height)
            print("Using Face Tracker")
        elif tracker_type == 'color':
            self.tracker = ColorTracker(frame_width, frame_height)
            print("Using Color Tracker (tracking red by default)")
        else:
            raise ValueError(f"Unknown tracker type: {tracker_type}")
        
        # Initialize PID controllers for pan and tilt
        # PID tuning: kp=proportional, ki=integral, kd=derivative
        self.pid_pan = PIDController(
            kp=0.15, ki=0.01, kd=0.05,
            setpoint=0.0,  # Error should be 0 (centered)
            output_limits=(-30, 30),  # Max angle change per update
            sample_time=0.03
        )
        
        self.pid_tilt = PIDController(
            kp=0.15, ki=0.01, kd=0.05,
            setpoint=0.0,
            output_limits=(-30, 30),
            sample_time=0.03
        )
        
        # Initialize OSC client
        self.osc_client = FlowerOSCClient(esp32_ip, esp32_port)
        print(f"OSC client initialized: {esp32_ip}:{esp32_port}")
        
        # Servo positions (center position)
        self.pan_angle = 90
        self.tilt_angle = 90
        
        # Tracking state
        self.tracking_active = False
        self.flower_openness = 0.0
        self.lost_target_time = None
        
    def run(self):
        """Main control loop."""
        print("\nStarting control loop...")
        print("Controls:")
        print("  SPACE - Toggle tracking on/off")
        print("  'o'   - Open flower")
        print("  'c'   - Close flower")
        print("  'r'   - Reset servo positions")
        print("  'q'   - Quit")
        print("-" * 50)
        
        try:
            while True:
                # Read frame from camera
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Draw center crosshair
                cv2.line(frame, (self.tracker.center_x - 20, self.tracker.center_y),
                        (self.tracker.center_x + 20, self.tracker.center_y), 
                        (255, 255, 255), 1)
                cv2.line(frame, (self.tracker.center_x, self.tracker.center_y - 20),
                        (self.tracker.center_x, self.tracker.center_y + 20), 
                        (255, 255, 255), 1)
                
                # Get tracking error
                x_error, y_error, detected = self.tracker.get_tracking_error(frame)
                
                if self.tracking_active:
                    if detected:
                        # Calculate PID output
                        pan_correction = self.pid_pan.update(x_error)
                        tilt_correction = self.pid_tilt.update(y_error)
                        
                        # Update servo positions
                        self.pan_angle -= pan_correction  # Negative to follow target
                        self.tilt_angle += tilt_correction
                        
                        # Clamp to valid servo range
                        self.pan_angle = max(0, min(180, self.pan_angle))
                        self.tilt_angle = max(0, min(180, self.tilt_angle))
                        
                        # Send servo commands
                        self.osc_client.send_servo_command(
                            int(self.pan_angle), 
                            int(self.tilt_angle)
                        )
                        
                        # Open flower when target is detected
                        if self.flower_openness < 1.0:
                            self.flower_openness = min(1.0, self.flower_openness + 0.05)
                            self.osc_client.send_flower_state(self.flower_openness)
                        
                        # Reset lost target timer
                        self.lost_target_time = None
                        
                    else:
                        # Target lost
                        if self.lost_target_time is None:
                            self.lost_target_time = time.time()
                        
                        # Close flower after 2 seconds of no detection
                        if time.time() - self.lost_target_time > 2.0:
                            if self.flower_openness > 0.0:
                                self.flower_openness = max(0.0, self.flower_openness - 0.05)
                                self.osc_client.send_flower_state(self.flower_openness)
                
                # Display status
                status_color = (0, 255, 0) if detected else (0, 0, 255)
                status_text = "TRACKING" if self.tracking_active else "IDLE"
                cv2.putText(frame, f"Mode: {status_text}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                cv2.putText(frame, f"Target: {'DETECTED' if detected else 'LOST'}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                cv2.putText(frame, f"Pan: {int(self.pan_angle)}° Tilt: {int(self.tilt_angle)}°", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, f"Flower: {int(self.flower_openness * 100)}%", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if detected:
                    cv2.putText(frame, f"Error: X={x_error:+.0f} Y={y_error:+.0f}", 
                               (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Show frame
                cv2.imshow('Flower Vision Control', frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):
                    self.tracking_active = not self.tracking_active
                    if self.tracking_active:
                        self.osc_client.send_tracking_mode(1)
                        self.pid_pan.reset()
                        self.pid_tilt.reset()
                        print("Tracking ENABLED")
                    else:
                        self.osc_client.send_tracking_mode(0)
                        print("Tracking DISABLED")
                elif key == ord('o'):
                    self.flower_openness = 1.0
                    self.osc_client.send_flower_state(self.flower_openness)
                    print("Flower OPEN")
                elif key == ord('c'):
                    self.flower_openness = 0.0
                    self.osc_client.send_flower_state(self.flower_openness)
                    print("Flower CLOSED")
                elif key == ord('r'):
                    self.pan_angle = 90
                    self.tilt_angle = 90
                    self.osc_client.send_servo_command(90, 90)
                    print("Servos RESET to center")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("\nCleaning up...")
        
        # Return servos to center
        self.osc_client.send_servo_command(90, 90)
        
        # Close flower
        self.osc_client.send_flower_state(0.0)
        
        # Stop tracking
        self.osc_client.send_tracking_mode(0)
        
        # Release camera
        self.cap.release()
        
        # Close windows
        cv2.destroyAllWindows()
        
        print("Cleanup complete")


def main():
    """Entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Vision PID Control System for ESP32 Flower'
    )
    parser.add_argument('--tracker', type=str, default='face',
                       choices=['face', 'color'],
                       help='Type of tracker to use (default: face)')
    parser.add_argument('--ip', type=str, default='192.168.1.100',
                       help='ESP32 IP address (default: 192.168.1.100)')
    parser.add_argument('--port', type=int, default=8000,
                       help='ESP32 OSC port (default: 8000)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID (default: 0)')
    
    args = parser.parse_args()
    
    try:
        system = FlowerControlSystem(
            tracker_type=args.tracker,
            esp32_ip=args.ip,
            esp32_port=args.port,
            camera_id=args.camera
        )
        system.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
