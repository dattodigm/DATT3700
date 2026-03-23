#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <ESP32Servo.h>
#include <OSCMessage.h>

// ============================================================
// Configuration
// ============================================================
#define USE_AP_MODE false

const char* AP_SSID = "F7OWER";
const char* AP_PASSWORD = "12345678";

const char* STA_SSID = "F7OWER";
const char* STA_PASSWORD = "12345678";

const char* NODE_ID = "face_track_1";
const char* NODE_TYPE = "face_track";
const int OSC_PORT = 8888;

const int FRAME_WIDTH_DEFAULT = 1920;
const int FRAME_HEIGHT_DEFAULT = 1080;

const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2400;
const int SERVO_HZ = 50;

const int SERVO_UPDATE_MS = 20;
const int SERIAL_BAUD = 115200;

// Pan(X) and Tilt(Y) pins for 4 flowers
int pinsX[4] = {18, 21, 23, 26};
int pinsY[4] = {19, 22, 25, 27};

// ============================================================
// Runtime state
// ============================================================
WiFiUDP udp;
Servo servosX[4];
Servo servosY[4];

bool autoTracking = true;
int smoothFactorPct = 40;  // 0-100, larger = faster response
int deadbandDeg = 1;

int targetPan = 90;
int targetTilt = 90;
int currentPan = 90;
int currentTilt = 90;

unsigned long lastServoUpdateMs = 0;

// ============================================================
// Forward declarations
// ============================================================
void setupNetwork();
void setupMDNS();
void setupServos();
void updateServos();
void applyTargetAngles(int pan, int tilt);
void setAllServos(int pan, int tilt);
void parseSerialLine();
void printHelp();

void routeTrackAuto(OSCMessage& msg, int addrOffset);
void routeTrackNorm(OSCMessage& msg, int addrOffset);
void routeTrackXY(OSCMessage& msg, int addrOffset);
void routeTrackCenter(OSCMessage& msg, int addrOffset);
void routeTrackSmooth(OSCMessage& msg, int addrOffset);
void routeFlower1(OSCMessage& msg, int addrOffset);
void routeFlower2(OSCMessage& msg, int addrOffset);
void routeFlower3(OSCMessage& msg, int addrOffset);
void routeFlower4(OSCMessage& msg, int addrOffset);
void routeInfoSelf(OSCMessage& msg, int addrOffset);
void routeInfoServo(OSCMessage& msg, int addrOffset);

// ============================================================
// Utility helpers
// ============================================================
int smoothStep(int currentValue, int targetValue) {
  int delta = targetValue - currentValue;
  if (abs(delta) <= deadbandDeg) {
    return targetValue;
  }

  int step = (abs(delta) * smoothFactorPct) / 100;
  if (step < 1) step = 1;
  if (delta > 0) return currentValue + step;
  return currentValue - step;
}

void setAllServos(int pan, int tilt) {
  pan = constrain(pan, 0, 180);
  tilt = constrain(tilt, 0, 180);
  for (int i = 0; i < 4; i++) {
    servosX[i].write(pan);
    servosY[i].write(tilt);
  }
}

void applyTargetAngles(int pan, int tilt) {
  targetPan = constrain(pan, 0, 180);
  targetTilt = constrain(tilt, 0, 180);
}

void updateServos() {
  unsigned long now = millis();
  if (now - lastServoUpdateMs < (unsigned long)SERVO_UPDATE_MS) {
    return;
  }
  lastServoUpdateMs = now;

  currentPan = smoothStep(currentPan, targetPan);
  currentTilt = smoothStep(currentTilt, targetTilt);
  setAllServos(currentPan, currentTilt);
}

void applyNormTarget(float nx, float ny) {
  nx = constrain(nx, 0.0f, 1.0f);
  ny = constrain(ny, 0.0f, 1.0f);

  // Mirror left-right to match original mapping direction.
  int pan = map((int)(nx * 1000.0f), 0, 1000, 180, 0);
  int tilt = map((int)(ny * 1000.0f), 0, 1000, 180, 0);
  applyTargetAngles(pan, tilt);
}

void applyPixelTarget(int x, int y, int frameW, int frameH) {
  frameW = max(frameW, 1);
  frameH = max(frameH, 1);

  int pan = map(constrain(x, 0, frameW), 0, frameW, 180, 0);
  int tilt = map(constrain(y, 0, frameH), 0, frameH, 180, 0);
  applyTargetAngles(pan, tilt);
}

void printSelfInfo() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  IPAddress ip = USE_AP_MODE ? WiFi.softAPIP() : WiFi.localIP();

  Serial.println("\n=== Face Tracking Node Info ===");
  Serial.printf("Node ID: %s\n", NODE_ID);
  Serial.printf("Node Type: %s\n", NODE_TYPE);
  Serial.printf("IP: %d.%d.%d.%d\n", ip[0], ip[1], ip[2], ip[3]);
  Serial.printf("MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.printf("AutoTracking: %s\n", autoTracking ? "ON" : "OFF");
  Serial.printf("Current Pan/Tilt: %d / %d\n", currentPan, currentTilt);
  Serial.printf("Target Pan/Tilt: %d / %d\n", targetPan, targetTilt);
  Serial.printf("Smoothing: %d%%\n", smoothFactorPct);
  Serial.println("===============================\n");
}

// ============================================================
// Network setup
// ============================================================
void setupNetwork() {
  if (USE_AP_MODE) {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    Serial.print("[Net] AP started, IP: ");
    Serial.println(WiFi.softAPIP());
    return;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(STA_SSID, STA_PASSWORD);

  Serial.print("[Net] Connecting");
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n[Net] Connected, IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[Net] STA failed, fallback to AP mode");
    WiFi.disconnect(true);
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    Serial.print("[Net] AP started, IP: ");
    Serial.println(WiFi.softAPIP());
  }
}

void setupMDNS() {
  if (!MDNS.begin(NODE_ID)) {
    Serial.println("[Net] mDNS failed");
    return;
  }

  // For generic OSC lookup (_osc._udp)
  MDNS.addService("osc", "udp", OSC_PORT);
  MDNS.addServiceTxt("osc", "udp", "node_type", NODE_TYPE);
  MDNS.addServiceTxt("osc", "udp", "node_id", NODE_ID);

  // For project discovery (_datt_flower._tcp)
  MDNS.addService("datt_flower", "tcp", OSC_PORT);
  MDNS.addServiceTxt("datt_flower", "tcp", "node_type", NODE_TYPE);
  MDNS.addServiceTxt("datt_flower", "tcp", "node_id", NODE_ID);

  Serial.printf("[Net] mDNS ready: %s.local\n", NODE_ID);
}

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

  setAllServos(90, 90);
  currentPan = targetPan = 90;
  currentTilt = targetTilt = 90;
}

// ============================================================
// OSC routes
// ============================================================
void routeTrackAuto(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  autoTracking = (msg.getInt(0) != 0);
  Serial.printf("[OSC] /track/auto -> %s\n", autoTracking ? "ON" : "OFF");
}

void routeTrackNorm(OSCMessage& msg, int addrOffset) {
  if (!autoTracking) return;

  float nx = 0.5f;
  float ny = 0.5f;
  if (msg.isFloat(0)) nx = msg.getFloat(0);
  else if (msg.isInt(0)) nx = (float)msg.getInt(0);

  if (msg.isFloat(1)) ny = msg.getFloat(1);
  else if (msg.isInt(1)) ny = (float)msg.getInt(1);

  applyNormTarget(nx, ny);
}

void routeTrackXY(OSCMessage& msg, int addrOffset) {
  if (!autoTracking) return;
  if (!msg.isInt(0) || !msg.isInt(1)) return;

  int x = msg.getInt(0);
  int y = msg.getInt(1);
  int frameW = FRAME_WIDTH_DEFAULT;
  int frameH = FRAME_HEIGHT_DEFAULT;

  if (msg.isInt(2)) frameW = msg.getInt(2);
  if (msg.isInt(3)) frameH = msg.getInt(3);

  applyPixelTarget(x, y, frameW, frameH);
}

void routeTrackCenter(OSCMessage& msg, int addrOffset) {
  applyTargetAngles(90, 90);
  Serial.println("[OSC] /track/center");
}

void routeTrackSmooth(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0)) return;
  smoothFactorPct = constrain(msg.getInt(0), 0, 100);
  Serial.printf("[OSC] /track/smoothing -> %d%%\n", smoothFactorPct);
}

void routeFlowerDirect(OSCMessage& msg, int flowerIdx) {
  if (flowerIdx < 0 || flowerIdx > 3) return;
  if (!msg.isInt(0) || !msg.isInt(1)) return;

  autoTracking = false;
  int pan = constrain(msg.getInt(0), 0, 180);
  int tilt = constrain(msg.getInt(1), 0, 180);

  servosX[flowerIdx].write(pan);
  servosY[flowerIdx].write(tilt);

  currentPan = pan;
  currentTilt = tilt;
  targetPan = pan;
  targetTilt = tilt;

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

  reply.add(WiFi.getMode() == WIFI_AP ? "AP" : "STA");

  IPAddress ip = (WiFi.getMode() == WIFI_AP) ? WiFi.softAPIP() : WiFi.localIP();
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
  reply.add((int32_t)(autoTracking ? 1 : 0));
  reply.add((int32_t)currentPan);
  reply.add((int32_t)currentTilt);
  reply.add((int32_t)targetPan);
  reply.add((int32_t)targetTilt);
  reply.add((int32_t)smoothFactorPct);

  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  reply.send(udp);
  udp.endPacket();
  reply.empty();
}

// ============================================================
// Serial commands
// ============================================================
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
    applyTargetAngles(90, 90);
    return;
  }

  if (line.startsWith("auto")) {
    int v = 0;
    sscanf(line.c_str(), "auto %d", &v);
    autoTracking = (v != 0);
    Serial.printf("[Serial] auto=%d\n", autoTracking ? 1 : 0);
    return;
  }

  if (line.startsWith("smooth")) {
    int v = 40;
    sscanf(line.c_str(), "smooth %d", &v);
    smoothFactorPct = constrain(v, 0, 100);
    Serial.printf("[Serial] smoothing=%d%%\n", smoothFactorPct);
    return;
  }

  if (line.startsWith("norm")) {
    float nx = 0.5f, ny = 0.5f;
    if (sscanf(line.c_str(), "norm %f %f", &nx, &ny) == 2) {
      applyNormTarget(nx, ny);
      Serial.printf("[Serial] norm=%.3f,%.3f\n", nx, ny);
    }
    return;
  }

  // Backward compatible format: x,y
  int commaIdx = line.indexOf(',');
  if (commaIdx > 0) {
    int x = line.substring(0, commaIdx).toInt();
    int y = line.substring(commaIdx + 1).toInt();
    if (autoTracking) {
      applyPixelTarget(x, y, FRAME_WIDTH_DEFAULT, FRAME_HEIGHT_DEFAULT);
      Serial.printf("[Serial] xy=%d,%d\n", x, y);
    }
    return;
  }

  if (line.startsWith("xy")) {
    int x = 0, y = 0, w = FRAME_WIDTH_DEFAULT, h = FRAME_HEIGHT_DEFAULT;
    int parsed = sscanf(line.c_str(), "xy %d %d %d %d", &x, &y, &w, &h);
    if (parsed >= 2) {
      applyPixelTarget(x, y, w, h);
      Serial.printf("[Serial] xy=%d,%d frame=%d,%d\n", x, y, w, h);
    }
    return;
  }

  if (line.startsWith("flower")) {
    int idx = 0, pan = 90, tilt = 90;
    if (sscanf(line.c_str(), "flower%d %d %d", &idx, &pan, &tilt) == 3) {
      if (idx >= 1 && idx <= 4) {
        autoTracking = false;
        servosX[idx - 1].write(constrain(pan, 0, 180));
        servosY[idx - 1].write(constrain(tilt, 0, 180));
        Serial.printf("[Serial] flower%d=%d,%d\n", idx, pan, tilt);
      }
    }
    return;
  }

  Serial.printf("[Serial] Unknown command: %s\n", line.c_str());
}

void printHelp() {
  Serial.println("\n=== Face Tracking Commands ===");
  Serial.println("help                        - show this help");
  Serial.println("info                        - show device info");
  Serial.println("auto <0|1>                  - auto tracking off/on");
  Serial.println("center                      - move all servos to center");
  Serial.println("smooth <0-100>              - tracking smoothing");
  Serial.println("norm <x> <y>                - normalized coordinate (0.0-1.0)");
  Serial.println("xy <x> <y> [w h]            - pixel coordinate");
  Serial.println("x,y                         - legacy pixel coordinate");
  Serial.println("flower<n> <pan> <tilt>      - direct single flower control");
  Serial.println("OSC: /track/auto /track/norm /track/xy /track/center /track/smoothing");
  Serial.println("OSC: /flower1..4 /info/self /info/servo");
  Serial.println("==============================\n");
}

// ============================================================
// Arduino setup / loop
// ============================================================
void setup() {
  Serial.begin(SERIAL_BAUD);
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
      msg.route("/track/norm", routeTrackNorm);
      msg.route("/track/xy", routeTrackXY);
      msg.route("/track/center", routeTrackCenter);
      msg.route("/track/smoothing", routeTrackSmooth);

      msg.route("/flower1", routeFlower1);
      msg.route("/flower2", routeFlower2);
      msg.route("/flower3", routeFlower3);
      msg.route("/flower4", routeFlower4);

      msg.route("/info/self", routeInfoSelf);
      msg.route("/info/servo", routeInfoServo);
    }
  }

  parseSerialLine();
  updateServos();
}

