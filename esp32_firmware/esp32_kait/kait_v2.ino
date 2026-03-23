#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>

// ============================================================
// ⚙️  CONFIG — 所有可调参数都在这里修改
// ============================================================

// --- Station模式配置（连接已有WiFi）---
const char* STA_SSID     = "F7OWER";
const char* STA_PASSWORD = "12345678";

// --- mDNS 设备广播名称（局域网内可用 F7OWER_kait.local 访问）---
const char* MDNS_NAME = "F7OWER_kait";

// --- OSC 端口 ---
const int OSC_PORT = 8888;

// --- 引脚定义 ---
const int MOTOR_PWM_PIN = 22;   // PWM 速度控制
const int MOTOR_DIR_PIN = 23;   // 方向控制

// --- PWM Configuration for motor ---
const int PWM_FREQ       = 20000;  // 20 kHz PWM frequency (避免听觉噪音)
const int PWM_RESOLUTION = 8;      // 8-bit resolution (0-255)

// --- Motor configuration ---
const int MOTOR_KICK_START_POWER = 255;  // 启动冲击功率 (100%)
const int MOTOR_KICK_START_DELAY = 30;   // 启动冲击延时 (ms)

// ============================================================
// 运行时变量
// ============================================================
WiFiUDP udp;

// Motor state / 电机状态
struct MotorState {
  int targetSpeed;      // -255 ~ 255 (负数=反向，正数=正向)
  int currentSpeed;     // 当前速度
  unsigned long lastUpdate;
  bool isRunning;
} motorState = {0, 0, 0, false};

// Auto sequence state / 自动序列状态
struct AutoSequence {
  bool active;
  int sequenceMode;     // 预设模式 1-5
  unsigned long startTime;
  int currentPhase;
  unsigned long phaseStartTime;
} autoSeq = {false, 0, 0, 0, 0};

// ── 前向声明 ────────────────────────────────────────────────
void setMotorSpeed(int speed);
void executeMotionMode(int mode);
void sway(int amplitude, int duration);
void fastSpin(int duration);
void vibrate(int intensity, int duration);
void accelerateSpin(int maxSpeed, int duration);
void smoothBrake(int initialSpeed);
void stopMotor();
void runAutoSequence();
void routeMotor(OSCMessage &msg, int addrOffset);
void routeMotion(OSCMessage &msg, int addrOffset);
void routeStop(OSCMessage &msg, int addrOffset);
void sendSelfInfoOSC();
void handleSerialCommand();
// ────────────────────────────────────────────────────────────

// ============================================================
// WiFi 初始化（Station 模式只）
// ============================================================
void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(STA_SSID, STA_PASSWORD);

  Serial.print("🔗 连接WiFi中");
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n✅ WiFi已连接，IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi连接失败，请检查 STA_SSID / STA_PASSWORD");
  }
}

// ============================================================
// mDNS 初始化
// ============================================================
void setupmDNS() {
  if (MDNS.begin(MDNS_NAME)) {
    Serial.printf("✅ mDNS 已启动: http://%s.local\n", MDNS_NAME);
    MDNS.addService("osc", "udp", OSC_PORT);
  } else {
    Serial.println("❌ mDNS 启动失败");
  }
}

// ============================================================
// 电机控制（核心函数）
// ============================================================
// speed: -255 ~ 255
// 负值 = 反向，正值 = 正向，0 = 停止
void setMotorSpeed(int speed) {
  speed = constrain(speed, -255, 255);

  int direction = (speed >= 0) ? HIGH : LOW;
  int pwmValue = abs(speed);

  digitalWrite(MOTOR_DIR_PIN, direction);

  if (pwmValue > 0) {
    // 启动冲击
    ledcWrite(MOTOR_PWM_PIN, MOTOR_KICK_START_POWER);
    delay(MOTOR_KICK_START_DELAY);
  }

  ledcWrite(MOTOR_PWM_PIN, pwmValue);
  motorState.targetSpeed = speed;
  motorState.currentSpeed = pwmValue;
  motorState.lastUpdate = millis();
  motorState.isRunning = (pwmValue > 0);
}

void stopMotor() {
  digitalWrite(MOTOR_DIR_PIN, HIGH);
  ledcWrite(MOTOR_PWM_PIN, 0);
  motorState.targetSpeed = 0;
  motorState.currentSpeed = 0;
  motorState.isRunning = false;
}

// ============================================================
// 运动模式库
// ============================================================

// 模式 1: 缓慢摇晃（来回摆动）
void sway(int amplitude = 80, int duration = 3000) {
  unsigned long startTime = millis();
  int cycles = duration / 1000;

  for (int i = 0; i < cycles; i++) {
    setMotorSpeed(amplitude);       // 正向
    delay(1000);
    setMotorSpeed(-amplitude);      // 反向
    delay(1000);
  }
  stopMotor();
}

// 模式 2: 快速旋转
void fastSpin(int duration = 2000) {
  setMotorSpeed(220);
  delay(duration);
  stopMotor();
}

// 模式 3: 脉冲抖动（细微颤动效果）
void vibrate(int intensity = 120, int duration = 1000) {
  unsigned long startTime = millis();

  while (millis() - startTime < duration) {
    setMotorSpeed(intensity);
    delay(50);
    setMotorSpeed(-intensity);
    delay(50);
  }
  stopMotor();
}

// 模式 4: 加速螺旋（逐渐加速）
void accelerateSpin(int maxSpeed = 220, int duration = 3000) {
  unsigned long startTime = millis();
  int steps = 15;  // 加速段数
  int delayPerStep = duration / steps;

  for (int speed = 50; speed <= maxSpeed; speed += (maxSpeed - 50) / steps) {
    setMotorSpeed(speed);
    delay(delayPerStep);
  }
  stopMotor();
}

// 模式 5: 减速停止（平滑制动）
void smoothBrake(int initialSpeed = 200, int duration = 1500) {
  unsigned long startTime = millis();
  int steps = 10;
  int delayPerStep = duration / steps;

  for (int speed = initialSpeed; speed > 0; speed -= initialSpeed / steps) {
    setMotorSpeed(speed);
    delay(delayPerStep);
  }
  stopMotor();
}

// 模式 6: 脉冲启动（渐进式启动）
void pulseStart(int targetSpeed = 150, int duration = 2000) {
  // 先快速脉冲3次，然后稳定运行
  for (int i = 0; i < 3; i++) {
    setMotorSpeed(200);
    delay(100);
    setMotorSpeed(0);
    delay(100);
  }
  setMotorSpeed(targetSpeed);
  delay(duration);
  stopMotor();
}

// ============================================================
// 执行预设运动模式
// ============================================================
void executeMotionMode(int mode) {
  Serial.printf("📍 执行运动模式: %d\n", mode);

  switch (mode) {
    case 1:
      sway(80, 3000);
      Serial.println("✓ 模式1: 缓慢摇晃完成");
      break;
    case 2:
      fastSpin(2000);
      Serial.println("✓ 模式2: 快速旋转完成");
      break;
    case 3:
      vibrate(120, 1000);
      Serial.println("✓ 模式3: 脉冲抖动完成");
      break;
    case 4:
      accelerateSpin(220, 3000);
      Serial.println("✓ 模式4: 加速螺旋完成");
      break;
    case 5:
      smoothBrake(200, 1500);
      Serial.println("✓ 模式5: 平滑制动完成");
      break;
    case 6:
      pulseStart(150, 2000);
      Serial.println("✓ 模式6: 脉冲启动完成");
      break;
    default:
      stopMotor();
      Serial.println("⚠️ 未知的运动模式");
  }
}

// ============================================================
// 自动序列运行
// ============================================================
void runAutoSequence() {
  if (!autoSeq.active) return;

  unsigned long elapsed = millis() - autoSeq.startTime;

  // 简单的循环序列：每 10 秒执行一个模式
  int modeSequence[] = {1, 2, 3, 4, 5};
  int sequenceLength = 5;

  int currentMode = modeSequence[autoSeq.currentPhase % sequenceLength];

  if (elapsed > (autoSeq.currentPhase + 1) * 10000) {
    autoSeq.currentPhase++;
  }
}

// ============================================================
// OSC 路由函数
// ============================================================

// /motor <speed> [-255 ~ 255]
// 负数 = 反向，正数 = 正向，0 = 停止
void routeMotor(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    int speed = msg.getInt(0);
    setMotorSpeed(speed);
    Serial.printf("🎚️ 电机速度设置: %d\n", speed);
  }
}

// /motion <mode> [1-6]
// 执行预设运动模式
void routeMotion(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    int mode = msg.getInt(0);
    executeMotionMode(mode);
  }
}

// /stop
// 停止电机
void routeStop(OSCMessage &msg, int addrOffset) {
  stopMotor();
  Serial.println("⏹️ 电机已停止");
}

// ============================================================
// 串口命令解析
// ============================================================
void handleSerialCommand() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();

  if (line.startsWith("motor")) {
    // 格式: motor <speed>
    int speed = 0;
    sscanf(line.c_str(), "motor %d", &speed);
    setMotorSpeed(speed);
    Serial.printf("电机: speed=%d\n", speed);

  } else if (line.startsWith("motion")) {
    // 格式: motion <mode>
    int mode = 0;
    sscanf(line.c_str(), "motion %d", &mode);
    executeMotionMode(mode);

  } else if (line.equals("stop")) {
    stopMotor();
    Serial.println("已停止");

  } else if (line.equals("help")) {
    Serial.println("\n=== 串口命令帮助 ===");
    Serial.println("motor <speed>  - 设置电机速度 (-255 ~ 255)");
    Serial.println("motion <mode>  - 执行运动模式 (1-6)");
    Serial.println("stop           - 停止电机");
    Serial.println("info           - 显示设备信息");
    Serial.println("help           - 显示此帮助");
    Serial.println("====================\n");

  } else if (line.equals("info")) {
    Serial.println("\n=== 设备信息 ===");
    Serial.printf("设备名: %s\n", MDNS_NAME);
    Serial.printf("IP地址: %s\n", WiFi.localIP().toString().c_str());
    uint8_t mac[6];
    WiFi.macAddress(mac);
    Serial.printf("MAC地址: %02X:%02X:%02X:%02X:%02X:%02X\n",
      mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    Serial.printf("OSC端口: %d\n", OSC_PORT);
    Serial.printf("电机状态: %s (速度: %d)\n",
      motorState.isRunning ? "运行中" : "停止",
      motorState.currentSpeed);
    Serial.println("====================\n");
  }
}

// ============================================================
// Setup
// ============================================================
void setup() {
  Serial.begin(115200);

  // Initialize motor pins with LEDC PWM
  ledcAttach(MOTOR_PWM_PIN, PWM_FREQ, PWM_RESOLUTION);
  pinMode(MOTOR_DIR_PIN, OUTPUT);

  // 初始状态
  stopMotor();

  Serial.println("\n========== F7OWER Kait Node v2 ==========");
  Serial.println("设置 WiFi 连接...");

  setupWiFi();
  setupmDNS();

  udp.begin(OSC_PORT);
  Serial.printf("✅ OSC 监听端口: %d\n", OSC_PORT);
  Serial.println("📋 串口命令: motor 100 | motion 1 | stop | info | help");
  Serial.println("==========================================\n");
}

// ============================================================
// Loop
// ============================================================
void loop() {
  // OSC 消息处理
  OSCMessage msg;
  int size = udp.parsePacket();

  if (size > 0) {
    while (size--) {
      msg.fill(udp.read());
    }

    if (!msg.hasError()) {
      msg.route("/motor",  routeMotor);
      msg.route("/motion", routeMotion);
      msg.route("/stop",   routeStop);
    }
  }

  // 串口命令处理
  handleSerialCommand();

  // 自动序列（如果激活）
  runAutoSequence();
}

