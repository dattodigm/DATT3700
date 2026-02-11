from pythonosc import udp_client
import time

# 通过中继ESP32控制（PC连接到ESP32_Relay热点）
client = udp_client.SimpleUDPClient("192.168.4.1", 9000)

print("=== 通过中继器控制 ===\n")

# 切换到手动模式
print("1️⃣ 切换到手动模式")
client.send_message("/auto", 0)
time.sleep(1)

# 测试电机A
print("2️⃣ 电机A正转 (3秒)")
client.send_message("/motor1", 1)
time.sleep(3)

# LED1设为红色
print("3️⃣ LED1红色")
client.send_message("/led1", [255, 0, 0])
time.sleep(2)

# 预设场景1
print("4️⃣ 预设场景1")
client.send_message("/preset", 1)
time.sleep(3)

# 停止所有设备
print("5️⃣ 停止所有设备")
client.send_message("/preset", 3)

print("\n✅ 测试完成，所有设备已停止")