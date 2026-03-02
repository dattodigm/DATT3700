# Digital Bloom - 具身AI花朵系统架构

## 项目概述

Digital Bloom是一个融合计算机视觉、机器学习与物理计算的交互装置。系统通过摄像头捕捉观众的年龄、性别、情绪、姿态等信息，经ML模型处理后映射到机械花朵的运动参数，创造出具有"情感个性"的仿生AI实体。

## 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        感知层 (Perception Layer)                     │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Webcam     │  │  深度传感器  │  │    环境传感器            │  │
│  │   (USB)      │  │  (Ultrasonic)│  │ (Temperature/PIR)        │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬──────────────┘  │
│         │                  │                      │                 │
│         ▼                  ▼                      ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              特征提取模块 (Feature Extractor)                 │  │
│  │                                                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │ DeepFace     │  │ MediaPipe    │  │  Color Analysis  │  │  │
│  │  │ (情绪/年龄/  │  │ Pose (姿态)  │  │  (画面主色调)     │  │  │
│  │  │  性别识别)   │  │              │  │                  │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │  │
│  └─────────┼─────────────────┼──────────────────┼────────────┘  │
└────────────┼─────────────────┼──────────────────┼───────────────┘
             │                 │                  │
             └─────────────────┴──────────────────┘
                               │
                               ▼ Feature Vector [11维]
┌─────────────────────────────────────────────────────────────────────┐
│                   决策层 (Decision Layer) - ML Brain                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              性格分类器 (Persona Classifier)                  │  │
│  │                                                              │  │
│  │  输入: [anger, disgust, fear, happy, sad, surprise, neutral, │  │
│  │         age, gender, posture_openness, distance]             │  │
│  │         ↓                                                    │  │
│  │  模型: Random Forest / SVM / 小型MLP (scikit-learn)          │  │
│  │         ↓                                                    │  │
│  │  输出: 性格标签 (Defensive, Predatory, Empathy, Joyful,      │  │
│  │         Jealous, Sleepy, Startled, etc.)                     │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────┼─────────────────────────────────────┘
                              │ Persona Label
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                社会层 (Social Layer) - 群体交互                      │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              嫉妒网络 (Jealousy Network)                      │  │
│  │                                                              │  │
│  │  规则引擎:                                                   │  │
│  │  IF Flower_A.state == EMPATHY AND duration > 5s:             │  │
│  │      Flower_B.state = JEALOUS (Override)                     │  │
│  │      Flower_C.state = BOREDOM                                │  │
│  │                                                              │  │
│  │  花朵状态机:                                                 │  │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │  │
│  │  │  IDLE   │───→│ DETECT  │───→│ RESPOND │                 │  │
│  │  └────┬────┘    └─────────┘    └────┬────┘                 │  │
│  │       └──────────────────────────────┘                       │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────┼─────────────────────────────────────┘
                              │ Motion Parameters
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              渲染层 (Rendering Layer) - 物理表现                     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              运动插值器 (Motion Interpolator)                 │  │
│  │                                                              │  │
│  │  输入参数:                                                   │  │
│  │  - bloom_level: 0.0-1.0    (开放度)                          │  │
│  │  - jitter: 0.0-1.0         (颤动强度)                        │  │
│  │  - speed: 0.0-1.0          (运动速度)                        │  │
│  │  - sway_x, sway_y: -1~1    (摇摆方向)                        │  │
│  │                                                              │  │
│  │  数学滤波:                                                   │  │
│  │  - EMA (指数移动平均) 平滑突变                               │  │
│  │  - Perlin Noise 有机颤动                                     │  │
│  │  - PID 目标跟踪                                              │  │
│  │                                                              │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────┼─────────────────────────────────────┘
                              │ OSC Messages
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  执行层 (Actuation Layer)                            │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    WiFi Mesh Network                         │  │
│  │                                                              │  │
│  │   ┌──────────┐      ┌──────────┐      ┌──────────┐        │  │
│  │   │ ESP32    │←────→│ ESP32    │←────→│ ESP32    │        │  │
│  │   │ Flower_A │      │ Flower_B │      │ Flower_C │        │  │
│  │   │ (DC电机) │      │ (Servo)  │      │ (Stepper)│        │  │
│  │   └────┬─────┘      └────┬─────┘      └────┬─────┘        │  │
│  │        │                 │                 │               │  │
│  │        ▼                 ▼                 ▼               │  │
│  │   ┌──────────┐      ┌──────────┐      ┌──────────┐        │  │
│  │   │ Motor    │      │ Servo    │      │ Stepper  │        │  │
│  │   │ Driver   │      │ 8x       │      │ Driver   │        │  │
│  │   └──────────┘      └──────────┘      └──────────┘        │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 三层仿生系统详解

### 第一层：感知与意图识别 (The ML Brain)

**核心思想**：将模糊的情感数据离散化为可理解的"性格标签"

**输入特征矩阵 (11维)**：

| 特征 | 维度 | 范围 | 来源 |
|------|------|------|------|
| Anger | 1 | 0.0-1.0 | DeepFace |
| Disgust | 1 | 0.0-1.0 | DeepFace |
| Fear | 1 | 0.0-1.0 | DeepFace |
| Happy | 1 | 0.0-1.0 | DeepFace |
| Sad | 1 | 0.0-1.0 | DeepFace |
| Surprise | 1 | 0.0-1.0 | DeepFace |
| Neutral | 1 | 0.0-1.0 | DeepFace |
| Age | 1 | 0-100 | DeepFace |
| Gender | 1 | 0/1 | DeepFace |
| Posture Openness | 1 | 0.0-1.0 | MediaPipe Pose |
| Distance | 1 | 0.0-3.0m | Ultrasonic |

**输出性格标签**：

```python
PERSONA_LABELS = {
    'DEFENSIVE': {'bloom': 0.1, 'jitter': 0.8, 'speed': 0.9, 'color': 'red'},
    'PREDATORY': {'bloom': 0.3, 'jitter': 0.5, 'speed': 0.7, 'color': 'orange'},
    'EMPATHY': {'bloom': 0.9, 'jitter': 0.1, 'speed': 0.2, 'color': 'pink'},
    'JOYFUL': {'bloom': 1.0, 'jitter': 0.6, 'speed': 0.8, 'color': 'yellow'},
    'JEALOUS': {'bloom': 0.5, 'jitter': 0.9, 'speed': 1.0, 'color': 'purple'},
    'SLEEPY': {'bloom': 0.2, 'jitter': 0.0, 'speed': 0.1, 'color': 'blue'},
    'STARTLED': {'bloom': 0.0, 'jitter': 1.0, 'speed': 1.0, 'color': 'white'},
    'BOREDOM': {'bloom': 0.4, 'jitter': 0.2, 'speed': 0.3, 'color': 'gray'},
}
```

**ML模型选择**：
- **推荐**: Random Forest (可解释性强，适合小数据)
- **备选**: SVM (边界清晰，适合分类)
- **进阶**: 小型MLP神经网络 (PyTorch/sklearn)

### 第二层：社会网络与状态机 (The Nervous System)

**单体状态机**：

```
状态转换图:
                    ┌─────────────────────────────┐
                    │                             │
    ┌──→ [IDLE] ──→ [DETECTED] ──→ [RESPONDING]  │
    │      ↑            │               │        │
    │      └────────────┴───────────────┘        │
    │                   │                        │
    └───────────────────┴← [JEALOUS OVERRIDE]   │
```

**嫉妒网络算法**：

```python
def jealousy_network_update(flowers):
    """
    检测"被关注不平等"并触发嫉妒反应
    """
    empathy_counts = {f: f.empathy_duration for f in flowers}
    
    if max(empathy_counts.values()) > 5.0:  # 某朵花被关注超过5秒
        favored_flower = max(empathy_counts, key=empathy_counts.get)
        
        for flower in flowers:
            if flower != favored_flower:
                # 强制覆盖为嫉妒状态
                flower.force_state('JEALOUS', duration=3.0)
                flower.set_led_color(255, 0, 255)  # 紫色
                flower.lcd_display("(╯°□°）╯")  # 抖动表情
```

### 第三层：程序化物理渲染 (The Muscle & Eyes)

**运动插值策略**：

```python
class MotionInterpolator:
    def __init__(self):
        self.ema_alpha = 0.3  # 指数平滑系数
        self.perlin_seed = 0
        
    def interpolate(self, target_params, current_params, dt):
        """
        平滑插值 + 有机噪声
        """
        # EMA平滑
        smoothed = self.ema_smooth(target_params, current_params)
        
        # 添加Perlin噪声颤动
        if target_params['jitter'] > 0:
            noise = perlin_noise(self.perlin_seed) * target_params['jitter']
            smoothed['bloom'] += noise * 0.1
            
        # 限制物理边界
        return self.clamp_to_hardware_limits(smoothed)
```

**LCD眼睛动画系统**：

```cpp
// 精灵图动画（非ML）
struct EyeAnimation {
    const char* frames[8];
    uint8_t frame_count;
    uint16_t frame_duration_ms;
};

EyeAnimation animations[] = {
    [STARTLED] = {"(⊙_⊙)", "(◎_◎)", "(⊙_⊙)", ...},
    [SLEEPY]   = {"(-_-)", "(ー_ー)", "(--)", ...},
    [JEALOUS]  = {"(¬‿¬)", "(ಠ_ಠ)", ...},
};
```

## 通信协议 (OSC)

### PC → ESP32 消息格式

```
/flower/{flower_id}/state
    Arguments: [bloom_level, jitter, speed, color_r, color_g, color_b]
    
/flower/{flower_id}/motion
    Arguments: [sway_x, sway_y, rotation]
    
/flower/{flower_id}/lcd
    Arguments: [message_string]
    
/flower/{flower_id}/config
    Arguments: [param_name, value]  # 运行时配置

/system/broadcast
    Arguments: [command, value]  # 全体广播（如紧急停止）
```

### ESP32 → PC 消息格式

```
/flower/{flower_id}/status
    Arguments: [timestamp, current_state, motor_temp, wifi_rssi]

/flower/{flower_id}/sensor
    Arguments: [distance_cm, light_level, temperature]
```

## WiFi网络架构

### 模式1: 热点模式 (AP Mode) - 推荐用于演示

```
PC (Controller)
    │
    │ WiFi Connection
    │
ESP32_A (AP + Flower)
    │ 192.168.4.1
    │
ESP32_B (STA) ←──┐
ESP32_C (STA) ←──┤
                 │ ESP-Mesh
```

### 模式2: 现有网络 (STA Mode)

```
PC (Controller)
    │
    │ WiFi Router
    │
ESP32_A (192.168.1.100)
ESP32_B (192.168.1.101)
ESP32_C (192.168.1.102)
```

### 模式3: Mesh网络 (Advanced)

使用ESP-MESH协议实现去中心化通信，适合大面积部署。

## 硬件抽象层

### 统一硬件接口

```cpp
class FlowerHardware {
public:
    virtual void setBloom(float level) = 0;
    virtual void setJitter(float intensity) = 0;
    virtual void setColor(uint8_t r, uint8_t g, uint8_t b) = 0;
    virtual void setLCD(const char* message) = 0;
    virtual float readDistance() = 0;
};

class DCMotorFlower : public FlowerHardware {
    // DC电机 + LED实现
};

class ServoFlower : public FlowerHardware {
    // 舵机实现
};

class StepperFlower : public FlowerHardware {
    // 步进电机实现
};
```

## 文件结构

```
DATT3700/
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md      # 本文件
│   ├── SETUP_GUIDE.md              # 安装配置指南
│   ├── HARDWARE_ABSTRACTION.md     # 硬件抽象层文档
│   └── API_REFERENCE.md            # API参考手册
│
├── controller/                     # PC端控制器
│   ├── main.py                     # 主程序入口
│   ├── requirements.txt            # Python依赖
│   ├── config.yaml                 # 配置文件
│   │
│   ├── perception/                 # 感知层
│   │   ├── emotion_detector.py     # DeepFace情绪识别
│   │   ├── pose_tracker.py         # MediaPipe姿态跟踪
│   │   ├── face_analyzer.py        # 年龄/性别分析
│   │   └── sensor_fusion.py        # 多传感器融合
│   │
│   ├── decision/                   # 决策层
│   │   ├── persona_classifier.py   # 性格分类器
│   │   ├── ml_trainer.py           # 模型训练工具
│   │   └── models/                 # 预训练模型
│   │       ├── rf_persona.pkl
│   │       └── svm_persona.pkl
│   │
│   ├── social/                     # 社会层
│   │   ├── jealousy_network.py     # 嫉妒网络算法
│   │   ├── flower_orchestrator.py  # 花朵编排器
│   │   └── state_machine.py        # 状态机实现
│   │
│   ├── rendering/                  # 渲染层
│   │   ├── motion_interpolator.py  # 运动插值
│   │   ├── animation_engine.py     # 动画引擎
│   │   └── lcd_generator.py        # LCD内容生成
│   │
│   ├── communication/              # 通信层
│   │   ├── osc_server.py           # OSC服务器
│   │   ├── wifi_manager.py         # WiFi管理
│   │   └── flower_client.py        # 花朵客户端
│   │
│   └── ui/                         # 用户界面
│       ├── control_panel.py        # 主控制面板
│       ├── training_interface.py   # 数据录制界面
│       └── live_preview.py         # 实时预览
│
├── firmware/                       # ESP32固件
│   ├── libraries/                  # 共享库
│   │   ├── WiFiManager/            # WiFi管理库
│   │   ├── OSCProtocol/            # OSC协议库
│   │   └── FlowerHAL/              # 硬件抽象库
│   │
│   └── flowers/                    # 各花朵固件
│       ├── flower_dc_motor/        # DC电机版本
│       │   └── flower_dc_motor.ino
│       ├── flower_servo/           # 舵机版本
│       │   └── flower_servo.ino
│       └── flower_stepper/         # 步进电机版本
│           └── flower_stepper.ino
│
└── training_data/                  # 训练数据集
    ├── recorded_sessions/          # 录制的交互数据
    ├── labeled_dataset.csv         # 标注数据
    └── model_checkpoints/          # 模型检查点
```

## 性能指标

| 组件 | 延迟 | 频率 | 备注 |
|------|------|------|------|
| 情绪识别 | ~200ms | 5 FPS | DeepFace分析 |
| 姿态跟踪 | ~50ms | 20 FPS | MediaPipe实时 |
| ML推理 | <10ms | 30 FPS | scikit-learn极速 |
| OSC通信 | 5-20ms | 30 Hz | WiFi局域网 |
| 舵机响应 | 100-300ms | - | 机械限制 |
| DC电机 | <50ms | - | PWM控制 |

## 安全考虑

1. **物理安全**
   - 舵机速度限制（防止突然转动伤人）
   - 紧急停止机制（空格键立即停止所有运动）
   - 电流限制（防止电机烧毁）

2. **网络安全**
   - WiFi密码保护
   - OSC消息验证（可选）
   - 仅限局域网使用

3. **隐私保护**
   - 所有图像处理本地完成
   - 不存储人脸数据
   - 观众可选择退出追踪

## 扩展性

### 添加新传感器

在`perception/sensor_fusion.py`中扩展：

```python
class SensorFusion:
    def add_sensor(self, sensor_type, sensor_data):
        self.feature_vector.extend(sensor_data)
```

### 添加新花朵类型

1. 在`firmware/flowers/`创建新目录
2. 实现`FlowerHardware`接口
3. 在`controller/communication/`注册新硬件类型

### 添加新性格标签

1. 在`decision/persona_classifier.py`添加标签定义
2. 使用`training_interface.py`录制训练数据
3. 运行`ml_trainer.py`重新训练模型

---

**下一步**: 查看`SETUP_GUIDE.md`开始安装和配置系统。
