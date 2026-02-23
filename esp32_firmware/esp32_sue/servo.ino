#include <ESP32Servo.h>

Servo petalServo;

// ---- Pins (ESP32) ----
const int TRIG_PIN  = 27;
const int ECHO_PIN  = 33;
const int SERVO_PIN = 14;

// ---- Servo angles 
const int CLOSED_ANGLE = 60;
const int OPEN_ANGLE   = 120;

// ---- Distance thresholds 
const int OPEN_CM  = 20;
const int CLOSE_CM = 40;

// ---- Motion feel 
const int STEP_DELAY_MS = 5;
const int LOOP_DELAY_MS = 10;

bool isOpen = false;
int currentAngle = CLOSED_ANGLE;

long readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (duration == 0) return -1;

  long cm = (long)(duration * 0.0343 / 2.0);
  return cm;
}

void smoothMoveTo(int targetAngle) {
  if (targetAngle == currentAngle) return;

  if (targetAngle > currentAngle) {
    for (int a = currentAngle; a <= targetAngle; a++) {
      petalServo.write(a);
      delay(STEP_DELAY_MS);
    }
  } else {
    for (int a = currentAngle; a >= targetAngle; a--) {
      petalServo.write(a);
      delay(STEP_DELAY_MS);
    }
  }
  currentAngle = targetAngle;
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  petalServo.setPeriodHertz(50);
  petalServo.attach(SERVO_PIN, 500, 2400);

  petalServo.write(CLOSED_ANGLE);
  currentAngle = CLOSED_ANGLE;
}

void loop() {
  long d = readDistanceCM();

  if (d > 0) {
    Serial.print("Distance (cm): ");
    Serial.println(d);

    if (!isOpen && d <= OPEN_CM) {
      smoothMoveTo(OPEN_ANGLE);
      isOpen = true;
    }

    if (isOpen && d >= CLOSE_CM) {
      smoothMoveTo(CLOSED_ANGLE);
      isOpen = false;
    }
  }

  delay(LOOP_DELAY_MS);
}