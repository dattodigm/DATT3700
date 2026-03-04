from pythonosc import udp_client
import time

# 连接到ESP32热点后使用
client = udp_client.SimpleUDPClient("192.168.4.1", 8888)

# 切换到手动模式
print("切换到手动模式")
client.send_message("/auto", 0)
time.sleep(1)

# 电机A正转
print("电机A正转")
client.send_message("/motor1", 1)
time.sleep(2)

# LED1设为红色
print("LED1红色")
client.send_message("/led1", [255, 0, 0])
time.sleep(2)

# 预设场景1
print("预设场景1")
client.send_message("/preset", 1)
time.sleep(3)

# 停止所有设备（节约电量，保护电路）
print("停止所有设备")
client.send_message("/preset", 3)  # 预设3是停止所有
time.sleep(1)

print("测试完成，所有设备已停止")
# print("切换到自动模式")
# client.send_message("/auto", 1)