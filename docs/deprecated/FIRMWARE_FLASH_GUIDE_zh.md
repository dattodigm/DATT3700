# ESP32 多文件固件烧录指南

> **目标读者**：Arduino / ESP32 开发新手队友  
> **最后更新**：2026-03-04

---

## 目录

1. [准备工作](#1-准备工作)
2. [安装 Arduino IDE](#2-安装-arduino-ide)
3. [配置 ESP32 开发板支持](#3-配置-esp32-开发板支持)
4. [安装所需库](#4-安装所需库)
5. [理解 Arduino 多文件项目](#5-理解-arduino-多文件项目)
6. [打开项目](#6-打开项目)
7. [项目文件结构](#7-项目文件结构)
8. [配置你的节点](#8-配置你的节点)
9. [上传（烧录）固件](#9-上传烧录固件)
10. [验证上传结果](#10-验证上传结果)
11. [常见问题排查](#11-常见问题排查)

---

## 1. 准备工作

你需要：

- **一台电脑**（Windows / macOS / Linux 均可）
- **一根 USB 数据线**（Micro-USB 或 USB-C，取决于你的 ESP32 开发板型号）
- **一块 ESP32 开发板**（例如 ESP32-DevKitC、NodeMCU-32S）

---

## 2. 安装 Arduino IDE

1. 前往 [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)
2. 下载适用于你操作系统的 **Arduino IDE 2.x**（推荐最新版）
3. 安装并打开 IDE

---

## 3. 配置 ESP32 开发板支持

Arduino IDE 默认不支持 ESP32，需要手动添加：

1. 打开 Arduino IDE
2. 前往 **文件 → 首选项**（macOS: **Arduino IDE → 设置**）
3. 在 **"附加开发板管理器网址"** 中粘贴以下链接：
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. 点击 **确定**
5. 前往 **工具 → 开发板 → 开发板管理器**
6. 搜索 **"esp32"**
7. 安装 **"esp32 by Espressif Systems"**（选择最新版本）
8. 安装完成后，前往 **工具 → 开发板**，选择 **"ESP32 Dev Module"**

---

## 4. 安装所需库

我们的固件使用了一些外部库，需要通过库管理器安装：

1. 前往 **项目 → 加载库 → 管理库**（IDE 2.x 中也可点击左侧栏的库图标）
2. 搜索并安装以下库：

| 库名称 | 作者 | 用途 |
|---|---|---|
| **OSC** | Adrian Freed, Yotam Mann | OSC 协议，用于电机/LED 控制 |
| **ESPAsyncWebServer** | Me-No-Dev (lacamera) | 异步 HTTP 服务器，用于 `/config` 端点 |
| **AsyncTCP** | Me-No-Dev (dvarrel) | ESPAsyncWebServer 的依赖库 |

> **注意**：`WiFi.h`、`ESPmDNS.h` 和 `WiFiUdp.h` 是 ESP32 开发板包的 **内置库**，无需单独安装。

### 备选方案：通过 .zip 文件安装

如果在库管理器中找不到某个库：
1. 从 GitHub 下载 `.zip` 文件
2. 前往 **项目 → 加载库 → 添加 .ZIP 库**
3. 选择下载的 `.zip` 文件

---

## 5. 理解 Arduino 多文件项目

### Arduino 如何处理多个文件

Arduino 使用 **基于文件夹** 的项目结构：

- 主 `.ino` 文件的名称 **必须与其所在文件夹同名**
  - 正确示例：`eps32_sylvie/esp32_sylvie.ino` ✅
  - 错误示例：`my_project/sketch.ino` ❌（名称不匹配）
- 同一文件夹内的所有 `.h`（头文件）和 `.cpp`（源文件）会 **自动被编译**
- 你 **不需要** 手动将文件添加到构建系统

### 我们的项目文件

```
eps32_sylvie/                    ← 项目文件夹名
├── esp32_sylvie.ino             ← 主程序（必须与文件夹同名）
├── config.h                     ← 配置文件（编辑这个！）
├── MeshManager.h             ← 网络模块头文件
└── MeshManager.cpp           ← 网络模块实现文件
```

### 工作原理

1. `esp32_sylvie.ino` 通过 `#include` 引入 `config.h` 和 `MeshManager.h`
2. Arduino IDE 会自动编译同一文件夹中的 `MeshManager.cpp`
3. `config.h` 定义了所有可配置的值（WiFi 名称、密码、模式等）

---

## 6. 打开项目

1. 克隆或下载本仓库
2. 在 Arduino IDE 中，前往 **文件 → 打开**
3. 导航到 `esp32_firmware/eps32_sylvie/` 文件夹
4. 选择 `esp32_sylvie.ino`
5. IDE 顶部会以 **标签页** 的形式显示所有文件（`.ino`、`.h`、`.cpp`）

> **重要**：不要将单个文件移出该文件夹。所有文件必须放在一起。

---

## 7. 项目文件结构

| 文件 | 用途 | 需要编辑吗？ |
|---|---|---|
| `esp32_sylvie.ino` | 主程序，包含 `setup()` 和 `loop()` | 仅修改电机/LED 逻辑时需要 |
| `config.h` | 所有配置设置 | **需要** — 设置你的 WiFi、节点类型等 |
| `MeshManager.h` | 网络类声明 | 不需要（除非添加功能） |
| `MeshManager.cpp` | 网络类实现 | 不需要（除非添加功能） |

---

## 8. 配置你的节点

在上传之前，编辑 `config.h` 以匹配你的设置：

### 选择网络模式

```cpp
// 作为 WiFi 热点使用（默认，推荐用于测试）：
#define NETWORK_MODE NETWORK_MODE_AP

// 连接到现有的 WiFi 路由器：
#define NETWORK_MODE NETWORK_MODE_STA
```

### 设置 WiFi 凭据

**热点模式（AP）**（ESP32 创建自己的 WiFi 网络）：
```cpp
#define AP_SSID     "ESP32_Sylvie"    // WiFi 热点名称
#define AP_PASSWORD "12345678"         // 密码（至少8个字符）
```

**客户端模式（STA）**（ESP32 连接到你的路由器）：
```cpp
#define STA_SSID     "你的WiFi名称"       // 路由器的 WiFi 名称
#define STA_PASSWORD "你的WiFi密码"        // 路由器的 WiFi 密码
```

### 设置节点身份

```cpp
#define NODE_TYPE "sylvie"      // 节点类型: "sylvie", "sue", "kait", "face_track"
#define NODE_ID   "sylvie_1"    // 此 ESP32 的唯一名称
```

---

## 9. 上传（烧录）固件

### 详细步骤

1. 用 USB 线将 ESP32 **连接** 到电脑
2. 在 Arduino IDE 中，前往 **工具** 并设置：
   - **开发板**："ESP32 Dev Module"
   - **端口**：选择插入 ESP32 后出现的端口
     - Windows: `COM3`、`COM4` 等
     - macOS: `/dev/cu.usbserial-xxxx` 或 `/dev/cu.SLAB_USBtoUART`
     - Linux: `/dev/ttyUSB0` 或 `/dev/ttyACM0`
   - **上传速度**：115200（默认即可）
3. 点击 **上传按钮**（→ 箭头图标）或按 `Ctrl+U` / `Cmd+U`
4. 等待编译和上传完成
5. 输出面板应显示 "上传完成"

### 上传过程中发生了什么

1. **编译**：IDE 将所有文件（`.ino`、`.cpp`、`.h`）一起编译
2. **链接**：将编译后的代码与 ESP32 库合并
3. **烧录**：将二进制文件写入 ESP32 的闪存
4. **重启**：ESP32 自动使用新固件重新启动

---

## 10. 验证上传结果

1. 打开 **工具 → 串口监视器**（或点击放大镜图标）
2. 将波特率设置为 **115200**（右下角的下拉菜单）
3. 按 ESP32 上的 **RST（重置）** 按钮
4. 你应该看到如下输出：

```
[MeshManager] Starting AP mode... / 正在启动热点模式...
[MeshManager] AP started. SSID: ESP32_Sylvie
[MeshManager] AP IP address / 热点 IP 地址: 192.168.4.1
[MeshManager] mDNS started: sylvie_1.local
[MeshManager] Web server started on port 80
```

### 测试网络功能

**热点模式（AP）下：**
1. 在手机或笔记本上搜索 WiFi 网络 "ESP32_Sylvie"
2. 使用密码 "12345678" 连接
3. 打开浏览器，访问 `http://192.168.4.1/config`
4. 你应该能看到描述节点信息的 JSON 数据

**客户端模式（STA）下：**
1. 串口监视器会显示路由器分配的 IP 地址
2. 在同一网络的电脑上，用浏览器访问 `http://<IP地址>/config`

---

## 11. 常见问题排查

### "找不到端口" / 没有 COM 端口出现

- **安装 USB 驱动**：部分 ESP32 开发板使用 CH340 或 CP2102 芯片
  - CH340 驱动：[https://www.wch.cn/downloads/CH341SER_ZIP.html](https://www.wch.cn/downloads/CH341SER_ZIP.html)
  - CP2102 驱动：[https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- 尝试换一根 USB 线（有些线只能充电，不能传输数据）
- 尝试换一个 USB 接口

### "编译错误" / 构建失败

- 确保 **所有文件** 都在同一个文件夹内
- 确保文件夹名称与 `.ino` 文件名匹配
- 检查所有需要的库是否已安装（参见 [第4节](#4-安装所需库)）
- 检查 ESP32 开发板支持是否已安装（参见 [第3节](#3-配置-esp32-开发板支持)）

### "上传失败" / 无法烧录

- 点击上传时，按住 ESP32 上的 **BOOT** 按钮
- 当输出窗口显示 "Connecting..." 时松开 BOOT 按钮
- 尝试降低上传速度：**工具 → 上传速度 → 115200**

### WiFi 不工作

- 热点模式：检查密码是否至少8个字符
- 客户端模式：仔细检查 `config.h` 中路由器的 SSID 和密码是否正确
- 打开串口监视器查看错误信息

### "找不到 ESPAsyncWebServer"

- 这个库可能不在默认的库管理器中
- 手动从 GitHub 下载：[https://github.com/me-no-dev/ESPAsyncWebServer](https://github.com/me-no-dev/ESPAsyncWebServer)
- 同时下载 AsyncTCP：[https://github.com/me-no-dev/AsyncTCP](https://github.com/me-no-dev/AsyncTCP)
- 通过 **项目 → 加载库 → 添加 .ZIP 库** 安装

---

## 快速参考卡

| 操作 | 方法 |
|---|---|
| 打开项目 | 文件 → 打开 → 选择 `esp32_sylvie.ino` |
| 修改 WiFi 设置 | 编辑 `config.h` |
| 上传到 ESP32 | 点击 → （上传）按钮 |
| 查看输出 | 工具 → 串口监视器（波特率 115200） |
| 测试网络 | 连接 WiFi，用浏览器访问 IP 地址 |
| 查找 IP 地址 | 重置后查看串口监视器 |
