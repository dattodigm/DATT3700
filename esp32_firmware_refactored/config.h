/**
 * config.h - Global Configuration File / 全局配置文件
 * 
 * This file centralizes all configurable parameters for the ESP32 firmware.
 * Modify settings here instead of editing source code directly.
 * 
 * 本文件集中管理 ESP32 固件的所有可配置参数。
 * 请在此处修改设置，而非直接编辑源代码。
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================
// Network Mode Configuration / 网络模式配置
// ============================================================
#define NETWORK_MODE_AP   1  // Access Point mode / 热点模式
#define NETWORK_MODE_STA  2  // Station mode / 客户端模式

// Select network mode (change this to switch) / 选择网络模式（修改此值切换）
#define NETWORK_MODE NETWORK_MODE_AP

// ============================================================
// AP Mode Settings / 热点模式设置
// (Used when NETWORK_MODE == NETWORK_MODE_AP)
// ============================================================
#define AP_SSID     "ESP32_Sylvie"
#define AP_PASSWORD "12345678"     // Minimum 8 characters / 至少8位

// ============================================================
// STA Mode Settings / 客户端模式设置
// (Used when NETWORK_MODE == NETWORK_MODE_STA)
// ============================================================
#define STA_SSID     "YOUR_ROUTER_SSID"
#define STA_PASSWORD "YOUR_ROUTER_PASSWORD"

// Maximum STA connection attempts / STA 模式最大连接尝试次数
#define STA_MAX_RETRIES 20

// Interval between STA connection checks (ms) / STA 连接检查间隔（毫秒）
#define STA_RETRY_INTERVAL_MS 500

// ============================================================
// OSC / UDP Configuration / OSC/UDP 配置
// ============================================================
#define OSC_PORT 8888

// ============================================================
// Node Identification / 节点识别
// ============================================================
#define NODE_TYPE        "sylvie"       // Options: "sylvie", "sue", "kait", "face_track"
#define NODE_ID          "sylvie_1"     // Unique ID for this node / 节点唯一ID
#define FIRMWARE_VERSION "1.0.0"

// ============================================================
// Hardware Description (for /config endpoint) / 硬件描述
// ============================================================
#define HW_MOTORS  2  // Number of DC motors / 直流电机数量
#define HW_FLOWERS 4  // Number of flowers controlled / 控制的花朵数量

// ============================================================
// mDNS Service Configuration / mDNS 服务配置
// ============================================================
#define MDNS_SERVICE_NAME "_datt_flower"
#define MDNS_PROTOCOL     "_tcp"

// ============================================================
// Web Server Port (AP mode only) / Web 服务器端口（仅热点模式）
// ============================================================
#define WEB_SERVER_PORT 80

// Delay before starting web server after AP init (ms)
// AP 初始化后启动 Web 服务器前的延迟（毫秒）
#define WEB_SERVER_DEFER_MS 1000

#endif // CONFIG_H
