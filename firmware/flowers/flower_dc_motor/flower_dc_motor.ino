/**
 * flower_dc_motor.ino - DC电机花朵完整固件
 * 
 * 基于Digital Bloom系统架构
 * 兼容队友的eps32_sylvie硬件配置
 * 
 * 硬件: ESP32 + 2x DC电机 + 2x RGB LED
 * 通信: OSC over WiFi
 */

#include "../config.h"
#include "../libraries/WiFiManager/WiFiManager.h"
#include <OSCMessage.h>

// 全局对象
WiFiManager wifiManager;

// 状态变量
struct FlowerState {
    float bloomLevel;      // 0.0 - 1.0 (花朵开放度)
    float jitter;          // 0.0 - 1.0 (颤动强度)
    float speed;           // 0.0 - 1.0 (运动速度)
    uint8_t ledR, ledG, ledB;  // LED颜色
    char lcdMessage[32];   // LCD显示消息
    bool isResponding;     // 是否正在响应
    unsigned long lastUpdate;  // 最后更新时间
};

FlowerState currentState = {0, 0, 0, 0, 0, 0, "", false, 0};
FlowerState targetState = {0, 0, 0, 0, 0, 0, "", false, 0};

// 电机保护计时器
unsigned long motorStartTime = 0;
bool motorRunning = false;

// 平滑插值
float currentBloom = 0.0;
float smoothedJitter = 0.0;
const float EMA_ALPHA = 0.3;  // 指数平滑系数

void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(1000);
    
    printWelcomeMessage();
    
    // 初始化引脚
    initHardware();
    
    // 启动WiFi管理器
    wifiManager.begin(WiFiMode::AP);
    
    // 初始状态
    setLED(0, 0, 0);
    stopMotors();
    
    Serial.println("\n🌸 系统就绪，等待OSC命令...\n");
}

void loop() {
    // 更新WiFi状态
    wifiManager.update();
    
    // 处理OSC消息
    handleOSCMessage();
    
    // 更新物理状态（平滑插值）
    updatePhysics();
    
    // 更新硬件输出
    updateHardware();
    
    // 电机过热保护
    checkMotorSafety();
    
    delay(10);  // 100Hz更新频率
}

// ========== 硬件初始化 ==========
void initHardware() {
    // 初始化电机引脚
    pinMode(MOTOR_A_PIN1, OUTPUT);
    pinMode(MOTOR_A_PIN2, OUTPUT);
    pinMode(MOTOR_B_PIN1, OUTPUT);
    pinMode(MOTOR_B_PIN2, OUTPUT);
    
    // 初始化LED引脚
    pinMode(LED1_R, OUTPUT);
    pinMode(LED1_G, OUTPUT);
    pinMode(LED1_B, OUTPUT);
    pinMode(LED2_R, OUTPUT);
    pinMode(LED2_G, OUTPUT);
    pinMode(LED2_B, OUTPUT);
    
    // 超声波传感器（可选）
    #ifdef USE_ULTRASONIC
    pinMode(ULTRASONIC_TRIG, OUTPUT);
    pinMode(ULTRASONIC_ECHO, INPUT);
    #endif
    
    Serial.println("硬件初始化完成");
}

// ========== OSC消息处理 ==========
void handleOSCMessage() {
    WiFiUDP* udp = wifiManager.getUDP();
    OSCMessage msg;
    int size = udp->parsePacket();
    
    if (size > 0) {
        while (size--) {
            msg.fill(udp->read());
        }
        
        if (!msg.hasError()) {
            char addressBuffer[128];
            msg.getAddress(addressBuffer, 0, sizeof(addressBuffer));
            
            #ifdef DEBUG_MODE
            Serial.print("📨 收到OSC: ");
            Serial.println(addressBuffer);
            #endif
            
            // 路由到处理函数
            msg.route("/flower/state", routeFlowerState);
            msg.route("/flower/motion", routeFlowerMotion);
            msg.route("/flower/lcd", routeFlowerLCD);
            msg.route("/flower/preset", routePreset);
            msg.route("/system/stop", routeEmergencyStop);
        }
    }
}

void routeFlowerState(OSCMessage &msg, int addrOffset) {
    if (msg.isFloat(0)) targetState.bloomLevel = constrain(msg.getFloat(0), 0.0f, 1.0f);
    if (msg.isFloat(1)) targetState.jitter = constrain(msg.getFloat(1), 0.0f, 1.0f);
    if (msg.isFloat(2)) targetState.speed = constrain(msg.getFloat(2), 0.0f, 1.0f);
    if (msg.isInt(3)) targetState.ledR = msg.getInt(3);
    if (msg.isInt(4)) targetState.ledG = msg.getInt(4);
    if (msg.isInt(5)) targetState.ledB = msg.getInt(5);
    
    targetState.lastUpdate = millis();
    
    #ifdef DEBUG_MODE
    Serial.printf("State: bloom=%.2f jitter=%.2f speed=%.2f RGB=(%d,%d,%d)\n",
                  targetState.bloomLevel, targetState.jitter, targetState.speed,
                  targetState.ledR, targetState.ledG, targetState.ledB);
    #endif
}

void routeFlowerMotion(OSCMessage &msg, int addrOffset) {
    // 预留：处理运动参数（摇摆等）
    #ifdef DEBUG_MODE
    Serial.println("Motion route received");
    #endif
}

void routeFlowerLCD(OSCMessage &msg, int addrOffset) {
    if (msg.isString(0)) {
        char message[32];
        msg.getString(0, message, 32);
        strncpy(targetState.lcdMessage, message, 31);
        targetState.lcdMessage[31] = '\0';
        
        Serial.print("LCD: ");
        Serial.println(targetState.lcdMessage);
    }
}

void routePreset(OSCMessage &msg, int addrOffset) {
    if (msg.isInt(0)) {
        int preset = msg.getInt(0);
        applyPreset(preset);
    }
}

void routeEmergencyStop(OSCMessage &msg, int addrOffset) {
    Serial.println("🛑 紧急停止！");
    emergencyStop();
}

// ========== 物理更新（平滑插值） ==========
void updatePhysics() {
    // EMA平滑插值
    currentBloom = emaSmooth(currentBloom, targetState.bloomLevel, EMA_ALPHA);
    smoothedJitter = emaSmooth(smoothedJitter, targetState.jitter, EMA_ALPHA);
    
    // 更新LED颜色（直接设置，不需要平滑）
    currentState.ledR = targetState.ledR;
    currentState.ledG = targetState.ledG;
    currentState.ledB = targetState.ledB;
}

float emaSmooth(float current, float target, float alpha) {
    return current + alpha * (target - current);
}

// ========== 硬件输出更新 ==========
void updateHardware() {
    // 根据bloomLevel控制电机
    updateMotors();
    
    // 更新LED
    setLED(currentState.ledR, currentState.ledG, currentState.ledB);
    
    // 添加基于jitter的随机颤动
    if (smoothedJitter > 0.1) {
        applyJitter();
    }
}

void updateMotors() {
    // bloomLevel映射到电机行为
    // 0.0 = 完全关闭（电机停止）
    // 0.5 = 半开（电机间歇运行）
    // 1.0 = 完全开放（电机持续运行）
    
    if (currentBloom < 0.1) {
        stopMotors();
    } else if (currentBloom > 0.9) {
        // 完全开放：电机持续正转
        setMotor(1, 1);
        setMotor(2, -1);  // 反向形成开合动作
    } else {
        // 中间状态：基于speed参数脉动
        unsigned long period = map(targetState.speed * 100, 0, 100, 2000, 200);
        unsigned long phase = millis() % period;
        
        if (phase < period * currentBloom) {
            setMotor(1, 1);
            setMotor(2, -1);
        } else {
            stopMotors();
        }
    }
}

void applyJitter() {
    // 基于jitter参数添加随机颤动
    static unsigned long lastJitter = 0;
    if (millis() - lastJitter > 50) {  // 每50ms
        if (random(100) < smoothedJitter * 100) {
            // 短暂反转产生颤动效果
            setMotor(1, -1);
            delay(20);
            setMotor(1, 1);
        }
        lastJitter = millis();
    }
}

// ========== 电机控制 ==========
void setMotor(int motor, int direction) {
    int pin1, pin2;
    
    if (motor == 1) {
        pin1 = MOTOR_A_PIN1;
        pin2 = MOTOR_A_PIN2;
    } else {
        pin1 = MOTOR_B_PIN1;
        pin2 = MOTOR_B_PIN2;
    }
    
    if (direction > 0) {
        digitalWrite(pin1, HIGH);
        digitalWrite(pin2, LOW);
    } else if (direction < 0) {
        digitalWrite(pin1, LOW);
        digitalWrite(pin2, HIGH);
    } else {
        digitalWrite(pin1, LOW);
        digitalWrite(pin2, LOW);
    }
    
    if (direction != 0 && !motorRunning) {
        motorStartTime = millis();
        motorRunning = true;
    } else if (direction == 0) {
        motorRunning = false;
    }
}

void stopMotors() {
    setMotor(1, 0);
    setMotor(2, 0);
}

// ========== LED控制 ==========
void setLED(uint8_t r, uint8_t g, uint8_t b) {
    analogWrite(LED1_R, r);
    analogWrite(LED1_G, g);
    analogWrite(LED1_B, b);
    analogWrite(LED2_R, r);
    analogWrite(LED2_G, g);
    analogWrite(LED2_B, b);
}

// ========== 预设场景 ==========
void applyPreset(int preset) {
    Serial.printf("应用预设场景: %d\n", preset);
    
    switch(preset) {
        case 1: // 快乐 - 黄色，开放，快速
            targetState = {1.0f, 0.3f, 0.8f, 255, 255, 0, "Happy!", true, millis()};
            break;
            
        case 2: // 防御 - 红色，闭合，紧张
            targetState = {0.1f, 0.9f, 0.9f, 255, 0, 0, "Defensive", true, millis()};
            break;
            
        case 3: // 共情 - 粉色，开放，缓慢
            targetState = {0.9f, 0.1f, 0.2f, 255, 105, 180, "Empathy~", true, millis()};
            break;
            
        case 4: // 嫉妒 - 紫色，抖动
            targetState = {0.5f, 1.0f, 1.0f, 128, 0, 128, "Jealous!", true, millis()};
            break;
            
        case 5: // 睡眠 - 蓝色，闭合
            targetState = {0.0f, 0.0f, 0.0f, 0, 0, 255, "zZZ...", false, millis()};
            break;
            
        default:
            stopMotors();
            setLED(0, 0, 0);
    }
}

// ========== 安全保护 ==========
void checkMotorSafety() {
    if (motorRunning && millis() - motorStartTime > DC_MOTOR_MAX_RUN_TIME) {
        Serial.println("⚠️ 电机过热保护，强制停止");
        stopMotors();
        delay(DC_MOTOR_COOLDOWN);
    }
}

void emergencyStop() {
    targetState = {0, 0, 0, 0, 0, 0, "STOP", false, millis()};
    currentBloom = 0;
    stopMotors();
    setLED(0, 0, 0);
}

// ========== 串口命令（调试用） ==========
void checkSerialCommands() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        cmd.toLowerCase();
        
        if (cmd == "stop" || cmd == "s") {
            emergencyStop();
        } else if (cmd == "status") {
            wifiManager.printStatus();
            Serial.printf("Bloom: %.2f, Jitter: %.2f\n", currentBloom, smoothedJitter);
        } else if (cmd.startsWith("preset")) {
            int p = cmd.substring(7).toInt();
            applyPreset(p);
        }
    }
}

// ========== 辅助函数 ==========
void printWelcomeMessage() {
    Serial.println("\n");
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║     🌸 Digital Bloom - DC Motor 🌸    ║");
    Serial.println("║        具身AI花朵控制系统 v1.0         ║");
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println();
    Serial.print("花朵ID: ");
    Serial.println(FLOWER_ID);
    Serial.print("花朵名称: ");
    Serial.println(FLOWER_NAME);
    Serial.println();
}
