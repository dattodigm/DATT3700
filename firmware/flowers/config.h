/**
 * config.h - WiFi和系统配置文件
 * 
 * 复制此文件到每个花朵的固件目录，然后修改以下参数
 */

#ifndef CONFIG_H
#define CONFIG_H

// ========== WiFi 配置 ==========

// 选择WiFi模式:
// - WIFI_MODE_AP: 创建热点（推荐用于演示，电脑直接连接）
// - WIFI_MODE_STA: 连接现有WiFi
// - WIFI_MODE_AP_STA: 混合模式
#define WIFI_MODE_SELECTION WIFI_MODE_AP

// AP模式（创建热点）配置
#define AP_SSID "DigitalBloom_Flower1"  // 花朵热点名称
#define AP_PASSWORD "12345678"          // 至少8位密码

// STA模式（连接现有WiFi）配置
#define STA_SSID "YOUR_HOME_WIFI"
#define STA_PASSWORD "YOUR_WIFI_PASSWORD"

// ========== 花朵ID配置 ==========
#define FLOWER_ID "flower1"  // 每个花朵必须有唯一ID
#define FLOWER_NAME "Sylvie" // 花朵名字（用于显示）

// ========== OSC配置 ==========
#define OSC_PORT 8888
#define PC_IP "192.168.4.2"  // 电脑的IP（AP模式下通常是192.168.4.2）
#define PC_OSC_PORT 9999     // 电脑接收消息的端口

// ========== 硬件类型选择 ==========
// 取消注释你使用的硬件类型:
#define HARDWARE_TYPE_DC_MOTOR
// #define HARDWARE_TYPE_SERVO
// #define HARDWARE_TYPE_STEPPER

// ========== 引脚配置 ==========

#ifdef HARDWARE_TYPE_DC_MOTOR
    // DC电机+LED配置（基于eps32_sylvie）
    #define MOTOR_A_PIN1 25
    #define MOTOR_A_PIN2 26
    #define MOTOR_B_PIN1 18
    #define MOTOR_B_PIN2 19
    
    #define LED1_R 2
    #define LED1_G 4
    #define LED1_B 5
    #define LED2_R 12
    #define LED2_G 13
    #define LED2_B 14
#endif

#ifdef HARDWARE_TYPE_SERVO
    // 舵机配置（基于Face_tracking）
    #define SERVO_X_PINS {18, 21, 23, 26}  // X轴舵机引脚数组
    #define SERVO_Y_PINS {19, 22, 25, 27}  // Y轴舵机引脚数组
    #define NUM_SERVOS_X 4
    #define NUM_SERVOS_Y 4
#endif

#ifdef HARDWARE_TYPE_STEPPER
    // 步进电机配置（待实现）
    #define STEPPER_STEP_PIN 32
    #define STEPPER_DIR_PIN 33
    #define STEPPER_ENABLE_PIN 25
#endif

// 超声波传感器（可选）
#define ULTRASONIC_TRIG 27
#define ULTRASONIC_ECHO 33
#define USE_ULTRASONIC  // 取消注释以启用

// LCD屏幕（可选，I2C）
#define LCD_SDA 21
#define LCD_SCL 22
#define USE_LCD  // 取消注释以启用

// ========== 运动限制配置 ==========

// DC电机限制
#define DC_MOTOR_MAX_RUN_TIME 5000  // 电机最长连续运行时间(ms)，防止过热
#define DC_MOTOR_COOLDOWN 2000      // 冷却时间(ms)

// 舵机限制
#define SERVO_MIN_ANGLE 0
#define SERVO_MAX_ANGLE 180
#define SERVO_SMOOTHING_STEPS 10    // 平滑移动步数

// ========== 调试配置 ==========
#define DEBUG_MODE  // 取消注释以启用详细调试输出
#define SERIAL_BAUD 115200

#endif
