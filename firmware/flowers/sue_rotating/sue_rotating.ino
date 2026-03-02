/**
 * sue_rotating.ino - Sue旋转花朵固件
 * 
 * Sue硬件架构：
 * - Servo舵机：控制花朵旋转（与Sylvie不同，这是旋转而非底座追踪）
 * - 超声波传感器：检测距离并触发旋转
 * - 当有人靠近时，花朵开始旋转
 * 
 * 可以接收OSC命令覆盖自动模式
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <ESP32Servo.h>

// ========== 配置 ==========
const char* ssid = "DigitalBloom_Sue";
const char* password = "12345678";
const int localPort = 8888;

// ========== 硬件引脚 ==========
const int SERVO_PIN = 14;        // 旋转舵机
const int TRIG_PIN = 27;         // 超声波Trig
const int ECHO_PIN = 33;         // 超声波Echo
const int LED_R = 2;
const int LED_G = 4;
const int LED_B = 5;

// ========== 参数配置 ==========
const int DETECT_DISTANCE = 50;      // 检测距离(cm)
const int ROTATION_SPEED = 2;        // 旋转速度(度/循环)
const int ROTATION_RANGE = 180;      // 旋转范围

// ========== 状态变量 ==========
WiFiUDP udp;
Servo rotationServo;

bool autoMode = true;            // 自动模式（超声波触发）
int currentAngle = 0;            // 当前角度
int targetAngle = 0;             // 目标角度
bool rotatingForward = true;     // 旋转方向

unsigned long lastDistanceCheck = 0;
const unsigned long DISTANCE_INTERVAL = 100;  // 距离检测间隔(ms)

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n🌸 Sue Rotating Flower");
  Serial.println("旋转花朵系统启动...\n");
  
  // 初始化舵机
  ESP32PWM::allocateTimer(0);
  rotationServo.setPeriodHertz(50);
  rotationServo.attach(SERVO_PIN, 500, 2400);
  rotationServo.write(0);
  
  // 初始化超声波
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // 初始化LED
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  
  // 初始化WiFi
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
  
  Serial.println("\n等待OSC命令或超声波触发...");
  Serial.println("命令格式:");
  Serial.println("  /flower/rotate [angle] - 设置旋转角度(0-180)");
  Serial.println("  /flower/auto [0/1] - 开关自动模式");
  Serial.println("  /flower/state [...] - 标准状态命令");
}

void loop() {
  // 处理OSC消息
  handleOSCMessage();
  
  // 自动模式：超声波检测
  if (autoMode && millis() - lastDistanceCheck > DISTANCE_INTERVAL) {
    checkUltrasonic();
    lastDistanceCheck = millis();
  }
  
  // 更新旋转
  updateRotation();
  
  delay(20);
}

void handleOSCMessage() {
  OSCMessage msg;
  int size = udp.parsePacket();
  
  if (size > 0) {
    while (size--) {
      msg.fill(udp.read());
    }
    
    if (!msg.hasError()) {
      msg.route("/flower/rotate", routeRotate);
      msg.route("/flower/auto", routeAuto);
      msg.route("/flower/state", routeState);
    }
  }
}

void routeRotate(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    int angle = msg.getInt(0);
    angle = constrain(angle, 0, 180);
    
    autoMode = false;  // 收到OSC命令时退出自动模式
    targetAngle = angle;
    
    Serial.printf("OSC旋转到: %d°\n", angle);
  }
}

void routeAuto(OSCMessage &msg, int addrOffset) {
  if (msg.isInt(0)) {
    autoMode = (msg.getInt(0) == 1);
    Serial.printf("自动模式: %s\n", autoMode ? "开启" : "关闭");
  }
}

void routeState(OSCMessage &msg, int addrOffset) {
  // 标准状态命令 /flower/state [bloom] [jitter] [speed] [r] [g] [b]
  if (msg.isFloat(0)) {
    float bloom = msg.getFloat(0);
    // float jitter = msg.getFloat(1);
    // float speed = msg.getFloat(2);
    
    // bloom映射到旋转：bloom=1.0时旋转180度
    targetAngle = (int)(bloom * 180);
    targetAngle = constrain(targetAngle, 0, 180);
    
    // 设置LED颜色
    if (msg.isInt(3) && msg.isInt(4) && msg.isInt(5)) {
      int r = msg.getInt(3);
      int g = msg.getInt(4);
      int b = msg.getInt(5);
      setLED(r, g, b);
    }
    
    Serial.printf("State: Bloom=%.2f -> Angle=%d°\n", bloom, targetAngle);
  }
}

void checkUltrasonic() {
  long distance = readDistance();
  
  if (distance > 0 && distance < DETECT_DISTANCE) {
    // 有人靠近，开始旋转
    if (!rotatingForward && currentAngle <= 10) {
      rotatingForward = true;
      Serial.printf("有人靠近(%ld cm)，开始旋转\n", distance);
    }
  }
}

long readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
  
  long distance = duration * 0.034 / 2;
  return distance;
}

void updateRotation() {
  // 自动模式下的往复旋转
  if (autoMode) {
    if (rotatingForward) {
      currentAngle += ROTATION_SPEED;
      if (currentAngle >= ROTATION_RANGE) {
        currentAngle = ROTATION_RANGE;
        rotatingForward = false;
      }
    } else {
      currentAngle -= ROTATION_SPEED;
      if (currentAngle <= 0) {
        currentAngle = 0;
        // 等待下次触发
      }
    }
    rotationServo.write(currentAngle);
  } else {
    // OSC控制模式：平滑移动到目标角度
    int diff = targetAngle - currentAngle;
    if (abs(diff) > 2) {
      currentAngle += (diff > 0) ? 2 : -2;
      rotationServo.write(currentAngle);
    }
  }
}

void setLED(int r, int g, int b) {
  analogWrite(LED_R, r);
  analogWrite(LED_G, g);
  analogWrite(LED_B, b);
}

// 串口调试
void checkSerial() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "auto") {
      autoMode = true;
      Serial.println("切换到自动模式");
    } else if (cmd == "manual") {
      autoMode = false;
      Serial.println("切换到手动模式");
    } else if (cmd.startsWith("angle")) {
      int angle = cmd.substring(6).toInt();
      targetAngle = constrain(angle, 0, 180);
      autoMode = false;
      Serial.printf("设置角度: %d\n", targetAngle);
    } else if (cmd == "dist") {
      long d = readDistance();
      Serial.printf("距离: %ld cm\n", d);
    }
  }
}
