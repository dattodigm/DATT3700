/*
 * ESP32 Flower Control Firmware
 * Receives OSC commands via UDP and controls servos and motors
 * 
 * Hardware connections:
 * - Pan Servo: GPIO 18
 * - Tilt Servo: GPIO 19
 * - Flower Motor 1: GPIO 25 (IN1)
 * - Flower Motor 2: GPIO 26 (IN2)
 * - Motor Enable: GPIO 27 (PWM)
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <ESP32Servo.h>

// WiFi credentials - UPDATE THESE
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// OSC UDP settings
const unsigned int localPort = 8000;
WiFiUDP udp;

// Servo objects
Servo panServo;
Servo tiltServo;

// Pin definitions
const int PAN_SERVO_PIN = 18;
const int TILT_SERVO_PIN = 19;
const int MOTOR_IN1_PIN = 25;
const int MOTOR_IN2_PIN = 26;
const int MOTOR_ENABLE_PIN = 27;

// PWM settings for motor
const int PWM_FREQ = 5000;
const int PWM_CHANNEL = 0;
const int PWM_RESOLUTION = 8;

// Current state
int currentPanAngle = 90;
int currentTiltAngle = 90;
float currentFlowerState = 0.0;
int currentMotorSpeed = 0;
bool trackingMode = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize servos
  panServo.attach(PAN_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);
  
  // Set to center position
  panServo.write(90);
  tiltServo.write(90);
  
  // Initialize motor pins
  pinMode(MOTOR_IN1_PIN, OUTPUT);
  pinMode(MOTOR_IN2_PIN, OUTPUT);
  pinMode(MOTOR_ENABLE_PIN, OUTPUT);
  
  // Setup PWM for motor enable
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(MOTOR_ENABLE_PIN, PWM_CHANNEL);
  
  // Stop motor initially
  digitalWrite(MOTOR_IN1_PIN, LOW);
  digitalWrite(MOTOR_IN2_PIN, LOW);
  ledcWrite(PWM_CHANNEL, 0);
  
  // Connect to WiFi
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Listening on UDP port: ");
  Serial.println(localPort);
  
  // Start UDP
  udp.begin(localPort);
  
  Serial.println("ESP32 Flower Control Ready!");
}

void loop() {
  // Check for OSC messages
  OSCMessage msg;
  int size = udp.parsePacket();
  
  if (size > 0) {
    while (size--) {
      msg.fill(udp.read());
    }
    
    if (!msg.hasError()) {
      // Route OSC messages to appropriate handlers
      msg.dispatch("/flower/servo", handleServoCommand);
      msg.dispatch("/flower/state", handleFlowerState);
      msg.dispatch("/flower/motor", handleMotorCommand);
      msg.dispatch("/flower/mode", handleTrackingMode);
    } else {
      Serial.print("OSC Error: ");
      Serial.println(msg.getError());
    }
  }
  
  delay(10);
}

// Handle servo position command
void handleServoCommand(OSCMessage &msg) {
  if (msg.size() == 2) {
    int panAngle = msg.getInt(0);
    int tiltAngle = msg.getInt(1);
    
    // Constrain to valid range
    panAngle = constrain(panAngle, 0, 180);
    tiltAngle = constrain(tiltAngle, 0, 180);
    
    // Update servos
    panServo.write(panAngle);
    tiltServo.write(tiltAngle);
    
    currentPanAngle = panAngle;
    currentTiltAngle = tiltAngle;
    
    Serial.print("Servo: Pan=");
    Serial.print(panAngle);
    Serial.print("° Tilt=");
    Serial.print(tiltAngle);
    Serial.println("°");
  }
}

// Handle flower open/close state
void handleFlowerState(OSCMessage &msg) {
  if (msg.size() == 1) {
    float openness = msg.getFloat(0);
    
    // Constrain to 0.0-1.0
    openness = constrain(openness, 0.0, 1.0);
    
    currentFlowerState = openness;
    
    // Convert openness to motor control
    // 0.0 = fully closed, 1.0 = fully open
    // Map to motor speed: negative for closing, positive for opening
    int motorSpeed = 0;
    
    if (openness > currentFlowerState + 0.05) {
      // Opening
      motorSpeed = 70;
    } else if (openness < currentFlowerState - 0.05) {
      // Closing
      motorSpeed = -70;
    }
    
    setMotorSpeed(motorSpeed);
    
    Serial.print("Flower state: ");
    Serial.print(openness * 100);
    Serial.println("%");
  }
}

// Handle motor speed command
void handleMotorCommand(OSCMessage &msg) {
  if (msg.size() == 1) {
    int speed = msg.getInt(0);
    
    // Constrain to -100 to 100
    speed = constrain(speed, -100, 100);
    
    setMotorSpeed(speed);
    
    Serial.print("Motor speed: ");
    Serial.println(speed);
  }
}

// Handle tracking mode
void handleTrackingMode(OSCMessage &msg) {
  if (msg.size() == 1) {
    int mode = msg.getInt(0);
    
    trackingMode = (mode == 1);
    
    Serial.print("Tracking mode: ");
    Serial.println(trackingMode ? "ENABLED" : "DISABLED");
    
    if (!trackingMode) {
      // Stop motor when tracking disabled
      setMotorSpeed(0);
    }
  }
}

// Set motor speed and direction
void setMotorSpeed(int speed) {
  // speed: -100 to 100
  // negative = reverse (close), positive = forward (open)
  
  currentMotorSpeed = speed;
  
  if (speed > 0) {
    // Forward (open)
    digitalWrite(MOTOR_IN1_PIN, HIGH);
    digitalWrite(MOTOR_IN2_PIN, LOW);
    int pwmValue = map(abs(speed), 0, 100, 0, 255);
    ledcWrite(PWM_CHANNEL, pwmValue);
  } else if (speed < 0) {
    // Reverse (close)
    digitalWrite(MOTOR_IN1_PIN, LOW);
    digitalWrite(MOTOR_IN2_PIN, HIGH);
    int pwmValue = map(abs(speed), 0, 100, 0, 255);
    ledcWrite(PWM_CHANNEL, pwmValue);
  } else {
    // Stop
    digitalWrite(MOTOR_IN1_PIN, LOW);
    digitalWrite(MOTOR_IN2_PIN, LOW);
    ledcWrite(PWM_CHANNEL, 0);
  }
}
