import serial
import time
import cv2

# --- 核心修改 1: 串口配置 ---
# 1. 端口号：请在 Arduino IDE 的 "工具 -> 端口" 中确认 ESP32 的具体端口
# 2. 波特率：必须改为 115200，以匹配 ESP32 建议的代码设置
try:
    arduinoData = serial.Serial('/dev/cu.usbserial-0001', 115200) 
    time.sleep(2)
    print("ESP32 已连接")
except Exception as e:
    print(f"连接失败: {e}")

def send_coordinates_to_arduino(x, y, w, h):
    # 计算人脸中心点坐标，而不是左上角坐标，这样追踪更准确
    center_x = x + (w // 2)
    center_y = y + (h // 2)
    
    # --- 核心修改 2: 终止符 ---
    # ESP32 代码中使用的是 readStringUntil('\n')，所以这里发送 \n
    coordinates = f"{center_x},{center_y}\n"
    
    arduinoData.write(coordinates.encode())
    print(f"发送坐标 -> X: {center_x}, Y: {center_y}")

capture = cv2.VideoCapture(0) 
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 获取摄像头的真实分辨率，用于后续在 ESP32 中更精准地映射
width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"摄像头分辨率: {width} x {height}")

while True:
    isTrue, frame = capture.read()
    if not isTrue:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 调整检测参数以提高 8 舵机系统的响应速度
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100,100))
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        send_coordinates_to_arduino(x, y, w, h)
        # 找到一张脸后就跳出循环，避免多张脸导致 8 个舵机打架
        break 

    cv2.imshow('Face Tracking - Press D to Quit', frame)

    if cv2.waitKey(1) & 0xFF == ord('d'):
        break

capture.release()
cv2.destroyAllWindows()
arduinoData.close()
