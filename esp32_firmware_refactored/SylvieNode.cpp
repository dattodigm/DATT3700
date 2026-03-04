/**
 * SylvieNode.cpp - Sylvie Cluster Flower Node Implementation
 *                  Sylvie 集群花朵节点实现
 *
 * All hardware logic ported from verified esp32_sylvie.ino.
 * Refactored into OOP structure inheriting FlowerNode.
 * ⚠️ NO delay() — all timing via millis().
 *
 * 所有硬件逻辑移植自已验证的 esp32_sylvie.ino。
 * 重构为继承 FlowerNode 的面向对象结构。
 * ⚠️ 禁止 delay() — 所有计时使用 millis()。
 */

#include "SylvieNode.h"

// ============================================================
// Constructor / 构造函数
// ============================================================
SylvieNode::SylvieNode()
    : FlowerNode(NODE_ID, NODE_TYPE, OSC_PORT)
    , _autoMode(true)
    , _autoState(0)
    , _lastAutoUpdateMs(0)
{
}

// ============================================================
// begin() - Initialize hardware pins / 初始化硬件引脚
// Verified pin mapping from esp32_sylvie.ino
// ============================================================
bool SylvieNode::begin() {
    // Initialize all motor and LED pins to OUTPUT
    // 初始化所有电机和 LED 引脚为输出模式
    const int pins[] = {
        MOTOR1_PIN_A, MOTOR1_PIN_B,
        MOTOR2_PIN_A, MOTOR2_PIN_B,
        LED1_PIN_R, LED1_PIN_G, LED1_PIN_B,
        LED2_PIN_R, LED2_PIN_G, LED2_PIN_B
    };
    for (int p : pins) {
        pinMode(p, OUTPUT);
    }

    // Start with everything off / 初始状态全部关闭
    stopAll();

    // Record initial time for auto-mode / 记录自动模式初始时间
    _lastAutoUpdateMs = millis();

    Serial.printf("[%s] Hardware initialized (2 motors, 2 RGB LEDs)\n", getNodeId());
    Serial.println("[SylvieNode] 硬件初始化完成（2 电机，2 RGB LED）");

    // Print available commands / 打印可用命令
    Serial.println("\n=== OSC Command List / OSC 命令列表 ===");
    Serial.println("/auto [0/1]        - Switch auto/manual mode / 切换自动/手动模式");
    Serial.println("/motor1 [1/-1/0]   - Control Motor A / 控制电机A");
    Serial.println("/motor2 [1/-1/0]   - Control Motor B / 控制电机B");
    Serial.println("/led1 [r] [g] [b]  - Set LED1 color (0-255) / 设置LED1颜色");
    Serial.println("/led2 [r] [g] [b]  - Set LED2 color (0-255) / 设置LED2颜色");
    Serial.println("/preset [1/2/3]    - Preset scene / 预设场景");
    Serial.println("/stop              - Emergency stop / 紧急停止");
    Serial.println("======================================\n");

    return true;
}

// ============================================================
// update() - Non-blocking main loop tick / 非阻塞主循环
// ============================================================
void SylvieNode::update() {
    // 1. Poll OSC messages / 轮询 OSC 消息
    processOSC();

    // 2. Run auto-mode state machine if enabled / 如果启用则运行自动模式
    if (_autoMode) {
        runAutoMode();
    }

    // 3. Process serial debug commands / 处理串口调试命令
    if (Serial.available() > 0) {
        // Read one line, use fixed buffer (no String concat in loop)
        // 读取一行，使用固定缓冲区（循环中禁止 String 拼接）
        char cmdBuf[64];
        int len = 0;
        while (Serial.available() > 0 && len < (int)(sizeof(cmdBuf) - 1)) {
            char c = Serial.read();
            if (c == '\n' || c == '\r') break;
            cmdBuf[len++] = c;
        }
        cmdBuf[len] = '\0';

        if (len > 0) {
            processSerialCommand(cmdBuf);
        }
    }
}

// ============================================================
// onOSCMessage() - OSC command dispatch / OSC 命令分发
// Ported from esp32_sylvie.ino route functions
// ============================================================
void SylvieNode::onOSCMessage(OSCMessage &msg, const char* address) {
    Serial.printf("[%s] OSC received: %s\n", getNodeId(), address);

    // --- /auto [0|1] - Switch auto/manual mode ---
    if (strcmp(address, "/auto") == 0) {
        if (msg.isInt(0)) {
            int value = msg.getInt(0);
            if (value == 1) {
                _autoMode = true;
                _lastAutoUpdateMs = millis();
                _autoState = 0;
                Serial.println("[SylvieNode] Switched to AUTO mode / 切换到自动模式");
            } else {
                _autoMode = false;
                stopAll();
                Serial.println("[SylvieNode] Switched to MANUAL mode / 切换到手动模式");
            }
        }
    }
    // --- /motor1 [1|-1|0] ---
    else if (strcmp(address, "/motor1") == 0) {
        if (!_autoMode && msg.isInt(0)) {
            int dir = msg.getInt(0);
            setMotor(1, dir);
            Serial.printf("[SylvieNode] Motor A: %d\n", dir);
        }
    }
    // --- /motor2 [1|-1|0] ---
    else if (strcmp(address, "/motor2") == 0) {
        if (!_autoMode && msg.isInt(0)) {
            int dir = msg.getInt(0);
            setMotor(2, dir);
            Serial.printf("[SylvieNode] Motor B: %d\n", dir);
        }
    }
    // --- /led1 [r] [g] [b] ---
    else if (strcmp(address, "/led1") == 0) {
        if (!_autoMode && msg.isInt(0) && msg.isInt(1) && msg.isInt(2)) {
            int r = msg.getInt(0);
            int g = msg.getInt(1);
            int b = msg.getInt(2);
            setLED(1, r, g, b);
            Serial.printf("[SylvieNode] LED1: R=%d G=%d B=%d\n", r, g, b);
        }
    }
    // --- /led2 [r] [g] [b] ---
    else if (strcmp(address, "/led2") == 0) {
        if (!_autoMode && msg.isInt(0) && msg.isInt(1) && msg.isInt(2)) {
            int r = msg.getInt(0);
            int g = msg.getInt(1);
            int b = msg.getInt(2);
            setLED(2, r, g, b);
            Serial.printf("[SylvieNode] LED2: R=%d G=%d B=%d\n", r, g, b);
        }
    }
    // --- /preset [1|2|3] ---
    else if (strcmp(address, "/preset") == 0) {
        if (!_autoMode && msg.isInt(0)) {
            int preset = msg.getInt(0);
            setPreset(preset);
            Serial.printf("[SylvieNode] Preset %d activated\n", preset);
        }
    }
    // --- /stop - Emergency stop ---
    else if (strcmp(address, "/stop") == 0) {
        stopAll();
        Serial.println("[SylvieNode] Emergency stop / 紧急停止");
    }
}

// ============================================================
// stopAll() - Emergency stop / 紧急停止
// ============================================================
void SylvieNode::stopAll() {
    setMotor(1, 0);
    setMotor(2, 0);
    setLED(1, 0, 0, 0);
    setLED(2, 0, 0, 0);
}

// ============================================================
// setMotor() - Motor direction control / 电机方向控制
// Verified logic from esp32_sylvie.ino
// ============================================================
void SylvieNode::setMotor(int motor, int direction) {
    int pinA = (motor == 1) ? MOTOR1_PIN_A : MOTOR2_PIN_A;
    int pinB = (motor == 1) ? MOTOR1_PIN_B : MOTOR2_PIN_B;

    if (direction > 0) {        // FORWARD / 正转
        digitalWrite(pinA, HIGH);
        digitalWrite(pinB, LOW);
    } else if (direction < 0) { // REVERSE / 反转
        digitalWrite(pinA, LOW);
        digitalWrite(pinB, HIGH);
    } else {                    // STOP / 停止
        digitalWrite(pinA, LOW);
        digitalWrite(pinB, LOW);
    }
}

// ============================================================
// setLED() - RGB LED control / RGB LED 控制
// Verified logic from esp32_sylvie.ino
// ============================================================
void SylvieNode::setLED(int led, int r, int g, int b) {
    int pinR = (led == 1) ? LED1_PIN_R : LED2_PIN_R;
    int pinG = (led == 1) ? LED1_PIN_G : LED2_PIN_G;
    int pinB = (led == 1) ? LED1_PIN_B : LED2_PIN_B;

    analogWrite(pinR, r);
    analogWrite(pinG, g);
    analogWrite(pinB, b);
}

// ============================================================
// setPreset() - Preset scenes / 预设场景
// Verified logic from esp32_sylvie.ino
// ============================================================
void SylvieNode::setPreset(int preset) {
    switch (preset) {
        case 1: // Flower A blooms with YELLOW LED / 花A开（黄灯）
            setLED(1, 255, 255, 0);
            setLED(2, 0, 0, 0);
            setMotor(1, 1);
            setMotor(2, -1);
            break;

        case 2: // Flower B blooms with CYAN LED / 花B开（青灯）
            setLED(1, 0, 0, 0);
            setLED(2, 0, 255, 255);
            setMotor(1, -1);
            setMotor(2, 1);
            break;

        case 3: // STOP ALL / 全部停止
            stopAll();
            break;
    }
}

// ============================================================
// runAutoMode() - Auto-mode state machine (millis()-based)
// 自动模式状态机（基于 millis()，无 delay()）
// Ported from esp32_sylvie.ino runAutoMode()
// ============================================================
void SylvieNode::runAutoMode() {
    unsigned long now = millis();

    switch (_autoState) {
        case 0: // Flower A blooms (immediate on entry) / 花A开（进入时立即触发）
            setPreset(1);
            _lastAutoUpdateMs = now;
            _autoState = 1;
            break;

        case 1: // Stop buffer / 停止缓冲
            if (now - _lastAutoUpdateMs >= AUTO_BLOOM_DURATION_MS) {
                stopAll();
                _lastAutoUpdateMs = now;
                _autoState = 2;
            }
            break;

        case 2: // Flower B blooms / 花B开
            if (now - _lastAutoUpdateMs >= AUTO_PAUSE_DURATION_MS) {
                setPreset(2);
                _lastAutoUpdateMs = now;
                _autoState = 3;
            }
            break;

        case 3: // Wait then restart cycle / 等待后重新循环
            if (now - _lastAutoUpdateMs >= AUTO_BLOOM_DURATION_MS) {
                stopAll();
                _lastAutoUpdateMs = now;
                _autoState = 0;
            }
            break;
    }
}

// ============================================================
// processSerialCommand() - Serial debug handler / 串口调试处理器
// Ported from esp32_sylvie.ino processSerialCommand()
// Uses fixed-size char buffers (no String concat)
// ============================================================
void SylvieNode::processSerialCommand(const char* cmd) {
    // Parse command name and arguments / 解析命令名和参数
    char cmdBuf[64];
    strncpy(cmdBuf, cmd, sizeof(cmdBuf) - 1);
    cmdBuf[sizeof(cmdBuf) - 1] = '\0';

    // Convert to lowercase / 转换为小写
    for (int i = 0; cmdBuf[i]; i++) {
        if (cmdBuf[i] >= 'A' && cmdBuf[i] <= 'Z') {
            cmdBuf[i] = cmdBuf[i] + ('a' - 'A');
        }
    }

    // Split command and arguments / 分割命令和参数
    char* space = strchr(cmdBuf, ' ');
    const char* args = "";
    if (space) {
        *space = '\0';
        args = space + 1;
    }

    if (strcmp(cmdBuf, "auto") == 0) {
        int value = atoi(args);
        if (value == 1) {
            _autoMode = true;
            _lastAutoUpdateMs = millis();
            _autoState = 0;
            Serial.println("[Serial] Switched to AUTO mode.");
        } else {
            _autoMode = false;
            stopAll();
            Serial.println("[Serial] Switched to MANUAL mode.");
        }
    }
    else if (strcmp(cmdBuf, "motor1") == 0 || strcmp(cmdBuf, "m1") == 0) {
        if (!_autoMode) {
            int dir = atoi(args);
            setMotor(1, dir);
            Serial.printf("[Serial] Motor A set to: %d\n", dir);
        } else {
            Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
        }
    }
    else if (strcmp(cmdBuf, "motor2") == 0 || strcmp(cmdBuf, "m2") == 0) {
        if (!_autoMode) {
            int dir = atoi(args);
            setMotor(2, dir);
            Serial.printf("[Serial] Motor B set to: %d\n", dir);
        } else {
            Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
        }
    }
    else if (strcmp(cmdBuf, "led1") == 0 || strcmp(cmdBuf, "l1") == 0) {
        if (!_autoMode) {
            int r = 0, g = 0, b = 0;
            sscanf(args, "%d %d %d", &r, &g, &b);
            setLED(1, r, g, b);
            Serial.printf("[Serial] LED1 set to: R=%d G=%d B=%d\n", r, g, b);
        } else {
            Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
        }
    }
    else if (strcmp(cmdBuf, "led2") == 0 || strcmp(cmdBuf, "l2") == 0) {
        if (!_autoMode) {
            int r = 0, g = 0, b = 0;
            sscanf(args, "%d %d %d", &r, &g, &b);
            setLED(2, r, g, b);
            Serial.printf("[Serial] LED2 set to: R=%d G=%d B=%d\n", r, g, b);
        } else {
            Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
        }
    }
    else if (strcmp(cmdBuf, "preset") == 0) {
        if (!_autoMode) {
            int presetNum = atoi(args);
            setPreset(presetNum);
            Serial.printf("[Serial] Preset %d activated.\n", presetNum);
        } else {
            Serial.println("[Serial] Ignored. Switch to MANUAL mode first.");
        }
    }
    else if (strcmp(cmdBuf, "stop") == 0 || strcmp(cmdBuf, "alloff") == 0) {
        stopAll();
        Serial.println("[Serial] All devices STOPPED.");
    }
    else if (strcmp(cmdBuf, "help") == 0 || strcmp(cmdBuf, "?") == 0) {
        printSerialHelp();
    }
    else {
        Serial.printf("[Serial] Unknown command: '%s'. Type 'help'.\n", cmdBuf);
    }
}

// ============================================================
// printSerialHelp() - Serial help text / 串口帮助信息
// ============================================================
void SylvieNode::printSerialHelp() {
    Serial.println("\n=== Serial Debug Commands / 串口调试命令 ===");
    Serial.println("auto [0/1]         - Switch mode (0=Manual, 1=Auto)");
    Serial.println("motor1/m1 [1/-1/0] - Control Motor A");
    Serial.println("motor2/m2 [1/-1/0] - Control Motor B");
    Serial.println("led1/l1 [R] [G] [B] - Set LED1 color (0-255)");
    Serial.println("led2/l2 [R] [G] [B] - Set LED2 color");
    Serial.println("preset [1/2/3]     - Load preset scene");
    Serial.println("stop/alloff        - Stop all motors and LEDs");
    Serial.println("help/?             - Show this help");
    Serial.println("=============================================\n");
}
