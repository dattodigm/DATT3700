#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>

// ============================================================
// ⚙️  CONFIG — 所有可调参数都在这里修改
// ============================================================

// --- Station模式配置（连接已有WiFi）---
const char* STA_SSID     = "MisAXNet";
const char* STA_PASSWORD = "AX6000@O26";

// --- mDNS 设备广播名称（局域网内可用 sylvie.local 访问）---
const char* MDNS_NAME = "sylvie";

// --- OSC 端口 ---
const int OSC_PORT = 8888;

const int WIFI_BOOT_CONNECT_ATTEMPTS = 24;
const int WIFI_AUTO_RETRY_ATTEMPTS = 10;
const int WIFI_MANUAL_RETRY_DEFAULT = 6;
const int WIFI_RETRY_DELAY_MS = 500;
const unsigned long WIFI_RETRY_INTERVAL_MS = 6000;

// --- 引脚定义 ---
const int M1_A = 25, M1_B = 26;
const int L1_R = 2,  L1_G = 4,  L1_B_PIN = 5;
const int M2_A = 18, M2_B = 19;
const int L2_R = 12, L2_G = 13, L2_B_PIN = 14;

// ============================================================
// 运行时变量
// ============================================================
WiFiUDP udp;
bool autoMode = true;
unsigned long lastAutoUpdate = 0;
// unsigned long lastClientScan = 0;
int autoState = 0;
unsigned long lastWifiRetryMs = 0;
int wifiManualRetryAttempts = WIFI_MANUAL_RETRY_DEFAULT;
bool mdnsStarted = false;
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
void printWifiStatus();
void manualWifiRetry(int attempts);
void ensureWifiConnected();
void ensureMDNS();
void handleSerialCommand();
void sendClientListOSC(OSCMessage &msg, int addrOffset);
void sendSelfInfoOSC(OSCMessage &msg, int addrOffset);
// ────────────────────────────────────────────────────────────
// ============================================================
// WiFi / mDNS
// ============================================================
bool connectWifiWithAttempts(int attempts, bool verbose) {
  attempts = constrain(attempts, 1, 120);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(false);
  WiFi.begin(STA_SSID, STA_PASSWORD);

  if (verbose) Serial.print("[Net] Connecting");
  for (int i = 0; i < attempts; i++) {
    if (WiFi.status() == WL_CONNECTED) {
      if (verbose) {
        Serial.print("\n[Net] Connected, IP: ");
        Serial.println(WiFi.localIP());
      }
      return true;
    }
    delay(WIFI_RETRY_DELAY_MS);
    if (verbose) Serial.print(".");
  }

  if (verbose) Serial.println("\n[Net] STA connect failed");
  return WiFi.status() == WL_CONNECTED;
}

void setupNetwork() {
  if (!connectWifiWithAttempts(WIFI_BOOT_CONNECT_ATTEMPTS, true)) {
    Serial.println("[Net] Boot without WiFi, auto-retry enabled");
  }
}

void ensureWifiConnected() {
  if (WiFi.status() == WL_CONNECTED) return;
  unsigned long now = millis();
  if (now - lastWifiRetryMs < WIFI_RETRY_INTERVAL_MS) return;
  lastWifiRetryMs = now;
  Serial.println("[Net] WiFi disconnected, retrying...");
  connectWifiWithAttempts(WIFI_AUTO_RETRY_ATTEMPTS, false);
}

void setupMDNS() {
  if (mdnsStarted) return;
  if (WiFi.status() != WL_CONNECTED) return;
  if (!MDNS.begin(MDNS_NAME)) {
    Serial.println("[Net] mDNS failed");
    return;
  }
  MDNS.addService("osc", "udp", OSC_PORT);
  MDNS.addService("datt_flower", "tcp", OSC_PORT);
  MDNS.addServiceTxt("datt_flower", "tcp", "node_type", "sylvie");
  MDNS.addServiceTxt("datt_flower", "tcp", "node_id", MDNS_NAME);
  mdnsStarted = true;
  Serial.printf("[Net] mDNS ready: %s.local\n", MDNS_NAME);
}

void ensureMDNS() {
  if (!mdnsStarted && WiFi.status() == WL_CONNECTED) {
    setupMDNS();
  }
}

// ============================================================
// 打印当前在线客户端（AP 模式）
// ============================================================
void printConnectedClients() {
  Serial.println("[Net] AP client list disabled in STA-only firmware");
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

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("模式：STA (客户端)\n");
    Serial.printf("IP: %d.%d.%d.%d\n",
      WiFi.localIP()[0], WiFi.localIP()[1],
      WiFi.localIP()[2], WiFi.localIP()[3]);
  } else {
    Serial.println("模式：STA (未连接)");
    Serial.println("IP: 未分配");
  }
  Serial.println("====================\n");
}

void printWifiStatus() {
  wl_status_t st = WiFi.status();
  Serial.println("\n=== WiFi Status ===");
  Serial.printf("SSID: %s\n", STA_SSID);
  Serial.printf("Status: %d\n", (int)st);
  if (st == WL_CONNECTED) {
    Serial.printf("IP: %d.%d.%d.%d\n", WiFi.localIP()[0], WiFi.localIP()[1], WiFi.localIP()[2], WiFi.localIP()[3]);
    Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("IP: (not connected)");
  }
  Serial.println("===================\n");
}

void manualWifiRetry(int attempts) {
  wifiManualRetryAttempts = constrain(attempts, 1, 120);
  Serial.printf("[Net] Manual retry, attempts=%d\n", wifiManualRetryAttempts);
  bool ok = connectWifiWithAttempts(wifiManualRetryAttempts, true);
  if (ok) ensureMDNS();
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
    printConnectedClients();
  } else if (line.equals("selfinfo")) {
    printSelfInfo();
  } else if (line.equals("wifi status")) {
    printWifiStatus();
  } else if (line.startsWith("wifi retry")) {
    int attempts = wifiManualRetryAttempts;
    sscanf(line.c_str(), "wifi retry %d", &attempts);
    manualWifiRetry(attempts);
  }
}

// ============================================================
// Setup
// ============================================================
void setup() {
  Serial.begin(115200);

  int pins[] = {M1_A, M1_B, M2_A, M2_B, L1_R, L1_G, L1_B_PIN, L2_R, L2_G, L2_B_PIN};
  for (int p : pins) pinMode(p, OUTPUT);

  setupNetwork();
  setupMDNS();

  udp.begin(OSC_PORT);
  Serial.printf("✅ OSC 监听端口: %d\n", OSC_PORT);
  Serial.println("📋 串口命令: motor1 1 | motor2 -1 | led1 255 0 0 | led2 0 255 255 | auto 0 | preset 2 | wifi status | wifi retry 6");
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
  ensureWifiConnected();
  ensureMDNS();

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
  OSCMessage reply("/info/clients");
  // STA-only firmware: keep endpoint for host compatibility.
  reply.add((int32_t)0);

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
  strcpy(modeStr, "STA");
  reply.add(modeStr);

  char ipStr[16];
  if (WiFi.status() == WL_CONNECTED) {
    IPAddress ip = WiFi.localIP();
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