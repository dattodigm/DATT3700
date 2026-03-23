#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>

// ============================================================
// ⚙️  CONFIGURATION - Modify all parameters here
// ============================================================

// --- Station Mode Configuration (Connect to Existing WiFi) ---
const char* STA_SSID     = "F7OWER";
const char* STA_PASSWORD = "12345678";

// --- mDNS Device Broadcast Name (Access as F7OWER_kait.local on LAN) ---
const char* MDNS_NAME = "F7OWER_kait";

// --- OSC Port ---
const int OSC_PORT = 8888;

// --- Pin Definitions ---
const int MOTOR_PWM_PIN = 22;   // PWM Speed Control
const int MOTOR_DIR_PIN = 23;   // Direction Control

// --- PWM Configuration for Motor ---
const int PWM_FREQ       = 20000;  // 20 kHz PWM frequency (avoid audible noise)
const int PWM_RESOLUTION = 8;      // 8-bit resolution (0-255)

// --- Motor Configuration ---
const int MOTOR_KICK_START_POWER = 255;  // Kick Start Power (100%)
const int MOTOR_KICK_START_DELAY = 30;   // Kick Start Delay (ms)

// ============================================================
// Runtime Variables
// ============================================================
WiFiUDP udp;

// Motor state
struct MotorState {
  int targetSpeed;      // -255 ~ 255 (negative=reverse, positive=forward)
  int currentSpeed;     // Current speed
  unsigned long lastUpdate;
  bool isRunning;
} motorState = {0, 0, 0, false};

// Auto sequence state
struct AutoSequence {
  bool active;
  int sequenceMode;     // Preset mode 1-5
  unsigned long startTime;
  int currentPhase;
  unsigned long phaseStartTime;
} autoSeq = {false, 0, 0, 0, 0};

// ── Forward Declarations ────────────────────────────────────
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
// WiFi Initialization (Station Mode Only)
// ============================================================
void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(STA_SSID, STA_PASSWORD);

  Serial.print("🔗 Connecting to WiFi");
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n✅ WiFi Connected, IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi Connection Failed, Check STA_SSID / STA_PASSWORD");
  }
}

// ============================================================
// mDNS Initialization
// ============================================================
void setupmDNS() {
  if (MDNS.begin(MDNS_NAME)) {
    Serial.printf("✅ mDNS Started: http://%s.local\n", MDNS_NAME);
    MDNS.addService("osc", "udp", OSC_PORT);
  } else {
    Serial.println("❌ mDNS Startup Failed");
  }
}

// ============================================================
// Motor Control (Core Function)
// ============================================================
// speed: -255 ~ 255
// negative = reverse, positive = forward, 0 = stop
void setMotorSpeed(int speed) {
  speed = constrain(speed, -255, 255);

  int direction = (speed >= 0) ? HIGH : LOW;
  int pwmValue = abs(speed);

  digitalWrite(MOTOR_DIR_PIN, direction);

  if (pwmValue > 0) {
    // Kick Start Phase
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
// Motion Mode Library
// ============================================================

// Mode 1: Gentle Sway (back and forth gentle movement)
void sway(int amplitude = 80, int duration = 3000) {
  unsigned long startTime = millis();
  int cycles = duration / 1000;

  for (int i = 0; i < cycles; i++) {
    setMotorSpeed(amplitude);       // Forward
    delay(1000);
    setMotorSpeed(-amplitude);      // Reverse
    delay(1000);
  }
  stopMotor();
}

// Mode 2: Fast Spin (continuous rotation at high speed)
void fastSpin(int duration = 2000) {
  setMotorSpeed(220);
  delay(duration);
  stopMotor();
}

// Mode 3: Pulse Vibrate (rapid trembling effect)
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

// Mode 4: Accelerate Spin (gradually accelerating)
void accelerateSpin(int maxSpeed = 220, int duration = 3000) {
  unsigned long startTime = millis();
  int steps = 15;  // Number of acceleration steps
  int delayPerStep = duration / steps;

  for (int speed = 50; speed <= maxSpeed; speed += (maxSpeed - 50) / steps) {
    setMotorSpeed(speed);
    delay(delayPerStep);
  }
  stopMotor();
}

// Mode 5: Smooth Brake (gradual deceleration)
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

// Mode 6: Pulse Start (progressive startup with pulses)
void pulseStart(int targetSpeed = 150, int duration = 2000) {
  // First: 3 rapid pulses
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
// Execute Preset Motion Mode
// ============================================================
void executeMotionMode(int mode) {
  Serial.printf("📍 Executing Motion Mode: %d\n", mode);

  switch (mode) {
    case 1:
      sway(80, 3000);
      Serial.println("✓ Mode 1: Gentle Sway Completed");
      break;
    case 2:
      fastSpin(2000);
      Serial.println("✓ Mode 2: Fast Spin Completed");
      break;
    case 3:
      vibrate(120, 1000);
      Serial.println("✓ Mode 3: Pulse Vibrate Completed");
      break;
    case 4:
      accelerateSpin(220, 3000);
      Serial.println("✓ Mode 4: Accelerate Spin Completed");
      break;
    case 5:
      smoothBrake(200, 1500);
      Serial.println("✓ Mode 5: Smooth Brake Completed");
      break;
    case 6:
      pulseStart(150, 2000);
      Serial.println("✓ Mode 6: Pulse Start Completed");
      break;
    default:
      stopMotor();
      Serial.println("⚠️ Unknown Motion Mode");
  }
}

// ============================================================
// Auto Sequence Runner
// ============================================================
void runAutoSequence() {
  if (!autoSeq.active) return;

  unsigned long elapsed = millis() - autoSeq.startTime;

  // Simple loop sequence: execute one mode every 10 seconds
  int modeSequence[] = {1, 2, 3, 4, 5};
  int sequenceLength = 5;

  int currentMode = modeSequence[autoSeq.currentPhase % sequenceLength];

  if (elapsed > (autoSeq.currentPhase + 1) * 10000) {
    autoSeq.currentPhase++;
  }
}

// ============================================================
// OSC Route Functions
// ============================================================

// /motor <speed> [-255 ~ 255]
// negative = reverse, positive = forward, 0 = stop
void routeMotor(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    int speed = msg.getInt(0);
    setMotorSpeed(speed);
    Serial.printf("🎚️ Motor Speed Set: %d\n", speed);
  }
}

// /motion <mode> [1-6]
// Execute preset motion mode
void routeMotion(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    int mode = msg.getInt(0);
    executeMotionMode(mode);
  }
}

// /stop
// Stop motor
void routeStop(OSCMessage &msg, int addrOffset) {
  stopMotor();
  Serial.println("⏹️ Motor Stopped");
}

// ============================================================
// Serial Command Parser
// ============================================================
void handleSerialCommand() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();

  if (line.startsWith("motor")) {
    // Format: motor <speed>
    int speed = 0;
    sscanf(line.c_str(), "motor %d", &speed);
    setMotorSpeed(speed);
    Serial.printf("Motor: speed=%d\n", speed);

  } else if (line.startsWith("motion")) {
    // Format: motion <mode>
    int mode = 0;
    sscanf(line.c_str(), "motion %d", &mode);
    executeMotionMode(mode);

  } else if (line.equals("stop")) {
    stopMotor();
    Serial.println("Stopped");

  } else if (line.equals("help")) {
    Serial.println("\n=== Serial Command Help ===");
    Serial.println("motor <speed>  - Set motor speed (-255 ~ 255)");
    Serial.println("motion <mode>  - Execute motion mode (1-6)");
    Serial.println("stop           - Stop motor");
    Serial.println("info           - Show device info");
    Serial.println("help           - Show this help");
    Serial.println("==========================\n");

  } else if (line.equals("info")) {
    Serial.println("\n=== Device Info ===");
    Serial.printf("Device Name: %s\n", MDNS_NAME);
    Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
    uint8_t mac[6];
    WiFi.macAddress(mac);
    Serial.printf("MAC Address: %02X:%02X:%02X:%02X:%02X:%02X\n",
      mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    Serial.printf("OSC Port: %d\n", OSC_PORT);
    Serial.printf("Motor Status: %s (Speed: %d)\n",
      motorState.isRunning ? "Running" : "Stopped",
      motorState.currentSpeed);
    Serial.println("===================\n");
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

  // Initial state
  stopMotor();

  Serial.println("\n========== F7OWER Kait Node v2 ==========");
  Serial.println("Setting up WiFi connection...");

  setupWiFi();
  setupmDNS();

  udp.begin(OSC_PORT);
  Serial.printf("✅ OSC Listening on Port: %d\n", OSC_PORT);
  Serial.println("📋 Serial Commands: motor 100 | motion 1 | stop | info | help");
  Serial.println("==========================================\n");
}

// ============================================================
// Main Loop
// ============================================================
void loop() {
  // OSC Message Handling
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

  // Serial Command Handling
  handleSerialCommand();

  // Auto Sequence (if active)
  runAutoSequence();
}

