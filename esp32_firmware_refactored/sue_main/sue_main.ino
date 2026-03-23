/**
 * sue_main.ino - Sue Single-Flower Node with FSM Servo Control
 *                Sue 单花节点 - 有限状态机舵机控制
 *
 * Hardware / 硬件:
 *   - 1× Servo motor (GPIO 18) — petal open/close via L298N or direct
 *   - 1× Red LED (GPIO 22)     — danger indicator
 *   - 1× Green LED (GPIO 23)   — relax indicator
 *
 * FSM States / 有限状态机:
 *   IDLE    → Flower closed, waiting for command / 花朵闭合，等待指令
 *   OPENING → Servo smoothly moving 60° → 120° / 舵机平滑打开
 *   OPENED  → Flower open, holding position / 花朵开放，保持位置
 *   CLOSING → Servo smoothly moving 120° → 60° / 舵机平滑闭合
 *
 * Network / 网络:
 *   WiFi STA/AP + mDNS + UDP/OSC (NO ESPAsyncWebServer)
 *   Default: STA mode (connects to router / 默认客户端模式)
 *
 * OSC Commands / OSC 指令:
 *   /state [danger|relax|idle|alert|calm]  - Set flower state / 设置花朵状态
 *   /angle [value]      - Direct servo angle (0-180) / 直接设置舵机角度
 *   /speed [value]      - Set servo step speed (ms/degree) / 设置舵机速度
 *   /led [r] [g]        - Direct LED control / 直接控制 LED
 *   /stop               - Emergency stop / 紧急停止
 *
 * Constraints / 约束:
 *   ⚠️ NO delay() in loop() — millis() only
 *   ⚠️ No String concatenation in loops
 *   ⚠️ No malloc/new at runtime
 *
 * Note on PID / 关于 PID:
 *   Standard hobby servos have an internal PID controller — they move
 *   to a commanded angle using their own feedback loop. External PID
 *   would require a potentiometer or encoder for position feedback,
 *   which this wiring does not include. The smooth stepping here
 *   provides gentle motion profiles without needing external PID.
 *   标准舵机内部已有 PID 控制器。外部 PID 需要电位器或编码器反馈，
 *   当前接线不包含。此处的平滑步进已能提供柔和运动曲线。
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <ESP32Servo.h>
#include <OSCMessage.h>

// ============================================================
// Network Configuration / 网络配置
// ============================================================
#define USE_AP_MODE false  // false = STA (client), true = AP (hotspot)

// AP mode settings / 热点模式设置
const char* ap_ssid     = "ESP32_Sue";
const char* ap_password = "12345678";

// STA mode settings / 客户端模式设置
// ⚠️ Change these to your actual WiFi credentials before flashing!
// ⚠️ 烧录前请修改为你实际的 WiFi 账号密码！
const char* sta_ssid     = "F7OWER";
const char* sta_password = "12345678";

// Node identification / 节点识别
const char* NODE_ID   = "sue_1";
const char* NODE_TYPE = "sue";
const int   OSC_PORT  = 8888;

// mDNS service / mDNS 服务
const char* MDNS_SERVICE = "_datt_flower";
const char* MDNS_PROTO   = "_tcp";

// STA reconnection / STA 重连
const int   STA_MAX_RETRIES     = 20;
const int   STA_RETRY_INTERVAL  = 500;  // ms
bool        staConnecting       = false;
int         staRetryCount       = 0;
unsigned long lastSTACheckMs    = 0;
bool        networkConnected    = false;

// ============================================================
// Hardware Pins / 硬件引脚
// ============================================================
const int SERVO_PIN = 18;
const int RED_LED   = 22;
const int GREEN_LED = 23;

// ============================================================
// Servo Configuration / 舵机配置
// ============================================================
const int CLOSED_ANGLE = 60;   // Flower closed position / 花朵闭合角度
const int OPEN_ANGLE   = 120;  // Flower open position / 花朵开放角度

// ============================================================
// FSM States / 有限状态机状态
// ============================================================
enum FlowerState {
  STATE_IDLE,     // Closed, waiting / 闭合，等待
  STATE_OPENING,  // Smoothly opening / 平滑打开中
  STATE_OPENED,   // Open, holding / 开放，保持
  STATE_CLOSING   // Smoothly closing / 平滑闭合中
};

// ============================================================
// Global State / 全局状态
// ============================================================
Servo petalServo;
WiFiUDP udp;

FlowerState currentState = STATE_IDLE;
int   currentAngle       = CLOSED_ANGLE;
int   targetAngle        = CLOSED_ANGLE;
int   stepIntervalMs     = 20;   // ms per degree step / 每度步进间隔
unsigned long lastStepMs = 0;    // Last servo step timestamp / 上次步进时间
unsigned long stateEntryMs = 0;  // When current state was entered / 进入当前状态的时间

// Auto-close timer for OPENED state (0 = disabled) / 自动闭合定时器（0=禁用）
unsigned long autoCloseMs = 0;

// ============================================================
// setup() / 初始化
// ============================================================
void setup() {
  Serial.begin(115200);

  Serial.println("\n========================================");
  Serial.println("  DATT3700 Flower Node - Sue");
  Serial.println("  Single-Flower Servo Controller");
  Serial.println("  单花舵机控制节点");
  Serial.println("========================================\n");

  // --- Initialize hardware / 初始化硬件 ---
  // Configure LED pins with LEDC PWM for brightness control / 用 LEDC PWM 配置 LED 引脚
  ledcAttach(RED_LED, 1000, 8);
  ledcAttach(GREEN_LED, 1000, 8);
  ledcWrite(RED_LED, 0);
  ledcWrite(GREEN_LED, 0);

  petalServo.setPeriodHertz(50);
  petalServo.attach(SERVO_PIN, 500, 2400);
  petalServo.write(CLOSED_ANGLE);
  currentAngle = CLOSED_ANGLE;
  targetAngle  = CLOSED_ANGLE;

  Serial.printf("[Sue] Servo on GPIO %d, range %d-%d degrees\n",
                SERVO_PIN, CLOSED_ANGLE, OPEN_ANGLE);
  Serial.printf("[Sue] Red LED: GPIO %d, Green LED: GPIO %d\n",
                RED_LED, GREEN_LED);

  // --- Initialize network / 初始化网络 ---
  setupNetwork();

  // --- Start UDP for OSC / 启动 OSC UDP ---
  udp.begin(OSC_PORT);
  Serial.printf("[Sue] OSC listening on port %d\n", OSC_PORT);

  // --- Print command help / 打印命令帮助 ---
  printHelp();

  Serial.println("[Sue] System ready! / 系统就绪！\n");
}

// ============================================================
// loop() — Non-blocking / 非阻塞主循环
// ⚠️ NO delay() allowed
// ============================================================
void loop() {
  // 1. Network maintenance / 网络维护
  updateNetwork();

  // 2. Process OSC messages / 处理 OSC 消息
  processOSC();

  // 3. FSM servo update / 状态机舵机更新
  updateFSM();

  // 4. Serial debug commands / 串口调试命令
  processSerial();
}

// ============================================================
// Network Setup / 网络设置
// ============================================================
void setupNetwork() {
  if (USE_AP_MODE) {
    Serial.println("[Net] Starting AP mode... / 正在启动热点模式...");
    WiFi.softAP(ap_ssid, ap_password);
    Serial.printf("[Net] AP started. SSID: %s  IP: %s\n",
                  ap_ssid, WiFi.softAPIP().toString().c_str());
    networkConnected = true;

    // Start mDNS immediately in AP mode / AP 模式立即启动 mDNS
    startMDNS();
  } else {
    Serial.printf("[Net] Connecting to: %s\n", sta_ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(sta_ssid, sta_password);
    staConnecting = true;
    staRetryCount = 0;
    lastSTACheckMs = millis();
  }
}

void updateNetwork() {
  if (USE_AP_MODE) return;  // AP mode needs no maintenance / AP 模式无需维护

  unsigned long now = millis();

  if (staConnecting) {
    if (now - lastSTACheckMs >= STA_RETRY_INTERVAL) {
      lastSTACheckMs = now;

      if (WiFi.status() == WL_CONNECTED) {
        networkConnected = true;
        staConnecting = false;
        Serial.printf("[Net] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
        startMDNS();
      } else {
        staRetryCount++;
        Serial.printf("[Net] Connecting... attempt %d/%d\n",
                      staRetryCount, STA_MAX_RETRIES);

        if (staRetryCount >= STA_MAX_RETRIES) {
          Serial.println("[Net] STA failed. Falling back to AP mode...");
          staConnecting = false;
          WiFi.disconnect();
          WiFi.softAP(ap_ssid, ap_password);
          Serial.printf("[Net] AP fallback. SSID: %s  IP: %s\n",
                        ap_ssid, WiFi.softAPIP().toString().c_str());
          networkConnected = true;
          startMDNS();
        }
      }
    }
  } else if (networkConnected && WiFi.status() != WL_CONNECTED) {
    networkConnected = false;
    Serial.println("[Net] Connection lost. Reconnecting...");
    WiFi.reconnect();
    staConnecting = true;
    staRetryCount = 0;
    lastSTACheckMs = millis();
  }
}

void startMDNS() {
  if (!MDNS.begin(NODE_ID)) {
    Serial.println("[Net] mDNS failed");
    return;
  }
  MDNS.addService(MDNS_SERVICE, MDNS_PROTO, OSC_PORT);
  MDNS.addServiceTxt(MDNS_SERVICE, MDNS_PROTO, "node_type", NODE_TYPE);
  MDNS.addServiceTxt(MDNS_SERVICE, MDNS_PROTO, "node_id", NODE_ID);
  Serial.printf("[Net] mDNS: %s.local  Service: %s.%s\n",
                NODE_ID, MDNS_SERVICE, MDNS_PROTO);
}

// ============================================================
// OSC Processing / OSC 处理
// ============================================================
void processOSC() {
  int packetSize = udp.parsePacket();
  if (packetSize <= 0) return;

  OSCMessage msg;
  while (packetSize--) {
    msg.fill(udp.read());
  }

  if (msg.hasError()) {
    Serial.println("[OSC] Message error");
    return;
  }

  char address[64];
  msg.getAddress(address, 0, sizeof(address));
  Serial.printf("[OSC] Received: %s\n", address);

  // Route OSC messages / 路由 OSC 消息
  if (strcmp(address, "/state") == 0) {
    handleStateOSC(msg);
  }
  else if (strcmp(address, "/angle") == 0) {
    if (msg.isInt(0)) {
      int angle = constrain(msg.getInt(0), 0, 180);
      setTargetAngle(angle);
      Serial.printf("[OSC] Direct angle: %d\n", angle);
    }
  }
  else if (strcmp(address, "/speed") == 0) {
    if (msg.isInt(0)) {
      stepIntervalMs = constrain(msg.getInt(0), 1, 200);
      Serial.printf("[OSC] Step speed: %d ms/deg\n", stepIntervalMs);
    }
  }
  else if (strcmp(address, "/led") == 0) {
    if (msg.isInt(0) && msg.isInt(1)) {
      int r = msg.getInt(0);
      int g = msg.getInt(1);
      ledcWrite(RED_LED, constrain(r, 0, 255));
      ledcWrite(GREEN_LED, constrain(g, 0, 255));
      Serial.printf("[OSC] LED: R=%d G=%d\n", r, g);
    }
  }
  else if (strcmp(address, "/stop") == 0) {
    emergencyStop();
  }
}

void handleStateOSC(OSCMessage &msg) {
  // Accept string or int state commands / 接受字符串或整数状态指令
  if (msg.isString(0)) {
    char state[32];
    msg.getString(0, state, sizeof(state));
    applyState(state);
  } else if (msg.isInt(0)) {
    int stateNum = msg.getInt(0);
    switch (stateNum) {
      case 0: applyState("idle");    break;
      case 1: applyState("relax");   break;
      case 2: applyState("danger");  break;
      case 3: applyState("alert");   break;
      case 4: applyState("calm");    break;
      case 5: applyState("breathe"); break;
    }
  }
}

// ============================================================
// State Presets / 状态预设
// ============================================================
void applyState(const char* state) {
  Serial.printf("[Sue] State: %s\n", state);

  if (strcmp(state, "danger") == 0) {
    // Danger: red LED + close flower / 危险：红灯 + 闭合花朵
    ledcWrite(RED_LED, 255);
    ledcWrite(GREEN_LED, 0);
    startClosing();
  }
  else if (strcmp(state, "relax") == 0) {
    // Relax: green LED + open flower / 放松：绿灯 + 开放花朵
    ledcWrite(RED_LED, 0);
    ledcWrite(GREEN_LED, 255);
    startOpening();
  }
  else if (strcmp(state, "idle") == 0) {
    // Idle: all off, close flower / 待机：全灭，闭合花朵
    ledcWrite(RED_LED, 0);
    ledcWrite(GREEN_LED, 0);
    startClosing();
  }
  else if (strcmp(state, "alert") == 0) {
    // Alert: both LEDs on, half-open / 警戒：双灯亮，半开
    ledcWrite(RED_LED, 255);
    ledcWrite(GREEN_LED, 255);
    setTargetAngle((CLOSED_ANGLE + OPEN_ANGLE) / 2);
    currentState = STATE_OPENING;
    stateEntryMs = millis();
  }
  else if (strcmp(state, "calm") == 0) {
    // Calm: green LED, slow open / 平静：绿灯，慢开
    ledcWrite(RED_LED, 0);
    ledcWrite(GREEN_LED, 255);
    stepIntervalMs = 40;  // Slower / 更慢
    startOpening();
  }
  else if (strcmp(state, "breathe") == 0) {
    // Breathe: open then auto-close after 3s / 呼吸：开后 3 秒自动闭合
    ledcWrite(RED_LED, 0);
    ledcWrite(GREEN_LED, 255);
    startOpening();
    autoCloseMs = 3000;
  }
  else {
    Serial.printf("[Sue] Unknown state: %s\n", state);
  }
}

// ============================================================
// FSM Control / 状态机控制
// ============================================================
void startOpening() {
  targetAngle = OPEN_ANGLE;
  currentState = STATE_OPENING;
  stateEntryMs = millis();
}

void startClosing() {
  targetAngle = CLOSED_ANGLE;
  currentState = STATE_CLOSING;
  stateEntryMs = millis();
}

void setTargetAngle(int angle) {
  targetAngle = constrain(angle, 0, 180);
  if (targetAngle > currentAngle) {
    currentState = STATE_OPENING;
  } else if (targetAngle < currentAngle) {
    currentState = STATE_CLOSING;
  }
  stateEntryMs = millis();
}

void updateFSM() {
  unsigned long now = millis();

  switch (currentState) {
    case STATE_IDLE:
      // Nothing to do / 无操作
      break;

    case STATE_OPENING:
      if (now - lastStepMs >= (unsigned long)stepIntervalMs) {
        lastStepMs = now;
        if (currentAngle < targetAngle) {
          currentAngle++;
          petalServo.write(currentAngle);
        } else {
          // Reached target / 到达目标
          currentState = STATE_OPENED;
          stateEntryMs = now;
          Serial.printf("[FSM] Opened at %d degrees\n", currentAngle);
        }
      }
      break;

    case STATE_OPENED:
      // Auto-close timer if set / 自动闭合定时器
      if (autoCloseMs > 0 && (now - stateEntryMs >= autoCloseMs)) {
        autoCloseMs = 0;
        startClosing();
        Serial.println("[FSM] Auto-closing after timer");
      }
      break;

    case STATE_CLOSING:
      if (now - lastStepMs >= (unsigned long)stepIntervalMs) {
        lastStepMs = now;
        if (currentAngle > targetAngle) {
          currentAngle--;
          petalServo.write(currentAngle);
        } else {
          // Reached target / 到达目标
          currentState = STATE_IDLE;
          stateEntryMs = now;
          Serial.printf("[FSM] Closed at %d degrees\n", currentAngle);
        }
      }
      break;
  }
}

void emergencyStop() {
  currentState = STATE_IDLE;
  targetAngle = currentAngle;  // Stop where we are / 原地停止
  ledcWrite(RED_LED, 0);
  ledcWrite(GREEN_LED, 0);
  autoCloseMs = 0;
  Serial.println("[Sue] Emergency stop!");
}

// ============================================================
// Serial Debug / 串口调试
// ============================================================
void processSerial() {
  if (Serial.available() <= 0) return;

  char cmdBuf[64];
  int len = 0;
  while (Serial.available() > 0 && len < (int)(sizeof(cmdBuf) - 1)) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') break;
    cmdBuf[len++] = c;
  }
  cmdBuf[len] = '\0';
  if (len == 0) return;

  // Convert to lowercase / 转换为小写
  for (int i = 0; cmdBuf[i]; i++) {
    if (cmdBuf[i] >= 'A' && cmdBuf[i] <= 'Z')
      cmdBuf[i] += ('a' - 'A');
  }

  // Split command and args / 分割命令和参数
  char* space = strchr(cmdBuf, ' ');
  const char* args = "";
  if (space) {
    *space = '\0';
    args = space + 1;
  }

  if (strcmp(cmdBuf, "danger") == 0) {
    applyState("danger");
  }
  else if (strcmp(cmdBuf, "relax") == 0) {
    applyState("relax");
  }
  else if (strcmp(cmdBuf, "idle") == 0) {
    applyState("idle");
  }
  else if (strcmp(cmdBuf, "alert") == 0) {
    applyState("alert");
  }
  else if (strcmp(cmdBuf, "calm") == 0) {
    applyState("calm");
  }
  else if (strcmp(cmdBuf, "breathe") == 0) {
    applyState("breathe");
  }
  else if (strcmp(cmdBuf, "angle") == 0) {
    int a = atoi(args);
    setTargetAngle(a);
    Serial.printf("[Serial] Target angle: %d\n", a);
  }
  else if (strcmp(cmdBuf, "speed") == 0) {
    stepIntervalMs = constrain(atoi(args), 1, 200);
    Serial.printf("[Serial] Step speed: %d ms/deg\n", stepIntervalMs);
  }
  else if (strcmp(cmdBuf, "led") == 0) {
    int r = 0, g = 0;
    sscanf(args, "%d %d", &r, &g);
    ledcWrite(RED_LED, constrain(r, 0, 255));
    ledcWrite(GREEN_LED, constrain(g, 0, 255));
    Serial.printf("[Serial] LED: R=%d G=%d\n", r, g);
  }
  else if (strcmp(cmdBuf, "status") == 0) {
    const char* stateNames[] = {"IDLE", "OPENING", "OPENED", "CLOSING"};
    Serial.printf("[Status] State: %s  Angle: %d  Target: %d  Speed: %d ms/deg\n",
                  stateNames[currentState], currentAngle, targetAngle, stepIntervalMs);
    Serial.printf("[Status] Network: %s  IP: %s\n",
                  networkConnected ? "connected" : "disconnected",
                  USE_AP_MODE ? WiFi.softAPIP().toString().c_str()
                              : WiFi.localIP().toString().c_str());
  }
  else if (strcmp(cmdBuf, "stop") == 0) {
    emergencyStop();
  }
  else if (strcmp(cmdBuf, "help") == 0 || strcmp(cmdBuf, "?") == 0) {
    printHelp();
  }
  else {
    Serial.printf("[Serial] Unknown: '%s'. Type 'help'.\n", cmdBuf);
  }
}

// ============================================================
// Help Text / 帮助信息
// ============================================================
void printHelp() {
  Serial.println("\n=== Sue Node Commands / 命令列表 ===");
  Serial.println("--- State presets / 状态预设 ---");
  Serial.println("  danger   - Red LED + close / 红灯 + 闭合");
  Serial.println("  relax    - Green LED + open / 绿灯 + 开放");
  Serial.println("  idle     - All off + close / 全灭 + 闭合");
  Serial.println("  alert    - Both LEDs + half-open / 双灯 + 半开");
  Serial.println("  calm     - Green LED + slow open / 绿灯 + 慢开");
  Serial.println("  breathe  - Open then auto-close 3s / 开后3秒自动闭");
  Serial.println("--- Fine control / 精细控制 ---");
  Serial.println("  angle [0-180]  - Set target angle / 设置目标角度");
  Serial.println("  speed [1-200]  - Step interval ms/deg / 步进间隔");
  Serial.println("  led [R] [G]    - LED brightness (0-255) / LED 亮度");
  Serial.println("--- System ---");
  Serial.println("  status   - Show current state / 显示当前状态");
  Serial.println("  stop     - Emergency stop / 紧急停止");
  Serial.println("  help/?   - This help / 帮助");
  Serial.println("--- OSC (via network) ---");
  Serial.println("  /state [danger|relax|idle|alert|calm|breathe]");
  Serial.println("  /state [0-5]   - Same as above by number");
  Serial.println("  /angle [value] - Direct servo angle");
  Serial.println("  /speed [value] - Step speed ms/deg");
  Serial.println("  /led [r] [g]   - LED control");
  Serial.println("  /stop          - Emergency stop");
  Serial.println("==========================================\n");
}
