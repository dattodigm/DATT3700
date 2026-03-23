#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <ESP32Servo.h>
#include <OSCMessage.h>
#include <math.h>

// ============================================================
// Network / node configuration
// ============================================================
const char* STA_SSID = "F7OWER";
const char* STA_PASSWORD = "12345678";

const char* NODE_ID = "face_track_1";
const char* NODE_TYPE = "face_track";
const int OSC_PORT = 8888;

const int WIFI_BOOT_CONNECT_ATTEMPTS = 24;
const int WIFI_AUTO_RETRY_ATTEMPTS = 10;
const int WIFI_MANUAL_RETRY_DEFAULT = 6;
const int WIFI_RETRY_DELAY_MS = 500;
const unsigned long WIFI_RETRY_INTERVAL_MS = 6000;

// ============================================================
// Servo / tracking configuration
// ============================================================
const int FRAME_WIDTH_DEFAULT = 1920;
const int FRAME_HEIGHT_DEFAULT = 1080;

const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2400;
const int SERVO_HZ = 50;
const int SERVO_UPDATE_MS = 20;
const int SERIAL_BAUD = 115200;
const int SERIAL_TIMEOUT_MS = 20;

const int PAN_MIN_DEFAULT = 20;
const int PAN_MAX_DEFAULT = 160;
const int TILT_MIN_DEFAULT = 20;
const int TILT_MAX_DEFAULT = 160;

const int DEAD_BAND_DEG_DEFAULT = 1;
const int SMOOTH_PCT_DEFAULT = 40;
const int MAX_STEP_DEG_DEFAULT = 4;
const unsigned long TRACK_HOLD_TIMEOUT_MS = 1200;
const float MODE_BLEND_STEP = 0.08f;

// Pan(X) and Tilt(Y) pins for 4 flowers
int pinsX[4] = {18, 21, 23, 26};
int pinsY[4] = {19, 22, 25, 27};

// ============================================================
// Runtime state
// ============================================================
enum ControlMode {
  MODE_MANUAL = 0,
  MODE_TRACKING = 1,
};

WiFiUDP udp;
Servo servosX[4];
Servo servosY[4];

ControlMode controlMode = MODE_TRACKING;
float modeBlend = 1.0f;  // 1.0=tracking, 0.0=manual

int smoothFactorPct = SMOOTH_PCT_DEFAULT;
int deadbandDeg = DEAD_BAND_DEG_DEFAULT;
int maxStepDeg = MAX_STEP_DEG_DEFAULT;

int panMinDeg = PAN_MIN_DEFAULT;
int panMaxDeg = PAN_MAX_DEFAULT;
int tiltMinDeg = TILT_MIN_DEFAULT;
int tiltMaxDeg = TILT_MAX_DEFAULT;

int trackingPan = 90;
int trackingTilt = 90;
int manualPan[4] = {90, 90, 90, 90};
int manualTilt[4] = {90, 90, 90, 90};
int targetPan[4] = {90, 90, 90, 90};
int targetTilt[4] = {90, 90, 90, 90};
float currentPan[4] = {90, 90, 90, 90};
float currentTilt[4] = {90, 90, 90, 90};

unsigned long lastTrackInputMs = 0;
unsigned long lastServoUpdateMs = 0;
unsigned long lastWifiRetryMs = 0;
int wifiManualRetryAttempts = WIFI_MANUAL_RETRY_DEFAULT;
bool mdnsStarted = false;

// ============================================================
// Forward declarations
// ============================================================
void setupNetwork();
void ensureWifiConnected();
bool connectWifiWithAttempts(int attempts, bool verbose);
void setupMDNS();
void ensureMDNS();
void setupServos();
void updateServos();
void updateServoTargets();
void parseSerialLine();
void printHelp();
void printSelfInfo();
void printWifiStatus();
void manualWifiRetry(int attempts);

void routeTrackAuto(OSCMessage& msg, int addrOffset);
void routeTrackMode(OSCMessage& msg, int addrOffset);
void routeTrackNorm(OSCMessage& msg, int addrOffset);
void routeTrackXY(OSCMessage& msg, int addrOffset);
void routeTrackCenter(OSCMessage& msg, int addrOffset);
void routeTrackSmooth(OSCMessage& msg, int addrOffset);
void routeTrackLimits(OSCMessage& msg, int addrOffset);
void routeFlower1(OSCMessage& msg, int addrOffset);
void routeFlower2(OSCMessage& msg, int addrOffset);
void routeFlower3(OSCMessage& msg, int addrOffset);
void routeFlower4(OSCMessage& msg, int addrOffset);
void routeInfoSelf(OSCMessage& msg, int addrOffset);
void routeInfoServo(OSCMessage& msg, int addrOffset);

// ============================================================
// Utility helpers
// ============================================================
float clampf(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

int centerPanDeg() {
  return constrain((panMinDeg + panMaxDeg) / 2, panMinDeg, panMaxDeg);
}

int centerTiltDeg() {
  return constrain((tiltMinDeg + tiltMaxDeg) / 2, tiltMinDeg, tiltMaxDeg);
}

int mapNormToPan(float nx) {
  nx = clampf(nx, 0.0f, 1.0f);
  float span = (float)(panMaxDeg - panMinDeg);
  int pan = (int)round((float)panMaxDeg - (nx * span));
  return constrain(pan, panMinDeg, panMaxDeg);
}

int mapNormToTilt(float ny) {
  ny = clampf(ny, 0.0f, 1.0f);
  float span = (float)(tiltMaxDeg - tiltMinDeg);
  int tilt = (int)round((float)tiltMaxDeg - (ny * span));
  return constrain(tilt, tiltMinDeg, tiltMaxDeg);
}

void clampAllStateToLimits() {
  trackingPan = constrain(trackingPan, panMinDeg, panMaxDeg);
  trackingTilt = constrain(trackingTilt, tiltMinDeg, tiltMaxDeg);
  for (int i = 0; i < 4; i++) {
    manualPan[i] = constrain(manualPan[i], panMinDeg, panMaxDeg);
    manualTilt[i] = constrain(manualTilt[i], tiltMinDeg, tiltMaxDeg);
    targetPan[i] = constrain(targetPan[i], panMinDeg, panMaxDeg);
    targetTilt[i] = constrain(targetTilt[i], tiltMinDeg, tiltMaxDeg);
    currentPan[i] = clampf(currentPan[i], (float)panMinDeg, (float)panMaxDeg);
    currentTilt[i] = clampf(currentTilt[i], (float)tiltMinDeg, (float)tiltMaxDeg);
  }
}

void setControlMode(ControlMode mode) {
  if (controlMode == mode) return;
  controlMode = mode;
  Serial.printf("[Mode] %s\n", controlMode == MODE_TRACKING ? "TRACKING" : "MANUAL");
}

void setTrackByNorm(float nx, float ny) {
  trackingPan = mapNormToPan(nx);
  trackingTilt = mapNormToTilt(ny);
  lastTrackInputMs = millis();
}

void setTrackByPixel(int x, int y, int frameW, int frameH) {
  frameW = max(frameW, 1);
  frameH = max(frameH, 1);
  float nx = (float)constrain(x, 0, frameW) / (float)frameW;
  float ny = (float)constrain(y, 0, frameH) / (float)frameH;
  setTrackByNorm(nx, ny);
}

void setManualFlower(int flowerIdx, int pan, int tilt, bool switchToManual) {
  if (flowerIdx < 0 || flowerIdx > 3) return;
  manualPan[flowerIdx] = constrain(pan, panMinDeg, panMaxDeg);
  manualTilt[flowerIdx] = constrain(tilt, tiltMinDeg, tiltMaxDeg);
  if (switchToManual) setControlMode(MODE_MANUAL);
}

float smoothStep(float currentValue, float targetValue) {
  float delta = targetValue - currentValue;
  if (fabs(delta) <= (float)deadbandDeg) {
    return targetValue;
  }

  float pct = clampf((float)smoothFactorPct / 100.0f, 0.0f, 1.0f);
  float step = fabs(delta) * pct;
  if (step < 0.6f) step = 0.6f;
  if (step > (float)maxStepDeg) step = (float)maxStepDeg;

  if (delta > 0.0f) {
    return min(currentValue + step, targetValue);
  }
  return max(currentValue - step, targetValue);
}

void writeServosNow() {
  for (int i = 0; i < 4; i++) {
    servosX[i].write((int)round(currentPan[i]));
    servosY[i].write((int)round(currentTilt[i]));
  }
}

void updateServoTargets() {
  if (controlMode == MODE_TRACKING) {
    modeBlend = min(1.0f, modeBlend + MODE_BLEND_STEP);
  } else {
    modeBlend = max(0.0f, modeBlend - MODE_BLEND_STEP);
  }

  int desiredTrackPan = trackingPan;
  int desiredTrackTilt = trackingTilt;
  unsigned long now = millis();
  if (now - lastTrackInputMs > TRACK_HOLD_TIMEOUT_MS) {
    desiredTrackPan = centerPanDeg();
    desiredTrackTilt = centerTiltDeg();
  }

  for (int i = 0; i < 4; i++) {
    float mixedPan = ((float)manualPan[i] * (1.0f - modeBlend)) + ((float)desiredTrackPan * modeBlend);
    float mixedTilt = ((float)manualTilt[i] * (1.0f - modeBlend)) + ((float)desiredTrackTilt * modeBlend);
    targetPan[i] = constrain((int)round(mixedPan), panMinDeg, panMaxDeg);
    targetTilt[i] = constrain((int)round(mixedTilt), tiltMinDeg, tiltMaxDeg);
  }
}

void updateServos() {
  unsigned long now = millis();
  if (now - lastServoUpdateMs < (unsigned long)SERVO_UPDATE_MS) return;
  lastServoUpdateMs = now;

  updateServoTargets();
  for (int i = 0; i < 4; i++) {
    currentPan[i] = smoothStep(currentPan[i], (float)targetPan[i]);
    currentTilt[i] = smoothStep(currentTilt[i], (float)targetTilt[i]);
  }
  writeServosNow();
}

void applyAngleLimits(int panMin, int panMax, int tiltMin, int tiltMax) {
  panMinDeg = constrain(panMin, 0, 180);
  panMaxDeg = constrain(panMax, 0, 180);
  tiltMinDeg = constrain(tiltMin, 0, 180);
  tiltMaxDeg = constrain(tiltMax, 0, 180);

  if (panMinDeg > panMaxDeg) {
    int t = panMinDeg;
    panMinDeg = panMaxDeg;
    panMaxDeg = t;
  }
  if (tiltMinDeg > tiltMaxDeg) {
    int t = tiltMinDeg;
    tiltMinDeg = tiltMaxDeg;
    tiltMaxDeg = t;
  }
  clampAllStateToLimits();
  Serial.printf("[Servo] limits pan=%d..%d tilt=%d..%d\n", panMinDeg, panMaxDeg, tiltMinDeg, tiltMaxDeg);
}

void centerAllModes() {
  int cp = centerPanDeg();
  int ct = centerTiltDeg();
  trackingPan = cp;
  trackingTilt = ct;
  for (int i = 0; i < 4; i++) {
    manualPan[i] = cp;
    manualTilt[i] = ct;
    targetPan[i] = cp;
    targetTilt[i] = ct;
  }
}

// ============================================================
// Network setup
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

  if (verbose) {
    Serial.println("\n[Net] STA connect failed");
  }
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

  if (!MDNS.begin(NODE_ID)) {
    Serial.println("[Net] mDNS failed");
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
  if (mdnsStarted) return;
  if (WiFi.status() == WL_CONNECTED) {
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
  Serial.printf("[Net] Manual retry, attempts=%d\n", wifiManualRetryAttempts);
  bool ok = connectWifiWithAttempts(wifiManualRetryAttempts, true);
  if (ok) ensureMDNS();
}

// ============================================================
// Servo setup
// ============================================================
void setupServos() {
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for (int i = 0; i < 4; i++) {
    servosX[i].setPeriodHertz(SERVO_HZ);
    servosY[i].setPeriodHertz(SERVO_HZ);
    servosX[i].attach(pinsX[i], SERVO_MIN_US, SERVO_MAX_US);
    servosY[i].attach(pinsY[i], SERVO_MIN_US, SERVO_MAX_US);
  }

  centerAllModes();
  clampAllStateToLimits();
  writeServosNow();
}

// ============================================================
// OSC routes
// ============================================================
void routeTrackAuto(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  setControlMode(msg.getInt(0) != 0 ? MODE_TRACKING : MODE_MANUAL);
}

void routeTrackMode(OSCMessage& msg, int addrOffset) {
  routeTrackAuto(msg, addrOffset);
}

void routeTrackNorm(OSCMessage& msg, int addrOffset) {
  float nx = 0.5f;
  float ny = 0.5f;
  if (msg.isFloat(0)) nx = msg.getFloat(0);
  else if (msg.isInt(0)) nx = (float)msg.getInt(0);

  if (msg.isFloat(1)) ny = msg.getFloat(1);
  else if (msg.isInt(1)) ny = (float)msg.getInt(1);

  setTrackByNorm(nx, ny);
}

void routeTrackXY(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0) || !msg.isInt(1)) return;
  int x = msg.getInt(0);
  int y = msg.getInt(1);
  int frameW = FRAME_WIDTH_DEFAULT;
  int frameH = FRAME_HEIGHT_DEFAULT;
  if (msg.isInt(2)) frameW = msg.getInt(2);
  if (msg.isInt(3)) frameH = msg.getInt(3);
  setTrackByPixel(x, y, frameW, frameH);
}

void routeTrackCenter(OSCMessage& msg, int addrOffset) {
  centerAllModes();
  Serial.println("[OSC] /track/center");
}

void routeTrackSmooth(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  smoothFactorPct = constrain(msg.getInt(0), 0, 100);
  Serial.printf("[OSC] /track/smoothing -> %d%%\n", smoothFactorPct);
}

void routeTrackLimits(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0) || !msg.isInt(1) || !msg.isInt(2) || !msg.isInt(3)) return;
  applyAngleLimits(msg.getInt(0), msg.getInt(1), msg.getInt(2), msg.getInt(3));
}

void routeFlowerDirect(OSCMessage& msg, int flowerIdx) {
  if (flowerIdx < 0 || flowerIdx > 3) return;
  if (!msg.isInt(0) || !msg.isInt(1)) return;

  int pan = msg.getInt(0);
  int tilt = msg.getInt(1);
  setManualFlower(flowerIdx, pan, tilt, true);
  Serial.printf("[OSC] /flower%d %d %d\n", flowerIdx + 1, pan, tilt);
}

void routeFlower1(OSCMessage& msg, int addrOffset) { routeFlowerDirect(msg, 0); }
void routeFlower2(OSCMessage& msg, int addrOffset) { routeFlowerDirect(msg, 1); }
void routeFlower3(OSCMessage& msg, int addrOffset) { routeFlowerDirect(msg, 2); }
void routeFlower4(OSCMessage& msg, int addrOffset) { routeFlowerDirect(msg, 3); }

void routeInfoSelf(OSCMessage& msg, int addrOffset) {
  OSCMessage reply("/info/self");

  reply.add(NODE_ID);
  uint8_t mac[6];
  WiFi.macAddress(mac);
  char macStr[18];
  sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
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
  reply.add((int32_t)(controlMode == MODE_TRACKING ? 1 : 0));
  reply.add((int32_t)round(currentPan[0]));
  reply.add((int32_t)round(currentTilt[0]));
  reply.add((int32_t)targetPan[0]);
  reply.add((int32_t)targetTilt[0]);
  reply.add((int32_t)smoothFactorPct);
  reply.add((int32_t)panMinDeg);
  reply.add((int32_t)panMaxDeg);
  reply.add((int32_t)tiltMinDeg);
  reply.add((int32_t)tiltMaxDeg);

  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  reply.send(udp);
  udp.endPacket();
  reply.empty();
}

// ============================================================
// Serial commands
// ============================================================
void printSelfInfo() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  IPAddress ip = WiFi.localIP();

  Serial.println("\n=== Face Tracking Node Info ===");
  Serial.printf("Node ID: %s\n", NODE_ID);
  Serial.printf("Node Type: %s\n", NODE_TYPE);
  Serial.printf("Mode: %s\n", controlMode == MODE_TRACKING ? "TRACKING" : "MANUAL");
  Serial.printf("IP: %d.%d.%d.%d\n", ip[0], ip[1], ip[2], ip[3]);
  Serial.printf("MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.printf("Track Pan/Tilt: %d / %d\n", trackingPan, trackingTilt);
  Serial.printf("Blend (tracking): %.2f\n", modeBlend);
  Serial.printf("Limits Pan=%d..%d Tilt=%d..%d\n", panMinDeg, panMaxDeg, tiltMinDeg, tiltMaxDeg);
  Serial.printf("Smooth=%d%% Deadband=%d MaxStep=%d\n", smoothFactorPct, deadbandDeg, maxStepDeg);
  Serial.println("===============================\n");
}

void parseSerialLine() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return;

  if (line.equals("help")) {
    printHelp();
    return;
  }
  if (line.equals("info")) {
    printSelfInfo();
    return;
  }
  if (line.equals("center")) {
    centerAllModes();
    return;
  }

  if (line.equals("wifi status")) {
    printWifiStatus();
    return;
  }
  if (line.startsWith("wifi retry")) {
    int attempts = wifiManualRetryAttempts;
    sscanf(line.c_str(), "wifi retry %d", &attempts);
    manualWifiRetry(attempts);
    return;
  }

  if (line.startsWith("auto")) {
    int v = 1;
    sscanf(line.c_str(), "auto %d", &v);
    setControlMode(v != 0 ? MODE_TRACKING : MODE_MANUAL);
    return;
  }

  if (line.startsWith("mode")) {
    int v = -1;
    if (sscanf(line.c_str(), "mode %d", &v) == 1) {
      setControlMode(v != 0 ? MODE_TRACKING : MODE_MANUAL);
      return;
    }
    if (line.endsWith("track")) {
      setControlMode(MODE_TRACKING);
      return;
    }
    if (line.endsWith("manual")) {
      setControlMode(MODE_MANUAL);
      return;
    }
  }

  if (line.startsWith("smooth")) {
    int v = smoothFactorPct;
    sscanf(line.c_str(), "smooth %d", &v);
    smoothFactorPct = constrain(v, 0, 100);
    Serial.printf("[Serial] smoothing=%d%%\n", smoothFactorPct);
    return;
  }

  if (line.startsWith("deadband")) {
    int v = deadbandDeg;
    sscanf(line.c_str(), "deadband %d", &v);
    deadbandDeg = constrain(v, 0, 20);
    Serial.printf("[Serial] deadband=%d\n", deadbandDeg);
    return;
  }

  if (line.startsWith("step")) {
    int v = maxStepDeg;
    sscanf(line.c_str(), "step %d", &v);
    maxStepDeg = constrain(v, 1, 45);
    Serial.printf("[Serial] maxStep=%d\n", maxStepDeg);
    return;
  }

  if (line.startsWith("limits")) {
    int pMin = panMinDeg, pMax = panMaxDeg, tMin = tiltMinDeg, tMax = tiltMaxDeg;
    if (sscanf(line.c_str(), "limits %d %d %d %d", &pMin, &pMax, &tMin, &tMax) == 4) {
      applyAngleLimits(pMin, pMax, tMin, tMax);
    }
    return;
  }

  if (line.startsWith("norm")) {
    float nx = 0.5f, ny = 0.5f;
    if (sscanf(line.c_str(), "norm %f %f", &nx, &ny) == 2) {
      setTrackByNorm(nx, ny);
      Serial.printf("[Serial] norm=%.3f,%.3f\n", nx, ny);
    }
    return;
  }

  // Backward compatible format: x,y
  int commaIdx = line.indexOf(',');
  if (commaIdx > 0) {
    int x = line.substring(0, commaIdx).toInt();
    int y = line.substring(commaIdx + 1).toInt();
    setTrackByPixel(x, y, FRAME_WIDTH_DEFAULT, FRAME_HEIGHT_DEFAULT);
    Serial.printf("[Serial] xy=%d,%d\n", x, y);
    return;
  }

  if (line.startsWith("xy")) {
    int x = 0, y = 0, w = FRAME_WIDTH_DEFAULT, h = FRAME_HEIGHT_DEFAULT;
    int parsed = sscanf(line.c_str(), "xy %d %d %d %d", &x, &y, &w, &h);
    if (parsed >= 2) {
      setTrackByPixel(x, y, w, h);
      Serial.printf("[Serial] xy=%d,%d frame=%d,%d\n", x, y, w, h);
    }
    return;
  }

  if (line.startsWith("flower")) {
    int idx = 0, pan = 90, tilt = 90;
    if (sscanf(line.c_str(), "flower%d %d %d", &idx, &pan, &tilt) == 3) {
      if (idx >= 1 && idx <= 4) {
        setManualFlower(idx - 1, pan, tilt, true);
        Serial.printf("[Serial] flower%d=%d,%d\n", idx, pan, tilt);
      }
    }
    return;
  }

  Serial.printf("[Serial] Unknown command: %s\n", line.c_str());
}

void printHelp() {
  Serial.println("\n=== Face Tracking Commands ===");
  Serial.println("help                            - show this help");
  Serial.println("info                            - show device info");
  Serial.println("center                          - move all groups to center");
  Serial.println("auto <0|1>                      - MANUAL/TRACKING mode");
  Serial.println("mode <0|1|manual|track>         - mode switch");
  Serial.println("smooth <0-100>                  - smoothing percent");
  Serial.println("deadband <0-20>                 - servo deadband in deg");
  Serial.println("step <1-45>                     - max servo step per update");
  Serial.println("limits <panMin panMax tiltMin tiltMax>");
  Serial.println("norm <x> <y>                    - normalized coordinate (0.0-1.0)");
  Serial.println("xy <x> <y> [w h]                - pixel coordinate");
  Serial.println("x,y                             - legacy pixel coordinate");
  Serial.println("flower<n> <pan> <tilt>          - direct single flower control");
  Serial.println("wifi status                     - print WiFi status");
  Serial.println("wifi retry <attempts>           - manual STA reconnect tries");
  Serial.println("OSC: /track/auto /track/mode /track/norm /track/xy /track/center");
  Serial.println("OSC: /track/smoothing /track/limits /flower1..4 /info/self /info/servo");
  Serial.println("==============================\n");
}

// ============================================================
// Arduino setup / loop
// ============================================================
void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(SERIAL_TIMEOUT_MS);
  Serial.println("\n========== DATT3700 Face Tracking Node ==========");

  setupServos();
  setupNetwork();
  setupMDNS();

  udp.begin(OSC_PORT);
  Serial.printf("[OSC] Listening on %d\n", OSC_PORT);
  printHelp();
}

void loop() {
  int size = udp.parsePacket();
  if (size > 0) {
    OSCMessage msg;
    while (size--) {
      msg.fill(udp.read());
    }

    if (!msg.hasError()) {
      msg.route("/track/auto", routeTrackAuto);
      msg.route("/track/mode", routeTrackMode);
      msg.route("/track/norm", routeTrackNorm);
      msg.route("/track/xy", routeTrackXY);
      msg.route("/track/center", routeTrackCenter);
      msg.route("/track/smoothing", routeTrackSmooth);
      msg.route("/track/limits", routeTrackLimits);

      msg.route("/flower1", routeFlower1);
      msg.route("/flower2", routeFlower2);
      msg.route("/flower3", routeFlower3);
      msg.route("/flower4", routeFlower4);

      msg.route("/info/self", routeInfoSelf);
      msg.route("/info/servo", routeInfoServo);
    }
  }

  parseSerialLine();
  ensureWifiConnected();
  ensureMDNS();
  updateServos();
}
