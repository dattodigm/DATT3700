/**
 * sylvie_v2.ino - Sylvie Cluster Flower Main Sketch
 *                   Sylvie 集群花朵主程序
 *
 * Integrates MeshManager + FlowerNode + SylvieNode into a clean
 * Arduino entry point. This replaces the original monolithic
 * esp32_sylvie.ino with an object-oriented architecture.
 *
 * 将 MeshManager + FlowerNode + SylvieNode 集成为简洁的
 * Arduino 入口。以面向对象架构替代原始的单文件 esp32_sylvie.ino。
 *
 * Architecture / 架构:
 *   config.h          → All configurable parameters / 所有可配置参数
 *   MeshManager       → WiFi AP/STA + mDNS + HTTP / WiFi 网络管理
 *   FlowerNode        → Abstract base class / 抽象基类
 *   SylvieNode        → Concrete hardware driver / 具体硬件驱动
 *
 * Constraints / 约束:
 *   ⚠️ NO delay() in loop() — millis() only
 *   ⚠️ No String concatenation in loops
 *   ⚠️ No malloc/new at runtime
 */

#include "config.h"
#include "MeshManager.h"
#include "SylvieNode.h"

// ============================================================
// Global Instances / 全局实例
// ============================================================

MeshManager    network;   // WiFi + mDNS + Web Server / WiFi 网络管理器
SylvieNode     sylvie;    // Flower hardware driver / 花朵硬件驱动

// ============================================================
// setup() - One-time initialization / 一次性初始化
// ============================================================
void setup() {
    Serial.begin(115200);

    Serial.println("\n========================================");
    Serial.println("  DATT3700 Flower Node - Sylvie");
    Serial.println("  Interactive Flower Installation");
    Serial.println("  互动花朵装置 - Sylvie 节点");
    Serial.println("========================================\n");

    // 1. Initialize network (WiFi + mDNS + Web Server)
    //    初始化网络（WiFi + mDNS + Web 服务器）
    Serial.println("[Main] Initializing network... / 正在初始化网络...");
    if (!network.begin()) {
        Serial.println("[Main] ERROR: Network init failed! / 网络初始化失败！");
    }

    // 2. Initialize hardware (motors + LEDs)
    //    初始化硬件（电机 + LED）
    Serial.println("[Main] Initializing hardware... / 正在初始化硬件...");
    if (!sylvie.begin()) {
        Serial.println("[Main] ERROR: Hardware init failed! / 硬件初始化失败！");
    }

    // 3. Start OSC listener (after WiFi is up)
    //    启动 OSC 监听器（WiFi 就绪后）
    sylvie.beginOSC();

    Serial.println("[Main] System ready! / 系统就绪！\n");
    Serial.printf("[Main] Node ID: %s  Type: %s  OSC Port: %d\n",
                  sylvie.getNodeId(), sylvie.getNodeType(), sylvie.getOSCPort());
    Serial.printf("[Main] IP: %s\n", network.getIP().toString().c_str());
    Serial.println("[Main] Type 'help' in Serial for debug commands.");
    Serial.println("[Main] 在串口中输入 'help' 查看调试命令。\n");
}

// ============================================================
// loop() - Non-blocking main loop / 非阻塞主循环
// ⚠️ NO delay() allowed here
// ============================================================
void loop() {
    // 1. Network maintenance (STA reconnection, etc.)
    //    网络维护（STA 重连等）
    network.update();

    // 2. Hardware update (OSC receive + auto-mode + serial debug)
    //    硬件更新（OSC 接收 + 自动模式 + 串口调试）
    sylvie.update();
}
