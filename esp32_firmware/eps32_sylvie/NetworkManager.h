/**
 * NetworkManager.h - Network Management Module / 网络管理模块
 * 
 * Encapsulates WiFi (AP/STA), mDNS discovery, and HTTP config server
 * into a reusable class for all ESP32 flower nodes.
 * 
 * 将 WiFi（AP/STA）、mDNS 发现和 HTTP 配置服务器
 * 封装为可复用的类，适用于所有 ESP32 花朵节点。
 * 
 * Dependencies / 依赖库:
 *   - WiFi.h          (ESP32 built-in / ESP32 内置)
 *   - ESPmDNS.h       (ESP32 built-in / ESP32 内置)
 *   - ESPAsyncWebServer.h  (install via Library Manager / 通过库管理器安装)
 * 
 * Usage / 使用方法:
 *   #include "config.h"
 *   #include "NetworkManager.h"
 *   NetworkManager network;
 *   void setup() { network.begin(); }
 *   void loop()  { network.update(); }
 */

#ifndef NETWORK_MANAGER_H
#define NETWORK_MANAGER_H

#include <WiFi.h>
#include <ESPmDNS.h>
#include <ESPAsyncWebServer.h>
#include "config.h"

/**
 * NetworkManager class / 网络管理器类
 * 
 * Handles WiFi connection, mDNS service registration,
 * and a minimal configuration web server.
 * 
 * 负责 WiFi 连接、mDNS 服务注册和极简配置 Web 服务器。
 */
class NetworkManager {
public:
    /**
     * Constructor / 构造函数
     */
    NetworkManager();

    /**
     * Initialize network based on config.h settings.
     * Call once in setup().
     * 
     * 根据 config.h 的设置初始化网络。
     * 在 setup() 中调用一次。
     * 
     * @return true if initialization succeeded / 初始化成功返回 true
     */
    bool begin();

    /**
     * Non-blocking periodic update. Call in loop().
     * Handles STA reconnection and other maintenance tasks.
     * 
     * 非阻塞的周期性更新，在 loop() 中调用。
     * 处理 STA 重连等维护任务。
     */
    void update();

    /**
     * Check if network is connected and ready.
     * 检查网络是否已连接且就绪。
     * 
     * @return true if connected / 已连接返回 true
     */
    bool isConnected() const;

    /**
     * Get the current IP address as a string.
     * 获取当前 IP 地址（字符串形式）。
     * 
     * @return IP address string / IP 地址字符串
     */
    IPAddress getIP() const;

    /**
     * Get the current network mode.
     * 获取当前网络模式。
     * 
     * @return NETWORK_MODE_AP or NETWORK_MODE_STA
     */
    int getMode() const;

private:
    // --- Internal methods / 内部方法 ---

    /**
     * Start Access Point mode / 启动热点模式
     * @return true on success / 成功返回 true
     */
    bool startAP();

    /**
     * Start Station mode (non-blocking) / 启动客户端模式（非阻塞）
     * @return true if connection initiated / 连接发起成功返回 true
     */
    bool startSTA();

    /**
     * Register mDNS service / 注册 mDNS 服务
     * @return true on success / 成功返回 true
     */
    bool startMDNS();

    /**
     * Setup the async web server routes / 设置异步 Web 服务器路由
     */
    void setupWebServer();

    // --- Member variables / 成员变量 ---

    AsyncWebServer _server;            // Async HTTP server / 异步 HTTP 服务器
    bool           _connected;         // Connection status / 连接状态
    bool           _mdnsStarted;       // mDNS status / mDNS 状态
    bool           _serverStarted;     // Web server status / Web 服务器状态
    int            _mode;              // Current network mode / 当前网络模式

    // STA mode reconnection state / STA 模式重连状态
    unsigned long  _lastSTACheckMs;    // Last reconnect check time / 上次重连检查时间
    int            _staRetryCount;     // Current retry count / 当前重试次数
    bool           _staConnecting;     // Whether STA is attempting to connect / STA 是否正在尝试连接
};

#endif // NETWORK_MANAGER_H
