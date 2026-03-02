"""
OSC Client for ESP32 Communication
Sends motor and servo commands via OSC over UDP.
"""

from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder


class FlowerOSCClient:
    """OSC client for sending commands to ESP32."""
    
    def __init__(self, ip="192.168.1.100", port=8000):
        """
        Initialize OSC client.
        
        Args:
            ip: IP address of ESP32
            port: UDP port for OSC communication
        """
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(ip, port)
        
    def send_servo_command(self, pan_angle, tilt_angle):
        """
        Send servo angles to ESP32.
        
        Args:
            pan_angle: Pan servo angle (0-180 degrees)
            tilt_angle: Tilt servo angle (0-180 degrees)
        """
        # Clamp angles to valid range
        pan_angle = max(0, min(180, pan_angle))
        tilt_angle = max(0, min(180, tilt_angle))
        
        # Send OSC message
        self.client.send_message("/flower/servo", [pan_angle, tilt_angle])
    
    def send_flower_state(self, openness):
        """
        Send flower open/close state to ESP32.
        
        Args:
            openness: Flower openness (0.0 = closed, 1.0 = fully open)
        """
        # Clamp to valid range
        openness = max(0.0, min(1.0, openness))
        
        # Send OSC message
        self.client.send_message("/flower/state", openness)
    
    def send_motor_speed(self, speed):
        """
        Send motor speed command to ESP32.
        
        Args:
            speed: Motor speed (-100 to 100, negative = reverse)
        """
        # Clamp to valid range
        speed = max(-100, min(100, speed))
        
        # Send OSC message
        self.client.send_message("/flower/motor", speed)
    
    def send_tracking_mode(self, mode):
        """
        Send tracking mode to ESP32.
        
        Args:
            mode: Tracking mode (0 = idle, 1 = tracking)
        """
        self.client.send_message("/flower/mode", mode)
