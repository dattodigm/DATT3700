#include <ESP32Servo.h>

Servo petalServo;

const int SERVO_PIN = 18;
const int RED_LED   = 22;
const int GREEN_LED = 23;

const int CLOSED_ANGLE = 60;
const int OPEN_ANGLE   = 120;

void setup() {
  Serial.begin(115200);

  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);

  petalServo.setPeriodHertz(50);
  petalServo.attach(SERVO_PIN, 500, 2400);
}

void loop() {
  // Danger: red + close
  digitalWrite(RED_LED, HIGH);
  digitalWrite(GREEN_LED, LOW);
  petalServo.write(CLOSED_ANGLE);
  delay(2000);

  // Relax: green + open
  digitalWrite(RED_LED, LOW);
  digitalWrite(GREEN_LED, HIGH);
  petalServo.write(OPEN_ANGLE);
  delay(2000);
}