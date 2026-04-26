const int motorPin = 22;

const int pwmFreq = 20000;
const int pwmResolution = 8;

void setup() {
  ledcAttach(motorPin, pwmFreq, pwmResolution);
}

void setMotorSpeed(int speed) {

  if (speed > 0) {
    // Kick start
    ledcWrite(motorPin, 255);
    delay(30);  // 20–50 ms works well for N20 motors
  }

  // Set desired speed
  ledcWrite(motorPin, speed);
}

void loop() {

  setMotorSpeed(100);  // very low speed but still starts
}
