# F7OWER Kait Node - 固件与调试指南

## 📋 文件清单

- **kait_v2.ino** - 升级版固件（支持 WiFi、OSC、串口控制）
- **kait_osc_debug.py** - OSC 调试脚本
- **kait_serial_debug.py** - 串口调试脚本

## 🔧 硬件接线

### 引脚配置

| 组件 | 功能 | ESP32 引脚 |
|------|------|----------|
| **电机 PWM** | 速度控制 | GPIO 22 |
| **电机方向** | 正反向控制 | GPIO 23 |

### 驱动电路

```
ESP32 GPIO22 → L298N/MOS管 IN1/PWM
ESP32 GPIO23 → L298N/MOS管 IN2/DIR
ESP32 GND ── L298N GND (共地)
```

## 💻 固件上传

1. 使用 Arduino IDE 或 PlatformIO
2. 选择 ESP32 开发板
3. 上传 `kait_v2.ino`

## 🌐 WiFi 配置

编辑 `kait_v2.ino` 中的配置部分：

```cpp
const char* STA_SSID     = "F7OWER";          // 你的 WiFi SSID
const char* STA_PASSWORD = "12345678";        // WiFi 密码
const char* MDNS_NAME = "F7OWER_kait";        // mDNS 设备名
```

上传后，设备将自动连接到 WiFi 并通过 mDNS 广播为 `F7OWER_kait.local`

## 📡 OSC 控制协议

### 基础命令

#### /motor <speed>
设置电机速度

- **参数**: `speed` (整数, -255 ~ 255)
- **含义**: 
  - 负数: 反向旋转
  - 正数: 正向旋转
  - 0: 停止

```bash
# 正向 100% 速度
osc /motor 255

# 反向 50% 速度
osc /motor -128

# 停止
osc /motor 0
```

#### /motion <mode>
执行预设运动模式

- **参数**: `mode` (整数, 1-6)

| 模式 | 名称 | 效果 |
|------|------|------|
| 1 | 缓慢摇晃 | 藤条温柔摇晃 |
| 2 | 快速旋转 | 持续快速旋转 |
| 3 | 脉冲抖动 | 快速前后颤动 |
| 4 | 加速螺旋 | 从慢到快加速 |
| 5 | 平滑制动 | 缓慢减速停止 |
| 6 | 脉冲启动 | 脉冲后稳定运行 |

```bash
# 执行模式 1: 缓慢摇晃
osc /motion 1
```

#### /stop
停止电机

```bash
osc /stop
```

## 🖥️ Python OSC 调试脚本

### 安装依赖

```bash
pip install python-osc
```

### 使用方法

#### 连接到默认地址（127.0.0.1:8888）

```bash
python3 kait_osc_debug.py --interactive
```

#### 连接到指定 IP

```bash
python3 kait_osc_debug.py -i 192.168.1.100 --interactive
```

#### 快速命令

```bash
# 设置速度
python3 kait_osc_debug.py -i 192.168.1.100 --speed 150

# 执行运动模式
python3 kait_osc_debug.py -i 192.168.1.100 --motion 1

# 执行预设序列
python3 kait_osc_debug.py -i 192.168.1.100 --seq gentle_sway

# 停止电机
python3 kait_osc_debug.py -i 192.168.1.100 --stop
```

### 交互模式命令

进入交互模式后，可用的命令：

```
motor <speed>    - 设置电机速度 (-255 ~ 255)
motion <mode>    - 执行运动模式 (1-6)
stop             - 停止电机
seq <name>       - 执行预设序列
seqs             - 列出所有预设序列
help             - 显示帮助
quit/exit        - 退出
```

### 预设序列

| 序列名 | 描述 |
|--------|------|
| `gentle_sway` | 温柔摇晃 - 缓慢来回摆动 5 次 |
| `excited_spin` | 兴奋旋转 - 快速旋转，间隔停顿 3 次 |
| `alert_vibrate` | 告急信号 - 快速颤动（2 个周期） |
| `smooth_wake` | 平滑唤醒 - 从 50 加速到 200，再缓慢减速 |
| `dance` | 舞蹈节奏 - 复杂的组合运动（2 个周期） |
| `test_all` | 测试所有模式 - 依次测试模式 1-6 |

#### 示例

```bash
# 交互模式中
kait> seq gentle_sway

# 或命令行中
python3 kait_osc_debug.py -i 192.168.1.100 --seq dance
```

## 🔌 串口调试脚本

### 安装依赖

```bash
pip install pyserial
```

### 使用方法

#### 列出可用的串口

```bash
python3 kait_serial_debug.py --list-ports
```

输出示例：
```
可用的串口设备:
  /dev/ttyUSB0             - Silicon Labs CP210x USB to UART Bridge
  /dev/ttyUSB1             - USB to UART Bridge Controller
```

#### 连接到默认串口（/dev/ttyUSB0，115200）

```bash
python3 kait_serial_debug.py --interactive
```

#### 连接到指定串口

```bash
python3 kait_serial_debug.py -p /dev/ttyUSB1 --interactive
```

#### 快速命令

```bash
# 设置速度
python3 kait_serial_debug.py --speed 150

# 执行运动模式
python3 kait_serial_debug.py --motion 1

# 执行预设序列
python3 kait_serial_debug.py --seq gentle_sway

# 获取设备信息
python3 kait_serial_debug.py --info

# 停止电机
python3 kait_serial_debug.py --stop
```

### 交互模式命令

```
motor <speed>    - 设置电机速度 (-255 ~ 255)
motion <mode>    - 执行运动模式 (1-6)
stop             - 停止电机
info             - 获取设备信息
seq <name>       - 执行预设序列
seqs             - 列出所有预设序列
help             - 显示帮助
quit/exit        - 退出
```

#### 交互模式示例

```
kait> motor 100
🎚️ 电机设置: 正向 (速度: 100)

kait> motor -80
🎚️ 电机设置: 反向 (速度: 80)

kait> motion 1
📍 执行运动模式 1: 缓慢摇晃

kait> seq smooth_wake
🌅 执行序列: 平滑唤醒

kait> stop
⏹️ 电机已停止

kait> info
📤 发送: info
📥 设备信息:
=== 设备信息 ===
设备名: F7OWER_kait
...
```

## 📊 运动效果对比

| 速度范围 | 方向 | 频率 | 运动效果 |
|---------|------|------|--------|
| 50-100 | 正/反交替 | 低 | 温柔摇晃（安抚） |
| 120-180 | 持续正向 | 中 | 缓慢旋转（展示） |
| 200-255 | 快速切换 | 高 | 剧烈抖动（告急） |
| 0 | — | 0 | 静止（休眠） |

## 🔍 调试技巧

### 1. 验证 WiFi 连接

通过 mDNS 访问：
```bash
ping F7OWER_kait.local
```

或者通过路由器查看设备 IP

### 2. 使用串口监视器

在 Arduino IDE 中打开串口监视器（波特率 115200）查看实时日志

```
✅ WiFi已连接，IP: 192.168.1.100
✅ mDNS 已启动: http://F7OWER_kait.local
✅ OSC 监听端口: 8888
```

### 3. 测试运动模式

按顺序测试每个模式：
```bash
python3 kait_osc_debug.py -i F7OWER_kait.local --seq test_all
```

### 4. 调整参数

在 Python 脚本中修改延时和速度参数测试不同的运动效果

## 🎨 自定义运动模式

### 在 Arduino 中添加新模式

1. 在 `kait_v2.ino` 中添加新函数（参考现有模式）
2. 在 `executeMotionMode()` 中添加对应的 case 分支
3. 更新 OSC 协议文档

### 在 Python 中添加新序列

在 `kait_osc_debug.py` 或 `kait_serial_debug.py` 中：

```python
def sequence_my_custom(self):
    """自定义序列描述"""
    print("\n🎨 执行序列: 自定义运动")
    # 添加你的运动逻辑
    self.set_motor_speed(150)
    time.sleep(2)
    self.stop()
    print("✓ 序列完成\n")
```

然后在 `_list_sequences()` 和 `_run_sequence()` 中注册

## ⚠️ 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 电机不动 | 未给启动冲击 | 检查 GPIO 23 连接（方向控制） |
| 速度不可控 | PWM 冲击时间过长 | 调小 `MOTOR_KICK_START_DELAY` |
| WiFi 无法连接 | SSID/密码错误 | 检查 `STA_SSID` 和 `STA_PASSWORD` |
| OSC 命令无效 | 设备 IP 错误 | 使用 `ping F7OWER_kait.local` 验证 |
| 串口连接失败 | 设备权限问题 | 运行 `sudo chmod 666 /dev/ttyUSB*` |

## 📞 技术支持

- 检查串口输出日志
- 确保硬件接线正确
- 验证电源供应充足
- 尝试重启 ESP32

---

**版本**: Kait v2.0  
**最后更新**: 2026-03-14

