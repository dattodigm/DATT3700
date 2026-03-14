# 🚀 Kait v2 - 快速启动指南

## 📋 30 秒快速开始

### 1️⃣ 安装（1 分钟）
```bash
cd python_host
./install_kait_tools.sh
```

### 2️⃣ 上传固件（2 分钟）
- 打开 Arduino IDE
- 打开 `esp32_firmware/esp32_kait/kait_v2.ino`
- 编辑 WiFi 配置（SSID/密码）
- 上传到 ESP32

### 3️⃣ 开始控制（10 秒）
```bash
python3 python_host/kait_osc_debug.py -i F7OWER_kait.local --interactive
```

**完成！** 🎉

---

## 📂 重要文件位置

| 文件 | 位置 | 说明 |
|------|------|------|
| **主固件** | `esp32_firmware/esp32_kait/kait_v2.ino` | ⭐ 上传到 ESP32 |
| **快速参考** | `esp32_firmware/esp32_kait/QUICK_REFERENCE.md` | 📖 5 分钟速查 |
| **完整指南** | `esp32_firmware/esp32_kait/KAIT_V2_GUIDE.md` | 📚 详细学习 |
| **OSC 工具** | `python_host/kait_osc_debug.py` | 🌐 网络控制 |
| **串口工具** | `python_host/kait_serial_debug.py` | 🔌 本地调试 |
| **可视化** | `python_host/kait_motion_visualization.py` | 📊 查看效果 |

---

## 🎯 3 种使用方式

### 方式 1️⃣ 远程 WiFi 控制（推荐）

```bash
# 第一次运行：查找设备 IP
ping F7OWER_kait.local

# 交互式控制
python3 python_host/kait_osc_debug.py -i F7OWER_kait.local --interactive

# 快速命令
python3 python_host/kait_osc_debug.py -i F7OWER_kait.local --motion 1
python3 python_host/kait_osc_debug.py -i F7OWER_kait.local --seq dance
```

### 方式 2️⃣ USB 串口控制（调试）

```bash
# 列出可用串口
python3 python_host/kait_serial_debug.py --list-ports

# 连接设备
python3 python_host/kait_serial_debug.py -p /dev/ttyUSB0 --interactive
```

### 方式 3️⃣ 直接在 Arduino IDE 测试

1. 打开 Arduino IDE 的 "串口监视器" (波特率 115200)
2. 输入命令：
   ```
   motor 100
   motion 1
   stop
   info
   ```

---

## 🎮 常用命令

### 速度控制
```
motor 100      # 正向，速度 100
motor -100     # 反向，速度 100
motor 0        # 停止
```

### 运动模式
```
motion 1       # 缓慢摇晃
motion 2       # 快速旋转
motion 3       # 脉冲抖动
motion 4       # 加速螺旋
motion 5       # 平滑制动
motion 6       # 脉冲启动
```

### 预设序列（OSC 工具）
```
seq gentle_sway      # 温柔摇晃 5 次
seq excited_spin     # 快速旋转 3 次
seq alert_vibrate    # 告急信号
seq smooth_wake      # 平滑唤醒
seq dance            # 舞蹈节奏
seq test_all         # 测试所有模式
```

### 可视化
```bash
# 查看所有运动模式的时序图
python3 python_host/kait_motion_visualization.py --all

# 保存为 PNG
python3 python_host/kait_motion_visualization.py --all -o motion.png
```

---

## 🔌 硬件接线（关键！）

```
ESP32                          L298N 驱动
─────────                      ──────────
GPIO 22 ──────→ PWM 信号 ───→ IN1
GPIO 23 ──────→ 方向信号 ───→ IN2
GND ───────────→ 地线 ────→ GND

L298N 输出
──────
OUT+ ──→ 电机 + 线
OUT- ──→ 电机 - 线
```

**关键点**:
- ✅ GPIO 22: PWM 速度控制（必须！）
- ✅ GPIO 23: 方向控制（必须！）
- ✅ 共地: ESP32 GND 和 L298N GND 必须连接

---

## ⚙️ WiFi 配置

在 `kait_v2.ino` 中修改：

```cpp
const char* STA_SSID     = "你的WiFi名称";     // 改这里
const char* STA_PASSWORD = "你的WiFi密码";     // 改这里
```

然后重新上传固件。

---

## 🆘 快速故障排除

| 问题 | 解决方案 |
|------|--------|
| **电机不动** | 检查 GPIO 23 接线（方向控制） |
| **WiFi 无法连接** | 检查 SSID/密码配置 |
| **OSC 命令无效** | `ping F7OWER_kait.local` 验证设备 |
| **串口连接失败** | `sudo chmod 666 /dev/ttyUSB*` |
| **脚本导入错误** | `pip install -r requirements-kait.txt` |

更多问题？查看 `KAIT_V2_GUIDE.md` 的故障排除章节。

---

## 📖 深入学习

### 5 分钟快速了解
→ 阅读 `QUICK_REFERENCE.md`

### 15 分钟完整学习
→ 阅读 `KAIT_V2_GUIDE.md`

### 1 小时深入开发
→ 研究 `kait_v2.ino` 源代码

### 理解运动效果
→ 运行 `kait_motion_visualization.py --all`

---

## 💡 3 个试用场景

### 场景 1️⃣ 温柔欢迎
```bash
seq gentle_sway      # 温柔摇晃欢迎来访者
```

### 场景 2️⃣ 高兴反应
```bash
motor 200            # 快速旋转表达高兴
# 或
seq excited_spin     # 多次快速旋转
```

### 场景 3️⃣ 警告信号
```bash
seq alert_vibrate    # 快速颤动发出警告
```

---

## 🎨 自定义编舞

在 Python 脚本中添加新序列：

```python
def my_custom_sequence(self):
    """我的自定义编舞"""
    self.set_motor_speed(150)
    time.sleep(2)
    self.set_motor_speed(-100)
    time.sleep(1)
    self.stop()

# 然后在交互模式中使用：
# kait> seq my_custom_sequence
```

详见 `KAIT_V2_GUIDE.md` 的定制章节。

---

## 🎉 完成设置检查清单

- [ ] Arduino IDE 中上传 `kait_v2.ino`
- [ ] 编辑并保存 WiFi 配置
- [ ] 硬件接线检查（GPIO 22/23 + GND）
- [ ] 安装 Python 依赖：`./install_kait_tools.sh`
- [ ] 验证 WiFi 连接：`ping F7OWER_kait.local`
- [ ] 测试远程控制：`python3 kait_osc_debug.py --seq test_all`
- [ ] ✅ 完成！开始创意应用吧！

---

## 📞 获取帮助

1. **查看文档** → `KAIT_V2_GUIDE.md` 和 `QUICK_REFERENCE.md`
2. **查看源代码** → 代码注释详细清晰
3. **查看示例** → `kait_osc_debug.py` 和 `kait_serial_debug.py` 中有大量示例
4. **查看日志** → Arduino IDE 串口监视器（115200）

---

**🌸 祝你创意无限！Let's create amazing interactions! 🌸**

---

**版本**: 2.0  
**最后更新**: 2026-03-14  
**状态**: ✅ 可用

