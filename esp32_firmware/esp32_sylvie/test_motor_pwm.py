"""
test_motor_pwm.py - PWM Motor Speed Test / PWM 电机调速测试

Tests the upgraded setMotor() with speed parameter via OSC.
Connect your PC to the ESP32_Sylvie WiFi hotspot first.

使用 OSC 测试升级后的 setMotor() 速度参数。
请先将电脑连接到 ESP32_Sylvie WiFi 热点。

Usage / 用法:
  pip install python-osc
  python test_motor_pwm.py
"""

from pythonosc import udp_client
import time

client = udp_client.SimpleUDPClient("192.168.4.1", 8888)

print("=== PWM Motor Speed Test / PWM 电机调速测试 ===\n")

# Switch to manual mode / 切换到手动模式
client.send_message("/auto", 0)
time.sleep(0.5)

# Test: Motor 1 forward at half speed / 电机1 半速正转
print("1. Motor A forward, speed=128 (half)")
client.send_message("/motor1", [1, 128])
time.sleep(3)

# Test: Motor 1 forward at full speed / 电机1 全速正转
print("2. Motor A forward, speed=255 (full)")
client.send_message("/motor1", [1, 255])
time.sleep(3)

# Test: Motor 1 reverse at quarter speed / 电机1 1/4速反转
print("3. Motor A reverse, speed=64 (quarter)")
client.send_message("/motor1", [-1, 64])
time.sleep(3)

# Stop all / 全部停止
print("4. Stop all")
client.send_message("/preset", 3)

print("\n✅ Test complete / 测试完成")
