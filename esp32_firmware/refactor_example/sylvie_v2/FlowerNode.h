/**
 * FlowerNode.h - Abstract Base Class for All Flower Nodes / 花朵节点抽象基类
 *
 * Provides a unified interface for all ESP32 hardware nodes in the
 * DATT3700 interactive flower installation.
 *
 * 为 DATT3700 互动花朵装置中的所有 ESP32 硬件节点提供统一接口。
 *
 * Design Constraints / 设计约束:
 *   1. Pure virtual functions force subclass implementation / 纯虚函数强制子类实现
 *   2. NO delay() — all timing via millis() / 禁止 delay()，所有计时使用 millis()
 *   3. Unified OSC command parsing interface / 统一的 OSC 命令解析接口
 *
 * Usage / 使用方法:
 *   class SylvieNode : public FlowerNode {
 *       // implement all pure virtual functions
 *   };
 */

#ifndef FLOWER_NODE_H
#define FLOWER_NODE_H

#include <Arduino.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>

/**
 * FlowerNode - Abstract base class / 抽象基类
 *
 * All hardware nodes (Sylvie, Sue, Kait, FaceTracking) must inherit
 * from this class and implement every pure virtual function.
 *
 * 所有硬件节点（Sylvie、Sue、Kait、FaceTracking）必须继承此类
 * 并实现每个纯虚函数。
 */
class FlowerNode {
public:
    // ============================================================
    // Constructor & Destructor / 构造函数与析构函数
    // ============================================================

    /**
     * Constructor / 构造函数
     * @param nodeId   Unique identifier (e.g. "sylvie_1") / 唯一标识符
     * @param nodeType Node type (e.g. "sylvie") / 节点类型
     * @param oscPort  UDP port for OSC reception / OSC 接收的 UDP 端口
     */
    FlowerNode(const char* nodeId, const char* nodeType, uint16_t oscPort)
        : _oscPort(oscPort)
    {
        strncpy(_nodeId, nodeId, sizeof(_nodeId) - 1);
        _nodeId[sizeof(_nodeId) - 1] = '\0';
        strncpy(_nodeType, nodeType, sizeof(_nodeType) - 1);
        _nodeType[sizeof(_nodeType) - 1] = '\0';
    }

    /**
     * Virtual destructor / 虚析构函数
     */
    virtual ~FlowerNode() {}

    // ============================================================
    // Core Lifecycle — Pure Virtual / 核心生命周期 — 纯虚函数
    // ============================================================

    /**
     * Initialize hardware peripherals (pins, servos, motors, etc.).
     * Called once in Arduino setup().
     * ⚠️ Must NOT call delay().
     *
     * 初始化硬件外设（引脚、舵机、电机等）。
     * 在 Arduino setup() 中调用一次。
     * ⚠️ 禁止调用 delay()。
     *
     * @return true if initialization succeeded / 初始化成功返回 true
     */
    virtual bool begin() = 0;

    /**
     * Non-blocking periodic update. Called every iteration of loop().
     * Must use millis() for all timing — NO delay().
     *
     * 非阻塞周期性更新，在 loop() 的每次迭代中调用。
     * 必须使用 millis() 计时 — 禁止 delay()。
     */
    virtual void update() = 0;

    /**
     * Handle an incoming OSC message.
     * Called when the base class receives and validates an OSC packet.
     *
     * 处理收到的 OSC 消息。
     * 当基类接收并验证 OSC 数据包后调用。
     *
     * @param msg       The parsed OSC message / 已解析的 OSC 消息
     * @param address   The OSC address pattern (e.g. "/motor1") / OSC 地址模式
     */
    virtual void onOSCMessage(OSCMessage &msg, const char* address) = 0;

    /**
     * Emergency stop — immediately halt all actuators.
     * 紧急停止 — 立即停止所有执行器。
     */
    virtual void stopAll() = 0;

    // ============================================================
    // Shared Implementation / 共享实现
    // ============================================================

    /**
     * Start the UDP listener for OSC messages.
     * Call after WiFi is connected.
     *
     * 启动用于接收 OSC 消息的 UDP 监听器。
     * 在 WiFi 连接后调用。
     *
     * @return true if UDP started successfully / UDP 启动成功返回 true
     */
    bool beginOSC() {
        _udp.begin(_oscPort);
        Serial.printf("[%s] OSC listening on port %d\n", _nodeId, _oscPort);
        return true;
    }

    /**
     * Poll for incoming OSC packets and dispatch to onOSCMessage().
     * Call this inside update() or loop(). Non-blocking.
     *
     * 轮询传入的 OSC 数据包并分发给 onOSCMessage()。
     * 在 update() 或 loop() 中调用。非阻塞。
     */
    void processOSC() {
        int packetSize = _udp.parsePacket();
        if (packetSize <= 0) return;

        OSCMessage msg;
        while (packetSize--) {
            msg.fill(_udp.read());
        }

        if (msg.hasError()) {
            Serial.printf("[%s] OSC message error\n", _nodeId);
            return;
        }

        // Extract address for dispatch (offset 0 = full address from start)
        // 提取地址用于分发（偏移 0 = 从头开始的完整地址）
        char address[64];
        msg.getAddress(address, 0, sizeof(address));
        onOSCMessage(msg, address);
    }

    /**
     * Get this node's unique identifier.
     * 获取此节点的唯一标识符。
     */
    const char* getNodeId() const { return _nodeId; }

    /**
     * Get this node's type string.
     * 获取此节点的类型字符串。
     */
    const char* getNodeType() const { return _nodeType; }

    /**
     * Get the OSC port.
     * 获取 OSC 端口。
     */
    uint16_t getOSCPort() const { return _oscPort; }

protected:
    // ============================================================
    // Timing Utility / 计时工具
    // ============================================================

    /**
     * Non-blocking interval check using millis().
     * Returns true if at least intervalMs has elapsed since lastMs,
     * and updates lastMs to the current time.
     *
     * 基于 millis() 的非阻塞间隔检查。
     * 如果自 lastMs 以来已经过至少 intervalMs 毫秒，返回 true
     * 并将 lastMs 更新为当前时间。
     *
     * @param lastMs      Reference to the timestamp to check / 要检查的时间戳引用
     * @param intervalMs  Desired interval in milliseconds / 期望间隔（毫秒）
     * @return true if interval has elapsed / 间隔已过返回 true
     */
    bool intervalElapsed(unsigned long &lastMs, unsigned long intervalMs) {
        unsigned long now = millis();
        if (now - lastMs >= intervalMs) {
            lastMs = now;
            return true;
        }
        return false;
    }

    // ============================================================
    // Member Variables / 成员变量
    // ============================================================

    char          _nodeId[32];    // Unique node identifier / 唯一节点标识符
    char          _nodeType[16];  // Node type string / 节点类型字符串
    uint16_t      _oscPort;       // UDP port for OSC / OSC 的 UDP 端口
    WiFiUDP       _udp;           // UDP instance for OSC / 用于 OSC 的 UDP 实例
};

#endif // FLOWER_NODE_H
