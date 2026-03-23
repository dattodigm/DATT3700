"""Minimal OSC motor test — send ["/motor1", 1, 128] for half-speed forward."""
from pythonosc import udp_client
import time

ESP32_IP = "192.168.4.1"
ESP32_PORT = 8888

client = udp_client.SimpleUDPClient(ESP32_IP, ESP32_PORT)
client.send_message("/auto", 0)            # switch to manual mode
time.sleep(0.2)
client.send_message("/motor1", [1, 128])   # dir=1 (forward), speed=128 (half)
print("✅ Sent /motor1 dir=1 speed=128 — flower should spin at ~50% speed")
