# 🌸 Digital Bloom 硬件架构说明

本文档详细说明项目中各花朵的硬件配置和控制方式。

## 📋 硬件清单总览

| 设备 | 数量 | 硬件类型 | 功能描述 | 固件位置 |
|------|------|----------|----------|----------|
| **Sylvie底座** | 1 | Servo (8x) | 人脸追踪底座 | `firmware/flowers/sylvie_composite/` |
| **Sylvie花朵** | 1 | DC Motor (2x) | 两朵花开合控制 | `firmware/flowers/flower_dc_motor/` |
| **Sue** | 1 | Servo + 超声波 | 旋转花朵+距离触发 | `firmware/flowers/sue_rotating/` |

---

## 🌺 Sylvie 复合花朵

Sylvie是**复合系统**，由**两个ESP32**分别控制：

### 架构图

```
PC (Python控制器)
    │
    │ OSC/UDP over WiFi
    ├──────────────────────────┬──────────────────────────┐
    │                          │                          │
ESP32-1 (底座控制器)       ESP32-2 (花朵控制器)       
    │                          │                          
┌───┴───┐                  ┌───┴───┐                  
│8x Servo│                  │2x DC  │                  
│(X/Y轴) │                  │Motor  │                  
│ 追踪   │                  │(开合) │                  
└───────┘                  │2x LED │                  
                           └───────┘                  
```

### ESP32-1: Sylvie底座（人脸追踪）

**硬件:**
- ESP32 Dev Module
- **8个SG90舵机**：
  - X轴（水平）4个：引脚 18, 21, 23, 26
  - Y轴（垂直）4个：引脚 19, 22, 25, 27
- RGB LED灯：引脚 2(R), 4(G), 5(B)

**功能:**
- 接收OSC命令 `/flower/servo [pan] [tilt]`
- 8个舵机同步运动，实现稳定的人脸追踪
- PID平滑控制，避免抖动

**固件:** `firmware/flowers/sylvie_composite/sylvie_composite.ino`

**WiFi配置:**
- SSID: `DigitalBloom_Sylvie_Base`
- IP: `192.168.4.1`
- Port: `8888`

**OSC消息格式:**
```
/flower/servo [int pan] [int tilt]     # 设置舵机角度(0-180)
/flower/composite [float bloom] [int pan] [int tilt] [int r] [int g] [int b]
/flower/state [float bloom] [float jitter] [float speed] [int r] [int g] [int b]
```

### ESP32-2: Sylvie花朵（开合控制）

**硬件:**
- ESP32 Dev Module
- **2个DC电机**（带驱动板如L298N）：
  - 电机A: 引脚 25, 26
  - 电机B: 引脚 32, 33
- 2个RGB LED灯

**功能:**
- 根据情绪参数控制花朵开合
- 正转=打开，反转=关闭
- 根据bloom参数控制开合程度

**固件:** `firmware/flowers/flower_dc_motor/flower_dc_motor.ino`

**WiFi配置:**
- SSID: `DigitalBloom_Sylvie_Petals`
- IP: `192.168.4.2`
- Port: `8888`

**OSC消息格式:**
```
/flower/state [float bloom] [float jitter] [float speed] [int r] [int g] [int b]
/flower/preset [int preset_id]          # 预设场景
```

### Sylvie控制流程

```
1. PC检测人脸 → 计算误差(x_error, y_error)
2. PID控制器 → 计算舵机角度(pan, tilt)
3. 发送OSC到ESP32-1 → 底座追踪人脸
4. 同时发送情绪参数到ESP32-2 → 花朵开合
5. Sylvie"看着"你，同时根据情绪"绽放"或"闭合"
```

---

## 🌸 Sue 旋转花朵

Sue是**独立系统**，使用单个ESP32控制。

### 架构图

```
PC (Python控制器)
    │
    │ OSC/UDP over WiFi (可选)
    │
ESP32 (Sue Controller)
    │
┌───┴───┐
│1x Servo│ ← 旋转花朵
│(旋转)  │
├───────┤
│Ultrasonic│ ← 距离检测
│(HC-SR04)│
├───────┤
│RGB LED│ ← 颜色反馈
└───────┘
```

### 硬件配置

- ESP32 Dev Module
- **1个Servo舵机**（旋转花朵）：引脚 14
- **超声波传感器** HC-SR04：
  - Trig: 引脚 27
  - Echo: 引脚 33
- RGB LED灯：引脚 2(R), 4(G), 5(B)

### 工作模式

**模式1: 自动模式（默认）**
- 超声波检测距离
- 当有人靠近 (<50cm)，花朵开始旋转
- 旋转范围: 0-180度，往复运动

**模式2: OSC控制模式**
- 接收PC的情绪参数
- bloom参数映射到旋转角度
- 例如: bloom=1.0 → 旋转180度

### 固件

**文件:** `firmware/flowers/sue_rotating/sue_rotating.ino`

**WiFi配置:**
- SSID: `DigitalBloom_Sue`
- IP: `192.168.4.3`
- Port: `8888`

**OSC消息格式:**
```
/flower/rotate [int angle]          # 直接设置旋转角度(0-180)
/flower/auto [int 0/1]              # 开关自动模式
/flower/state [float bloom] ...     # 标准状态命令
```

### Sue与Sylvie的区别

| 特性 | Sylvie | Sue |
|------|--------|-----|
| **舵机用途** | 8个底座追踪 | 1个花朵旋转 |
| **运动方式** | 追踪人脸位置 | 旋转展示花朵 |
| **触发方式** | OSC命令控制 | 超声波自动+OSC |
| **花朵动作** | 开合(DC电机) | 旋转(Servo) |

---

## 🔌 接线图

### Sylvie底座 (8 Servo)

```
ESP32 GPIO        Servo
─────────────────────────
18  ────────────  X轴舵机1
21  ────────────  X轴舵机2
23  ────────────  X轴舵机3
26  ────────────  X轴舵机4
19  ────────────  Y轴舵机1
22  ────────────  Y轴舵机2
25  ────────────  Y轴舵机3
27  ────────────  Y轴舵机4

2   ────────────  LED R
4   ────────────  LED G
5   ────────────  LED B

5V  ────────────  Servo VCC (外接电源!)
GND ────────────  Servo GND
```

⚠️ **警告**: 8个舵机电流需求大，**必须**使用外部5V/3A电源！

### Sylvie花朵 (DC电机)

```
ESP32 GPIO        L298N驱动板
─────────────────────────────
25  ────────────  IN1 (电机A)
26  ────────────  IN2 (电机A)
32  ────────────  IN3 (电机B)
33  ────────────  IN4 (电机B)

2   ────────────  LED R
4   ────────────  LED G
5   ────────────  LED B

外接电源12V ────  L298N 12V输入
GND ────────────  L298N GND (共地)
```

### Sue (旋转+超声波)

```
ESP32 GPIO        设备
─────────────────────────
14  ────────────  Servo信号
27  ────────────  超声波Trig
33  ────────────  超声波Echo
2   ────────────  LED R
4   ────────────  LED G
5   ────────────  LED B

5V  ────────────  Servo VCC
GND ────────────  Servo GND + 超声波GND
```

---

## 🎮 PC端控制配置

在 `controller/ui/control_panel.py` 中配置你的硬件:

```python
self.flowers_config = [
    {
        'id': 'sylvie_base',
        'name': 'Sylvie底座(追踪)',
        'ip': '192.168.4.1',
        'port': 8888,
        'hardware_type': 'servo_tracking'
    },
    {
        'id': 'sylvie_petals',
        'name': 'Sylvie花朵(开合)',
        'ip': '192.168.4.2',
        'port': 8888,
        'hardware_type': 'dc_motor'
    },
    {
        'id': 'sue',
        'name': 'Sue(旋转)',
        'ip': '192.168.4.3',
        'port': 8888,
        'hardware_type': 'servo'
    },
]
```

### 追踪模式切换

在控制面板中，你可以：

1. **自动追踪模式**: 
   - PC检测人脸 → 计算舵机角度 → 发送给Sylvie底座
   - Sylvie"看着"最显著的人脸（面积最大+最居中）

2. **手动控制模式**:
   - 使用滑块手动控制舵机角度
   - 适用于调试和录制训练数据

---

## 🔧 快速测试

### 测试Sylvie底座

```bash
# 安装python-osc
pip install python-osc

# 测试脚本
python -c "
from pythonosc import udp_client
client = udp_client.SimpleUDPClient('192.168.4.1', 8888)

# 测试舵机角度
client.send_message('/flower/servo', [45, 90])   # 左45度，水平
client.send_message('/flower/servo', [135, 90])  # 右45度
client.send_message('/flower/servo', [90, 45])   # 上45度
client.send_message('/flower/servo', [90, 135])  # 下45度
client.send_message('/flower/servo', [90, 90])   # 归中

print('测试完成')
"
```

### 测试Sue旋转

```bash
python -c "
from python_osc import udp_client
client = udp_client.SimpleUDPClient('192.168.4.3', 8888)

# 测试旋转
client.send_message('/flower/rotate', [0])      # 0度
client.send_message('/flower/rotate', [90])     # 90度
client.send_message('/flower/rotate', [180])    # 180度

print('测试完成')
"
```

---

## ⚡ 电源要求

| 设备 | 电压 | 电流 | 备注 |
|------|------|------|------|
| ESP32 | 5V | 500mA | USB供电即可 |
| 8x Servo (Sylvie底座) | 5V | 3A+ | **必须外接电源** |
| 2x DC Motor (Sylvie花朵) | 5-12V | 1A | 外接电池或电源 |
| 1x Servo (Sue) | 5V | 1A | 可与ESP32共用 |
| 超声波传感器 | 5V | 15mA | 功耗很小 |

⚠️ **重要**: Sylvie的8个舵机不能直接从ESP32取电，会烧毁板子！

---

## 📞 故障排除

### 舵机抖动
- 检查电源电压是否稳定
- 在舵机电源两端并联100μF电容
- 缩短舵机信号线

### WiFi连接失败
- 检查SSID和密码
- 确保PC连接到正确热点
- 检查IP地址（可能不是192.168.4.x）

### 人脸追踪延迟
- 降低视频分辨率到320x240
- 增加PID的Kd参数减少抖动
- 检查WiFi信号强度

---

如有问题，请参考 `docs/SETUP_GUIDE.md` 获取详细安装步骤。
