# DATT 3700 协作项目文档 · Collaborative Project Documentation

**课程 Course:** DATT 3700 — Collaborative Project Development  
**主题 Theme:** 机器代理与具身 AI · Machine Agency & Embodied AI  

本文档为**中英文对照**说明，概述装置概念、硬件分工、软件架构、感知与控制策略，以及已完成工作与后续计划。

This document is a **bilingual (Chinese / English)** overview of the installation concept, hardware roles, software architecture, perception and control strategy, deliverables, and future work.

---

## 1. 项目概述 · Project overview

**中文**  
本小组作品是一件 **AI 驱动的花朵艺术装置**：多台 ESP32 控制不同形态的“花朵”，根据摄像头捕捉到的人类行为做出类似伙伴的反应，从而**脱离传统聊天式语言模型与纯按钮 UI**，以具身、空间化的方式与“AI 代理”互动。

**English**  
Our team built an **AI-driven floral art installation**: multiple ESP32 boards animate distinct “flower” forms in response to camera-captured human behavior, enabling **embodied, spatial interaction** that steps beyond conventional chat-style LLM interfaces and purely button-driven UIs.

---

## 2. 装置构成与分工 · Installation layout & team roles

**中文**  
装置共 **三种花朵形态、五个 ESP32 节点**（含追踪与显示子系统），分工概览如下：

| 成员 / 模块 | 硬件与形态 | 说明 |
|-------------|------------|------|
| **Sylvie（Sylvia）** | DC 马达驱动的曼陀罗/彼岸花状开合结构；**四朵花**置于 **8 个舵机（4 组 pan/tilt）** 构成的 XY 机械臂追踪机构上；中央 **GC9D01 TFT** 播放眼睛动画（基于 TFT_eSPI 与 **Animated_Eye12** 一类精灵帧动画思路，局部 Canvas 重绘以降低撕裂与内存压力） | 集群视觉焦点 + 追踪承载 |
| **Kait** | DC 马达为主、**旋转**表现突出的条状花朵 | 强调旋转与动态节奏 |
| **Sue** | 伺服拉动传动轴实现**荷花状开合**；**GC0A01** 小屏显示 | 开合语义与副屏反馈 |

**English**  
The installation comprises **three flower archetypes across five ESP32 nodes** (including tracking and display subsystems):

| Contributor / module | Hardware & form | Notes |
|----------------------|-----------------|-------|
| **Sylvie (Sylvia)** | DC-motor “mandala / otherworldly flower” opening–closing; **four blooms** on **eight servos (four pan/tilt pairs)** for XY tracking; central **GC9D01 TFT** eye animation (TFT_eSPI + **Animated_Eye12**-style sprite frames with **partial canvas redraw** to mitigate tearing and RAM limits) | Cluster focal point + tracking platform |
| **Kait** | DC-motor, **rotation-forward** bar-shaped flower | Emphasizes spin and rhythmic motion |
| **Sue** | Servo-driven linkage for **lotus-like** bloom; **GC0A01** display | Bloom semantics + secondary screen |

---

## 3. 软件与重构工作 · Software stack & refactoring

**中文**  
原始固件多为**阻塞式 `delay`、缺少封装与统一接口**，显示部分也存在 **GFX 全屏绘制导致撕裂**、**全屏 Canvas 内存不足**等问题。项目中的**统一网络与控制层**主要包括：

- **`esp32_firmware_refactored/`**  
  - **WiFi**（含 AP/STA、mDNS 等，依节点而定）、**OSC** 控制接口、**非阻塞主循环**（`millis()` 调度）、串口调试命令与**预设动作**。  
  - **Sylvie 节点**：`MeshManager`、`FlowerNode` 抽象、`SylvieNode` 实现，主从结构（如 `sylvie_main` / `sylvie_client`）与网关式协同。  
  - **人脸追踪节点**：舵机追踪与坐标消费（与 Python 侧发布器配合）。  
  - **Kait / Sue**：对应 v2 固件与 OSC/串口调试脚本（如 `kait_v2_en` 目录内文档与工具）。

- **`python_host/`**（Flask **Web 控制面板**）  
  - mDNS / 网关回退扫描、设备发现 API、按节点类型渲染控制界面（`sylvie` / `sue` / `kait` / `face_track` / `eye_anime` 等）。  
  - **OSC 原始控制台**、**动作序列录制**（`data/sequences/<label>`）、人脸追踪坐标发布（**OSC / Wi‑Fi 或 USB 串口**可切换）。  
  - 可选 **ViT + DeepFace** 表情管线（`requirements-ml.txt`、`bootstrap_ml_models` 本地模型引导）。

**English**  
Early firmware relied heavily on **blocking `delay` calls** with **little modularization or shared interfaces**; displays suffered from **full-screen GFX tearing** and **full-frame canvas OOM** issues. The **integrated networking and control layer** includes:

- **`esp32_firmware_refactored/`**  
  - **WiFi** (AP/STA, mDNS where applicable), **OSC** control, **non-blocking `loop()`** (`millis()`-based scheduling), serial debug commands, and **preset motions**.  
  - **Sylvie**: `MeshManager`, abstract `FlowerNode`, concrete `SylvieNode`, main/client sketches for gateway-style coordination.  
  - **Face tracking**: servo tracking driven by host-published coordinates.  
  - **Kait / Sue**: v2 firmware plus OSC/serial tooling (see `kait_v2_en` docs).

- **`python_host/`** (Flask **web control panel**)  
  - mDNS + gateway fallback discovery, device APIs, **node-type-aware** UI.  
  - Raw OSC console, **motion sequence recorder**, face-tracking publisher (**OSC/Wi‑Fi or USB serial**).  
  - Optional **ViT + DeepFace** stack (`requirements-ml.txt`, `bootstrap_ml_models`).

**设备类型注册示例（节选）· Excerpt from device registry (`ui/device_registry.json`)**  

节点类型包括：`sylvie`（双 DC、RGB、预设）、`kait`（DC + 模式）、`sue`（舵机花瓣 + TFT 眼）、`face_track`（8 舵机）、`eye_anime`（Animated_Eye12 + OSC 追踪与帧动画）等。

Node kinds include: `sylvie`, `kait`, `sue`, `face_track`, `eye_anime`, etc., each with distinct OSC/UI affordances.

---

## 4. 机器学习与行为决策的演进 · ML & behavior design evolution

**中文**  

1. **初期设想**：用摄像头视频 + 花朵控制序列训练**世界模型**——受限于算力、优质数据量、物理约束（缠线、碰撞桌面等），难以在课程周期内闭环。  
2. **快慢脑设想**：**快脑**做人脸检测/追踪；**慢脑**用 **VLM** 对采样帧序列做高层决策——训练与推理对多卡工作站依赖较强，在仅有笔记本的条件下不现实。  
3. **期末折中方案**：**ViT / DeepFace 人脸表情识别** → **花朵“情绪”分池化（积分/衰减）** → **映射到离散花态（如 BLOOM / ALERT / SOOTHE / REST）并路由 OSC 指令**（见 `vision/emotion_reactor.py`），形成可演示的**动态响应模式**。

**English**  

1. **Early idea**: train a **world model** from video + motor command logs — blocked by compute, scarce clean data, and physical hazards (cable tangling, collisions).  
2. **Fast/slow brain**: fast face track + slow **VLM** over frame sequences — prohibitive on a laptop without a multi-GPU workstation.  
3. **Showcase compromise**: **ViT / DeepFace expression cues** → **pooled, decaying “flower emotion” scores** → **discrete states (e.g. BLOOM, ALERT, SOOTHE, REST) mapped to OSC** (`vision/emotion_reactor.py`) for a **stable demo loop**.

---

## 5. 外部资源与显示示例 · External resources & eye example

**中文**  
- **`lib_TFT_eSPI_GC9D01`**（及示例 **`examples/5.Animated_Eye12`**）：GC9D01 眼睛动画资源与工具链（如 RGB565 头文件生成、多眼风格数据）。与 Sylvie 中央屏的**精灵局部重绘**策略一致，用于在内存受限的 MCU 上保持流畅观感。

**English**  
- **`lib_TFT_eSPI_GC9D01`**, especially **`examples/5.Animated_Eye12`**: assets and tooling for GC9D01 eye animation (RGB565 headers, multiple eye themes). Aligns with **partial sprite redraw** on resource-constrained MCUs.

---

## 6. 已知限制与后续计划 · Limitations & roadmap

**中文**  
因需承担**跨节点固件整合、显示与网络层修复**，以下方向在期末前**仅部分实现或留作长期计划**：

| 方向 | 说明 |
|------|------|
| **姿态 / 手势** | MediaPipe 等人体关键点，驱动旋转、开合、舵机位姿等语义动作 |
| **眼动与群体行为** | 注视时长统计、“嫉妒/争艳”式多朵花协同动作 |
| **控制面板下一代** | 已用 v0 等工具搭建 **Next.js** 现代化前端，**尚未与 Python 后端路由全面接通** |
| **固件抽象** | 更统一的花朵节点基类、配置与 OTA/版本策略 |
| **网络** | 更稳定的 **热点转发 / Mesh** 与仓库目录整理 |
| **双脑 / VLM** | 图片序列拼图、视频反馈、自主数据收集与离线训练闭环 |

**English**  
Firmware integration, display fixes, and networking consumed most bandwidth; the following remain **partially implemented or roadmap items**:

| Track | Description |
|-------|-------------|
| **Pose / gestures** | MediaPipe-style keypoints → spin, bloom, servo poses |
| **Gaze & swarm affect** | dwell-time jealousy/competition choreography across blooms |
| **Next-gen panel** | **Next.js** UI drafted; **not yet wired to all Python routes** |
| **Firmware abstraction** | Stronger shared node base classes and release hygiene |
| **Networking** | Robust **AP relay / mesh** and repo hygiene |
| **Dual-brain / VLM** | tiled frame narratives, video feedback, self-supervised data loops |

---

## 7. 快速运行参考 · Quick run reference

**中文**  
```bash
python -m pip install -r python_host/requirements.txt
python -m python_host.main --port 15000
```  
浏览器访问 `http://127.0.0.1:15000`。机器学习资源见 `python_host/README.md` 中 **ViT + DeepFace** 引导命令。

**English**  
```bash
python -m pip install -r python_host/requirements.txt
python -m python_host.main --port 15000
```  
Open `http://127.0.0.1:15000`. For ML assets, follow the **ViT + DeepFace** bootstrap section in `python_host/README.md`.

---

## 8. 文档与仓库路径 · Document & repo paths

| 路径 Path | 内容 Contents |
|-----------|----------------|
| `DATT3700/python_host/` | Flask 主机、感知、OSC、Web UI |
| `DATT3700/esp32_firmware_refactored/` | 重构后 ESP32 工程（Sylvie / Kait / Sue / face_tracking 等） |
| `lib_TFT_eSPI_GC9D01/examples/5.Animated_Eye12/` | GC9D01 眼睛动画示例与工具 |

---

*文档版本 Document version: 2026-03-30 — 与课程小组陈述一致时可随答辩更新。*  
*Update this file if demo URLs, ports, or node names change.*
