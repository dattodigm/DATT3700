# 🌸 Digital Bloom - 具身AI花朵系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 一个融合计算机视觉、机器学习与物理计算的交互装置项目
> > **Digital Media课程项目** | 基于队友实际硬件配置重构

## ✨ 项目简介

Digital Bloom是一个具有"情感个性"的3D打印机械花朵系统。通过摄像头捕捉观众的**年龄、性别、情绪、姿态**等信息，经**机器学习模型**处理后映射到机械花朵的运动参数，创造出独特的仿生AI交互体验。

### 核心特性

- 🎭 **实时情绪识别** - 使用DeepFace分析7类情绪
- 🕺 **姿态跟踪** - MediaPipe检测身体开放度和能量
- 🧠 **AI性格分类** - 机器学习将感知数据映射到8种性格标签
- 💜 **嫉妒网络** - 多朵花之间的社会交互算法
- 🌸 **群体编排** - 支持多朵花的协同表演（DC电机 + Servo舵机 + Stepper步进）
- 🎮 **友好控制面板** - 为非程序员设计的Tkinter界面
- 📡 **OSC通信** - 低延迟WiFi控制（基于现有esp32_sylvie实现）

## 🎬 系统演示

```
用户 → Webcam → DeepFace(情绪+年龄+性别) → ML分类器 → 性格标签 → OSC → ESP32花朵
                ↓
            MediaPipe(姿态开放度) → 辅助特征
                ↓
            控制面板(手动录制训练数据)
```

## 🏗️ 系统架构

### 三层仿生系统

```
┌─────────────────────────────────────────────────────────────┐
│  第一层: 感知与意图识别 (ML Brain)                            │
│  输入: 7维情绪 + 年龄 + 性别 + 姿态开放度 + 距离              │
│  模型: Random Forest / SVM / MLP (scikit-learn)              │
│  输出: 性格标签 (Defensive, Empathy, Joyful, Jealous...)    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第二层: 社会网络与状态机 (Nervous System)                    │
│  - 单体状态机 (Idle → Detected → Responding)                 │
│  - 嫉妒网络 (某朵花被关注太久，其他花会嫉妒)                  │
│  - 硬代码实现，绝对可靠                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第三层: 程序化物理渲染 (Muscle & Eyes)                       │
│  - EMA平滑插值 (避免突变)                                     │
│  - Perlin噪声 (有机颤动)                                      │
│  - LCD精灵图动画 (非ML)                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
                        OSC over WiFi
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ESP32 (DC)            ESP32 (Servo)          ESP32 (Stepper)
   ├─ 2x DC电机          ├─ 8x 舵机              └─ (待实现)
   └─ 2x RGB LED         └─ 超声波传感器
```

## 🚀 快速开始

### 硬件要求

**已验证的队友硬件配置：**

| 设备 | 硬件 | 固件位置 | 状态 |
|------|------|----------|------|
| Sylvie | ESP32 + 2x DC电机 + 2x RGB LED | `esp32_firmware/eps32_sylvie/` | ✅ 可用 |
| Sue | ESP32 + 超声波 + 1x Servo | `esp32_firmware/esp32_sue/` | ✅ 可用 |
| Flower 3 | ESP32 + Stepper电机 | `esp32_firmware/` | 🚧 待实现 |

**WiFi配置：**
- 默认AP模式：ESP32创建热点 `DigitalBloom_Flower1`，密码 `12345678`
- PC连接热点后，ESP32 IP为 `192.168.4.1`

### 软件安装

```bash
# 1. 克隆仓库
cd DATT3700

# 2. 安装Python依赖
cd controller
pip install -r requirements.txt

# ⚠️ 首次运行会下载DeepFace模型（约100MB），请耐心等待
```

### 启动控制面板

```bash
# 启动GUI控制面板
python controller/main.py

# 或命令行模式
python controller/main.py --cli

# 训练ML模型
python controller/main.py --train training_data.csv
```

### Arduino固件上传

1. **复制配置文件**
   ```bash
   # 将config.h复制到对应花朵目录
   cp firmware/flowers/config.h firmware/flowers/flower_dc_motor/
   ```

2. **修改config.h**
   ```cpp
   #define FLOWER_ID "flower1"
   #define FLOWER_NAME "Sylvie"
   #define HARDWARE_TYPE_DC_MOTOR  // 根据实际硬件选择
   ```

3. **上传固件**
   - 打开Arduino IDE
   - 安装库：`WiFi`, `WiFiUdp`, `OSCMessage`
   - 上传 `firmware/flowers/flower_dc_motor/flower_dc_motor.ino`

## 🎮 控制面板使用

### 界面说明

```
┌──────────────────────────────────────────────────────────────┐
│ 🌸 Digital Bloom 控制面板                          [连接] [停止]│
├──────────────────────────────────────────────────────────────┤
│  📹 摄像头预览 (640×480)      │  🧠 AI性格识别                  │
│  ┌─────────────────────────┐  │  当前状态: JOYFUL 🟡            │
│  │                         │  │  置信度: 85%                    │
│  │   实时显示人脸框        │  ├─────────────────────────────────┤
│  │   和姿态骨架           │  │  🎚️ 手动控制面板                 │
│  │                         │  │  开放度  [────────●────] 60%    │
│  └─────────────────────────┘  │  颤动    [──────●──────] 40%    │
│                               │  速度    [──────────●──] 70%    │
│  📊 情绪分析                   │  RGB颜色 [R][G][B]滑块          │
│  😠 愤怒 [░░░░] 5%            │                                 │
│  😊 快乐 [████] 85%           │  [✓ 应用到花朵]                 │
│  😢 悲伤 [░░░░] 3%            ├─────────────────────────────────┤
│  😮 惊讶 [░░░░] 5%            │  📝 训练数据录制                 │
│  😐 中性 [░░░░] 2%            │  性格标签: [JOYFUL ▼]           │
│                               │  [🔴 开始录制] 已录制: 0条      │
│  年龄: 25 | 性别: Female       │  [💾 保存训练数据]              │
│  开放度: 0.78 | 姿态: 开放     ├─────────────────────────────────┤
│                               │  🌸 花朵状态                     │
│                               │  🟢 Sylvie (DC) @ 192.168.4.1   │
│                               │  🟢 Sue (Servo) @ 192.168.4.2   │
└──────────────────────────────────────────────────────────────┘
```

### 录制训练数据步骤

1. **站在摄像头前**，让系统检测到你的情绪
2. **观察感知数据**，确认情绪识别准确
3. **调整手动控制滑块**，让花朵呈现你想要的反应
4. **选择性格标签**（如JOYFUL、EMPATHY等）
5. **点击"开始录制"**保存数据点
6. **重复30-50次**，覆盖不同情绪状态
7. **点击"保存训练数据"**，生成CSV文件
8. **训练模型**: `python main.py --train training_data.csv`

## 🌸 性格标签系统

| 标签 | 颜色 | 花朵行为 | 运动参数 |
|------|------|----------|----------|
| **JOYFUL** 🟡 | 黄色 | 完全开放，快速摇摆 | bloom=1.0, jitter=0.6, speed=0.8 |
| **EMPATHY** 💗 | 粉色 | 温柔开放，缓慢运动 | bloom=0.9, jitter=0.1, speed=0.2 |
| **DEFENSIVE** 🔴 | 红色 | 紧张闭合，高频颤动 | bloom=0.1, jitter=0.8, speed=0.9 |
| **STARTLED** ⚪ | 白色 | 瞬间闭合，快速抖动 | bloom=0.0, jitter=1.0, speed=1.0 |
| **JEALOUS** 🟣 | 紫色 | 不安抖动，半开状态 | bloom=0.5, jitter=1.0, speed=1.0 |
| **SLEEPY** 🔵 | 蓝色 | 静止闭合，缓慢呼吸 | bloom=0.2, jitter=0.0, speed=0.1 |
| **PREDATORY** 🟠 | 橙色 | 警觉半开，准备动作 | bloom=0.3, jitter=0.5, speed=0.7 |
| **BOREDOM** ⚫ | 灰色 | 无精打彩，缓慢运动 | bloom=0.4, jitter=0.2, speed=0.3 |

### 嫉妒网络算法

当某朵花被观众持续关注（EMPATHY状态）超过5秒时：
1. 该花获得"被关注"状态
2. 其他花朵自动进入JEALOUS状态（紫色、抖动）
3. 3秒后恢复自然状态

这创造了"花朵间争夺注意力"的社会动力学效果。

## 📁 项目结构

```
DATT3700/
├── 📄 README.md                    # 本文件
├── 📁 controller/                  # PC端Python控制器
│   ├── main.py                    # 主入口
│   ├── requirements.txt           # Python依赖
│   ├── perception/                # 感知层
│   │   ├── emotion_detector.py   # DeepFace情绪识别
│   │   └── pose_tracker.py       # MediaPipe姿态跟踪
│   ├── decision/                  # 决策层
│   │   └── persona_classifier.py # ML性格分类器
│   ├── communication/             # 通信层
│   │   └── flower_client.py      # OSC客户端
│   └── ui/                        # 用户界面
│       └── control_panel.py      # Tkinter控制面板
│
├── 📁 firmware/                    # ESP32固件
│   ├── libraries/
│   │   └── WiFiManager/          # WiFi管理库
│   ├── flowers/
│   │   ├── config.h              # 配置文件模板
│   │   ├── flower_dc_motor/      # DC电机花朵
│   │   │   └── flower_dc_motor.ino
│   │   └── flower_servo/         # 舵机花朵（待实现）
│   └── README.md                 # 固件说明
│
├── 📁 docs/                        # 文档
│   ├── SYSTEM_ARCHITECTURE.md    # 系统架构详解
│   └── SETUP_GUIDE.md            # 详细安装指南
│
└── 📁 training_data/              # 训练数据集（自动生成）
    └── *.csv
```

## 🔧 硬件配置示例

### DC电机花朵 (Sylvie)

```cpp
// config.h 配置
#define FLOWER_ID "flower1"
#define FLOWER_NAME "Sylvie"
#define HARDWARE_TYPE_DC_MOTOR

// 引脚定义
#define MOTOR_A_PIN1 25
#define MOTOR_A_PIN2 26
#define MOTOR_B_PIN1 18
#define MOTOR_B_PIN2 19
#define LED1_R 2
#define LED1_G 4
#define LED1_B 5
```

### Servo花朵 (Sue)

```cpp
// config.h 配置
#define FLOWER_ID "flower2"
#define FLOWER_NAME "Sue"
#define HARDWARE_TYPE_SERVO

// 引脚定义
#define SERVO_PIN 14
#define ULTRASONIC_TRIG 27
#define ULTRASONIC_ECHO 33
```

## 🐛 故障排除

### 问题1: DeepFace模型下载失败
```bash
# 手动下载模型
mkdir -p ~/.deepface/weights
# 从 https://github.com/serengil/deepface_models/releases 下载
# 放入 ~/.deepface/weights/ 目录
```

### 问题2: 控制面板启动失败
```bash
# 检查依赖
python -c "import cv2, mediapipe, deepface, sklearn; print('OK')"

# 如果缺少tkinter（Linux）
sudo apt-get install python3-tk
```

### 问题3: ESP32连接不上
- 检查PC是否连接到ESP32的WiFi热点
- 检查IP地址是否正确（通常是192.168.4.1）
- 检查防火墙是否阻止UDP端口8888

### 问题4: 花朵反应迟钝
- 降低视频分辨率：在`control_panel.py`中修改`frame = cv2.resize(frame, (320, 240))`
- 检查WiFi信号强度
- 减少平滑窗口大小

## 🎯 开发路线图

- [x] 情绪识别模块（DeepFace）
- [x] 姿态跟踪模块（MediaPipe）
- [x] ML性格分类器（scikit-learn）
- [x] WiFi连接管理（AP/STA模式）
- [x] DC电机花朵固件
- [x] Tkinter控制面板
- [x] 训练数据录制功能
- [x] 嫉妒网络算法
- [ ] Servo花朵固件完善
- [ ] Stepper电机支持
- [ ] LCD屏幕动画
- [ ] 多摄像头支持
- [ ] Web界面（Flask）

## 📚 文档

- [系统架构详解](docs/SYSTEM_ARCHITECTURE.md) - 三层仿生系统详细说明
- [详细安装指南](docs/SETUP_GUIDE.md) - 逐步安装和配置教程

## 🙏 致谢

- [DeepFace](https://github.com/serengil/deepface) - 情绪识别
- [MediaPipe](https://mediapipe.dev/) - 姿态跟踪
- [OpenCV](https://opencv.org/) - 计算机视觉
- [scikit-learn](https://scikit-learn.org/) - 机器学习
- [python-osc](https://github.com/attwad/python-osc) - OSC通信

## 👥 团队

Digital Media Art课程项目 - DATT3700

基于队友实际硬件配置重构开发

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**🌸 让每一朵花都有自己的情感个性！**
