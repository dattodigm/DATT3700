# Kait Node v2 - 快速参考

## 🔌 硬件接线

```
+=============================+
|      ESP32 Dev Board        |
|                             |
|  GPIO22 ──┬─ PWM (速度)    |
|           │                 |
|  GPIO23 ──┼─ DIR (方向)    |
|           │                 |
|  GND ─────┴─────────┐       |
+=============================+
                      │
                +─────┴──────────┐
                │                │
         ┌──────┴──────┐     ┌───┴─────┐
         │   L298N     │     │  电源   │
         │   驱动板    │     │  12V    │
         │             │     └───┬─────┘
         │ IN1: PWM ←──┘         │
         │ IN2: DIR ←────────┐   │
         │                   │   │
         │ OUT+ ────→ 电机+ ─┴───┘
         │ OUT- ────→ 电机- ─────┘
         │                   
         │ GND ─────→ GND ←─┴── 共地
         └────────────────────
```

## ⚙️ 配置调整

### WiFi 参数（编辑 kait_v2.ino）

```cpp
const char* STA_SSID     = "F7OWER";           // WiFi 名称
const char* STA_PASSWORD = "12345678";         // WiFi 密码
const char* MDNS_NAME = "F7OWER_kait";         // 设备名（mDNS）
const int OSC_PORT = 8888;                     // OSC 端口
```

### 电机参数

```cpp
const int MOTOR_KICK_START_POWER = 255;        // 启动冲击功率（最高=255）
const int MOTOR_KICK_START_DELAY = 30;         // 启动冲击延时（毫秒）
```

调整这两个参数来改变：
- `POWER` 越高，启动越猛烈
- `DELAY` 越长，启动冲击持续越久

## 📡 OSC 命令速查

### 基础命令

| 命令 | 参数 | 示例 | 效果 |
|------|------|------|------|
| `/motor` | -255 ~ 255 | `/motor 150` | 正向 150 速 |
| `/motor` | 负数 | `/motor -100` | 反向 100 速 |
| `/motion` | 1-6 | `/motion 1` | 执行模式 1 |
| `/stop` | 无 | `/stop` | 停止电机 |

### 运动模式快速参考

```
/motion 1  →  缓慢摇晃 (3~4秒)
/motion 2  →  快速旋转 (2秒)
/motion 3  →  脉冲抖动 (1秒)
/motion 4  →  加速螺旋 (3秒)
/motion 5  →  平滑制动 (1.5秒)
/motion 6  →  脉冲启动 (2秒)
```

## 🎯 Python 脚本常用命令

### OSC 脚本

```bash
# 连接并进入交互模式
python3 kait_osc_debug.py -i F7OWER_kait.local

# 快速控制
python3 kait_osc_debug.py -i 192.168.1.100 --speed 180
python3 kait_osc_debug.py -i 192.168.1.100 --motion 1
python3 kait_osc_debug.py -i 192.168.1.100 --seq dance
```

### 串口脚本

```bash
# 列出串口设备
python3 kait_serial_debug.py --list-ports

# 连接并进入交互模式
python3 kait_serial_debug.py -p /dev/ttyUSB0

# 快速控制
python3 kait_serial_debug.py --speed 180 --motion 1
```

## 🎬 预设序列

| 序列名 | 效果 | 用时 |
|--------|------|------|
| `gentle_sway` | 温柔摇晃 5 次 | ~10 秒 |
| `excited_spin` | 快速旋转 3 次 | ~8 秒 |
| `alert_vibrate` | 告急颤动 2 轮 | ~3 秒 |
| `smooth_wake` | 逐步加速到 200，再减速 | ~8 秒 |
| `dance` | 舞蹈组合 2 轮 | ~6 秒 |
| `test_all` | 测试全部 6 模式 | ~21 秒 |

### 交互模式示例

```
kait> motor 120
🎚️ 电机设置: 正向 (速度: 120)

kait> motion 1
📍 执行运动模式 1: 缓慢摇晃

kait> seq smooth_wake
🌅 执行序列: 平滑唤醒

kait> stop
⏹️ 电机已停止

kait> help
[显示所有可用命令]

kait> quit
👋 再见!
```

## 📊 电机响应特性

### 速度对应表

| 速度值 | 占空比 | 效果 | 适用场景 |
|--------|--------|------|--------|
| 0 | 0% | 停止 | 待命 |
| 50 | 20% | 很慢摇晃 | 睡眠态 |
| 100 | 39% | 缓慢旋转 | 展示 |
| 150 | 59% | 中速旋转 | 交互 |
| 200 | 78% | 快速旋转 | 高兴 |
| 255 | 100% | 极速旋转 | 告急 |

### 方向控制

```
speed > 0   →  正向旋转 (GPIO23 = HIGH)
speed < 0   →  反向旋转 (GPIO23 = LOW)
speed = 0   →  停止     (PWM = 0)
```

## 🔧 故障快速诊断

| 症状 | 可能原因 | 排查方法 |
|------|--------|--------|
| 电机不动 | ❌ GPIO 23 未接 | 检查方向引脚 |
| 无法启动低速 | ❌ 启动冲击功率不足 | 增加 `KICK_START_POWER` |
| WiFi 无法连接 | ❌ SSID/密码错 | 重新检查 WiFi 配置 |
| OSC 无响应 | ❌ IP 地址错 | 用 `ping` 验证设备 |
| 串口连接失败 | ❌ 权限问题 | `sudo chmod 666 /dev/ttyUSB*` |

## 🌟 性能指标

| 指标 | 值 |
|------|-----|
| **PWM 频率** | 20 kHz（无噪音） |
| **PWM 分辨率** | 8 bit (0-255) |
| **启动响应时间** | ~30 ms |
| **速度精度** | ±5 级（256 级中） |
| **OSC 端口** | 8888 (UDP) |
| **mDNS 广播间隔** | 实时 |

## 📝 开发流程

1. **上传固件**
   ```bash
   Arduino IDE → 选择 ESP32 → 上传 kait_v2.ino
   ```

2. **配置 WiFi**
   - 编辑 `kait_v2.ino` 中的 SSID/密码
   - 重新上传

3. **验证连接**
   ```bash
   ping F7OWER_kait.local
   ```

4. **开始调试**
   ```bash
   python3 kait_osc_debug.py -i F7OWER_kait.local --interactive
   ```

---

**💡 提示**: 所有参数均可在运行时通过 OSC 或串口动态调节，无需重新编译

