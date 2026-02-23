#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCBundle.h>

// --- WiFi hotspot configuration 建立热点 WiFi 配置---
const char* ap_ssid = "ESP32_Sylvie";
const char* ap_password = "12345678";  //  At least 8 digits 至少8位

// ---OSC protocol settings OSC 协议端口设置 ---
const int localPort = 8888;
WiFiUDP udp;

// --- Group 1: Motor A and LED 1 第一组：电机 A 与 LED 1 ---
const int M1_A = 25; const int M1_B = 26;
const int L1_R = 2;  const int L1_G = 4;  const int L1_B = 5;

// ---  Group 2: Motor B and LED 2 第二组：电机 B 与 LED 2 ---
const int M2_A = 18; const int M2_B = 19;
const int L2_R = 12; const int L2_G = 13; const int L2_B = 14;

// --- Automatic mode control 自动模式控制 ---
bool autoMode = true;
unsigned long lastAutoUpdate = 0;
int autoState = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize all pins to output mode 初始化所有引脚为输出模式
  int pins[] = {M1_A, M1_B, M2_A, M2_B, L1_R, L1_G, L1_B, L2_R, L2_G, L2_B};
  for (int p : pins) pinMode(p, OUTPUT);
  
  // Create WiFi hotspot
  Serial.println("Creating WiFi hotspot 正在创建WiFi热点...");
  WiFi.softAP(ap_ssid, ap_password);
  IPAddress IP = WiFi.softAPIP();
  Serial.print("Hotspot IP address: ");
  Serial.println(IP);
  Serial.print("OSC port: ");
  Serial.println(localPort);
  
  // 启动 UDP
  udp.begin(localPort);
  
  Serial.println("\n=== OSC  command list  ===");
  Serial.println("/auto [0/1] -  Switch auto/manual mode");
  Serial.println("/motor1 [1/-1/0] - Control motor A (forward/reverse/stop)");
  Serial.println("/motor2 [1/-1/0] - Control motor B 控制电机B");
  Serial.println("/led1 [r] [g] [b] - Set LED1 color (0-255)");
  Serial.println("/led2 [r] [g] [b] - Set LED2 color");
  Serial.println("/preset [1/2/3] - Preset scene 预设场景");
  Serial.println("=====================\n");
}

void loop() {
  // Handle OSC message 处理 OSC 消息
  OSCMessage msg;
  int size = udp.parsePacket();
  
  if (size > 0) {
    while (size--) {
      msg.fill(udp.read());
    }
    
    if (!msg.hasError()) {
      // Print the received message
      char addressBuffer[128];
      msg.getAddress(addressBuffer, 0, sizeof(addressBuffer));
      Serial.print("Received OSC message: ");
      Serial.println(addressBuffer);
      
      // Route to handler function 路由到处理函数
      msg.route("/auto", routeAuto);
      msg.route("/motor1", routeMotor1);
      msg.route("/motor2", routeMotor2);
      msg.route("/led1", routeLED1);
      msg.route("/led2", routeLED2);
      msg.route("/preset", routePreset);
    } else {
      Serial.println("OSC message error");
    }
  }
  
  if (autoMode) {
    runAutoMode();
  }
}

// OSC routing function 路由函数
void routeAuto(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    int value = msg.getInt(0);
    if (value == 1) {
      autoMode = true;
      lastAutoUpdate = millis();
      autoState = 0;
      Serial.println("Switch to automatic mode 切换到自动模式");
    } else {
      autoMode = false;
      stopAll();
      Serial.println("Switch to manual mode 切换到手动模式");
    }
  }
}

void routeMotor1(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0)) {
    int dir = msg.getInt(0);
    setMotor(1, dir);
    Serial.print("Motor A: ");
    Serial.println(dir);
  }
}

void routeMotor2(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0)) {
    int dir = msg.getInt(0);
    setMotor(2, dir);
    Serial.print("Motor B: ");
    Serial.println(dir);
  }
}

void routeLED1(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0) && msg.isInt(1) && msg.isInt(2)) {
    int r = msg.getInt(0);
    int g = msg.getInt(1);
    int b = msg.getInt(2);
    setLED(1, r, g, b);
    Serial.printf("LED1: R=%d G=%d B=%d\n", r, g, b);
  }
}

void routeLED2(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0) && msg.isInt(1) && msg.isInt(2)) {
    int r = msg.getInt(0);
    int g = msg.getInt(1);
    int b = msg.getInt(2);
    setLED(2, r, g, b);
    Serial.printf("LED2: R=%d G=%d B=%d\n", r, g, b);
  }
}

void routePreset(OSCMessage &msg, int addrOffset) {
  if (!autoMode && msg.isInt(0)) {
    int preset = msg.getInt(0);
    setPreset(preset);
    Serial.print("Default preset scene:");
    Serial.println(preset);
  }
}

// Auto mode loop
void runAutoMode() {
  unsigned long currentTime = millis();
  
  switch(autoState) {
    case 0: // 花A开 Flower A blooms
      if (currentTime - lastAutoUpdate == 0 || currentTime - lastAutoUpdate > 3000) {
        setPreset(1);
        lastAutoUpdate = currentTime;
        autoState = 1;
      }
      break;
      
    case 1: // 停止缓冲 Stop buffering
      if (currentTime - lastAutoUpdate > 3000) {
        stopAll();
        lastAutoUpdate = currentTime;
        autoState = 2;
      }
      break;
      
    case 2: // 花B开 Flower B blooms
      if (currentTime - lastAutoUpdate > 500) {
        setPreset(2);
        lastAutoUpdate = currentTime;
        autoState = 3;
      }
      break;
      
    case 3: // wait
      if (currentTime - lastAutoUpdate > 3000) {
        stopAll();
        lastAutoUpdate = currentTime;
        autoState = 0;
      }
      break;
  }
}

// Control the motor 控制电机
void setMotor(int motor, int direction) {
  int pinA = (motor == 1) ? M1_A : M2_A;
  int pinB = (motor == 1) ? M1_B : M2_B;
  
  if (direction > 0) { // FORWARD rotation 正转
    digitalWrite(pinA, HIGH);
    digitalWrite(pinB, LOW);
  } else if (direction < 0) { // REVERSE 反转
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, HIGH);
  } else { // STOP 停止
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, LOW);
  }
}

// LED Control
void setLED(int led, int r, int g, int b) {
  int pinR = (led == 1) ? L1_R : L2_R;
  int pinG = (led == 1) ? L1_G : L2_G;
  int pinB = (led == 1) ? L1_B : L2_B;
  
  analogWrite(pinR, r);
  analogWrite(pinG, g);
  analogWrite(pinB, b);
}

// preset scene
void setPreset(int preset) {
  switch(preset) {
    case 1: // Flower A blooms with YELLOW LED 花A开（黄灯）
      setLED(1, 255, 255, 0);
      setLED(2, 0, 0, 0);
      setMotor(1, 1);
      setMotor(2, -1);
      break;
      
    case 2: // Flower B blooms with CYAN LED 花B开（青灯）
      setLED(1, 0, 0, 0);
      setLED(2, 0, 255, 255);
      setMotor(1, -1);
      setMotor(2, 1);
      break;
      
    case 3: // STOP ALL
      stopAll();
      break;
  }
}

// STOP ALL DEVICES
void stopAll() {
  setMotor(1, 0);
  setMotor(2, 0);
  setLED(1, 0, 0, 0);
  setLED(2, 0, 0, 0);
}
