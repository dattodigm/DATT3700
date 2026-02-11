from pythonosc import udp_client
import time

# 连接到ESP32_Sylvie热点后
esp1 = udp_client.SimpleUDPClient("192.168.4.1", 8888)  # 主ESP32
esp2 = udp_client.SimpleUDPClient("192.168.4.2", 8889)  # 客户端ESP32


def stop_all():
    """停止所有设备"""
    print("🛑 停止所有设备")
    esp1.send_message("/auto", 0)
    esp2.send_message("/auto", 0)
    time.sleep(0.2)
    esp1.send_message("/preset", 3)
    esp2.send_message("/preset", 3)
    print("✅ 所有设备已停止")


try:
    print("=== 双ESP32花朵控制系统 ===\n")

    # 切换到手动模式
    print("1️⃣ 切换所有ESP32到手动模式")
    esp1.send_message("/auto", 0)
    esp2.send_message("/auto", 0)
    time.sleep(1)

    # 测试ESP32 #1
    print("2️⃣ ESP32 #1 - 电机1正转 + LED1红色")
    esp1.send_message("/motor1", 1)
    esp1.send_message("/led1", [255, 0, 0])
    time.sleep(3)

    # 测试ESP32 #2
    print("3️⃣ ESP32 #2 - 电机3正转 + LED3蓝色")
    esp2.send_message("/motor3", 1)
    esp2.send_message("/led3", [0, 0, 255])
    time.sleep(3)

    # 同时控制
    print("4️⃣ 同时控制 - 预设场景1")
    esp1.send_message("/preset", 1)
    esp2.send_message("/preset", 1)
    time.sleep(3)

    # 安全停止
    stop_all()

except KeyboardInterrupt:
    print("\n检测到中断...")
    stop_all()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    stop_all()