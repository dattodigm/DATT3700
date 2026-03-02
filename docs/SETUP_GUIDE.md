# 📖 Digital Bloom 详细安装指南

本指南将帮助你从零开始搭建完整的Digital Bloom系统。

## 📋 目录

1. [硬件准备](#硬件准备)
2. [软件环境](#软件环境)
3. [固件上传](#固件上传)
4. [PC端配置](#pc端配置)
5. [系统测试](#系统测试)
6. [故障排除](#故障排除)

---

## 硬件准备

### 必需硬件清单

#### PC端
- [ ] 带摄像头的电脑（Windows 10+/macOS/Linux）
- [ ] WiFi功能（用于连接ESP32热点）
- [ ] 8GB+ RAM（DeepFace模型需要内存）

#### ESP32花朵端（根据你的硬件选择）

**方案A: DC电机花朵（推荐初学者）**
- [ ] ESP32开发板 × 1
- [ ] DC电机 × 2（带减速箱）
- [ ] L298N或TB6612FNG电机驱动板 × 1
- [ ] RGB LED灯 × 2
- [ ] 5V/2A电源适配器 × 1
- [ ] 面包板 + 杜邦线

**方案B: Servo舵机花朵**
- [ ] ESP32开发板 × 1
- [ ] SG90或MG996R舵机 × 1-8（根据设计）
- [ ] 超声波传感器HC-SR04（可选）
- [ ] RGB LED灯（可选）
- [ ] 5V/2A电源适配器

**方案C: 步进电机花朵（高级）**
- [ ] ESP32开发板 × 1
- [ ] NEMA 17步进电机 × 1-2
- [ ] A4988或DRV8825驱动板
- [ ] 12V电源

### 3D打印部件

根据你的机械设计，可能需要打印：
- 花瓣机构
- 底座外壳
- 传动齿轮
- 支架

> 💡 **提示**: 本项目不涉及3D建模教学，请使用现有的花朵机械结构。

---

## 软件环境

### 1. 安装Python（PC端）

**Windows:**
1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.8 或更高版本
3. 安装时勾选 "Add Python to PATH"
4. 验证安装:
```bash
python --version
pip --version
```

**macOS:**
```bash
# 使用Homebrew安装
brew install python@3.11

# 验证
python3 --version
pip3 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

### 2. 安装Arduino IDE（ESP32端）

1. 下载Arduino IDE: https://www.arduino.cc/en/software
2. 安装ESP32板支持:
   - 打开 Arduino IDE → 文件 → 首选项
   - 在"附加开发板管理器网址"添加:
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
   - 工具 → 开发板 → 开发板管理器 → 搜索 "ESP32" → 安装

### 3. 安装Arduino库

打开Arduino IDE，安装以下库：
- **WiFi** (自带)
- **WiFiUdp** (自带)
- **ESP32Servo** by Kevin Harrington (舵机控制)
- **OSC** by Adrian Freed (OSC通信)

安装方法：
```
项目 → 加载库 → 管理库 → 搜索库名称 → 安装
```

### 4. 安装Python依赖

```bash
# 进入项目目录
cd DATT3700/controller

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> ⚠️ **注意**: 安装DeepFace时会自动下载TensorFlow和模型文件，可能需要10-20分钟。

### 5. 验证安装

```bash
python main.py --demo
```

如果看到所有组件都显示"✅ 已安装"，说明环境配置成功。

---

## 固件上传

### 步骤1: 配置config.h

1. 复制配置文件模板:
```bash
cp firmware/flowers/config.h firmware/flowers/flower_dc_motor/
```

2. 用Arduino IDE打开 `config.h`，根据你的硬件修改:

```cpp
// ========== 基本配置 ==========
#define FLOWER_ID "flower1"
#define FLOWER_NAME "Sylvie"

// 选择WiFi模式
#define WIFI_MODE_SELECTION WIFI_MODE_AP  // 创建热点

// 热点配置
#define AP_SSID "DigitalBloom_Sylvie"
#define AP_PASSWORD "12345678"

// 选择硬件类型（取消注释对应的行）
#define HARDWARE_TYPE_DC_MOTOR
// #define HARDWARE_TYPE_SERVO
// #define HARDWARE_TYPE_STEPPER

// 引脚配置（根据实际接线修改）
#define MOTOR_A_PIN1 25
#define MOTOR_A_PIN2 26
// ... 其他引脚
```

### 步骤2: 上传固件

1. 用USB线连接ESP32到电脑
2. 在Arduino IDE中选择:
   - 开发板: "ESP32 Dev Module"
   - 端口: 对应的COM端口（Windows）或/dev/ttyUSB0（Linux）
3. 打开 `flower_dc_motor.ino`
4. 点击"上传"按钮
5. 等待上传完成，查看串口监视器（波特率115200）

### 步骤3: 验证WiFi

上传成功后，打开串口监视器，你应该看到:
```
🌸 Digital Bloom - DC Motor 🌸
   具身AI花朵控制系统 v1.0

花朵ID: flower1
花朵名称: Sylvie

==============================================
       WiFi Manager Initializing...
==============================================
Mode: Access Point (创建热点)

✅ WiFi热点已创建！
----------------------------------------------
热点名称 (SSID): DigitalBloom_Sylvie
热点密码: 12345678
ESP32 IP地址: 192.168.4.1
OSC端口: 8888
----------------------------------------------
```

---

## PC端配置

### 1. 连接WiFi

在电脑上:
1. 打开WiFi设置
2. 连接到ESP32的热点（如 `DigitalBloom_Sylvie`）
3. 输入密码 `12345678`
4. 等待连接成功

### 2. 启动控制面板

```bash
cd controller
python main.py
```

### 3. 控制面板界面说明

首次启动时会自动初始化所有组件。

**左侧面板:**
- 📹 **实时预览**: 显示摄像头画面，叠加人脸框和姿态骨架
- 📊 **情绪分析**: 7类情绪的实时条形图
- 显示年龄、性别、姿态开放度

**右侧面板:**
- 🧠 **AI性格识别**: 显示当前预测的性格标签
- 🎚️ **手动控制**: 滑块调节花朵参数
- 📝 **训练数据录制**: 录制功能
- 🌸 **花朵状态**: 显示连接的花朵

### 4. 首次测试

1. 点击"🔗 连接系统"按钮
2. 站在摄像头前，让系统检测到你
3. 观察情绪分析面板，确认识别准确
4. 调节手动控制滑块，点击"应用到花朵"
5. 观察花朵是否响应

---

## 系统测试

### 测试1: 基本通信

在Arduino串口监视器中应该能看到:
```
📨 收到OSC: /flower/state
State: bloom=0.60 jitter=0.40 speed=0.70 RGB=(128,128,128)
```

### 测试2: 情绪识别

在控制面板中:
- 做出开心的表情 → 应该显示JOYFUL或EMPATHY
- 假装惊讶 → 应该显示STARTLED
- 面无表情 → 应该显示BOREDOM或SLEEPY

### 测试3: 训练数据录制

1. 做出特定表情
2. 调整滑块到想要的状态
3. 选择对应的性格标签
4. 点击"开始录制"
5. 重复10次以上
6. 点击"保存训练数据"

---

## 故障排除

### 问题: "无法找到摄像头"

**Windows:**
```bash
# 检查摄像头ID
python -c "import cv2; print([cv2.VideoCapture(i).isOpened() for i in range(3)])"
```

**Linux:**
```bash
# 添加用户到video组
sudo usermod -a -G video $USER
# 重新登录
```

### 问题: "DeepFace模型下载失败"

**原因**: 网络问题或磁盘空间不足

**解决**:
1. 手动下载模型:
   ```bash
   mkdir -p ~/.deepface/weights
   cd ~/.deepface/weights
   # 从 https://github.com/serengil/deepface_models/releases 下载
   wget https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5
   ```

2. 或使用代理:
   ```bash
   export HTTP_PROXY=http://your-proxy:port
   pip install deepface
   ```

### 问题: "控制面板启动时报ImportError"

```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 如果还是不行，尝试单独安装
pip install opencv-python mediapipe deepface scikit-learn python-osc
```

### 问题: "ESP32上传失败"

**检查:**
1. 是否正确选择了开发板型号（ESP32 Dev Module）
2. 是否正确选择了串口
3. 是否安装了ESP32板支持包
4. USB线是否支持数据传输（有些线只能充电）

**解决**:
- 按住ESP32的BOOT按钮，然后点击上传，等出现"Connecting..."时松开
- 或尝试更换USB端口

### 问题: "花朵不响应命令"

**检查:**
1. PC是否连接到ESP32的WiFi热点
2. IP地址是否正确（打开cmd，输入`ipconfig`查看网关）
3. 防火墙是否阻止了UDP通信

**调试**:
```bash
# 在controller目录下
python -c "
from communication.flower_client import FlowerClient
fc = FlowerClient('flower1', 'test', '192.168.4.1', 8888)
fc.send_state(0.5, 0.5, 0.5, 255, 0, 0, 'Test')
print('发送成功')
"
```

### 问题: "电机运行时有噪音或不转"

**可能原因**:
- 电源功率不足
- 电机驱动接线错误
- PWM频率设置不当

**解决**:
- 使用独立的5V/2A电源给电机供电（不要从ESP32取电）
- 检查接线
- 在代码中调整PWM频率

### 问题: "舵机抖动"

**原因**: 电源不稳定或信号干扰

**解决**:
- 在舵机电源引脚并联100μF电容
- 缩短舵机信号线长度
- 使用独立的5V电源给舵机供电

---

## 高级配置

### 使用现有WiFi网络（而非AP模式）

修改 `config.h`:
```cpp
#define WIFI_MODE_SELECTION WIFI_MODE_STA

#define STA_SSID "你的WiFi名称"
#define STA_PASSWORD "你的WiFi密码"
```

重新上传固件后，ESP32会连接到现有网络，你需要在控制面板中指定正确的IP地址。

### 多花朵配置

为每朵花创建独立的配置:

**Flower 1 (config.h):**
```cpp
#define FLOWER_ID "flower1"
#define FLOWER_NAME "Sylvie"
#define AP_SSID "DigitalBloom_Sylvie"
```

**Flower 2 (config.h):**
```cpp
#define FLOWER_ID "flower2"
#define FLOWER_NAME "Sue"
#define AP_SSID "DigitalBloom_Sue"
```

分别上传到两个ESP32，PC需要依次连接不同的热点来控制不同的花。

### 自定义性格标签

编辑 `controller/decision/persona_classifier.py`:

```python
PERSONA_LABELS = [
    'DEFENSIVE',
    'PREDATORY',
    'EMPATHY',
    'JOYFUL',
    'JEALOUS',
    'SLEEPY',
    'STARTLED',
    'BOREDOM',
    'YOUR_NEW_LABEL'  # 添加新标签
]
```

然后录制训练数据并重新训练模型。

---

## 下一步

完成安装后，你可以:
1. 阅读 [系统架构详解](../SYSTEM_ARCHITECTURE.md) 了解技术细节
2. 尝试录制训练数据并训练自己的ML模型
3. 探索嫉妒网络的多花交互效果
4. 修改固件添加新的传感器（距离、声音等）

---

## 获取帮助

如果遇到问题:
1. 查看本指南的故障排除部分
2. 检查Arduino串口监视器的错误信息
3. 查看Python控制台的错误输出
4. 提交Issue到项目仓库

祝使用愉快！🌸
