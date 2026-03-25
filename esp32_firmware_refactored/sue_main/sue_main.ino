#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <ESP32Servo.h>
#include <OSCMessage.h>
#include <Arduino_GFX_Library.h>
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
const int WIFI_AUTO_RETRY_ATTEMPTS = 10;
const int WIFI_MANUAL_RETRY_DEFAULT = 6;
const int WIFI_RETRY_DELAY_MS = 500;
const unsigned long WIFI_RETRY_INTERVAL_MS = 6000;

// ============================================================
// Display pins (GC9A01 round TFT)
// ============================================================
#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS   19
#define TFT_DC   21
#define TFT_RST  22

Arduino_DataBus* bus = new Arduino_ESP32SPI(TFT_DC, TFT_CS, TFT_SCLK, TFT_MOSI, -1);
Arduino_GFX* panel = new Arduino_GC9A01(bus, TFT_RST, 0);

const int PATCH_X = 52;
const int PATCH_Y = 48;
const int PATCH_W = 136;
const int PATCH_H = 144;
const int EYE_CX = 120;
const int EYE_CY = 120;
const int LCX = EYE_CX - PATCH_X;
const int LCY = EYE_CY - PATCH_Y;

Arduino_GFX* eyeCanvasA = new Arduino_Canvas(PATCH_W, PATCH_H, panel, PATCH_X, PATCH_Y);
Arduino_GFX* eyeCanvasB = new Arduino_Canvas(PATCH_W, PATCH_H, panel, PATCH_X, PATCH_Y);
Arduino_GFX* frontCanvas = eyeCanvasA;
Arduino_GFX* backCanvas = eyeCanvasB;

// ============================================================
// Servo config (physical-safe travel)
// ============================================================
Servo petalServo;
const int SERVO_PIN = 4;
const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2400;
const int SERVO_SAFE_MIN_ANGLE = 66;
const int SERVO_SAFE_MAX_ANGLE = 118;
const int PETAL_CLOSED_ANGLE = 72;
const int PETAL_OPEN_ANGLE = 110;
const int PETAL_ALERT_ANGLE = 88;

enum PetalMode {
  PETAL_IDLE = 0,
  PETAL_MOVING = 1,
  PETAL_BREATHING = 2
};

PetalMode petalMode = PETAL_IDLE;
int currentPetalAngle = PETAL_CLOSED_ANGLE;
int targetPetalAngle = PETAL_CLOSED_ANGLE;
int petalStepIntervalMs = 16;
unsigned long lastPetalStepMs = 0;
int breathMinPct = 35;
int breathMaxPct = 75;
int breathPeriodMs = 3800;
unsigned long breathStartMs = 0;

// ============================================================
// Eye runtime state
// ============================================================
struct EyeState {
  float gazeX;
  float gazeY;
  float targetX;
  float targetY;
  float gazeLimitX;
  float gazeLimitY;
  float manualOpen;
  float pupilSpinPhase;
  bool manualOpenOverride;
  bool trackEnabled;
  bool autoBlink;
  bool autoBreathe;
  bool pupilAutoSpin;
  bool blinkRunning;
  unsigned long blinkStartMs;
  unsigned long blinkDurationMs;
  unsigned long nextBlinkMs;
  unsigned long lastTrackInputMs;
};

EyeState eye = {
  0.0f, 0.0f,
  0.0f, 0.0f,
  1.0f, 1.0f,
  1.0f,
  0.0f,
  false,
  true, true, true, true,
  false, 0, 180, 0, 0
};

const unsigned long EYE_FRAME_INTERVAL_MS = 33;
const unsigned long TRACK_HOLD_TIMEOUT_MS = 1400;
unsigned long lastEyeFrameMs = 0;

// ============================================================
// Network runtime
// ============================================================
WiFiUDP udp;
unsigned long lastWifiRetryMs = 0;
int wifiManualRetryAttempts = WIFI_MANUAL_RETRY_DEFAULT;
bool mdnsStarted = false;

// ============================================================
// Colors
// ============================================================
const uint16_t COLOR_BLACK = 0x0000;
const uint16_t COLOR_WHITE = 0xFFFF;
const uint16_t COLOR_SCLERA = 0xEF7D;
const uint16_t COLOR_IRIS_DARK = 0x0015;
const uint16_t COLOR_IRIS_MID = 0x027F;
const uint16_t COLOR_IRIS_LIGHT = 0x3DFF;
const uint16_t COLOR_SHADOW = 0x4208;
const uint16_t COLOR_LID = 0x20C4;

// ============================================================
// Forward declarations
// ============================================================
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

void setPetalOpenPercent(int pct, bool smooth = true);
void setPetalAngleSafe(int angle, bool smooth = true);
void startPetalBreathe(int minPct, int maxPct, int periodMs);
void stopPetalBreathe();
void updatePetal();
void applyState(const char* state);
void emergencyStop();

void setTrackNorm(float nx, float ny);
void setTrackPixel(int x, int y, int frameW, int frameH);
void setManualEyeOpenPercent(int pct);
void setManualEyeLook(float x, float y);
void updateEye(bool force = false);
void drawEyeFrame(
  Arduino_GFX* c,
  float gazeX,
  float gazeY,
  float openFactor,
  float breatheScale,
  float breatheDrift,
  float pupilSpinPhase,
  bool pupilAutoSpin
);
void drawStaticBackground();
unsigned long chooseNextBlinkDelayMs();

// OSC routes
void routeState(OSCMessage& msg, int addrOffset);
void routeAngle(OSCMessage& msg, int addrOffset);
void routeOpen(OSCMessage& msg, int addrOffset);
void routeSpeed(OSCMessage& msg, int addrOffset);
void routeStop(OSCMessage& msg, int addrOffset);
void routeTrackAuto(OSCMessage& msg, int addrOffset);
void routeTrackNorm(OSCMessage& msg, int addrOffset);
void routeTrackXY(OSCMessage& msg, int addrOffset);
void routeTrackCenter(OSCMessage& msg, int addrOffset);
void routeEyeLook(OSCMessage& msg, int addrOffset);
void routeEyeOpen(OSCMessage& msg, int addrOffset);
void routeEyeBlink(OSCMessage& msg, int addrOffset);
void routeEyeBreathe(OSCMessage& msg, int addrOffset);
void routeEyeLimits(OSCMessage& msg, int addrOffset);
void routeEyePupilAuto(OSCMessage& msg, int addrOffset);
void routeInfoSelf(OSCMessage& msg, int addrOffset);
void routeInfoServo(OSCMessage& msg, int addrOffset);

float clampf(float v, float lo, float hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

int mapOpenPctToAngle(int pct) {
  pct = constrain(pct, 0, 100);
  int angle = PETAL_CLOSED_ANGLE + ((PETAL_OPEN_ANGLE - PETAL_CLOSED_ANGLE) * pct) / 100;
  return constrain(angle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
}

unsigned long chooseNextBlinkDelayMs() {
  return (unsigned long)random(2500, 6800);
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
  Serial.printf("[Net] Manual retry, attempts=%d\n", wifiManualRetryAttempts);
  bool ok = connectWifiWithAttempts(wifiManualRetryAttempts, true);
  if (ok) ensureMDNS();
}

// ============================================================
// Petal / state control
// ============================================================
void setPetalAngleSafe(int angle, bool smooth) {
  int safe = constrain(angle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
  targetPetalAngle = safe;
  if (!smooth) {
    currentPetalAngle = safe;
    petalServo.write(currentPetalAngle);
    petalMode = PETAL_IDLE;
  } else {
    petalMode = PETAL_MOVING;
  }
}

void setPetalOpenPercent(int pct, bool smooth) {
  setPetalAngleSafe(mapOpenPctToAngle(pct), smooth);
}

void startPetalBreathe(int minPct, int maxPct, int periodMs) {
  breathMinPct = constrain(minPct, 0, 100);
  breathMaxPct = constrain(maxPct, 0, 100);
  if (breathMinPct > breathMaxPct) {
    int t = breathMinPct;
    breathMinPct = breathMaxPct;
    breathMaxPct = t;
  }
  breathPeriodMs = constrain(periodMs, 800, 12000);
  breathStartMs = millis();
  petalMode = PETAL_BREATHING;
}

void stopPetalBreathe() {
  if (petalMode == PETAL_BREATHING) {
    petalMode = PETAL_IDLE;
  }
}

void updatePetal() {
  unsigned long now = millis();
  if (petalMode == PETAL_BREATHING) {
    float phase = (float)(now - breathStartMs) / (float)breathPeriodMs;
    float wave = 0.5f + 0.5f * sinf(phase * 2.0f * PI);
    int pct = breathMinPct + (int)roundf((float)(breathMaxPct - breathMinPct) * wave);
    int angle = mapOpenPctToAngle(pct);
    currentPetalAngle = angle;
    targetPetalAngle = angle;
    petalServo.write(angle);
    return;
  }

  if (petalMode != PETAL_MOVING) return;
  if (now - lastPetalStepMs < (unsigned long)petalStepIntervalMs) return;
  lastPetalStepMs = now;

  if (currentPetalAngle < targetPetalAngle) {
    currentPetalAngle++;
    petalServo.write(currentPetalAngle);
  } else if (currentPetalAngle > targetPetalAngle) {
    currentPetalAngle--;
    petalServo.write(currentPetalAngle);
  } else {
    petalMode = PETAL_IDLE;
  }
}

void applyState(const char* state) {
  if (!state) return;
  Serial.printf("[Sue] state=%s\n", state);

  if (strcmp(state, "bloom") == 0 || strcmp(state, "relax") == 0) {
    stopPetalBreathe();
    petalStepIntervalMs = 18;
    setPetalOpenPercent(95, true);
    eye.trackEnabled = true;
    eye.autoBlink = true;
    eye.autoBreathe = true;
    eye.manualOpenOverride = false;
  } else if (strcmp(state, "alert") == 0 || strcmp(state, "danger") == 0) {
    stopPetalBreathe();
    petalStepIntervalMs = 8;
    setPetalAngleSafe(PETAL_ALERT_ANGLE, true);
    eye.trackEnabled = true;
    eye.autoBlink = true;
    eye.autoBreathe = false;
    eye.manualOpenOverride = true;
    eye.manualOpen = 0.92f;
  } else if (strcmp(state, "soothe") == 0 || strcmp(state, "calm") == 0) {
    petalStepIntervalMs = 24;
    startPetalBreathe(45, 78, 4200);
    eye.trackEnabled = true;
    eye.autoBlink = true;
    eye.autoBreathe = true;
    eye.manualOpenOverride = false;
  } else if (strcmp(state, "breathe") == 0) {
    petalStepIntervalMs = 20;
    startPetalBreathe(30, 85, 3600);
    eye.trackEnabled = true;
    eye.autoBlink = true;
    eye.autoBreathe = true;
    eye.manualOpenOverride = false;
  } else if (strcmp(state, "rest") == 0 || strcmp(state, "idle") == 0) {
    stopPetalBreathe();
    petalStepIntervalMs = 28;
    setPetalOpenPercent(15, true);
    eye.trackEnabled = false;
    eye.autoBlink = true;
    eye.autoBreathe = true;
    eye.manualOpenOverride = false;
    eye.targetX = 0.0f;
    eye.targetY = 0.0f;
  }
}

void emergencyStop() {
  petalMode = PETAL_IDLE;
  targetPetalAngle = currentPetalAngle;
  eye.trackEnabled = false;
  eye.targetX = 0.0f;
  eye.targetY = 0.0f;
  Serial.println("[Sue] emergency stop");
}

// ============================================================
// Eye update / render
// ============================================================
void setTrackNorm(float nx, float ny) {
  nx = clampf(nx, 0.0f, 1.0f);
  ny = clampf(ny, 0.0f, 1.0f);
  eye.targetX = clampf(((nx * 2.0f) - 1.0f) * eye.gazeLimitX, -1.0f, 1.0f);
  eye.targetY = clampf(((ny * 2.0f) - 1.0f) * eye.gazeLimitY, -1.0f, 1.0f);
  eye.lastTrackInputMs = millis();
}

void setTrackPixel(int x, int y, int frameW, int frameH) {
  frameW = max(frameW, 1);
  frameH = max(frameH, 1);
  float nx = (float)constrain(x, 0, frameW) / (float)frameW;
  float ny = (float)constrain(y, 0, frameH) / (float)frameH;
  setTrackNorm(nx, ny);
}

void setManualEyeOpenPercent(int pct) {
  eye.manualOpenOverride = true;
  eye.manualOpen = clampf((float)constrain(pct, 0, 100) / 100.0f, 0.03f, 1.0f);
}

void setManualEyeLook(float x, float y) {
  eye.trackEnabled = false;
  eye.targetX = clampf(x * eye.gazeLimitX, -1.0f, 1.0f);
  eye.targetY = clampf(y * eye.gazeLimitY, -1.0f, 1.0f);
}

void drawEyeFrame(
  Arduino_GFX* c,
  float gazeX,
  float gazeY,
  float openFactor,
  float breatheScale,
  float breatheDrift,
  float pupilSpinPhase,
  bool pupilAutoSpin
) {
  int irisCx = LCX + (int)roundf(gazeX * 23.0f);
  int irisCy = LCY + (int)roundf(gazeY * 18.0f + breatheDrift);
  int irisOuter = (int)roundf(30.0f * breatheScale);
  int irisMid = (int)roundf(23.0f * breatheScale);
  int irisInner = (int)roundf(14.0f * breatheScale);
  int pupilR = (int)roundf(11.0f * breatheScale);
  int pupilCx = irisCx;
  int pupilCy = irisCy;
  int hiCx = pupilCx - 4;
  int hiCy = pupilCy - 6;

  if (pupilAutoSpin) {
    // Pupil/highlight-only orbit amount is driven by lid open factor.
    float orbitR = 1.2f + (1.0f - openFactor) * 4.8f;
    float dx = orbitR * cosf(pupilSpinPhase);
    float dy = orbitR * sinf(pupilSpinPhase * 0.85f + 0.45f);
    pupilCx += (int)roundf(dx);
    pupilCy += (int)roundf(dy);
    hiCx = pupilCx + (int)roundf((orbitR + 1.2f) * cosf(pupilSpinPhase + 1.85f));
    hiCy = pupilCy + (int)roundf((orbitR + 0.8f) * sinf(pupilSpinPhase + 2.2f));
  }

  c->fillScreen(COLOR_BLACK);
  c->fillCircle(LCX, LCY, 66, COLOR_SCLERA);
  c->fillRoundRect(20, 14, PATCH_W - 40, 18, 9, COLOR_SHADOW);
  c->fillCircle(irisCx, irisCy, irisOuter, COLOR_IRIS_DARK);
  c->fillCircle(irisCx, irisCy, irisMid, COLOR_IRIS_MID);
  c->fillCircle(irisCx, irisCy, irisInner, COLOR_IRIS_LIGHT);
  c->fillCircle(pupilCx, pupilCy, pupilR, COLOR_BLACK);
  c->fillCircle(hiCx, hiCy, 4, COLOR_WHITE);

  openFactor = clampf(openFactor, 0.02f, 1.0f);
  int coverPx = (int)roundf((1.0f - openFactor) * 66.0f);
  int topEdge = (LCY - 66) + coverPx;
  int botEdge = (LCY + 66) - coverPx;
  c->fillRect(0, 0, PATCH_W, max(0, topEdge), COLOR_BLACK);
  c->fillRect(0, max(0, botEdge), PATCH_W, PATCH_H - max(0, botEdge), COLOR_BLACK);
  c->drawFastHLine(0, constrain(topEdge, 0, PATCH_H - 1), PATCH_W, COLOR_LID);
  c->drawFastHLine(0, constrain(botEdge, 0, PATCH_H - 1), PATCH_W, COLOR_LID);
}

void drawStaticBackground() {
  panel->fillScreen(COLOR_BLACK);
}

void updateEye(bool force) {
  unsigned long now = millis();
  unsigned long dtMs = (lastEyeFrameMs > 0) ? (now - lastEyeFrameMs) : EYE_FRAME_INTERVAL_MS;
  if (!force && now - lastEyeFrameMs < EYE_FRAME_INTERVAL_MS) return;
  lastEyeFrameMs = now;

  if (eye.trackEnabled && (now - eye.lastTrackInputMs > TRACK_HOLD_TIMEOUT_MS)) {
    eye.targetX = 0.0f;
    eye.targetY = 0.0f;
  }

  eye.gazeX += (eye.targetX - eye.gazeX) * 0.18f;
  eye.gazeY += (eye.targetY - eye.gazeY) * 0.18f;

  if (eye.autoBlink && !eye.blinkRunning && now >= eye.nextBlinkMs) {
    eye.blinkRunning = true;
    eye.blinkStartMs = now;
  }

  float blinkOpen = 1.0f;
  if (eye.blinkRunning) {
    float p = (float)(now - eye.blinkStartMs) / (float)eye.blinkDurationMs;
    if (p >= 1.0f) {
      eye.blinkRunning = false;
      eye.nextBlinkMs = now + chooseNextBlinkDelayMs();
      blinkOpen = 1.0f;
    } else {
      blinkOpen = 1.0f - sinf(p * PI);
      blinkOpen = clampf(blinkOpen, 0.04f, 1.0f);
    }
  }

  float breatheScale = 1.0f;
  float breatheDrift = 0.0f;
  if (eye.autoBreathe) {
    float phase = (float)now / 2400.0f;
    breatheScale = 1.0f + 0.04f * sinf(phase * 2.0f * PI);
    breatheDrift = 1.6f * sinf(phase * PI);
  }

  float openBase = eye.manualOpenOverride ? eye.manualOpen : 1.0f;
  float openFactor = clampf(openBase * blinkOpen, 0.02f, 1.0f);

  if (eye.pupilAutoSpin) {
    float spinSpeed = 0.65f + ((1.0f - openFactor) * 2.8f);
    eye.pupilSpinPhase += spinSpeed * ((float)dtMs / 1000.0f);
    if (eye.pupilSpinPhase > (2.0f * PI)) {
      eye.pupilSpinPhase = fmodf(eye.pupilSpinPhase, 2.0f * PI);
    }
  }

  drawEyeFrame(
    backCanvas,
    eye.gazeX,
    eye.gazeY,
    openFactor,
    breatheScale,
    breatheDrift,
    eye.pupilSpinPhase,
    eye.pupilAutoSpin
  );
  ((Arduino_Canvas*)backCanvas)->flush();
  Arduino_GFX* tmp = frontCanvas;
  frontCanvas = backCanvas;
  backCanvas = tmp;
}

// ============================================================
// OSC
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

void routeAngle(OSCMessage& msg, int addrOffset) { if (msg.isInt(0)) setPetalAngleSafe(msg.getInt(0), true); }
void routeOpen(OSCMessage& msg, int addrOffset) { if (msg.isInt(0)) setPetalOpenPercent(msg.getInt(0), true); }
void routeSpeed(OSCMessage& msg, int addrOffset) { if (msg.isInt(0)) petalStepIntervalMs = constrain(msg.getInt(0), 2, 120); }
void routeStop(OSCMessage& msg, int addrOffset) { emergencyStop(); }
void routeTrackAuto(OSCMessage& msg, int addrOffset) { if (msg.isInt(0)) eye.trackEnabled = msg.getInt(0) != 0; }
void routeTrackNorm(OSCMessage& msg, int addrOffset) {
  float x = msg.isFloat(0) ? msg.getFloat(0) : (msg.isInt(0) ? (float)msg.getInt(0) : 0.5f);
  float y = msg.isFloat(1) ? msg.getFloat(1) : (msg.isInt(1) ? (float)msg.getInt(1) : 0.5f);
  setTrackNorm(x, y);
}
void routeTrackXY(OSCMessage& msg, int addrOffset) {
  if (!msg.isInt(0) || !msg.isInt(1)) return;
  int x = msg.getInt(0), y = msg.getInt(1);
  int w = msg.isInt(2) ? msg.getInt(2) : 1920;
  int h = msg.isInt(3) ? msg.getInt(3) : 1080;
  setTrackPixel(x, y, w, h);
}
void routeTrackCenter(OSCMessage& msg, int addrOffset) { eye.targetX = 0.0f; eye.targetY = 0.0f; }
void routeEyeLook(OSCMessage& msg, int addrOffset) {
  float x = msg.isFloat(0) ? msg.getFloat(0) : (msg.isInt(0) ? (float)msg.getInt(0) / 100.0f : 0.0f);
  float y = msg.isFloat(1) ? msg.getFloat(1) : (msg.isInt(1) ? (float)msg.getInt(1) / 100.0f : 0.0f);
  setManualEyeLook(x, y);
}
void routeEyeOpen(OSCMessage& msg, int addrOffset) { if (msg.isInt(0)) setManualEyeOpenPercent(msg.getInt(0)); }
void routeEyeBlink(OSCMessage& msg, int addrOffset) { if (msg.isInt(0)) eye.autoBlink = msg.getInt(0) != 0; }
void routeEyeBreathe(OSCMessage& msg, int addrOffset) { if (msg.isInt(0)) eye.autoBreathe = msg.getInt(0) != 0; }
void routeEyeLimits(OSCMessage& msg, int addrOffset) {
  int lx = msg.isInt(0) ? msg.getInt(0) : 100;
  int ly = msg.isInt(1) ? msg.getInt(1) : lx;
  eye.gazeLimitX = clampf((float)constrain(lx, 10, 100) / 100.0f, 0.1f, 1.0f);
  eye.gazeLimitY = clampf((float)constrain(ly, 10, 100) / 100.0f, 0.1f, 1.0f);
}
void routeEyePupilAuto(OSCMessage& msg, int addrOffset) {
  if (msg.isInt(0)) eye.pupilAutoSpin = msg.getInt(0) != 0;
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
  udp.beginPacket(udp.remoteIP(), udp.remotePort()); reply.send(udp); udp.endPacket(); reply.empty();
}

void routeInfoServo(OSCMessage& msg, int addrOffset) {
  OSCMessage reply("/info/servo");
  reply.add((int32_t)currentPetalAngle);
  reply.add((int32_t)targetPetalAngle);
  reply.add((int32_t)petalStepIntervalMs);
  reply.add((int32_t)(eye.trackEnabled ? 1 : 0));
  udp.beginPacket(udp.remoteIP(), udp.remotePort()); reply.send(udp); udp.endPacket(); reply.empty();
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
  msg.route("/eye/look", routeEyeLook);
  msg.route("/eye/open", routeEyeOpen);
  msg.route("/eye/blink", routeEyeBlink);
  msg.route("/eye/breathe", routeEyeBreathe);
  msg.route("/eye/limits", routeEyeLimits);
  msg.route("/eye/pupil_auto", routeEyePupilAuto);
  msg.route("/info/self", routeInfoSelf);
  msg.route("/info/servo", routeInfoServo);
}

// ============================================================
// Serial
// ============================================================
void parseSerialLine() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return;

  if (line == "help") { printHelp(); return; }
  if (line == "info") { printSelfInfo(); return; }
  if (line == "status") {
    Serial.printf("[Status] angle=%d target=%d mode=%d eye=(%.2f,%.2f)\n", currentPetalAngle, targetPetalAngle, (int)petalMode, eye.gazeX, eye.gazeY);
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
  if (line.startsWith("angle ")) { setPetalAngleSafe(line.substring(6).toInt(), true); return; }
  if (line.startsWith("open ")) { setPetalOpenPercent(line.substring(5).toInt(), true); return; }
  if (line.startsWith("speed ")) { petalStepIntervalMs = constrain(line.substring(6).toInt(), 2, 120); return; }
  if (line.startsWith("look ")) {
    float x = 0, y = 0;
    if (sscanf(line.c_str(), "look %f %f", &x, &y) == 2) setManualEyeLook(x, y);
    return;
  }
  if (line.startsWith("eyeopen ")) { setManualEyeOpenPercent(line.substring(8).toInt()); return; }
  if (line.startsWith("eyelimits ")) {
    int lx = 100, ly = 100;
    if (sscanf(line.c_str(), "eyelimits %d %d", &lx, &ly) >= 1) {
      eye.gazeLimitX = clampf((float)constrain(lx, 10, 100) / 100.0f, 0.1f, 1.0f);
      eye.gazeLimitY = clampf((float)constrain(ly, 10, 100) / 100.0f, 0.1f, 1.0f);
    }
    return;
  }
  if (line == "pupilauto on") { eye.pupilAutoSpin = true; return; }
  if (line == "pupilauto off") { eye.pupilAutoSpin = false; return; }
  if (line == "track on") { eye.trackEnabled = true; return; }
  if (line == "track off") { eye.trackEnabled = false; return; }
}

void printSelfInfo() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  IPAddress ip = WiFi.localIP();
  Serial.println("\n=== Sue Node Info ===");
  Serial.printf("Node ID: %s\n", NODE_ID);
  Serial.printf("Node Type: %s\n", NODE_TYPE);
  Serial.printf("IP: %d.%d.%d.%d\n", ip[0], ip[1], ip[2], ip[3]);
  Serial.printf("MAC: %02X:%02X:%02X:%02X:%02X:%02X\n", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.printf("Servo angle: %d (safe %d..%d)\n", currentPetalAngle, SERVO_SAFE_MIN_ANGLE, SERVO_SAFE_MAX_ANGLE);
  Serial.printf(
    "Eye track=%d blink=%d breathe=%d pupilAuto=%d limits=(%.2f,%.2f)\n",
    eye.trackEnabled ? 1 : 0,
    eye.autoBlink ? 1 : 0,
    eye.autoBreathe ? 1 : 0,
    eye.pupilAutoSpin ? 1 : 0,
    eye.gazeLimitX,
    eye.gazeLimitY
  );
  Serial.println("=====================\n");
}

void printHelp() {
  Serial.println("\n=== Sue Commands ===");
  Serial.println("state <rest|bloom|alert|soothe|relax|danger|calm|breathe|idle>");
  Serial.println("open <0-100> | angle <safe-angle> | speed <2-120>");
  Serial.println("look <x y>  (range -1..1)");
  Serial.println("eyeopen <0-100>");
  Serial.println("eyelimits <x% y%>  (10..100)");
  Serial.println("pupilauto on|off");
  Serial.println("track on|off");
  Serial.println("wifi status | wifi retry <attempts>");
  Serial.println("status | info | help");
  Serial.println("====================\n");
}

// ============================================================
// Arduino setup / loop
// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);
  randomSeed((uint32_t)esp_random());
  Serial.println("\n========== DATT3700 Sue Node ==========");

  panel->begin();
  panel->setRotation(2);
  eyeCanvasA->begin();
  eyeCanvasB->begin();
  drawStaticBackground();

  petalServo.setPeriodHertz(50);
  petalServo.attach(SERVO_PIN, SERVO_MIN_US, SERVO_MAX_US);
  petalServo.write(PETAL_CLOSED_ANGLE);
  currentPetalAngle = PETAL_CLOSED_ANGLE;
  targetPetalAngle = PETAL_CLOSED_ANGLE;

  eye.nextBlinkMs = millis() + chooseNextBlinkDelayMs();

  setupNetwork();
  setupMDNS();
  udp.begin(OSC_PORT);
  Serial.printf("[OSC] Listening on %d\n", OSC_PORT);

  applyState("rest");
  updateEye(true);
  printHelp();
}

void loop() {
  processOSC();
  parseSerialLine();
  ensureWifiConnected();
  ensureMDNS();
  updatePetal();
  updateEye(false);
}
