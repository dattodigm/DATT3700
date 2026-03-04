/**
 * SylvieNode.h - Sylvie Cluster Flower Node / Sylvie 集群花朵节点
 *
 * Concrete implementation of FlowerNode for the Sylvie hardware:
 *   - 2× DC motors (via H-bridge driver, e.g. L298N)
 *   - 2× RGB LEDs
 *   - Auto-mode state machine (millis()-based, NO delay())
 *   - OSC command routing + Serial debug interface
 *
 * Sylvie 硬件的 FlowerNode 具体实现：
 *   - 2× 直流电机（通过 H 桥驱动，如 L298N）
 *   - 2× RGB LED
 *   - 自动模式状态机（基于 millis()，禁止 delay()）
 *   - OSC 命令路由 + 串口调试接口
 *
 * Pin mapping verified against esp32_sylvie.ino:
 *   Motor A: GPIO 25 (IN1), GPIO 26 (IN2)
 *   LED 1:   GPIO 2 (R), GPIO 4 (G), GPIO 5 (B)
 *   Motor B: GPIO 18 (IN3), GPIO 19 (IN4)
 *   LED 2:   GPIO 12 (R), GPIO 13 (G), GPIO 14 (B)
 */

#ifndef SYLVIE_NODE_H
#define SYLVIE_NODE_H

#include "FlowerNode.h"
#include "config.h"

// ============================================================
// Hardware Pin Definitions / 硬件引脚定义
// Verified against esp32_sylvie.ino
// ============================================================

// Group 1: Motor A + LED 1 / 第一组：电机 A + LED 1
#define MOTOR1_PIN_A  25
#define MOTOR1_PIN_B  26
#define LED1_PIN_R     2
#define LED1_PIN_G     4
#define LED1_PIN_B     5

// Group 2: Motor B + LED 2 / 第二组：电机 B + LED 2
#define MOTOR2_PIN_A  18
#define MOTOR2_PIN_B  19
#define LED2_PIN_R    12
#define LED2_PIN_G    13
#define LED2_PIN_B    14

// PWM Configuration for L298N motors / L298N 电机 PWM 配置
#define PWM_FREQ       1000  // 1 kHz PWM frequency / PWM 频率
#define PWM_RESOLUTION 8     // 8-bit resolution (0-255) / 8 位分辨率

// ============================================================
// Auto-Mode Timing / 自动模式时间参数
// ============================================================
#define AUTO_BLOOM_DURATION_MS   3000  // Bloom hold time / 开花保持时间
#define AUTO_PAUSE_DURATION_MS    500  // Pause between transitions / 过渡间暂停时间

/**
 * SylvieNode - Concrete FlowerNode for Sylvie cluster hardware
 * Sylvie 集群硬件的 FlowerNode 具体实现
 */
class SylvieNode : public FlowerNode {
public:
    /**
     * Constructor / 构造函数
     */
    SylvieNode();

    // ============================================================
    // FlowerNode Pure Virtual Overrides / FlowerNode 纯虚函数实现
    // ============================================================

    bool begin() override;
    void update() override;
    void onOSCMessage(OSCMessage &msg, const char* address) override;
    void stopAll() override;

    // ============================================================
    // Hardware Control / 硬件控制
    // ============================================================

    /**
     * Set motor direction and speed (PWM).
     * 设置电机方向和速度（PWM）。
     *
     * @param motor     Motor number (1 or 2) / 电机编号（1 或 2）
     * @param direction  1=forward, -1=reverse, 0=stop / 1=正转, -1=反转, 0=停止
     * @param speed     PWM duty cycle 0-255 / PWM 占空比
     */
    void setMotor(int motor, int direction, int speed = 255);

    /**
     * Set LED color.
     * 设置 LED 颜色。
     *
     * @param led  LED number (1 or 2) / LED 编号（1 或 2）
     * @param r    Red value (0-255) / 红色值
     * @param g    Green value (0-255) / 绿色值
     * @param b    Blue value (0-255) / 蓝色值
     */
    void setLED(int led, int r, int g, int b);

    /**
     * Activate a preset scene.
     * 激活预设场景。
     *
     * @param preset  Preset number (1=FlowerA, 2=FlowerB, 3=StopAll)
     *                预设编号（1=花A, 2=花B, 3=全部停止）
     */
    void setPreset(int preset);

    // ============================================================
    // Serial Debug Interface / 串口调试接口
    // ============================================================

    /**
     * Process a serial debug command.
     * 处理串口调试命令。
     *
     * @param cmd  Command string from Serial / 来自串口的命令字符串
     */
    void processSerialCommand(const char* cmd);

private:
    // ============================================================
    // Auto-Mode State Machine / 自动模式状态机
    // ============================================================

    void runAutoMode();
    void printSerialHelp();

    bool          _autoMode;          // Auto/manual mode flag / 自动/手动模式标志
    int           _autoState;         // State machine step / 状态机步骤
    unsigned long _lastAutoUpdateMs;  // Last auto-mode transition time / 上次自动模式切换时间
};

#endif // SYLVIE_NODE_H
