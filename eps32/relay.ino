#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCBundle.h>

// --- 连接到主ESP32热点的配置 ---
const char* main_ssid = "ESP32_Sylvie";
const char* main_password = "12345678";

// --- 创建自己的热点配置 ---
const char* relay_ssid = "ESP32_Relay";
const char* relay_password = "12345678";

// --- OSC 配置 ---
const int relayPort = 9000;      // 本机监听端口（PC连接用）
const int mainPort = 8888;        // 主ESP32端口
IPAddress mainESP32IP(192, 168, 4, 1);  // 主ESP32的IP

WiFiUDP udpRelay;    // 接收来自PC的消息
WiFiUDP udpToMain;   // 转发到主ESP32的消息

// --- 状态指示灯 ---
const int STATUS_LED = 2;  // 板载LED
bool wifiConnected = false;

void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED, OUTPUT);
  
  Serial.println("\n=== ESP32 OSC中继器 ===");
  
  // 先连接到主ESP32热点
  connectToMainESP32();
  
  // 创建自己的热点供PC连接
  createRelayHotspot();
  
  // 启动UDP服务
  udpRelay.begin(relayPort);
  
  printStatus();
}

void loop() {
  // 检查WiFi连接状态
  if (WiFi.status() != WL_CONNECTED) {
    if (wifiConnected) {
      Serial.println("⚠️ WiFi断开，尝试重连...");
      wifiConnected = false;
      digitalWrite(STATUS_LED, LOW);
    }
    reconnectToMainESP32();
  } else {
    if (!wifiConnected) {
      wifiConnected = true;
      digitalWrite(STATUS_LED, HIGH);
      Serial.println("✅ WiFi已连接");
    }
  }
  
  // 接收来自PC的OSC消息
  OSCMessage msgFromPC;
  int size = udpRelay.parsePacket();
  
  if (size > 0) {
    Serial.print("📥 收到来自PC的消息 (");
    Serial.print(udpRelay.remoteIP());
    Serial.print(":");
    Serial.print(udpRelay.remotePort());
    Serial.println(")");
    
    // 读取消息
    while (size--) {
      msgFromPC.fill(udpRelay.read());
    }
    
    if (!msgFromPC.hasError()) {
      // 获取并打印地址
      char addressBuffer[128];
      msgFromPC.getAddress(addressBuffer, 0, sizeof(addressBuffer));
      Serial.print("   地址: ");
      Serial.println(addressBuffer);
      
      // 转发到主ESP32
      if (wifiConnected) {
        forwardToMainESP32(msgFromPC);
      } else {
        Serial.println("❌ 无法转发：未连接到主ESP32");
      }
    } else {
      Serial.println("❌ OSC消息解析错误");
    }
  }
  
  // 状态指示灯闪烁
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 1000) {
    if (wifiConnected) {
      // 连接成功：快速闪烁
      digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    } else {
      // 未连接：慢速闪烁
      static int blinkCount = 0;
      blinkCount++;
      digitalWrite(STATUS_LED, (blinkCount % 4) < 1);
    }
    lastBlink = millis();
  }
}

// 连接到主ESP32热点
void connectToMainESP32() {
  Serial.println("🔗 正在连接到主ESP32热点...");
  Serial.print("   SSID: ");
  Serial.println(main_ssid);
  
  WiFi.mode(WIFI_AP_STA);  // 同时支持AP和STA模式
  WiFi.begin(main_ssid, main_password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\n✅ 已连接到主ESP32");
    Serial.print("   本机IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("   主ESP32 IP: ");
    Serial.println(mainESP32IP);
  } else {
    wifiConnected = false;
    Serial.println("\n❌ 连接失败");
  }
}

// 重连到主ESP32
void reconnectToMainESP32() {
  static unsigned long lastAttempt = 0;
  if (millis() - lastAttempt > 5000) {  // 每5秒尝试一次
    Serial.println("🔄 尝试重连到主ESP32...");
    WiFi.disconnect();
    delay(100);
    WiFi.begin(main_ssid, main_password);
    lastAttempt = millis();
  }
}

// 创建中继热点
void createRelayHotspot() {
  Serial.println("📡 正在创建中继热点...");
  Serial.print("   SSID: ");
  Serial.println(relay_ssid);
  
  WiFi.softAP(relay_ssid, relay_password);
  IPAddress relayIP = WiFi.softAPIP();
  
  Serial.println("✅ 中继热点已创建");
  Serial.print("   热点IP: ");
  Serial.println(relayIP);
  Serial.print("   OSC端口: ");
  Serial.println(relayPort);
}

// 转发消息到主ESP32
void forwardToMainESP32(OSCMessage &msg) {
  Serial.print("📤 转发消息到主ESP32... ");
  
  udpToMain.beginPacket(mainESP32IP, mainPort);
  msg.send(udpToMain);
  udpToMain.endPacket();
  
  Serial.println("完成");
  
  // 闪烁LED表示转发成功
  digitalWrite(STATUS_LED, LOW);
  delay(50);
  digitalWrite(STATUS_LED, HIGH);
}

// 打印状态信息
void printStatus() {
  Serial.println("\n==================================================");
  Serial.println("📊 中继器状态");
  Serial.println("==================================================");
  Serial.println("主ESP32连接:");
  Serial.print("  SSID: ");
  Serial.println(main_ssid);
  Serial.print("  IP: ");
  Serial.println(mainESP32IP);
  Serial.print("  端口: ");
  Serial.println(mainPort);
  Serial.println("\n中继热点:");
  Serial.print("  SSID: ");
  Serial.println(relay_ssid);
  Serial.print("  IP: ");
  Serial.println(WiFi.softAPIP());
  Serial.print("  端口: ");
  Serial.println(relayPort);
  Serial.println("\nPC连接方法:");
  Serial.println("  1. 连接到WiFi: ESP32_Relay (密码: 12345678)");
  Serial.print("  2. 发送OSC到: ");
  Serial.print(WiFi.softAPIP());
  Serial.print(":");
  Serial.println(relayPort);
  Serial.println("\n支持的OSC命令:");
  Serial.println("  /auto [0/1]");
  Serial.println("  /motor1 [1/-1/0]");
  Serial.println("  /motor2 [1/-1/0]");
  Serial.println("  /led1 [r] [g] [b]");
  Serial.println("  /led2 [r] [g] [b]");
  Serial.println("  /preset [1/2/3]");
  Serial.println("==================================================\n");
}
