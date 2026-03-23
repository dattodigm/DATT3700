#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <esp_wifi.h>
#include <esp_event.h>

// ============================================================
// ⚙️  CONFIG — 所有可调参数都在这里修改
// ============================================================

// --- 模式选择：true = 热点模式(AP)，false = 连接已有WiFi(STA) ---
#define USE_AP_MODE  false

// --- 热点模式配置 ---
const char* AP_SSID     = "F7OWER";
const char* AP_PASSWORD = "12345678";

// --- Station模式配置（连接已有WiFi）---
const char* STA_SSID     = "MisAXNet";
const char* STA_PASSWORD = "AX6000@O26";

// --- mDNS 设备广播名称（局域网内可用 sylvie.local 访问）---
const char* MDNS_NAME = "sylvie";

// --- OSC 端口 ---
const int OSC_PORT = 8888;

// --- 热点客户端扫描间隔（毫秒）---
// const unsigned long CLIENT_SCAN_INTERVAL = 5000;

// --- 引脚定义 ---
const int M1_A = 25, M1_B = 26;
const int L1_R = 2,  L1_G = 4,  L1_B_PIN = 5;
const int M2_A = 18, M2_B = 19;
const int L2_R = 12, L2_G = 13, L2_B_PIN = 14;

// ============================================================
// 客户端信息结构
// ============================================================
struct ClientInfo {
  uint8_t mac[6];
  uint32_t ip;
  bool active;
};
#define MAX_CLIENTS 5
ClientInfo clients[MAX_CLIENTS];

// ============================================================
// 运行时变量
// ============================================================
WiFiUDP udp;
bool autoMode = true;
unsigned long lastAutoUpdate = 0;
// unsigned long lastClientScan = 0;
int autoState = 0;
// ── 前向声明 ────────────────────────────────────────────────
void setMotor(int motor, int direction);
void setLED(int led, int r, int g, int b);
void setPreset(int preset);
void stopAll();
void runAutoMode();
void routeAuto(OSCMessage &msg, int addrOffset);
void routeMotor1(OSCMessage &msg, int addrOffset);
void routeMotor2(OSCMessage &msg, int addrOffset);
void routeLED1(OSCMessage &msg, int addrOffset);
void routeLED2(OSCMessage &msg, int addrOffset);
void routePreset(OSCMessage &msg, int addrOffset);
void printConnectedClients();
void printSelfInfo();
void handleSerialCommand();
void sendClientListOSC(OSCMessage &msg, int addrOffset);
void sendSelfInfoOSC(OSCMessage &msg, int addrOffset);
// ────────────────────────────────────────────────────────────
// ============================================================
// WiFi 事件处理
// ============================================================
void onWifiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  switch (event) {

    case ARDUINO_EVENT_WIFI_AP_STACONNECTED:
      Serial.printf("\n🔌 客户端已连接  MAC: %02X:%02X:%02X:%02X:%02X:%02X（等待 DHCP 分配 IP...）\n",
        info.wifi_ap_staconnected.mac[0], info.wifi_ap_staconnected.mac[1],
        info.wifi_ap_staconnected.mac[2], info.wifi_ap_staconnected.mac[3],
        info.wifi_ap_staconnected.mac[4], info.wifi_ap_staconnected.mac[5]);
      break;

    case ARDUINO_EVENT_WIFI_AP_STAIPASSIGNED:
      {
        ip_event_ap_staipassigned_t* event_data = (ip_event_ap_staipassigned_t*)&info.wifi_ap_staipassigned;
        uint32_t ip = event_data->ip.addr;
        uint8_t* mac = event_data->mac;
        Serial.printf("✅ IP 已分配  MAC: %02X:%02X:%02X:%02X:%02X:%02X  IP: %d.%d.%d.%d\n",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5],
          ip & 0xFF, (ip >> 8) & 0xFF, (ip >> 16) & 0xFF, (ip >> 24) & 0xFF);
        for (int i = 0; i < MAX_CLIENTS; i++) {
          if (!clients[i].active) {
            memcpy(clients[i].mac, mac, 6);
            clients[i].ip = ip;
            clients[i].active = true;
            break;
          }
        }
        printConnectedClients();
      }
      break;

    case ARDUINO_EVENT_WIFI_AP_STADISCONNECTED:
      {
        uint8_t* mac = info.wifi_ap_stadisconnected.mac;
        Serial.printf("❌ 客户端已断开  MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        for (int i = 0; i < MAX_CLIENTS; i++) {
          if (clients[i].active && memcmp(clients[i].mac, mac, 6) == 0) {
            clients[i].active = false;
            break;
          }
        }
        printConnectedClients();
      }
      break;

    default: break;
  }
}

// ============================================================
// WiFi 初始化
// ============================================================
void setupWiFi() {
  if (USE_AP_MODE) {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    Serial.print("✅ AP模式已启动，IP: ");
    Serial.println(WiFi.softAPIP());
  } else {
    WiFi.mode(WIFI_STA);
    WiFi.begin(STA_SSID, STA_PASSWORD);
    Serial.print("🔗 连接WiFi中");
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 20) {
      delay(500); Serial.print("."); retry++;
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("\n✅ STA模式已连接，IP: ");
      Serial.println(WiFi.localIP());
    } else {
      Serial.println("\n❌ WiFi连接失败，请检查 STA_SSID / STA_PASSWORD");
    }
  }
}

// ============================================================
// 打印当前在线客户端（AP 模式）
// ============================================================
void printConnectedClients() {
  if (!USE_AP_MODE) return;
  int count = WiFi.softAPgetStationNum();
  Serial.printf("\n📡 当前在线客户端：%d\n", count);
  for (int i = 0; i < MAX_CLIENTS; i++) {
    if (clients[i].active) {
      uint32_t ip = clients[i].ip;
      Serial.printf("  [%d] MAC: %02X:%02X:%02X:%02X:%02X:%02X  IP: %d.%d.%d.%d\n",
        i,
        clients[i].mac[0], clients[i].mac[1], clients[i].mac[2],
        clients[i].mac[3], clients[i].mac[4], clients[i].mac[5],
        ip & 0xFF, (ip >> 8) & 0xFF, (ip >> 16) & 0xFF, (ip >> 24) & 0xFF);
    }
  }
}

// ============================================================
// 打印本机网络信息
// ============================================================
void printSelfInfo() {
  Serial.println("\n=== 本机网络信息 ===");

  uint8_t mac[6];
  WiFi.macAddress(mac);
  Serial.printf("设备名：%s\n", MDNS_NAME);
  Serial.printf("MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
    mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

  if (USE_AP_MODE) {
    Serial.printf("模式：AP (热点)\n");
    Serial.printf("IP: %d.%d.%d.%d\n",
      WiFi.softAPIP()[0], WiFi.softAPIP()[1],
      WiFi.softAPIP()[2], WiFi.softAPIP()[3]);
  } else {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("模式：STA (客户端)\n");
      Serial.printf("IP: %d.%d.%d.%d\n",
        WiFi.localIP()[0], WiFi.localIP()[1],
        WiFi.localIP()[2], WiFi.localIP()[3]);
    } else {
      Serial.println("模式：STA (未连接)");
      Serial.println("IP: 未分配");
    }
  }
  Serial.println("====================\n");
}

// ============================================================
// 串口命令解析
// 支持格式：motor1 1 / led1 255 0 0 / auto 0 / preset 2 / clients / selfinfo
// ============================================================
void handleSerialCommand() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.startsWith("motor1")) {
    int dir = line.substring(7).toInt();
    setMotor(1, dir);
    Serial.printf("电机 A: %d\n", dir);
  } else if (line.startsWith("motor2")) {
    int dir = line.substring(7).toInt();
    setMotor(2, dir);
    Serial.printf("电机 B: %d\n", dir);
  } else if (line.startsWith("led1")) {
    int r, g, b;
    sscanf(line.c_str(), "led1 %d %d %d", &r, &g, &b);
    setLED(1, r, g, b);
    Serial.printf("LED1: R=%d G=%d B=%d\n", r, g, b);
  } else if (line.startsWith("led2")) {
    int r, g, b;
    sscanf(line.c_str(), "led2 %d %d %d", &r, &g, &b);
    setLED(2, r, g, b);
    Serial.printf("LED2: R=%d G=%d B=%d\n", r, g, b);
  } else if (line.startsWith("auto")) {
    autoMode = line.substring(5).toInt();
    Serial.printf("自动模式：%s\n", autoMode ? "开" : "关");
  } else if (line.startsWith("preset")) {
    int p = line.substring(7).toInt();
    setPreset(p);
    Serial.printf("预设场景：%d\n", p);
  } else if (line.equals("clients")) {
    if (USE_AP_MODE) {
      printConnectedClients();
    } else {
      Serial.println("⚠️ 仅在 AP 模式下有效");
    }
  } else if (line.equals("selfinfo")) {
    printSelfInfo();
  }
}

// ============================================================
// Setup
// ============================================================
void setup() {
  Serial.begin(115200);
  memset(clients, 0, sizeof(clients));

  int pins[] = {M1_A, M1_B, M2_A, M2_B, L1_R, L1_G, L1_B_PIN, L2_R, L2_G, L2_B_PIN};
  for (int p : pins) pinMode(p, OUTPUT);

  WiFi.onEvent(onWifiEvent);
  setupWiFi();

  if (MDNS.begin(MDNS_NAME)) {
    Serial.printf("✅ mDNS 已启动: http://%s.local\n", MDNS_NAME);
    MDNS.addService("osc", "udp", OSC_PORT);
  }

  udp.begin(OSC_PORT);
  Serial.printf("✅ OSC 监听端口: %d\n", OSC_PORT);
  Serial.println("📋 串口命令: motor1 1 | motor2 -1 | led1 255 0 0 | led2 0 255 255 | auto 0 | preset 2");
}

// ============================================================
// Loop
// ============================================================
void loop() {
  OSCMessage msg;
  int size = udp.parsePacket();
  if (size > 0) {
    while (size--) msg.fill(udp.read());
    if (!msg.hasError()) {
      msg.route("/auto",   routeAuto);
      msg.route("/motor1", routeMotor1);
      msg.route("/motor2", routeMotor2);
      msg.route("/led1",   routeLED1);
      msg.route("/led2",   routeLED2);
      msg.route("/preset", routePreset);
      msg.route("/info/clients", sendClientListOSC);
      msg.route("/info/self", sendSelfInfoOSC);
    }
  }

  handleSerialCommand();

  if (autoMode) runAutoMode();
}

// ============================================================
// OSC 路由函数
// ============================================================
void routeAuto(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    int value = msg.getInt(0);
    if (value == 1) {
      autoMode = true;
      lastAutoUpdate = millis();
      autoState = 0;
      Serial.println("切换到自动模式");
    } else {
      autoMode = false;
      stopAll();
      Serial.println("切换到手动模式");
    }
  }
}

void routeMotor1(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0)) {
    int dir = msg.getInt(0);
    setMotor(1, dir);
    Serial.printf("Motor A: %d\n", dir);
  }
}

void routeMotor2(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0)) {
    int dir = msg.getInt(0);
    setMotor(2, dir);
    Serial.printf("Motor B: %d\n", dir);
  }
}

void routeLED1(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0) && msg.isInt(1) && msg.isInt(2)) {
    int r = msg.getInt(0), g = msg.getInt(1), b = msg.getInt(2);
    setLED(1, r, g, b);
    Serial.printf("LED1: R=%d G=%d B=%d\n", r, g, b);
  }
}

void routeLED2(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0) && msg.isInt(1) && msg.isInt(2)) {
    int r = msg.getInt(0), g = msg.getInt(1), b = msg.getInt(2);
    setLED(2, r, g, b);
    Serial.printf("LED2: R=%d G=%d B=%d\n", r, g, b);
  }
}

void routePreset(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0)) {
    int preset = msg.getInt(0);
    setPreset(preset);
    Serial.printf("预设场景: %d\n", preset);
  }
}

// ============================================================
// 自动模式
// ============================================================
void runAutoMode() {
  unsigned long currentTime = millis();
  switch (autoState) {
    case 0:
      if (currentTime - lastAutoUpdate == 0 || currentTime - lastAutoUpdate > 3000) {
        setPreset(1); lastAutoUpdate = currentTime; autoState = 1;
      }
      break;
    case 1:
      if (currentTime - lastAutoUpdate > 3000) {
        stopAll(); lastAutoUpdate = currentTime; autoState = 2;
      }
      break;
    case 2:
      if (currentTime - lastAutoUpdate > 500) {
        setPreset(2); lastAutoUpdate = currentTime; autoState = 3;
      }
      break;
    case 3:
      if (currentTime - lastAutoUpdate > 3000) {
        stopAll(); lastAutoUpdate = currentTime; autoState = 0;
      }
      break;
  }
}

// ============================================================
// 硬件控制
// ============================================================
void setMotor(int motor, int direction) {
  int pinA = (motor == 1) ? M1_A : M2_A;
  int pinB = (motor == 1) ? M1_B : M2_B;
  if (direction > 0)      { digitalWrite(pinA, HIGH); digitalWrite(pinB, LOW);  }
  else if (direction < 0) { digitalWrite(pinA, LOW);  digitalWrite(pinB, HIGH); }
  else                    { digitalWrite(pinA, LOW);  digitalWrite(pinB, LOW);  }
}

void setLED(int led, int r, int g, int b) {
  int pinR = (led == 1) ? L1_R     : L2_R;
  int pinG = (led == 1) ? L1_G     : L2_G;
  int pinB = (led == 1) ? L1_B_PIN : L2_B_PIN;
  analogWrite(pinR, r);
  analogWrite(pinG, g);
  analogWrite(pinB, b);
}

void setPreset(int preset) {
  switch (preset) {
    case 1:
      setLED(1, 255, 255, 0); setLED(2, 0, 0, 0);
      setMotor(1, 1);         setMotor(2, -1);
      break;
    case 2:
      setLED(1, 0, 0, 0);    setLED(2, 0, 255, 255);
      setMotor(1, -1);        setMotor(2, 1);
      break;
    case 3:
      stopAll();
      break;
  }
}

void stopAll() {
  setMotor(1, 0); setMotor(2, 0);
  setLED(1, 0, 0, 0); setLED(2, 0, 0, 0);
}

// ============================================================
// OSC 信息查询命令
// ============================================================
void sendClientListOSC(OSCMessage &msg, int addrOffset) {
  if (!USE_AP_MODE) return;

  OSCMessage reply("/info/clients");
  int count = WiFi.softAPgetStationNum();
  reply.add((int32_t)count);

  for (int i = 0; i < MAX_CLIENTS; i++) {
    if (clients[i].active) {
      uint32_t ip = clients[i].ip;
      char macStr[18];
      sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X",
        clients[i].mac[0], clients[i].mac[1], clients[i].mac[2],
        clients[i].mac[3], clients[i].mac[4], clients[i].mac[5]);

      char ipStr[16];
      sprintf(ipStr, "%d.%d.%d.%d",
        ip & 0xFF, (ip >> 8) & 0xFF, (ip >> 16) & 0xFF, (ip >> 24) & 0xFF);

      reply.add(macStr);
      reply.add(ipStr);
    }
  }

  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  reply.send(udp);
  udp.endPacket();
  reply.empty();
}

void sendSelfInfoOSC(OSCMessage &msg, int addrOffset) {
  OSCMessage reply("/info/self");

  reply.add(MDNS_NAME);

  uint8_t mac[6];
  WiFi.macAddress(mac);
  char macStr[18];
  sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X",
    mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  reply.add(macStr);

  char modeStr[10];
  strcpy(modeStr, USE_AP_MODE ? "AP" : "STA");
  reply.add(modeStr);

  char ipStr[16];
  if (USE_AP_MODE || WiFi.status() == WL_CONNECTED) {
    IPAddress ip = USE_AP_MODE ? WiFi.softAPIP() : WiFi.localIP();
    sprintf(ipStr, "%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);
  } else {
    strcpy(ipStr, "0.0.0.0");
  }
  reply.add(ipStr);

  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  reply.send(udp);
  udp.endPacket();
  reply.empty();
}