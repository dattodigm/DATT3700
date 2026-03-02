/**
 * sylvie_composite.ino - Sylvie复合花朵固件
 * 
 * Sylvie硬件架构：
 * - DC电机：控制两个花朵的开合（基于eps32_sylvie）
 * - Servo舵机：8个底座舵机用于人脸追踪（基于Face_tracking）
 * 
 * 此固件运行在控制底座的ESP32上，接收追踪命令和情绪参数
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <ESP32Servo.h>

// ========== 配置 ==========
const char* ssid = "DigitalBloom_Sylvie_Base";
const char* password = "12345678";
const int localPort = 8888;

// ========== Servo配置 ==========
// X轴组（水平追踪）- 4个舵机同步
Servo servoX[4];
int pinsX[4] = {18, 21, 23, 26};

// Y轴组（垂直追踪）- 4个舵机同步
Servo servoY[4];
int pinsY[4] = {19, 22, 25, 27};

// 当前角度
int currentAngleX = 90;
int currentAngleY = 90;

// ========== DC电机配置（接收来自另一ESP32或本机控制）==========
// 注：如果本ESP32也控制DC电机，取消下面注释
// const int MOTOR_A_1 = 25;
// const int MOTOR_A_2 = 26;
// const int MOTOR_B_1 = 32;
// const int MOTOR_B_2 = 33;

// ========== LED配置 ==========
const int LED_R = 2;
const int LED_G = 4;
const int LED_B = 5;

// ========== 状态变量 ==========
WiFiUDP udp;
bool trackingEnabled = false;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n🌸 Sylvie Composite Flower - Base Tracker");
  Serial.println("花朵底座追踪系统启动...\n");
  
  // 初始化Servo
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  
  // 初始化X轴舵机
  for (int i = 0; i < 4; i++) {
    servoX[i].setPeriodHertz(50);
    servoX[i].attach(pinsX[i], 500, 2400);
    servoX[i].write(90);
    delay(100);
  }
  
  // 初始化Y轴舵机
  for (int i = 0; i < 4; i++) {
    servoY[i].setPeriodHertz(50);
    servoY[i].attach(pinsY[i], 500, 2400);
    servoY[i].write(90);
    delay(100);
  }
  
  // 初始化LED引脚
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  
  // 初始化WiFi热点
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.println("✅ WiFi热点已创建");
  Serial.print("SSID: ");
  Serial.println(ssid);
  Serial.print("IP地址: ");
  Serial.println(IP);
  Serial.print("OSC端口: ");
  Serial.println(localPort);
  
  // 启动UDP
  udp.begin(localPort);
  
  Serial.println("\n等待OSC命令...");
  Serial.println("命令格式:");
  Serial.println("  /flower/servo [pan] [tilt] - 设置舵机角度");
  Serial.println("  /flower/composite [bloom] [pan] [tilt] [r] [g] [b]");
  Serial.println("  /flower/state [bloom] [jitter] [speed] [r] [g] [b]");
}

void loop() {
  handleOSCMessage();
  delay(10);
}

void handleOSCMessage() {
  OSCMessage msg;
  int size = udp.parsePacket();
  
  if (size > 0) {
    while (size--) {
      msg.fill(udp.read());
    }
    
    if (!msg.hasError()) {
      char addressBuffer[128];
      msg.getAddress(addressBuffer, 0, sizeof(addressBuffer));
      
      // 路由到不同处理函数
      msg.route("/flower/servo", routeServo);
      msg.route("/flower/composite", routeComposite);
      msg.route("/flower/state", routeState);
    }
  }
}

void routeServo(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0) && msg.isInt(1)) {
    int pan = msg.getInt(0);
    int tilt = msg.getInt(1);
    
    // 限制角度范围
    pan = constrain(pan, 0, 180);
    tilt = constrain(tilt, 0, 180);
    
    // 更新所有舵机
    setServoAngles(pan, tilt);
    
    Serial.printf("Servo: Pan=%d, Tilt=%d\n", pan, tilt);
  }
}

void routeComposite(OSCMessage &msg, int addrOffset) {
  // /flower/composite [bloom] [pan] [tilt] [r] [g] [b]
  if (msg.isFloat(0) && msg.isInt(1) && msg.isInt(2)) {
    float bloom = msg.getFloat(0);
    int pan = msg.getInt(1);
    int tilt = msg.getInt(2);
    
    // 设置舵机
    setServoAngles(pan, tilt);
    
    // 设置LED颜色（如果有颜色参数）
    if (msg.isInt(3) && msg.isInt(4) && msg.isInt(5)) {
      int r = msg.getInt(3);
      int g = msg.getInt(4);
      int b = msg.getInt(5);
      setLED(r, g, b);
    }
    
    Serial.printf("Composite: Bloom=%.2f, Pan=%d, Tilt=%d\n", bloom, pan, tilt);
  }
}

void routeState(OSCMessage &msg, int addrOffset) {
  // /flower/state [bloom] [jitter] [speed] [r] [g] [b]
  if (msg.isFloat(0) && msg.isFloat(1) && msg.isFloat(2)) {
    float bloom = msg.getFloat(0);
    // float jitter = msg.getFloat(1);  // 可用于控制颤动
    // float speed = msg.getFloat(2);   // 可用于控制速度
    
    // 设置LED颜色
    if (msg.isInt(3) && msg.isInt(4) && msg.isInt(5)) {
      int r = msg.getInt(3);
      int g = msg.getInt(4);
      int b = msg.getInt(5);
      setLED(r, g, b);
    }
    
    Serial.printf("State: Bloom=%.2f\n", bloom);
  }
}

void setServoAngles(int pan, int tilt) {
  currentAngleX = pan;
  currentAngleY = tilt;
  
  // 同步更新所有X轴舵机
  for (int i = 0; i < 4; i++) {
    servoX[i].write(pan);
  }
  
  // 同步更新所有Y轴舵机
  for (int i = 0; i < 4; i++) {
    servoY[i].write(tilt);
  }
}

void setLED(int r, int g, int b) {
  analogWrite(LED_R, r);
  analogWrite(LED_G, g);
  analogWrite(LED_B, b);
}

// 串口调试命令
void checkSerialCommands() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd.startsWith("servo")) {
      int space1 = cmd.indexOf(' ');
      int space2 = cmd.indexOf(' ', space1 + 1);
      
      if (space1 > 0 && space2 > 0) {
        int pan = cmd.substring(space1 + 1, space2).toInt();
        int tilt = cmd.substring(space2 + 1).toInt();
        setServoAngles(pan, tilt);
        Serial.printf("手动设置: Pan=%d, Tilt=%d\n", pan, tilt);
      }
    } else if (cmd == "center") {
      setServoAngles(90, 90);
      Serial.println("舵机归中");
    }
  }
}
