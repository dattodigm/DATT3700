#include <ESP32Servo.h>

String inputString;

// 定义舵机数组
Servo servosX[4];
Servo servosY[4];

// 按照你的要求分配引脚
int pinsX[4] = {18, 21, 23, 26}; // X 轴组 (水平)
int pinsY[4] = {19, 22, 25, 27}; // Y 轴组 (垂直)

void setup() {
  Serial.begin(115200);

  // 分配硬件定时器
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  // 初始化 X 轴组
  for (int i = 0; i < 4; i++) {
    servosX[i].setPeriodHertz(50);
    servosX[i].attach(pinsX[i], 500, 2400);
    servosX[i].write(90); 
    delay(100); 
  }

  // 初始化 Y 轴组
  for (int i = 0; i < 4; i++) {
    servosY[i].setPeriodHertz(50);
    servosY[i].attach(pinsY[i], 500, 2400);
    servosY[i].write(90);
    delay(100);
  }

  Serial.println("8 Servos (4X, 4Y) Tracking System Ready!");
}

void loop() {
  while (Serial.available()) {
    inputString = Serial.readStringUntil('\n'); 
    
    int commaIndex = inputString.indexOf(',');
    if (commaIndex != -1) {
      int x_axis = inputString.substring(0, commaIndex).toInt();
      int y_axis = inputString.substring(commaIndex + 1).toInt();

      // 根据你的 1920x1080 分辨率进行映射
      int angleX = map(x_axis, 0, 1920, 180, 0); 
      int angleY = map(y_axis, 0, 1080, 180, 0);

      // 同步更新 4 个 X 轴舵机
      for (int i = 0; i < 4; i++) {
        servosX[i].write(angleX);
      }

      // 同步更新 4 个 Y 轴舵机
      for (int i = 0; i < 4; i++) {
        servosY[i].write(angleY);
      }

      Serial.printf("X_Angle: %d, Y_Angle: %d\n", angleX, angleY);
    }
  }
}