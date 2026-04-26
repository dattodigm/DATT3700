#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <ESP32Servo.h>
#include <OSCMessage.h>
#include <math.h>

// ============================================================
// Node / network config
// ============================================================
const char* STA_SSID = "F7OWER";
const char* STA_PASSWORD = "12345678";

const char* NODE_ID = "sue_1";
const char* NODE_TYPE = "sue";
const int OSC_PORT = 8888;

const int WIFI_BOOT_CONNECT_ATTEMPTS = 24;
const int WIFI_AUTO_RETRY_ATTEMPTS = 8;
const int WIFI_MANUAL_RETRY_DEFAULT = 6;
const int WIFI_RETRY_DELAY_MS = 500;
const unsigned long WIFI_RETRY_INTERVAL_MS = 7000;

// ============================================================
// Servo config (gravity-aware rope drive)
// ============================================================
Servo petalServo;
const int SERVO_PIN = 4;
const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2400;

// Absolute mechanical safety guard.
const int SERVO_SAFE_MIN_ANGLE = 50;
const int SERVO_SAFE_MAX_ANGLE = 130;

// Practical petal endpoints (OPEN is smaller angle on this build).
const int PETAL_OPEN_ANGLE = 55;
const int PETAL_CLOSED_ANGLE = 125;

const int STEP_INTERVAL_MIN_MS = 2;
const int STEP_INTERVAL_MAX_MS = 50;   // >50 feels too slow on this mechanism
int stepIntervalMs = 16;
int manualStepIntervalMs = 16;

int currentPetalAngle = PETAL_CLOSED_ANGLE;
int targetPetalAngle = PETAL_CLOSED_ANGLE;
unsigned long lastPetalStepMs = 0;

// ============================================================
// Motion state machine
// ============================================================
enum FlowerState {
  FLOWER_REST = 0,
  FLOWER_BLOOM = 1,
  FLOWER_ALERT = 2,
  FLOWER_SOOTHE = 3,
  FLOWER_BREATHE = 4,
  FLOWER_MANUAL = 5
};

enum PulseStage {
  PULSE_NONE = 0,
  PULSE_TO_OPEN = 1,
  PULSE_DWELL_OPEN = 2,
  PULSE_TO_CLOSE = 3,
  PULSE_DWELL_CLOSE = 4
};

struct PulsePattern {
  bool active;
  PulseStage stage;
  int openAngle;
  int closeAngle;
  int totalCycles;
  int completedCycles;
  int finalAngle;
  int dwellOpenMs;
  int dwellCloseMs;
  unsigned long stageStartMs;
} pulse = {false, PULSE_NONE, PETAL_OPEN_ANGLE, PETAL_CLOSED_ANGLE, 0, 0, PETAL_CLOSED_ANGLE, 100, 100, 0};

FlowerState flowerState = FLOWER_REST;
unsigned long lastPatternTuneMs = 0;

// ============================================================
// Tracking input (used as reactive modulation, no LCD eye)
// ============================================================
bool trackEnabled = true;
float trackNormX = 0.5f;
float trackNormY = 0.5f;
unsigned long lastTrackInputMs = 0;
const unsigned long TRACK_INPUT_TIMEOUT_MS = 1400;

// ============================================================
// Network runtime
// ============================================================
WiFiUDP udp;
unsigned long lastWifiRetryMs = 0;
int wifiManualRetryAttempts = WIFI_MANUAL_RETRY_DEFAULT;
bool mdnsStarted = false;
bool wifiDownReported = false;

// ============================================================
// Forward declarations
// ============================================================
float clampf(float value, float low, float high);
int mapOpenPctToAngle(int pct);
float computeTrackIntensity(unsigned long nowMs);
int mapStepFromIntensity(float intensity, int fastMs, int slowMs);
int mapCyclesFromIntensity(float intensity, int minCycles, int maxCycles);
void setTrackNorm(float nx, float ny);
void setTrackPixel(int x, int y, int frameW, int frameH);
void setPetalAngleSafe(int angle, bool smooth = true);
void setPetalOpenPercent(int pct, bool smooth = true);
void startPulsePattern(int openAngle, int closeAngle, int cycles, int dwellOpenMs, int dwellCloseMs, int finalAngle);
void stopPulsePattern();
void startReactivePattern(FlowerState state);
void applyState(const char* state);
void emergencyStop();
void updatePetal();
void updatePulsePattern(unsigned long nowMs);
void updatePetalStep(unsigned long nowMs);
void maybeRetunePattern(unsigned long nowMs);

bool connectWifiWithAttempts(int attempts, bool verbose);
void setupNetwork();
void ensureWifiConnected();
void setupMDNS();
void ensureMDNS();
void printWifiStatus();
void manualWifiRetry(int attempts);

void processOSC();
void parseSerialLine();
void printHelp();
void printSelfInfo();

void routeState(OSCMessage& msg, int addrOffset);
void routeAngle(OSCMessage& msg, int addrOffset);
void routeOpen(OSCMessage& msg, int addrOffset);
void routeSpeed(OSCMessage& msg, int addrOffset);
void routeStop(OSCMessage& msg, int addrOffset);
void routeTrackAuto(OSCMessage& msg, int addrOffset);
void routeTrackNorm(OSCMessage& msg, int addrOffset);
void routeTrackXY(OSCMessage& msg, int addrOffset);
void routeTrackCenter(OSCMessage& msg, int addrOffset);
void routeInfoSelf(OSCMessage& msg, int addrOffset);
void routeInfoServo(OSCMessage& msg, int addrOffset);

// ============================================================
// Helpers
// ============================================================
float clampf(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

int mapOpenPctToAngle(int pct) {
  pct = constrain(pct, 0, 100);
  int span = PETAL_CLOSED_ANGLE - PETAL_OPEN_ANGLE;
  int angle = PETAL_CLOSED_ANGLE - ((span * pct) / 100);
  return constrain(angle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
}

float computeTrackIntensity(unsigned long nowMs) {
  float fallback = 0.35f;
  if (!trackEnabled) return fallback;
  if (lastTrackInputMs == 0 || (nowMs - lastTrackInputMs) > TRACK_INPUT_TIMEOUT_MS) return fallback;

  float x = clampf(trackNormX, 0.0f, 1.0f);
  float y = clampf(trackNormY, 0.0f, 1.0f);
  float dx = fabsf(x - 0.5f) * 2.0f;
  float dy = fabsf(y - 0.5f) * 2.0f;
  float dist = sqrtf(dx * dx + dy * dy) / 1.41421356f;  // 0..1
  float upperBias = clampf(1.0f - y, 0.0f, 1.0f);
  return clampf((dist * 0.7f) + (upperBias * 0.3f), 0.0f, 1.0f);
}

int mapStepFromIntensity(float intensity, int fastMs, int slowMs) {
  intensity = clampf(intensity, 0.0f, 1.0f);
  fastMs = constrain(fastMs, STEP_INTERVAL_MIN_MS, STEP_INTERVAL_MAX_MS);
  slowMs = constrain(slowMs, STEP_INTERVAL_MIN_MS, STEP_INTERVAL_MAX_MS);
  if (fastMs > slowMs) {
    int t = fastMs;
    fastMs = slowMs;
    slowMs = t;
  }
  int value = (int)roundf((float)slowMs - ((float)(slowMs - fastMs) * intensity));
  return constrain(value, STEP_INTERVAL_MIN_MS, STEP_INTERVAL_MAX_MS);
}

int mapCyclesFromIntensity(float intensity, int minCycles, int maxCycles) {
  intensity = clampf(intensity, 0.0f, 1.0f);
  minCycles = max(1, minCycles);
  maxCycles = max(minCycles, maxCycles);
  int value = (int)roundf((float)minCycles + ((float)(maxCycles - minCycles) * intensity));
  return constrain(value, minCycles, maxCycles);
}

void setTrackNorm(float nx, float ny) {
  trackNormX = clampf(nx, 0.0f, 1.0f);
  trackNormY = clampf(ny, 0.0f, 1.0f);
  lastTrackInputMs = millis();
}

void setTrackPixel(int x, int y, int frameW, int frameH) {
  frameW = max(frameW, 1);
  frameH = max(frameH, 1);
  float nx = (float)constrain(x, 0, frameW) / (float)frameW;
  float ny = (float)constrain(y, 0, frameH) / (float)frameH;
  setTrackNorm(nx, ny);
}

// ============================================================
// Servo / petal control
// ============================================================
void setPetalAngleSafe(int angle, bool smooth) {
  int safe = constrain(angle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
  targetPetalAngle = safe;
  if (!smooth) {
    currentPetalAngle = safe;
    petalServo.write(currentPetalAngle);
  }
}

void setPetalOpenPercent(int pct, bool smooth) {
  setPetalAngleSafe(mapOpenPctToAngle(pct), smooth);
}

void stopPulsePattern() {
  pulse.active = false;
  pulse.stage = PULSE_NONE;
  pulse.completedCycles = 0;
}

void startPulsePattern(int openAngle, int closeAngle, int cycles, int dwellOpenMs, int dwellCloseMs, int finalAngle) {
  pulse.openAngle = constrain(openAngle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
  pulse.closeAngle = constrain(closeAngle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
  if (pulse.openAngle > pulse.closeAngle) {
    int t = pulse.openAngle;
    pulse.openAngle = pulse.closeAngle;
    pulse.closeAngle = t;
  }

  pulse.totalCycles = max(1, cycles);
  pulse.completedCycles = 0;
  pulse.finalAngle = constrain(finalAngle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
  pulse.dwellOpenMs = constrain(dwellOpenMs, 0, 800);
  pulse.dwellCloseMs = constrain(dwellCloseMs, 0, 800);
  pulse.stage = PULSE_TO_OPEN;
  pulse.stageStartMs = millis();
  pulse.active = true;
  setPetalAngleSafe(pulse.openAngle, true);
}

void startReactivePattern(FlowerState state) {
  float intensity = computeTrackIntensity(millis());
  int cycles = 3;
  int openA = PETAL_OPEN_ANGLE;
  int closeA = PETAL_CLOSED_ANGLE;
  int dwellOpen = 120;
  int dwellClose = 90;
  int finalA = PETAL_CLOSED_ANGLE;

  if (state == FLOWER_ALERT) {
    stepIntervalMs = mapStepFromIntensity(intensity, 4, 16);
    cycles = mapCyclesFromIntensity(intensity, 3, 7);
    openA = 62;
    closeA = PETAL_CLOSED_ANGLE;
    dwellOpen = (int)roundf(110.0f - intensity * 60.0f);
    dwellClose = (int)roundf(80.0f - intensity * 35.0f);
    finalA = 118;
  } else if (state == FLOWER_SOOTHE) {
    stepIntervalMs = mapStepFromIntensity(intensity, 10, 28);
    cycles = mapCyclesFromIntensity(intensity, 2, 5);
    openA = 78;
    closeA = PETAL_CLOSED_ANGLE;
    dwellOpen = (int)roundf(220.0f - intensity * 80.0f);
    dwellClose = (int)roundf(180.0f - intensity * 60.0f);
    finalA = 115;
  } else {
    stepIntervalMs = mapStepFromIntensity(intensity, 8, 24);
    cycles = mapCyclesFromIntensity(intensity, 4, 8);
    openA = 70;
    closeA = PETAL_CLOSED_ANGLE;
    dwellOpen = (int)roundf(180.0f - intensity * 70.0f);
    dwellClose = (int)roundf(170.0f - intensity * 60.0f);
    finalA = 120;
  }

  startPulsePattern(openA, closeA, cycles, dwellOpen, dwellClose, finalA);
}

void applyState(const char* state) {
  if (!state) return;
  Serial.printf("[SueFix] state=%s\n", state);

  if (strcmp(state, "bloom") == 0 || strcmp(state, "relax") == 0) {
    flowerState = FLOWER_BLOOM;
    stopPulsePattern();
    stepIntervalMs = mapStepFromIntensity(computeTrackIntensity(millis()), 5, 22);
    setPetalAngleSafe(PETAL_OPEN_ANGLE, true);
    return;
  }

  if (strcmp(state, "rest") == 0 || strcmp(state, "idle") == 0) {
    flowerState = FLOWER_REST;
    stopPulsePattern();
    stepIntervalMs = mapStepFromIntensity(computeTrackIntensity(millis()), 8, 30);
    setPetalAngleSafe(PETAL_CLOSED_ANGLE, true);
    return;
  }

  if (strcmp(state, "alert") == 0 || strcmp(state, "danger") == 0) {
    flowerState = FLOWER_ALERT;
    startReactivePattern(FLOWER_ALERT);
    return;
  }

  if (strcmp(state, "soothe") == 0 || strcmp(state, "calm") == 0) {
    flowerState = FLOWER_SOOTHE;
    startReactivePattern(FLOWER_SOOTHE);
    return;
  }

  if (strcmp(state, "breathe") == 0) {
    flowerState = FLOWER_BREATHE;
    startReactivePattern(FLOWER_BREATHE);
    return;
  }
}

void emergencyStop() {
  stopPulsePattern();
  targetPetalAngle = currentPetalAngle;
  Serial.println("[SueFix] emergency stop");
}

void updatePulsePattern(unsigned long nowMs) {
  if (!pulse.active) return;

  if (pulse.stage == PULSE_TO_OPEN) {
    if (currentPetalAngle == pulse.openAngle) {
      pulse.stage = PULSE_DWELL_OPEN;
      pulse.stageStartMs = nowMs;
    }
    return;
  }

  if (pulse.stage == PULSE_DWELL_OPEN) {
    if ((nowMs - pulse.stageStartMs) >= (unsigned long)pulse.dwellOpenMs) {
      pulse.stage = PULSE_TO_CLOSE;
      setPetalAngleSafe(pulse.closeAngle, true);
    }
    return;
  }

  if (pulse.stage == PULSE_TO_CLOSE) {
    if (currentPetalAngle == pulse.closeAngle) {
      pulse.completedCycles++;
      if (pulse.completedCycles >= pulse.totalCycles) {
        stopPulsePattern();
        setPetalAngleSafe(pulse.finalAngle, true);
      } else {
        pulse.stage = PULSE_DWELL_CLOSE;
        pulse.stageStartMs = nowMs;
      }
    }
    return;
  }

  if (pulse.stage == PULSE_DWELL_CLOSE) {
    if ((nowMs - pulse.stageStartMs) >= (unsigned long)pulse.dwellCloseMs) {
      pulse.stage = PULSE_TO_OPEN;
      setPetalAngleSafe(pulse.openAngle, true);
    }
  }
}

void maybeRetunePattern(unsigned long nowMs) {
  if (!pulse.active) return;
  if ((nowMs - lastPatternTuneMs) < 200) return;
  lastPatternTuneMs = nowMs;

  float intensity = computeTrackIntensity(nowMs);
  if (flowerState == FLOWER_ALERT) {
    stepIntervalMs = mapStepFromIntensity(intensity, 4, 16);
    int desiredCycles = mapCyclesFromIntensity(intensity, 3, 7);
    if (desiredCycles > pulse.totalCycles) pulse.totalCycles = desiredCycles;
  } else if (flowerState == FLOWER_SOOTHE) {
    stepIntervalMs = mapStepFromIntensity(intensity, 10, 28);
    int desiredCycles = mapCyclesFromIntensity(intensity, 2, 5);
    if (desiredCycles > pulse.totalCycles) pulse.totalCycles = desiredCycles;
  } else if (flowerState == FLOWER_BREATHE) {
    stepIntervalMs = mapStepFromIntensity(intensity, 8, 24);
    int desiredCycles = mapCyclesFromIntensity(intensity, 4, 8);
    if (desiredCycles > pulse.totalCycles) pulse.totalCycles = desiredCycles;
  }
}

void updatePetalStep(unsigned long nowMs) {
  if ((nowMs - lastPetalStepMs) < (unsigned long)stepIntervalMs) return;
  lastPetalStepMs = nowMs;

  if (currentPetalAngle < targetPetalAngle) {
    currentPetalAngle++;
    petalServo.write(currentPetalAngle);
  } else if (currentPetalAngle > targetPetalAngle) {
    currentPetalAngle--;
    petalServo.write(currentPetalAngle);
  }
}

void updatePetal() {
  unsigned long nowMs = millis();
  maybeRetunePattern(nowMs);
  updatePulsePattern(nowMs);
  updatePetalStep(nowMs);
}

// ============================================================
// Network
// ============================================================
bool connectWifiWithAttempts(int attempts, bool verbose) {
  attempts = constrain(attempts, 1, 120);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(false);
  WiFi.begin(STA_SSID, STA_PASSWORD);

  if (verbose) Serial.printf("[Net] Connecting to %s", STA_SSID);
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

  if (verbose) Serial.println("\n[Net] Connect failed");
  return WiFi.status() == WL_CONNECTED;
}

void setupNetwork() {
  if (!connectWifiWithAttempts(WIFI_BOOT_CONNECT_ATTEMPTS, true)) {
    Serial.println("[Net] Boot without WiFi, auto retry active");
  }
}

void ensureWifiConnected() {
  if (WiFi.status() == WL_CONNECTED) {
    wifiDownReported = false;
    return;
  }

  unsigned long now = millis();
  if (now - lastWifiRetryMs < WIFI_RETRY_INTERVAL_MS) return;
  lastWifiRetryMs = now;

  if (!wifiDownReported) {
    Serial.println("[Net] WiFi disconnected, scheduled retry...");
    wifiDownReported = true;
  }

  bool ok = connectWifiWithAttempts(WIFI_AUTO_RETRY_ATTEMPTS, false);
  if (ok) {
    Serial.print("[Net] WiFi reconnected, IP: ");
    Serial.println(WiFi.localIP());
    wifiDownReported = false;
  } else {
    Serial.println("[Net] Auto retry did not connect");
  }
}

void setupMDNS() {
  if (mdnsStarted) return;
  if (WiFi.status() != WL_CONNECTED) return;
  if (!MDNS.begin(NODE_ID)) {
    Serial.println("[Net] mDNS start failed");
    return;
  }
  MDNS.addService("osc", "udp", OSC_PORT);
  MDNS.addServiceTxt("osc", "udp", "node_type", NODE_TYPE);
  MDNS.addServiceTxt("osc", "udp", "node_id", NODE_ID);
  MDNS.addService("datt_flower", "tcp", OSC_PORT);
  MDNS.addServiceTxt("datt_flower", "tcp", "node_type", NODE_TYPE);
  MDNS.addServiceTxt("datt_flower", "tcp", "node_id", NODE_ID);
  mdnsStarted = true;
  Serial.printf("[Net] mDNS ready: %s.local\n", NODE_ID);
}

void ensureMDNS() {
  if (!mdnsStarted && WiFi.status() == WL_CONNECTED) {
    setupMDNS();
  }
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
  Serial.printf("[Net] Manual retry attempts=%d\n", wifiManualRetryAttempts);
  bool ok = connectWifiWithAttempts(wifiManualRetryAttempts, true);
  if (ok) ensureMDNS();
}

// ============================================================
// OSC routes / processing
// ============================================================
void routeState(OSCMessage& msg, int addrOffset) {
  if (msg.isString(0)) {
    char s[24];
    msg.getString(0, s, sizeof(s));
    applyState(s);
  } else if (msg.isInt(0)) {
    int v = msg.getInt(0);
    if (v == 0) applyState("rest");
    else if (v == 1) applyState("bloom");
    else if (v == 2) applyState("alert");
    else if (v == 3) applyState("soothe");
  }
}

void routeAngle(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  flowerState = FLOWER_MANUAL;
  stopPulsePattern();
  setPetalAngleSafe(msg.getInt(0), true);
  stepIntervalMs = manualStepIntervalMs;
}

void routeOpen(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  flowerState = FLOWER_MANUAL;
  stopPulsePattern();
  setPetalOpenPercent(msg.getInt(0), true);
  stepIntervalMs = manualStepIntervalMs;
}

void routeSpeed(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  manualStepIntervalMs = constrain(msg.getInt(0), STEP_INTERVAL_MIN_MS, STEP_INTERVAL_MAX_MS);
  if (!pulse.active) stepIntervalMs = manualStepIntervalMs;
}

void routeStop(OSCMessage& msg, int addrOffset) {
  emergencyStop();
}

void routeTrackAuto(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  trackEnabled = msg.getInt(0) != 0;
}

void routeTrackNorm(OSCMessage& msg, int addrOffset) {
  float x = msg.isFloat(0) ? msg.getFloat(0) : (msg.isInt(0) ? (float)msg.getInt(0) : 0.5f);
  float y = msg.isFloat(1) ? msg.getFloat(1) : (msg.isInt(1) ? (float)msg.getInt(1) : 0.5f);
  setTrackNorm(x, y);
}

void routeTrackXY(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0) || !msg.isInt(1)) return;
  int x = msg.getInt(0);
  int y = msg.getInt(1);
  int w = msg.isInt(2) ? msg.getInt(2) : 1920;
  int h = msg.isInt(3) ? msg.getInt(3) : 1080;
  setTrackPixel(x, y, w, h);
}

void routeTrackCenter(OSCMessage& msg, int addrOffset) {
  setTrackNorm(0.5f, 0.5f);
}

void routeInfoSelf(OSCMessage& msg, int addrOffset) {
  OSCMessage reply("/info/self");
  reply.add(NODE_ID);
  uint8_t mac[6];
  WiFi.macAddress(mac);
  char macStr[18];
  sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  reply.add(macStr);
  reply.add("STA");
  IPAddress ip = WiFi.localIP();
  char ipStr[16];
  sprintf(ipStr, "%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);
  reply.add(ipStr);
  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  reply.send(udp);
  udp.endPacket();
  reply.empty();
}

void routeInfoServo(OSCMessage& msg, int addrOffset) {
  OSCMessage reply("/info/servo");
  reply.add((int32_t)currentPetalAngle);
  reply.add((int32_t)targetPetalAngle);
  reply.add((int32_t)stepIntervalMs);
  reply.add((int32_t)(pulse.active ? 1 : 0));
  reply.add((int32_t)pulse.totalCycles);
  reply.add((int32_t)pulse.completedCycles);
  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  reply.send(udp);
  udp.endPacket();
  reply.empty();
}

void processOSC() {
  int size = udp.parsePacket();
  if (size <= 0) return;
  OSCMessage msg;
  while (size--) msg.fill(udp.read());
  if (msg.hasError()) return;

  msg.route("/state", routeState);
  msg.route("/angle", routeAngle);
  msg.route("/open", routeOpen);
  msg.route("/speed", routeSpeed);
  msg.route("/stop", routeStop);
  msg.route("/track/auto", routeTrackAuto);
  msg.route("/track/mode", routeTrackAuto);
  msg.route("/track/norm", routeTrackNorm);
  msg.route("/track/xy", routeTrackXY);
  msg.route("/track/center", routeTrackCenter);
  msg.route("/info/self", routeInfoSelf);
  msg.route("/info/servo", routeInfoServo);
}

// ============================================================
// Serial commands
// ============================================================
void parseSerialLine() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return;

  if (line == "help") { printHelp(); return; }
  if (line == "info") { printSelfInfo(); return; }
  if (line == "status") {
    float intensity = computeTrackIntensity(millis());
    Serial.printf(
      "[Status] angle=%d target=%d state=%d pulse=%d cycles=%d/%d speed=%d track=(%.3f,%.3f) I=%.2f\n",
      currentPetalAngle,
      targetPetalAngle,
      (int)flowerState,
      pulse.active ? 1 : 0,
      pulse.completedCycles,
      pulse.totalCycles,
      stepIntervalMs,
      trackNormX,
      trackNormY,
      intensity
    );
    return;
  }

  if (line == "wifi status") { printWifiStatus(); return; }
  if (line.startsWith("wifi retry")) {
    int attempts = wifiManualRetryAttempts;
    sscanf(line.c_str(), "wifi retry %d", &attempts);
    manualWifiRetry(attempts);
    return;
  }

  if (line.startsWith("state ")) { applyState(line.substring(6).c_str()); return; }
  if (line.startsWith("angle ")) {
    flowerState = FLOWER_MANUAL;
    stopPulsePattern();
    setPetalAngleSafe(line.substring(6).toInt(), true);
    stepIntervalMs = manualStepIntervalMs;
    return;
  }
  if (line.startsWith("open ")) {
    flowerState = FLOWER_MANUAL;
    stopPulsePattern();
    setPetalOpenPercent(line.substring(5).toInt(), true);
    stepIntervalMs = manualStepIntervalMs;
    return;
  }
  if (line.startsWith("speed ")) {
    manualStepIntervalMs = constrain(line.substring(6).toInt(), STEP_INTERVAL_MIN_MS, STEP_INTERVAL_MAX_MS);
    if (!pulse.active) stepIntervalMs = manualStepIntervalMs;
    return;
  }
  if (line.startsWith("norm ")) {
    float x = 0.5f, y = 0.5f;
    if (sscanf(line.c_str(), "norm %f %f", &x, &y) == 2) {
      setTrackNorm(x, y);
    }
    return;
  }
  if (line == "track on") { trackEnabled = true; return; }
  if (line == "track off") { trackEnabled = false; return; }
  if (line == "center") { setTrackNorm(0.5f, 0.5f); return; }
  if (line == "stop") { emergencyStop(); return; }
}

void printSelfInfo() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  IPAddress ip = WiFi.localIP();
  Serial.println("\n=== Sue Fix Node Info ===");
  Serial.printf("Node ID: %s\n", NODE_ID);
  Serial.printf("Node Type: %s\n", NODE_TYPE);
  Serial.printf("IP: %d.%d.%d.%d\n", ip[0], ip[1], ip[2], ip[3]);
  Serial.printf("MAC: %02X:%02X:%02X:%02X:%02X:%02X\n", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.printf("Safe angle: %d..%d\n", SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
  Serial.printf("Open/Closed: %d / %d\n", PETAL_OPEN_ANGLE, PETAL_CLOSED_ANGLE);
  Serial.printf("Current/Target: %d / %d\n", currentPetalAngle, targetPetalAngle);
  Serial.printf("State=%d pulse=%d cycles=%d/%d speed=%dms\n", (int)flowerState, pulse.active ? 1 : 0, pulse.completedCycles, pulse.totalCycles, stepIntervalMs);
  Serial.printf("Track enabled=%d norm=(%.3f, %.3f)\n", trackEnabled ? 1 : 0, trackNormX, trackNormY);
  Serial.println("=========================\n");
}

void printHelp() {
  Serial.println("\n=== Sue Fix Commands ===");
  Serial.println("state <rest|bloom|alert|soothe|relax|danger|calm|breathe|idle>");
  Serial.println("open <0-100> | angle <safe-angle> | speed <2-50>");
  Serial.println("norm <x y>  (range 0..1)");
  Serial.println("track on|off | center | stop");
  Serial.println("wifi status | wifi retry <attempts>");
  Serial.println("status | info | help");
  Serial.println("========================\n");
}

// ============================================================
// Arduino setup / loop
// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);
  Serial.println("\n========== DATT3700 Sue Fix Node ==========");

  petalServo.setPeriodHertz(50);
  petalServo.attach(SERVO_PIN, SERVO_MIN_US, SERVO_MAX_US);
  petalServo.write(PETAL_CLOSED_ANGLE);
  currentPetalAngle = PETAL_CLOSED_ANGLE;
  targetPetalAngle = PETAL_CLOSED_ANGLE;

  setupNetwork();
  setupMDNS();
  udp.begin(OSC_PORT);
  Serial.printf("[OSC] Listening on %d\n", OSC_PORT);

  applyState("rest");
  printHelp();
}

void loop() {
  processOSC();
  parseSerialLine();
  ensureWifiConnected();
  ensureMDNS();
  updatePetal();
}

