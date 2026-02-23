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

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // 读取一行命令
    command.trim(); // 去除首尾空格和换行符
    processSerialCommand(command);
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

// 串口命令处理器
void processSerialCommand(String cmd) {
  // 转换为小写，使命令不区分大小写（可选）
  cmd.toLowerCase();

  // 分割命令和参数
  int firstSpace = cmd.indexOf(' ');
  String cmdName = (firstSpace == -1) ? cmd : cmd.substring(0, firstSpace);
  String args = (firstSpace == -1) ? "" : cmd.substring(firstSpace + 1);

  if (cmdName == "auto") {
    // 示例：auto 1 或 auto 0
    int value = args.toInt();
    if (value == 1) {
      autoMode = true;
      lastAutoUpdate = millis();
      autoState = 0;
      Serial.println("[Serial] Switched to AUTO mode.");
    } else {
      autoMode = false;
      stopAll();
      Serial.println("[Serial] Switched to MANUAL mode.");
    }

  } else if (cmdName == "motor1" || cmdName == "m1") {
    if (!autoMode) {
      int dir = args.toInt(); // 应为 1, -1, 或 0
      setMotor(1, dir);
      Serial.printf("[Serial] Motor A set to: %d\n", dir);
    } else {
      Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
    }

  } else if (cmdName == "motor2" || cmdName == "m2") {
    if (!autoMode) {
      int dir = args.toInt();
      setMotor(2, dir);
      Serial.printf("[Serial] Motor B set to: %d\n", dir);
    } else {
      Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
    }

  } else if (cmdName == "led1" || cmdName == "l1") {
    if (!autoMode) {
      // 解析三个RGB参数，例如：led1 255 0 0
      int r, g, b;
      sscanf(args.c_str(), "%d %d %d", &r, &g, &b); // 简单解析
      setLED(1, r, g, b);
      Serial.printf("[Serial] LED1 set to: R=%d G=%d B=%d\n", r, g, b);
    } else {
      Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
    }

  } else if (cmdName == "led2" || cmdName == "l2") {
    if (!autoMode) {
      int r, g, b;
      sscanf(args.c_str(), "%d %d %d", &r, &g, &b);
      setLED(2, r, g, b);
      Serial.printf("[Serial] LED2 set to: R=%d G=%d B=%d\n", r, g, b);
    } else {
      Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
    }

  } else if (cmdName == "preset") {
    if (!autoMode) {
      int presetNum = args.toInt();
      setPreset(presetNum);
      Serial.printf("[Serial] Preset %d activated.\n", presetNum);
    } else {
      Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
    }

  } else if (cmdName == "stop" || cmdName == "alloff") {
    stopAll();
    Serial.println("[Serial] All devices STOPPED.");

  } else if (cmdName == "help" || cmdName == "?") {
    printSerialHelp();

  } else {
    Serial.printf("[Serial] Unknown command: '%s'. Type 'help'.\n", cmdName.c_str());
  }
}

// 串口帮助信息
void printSerialHelp() {
  Serial.println("\n=== Serial Debug Commands ===");
  Serial.println("auto [0/1]     - Switch mode (0=Manual, 1=Auto)");
  Serial.println("motor1/m1 [1/-1/0] - Control Motor A");
  Serial.println("motor2/m2 [1/-1/0] - Control Motor B");
  Serial.println("led1/l1 [R] [G] [B] - Set LED1 color (0-255)");
  Serial.println("led2/l2 [R] [G] [B] - Set LED2 color");
  Serial.println("preset [1/2/3] - Load preset scene");
  Serial.println("stop/alloff    - Stop all motors and LEDs");
  Serial.println("help/?         - Show this help");
  Serial.println("=============================\n");
}
