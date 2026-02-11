# ESP32 硬件连接指南 / ESP32 Hardware Connection Guide
## 硬件需求 / Hardware Requirements
- 1× ESP32 开发板 / ESP32 Development Board
- 2× 直流电机 / DC Motors
- 2× RGB LED灯 / RGB LED Lights
- 导线若干 / Multiple Jumper Wires

## 引脚连接说明 / Pin Connection Guide
### 电机连接 / Motor Connections
#### 电机A / Motor A
- M1_A → GPIO25 (电机A正极端 / Motor A positive terminal)
- M1_B → GPIO26 (电机A负极端 / Motor A negative terminal)

#### 电机B / Motor B
- M2_A → GPIO18 (电机B正极端 / Motor B positive terminal)
- M2_B → GPIO19 (电机B负极端 / Motor B negative terminal)

### LED灯连接 / LED Connections
#### LED1
- L1_R → GPIO2 (LED1红色引脚 / LED1 Red pin)
- L1_G → GPIO4 (LED1绿色引脚 / LED1 Green pin)
- L1_B → GPIO5 (LED1蓝色引脚 / LED1 Blue pin)

#### LED2
- L2_R → GPIO12 (LED2红色引脚 / LED2 Red pin)
- L2_G → GPIO13 (LED2绿色引脚 / LED2 Green pin)
- L2_B → GPIO14 (LED2蓝色引脚 / LED2 Blue pin)

## 注意事项 / Important Notes
1. 请确保所有连接牢固可靠 / Ensure all connections are secure and reliable
2. LED灯需要串联适当的限流电阻 / LEDs should be connected with appropriate current-limiting resistors
3. 电机可能需要额外的驱动电路 / Motors may require additional driver circuits
4. 注意电源供电要求 / Pay attention to power supply requirements

## 网络配置 / Network Configuration
- WiFi名称 / SSID: ESP32_Sylvie
- 密码 / Password: 12345678
- OSC端口 / OSC Port: 8888

## 控制说明 / Control Instructions
系统支持以下OSC命令 / The system supports the following OSC commands:
- `/auto [0/1]` - 切换自动/手动模式 / Toggle auto/manual mode
- `/motor1 [1/-1/0]` - 控制电机A / Control Motor A
- `/motor2 [1/-1/0]` - 控制电机B / Control Motor B
- `/led1 [r] [g] [b]` - 控制LED1颜色 / Control LED1 color
- `/led2 [r] [g] [b]` - 控制LED2颜色 / Control LED2 color
- `/preset [1/2/3]` - 预设场景选择 / Preset scene selection

## 当前控制方案的局限性 / Current Control Limitations
1. 缺乏速度控制 / Lack of speed control
2. 无位置反馈 / No position feedback
3. 启停不平滑 / Abrupt start and stop
4. 负载变化时无法自适应 / Cannot adapt to load changes

## 建议的改进方案 / Suggested Improvements
### 1. 硬件升级 / Hardware Upgrades
- 添加编码器 / Add encoders
    - 用于速度和位置反馈 / For speed and position feedback

- 使用PWM控制端口 / Use PWM control pins
    - 实现速度调节 / Enable speed adjustment

- 可选添加电流传感器 / Optionally add current sensors
    - 监控电机负载 / Monitor motor load

### 2. 软件改进 / Software Improvements
```ino
// PID控制相关参数
struct PIDController {
    float Kp = 2.0;    // 比例系数 / Proportional gain
    float Ki = 0.5;    // 积分系数 / Integral gain
    float Kd = 0.1;    // 微分系数 / Derivative gain
    float setpoint;    // 目标值 / Target value
    float lastError;   // 上次误差 / Previous error
    float integral;    // 积分项 / Integral term
    
    float compute(float input) {
        float error = setpoint - input;
        integral += error;
        float derivative = error - lastError;
        lastError = error;
        
        return Kp * error + Ki * integral + Kd * derivative;
    }
};
```
/
### 3. 具体优势 / Specific Advantages
- 精确的速度控制 / Precise speed control
- 平滑的启动和停止 / Smooth start and stop
- 位置精确控制 / Accurate position control
- 负载自适应 / Load adaptation
- 减少机械应力 / Reduced mechanical stress

### 4. 实现建议 / Implementation Suggestions
1. 每个电机配置独立的PID控制器 / Separate PID controller for each motor
2. 使用中断方式读取编码器 / Use interrupts for encoder reading
3. 实现软启动和软停止 / Implement soft start and stop
4. 添加安全限位 / Add safety limits
5. 提供实时监控和参数调整接口 / Provide real-time monitoring and parameter adjustment
