# Kait Node v2 - 文件索引

## 📂 项目结构

```
DATT3700/
├── esp32_firmware/esp32_kait/
│   ├── kait_v2.ino                    ⭐ 主要固件（新）
│   ├── esp32_kait.ino                 📚 原始版本（参考）
│   ├── KAIT_V2_GUIDE.md               📖 完整使用指南（新）
│   ├── QUICK_REFERENCE.md             📝 快速参考卡（新）
│   └── UPGRADE_SUMMARY.md             🎯 升级总结（新）
│
└── python_host/
    ├── kait_osc_debug.py              🌐 OSC 调试脚本（新）
    ├── kait_serial_debug.py           🔌 串口调试脚本（新）
    ├── kait_motion_visualization.py   📊 运动可视化工具（新）
    ├── install_kait_tools.sh          ⚙️ 自动安装脚本（新）
    └── requirements-kait.txt          📦 Python 依赖列表（新）
```

## 🚀 快速开始（3 步）

### 1️⃣ 安装 Python 依赖

**自动安装（推荐）:**
```bash
cd python_host
chmod +x install_kait_tools.sh
./install_kait_tools.sh
```

**手动安装:**
```bash
pip install -r python_host/requirements-kait.txt
```

### 2️⃣ 上传固件到 ESP32

- 打开 Arduino IDE
- 打开 `esp32_firmware/esp32_kait/kait_v2.ino`
- 编辑 WiFi 配置（SSID 和密码）
- 上传到 ESP32 开发板

### 3️⃣ 开始控制

**通过 OSC（远程 WiFi 控制）:**
```bash
python3 python_host/kait_osc_debug.py -i F7OWER_kait.local --interactive
```

**通过串口（本地 USB 调试）:**
```bash
python3 python_host/kait_serial_debug.py --list-ports
python3 python_host/kait_serial_debug.py -p /dev/ttyUSB0 --interactive
```

---

## 📖 文档导航

### 按用途分类

| 用途 | 推荐文档 | 所需时间 |
|------|---------|--------|
| **快速上手** | QUICK_REFERENCE.md | 5 分钟 ⚡ |
| **完整学习** | KAIT_V2_GUIDE.md | 15 分钟 📚 |
| **深入开发** | 源代码 + 注释 | 1 小时 🔧 |
| **理解运动** | motion_visualization.py | 10 分钟 📊 |
| **版本对比** | UPGRADE_SUMMARY.md | 5 分钟 📝 |

### 按角色分类

#### 🎯 **使用者**（想要控制花朵）
1. 阅读 `QUICK_REFERENCE.md`
2. 运行 `kait_osc_debug.py --interactive`
3. 完成！

#### 🔧 **开发者**（想要修改固件）
1. 阅读 `KAIT_V2_GUIDE.md`
2. 修改 `kait_v2.ino`
3. 在 Arduino IDE 中上传

#### 🎓 **学生**（想要理解工作原理）
1. 研读 `UPGRADE_SUMMARY.md`
2. 查看 `kait_motion_visualization.py`
3. 研究源代码

#### 🎨 **艺术家**（想要创作编舞）
1. 学习所有 6 种运动模式
2. 使用 `--seq` 命令组合序列
3. 编写 Python 脚本定制编舞

---

## 🎯 常用命令速查

### OSC 脚本基本命令

```bash
# 连接设备（交互模式）
python3 kait_osc_debug.py -i F7OWER_kait.local --interactive

# 快速控制
python3 kait_osc_debug.py -i F7OWER_kait.local --speed 150
python3 kait_osc_debug.py -i F7OWER_kait.local --motion 1
python3 kait_osc_debug.py -i F7OWER_kait.local --seq dance
python3 kait_osc_debug.py -i F7OWER_kait.local --stop

# 列出所有预设序列
python3 kait_osc_debug.py -i F7OWER_kait.local --interactive
kait> seqs
```

### 串口脚本基本命令

```bash
# 列出可用串口设备
python3 kait_serial_debug.py --list-ports

# 连接设备（交互模式）
python3 kait_serial_debug.py -p /dev/ttyUSB0 --interactive

# 快速控制
python3 kait_serial_debug.py -p /dev/ttyUSB0 --speed 150
python3 kait_serial_debug.py -p /dev/ttyUSB0 --motion 1
python3 kait_serial_debug.py -p /dev/ttyUSB0 --info
```

### 可视化工具命令

```bash
# 绘制所有模式
python3 kait_motion_visualization.py --all

# 绘制单个模式
python3 kait_motion_visualization.py --mode 1

# 绘制时间轴对比
python3 kait_motion_visualization.py --timeline

# 绘制信息表
python3 kait_motion_visualization.py --info

# 保存为 PNG
python3 kait_motion_visualization.py --all -o motion_guide.png
```

---

## 📋 6 种内置运动模式

### 基础模式（通过 `/motion` 调用）

| 模式号 | 名称 | 特效 | 时长 | 命令 |
|-------|------|------|------|------|
| 1 | 缓慢摇晃 | 🌿 温柔摆动 | 4s | `/motion 1` |
| 2 | 快速旋转 | ⚡ 持续旋转 | 2s | `/motion 2` |
| 3 | 脉冲抖动 | 🚨 快速颤动 | 1s | `/motion 3` |
| 4 | 加速螺旋 | 🌪️ 逐步加速 | 3s | `/motion 4` |
| 5 | 平滑制动 | ⏱️ 缓速减速 | 1.5s | `/motion 5` |
| 6 | 脉冲启动 | ⚙️ 冲击启动 | 2s | `/motion 6` |

### Python 预设序列（通过 `--seq` 调用）

| 序列名 | 描述 | 时长 | 命令 |
|--------|------|------|------|
| `gentle_sway` | 温柔摇晃 5 次 | 10s | `seq gentle_sway` |
| `excited_spin` | 快速旋转 3 次 | 8s | `seq excited_spin` |
| `alert_vibrate` | 告急颤动 2 轮 | 3s | `seq alert_vibrate` |
| `smooth_wake` | 逐步加速再减速 | 8s | `seq smooth_wake` |
| `dance` | 舞蹈节奏 2 轮 | 6s | `seq dance` |
| `test_all` | 测试所有 6 模式 | 21s | `seq test_all` |

---

## 🔌 硬件接线

```
ESP32 引脚         功能              L298N 驱动板
───────────────────────────────────────────────
GPIO 22  ────────→ PWM 信号      ──→ IN1
GPIO 23  ────────→ 方向控制      ──→ IN2
GND      ────────→ 地线         ──→ GND

L298N 输出
───────
OUT+  ──→ 电机 + （红线）
OUT-  ──→ 电机 - （黑线）
```

---

## ⚙️ 配置参数

### 在 `kait_v2.ino` 中编辑

```cpp
// WiFi 配置
const char* STA_SSID     = "F7OWER";        // 你的 WiFi 名称
const char* STA_PASSWORD = "12345678";      // WiFi 密码
const char* MDNS_NAME = "F7OWER_kait";      // mDNS 设备名

// 电机配置
const int MOTOR_KICK_START_POWER = 255;     // 启动冲击功率（0-255）
const int MOTOR_KICK_START_DELAY = 30;      // 启动冲击延时（毫秒）

// OSC 配置
const int OSC_PORT = 8888;                  // OSC 监听端口
```

---

## 🐛 故障排除

### 常见问题及解决方案

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 串口连接失败 | 权限不足 | `sudo chmod 666 /dev/ttyUSB*` |
| WiFi 无法连接 | SSID/密码错 | 检查 `kait_v2.ino` 中的配置 |
| OSC 命令无效 | 设备 IP 错误 | `ping F7OWER_kait.local` 验证 |
| 电机不动 | GPIO 23 未接 | 检查方向控制引脚连接 |
| 脚本导入错误 | 依赖未安装 | `pip install -r requirements-kait.txt` |

### 获取帮助

1. 查看完整日志：打开串口监视器（115200）
2. 查看硬件连接：对照 QUICK_REFERENCE.md 接线图
3. 查看使用方法：运行 `python3 script.py --help`
4. 查看详细文档：阅读 KAIT_V2_GUIDE.md

---

## 📊 文件大小和内容

| 文件 | 大小 | 行数 | 用途 |
|------|------|------|------|
| kait_v2.ino | 16 KB | 450 | ESP32 固件 |
| kait_osc_debug.py | 18 KB | 320 | OSC 调试工具 |
| kait_serial_debug.py | 20 KB | 360 | 串口调试工具 |
| kait_motion_visualization.py | 22 KB | 380 | 可视化工具 |
| KAIT_V2_GUIDE.md | 18 KB | 350 | 完整指南 |
| QUICK_REFERENCE.md | 12 KB | 250 | 快速参考 |
| UPGRADE_SUMMARY.md | 15 KB | 300 | 升级总结 |

---

## 🎓 学习路线

### 初级（1 小时）
✅ 安装依赖  
✅ 上传固件  
✅ 运行 `--seq test_all`  
✅ 理解 6 种运动模式  

### 中级（3 小时）
✅ 编写自定义 Python 序列  
✅ 理解 OSC 协议  
✅ 修改运动模式参数  
✅ 创建编舞脚本  

### 高级（1 天）
✅ 修改 Arduino 固件  
✅ 添加新运动模式  
✅ 多设备网络控制  
✅ 系统集成开发  

---

## 💡 提示和技巧

### 🎯 性能优化

- 使用本地 IP 而不是 mDNS 以获得更低延迟
- 批量发送 OSC 消息而不是逐个发送
- 将长序列存储在 Python 脚本中而不是 Arduino

### 🎨 创意应用

- 结合传感器创建交互式花朵
- 多个 Kait 节点同步运动（网络编舞）
- 使用 Python 脚本驱动音乐同步
- 与视觉效果配合创建装置艺术

### 📚 扩展资源

- Arduino 官方文档：https://www.arduino.cc/
- ESP32 文档：https://docs.espressif.com/
- OSC 协议：http://opensoundcontrol.org/
- Python OSC 库：https://github.com/attwad/python-osc

---

## 📞 获取支持

### 自助诊断

1. **检查连接**: `ping F7OWER_kait.local`
2. **查看日志**: 打开 Arduino IDE 串口监视器
3. **测试模式**: `python3 kait_osc_debug.py --seq test_all`
4. **查看文档**: 阅读 KAIT_V2_GUIDE.md 或 QUICK_REFERENCE.md

### 社区资源

- GitHub Issues（如果有的话）
- Arduino 论坛
- ESP32 社区

---

## ✨ 版本信息

- **当前版本**: 2.0
- **发布日期**: 2026-03-14
- **Python 最低版本**: 3.6
- **Arduino IDE 最低版本**: 1.8.0
- **ESP32 核心版本**: 2.0.0+

---

## 📄 许可证

MIT License - 可自由使用、修改和分发

---

## 🙏 致谢

感谢所有贡献者和用户的反馈！

---

**🌸 Ready to create amazing interactive art with Kait! 🌸**

最后更新: 2026-03-14

