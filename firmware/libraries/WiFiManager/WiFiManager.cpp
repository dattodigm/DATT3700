/**
 * WiFiManager.cpp - ESP32 WiFi连接管理实现
 */

#include "WiFiManager.h"

WiFiManager::WiFiManager() 
    : _mode(WiFiMode::AP), 
      _state(ConnectionState::DISCONNECTED),
      _oscPort(OSC_PORT),
      _lastReconnectAttempt(0),
      _connectionStartTime(0) {
}

void WiFiManager::begin(WiFiMode mode) {
    _mode = mode;
    
    printLogo();
    
    Serial.println("\n==============================================");
    Serial.println("       WiFi Manager Initializing...");
    Serial.println("==============================================");
    
    switch(_mode) {
        case WiFiMode::AP:
            Serial.println("Mode: Access Point (创建热点)");
            startAP();
            break;
            
        case WiFiMode::STA:
            Serial.println("Mode: Station (连接WiFi)");
            startSTA();
            break;
            
        case WiFiMode::AP_STA:
            Serial.println("Mode: AP + Station (混合模式)");
            startAP_STA();
            break;
    }
    
    // 启动UDP用于OSC通信
    _udp.begin(_oscPort);
    Serial.printf("OSC Server started on port: %d\n", _oscPort);
    Serial.println("==============================================\n");
}

void WiFiManager::startAP() {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    
    IPAddress IP = WiFi.softAPIP();
    _state = ConnectionState::CONNECTED;
    
    Serial.println("\n✅ WiFi热点已创建！");
    Serial.println("----------------------------------------------");
    Serial.print("热点名称 (SSID): ");
    Serial.println(AP_SSID);
    Serial.print("热点密码: ");
    Serial.println(AP_PASSWORD);
    Serial.print("ESP32 IP地址: ");
    Serial.println(IP);
    Serial.print("OSC端口: ");
    Serial.println(_oscPort);
    Serial.println("----------------------------------------------");
    Serial.println("请用电脑连接此WiFi后发送OSC命令");
}

void WiFiManager::startSTA() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(STA_SSID, STA_PASSWORD);
    
    _state = ConnectionState::CONNECTING;
    _connectionStartTime = millis();
    
    Serial.print("\n正在连接到WiFi: ");
    Serial.println(STA_SSID);
    Serial.print("密码: ");
    Serial.println(STA_PASSWORD);
    Serial.println("等待连接...");
}

void WiFiManager::startAP_STA() {
    WiFi.mode(WIFI_AP_STA);
    
    // 启动AP部分
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    IPAddress APIP = WiFi.softAPIP();
    
    // 启动STA部分
    WiFi.begin(STA_SSID, STA_PASSWORD);
    
    _state = ConnectionState::CONNECTING;
    _connectionStartTime = millis();
    
    Serial.println("\n混合模式启动中...");
    Serial.println("----------------------------------------------");
    Serial.println("热点部分:");
    Serial.print("  SSID: ");
    Serial.println(AP_SSID);
    Serial.print("  IP: ");
    Serial.println(APIP);
    Serial.println("\nSTA部分:");
    Serial.print("  目标WiFi: ");
    Serial.println(STA_SSID);
    Serial.println("  状态: 连接中...");
    Serial.println("----------------------------------------------");
}

void WiFiManager::update() {
    if (_mode == WiFiMode::STA || _mode == WiFiMode::AP_STA) {
        checkConnection();
    }
}

void WiFiManager::checkConnection() {
    if (_state == ConnectionState::CONNECTING) {
        if (WiFi.status() == WL_CONNECTED) {
            _state = ConnectionState::CONNECTED;
            printConnectionSuccess();
        } else if (millis() - _connectionStartTime > CONNECTION_TIMEOUT) {
            Serial.println("\n❌ WiFi连接超时！");
            _state = ConnectionState::ERROR;
        } else {
            // 每2秒打印一次进度
            static unsigned long lastProgress = 0;
            if (millis() - lastProgress > 2000) {
                Serial.print(".");
                lastProgress = millis();
            }
        }
    } else if (_state == ConnectionState::DISCONNECTED || 
               _state == ConnectionState::ERROR) {
        // 尝试重连
        if (millis() - _lastReconnectAttempt > RECONNECT_INTERVAL) {
            Serial.println("\n尝试重新连接...");
            WiFi.reconnect();
            _state = ConnectionState::CONNECTING;
            _connectionStartTime = millis();
            _lastReconnectAttempt = millis();
        }
    } else if (_state == ConnectionState::CONNECTED) {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("\n⚠️ WiFi连接断开！");
            _state = ConnectionState::DISCONNECTED;
            _lastReconnectAttempt = millis();
        }
    }
}

void WiFiManager::printConnectionSuccess() {
    Serial.println("\n✅ WiFi连接成功！");
    Serial.println("----------------------------------------------");
    Serial.print("SSID: ");
    Serial.println(STA_SSID);
    Serial.print("ESP32 IP地址: ");
    Serial.println(WiFi.localIP());
    Serial.print("子网掩码: ");
    Serial.println(WiFi.subnetMask());
    Serial.print("网关: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("信号强度 (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    Serial.print("MAC地址: ");
    Serial.println(WiFi.macAddress());
    Serial.println("----------------------------------------------");
    Serial.println("发送OSC命令到此IP地址");
}

IPAddress WiFiManager::getIP() {
    if (_mode == WiFiMode::AP || _mode == WiFiMode::AP_STA) {
        return WiFi.softAPIP();
    } else {
        return WiFi.localIP();
    }
}

ConnectionState WiFiManager::getState() {
    return _state;
}

int WiFiManager::getRSSI() {
    if (_mode == WiFiMode::STA || _mode == WiFiMode::AP_STA) {
        return WiFi.RSSI();
    }
    return 0;
}

bool WiFiManager::isConnected() {
    return _state == ConnectionState::CONNECTED;
}

void WiFiManager::printStatus() {
    Serial.println("\n========== WiFi 状态 ==========");
    Serial.print("模式: ");
    switch(_mode) {
        case WiFiMode::AP: Serial.println("AP (热点)"); break;
        case WiFiMode::STA: Serial.println("STA (客户端)"); break;
        case WiFiMode::AP_STA: Serial.println("AP+STA (混合)"); break;
    }
    
    Serial.print("状态: ");
    switch(_state) {
        case ConnectionState::DISCONNECTED: Serial.println("断开"); break;
        case ConnectionState::CONNECTING: Serial.println("连接中"); break;
        case ConnectionState::CONNECTED: Serial.println("已连接 ✓"); break;
        case ConnectionState::ERROR: Serial.println("错误"); break;
    }
    
    Serial.print("IP地址: ");
    Serial.println(getIP());
    
    if (_mode == WiFiMode::STA || _mode == WiFiMode::AP_STA) {
        Serial.print("信号强度: ");
        Serial.print(getRSSI());
        Serial.println(" dBm");
    }
    Serial.println("================================\n");
}

void WiFiManager::reconnect() {
    Serial.println("手动触发重连...");
    WiFi.disconnect();
    delay(100);
    WiFi.reconnect();
    _state = ConnectionState::CONNECTING;
    _connectionStartTime = millis();
}

void WiFiManager::setOscPort(int port) {
    _oscPort = port;
}

WiFiUDP* WiFiManager::getUDP() {
    return &_udp;
}

void WiFiManager::printLogo() {
    Serial.println("\n");
    Serial.println("    🌸 Digital Bloom 🌸");
    Serial.println("   具身AI花朵控制系统");
    Serial.println();
}
