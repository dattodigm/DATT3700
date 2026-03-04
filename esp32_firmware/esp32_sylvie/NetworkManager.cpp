/**
 * NetworkManager.cpp - Network Management Implementation / 网络管理模块实现
 * 
 * Implements WiFi AP/STA mode, mDNS discovery, and HTTP config endpoint.
 * Based on verified WiFi code from esp32_sylvie.ino.
 * 
 * 实现 WiFi AP/STA 模式、mDNS 发现和 HTTP 配置端点。
 * 基于 esp32_sylvie.ino 中已验证的 WiFi 代码。
 */

#include "NetworkManager.h"

// ============================================================
// Constructor / 构造函数
// ============================================================
DattNetworkManager::DattNetworkManager()
    : _server(WEB_SERVER_PORT)
    , _connected(false)
    , _mdnsStarted(false)
    , _serverStarted(false)
    , _mode(NETWORK_MODE)
    , _lastSTACheckMs(0)
    , _staRetryCount(0)
    , _staConnecting(false)
{
}

// ============================================================
// begin() - Initialize network / 初始化网络
// ============================================================
bool DattNetworkManager::begin() {
    bool success = false;

    if (_mode == NETWORK_MODE_AP) {
        // --- Access Point mode / 热点模式 ---
        Serial.println("[NetworkManager] Starting AP mode... / 正在启动热点模式...");
        success = startAP();
    } else if (_mode == NETWORK_MODE_STA) {
        // --- Station mode / 客户端模式 ---
        Serial.println("[NetworkManager] Starting STA mode... / 正在启动客户端模式...");
        success = startSTA();
    } else {
        Serial.println("[NetworkManager] ERROR: Invalid NETWORK_MODE in config.h");
        return false;
    }

    if (success) {
        // Start mDNS service discovery / 启动 mDNS 服务发现
        startMDNS();

        // Start web server in AP mode / 在热点模式下启动 Web 服务器
        if (_mode == NETWORK_MODE_AP) {
            setupWebServer();
        }
    }

    return success;
}

// ============================================================
// update() - Non-blocking periodic tasks / 非阻塞周期性任务
// ============================================================
void DattNetworkManager::update() {
    // STA mode: non-blocking connection monitoring / STA 模式：非阻塞连接监控
    if (_mode == NETWORK_MODE_STA) {
        unsigned long now = millis();

        if (_staConnecting) {
            // Still waiting for initial connection / 仍在等待初始连接
            if (now - _lastSTACheckMs >= STA_RETRY_INTERVAL_MS) {
                _lastSTACheckMs = now;

                if (WiFi.status() == WL_CONNECTED) {
                    // Connection established / 连接已建立
                    _connected = true;
                    _staConnecting = false;
                    Serial.print("[NetworkManager] STA connected! IP: ");
                    Serial.println(WiFi.localIP());

                    // Start mDNS now that we have an IP / 获得 IP 后启动 mDNS
                    if (!_mdnsStarted) {
                        startMDNS();
                    }
                } else {
                    _staRetryCount++;
                    Serial.printf("[NetworkManager] STA connecting... attempt %d/%d\n",
                                  _staRetryCount, STA_MAX_RETRIES);

                    if (_staRetryCount >= STA_MAX_RETRIES) {
                        // Give up and fall back to AP mode / 放弃并回退到热点模式
                        Serial.println("[NetworkManager] STA failed. Falling back to AP mode...");
                        Serial.println("[NetworkManager] STA 连接失败，回退到热点模式...");
                        _staConnecting = false;
                        _mode = NETWORK_MODE_AP;
                        WiFi.disconnect();
                        startAP();
                        startMDNS();
                        setupWebServer();
                    }
                }
            }
        } else if (_connected && WiFi.status() != WL_CONNECTED) {
            // Lost connection, attempt reconnect / 连接断开，尝试重连
            _connected = false;
            Serial.println("[NetworkManager] STA connection lost. Reconnecting...");
            Serial.println("[NetworkManager] STA 连接断开，正在重连...");
            WiFi.reconnect();
            _staConnecting = true;
            _staRetryCount = 0;
            _lastSTACheckMs = now;
        }
    }
    // AP mode: no periodic tasks needed / 热点模式：无需周期性任务
}

// ============================================================
// isConnected() / 检查连接状态
// ============================================================
bool DattNetworkManager::isConnected() const {
    if (_mode == NETWORK_MODE_AP) {
        return _connected;  // AP is always "connected" once started / AP 启动后始终为"已连接"
    }
    return WiFi.status() == WL_CONNECTED;
}

// ============================================================
// getIP() / 获取 IP 地址
// ============================================================
IPAddress DattNetworkManager::getIP() const {
    if (_mode == NETWORK_MODE_AP) {
        return WiFi.softAPIP();
    }
    return WiFi.localIP();
}

// ============================================================
// getMode() / 获取当前模式
// ============================================================
int DattNetworkManager::getMode() const {
    return _mode;
}

// ============================================================
// startAP() - Access Point initialization / 热点模式初始化
// Based on verified code from esp32_sylvie.ino
// 基于 esp32_sylvie.ino 中已验证的代码
// ============================================================
bool DattNetworkManager::startAP() {
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    IPAddress ip = WiFi.softAPIP();

    Serial.print("[NetworkManager] AP started. SSID: ");
    Serial.println(AP_SSID);
    Serial.print("[NetworkManager] AP IP address / 热点 IP 地址: ");
    Serial.println(ip);

    _connected = true;
    return true;
}

// ============================================================
// startSTA() - Station mode initialization (non-blocking)
// 客户端模式初始化（非阻塞）
// ============================================================
bool DattNetworkManager::startSTA() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(STA_SSID, STA_PASSWORD);

    Serial.print("[NetworkManager] Connecting to / 正在连接: ");
    Serial.println(STA_SSID);

    _staConnecting = true;
    _staRetryCount = 0;
    _lastSTACheckMs = millis();

    // Non-blocking: actual connection is monitored in update()
    // 非阻塞：实际连接在 update() 中监控
    return true;
}

// ============================================================
// startMDNS() - Register mDNS service / 注册 mDNS 服务
// Service: _datt_flower._tcp (as specified in AI_INSTRUCTIONS.md)
// ============================================================
bool DattNetworkManager::startMDNS() {
    // Use NODE_ID as the hostname / 使用 NODE_ID 作为主机名
    if (!MDNS.begin(NODE_ID)) {
        Serial.println("[NetworkManager] ERROR: mDNS failed to start / mDNS 启动失败");
        return false;
    }

    // Register service with TXT records / 注册服务并附带 TXT 记录
    // As specified: _datt_flower._tcp
    MDNS.addService(MDNS_SERVICE_NAME, MDNS_PROTOCOL, OSC_PORT);

    // Add TXT records for service discovery / 添加 TXT 记录用于服务发现
    MDNS.addServiceTxt(MDNS_SERVICE_NAME, MDNS_PROTOCOL, "node_type", NODE_TYPE);
    MDNS.addServiceTxt(MDNS_SERVICE_NAME, MDNS_PROTOCOL, "node_id", NODE_ID);
    MDNS.addServiceTxt(MDNS_SERVICE_NAME, MDNS_PROTOCOL, "firmware_version", FIRMWARE_VERSION);

    _mdnsStarted = true;
    Serial.print("[NetworkManager] mDNS started: ");
    Serial.print(NODE_ID);
    Serial.println(".local");
    Serial.println("[NetworkManager] Service registered / 服务已注册: "
                   MDNS_SERVICE_NAME "." MDNS_PROTOCOL);

    return true;
}

// ============================================================
// setupWebServer() - Configure HTTP endpoints / 配置 HTTP 端点
// ============================================================
void DattNetworkManager::setupWebServer() {
    if (_serverStarted) return;  // Prevent double-start / 防止重复启动

    // GET /config - Returns JSON describing this node's hardware
    // GET /config - 返回描述此节点硬件的 JSON 数据
    _server.on("/config", HTTP_GET, [](AsyncWebServerRequest *request) {
        // Build JSON response using fixed-size buffer (no dynamic allocation)
        // 使用固定大小缓冲区构建 JSON 响应（无动态分配）
        char json[256];
        snprintf(json, sizeof(json),
            "{"
                "\"node_id\":\"%s\","
                "\"type\":\"%s\","
                "\"motors\":%d,"
                "\"flowers\":%d,"
                "\"firmware_version\":\"%s\","
                "\"osc_port\":%d,"
                "\"network_mode\":\"AP\""
            "}",
            NODE_ID,
            NODE_TYPE,
            HW_MOTORS,
            HW_FLOWERS,
            FIRMWARE_VERSION,
            OSC_PORT
        );
        request->send(200, "application/json", json);
    });

    // GET / - Simple status page / 简单状态页面
    _server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        char html[512];
        snprintf(html, sizeof(html),
            "<!DOCTYPE html><html><head><title>%s</title></head>"
            "<body>"
            "<h1>DATT3700 Flower Node / 花朵节点</h1>"
            "<p>Node ID: %s</p>"
            "<p>Type: %s</p>"
            "<p>Firmware: %s</p>"
            "<p><a href=\"/config\">View Config JSON / 查看配置 JSON</a></p>"
            "</body></html>",
            NODE_ID, NODE_ID, NODE_TYPE, FIRMWARE_VERSION
        );
        request->send(200, "text/html", html);
    });

    _server.begin();
    _serverStarted = true;
    Serial.printf("[NetworkManager] Web server started on port %d\n", WEB_SERVER_PORT);
    Serial.println("[NetworkManager] Endpoints / 端点: GET /  GET /config");
}
