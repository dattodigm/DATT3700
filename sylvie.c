#include <WiFi.h>
#include <WiFiUdp.h>
#include <MicroOscUdp.h>

// --- WiFi 热点配置 ---
const char* ap_ssid = "ESP32_Sylvie";
const char* ap_password = "12345678";  // 至少8位

// --- OSC 配置 ---
const int localPort = 8888;
MicroOscUdp<512> oscUdp(&Serial);

// --- 第一组：电机 A 与 LED 1 ---
const int M1_A = 25; const int M1_B = 26;
const int L1_R = 2;  const int L1_G = 4;  const int L1_B = 5;

// --- 第二组：电机 B 与 LED 2 ---
const int M2_A = 18; const int M2_B = 19;
const int L2_R = 12; const int L2_G = 13; const int L2_B = 14;

// --- 自动模式控制 ---
bool autoMode = true;
unsigned long lastAutoUpdate = 0;
int autoState = 0;

void setup() {
  Serial.begin(115200);
  
  // 初始化所有引脚为输出模式
  int pins[] = {M1_A, M1_B, M2_A, M2_B, L1_R, L1_G, L1_B, L2_R, L2_G, L2_B};
  for (int p : pins) pinMode(p, OUTPUT);
  
  // 创建 WiFi 热点
  Serial.println("正在创建WiFi热点...");
  WiFi.softAP(ap_ssid, ap_password);
  IPAddress IP = WiFi.softAPIP();
  Serial.print("热点IP地址: ");
  Serial.println(IP);
  Serial.print("OSC端口: ");
  Serial.println(localPort);
  
  // 启动 UDP
  oscUdp.begin(localPort);
  
  Serial.println("\n=== OSC 命令列表 ===");
  Serial.println("/auto [0/1] - 切换自动/手动模式");
  Serial.println("/motor1 [1/-1/0] - 控制电机A (正转/反转/停止)");
  Serial.println("/motor2 [1/-1/0] - 控制电机B");
  Serial.println("/led1 [r] [g] [b] - 设置LED1颜色 (0-255)");
  Serial.println("/led2 [r] [g] [b] - 设置LED2颜色");
  Serial.println("/preset [1/2/3] - 预设场景");
  Serial.println("=====================\n");
}

void loop() {
  // 处理 OSC 消息
  oscUdp.onPacketReceive();
  
  if (autoMode) {
    runAutoMode();
  }
}

// 自动模式循环
void runAutoMode() {
  unsigned long currentTime = millis();
  
  switch(autoState) {
    case 0: // 花A开
      if (currentTime - lastAutoUpdate == 0 || currentTime - lastAutoUpdate > 3000) {
        setPreset(1);
        lastAutoUpdate = currentTime;
        autoState = 1;
      }
      break;
      
    case 1: // 停止缓冲
      if (currentTime - lastAutoUpdate > 3000) {
        stopAll();
        lastAutoUpdate = currentTime;
        autoState = 2;
      }
      break;
      
    case 2: // 花B开
      if (currentTime - lastAutoUpdate > 500) {
        setPreset(2);
        lastAutoUpdate = currentTime;
        autoState = 3;
      }
      break;
      
    case 3: // 等待
      if (currentTime - lastAutoUpdate > 3000) {
        stopAll();
        lastAutoUpdate = currentTime;
        autoState = 0;
      }
      break;
  }
}

// OSC 消息回调
void onOscMessageReceived(MicroOscMessage& msg) {
  // /auto - 切换自动/手动模式
  if (msg.match("/auto")) {
    if (msg.nextAsInt() == 1) {
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
  
  // /motor1 - 控制电机A
  else if (msg.match("/motor1") && !autoMode) {
    int dir = msg.nextAsInt();
    setMotor(1, dir);
    Serial.print("电机A: ");
    Serial.println(dir);
  }
  
  // /motor2 - 控制电机B
  else if (msg.match("/motor2") && !autoMode) {
    int dir = msg.nextAsInt();
    setMotor(2, dir);
    Serial.print("电机B: ");
    Serial.println(dir);
  }
  
  // /led1 - 设置LED1颜色
  else if (msg.match("/led1") && !autoMode) {
    int r = msg.nextAsInt();
    int g = msg.nextAsInt();
    int b = msg.nextAsInt();
    setLED(1, r, g, b);
    Serial.printf("LED1: R=%d G=%d B=%d\n", r, g, b);
  }
  
  // /led2 - 设置LED2颜色
  else if (msg.match("/led2") && !autoMode) {
    int r = msg.nextAsInt();
    int g = msg.nextAsInt();
    int b = msg.nextAsInt();
    setLED(2, r, g, b);
    Serial.printf("LED2: R=%d G=%d B=%d\n", r, g, b);
  }
  
  // /preset - 预设场景
  else if (msg.match("/preset") && !autoMode) {
    int preset = msg.nextAsInt();
    setPreset(preset);
    Serial.print("预设场景: ");
    Serial.println(preset);
  }
}

// 控制电机
void setMotor(int motor, int direction) {
  int pinA = (motor == 1) ? M1_A : M2_A;
  int pinB = (motor == 1) ? M1_B : M2_B;
  
  if (direction > 0) { // 正转
    digitalWrite(pinA, HIGH);
    digitalWrite(pinB, LOW);
  } else if (direction < 0) { // 反转
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, HIGH);
  } else { // 停止
    digitalWrite(pinA, LOW);
    digitalWrite(pinB, LOW);
  }
}

// 控制LED
void setLED(int led, int r, int g, int b) {
  int pinR = (led == 1) ? L1_R : L2_R;
  int pinG = (led == 1) ? L1_G : L2_G;
  int pinB = (led == 1) ? L1_B : L2_B;
  
  analogWrite(pinR, r);
  analogWrite(pinG, g);
  analogWrite(pinB, b);
}

// 预设场景
void setPreset(int preset) {
  switch(preset) {
    case 1: // 花A开（黄灯）
      setLED(1, 255, 255, 0);
      setLED(2, 0, 0, 0);
      setMotor(1, 1);
      setMotor(2, -1);
      break;
      
    case 2: // 花B开（青灯）
      setLED(1, 0, 0, 0);
      setLED(2, 0, 255, 255);
      setMotor(1, -1);
      setMotor(2, 1);
      break;
      
    case 3: // 全部停止
      stopAll();
      break;
  }
}

// 停止所有设备
void stopAll() {
  setMotor(1, 0);
  setMotor(2, 0);
  setLED(1, 0, 0, 0);
  setLED(2, 0, 0, 0);
}
