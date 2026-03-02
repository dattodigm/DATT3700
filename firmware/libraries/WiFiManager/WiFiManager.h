/**
 * WiFiManager - ESP32 WiFi连接管理库
 * 
 * 功能特点：
 * - 支持AP模式（创建热点）和STA模式（连接现有网络）
 * - 自动重连机制
 * - 串口输出详细的连接状态
 * - 内存友好，适合ESP32
 * 
 * 使用方法：
 * 1. 修改 config.h 设置WiFi参数
 * 2. 在setup()中调用 wifiManager.begin();
 * 3. 在loop()中调用 wifiManager.update();
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include <WiFiUdp.h>

// 默认配置（可在 config.h 中覆盖）
#ifndef WIFI_MODE_SELECTION
#define WIFI_MODE_SELECTION WIFI_MODE_AP  // 默认AP模式
#endif

#ifndef AP_SSID
#define AP_SSID "DigitalBloom_Flower"
#endif

#ifndef AP_PASSWORD
#define AP_PASSWORD "12345678"
#endif

#ifndef STA_SSID
#define STA_SSID "YOUR_WIFI_SSID"
#endif

#ifndef STA_PASSWORD
#define STA_PASSWORD "YOUR_WIFI_PASSWORD"
#endif

#ifndef OSC_PORT
#define OSC_PORT 8888
#endif

// WiFi模式枚举
enum class WiFiMode {
    AP,      // 创建热点模式
    STA,     // 连接现有网络
    AP_STA   // 混合模式（创建热点+连接网络）
};

// 连接状态枚举
enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    ERROR
};

class WiFiManager {
public:
    WiFiManager();
    
    // 初始化（在setup中调用）
    void begin(WiFiMode mode = WiFiMode::AP);
    
    // 更新状态（在loop中调用）
    void update();
    
    // 获取当前IP地址
    IPAddress getIP();
    
    // 获取连接状态
    ConnectionState getState();
    
    // 获取WiFi信号强度（仅STA模式）
    int getRSSI();
    
    // 检查是否已连接
    bool isConnected();
    
    // 打印当前状态到串口
    void printStatus();
    
    // 手动重连
    void reconnect();
    
    // 设置OSC端口
    void setOscPort(int port);
    
    // 获取UDP对象（用于OSC通信）
    WiFiUDP* getUDP();

private:
    WiFiMode _mode;
    ConnectionState _state;
    WiFiUDP _udp;
    int _oscPort;
    unsigned long _lastReconnectAttempt;
    unsigned long _connectionStartTime;
    static const unsigned long RECONNECT_INTERVAL = 5000;  // 5秒重试间隔
    static const unsigned long CONNECTION_TIMEOUT = 15000; // 15秒连接超时
    
    void startAP();
    void startSTA();
    void startAP_STA();
    void checkConnection();
    void printConnectionSuccess();
    void printLogo();
};

#endif
